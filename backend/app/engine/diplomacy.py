"""Bilateral relations, official visits and simulated international agenda."""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any

COUNTRIES: dict[str, dict[str, Any]] = {
    "ARG": {"name": "Argentina", "region": "America do Sul", "relation": 62, "trade_weight": 6, "travel_cost_bi": .045, "focus": "comercio e energia"},
    "CHL": {"name": "Chile", "region": "America do Sul", "relation": 61, "trade_weight": 4, "travel_cost_bi": .05, "focus": "mineracao e energia limpa"},
    "COL": {"name": "Colombia", "region": "America do Sul", "relation": 57, "trade_weight": 3, "travel_cost_bi": .055, "focus": "seguranca e Amazonia"},
    "URY": {"name": "Uruguai", "region": "America do Sul", "relation": 64, "trade_weight": 2, "travel_cost_bi": .045, "focus": "Mercosul e fronteira"},
    "USA": {"name": "Estados Unidos", "region": "America do Norte", "relation": 54, "trade_weight": 12, "travel_cost_bi": .18, "focus": "comercio, tecnologia e defesa"},
    "MEX": {"name": "Mexico", "region": "America do Norte", "relation": 53, "trade_weight": 4, "travel_cost_bi": .16, "focus": "industria e cadeias produtivas"},
    "CHN": {"name": "China", "region": "Asia", "relation": 64, "trade_weight": 22, "travel_cost_bi": .23, "focus": "comercio, infraestrutura e investimento"},
    "IND": {"name": "India", "region": "Asia", "relation": 56, "trade_weight": 3, "travel_cost_bi": .22, "focus": "tecnologia, saude e comercio"},
    "JPN": {"name": "Japao", "region": "Asia", "relation": 67, "trade_weight": 3, "travel_cost_bi": .24, "focus": "tecnologia e transicao energetica"},
    "DEU": {"name": "Alemanha", "region": "Europa", "relation": 63, "trade_weight": 5, "travel_cost_bi": .16, "focus": "industria e financiamento"},
    "FRA": {"name": "Franca", "region": "Europa", "relation": 58, "trade_weight": 3, "travel_cost_bi": .16, "focus": "clima, ciencia e comercio"},
    "PRT": {"name": "Portugal", "region": "Europa", "relation": 68, "trade_weight": 2, "travel_cost_bi": .15, "focus": "mobilidade, servicos e lingua"},
    "ZAF": {"name": "Africa do Sul", "region": "Africa", "relation": 59, "trade_weight": 2, "travel_cost_bi": .17, "focus": "BRICS, energia e comercio"},
    "AGO": {"name": "Angola", "region": "Africa", "relation": 66, "trade_weight": 1, "travel_cost_bi": .18, "focus": "cooperacao e infraestrutura"},
    "TUR": {"name": "Turquia", "region": "Mediterraneo", "relation": 48, "trade_weight": 2, "travel_cost_bi": .19, "focus": "alimentos, industria e logistica"},
    "VEN": {"name": "Venezuela", "region": "America do Sul", "relation": 38, "trade_weight": 1, "travel_cost_bi": .06, "focus": "fronteira e cooperacao consular"},
}

AGENDAS = {"trade": "Comercio e investimento", "climate": "Clima e energia", "science": "Ciencia e tecnologia", "security": "Seguranca e fronteiras"}

INTERNATIONAL_EVENTS = [
    {"id": "mercosur-eu-2027", "date": "2027-03-22", "name": "Rodada Mercosul-Uniao Europeia", "place": "Brasilia", "kind": "trade", "cost_bi": .08,
     "description": "Agenda simulada de facilitacao comercial e cadeias produtivas."},
    {"id": "climate-finance-2027", "date": "2027-06-05", "name": "Forum de Financiamento Climatico", "place": "Brasilia", "kind": "climate", "cost_bi": .06,
     "description": "Evento ficticio sobre adaptacao, financiamento e protecao de cidades."},
    {"id": "cop30-legacy-2027", "date": "2027-11-10", "name": "Acompanhamento do legado da COP30", "place": "Belem", "kind": "climate", "cost_bi": .10,
     "description": "Evento simulado, dois anos apos a COP30, para acompanhar financiamento e compromissos climaticos."},
    {"id": "un-assembly-2028", "date": "2028-09-20", "name": "Semana de Alto Nivel da ONU", "place": "Nova York", "kind": "multilateral", "cost_bi": .16,
     "description": "Agenda multilateral simulada para encontros bilaterais e coordenacao internacional."},
    {"id": "climate-summit-2029", "date": "2029-11-12", "name": "Cupula Global do Clima", "place": "Internacional", "kind": "climate", "cost_bi": .12,
     "description": "Cupula ficticia do calendario do jogo; nao representa uma conferencia oficial."},
]


def ensure_diplomacy_state(state: dict[str, Any]) -> dict[str, Any]:
    diplomacy = state.setdefault("diplomacy", {})
    saved = diplomacy.setdefault("countries", {})
    for code, country in COUNTRIES.items():
        saved.setdefault(code, {"relation": country["relation"], "trade_confidence": 50, "last_visit": None,
                                "focus": country["focus"], "region": country["region"], "trade_weight": country["trade_weight"]})
    diplomacy.setdefault("last_visit", None)
    diplomacy.setdefault("visit_log", [])
    diplomacy.setdefault("events", [{**event, "status": "upcoming"} for event in INTERNATIONAL_EVENTS])
    diplomacy.setdefault("multilateral_influence", 50.0)
    operating = state.setdefault("budget", {}).setdefault("operating", {})
    operating.setdefault("spent_by_year", {})
    return diplomacy


def _days_until_visit(state: dict[str, Any], diplomacy: dict[str, Any]) -> int:
    last = diplomacy.get("last_visit")
    return max(0, 30 - (date.fromisoformat(state["date"]) - date.fromisoformat(last)).days) if last else 0


def diplomacy_overview(state: dict[str, Any]) -> dict[str, Any]:
    diplomacy = ensure_diplomacy_state(state)
    today = date.fromisoformat(state["date"])
    countries = [{"code": code, **config, **diplomacy["countries"][code]} for code, config in COUNTRIES.items()]
    events = [{**event, "days_until": (date.fromisoformat(event["date"]) - today).days}
              for event in diplomacy["events"] if event.get("status") == "upcoming"
              and date.fromisoformat(event["date"]) + timedelta(days=30) >= today]
    relations = [float(country["relation"]) for country in diplomacy["countries"].values()]
    operating = state["budget"]["operating"]
    travel = operating["lines"]["official_travel"]
    ceiling = float(travel["annual_cost_bi"]) * (1 - float(operating.get("travel_cut_pct", 0)) / 100)
    spent = float(operating["spent_by_year"].get(str(today.year), 0))
    return {"countries": countries, "events": events, "visit_log": diplomacy["visit_log"][:12],
            "average_relation": round(sum(relations) / len(relations), 1) if relations else 0,
            "multilateral_influence": round(float(diplomacy["multilateral_influence"]), 1),
            "agendas": AGENDAS, "days_until_visit": _days_until_visit(state, diplomacy),
            "travel_spent_bi": round(spent, 4), "travel_remaining_bi": round(max(0, ceiling - spent), 4)}


def _spend_travel(state: dict[str, Any], amount_bi: float) -> None:
    operating = state["budget"]["operating"]
    year = int(state["date"][:4])
    spent_by_year = operating.setdefault("spent_by_year", {})
    spent = float(spent_by_year.get(str(year), 0))
    line = operating["lines"]["official_travel"]
    ceiling = float(line["annual_cost_bi"]) * (1 - float(operating.get("travel_cut_pct", 0)) / 100)
    if spent + amount_bi > ceiling + 1e-9:
        raise ValueError("A verba anual de viagens nao cobre esta agenda.")
    spent_by_year[str(year)] = round(spent + amount_bi, 4)
    # Travel is charged against the annual operating line already in primary spending.


def visit_country(state: dict[str, Any], country_code: str, agenda: str) -> dict[str, Any]:
    diplomacy = ensure_diplomacy_state(state)
    code = country_code.upper()
    if code not in COUNTRIES:
        raise ValueError("Escolha um pais disponivel na agenda diplomatica.")
    if agenda not in AGENDAS:
        raise ValueError("Escolha uma pauta diplomatica valida.")
    wait = _days_until_visit(state, diplomacy)
    if wait:
        raise ValueError(f"A proxima visita oficial pode ser marcada em {wait} dia(s).")
    bilateral = diplomacy["countries"][code]
    today = date.fromisoformat(state["date"])
    last = bilateral.get("last_visit")
    if last and (today - date.fromisoformat(last)).days < 180:
        raise ValueError("Esta visita bilateral ocorreu nos ultimos seis meses.")
    config = COUNTRIES[code]
    cost = float(config["travel_cost_bi"])
    _spend_travel(state, cost)
    gain = {"trade": 4, "climate": 3, "science": 3, "security": 4}[agenda]
    bilateral["relation"] = min(100, int(bilateral["relation"]) + gain)
    bilateral["trade_confidence"] = min(100, float(bilateral.get("trade_confidence", 50)) + (2.5 if agenda == "trade" else 1.0))
    bilateral["last_visit"] = today.isoformat()
    diplomacy["last_visit"] = today.isoformat()
    diplomacy["visit_log"].insert(0, {"date": today.isoformat(), "country": config["name"], "code": code,
                                      "agenda": AGENDAS[agenda], "cost_bi": cost, "relation_gain": gain, "simulated": True})
    diplomacy["visit_log"] = diplomacy["visit_log"][:30]
    state["metrics"]["gdp_growth"] = round(min(15, float(state["metrics"].get("gdp_growth", 2)) + .01), 2)
    return {"country": config["name"], "agenda": AGENDAS[agenda], "cost_bi": cost, "relation": bilateral["relation"],
            "message": f"Visita simulada a {config['name']}: pauta de {AGENDAS[agenda].lower()} avancou e a relacao bilateral melhorou."}


def attend_international_event(state: dict[str, Any], event_id: str) -> dict[str, Any]:
    diplomacy = ensure_diplomacy_state(state)
    event = next((item for item in diplomacy["events"] if item["id"] == event_id), None)
    if not event or event.get("status") != "upcoming":
        raise ValueError("Este evento internacional nao esta disponivel.")
    today = date.fromisoformat(state["date"])
    event_date = date.fromisoformat(event["date"])
    if today < event_date - timedelta(days=30):
        raise ValueError("A participacao pode ser confirmada ate 30 dias antes do evento.")
    if today > event_date + timedelta(days=30):
        event["status"] = "missed"
        raise ValueError("O prazo para participar deste evento ja passou.")
    _spend_travel(state, float(event["cost_bi"]))
    event["status"] = "attended"
    event["attended_on"] = today.isoformat()
    diplomacy["multilateral_influence"] = min(100, float(diplomacy["multilateral_influence"]) + 3)
    if event.get("kind") == "climate":
        outcomes = state["budget"].setdefault("outcomes", {})
        outcomes["rural_resilience"] = min(100, float(outcomes.get("rural_resilience", 50)) + 1)
    elif event.get("kind") == "trade":
        country = diplomacy["countries"]["ARG"]
        country["trade_confidence"] = min(100, float(country.get("trade_confidence", 50)) + 3)
    return {"event": event["name"], "cost_bi": event["cost_bi"],
            "message": f"Participacao simulada em {event['name']} registrada; a influencia multilateral aumentou."}
