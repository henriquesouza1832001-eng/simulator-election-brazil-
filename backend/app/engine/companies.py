"""Empresas públicas e estratégicas: relação do governo, saúde da empresa, visitas, reuniões e política de controle.

Catálogo de instituições e empresas reais, só com atributos qualitativos (setor, sede, tipo de controle). Os
índices de saúde e de relação com o governo são do jogo (0 a 100), não dados financeiros. Compra e venda continuam
nas competências (privatizar, estatizar), que exigem lei; aqui ficam as decisões de gestão que o Executivo pode tomar.
"""
from __future__ import annotations

import hashlib
from datetime import date, timedelta
from typing import Any

from . import consequences, ledger

CATALOG: dict[str, dict[str, Any]] = {
    "petrobras": {"name": "Petrobras", "sector": "Petróleo e gás", "hq": "RJ", "level": "federal", "control": "mista, controle da União", "strategic": True,
                  "note": "O monopólio da União sobre petróleo (CF art. 177) é exercido por contratação; a venda do controle exige lei.", "privatize_key": "Petrobras"},
    "bb": {"name": "Banco do Brasil", "sector": "Banco", "hq": "DF", "level": "federal", "control": "mista, controle da União", "strategic": True,
           "note": "Banco múltiplo com papel no crédito rural e na política de crédito.", "privatize_key": "Banco do Brasil"},
    "caixa": {"name": "Caixa Econômica Federal", "sector": "Banco", "hq": "DF", "level": "federal", "control": "empresa pública", "strategic": True,
              "note": "Operador de habitação, FGTS e programas sociais.", "privatize_key": "Caixa Econômica Federal"},
    "bndes": {"name": "BNDES", "sector": "Banco de desenvolvimento", "hq": "RJ", "level": "federal", "control": "empresa pública", "strategic": True,
              "note": "Financia investimento e infraestrutura.", "privatize_key": "BNDES"},
    "correios": {"name": "Correios", "sector": "Logística postal", "hq": "DF", "level": "federal", "control": "empresa pública", "strategic": False,
                 "note": "Serviço postal é competência da União (CF art. 21, X).", "privatize_key": "Correios"},
    "eletronuclear": {"name": "Eletronuclear", "sector": "Energia nuclear", "hq": "RJ", "level": "federal", "control": "subsidiária estatal", "strategic": True,
                      "note": "Atividade nuclear só para fins pacíficos e com aprovação do Congresso (CF art. 21, XXIII).", "privatize_key": "Eletronuclear"},
    "eletrobras": {"name": "Eletrobras", "sector": "Energia elétrica", "hq": "RJ", "level": "federal", "control": "privada, União minoritária", "strategic": True,
                   "note": "Privatizada em 2022; a União mantém participação e limite de voto.", "privatize_key": None},
    "embraer": {"name": "Embraer", "sector": "Aeronáutica", "hq": "SP", "level": "federal", "control": "privada, ação de classe especial da União", "strategic": True,
                "note": "A União tem poder de veto sobre decisões estratégicas (ação de classe especial).", "privatize_key": None},
    "vale": {"name": "Vale", "sector": "Mineração", "hq": "RJ", "level": "federal", "control": "privada", "strategic": True,
             "note": "Privatizada em 1997; minerais são bens da União e lavra depende de concessão (CF art. 176).", "privatize_key": None},
    "telebras": {"name": "Telebras", "sector": "Telecomunicações", "hq": "DF", "level": "federal", "control": "mista, controle da União", "strategic": False,
                 "note": "Opera infraestrutura de conectividade do governo.", "privatize_key": None},
    "cemig": {"name": "Cemig", "sector": "Energia elétrica", "hq": "MG", "level": "estadual", "control": "mista, controle do estado de Minas Gerais", "strategic": False,
              "note": "Privatizar estatal estadual exige lei da Assembleia (e, em MG, referendo previsto na constituição estadual).", "privatize_key": None},
    "sabesp": {"name": "Sabesp", "sector": "Saneamento", "hq": "SP", "level": "estadual", "control": "mista", "strategic": False,
               "note": "Saneamento é regulado pelo Marco Legal (Lei 14.026/2020).", "privatize_key": None},
}

ACTIONS = {
    "visit": {"label": "Visitar a empresa", "who": "all", "cooldown": 45, "text": "Agenda pública na sede ou em uma unidade; melhora a relação e pode render anúncio de investimento.", "options": []},
    "meeting": {"label": "Reunião com a diretoria", "who": "all", "cooldown": 30, "text": "Negocie uma prioridade com a diretoria.",
                "options": ["Pedir investimento", "Pedir contenção de preços", "Pedir mais empregos locais"]},
    "dividends": {"label": "Política de dividendos", "who": "controlled", "cooldown": 90, "text": "Quanto do lucro volta ao Tesouro e quanto fica na empresa.",
                  "options": ["Pedir mais dividendos", "Reter lucros para investir"]},
    "prices": {"label": "Política de preços", "who": "petrobras", "cooldown": 60, "text": "Segurar ou alinhar os preços de combustíveis ao mercado.",
               "options": ["Segurar preços", "Alinhar ao mercado"]},
    "leadership": {"label": "Escolher o comando", "who": "controlled", "cooldown": 180, "text": "Trocar a presidência: técnico independente ou aliado político.",
                   "options": ["Nome técnico independente", "Aliado político"]},
}
# (opção) -> efeitos {relation, health, metric deltas}
EFFECTS: dict[str, dict[str, float]] = {
    "visit": {"relation": 6.0, "approval": 0.3},
    "Pedir investimento": {"relation": 2.0, "health": -1.0, "gdp_growth": 0.02},
    "Pedir contenção de preços": {"relation": -4.0, "health": -3.0, "inflation": -0.08, "approval": 0.2},
    "Pedir mais empregos locais": {"relation": -2.0, "health": -1.0, "unemployment": -0.03, "approval": 0.2},
    "Pedir mais dividendos": {"relation": -5.0, "health": -3.0, "primary_balance": 0.03},
    "Reter lucros para investir": {"relation": 3.0, "health": 3.0, "primary_balance": -0.02},
    "Segurar preços": {"relation": -6.0, "health": -6.0, "inflation": -0.12, "approval": 0.6},
    "Alinhar ao mercado": {"relation": 4.0, "health": 4.0, "inflation": 0.1, "approval": -0.5},
    "Nome técnico independente": {"relation": 4.0, "health": 3.0, "integrity": 0.5, "congress_support": -0.4},
    "Aliado político": {"relation": 1.0, "health": -2.0, "integrity": -0.8, "congress_support": 0.6},
}


def _roll(seed: str) -> float:
    return int(hashlib.sha256(seed.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF


def ensure(state: dict[str, Any]) -> dict[str, Any]:
    comp = state.setdefault("company_state", {})
    for key, c in CATALOG.items():
        comp.setdefault(key, {"control": c["control"], "health": 60.0 + 20 * _roll(f"{state.get('campaign_seed', 1)}:{key}:h"), "relation": 50.0, "last": {}, "last_crisis": None})
    from .powers import structure
    for key, c in CATALOG.items():
        if c.get("privatize_key") and structure(state)["companies"].get(c["privatize_key"]) == "privada" and not comp[key]["control"].startswith("privada"):
            comp[key]["control"] = "privada (vendida pelo governo)"
    return comp


def _office(state: dict[str, Any]) -> tuple[str, bool]:
    from .career import is_career_governing
    career = state.get("career") or {}
    if career.get("mode"):
        return str(career.get("office")), bool(is_career_governing(career, date.fromisoformat(state["date"])))
    return "presidente", state.get("office_status", "incumbent") == "incumbent"


def _controlled(entry: dict[str, Any]) -> bool:
    return not entry["control"].startswith("privada")


def _scope_ok(state: dict[str, Any], key: str) -> str | None:
    office, governing = _office(state)
    c = CATALOG[key]
    if not governing:
        return "Disponível quando você estiver no exercício do cargo."
    if office == "presidente":
        return None
    if office == "governador" and c["level"] == "estadual" and c["hq"] == (state.get("career") or {}).get("state_code"):
        return None
    return "Esta empresa não está sob a competência do seu cargo."


def overview(state: dict[str, Any]) -> dict[str, Any]:
    comp = ensure(state)
    today = date.fromisoformat(state["date"])
    items = []
    for key, c in CATALOG.items():
        e = comp[key]
        scope = _scope_ok(state, key)
        acts = []
        for akey, a in ACTIONS.items():
            reason = scope
            if not reason:
                if a["who"] == "controlled" and not _controlled(e):
                    reason = "A empresa não é controlada pelo governo."
                elif a["who"] == "petrobras" and key != "petrobras":
                    continue
                elif (last := e["last"].get(akey)) and (today - date.fromisoformat(last)).days < a["cooldown"]:
                    reason = f"Disponível em {a['cooldown'] - (today - date.fromisoformat(last)).days} dia(s)."
            acts.append({"key": akey, "label": a["label"], "text": a["text"], "options": a["options"], "available": reason is None, "reason": reason})
        items.append({"id": key, **{k: c[k] for k in ("name", "sector", "hq", "level", "strategic", "note")}, "control": e["control"], "controlled": _controlled(e),
                      "health": round(e["health"], 1), "relation": round(e["relation"], 1), "actions": acts,
                      "can_privatize": bool(c.get("privatize_key")) and _controlled(e) and c["level"] == "federal", "privatize_key": c.get("privatize_key")})
    return {"companies": items, "note": "Saúde e relação são índices do jogo. A venda ou compra de empresas exige lei e fica na aba Competências."}


def act(state: dict[str, Any], key: str, action: str, option: str | None = None) -> dict[str, Any]:
    if key not in CATALOG or action not in ACTIONS:
        raise ValueError("Empresa ou ação desconhecida.")
    spec = ACTIONS[action]
    comp = ensure(state)
    e = comp[key]
    reason = _scope_ok(state, key)
    if reason:
        raise PermissionError(reason)
    if spec["who"] == "controlled" and not _controlled(e):
        raise PermissionError("A empresa não é controlada pelo governo.")
    if spec["who"] == "petrobras" and key != "petrobras":
        raise PermissionError("Ação exclusiva da Petrobras.")
    today = date.fromisoformat(state["date"])
    last = e["last"].get(action)
    if last and (today - date.fromisoformat(last)).days < spec["cooldown"]:
        raise RuntimeError(f"Disponível em {spec['cooldown'] - (today - date.fromisoformat(last)).days} dia(s).")
    if spec["options"]:
        if option not in spec["options"]:
            raise ValueError("Escolha uma das opções.")
        eff = dict(EFFECTS[option])
    else:
        option, eff = None, dict(EFFECTS["visit"])
    relation, health = eff.pop("relation", 0.0), eff.pop("health", 0.0)
    e["relation"] = round(max(0.0, min(100.0, e["relation"] + relation)), 2)
    e["health"] = round(max(0.0, min(100.0, e["health"] + health)), 2)
    e["last"][action] = state["date"]
    _apply_metrics(state, eff)
    title = f"{CATALOG[key]['name']}: {spec['label'].lower()}" + (f" — {option}" if option else "")
    forecast = {**eff, "relação": relation, "saúde da empresa": health}
    entry = ledger.record(state, "empresa", title, forecast, forecast, status="feito")
    msg = None
    if action == "visit" and _roll(f"{state.get('campaign_seed', 1)}:{key}:{state['date']}:inv") < 0.35 + 0.004 * e["relation"]:
        _apply_metrics(state, {"gdp_growth": 0.02, "unemployment": -0.02})
        msg = f"{CATALOG[key]['name']} anunciou novo investimento após a visita (simulação)."
        consequences._post(consequences._book(state), state, {"id": f"emp-{key}-{state['date']}", "kind": "mercado", "headline": msg, "body": "O anúncio melhora a expectativa de emprego e atividade, na simulação.", "tone": "positivo", "action_id": f"empresa_{key}"})
    consequences.schedule(state, action_id=f"empresa_{action}", title=title, domain="empresas", effects=eff, ledger_id=entry["id"], local=_office(state)[0] != "presidente")
    return {"entry": entry, "company": next(c for c in overview(state)["companies"] if c["id"] == key), "announcement": msg}


def _apply_metrics(state: dict[str, Any], eff: dict[str, float]) -> None:
    from .powers import METRIC_RANGES, _bump
    from .fiscal import record_policy_balance_delta
    career = state.get("career") or {}
    local = career.get("mode") and career.get("office") != "presidente"
    for k, v in eff.items():
        if local:
            if k == "approval":
                gov = career.setdefault("governance", {})
                gov["trust"] = round(max(0.0, min(100.0, float(gov.get("trust", 50)) + v)), 2)
        elif k == "primary_balance":
            record_policy_balance_delta(state, v)
        elif k in METRIC_RANGES:
            _bump(state, k, v)


def tick(state: dict[str, Any], before: date, after: date) -> list[str]:
    comp = ensure(state)
    msgs: list[str] = []
    growth = float(state.get("metrics", {}).get("gdp_growth", 2.0))
    month = after.isoformat()[:7]
    if state.setdefault("company_month", None) == month:
        return msgs
    state["company_month"] = month
    for key, e in comp.items():
        e["health"] = round(max(0.0, min(100.0, e["health"] + (growth - 2.0) * 0.4 + (60 - e["health"]) * 0.01)), 2)
        e["relation"] = round(e["relation"] + (50 - e["relation"]) * 0.02, 2)
        if e["health"] < 30 and _controlled(e) and (not e.get("last_crisis") or (after - date.fromisoformat(e["last_crisis"])).days > 180) and _scope_ok(state, key) is None:
            e["last_crisis"] = after.isoformat()
            name = CATALOG[key]["name"]
            consequences.open_crisis(state, crisis_id=f"emp-{key}-{month}", action_id=f"empresa_{key}", title=f"{name} em dificuldade financeira",
                                     text="Os resultados caíram e a diretoria pede apoio do controlador.", deadline_days=45, today=after,
                                     options=[{"id": "capitalizar", "label": "Capitalizar a empresa com recursos do Tesouro", "effects": {"primary_balance": -0.05, "approval": 0.2}},
                                              {"id": "reestruturar", "label": "Exigir plano de reestruturação", "effects": {"approval": -0.3, "integrity": 0.5}},
                                              {"id": "aguardar", "label": "Aguardar", "effects": {"approval": -1.0, "gdp_growth": -0.03}}])
            e["health"] = 35.0
            msgs.append(f"{name} entrou em dificuldade financeira. Responda na aba Imprensa.")
    return msgs
