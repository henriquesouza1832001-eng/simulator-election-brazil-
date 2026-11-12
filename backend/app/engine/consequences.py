"""Reações persistentes e crises encadeadas: toda decisão relevante gera notícias, reações de bancadas e, às vezes, uma crise.

- Imprensa e mercado reagem em dias ou semanas; bancadas do Congresso reagem conforme a posição ideológica do partido.
- Algumas decisões geram uma crise posterior (greve, protesto, crise institucional) com opções de resposta e prazo.
  Se o jogador não responde, vale a pior opção.
Tudo é determinístico pela semente da partida; textos usam só fatos do motor (título, direção dos efeitos, nomes de partidos).
"""
from __future__ import annotations

import hashlib
from datetime import date, timedelta
from typing import Any

from . import ledger
from .legislature import PARTIES

FEED_LIMIT = 120
# posição política de cada ação (-1 esquerda … +1 direita); as demais são neutras
LEAN: dict[str, float] = {
    "seg_armas_afrouxar": 0.8, "seg_armas_restringir": -0.7, "seg_desmilitarizar": -0.6, "empresa_privatizar": 0.8, "empresa_estatizar": -0.8,
    "eco_teto": 0.7, "eco_previdencia": 0.5, "eco_bolsa": -0.8, "eco_salario_minimo": -0.5, "eco_desoneracao": 0.5, "eco_reforma_tributaria": 0.1,
    "infra_conceder": 0.6, "defesa_glo": 0.5, "defesa_intervencao": 0.4, "ext_brics_sair": 0.4, "ext_otan": 0.5, "bc_revogar_autonomia": -0.5,
    "bc_restaurar_autonomia": 0.4, "empresa_monopolio_petroleo": 0.5, "ext_acordo_comercial": 0.4, "p_iptu": -0.2, "p_reajuste": -0.4, "p_reduzir_folha": 0.5,
}
TONE_WORDS = {"up": "avança", "down": "recua"}
BACKLASH: dict[str, dict[str, Any]] = {
    "empresa_privatizar": {"p": 0.55, "delay": (25, 70), "title": "Greve em empresa privatizada", "text": "Sindicatos paralisam parte das operações em protesto contra a venda.",
        "options": [{"id": "negociar", "label": "Abrir negociação com os sindicatos", "effects": {"approval": 0.6, "primary_balance": -0.02}},
                    {"id": "reprimir", "label": "Manter a venda e endurecer", "effects": {"approval": -1.5, "institutional_trust": -0.8}},
                    {"id": "ignorar", "label": "Aguardar", "effects": {"approval": -2.0, "gdp_growth": -0.03}}]},
    "seg_armas_afrouxar": {"p": 0.45, "delay": (30, 90), "title": "Debate sobre armas após ocorrência violenta", "text": "Um caso de grande repercussão reabre a discussão sobre o acesso a armas.",
        "options": [{"id": "revisar", "label": "Revisar parte das regras", "effects": {"approval": 0.5, "institutional_trust": 0.5}},
                    {"id": "manter", "label": "Manter a política", "effects": {"approval": -1.0}},
                    {"id": "ignorar", "label": "Aguardar", "effects": {"approval": -1.8, "institutional_trust": -0.5}}]},
    "eco_confisco": {"p": 0.7, "delay": (15, 45), "title": "Desabastecimento e protestos", "text": "Prateleiras vazias e filas aumentam a pressão sobre o governo.",
        "options": [{"id": "liberar", "label": "Liberar os preços gradualmente", "effects": {"approval": -0.5, "inflation": 0.3}},
                    {"id": "fiscalizar", "label": "Reforçar a fiscalização", "effects": {"approval": -1.5, "integrity": -0.5}},
                    {"id": "ignorar", "label": "Aguardar", "effects": {"approval": -3.0, "gdp_growth": -0.1}}]},
    "reg_forma_governo": {"p": 0.8, "delay": (20, 60), "title": "Crise institucional", "text": "Parte do Legislativo e do Judiciário questiona a legitimidade da mudança.",
        "options": [{"id": "dialogar", "label": "Convocar diálogo entre poderes", "effects": {"institutional_trust": 1.5, "governability": 1}},
                    {"id": "enfrentar", "label": "Enfrentar publicamente", "effects": {"institutional_trust": -3, "approval": -1}},
                    {"id": "ignorar", "label": "Aguardar", "effects": {"institutional_trust": -4, "governability": -2}}]},
    "defesa_intervencao": {"p": 0.4, "delay": (30, 80), "title": "Questionamento sobre a intervenção", "text": "Entidades pedem prestação de contas sobre a intervenção federal.",
        "options": [{"id": "relatorio", "label": "Publicar relatório de resultados", "effects": {"institutional_trust": 0.8}},
                    {"id": "ignorar", "label": "Aguardar", "effects": {"institutional_trust": -1.2, "approval": -0.8}}]},
    "defesa_glo": {"p": 0.35, "delay": (30, 90), "title": "Denúncia de excesso em operação", "text": "Organizações de direitos humanos apontam excessos em uma operação.",
        "options": [{"id": "apurar", "label": "Determinar apuração independente", "effects": {"institutional_trust": 1.0, "approval": -0.3}},
                    {"id": "ignorar", "label": "Aguardar", "effects": {"institutional_trust": -1.5, "approval": -0.8}}]},
    "bc_revogar_autonomia": {"p": 0.6, "delay": (10, 40), "title": "Mercado reage à perda de autonomia do BC", "text": "Câmbio e juros longos sobem com a leitura de menor credibilidade.",
        "options": [{"id": "sinalizar", "label": "Sinalizar compromisso fiscal e com a meta", "effects": {"institutional_trust": 1.0, "inflation": -0.05}},
                    {"id": "ignorar", "label": "Aguardar", "effects": {"institutional_trust": -2.0, "inflation": 0.2, "gdp_growth": -0.05}}]},
    "p_iptu": {"p": 0.5, "delay": (10, 40), "title": "Protesto contra o aumento do IPTU", "text": "Moradores e associações de bairro protestam diante da prefeitura.",
        "options": [{"id": "isencao", "label": "Ampliar isenções para famílias de baixa renda", "effects": {"trust": 1.5}},
                    {"id": "manter", "label": "Manter o reajuste", "effects": {"trust": -1.0}},
                    {"id": "ignorar", "label": "Aguardar", "effects": {"trust": -2.0}}]},
}


def _book(state: dict[str, Any]) -> dict[str, Any]:
    c = state.setdefault("consequences", {})
    c.setdefault("scheduled", [])
    c.setdefault("feed", [])
    c.setdefault("pending", [])
    return c


def _roll(seed: str) -> float:
    return int(hashlib.sha256(seed.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF


def _direction(effects: dict[str, float]) -> int:
    good = sum(v for k, v in effects.items() if k in {"approval", "gdp_growth", "institutional_trust", "trust", "mobilidade", "seguranca", "saude_atencao"})
    bad = sum(v for k, v in effects.items() if k in {"inflation", "unemployment"})
    return 1 if good - bad >= 0 else -1


def _opposing_parties(lean: float) -> list[str]:
    """Bancadas que reagem contra: partidos do lado oposto ao da ação (distância ideológica alta)."""
    return [p["id"] for p in sorted(PARTIES, key=lambda p: -abs(p["ideology"] - lean)) if p["seats"] >= 10 and abs(p["ideology"] - lean) > 0.9][:2]


def _supporting_parties(lean: float) -> list[str]:
    return [p["id"] for p in sorted(PARTIES, key=lambda p: abs(p["ideology"] - lean)) if p["seats"] >= 10][:2]


def schedule(state: dict[str, Any], *, action_id: str, title: str, domain: str, effects: dict[str, float], source: str = "presidencia",
             ledger_id: str | None = None, local: bool = False) -> None:
    book = _book(state)
    today = date.fromisoformat(state["date"])
    seed = f"{state.get('campaign_seed', 1)}:{action_id}:{state['date']}"
    direction = _direction(effects)
    lean = LEAN.get(action_id, 0.0)
    items = [{"kind": "imprensa", "after": 3 + int(_roll(seed + "p") * 10),
              "headline": f"{'Governo' if not local else 'Gestão'} {TONE_WORDS['up'] if direction > 0 else TONE_WORDS['down']} com a decisão: {title}",
              "body": "Jornais e portais repercutem a decisão, na simulação. A avaliação de especialistas varia conforme o campo político.", "tone": "positivo" if direction > 0 else "negativo",
              "effects": {"approval": 0.3 * direction} if not local else {"trust": 0.3 * direction}}]
    if not local and abs(lean) >= 0.3:
        for party in _opposing_parties(lean):
            items.append({"kind": "congresso", "after": 6 + int(_roll(seed + party) * 20), "headline": f"Bancada do {party} critica: {title}",
                          "body": f"O {party} anuncia oposição à medida, na simulação, e pode dificultar votações ligadas ao tema.", "tone": "negativo", "effects": {"congress_support": -0.6}})
        for party in _supporting_parties(lean)[:1]:
            items.append({"kind": "congresso", "after": 8 + int(_roll(seed + party + "s") * 15), "headline": f"Bancada do {party} apoia: {title}",
                          "body": f"O {party} defende a medida, na simulação, e promete ajudar na tramitação.", "tone": "positivo", "effects": {"congress_support": 0.5}})
    if not local and domain in {"economia", "banco", "empresas", "exterior"}:
        items.append({"kind": "mercado", "after": 2 + int(_roll(seed + "m") * 6), "headline": f"Mercado reage a: {title}",
                      "body": "Investidores reavaliam risco e câmbio, na simulação, conforme a credibilidade da medida.", "tone": "positivo" if direction > 0 else "negativo",
                      "effects": {"institutional_trust": 0.4 * direction}})
    for it in items:
        days = it.pop("after")
        book["scheduled"].append({**it, "id": f"re-{len(book['scheduled']) + len(book['feed']) + 1}-{action_id}", "action_id": action_id,
                                  "due": (today + timedelta(days=days)).isoformat(), "ledger_id": ledger_id})
    spec = BACKLASH.get(action_id)
    if spec and _roll(seed + "crise") < spec["p"]:
        lo, hi = spec["delay"]
        book["scheduled"].append({"kind": "crise", "id": f"cr-{len(book['scheduled']) + len(book['feed']) + 1}-{action_id}", "action_id": action_id, "ledger_id": ledger_id,
                                  "due": (today + timedelta(days=lo + int(_roll(seed + "d") * (hi - lo)))).isoformat()})


def _apply(state: dict[str, Any], effects: dict[str, float]) -> None:
    from .powers import METRIC_RANGES, _bump
    from .fiscal import record_policy_balance_delta
    career = state.get("career") or {}
    local = career.get("mode") and career.get("office") != "presidente"
    for key, value in effects.items():
        if local:
            gov = career.setdefault("governance", {})
            if key in {"trust", "approval"}:
                gov["trust"] = round(max(0.0, min(100.0, float(gov.get("trust", 50)) + value)), 2)
            continue
        if key == "primary_balance":
            record_policy_balance_delta(state, value)
        elif key in METRIC_RANGES:
            _bump(state, key, value)


def _post(book: dict[str, Any], state: dict[str, Any], item: dict[str, Any]) -> None:
    book["feed"].insert(0, {k: item[k] for k in ("id", "kind", "headline", "body", "tone", "action_id") if k in item} | {"date": state["date"]})
    del book["feed"][FEED_LIMIT:]


def open_crisis(state: dict[str, Any], *, crisis_id: str, action_id: str, title: str, text: str, options: list[dict[str, Any]],
                deadline_days: int = 30, regulator: str | None = None, ledger_id: str | None = None, today: date | None = None) -> dict[str, Any]:
    """Abre uma decisão pendente. As opções guardam seus efeitos; a última é a que vale se o prazo vencer."""
    book = _book(state)
    after = today or date.fromisoformat(state["date"])
    crisis = {"id": crisis_id, "action_id": action_id, "title": title, "text": text, "regulator": regulator,
              "deadline": (after + timedelta(days=deadline_days)).isoformat(), "ledger_id": ledger_id,
              "options": [{"id": o["id"], "label": o["label"], "effects": o["effects"], "note": o.get("note"), "hook": o.get("hook")} for o in options]}
    book["pending"].append(crisis)
    _post(book, state, {"id": crisis_id, "kind": "crise" if not regulator else "regulador", "headline": title, "body": text, "tone": "negativo", "action_id": action_id})
    return crisis


def tick(state: dict[str, Any], before: date, after: date) -> list[str]:
    book = _book(state)
    messages: list[str] = []
    keep = []
    for item in book["scheduled"]:
        due = date.fromisoformat(item["due"])
        if due > after:
            keep.append(item)
            continue
        if item["kind"] == "crise":
            spec = BACKLASH[item["action_id"]]
            open_crisis(state, crisis_id=item["id"], action_id=item["action_id"], title=spec["title"], text=spec["text"], options=spec["options"], ledger_id=item.get("ledger_id"), today=after)
            messages.append(f"Crise: {spec['title']}. Responda na aba Imprensa e reações.")
        else:
            _apply(state, item.get("effects", {}))
            _post(book, state, item)
    book["scheduled"] = keep
    # crises sem resposta expiram com a pior opção
    for crisis in list(book["pending"]):
        if date.fromisoformat(crisis["deadline"]) <= after:
            worst = crisis["options"][-1]
            _apply(state, worst["effects"])
            book["pending"].remove(crisis)
            _post(book, state, {"id": crisis["id"] + "-exp", "kind": "crise", "headline": f"{crisis['title']}: sem resposta do governo", "body": "O prazo passou e a crise se agravou, na simulação.", "tone": "negativo", "action_id": crisis["action_id"]})
            ledger.record(state, "crise", f"{crisis['title']} (sem resposta)", {}, {k: v for k, v in worst["effects"].items()}, status="agravada")
    return messages


def respond(state: dict[str, Any], crisis_id: str, option_id: str) -> dict[str, Any]:
    book = _book(state)
    crisis = next((c for c in book["pending"] if c["id"] == crisis_id), None)
    if crisis is None:
        raise ValueError("Crise não encontrada ou já resolvida.")
    option = next((o for o in crisis["options"] if o["id"] == option_id), None)
    if option is None:
        raise ValueError("Opção inválida.")
    _apply(state, option["effects"])
    hook = option.get("hook") or {}
    if hook.get("veto"):
        from . import congress_agenda
        congress_agenda.schedule_override(state, hook["veto"], hook["scope"], hook.get("author", ""))
    if hook.get("stf_risk_factor") and hook.get("case"):
        from . import regulators
        regulators.adjust_case_risk(state, hook["case"], float(hook["stf_risk_factor"]))
    book["pending"].remove(crisis)
    _post(book, state, {"id": crisis_id + "-res", "kind": "resposta", "headline": f"Resposta do governo: {option['label']}", "body": crisis["title"], "tone": "neutro", "action_id": crisis["action_id"]})
    entry = ledger.record(state, "crise", f"{crisis['title']}: {option['label']}", {}, dict(option["effects"]), status="respondida")
    return {"entry": entry, "effects": option["effects"]}


def overview(state: dict[str, Any]) -> dict[str, Any]:
    book = _book(state)
    return {"feed": book["feed"][:40], "pending": book["pending"], "scheduled": len(book["scheduled"])}
