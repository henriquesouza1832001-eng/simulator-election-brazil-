"""Motor de acontecimentos do mandato.

Três tipos: decisão (tem prazo e uma opção padrão), oportunidade (prazo maior) e informativo
(acontece e vai ao histórico). O diretor respeita ritmo: dias tranquilos entre acontecimentos,
nada de empilhar decisões nem repetir a mesma etiqueta em sequência. Sorteios são determinísticos
(hash da semente, do dia e da chave), então a mesma partida produz a mesma história.
Conceitos inspirados em estudo de projetos de referência; implementação e conteúdo originais.
"""
from __future__ import annotations

import hashlib
from datetime import date, timedelta
from typing import Any

from .event_library import get_library
from .event_remix import is_historical, remap_places, remix, scale_effects

EXPIRES_DAYS = {"decisao": 5, "oportunidade": 14, "info": 0}
BASE_DAILY_CHANCE = 0.05
MIN_GAP_DAYS = 7          # dias tranquilos entre acontecimentos
MAX_PENDING = 2           # nunca empilhar mais que isso
HISTORY_LIMIT = 60

# Limites por métrica ao aplicar efeitos.
CLAMPS: dict[str, tuple[float, float]] = {
    "approval": (0, 100), "congress_support": (0, 100), "integrity": (0, 100), "governability": (0, 100),
    "institutional_trust": (0, 100), "gdp_growth": (-10, 15), "inflation": (0.5, 40), "unemployment": (2, 30),
    "primary_balance": (-15, 10),
}
# Escala global dos efeitos dos acontecimentos nas métricas de opinião e instituições.
# Ajustada por simulação de mandato completo (ver tests/test_story_balance.py): sem isso, a soma de ~20
# acontecimentos em 4 anos derrubava a aprovação de forma desproporcional.
EFFECT_SCALE = 0.45


def _rand(state: dict[str, Any], day: date, key: str) -> float:
    """Número em [0, 1) determinístico por semente, dia e chave (sem random global)."""
    digest = hashlib.sha256(f"{state.get('campaign_seed', 203001)}|story|{day.isoformat()}|{key}".encode()).digest()
    return int.from_bytes(digest[:8], "big") / 2 ** 64


def ensure_story_state(state: dict[str, Any]) -> dict[str, Any]:
    story = state.setdefault("story", {})
    story.setdefault("pending", [])
    story.setdefault("history", [])
    story.setdefault("seen", {})
    story.setdefault("queue", [])        # continuações agendadas: {"def", "on"}
    story.setdefault("last_event", None)
    story.setdefault("last_tags", [])
    story.setdefault("counters", {})
    return story


def _apply_effects(state: dict[str, Any], effects: dict[str, float], cost_bi: float) -> list[dict[str, Any]]:
    """Aplica efeitos e devolve os deltas realmente aplicados, para mostrar ao jogador."""
    from .fiscal import record_one_off_spending

    deltas: list[dict[str, Any]] = []
    metrics = state.setdefault("metrics", {})
    for key, delta in effects.items():
        if not delta:
            continue
        if not key.startswith("pp:"):
            delta = round(delta * EFFECT_SCALE, 3)  # a trajetória partidária usa valores já na escala da própria tela
        if not delta:
            continue
        if key.startswith("inst:"):
            inst = state.setdefault("institutions", {})
            name = key[5:]
            before = float(inst.get(name, 50))
            inst[name] = round(max(0, min(100, before + delta)), 2)
            deltas.append({"key": key, "label": name.replace("_", " "), "delta": round(inst[name] - before, 2)})
            continue
        if key.startswith("pp:"):
            pp = state.get("party_path")
            if pp and pp.get("active"):
                name = key[3:]
                before = float(pp.get(name, 0))
                top = 100 if name != "energy" else 100
                pp[name] = round(max(0, min(top, before + delta)), 2)
                deltas.append({"key": key, "label": {"reputation": "reputação", "network": "contatos", "standing": "prestígio no partido",
                                                     "militancy": "militância", "energy": "energia"}[name], "delta": round(pp[name] - before, 2)})
            continue
        if key.startswith("rel:"):
            rel = state.setdefault("relation_delta", {})
            rel[key[4:]] = round(rel.get(key[4:], 0.0) + delta, 3)
            deltas.append({"key": key, "label": f"relação {key[4:]}", "delta": delta})
            continue
        low, high = CLAMPS.get(key, (-1e9, 1e9))
        before = float(metrics.get(key, 0))
        metrics[key] = round(max(low, min(high, before + delta)), 2)
        deltas.append({"key": key, "label": key.replace("_", " "), "delta": round(metrics[key] - before, 2)})
    if cost_bi:
        # Gasto único (não vira déficit recorrente): entra na dívida e nas despesas extras do ano corrente.
        record_one_off_spending(state, cost_bi)
        deltas.append({"key": "cost_bi", "label": "custo (R$ bi)", "delta": -cost_bi})
    return deltas


def _public(ev: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in ev.items() if k != "fallback"}


def _fire(state: dict[str, Any], def_id: str, day: date) -> dict[str, Any] | None:
    story = ensure_story_state(state)
    definition = get_library().get(def_id)
    kind = definition["kind"]
    number = story["seen"].get(def_id, {}).get("n", 0) + 1
    ev = {
        "id": f"{def_id}-{number}", "def": def_id, "kind": kind, "tags": definition.get("tags", []),
        "title": definition["title"], "text": definition["text"], "on": day.isoformat(),
        "expires": (day + timedelta(days=EXPIRES_DAYS[kind])).isoformat() if kind != "info" else None,
        "choices": [{"id": c["id"], "label": c["label"], "hint": c.get("hint", ""), "tone": c.get("tone", "neutra"),
                     "cost_bi": c.get("cost_bi", 0.0)} for c in definition["choices"]],
        "fallback": definition.get("fallback") or definition["choices"][-1]["id"], "simulated": True,
    }
    if is_historical(definition):
        # Fato real "fora de época": lugar, intensidade e redação próprios desta partida (ver event_remix).
        r = remix(definition, state, day.isoformat())
        ev["title"], ev["text"] = r["title"], r["text"]
        ev["remix"] = {"places": r["places"], "intensity": r["intensity"], "label": r["intensity_label"]}
        key = f"{def_id}|{day.isoformat()}"
        for c in ev["choices"]:
            c["label"] = remap_places(c["label"], state, key, ev["remix"]["places"])
            c["hint"] = remap_places(c["hint"], state, key, ev["remix"]["places"])
            c["cost_bi"] = round(c["cost_bi"] * r["intensity"], 2)
        ev["inspired_by_real_event"] = True
    if _career_governance(state) is not None:
        ev["career_level"] = True
        ev["career_costs"] = {}
        for c in ev["choices"]:
            cost_mi = _career_cost_mi(state, float(c["cost_bi"]))
            ev["career_costs"][c["id"]] = cost_mi
            had_cost = bool(c["cost_bi"])
            c["cost_bi"] = 0.0
            c["cost_mi"] = cost_mi
            if had_cost:
                c["hint"] = f"Usa R$ {cost_mi:.1f} mi da reserva do cargo." if cost_mi else "Sem verba própria do cargo: depende de articulação."
    story["seen"][def_id] = {"n": number, "last": day.isoformat()}
    story.setdefault("seen_family", {})[definition.get("family", "base")] = day.isoformat()
    story["last_event"] = day.isoformat()
    story["last_tags"] = definition.get("tags", [])
    if kind == "info":
        _resolve(state, ev, definition["choices"][0]["id"], day, auto=False)
    else:
        story["pending"].append(ev)
    return ev


def _resolve(state: dict[str, Any], ev: dict[str, Any], choice_id: str, day: date, auto: bool) -> dict[str, Any]:
    story = ensure_story_state(state)
    definition = get_library().get(ev["def"])
    choice = next((c for c in definition["choices"] if c["id"] == choice_id), None)
    if choice is None:
        raise ValueError("Opção inválida.")
    effects, cost, outcome = dict(choice.get("effects", {})), float(choice.get("cost_bi", 0.0)), choice.get("outcome", "")
    remixed = ev.get("remix")
    if remixed:  # a intensidade desta instância escala efeitos e custo; o desfecho usa os mesmos lugares
        effects = scale_effects(effects, remixed["intensity"])
        cost = round(cost * remixed["intensity"], 3)
        outcome = remap_places(outcome, state, f"{ev['def']}|{ev['on']}", remixed["places"])
    if ev.get("career_level") and _career_governance(state) is not None:
        # _fire stores the career cost after applying a historical remix intensity.
        # Do not scale it again here; only base event effects/costs need scaling at resolution.
        deltas = _apply_career_effects(state, effects, float(ev.get("career_costs", {}).get(choice_id, 0.0)))
    else:
        deltas = _apply_effects(state, effects, cost)
    for follow_id, days in choice.get("follow", []):
        story["queue"].append({"def": follow_id, "on": (day + timedelta(days=days)).isoformat()})
    entry = {"id": ev["id"], "def": ev["def"], "title": ev["title"], "kind": ev["kind"], "on": day.isoformat(),
             "choice": choice_id, "choice_label": choice["label"] if not remixed else next((c["label"] for c in ev["choices"] if c["id"] == choice_id), choice["label"]),
             "outcome": outcome, "deltas": deltas, "auto": auto, "tags": ev.get("tags", []),
             "inspired_by_real_event": bool(ev.get("inspired_by_real_event")), "intensity": (remixed or {}).get("label")}
    story["history"].insert(0, entry)
    del story["history"][HISTORY_LIMIT:]
    story["pending"] = [p for p in story["pending"] if p["id"] != ev["id"]]
    counters = story["counters"]
    counters[f"tom:{choice.get('tone', 'neutra')}"] = counters.get(f"tom:{choice.get('tone', 'neutra')}", 0) + 1
    if auto:
        counters["sem_resposta"] = counters.get("sem_resposta", 0) + 1
    return entry


def respond(state: dict[str, Any], event_id: str, choice_id: str) -> dict[str, Any]:
    story = ensure_story_state(state)
    ev = next((p for p in story["pending"] if p["id"] == event_id), None)
    if ev is None:
        raise ValueError("Acontecimento não encontrado ou já resolvido.")
    return _resolve(state, ev, choice_id, date.fromisoformat(state["date"]), auto=False)


FAMILY_COOLDOWN_DAYS = 75  # a mesma família de acontecimento não volta antes disso (vale para variações de setor/estado)


CAREER_LEVEL = {"vereador": "legislativo", "deputado_estadual": "legislativo", "deputado_federal": "legislativo", "senador": "legislativo",
                "prefeito": "municipal", "governador": "estadual", "presidente": "federal"}
EXECUTIVE_EVENT_COST_CAP = 0.04   # um acontecimento custa no máximo 4% da reserva anual do cargo (carreira)


def _career_governance(state: dict[str, Any]) -> dict[str, Any] | None:
    """Dados de governo do cargo de carreira, quando o jogador exerce mandato que não é a Presidência."""
    career = state.get("career") or {}
    if career.get("mode") and career.get("phase") == "office" and career.get("office") != "presidente":
        return career.setdefault("governance", {})
    return None


def current_level(state: dict[str, Any]) -> str | None:
    """Nível em que o jogador atua agora; None quando não há acontecimentos (ex.: campanha de carreira)."""
    from .party_path import story_level
    level = story_level(state)
    if level:
        return level
    career = state.get("career") or {}
    if career.get("mode"):
        if career.get("phase") != "office":
            return None
        return CAREER_LEVEL.get(career.get("office"), None)
    if state.get("office_status") in {"former_president", "detained_after_failed_rupture"}:
        return None
    return state.get("story_level", "federal")


def _career_cost_mi(state: dict[str, Any], cost_bi: float) -> float:
    governance = _career_governance(state) or {}
    annual = float(governance.get("annual_budget_mi") or 0)
    if not cost_bi or annual <= 0:
        return 0.0
    return round(min(cost_bi * 1000, annual * EXECUTIVE_EVENT_COST_CAP), 2)


def _apply_career_effects(state: dict[str, Any], effects: dict[str, float], cost_mi: float) -> list[dict[str, Any]]:
    """No mandato de carreira, os efeitos caem sobre confiança, reputação, capital político e reserva do cargo."""
    career = state["career"]
    governance = career.setdefault("governance", {})
    deltas: list[dict[str, Any]] = []

    def bump(holder: dict[str, Any], field: str, amount: float, label: str, default: float = 50.0) -> None:
        if not amount:
            return
        before = float(holder.get(field, default))
        holder[field] = round(max(0.0, min(100.0, before + amount)), 2)
        if holder[field] != before:
            deltas.append({"key": field, "label": label, "delta": round(holder[field] - before, 2)})

    trust = capital = reputation = 0.0
    for key, value in effects.items():
        if key == "approval":
            trust += value * 1.2
        elif key == "integrity":
            reputation += value * 0.8
        elif key in ("congress_support", "governability"):
            capital += value
    bump(governance, "trust", round(trust, 2), "confiança do eleitorado")
    bump(governance, "political_capital", round(capital, 2), "capital político")
    bump(career, "reputation", round(reputation, 2), "reputação")
    if cost_mi:
        before = float(governance.get("budget_mi", 0))
        governance["budget_mi"] = round(max(0.0, before - cost_mi), 2)
        deltas.append({"key": "cost_mi", "label": "reserva do cargo (R$ mi)", "delta": round(governance["budget_mi"] - before, 2)})
    return deltas


def _eligible(state: dict[str, Any], day: date) -> list[tuple[str, float]]:
    story = ensure_story_state(state)
    level = current_level(state)
    families = story.setdefault("seen_family", {})
    pending_defs = {p["def"] for p in story["pending"]}
    out = []
    for def_id, definition in get_library().events.items():
        weight = float(definition.get("weight", 1.0))
        if weight <= 0 or level not in definition["levels"]:
            continue  # peso 0 = só entra por continuação
        last = story["seen"].get(def_id, {}).get("last")
        if last and (day - date.fromisoformat(last)).days < int(definition.get("cooldown", 120)):
            continue
        fam_last = families.get(definition.get("family", "base"))
        if fam_last and (day - date.fromisoformat(fam_last)).days < FAMILY_COOLDOWN_DAYS:
            continue
        if def_id in pending_defs:
            continue
        if story["last_tags"] and set(story["last_tags"]) & set(definition.get("tags", [])):
            weight *= 0.3  # evita repetir o mesmo assunto em sequência
        try:
            if not definition["when"](state):
                continue
        except Exception:
            continue  # um acontecimento com defeito nunca trava o dia
        out.append((def_id, weight))
    return out


def tick(state: dict[str, Any], before: date, after: date) -> list[str]:
    """Processa dias entre `before` (exclusivo) e `after` (inclusivo)."""
    story = ensure_story_state(state)
    if current_level(state) is None:
        return []
    messages: list[str] = []
    day = before
    while day < after:
        day += timedelta(days=1)
        # 1) prazos: vale a opção padrão. Só vencem acontecimentos que já estavam pendentes antes deste
        #    avanço: o que nasce durante o avanço só começa a contar prazo quando o controle volta ao jogador.
        for ev in list(story["pending"]):
            if ev["on"] > before.isoformat():
                continue
            if ev["expires"] and date.fromisoformat(ev["expires"]) < day:
                entry = _resolve(state, ev, ev["fallback"], day, auto=True)
                messages.append(f"Sem resposta no prazo: {ev['title']} (valeu a opção padrão).")
                del entry
        # 2) continuações agendadas
        due = [q for q in story["queue"] if date.fromisoformat(q["on"]) <= day]
        story["queue"] = [q for q in story["queue"] if q not in due]
        for item in due:
            if get_library().get(item["def"]):
                ev = _fire(state, item["def"], day)
                if ev:
                    messages.append(f"Acontecimento: {ev['title']}.")
        # 3) acontecimento novo, respeitando o ritmo
        if len(story["pending"]) >= MAX_PENDING:
            continue
        last = story["last_event"]
        if last and (day - date.fromisoformat(last)).days < MIN_GAP_DAYS:
            continue
        if _rand(state, day, "chance") >= BASE_DAILY_CHANCE:
            continue
        pool = _eligible(state, day)
        if not pool:
            continue
        total = sum(w for _, w in pool)
        pick = _rand(state, day, "pick") * total
        for def_id, weight in pool:
            pick -= weight
            if pick <= 0:
                ev = _fire(state, def_id, day)
                if ev:
                    messages.append(f"Acontecimento: {ev['title']}.")
                break
    # Acontecimentos criados neste avanço: o prazo conta a partir do dia em que o jogador retoma o controle.
    for ev in story["pending"]:
        if ev["on"] > before.isoformat() and ev["expires"]:
            ev["expires"] = (after + timedelta(days=EXPIRES_DAYS[ev["kind"]])).isoformat()
    return messages


def overview(state: dict[str, Any]) -> dict[str, Any]:
    story = ensure_story_state(state)
    today = date.fromisoformat(state["date"])
    pending = []
    for ev in story["pending"]:
        days_left = (date.fromisoformat(ev["expires"]) - today).days if ev["expires"] else None
        pending.append({**_public(ev), "days_left": days_left})
    return {"simulated": True, "pending": pending, "history": story["history"][:30],
            "profile": {k[4:]: v for k, v in story["counters"].items() if k.startswith("tom:")},
            "unanswered": story["counters"].get("sem_resposta", 0)}
