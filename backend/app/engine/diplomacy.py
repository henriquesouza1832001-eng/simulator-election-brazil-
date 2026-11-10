"""Bilateral relations, official visits and simulated international agenda."""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from .fiscal import ensure_fiscal_state

COUNTRIES: dict[str, dict[str, Any]] = {
    "ARG": {"name": "Argentina", "region": "América do Sul", "relation": 62, "trade_weight": 6, "travel_cost_bi": .045, "focus": "comércio e energia"},
    "CHL": {"name": "Chile", "region": "América do Sul", "relation": 61, "trade_weight": 4, "travel_cost_bi": .05, "focus": "mineração e energia limpa"},
    "COL": {"name": "Colômbia", "region": "América do Sul", "relation": 57, "trade_weight": 3, "travel_cost_bi": .055, "focus": "segurança e Amazonia"},
    "URY": {"name": "Uruguai", "region": "América do Sul", "relation": 64, "trade_weight": 2, "travel_cost_bi": .045, "focus": "Mercosul e fronteira"},
    "USA": {"name": "Estados Unidos", "region": "América do Norte", "relation": 54, "trade_weight": 12, "travel_cost_bi": .18, "focus": "comércio, tecnologia e defesa"},
    "MEX": {"name": "México", "region": "América do Norte", "relation": 53, "trade_weight": 4, "travel_cost_bi": .16, "focus": "indústria e cadeias produtivas"},
    "CHN": {"name": "China", "region": "Ásia", "relation": 64, "trade_weight": 22, "travel_cost_bi": .23, "focus": "comércio, infraestrutura e investimento"},
    "IND": {"name": "Índia", "region": "Ásia", "relation": 56, "trade_weight": 3, "travel_cost_bi": .22, "focus": "tecnologia, saúde e comércio"},
    "JPN": {"name": "Japão", "region": "Ásia", "relation": 67, "trade_weight": 3, "travel_cost_bi": .24, "focus": "tecnologia e transição energética"},
    "DEU": {"name": "Alemanha", "region": "Europa", "relation": 63, "trade_weight": 5, "travel_cost_bi": .16, "focus": "indústria e financiamento"},
    "FRA": {"name": "França", "region": "Europa", "relation": 58, "trade_weight": 3, "travel_cost_bi": .16, "focus": "clima, ciência e comércio"},
    "PRT": {"name": "Portugal", "region": "Europa", "relation": 68, "trade_weight": 2, "travel_cost_bi": .15, "focus": "mobilidade, serviços e língua"},
    "ZAF": {"name": "África do Sul", "region": "África", "relation": 59, "trade_weight": 2, "travel_cost_bi": .17, "focus": "BRICS, energia e comércio"},
    "AGO": {"name": "Angola", "region": "África", "relation": 66, "trade_weight": 1, "travel_cost_bi": .18, "focus": "cooperação e infraestrutura"},
    "TUR": {"name": "Turquia", "region": "Mediterrâneo", "relation": 48, "trade_weight": 2, "travel_cost_bi": .19, "focus": "alimentos, indústria e logística"},
    "VEN": {"name": "Venezuela", "region": "América do Sul", "relation": 38, "trade_weight": 1, "travel_cost_bi": .06, "focus": "fronteira e cooperação consular"},
}

AGENDAS = {"trade": "Comércio e investimento", "climate": "Clima e energia", "science": "Ciência e tecnologia", "security": "Segurança e fronteiras"}

INTERNATIONAL_EVENTS = [
    {"id": "mercosur-eu-2027", "date": "2027-03-22", "name": "Rodada Mercosul-União Europeia", "place": "Brasília", "kind": "trade", "cost_bi": .08,
     "description": "Agenda simulada de facilitação comercial e cadeias produtivas."},
    {"id": "climate-finance-2027", "date": "2027-06-05", "name": "Fórum de Financiamento Climático", "place": "Brasília", "kind": "climate", "cost_bi": .06,
     "description": "Evento fictício sobre adaptação, financiamento e proteção de cidades."},
    {"id": "cop30-legacy-2027", "date": "2027-11-10", "name": "Acompanhamento do legado da COP30", "place": "Belém", "kind": "climate", "cost_bi": .10,
     "description": "Evento simulado, dois anos após a COP30, para acompanhar financiamento e compromissos climáticos."},
    {"id": "un-assembly-2028", "date": "2028-09-20", "name": "Semana de Alto Nível da ONU", "place": "Nova York", "kind": "multilateral", "cost_bi": .16,
     "description": "Agenda multilateral simulada para encontros bilaterais e coordenação internacional."},
    {"id": "climate-summit-2029", "date": "2029-11-12", "name": "Cúpula Global do Clima", "place": "Internacional", "kind": "climate", "cost_bi": .12,
     "description": "Cúpula fictícia do calendario do jogo; não representa uma conferência oficial."},
]


def ensure_diplomacy_state(state: dict[str, Any]) -> dict[str, Any]:
    ensure_fiscal_state(state)
    diplomacy = state.setdefault("diplomacy", {})
    saved = diplomacy.setdefault("countries", {})
    for code, country in COUNTRIES.items():
        saved.setdefault(code, {"relation": country["relation"], "trade_confidence": 50, "last_visit": None,
                                "focus": country["focus"], "region": country["region"], "trade_weight": country["trade_weight"]})
    diplomacy.setdefault("last_visit", None)
    diplomacy.setdefault("visit_log", [])
    diplomacy.setdefault("trip", None)
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
    travel_price_index = _travel_price_index(state)
    countries = [{"code": code, **config,
                  "base_travel_cost_bi": config["travel_cost_bi"],
                  "travel_cost_bi": round(config["travel_cost_bi"] * travel_price_index, 4),
                  "travel_price_index": round(travel_price_index, 4),
                  "trip_days": _country_trip_days(config), **diplomacy["countries"][code]}
                 for code, config in COUNTRIES.items()]
    events = [{**event, "base_cost_bi": event["cost_bi"],
               "cost_bi": round(float(event["cost_bi"]) * travel_price_index, 4),
               "travel_price_index": round(travel_price_index, 4),
               "days_until": (date.fromisoformat(event["date"]) - today).days,
               "trip_days": _event_trip_days(event, (date.fromisoformat(event["date"]) - today).days),
               "outbound_days": _event_outbound_days(event)}
              for event in diplomacy["events"] if event.get("status") == "upcoming"
              and today <= date.fromisoformat(event["date"])
              and _event_outbound_days(event) <= (date.fromisoformat(event["date"]) - today).days]
    relations = [float(country["relation"]) for country in diplomacy["countries"].values()]
    operating = state["budget"]["operating"]
    travel = operating["lines"]["official_travel"]
    ceiling = float(travel["annual_cost_bi"]) * (1 - float(operating.get("travel_cut_pct", 0)) / 100)
    spent = float(operating["spent_by_year"].get(str(today.year), 0))
    trip = diplomacy.get("trip")
    if trip:
        trip = {**trip, "days_remaining": max(0, (date.fromisoformat(trip["arrival_date"]) - today).days)}
        elapsed = max(0, int(trip["duration_days"]) - trip["days_remaining"])
        outbound = max(0, int(trip.get("outbound_days", 1)))
        returning = max(1, int(trip.get("return_days", 1)))
        if elapsed < outbound:
            trip["phase"] = "Deslocamento de ida"
            trip["route_progress"] = round(min(1.0, elapsed / max(1, outbound)) * 100, 1)
            trip["route_from"], trip["route_to"] = trip["origin"], trip["destination"]
        elif elapsed < max(outbound, int(trip["duration_days"]) - returning):
            trip["phase"] = "Agenda no destino"
            trip["route_progress"] = 100.0
            trip["route_from"], trip["route_to"] = trip["origin"], trip["destination"]
        else:
            trip["phase"] = "Deslocamento de retorno"
            trip["route_progress"] = round(max(0.0, (int(trip["duration_days"]) - elapsed) / returning) * 100, 1)
            trip["route_from"], trip["route_to"] = trip["destination"], trip["origin"]
    return {"countries": countries, "events": events, "visit_log": diplomacy["visit_log"][:12], "active_trip": trip,
            "average_relation": round(sum(relations) / len(relations), 1) if relations else 0,
            "multilateral_influence": round(float(diplomacy["multilateral_influence"]), 1),
            "agendas": AGENDAS, "days_until_visit": _days_until_visit(state, diplomacy),
            "travel_spent_bi": round(spent, 4), "travel_remaining_bi": round(max(0, ceiling - spent), 4)}


def _country_trip_days(country: dict[str, Any]) -> int:
    region = country.get("region")
    return {"América do Sul": 4, "América do Norte": 7, "Europa": 9, "Ásia": 12,
            "África": 10, "Mediterrâneo": 9}.get(region, 8)


def _country_outbound_days(country: dict[str, Any]) -> int:
    region = country.get("region")
    return {"América do Sul": 1, "América do Norte": 2, "Europa": 3,
            "Ásia": 4, "África": 4, "Mediterrâneo": 3}.get(region, 3)


def _event_return_days(event: dict[str, Any]) -> int:
    place = str(event.get("place", "")).lower()
    if "bras" in place:
        return 1
    if "belém" in place or "belem" in place:
        return 2
    if "nova york" in place or "new york" in place:
        return 4
    return 5


def _event_trip_days(event: dict[str, Any], days_until: int = 0) -> int:
    # The delegation leaves now, waits for the event, attends for a day, then returns.
    return max(1, max(0, int(days_until)) + 1 + _event_return_days(event))


def _event_outbound_days(event: dict[str, Any]) -> int:
    place = str(event.get("place", "")).lower()
    if "bras" in place:
        return 0
    if "belém" in place or "belem" in place:
        return 1
    if "nova york" in place or "new york" in place:
        return 4
    return 5


def _spend_travel(state: dict[str, Any], amount_bi: float) -> None:
    operating = state["budget"]["operating"]
    year = int(state["date"][:4])
    spent_by_year = operating.setdefault("spent_by_year", {})
    spent = float(spent_by_year.get(str(year), 0))
    line = operating["lines"]["official_travel"]
    ceiling = float(line["annual_cost_bi"]) * (1 - float(operating.get("travel_cut_pct", 0)) / 100)
    if spent + amount_bi > ceiling + 1e-9:
        raise ValueError("A verba anual de viagens não cobre esta agenda.")
    spent_by_year[str(year)] = round(spent + amount_bi, 4)
    # Travel is charged against the annual operating line already in primary spending.


def _travel_price_index(state: dict[str, Any]) -> float:
    line = state["budget"]["operating"]["lines"]["official_travel"]
    base = max(0.01, float(line.get("base_annual_cost_bi", 2.4)))
    return max(0.01, float(line.get("price_index", float(line.get("annual_cost_bi", base)) / base)))


def _indexed_travel_cost(state: dict[str, Any], base_cost_bi: float) -> float:
    return round(float(base_cost_bi) * _travel_price_index(state), 4)


def _begin_trip(state: dict[str, Any], destination: str, destination_code: str | None,
                trip_days: int, cost_bi: float, trip_type: str, agenda: str,
                event_id: str | None = None, outbound_days: int = 1,
                return_days: int = 1) -> dict[str, Any]:
    diplomacy = ensure_diplomacy_state(state)
    if diplomacy.get("trip"):
        trip = diplomacy["trip"]
        raise ValueError(f"A missão para {trip['destination']} ainda esta em andamento; retorno previsto para {trip['arrival_date']}.")
    _spend_travel(state, cost_bi)
    today = date.fromisoformat(state["date"])
    trip_days = max(1, int(trip_days))
    trip = {"id": f"viagem-{today.isoformat()}-{len(diplomacy['visit_log']) + 1}",
            "type": trip_type, "origin": "Brasília", "destination": destination,
            "country_code": destination_code, "agenda": agenda, "event_id": event_id,
            "started_on": today.isoformat(), "arrival_date": (today + timedelta(days=trip_days)).isoformat(),
            "duration_days": trip_days, "outbound_days": max(0, int(outbound_days)),
            "return_days": max(1, int(return_days)), "cost_bi": round(float(cost_bi), 4), "status": "traveling",
            "simulated": True}
    diplomacy["trip"] = trip
    diplomacy["last_visit"] = today.isoformat()
    return trip


def visit_country(state: dict[str, Any], country_code: str, agenda: str) -> dict[str, Any]:
    diplomacy = ensure_diplomacy_state(state)
    code = country_code.upper()
    if code not in COUNTRIES:
        raise ValueError("Escolha um país disponível na agenda diplomática.")
    if agenda not in AGENDAS:
        raise ValueError("Escolha uma pauta diplomática válida.")
    if diplomacy.get("trip"):
        trip = diplomacy["trip"]
        raise ValueError(f"A missão para {trip['destination']} ainda esta em andamento; retorno previsto para {trip['arrival_date']}.")
    wait = _days_until_visit(state, diplomacy)
    if wait:
        raise ValueError(f"A proxima visita oficial pode ser marcada em {wait} dia(s).")
    bilateral = diplomacy["countries"][code]
    today = date.fromisoformat(state["date"])
    last = bilateral.get("last_visit")
    if last and (today - date.fromisoformat(last)).days < 180:
        raise ValueError("Esta visita bilateral ocorreu nos ultimos seis meses.")
    config = COUNTRIES[code]
    cost = _indexed_travel_cost(state, float(config["travel_cost_bi"]))
    trip = _begin_trip(state, config["name"], code, _country_trip_days(config), cost, "bilateral", AGENDAS[agenda],
                       outbound_days=_country_outbound_days(config), return_days=_country_outbound_days(config))
    diplomacy["visit_log"].insert(0, {"id": trip["id"], "date": today.isoformat(), "country": config["name"], "code": code,
                                      "agenda": AGENDAS[agenda], "cost_bi": cost,
                                      "duration_days": trip["duration_days"], "arrival_date": trip["arrival_date"],
                                      "status": "traveling", "simulated": True})
    diplomacy["visit_log"] = diplomacy["visit_log"][:30]
    return {"country": config["name"], "agenda": AGENDAS[agenda], "cost_bi": cost,
            "duration_days": trip["duration_days"], "arrival_date": trip["arrival_date"],
            "message": f"Missão oficial simulada iniciada para {config['name']}. A pauta de {AGENDAS[agenda].lower()} sera concluida na volta, em {trip['arrival_date']}."}


def attend_international_event(state: dict[str, Any], event_id: str) -> dict[str, Any]:
    diplomacy = ensure_diplomacy_state(state)
    event = next((item for item in diplomacy["events"] if item["id"] == event_id), None)
    if not event or event.get("status") != "upcoming":
        raise ValueError("Este evento internacional não esta disponível.")
    today = date.fromisoformat(state["date"])
    event_date = date.fromisoformat(event["date"])
    if diplomacy.get("trip"):
        trip = diplomacy["trip"]
        raise ValueError(f"A missão para {trip['destination']} ainda esta em andamento; retorno previsto para {trip['arrival_date']}.")
    if today < event_date - timedelta(days=30):
        raise ValueError("A participacao pode ser confirmada até 30 dias antes do evento.")
    trip_days = _event_trip_days(event, (event_date - today).days)
    if today > event_date or today + timedelta(days=_event_outbound_days(event)) > event_date:
        event["status"] = "missed"
        raise ValueError("Não ha dias suficientes para chegar ao evento; ele foi perdido nesta simulacao.")
    cost = _indexed_travel_cost(state, float(event["cost_bi"]))
    trip = _begin_trip(state, event["place"], None, trip_days, cost, "multilateral", event["kind"], event_id,
                       outbound_days=_event_outbound_days(event), return_days=_event_return_days(event))
    event["status"] = "traveling"
    event["trip_id"] = trip["id"]
    return {"event": event["name"], "cost_bi": cost, "duration_days": trip_days,
            "arrival_date": trip["arrival_date"],
            "message": f"Viagem simulada para {event['name']} iniciada. A chegada esta prevista para {trip['arrival_date']}."}


def advance_diplomacy(state: dict[str, Any], before: date, after: date) -> list[str]:
    diplomacy = ensure_diplomacy_state(state)
    trip = diplomacy.get("trip")
    if not trip:
        return []
    arrival = date.fromisoformat(trip["arrival_date"])
    if after < arrival:
        return []
    trip_id = trip["id"]
    if trip["type"] == "bilateral":
        country = diplomacy["countries"][trip["country_code"]]
        agenda_key = next((key for key, label in AGENDAS.items() if label == trip["agenda"]), "trade")
        gain = {"trade": 4, "climate": 3, "science": 3, "security": 4}[agenda_key]
        country["relation"] = min(100, int(country["relation"]) + gain)
        country["trade_confidence"] = min(100, float(country.get("trade_confidence", 50)) + (2.5 if agenda_key == "trade" else 1.0))
        country["last_visit"] = trip["started_on"]
        message = f"Missão diplomática concluida: a relação com {trip['destination']} melhorou {gain} pontos após {trip['duration_days']} dias fora de Brasília."
        state["metrics"]["gdp_growth"] = round(min(15, float(state["metrics"].get("gdp_growth", 2)) + .01), 2)
    else:
        event = next((item for item in diplomacy["events"] if item.get("id") == trip.get("event_id")), None)
        if event:
            event["status"] = "attended"
            event["attended_on"] = arrival.isoformat()
            diplomacy["multilateral_influence"] = min(100, float(diplomacy["multilateral_influence"]) + 3)
            if event.get("kind") == "climate":
                outcomes = state["budget"].setdefault("outcomes", {})
                outcomes["rural_resilience"] = min(100, float(outcomes.get("rural_resilience", 50)) + 1)
            elif event.get("kind") == "trade":
                country = diplomacy["countries"]["ARG"]
                country["trade_confidence"] = min(100, float(country.get("trade_confidence", 50)) + 3)
            message = f"Participacao simulada em {event['name']} concluida; a influência multilateral aumentou."
        else:
            message = f"Viagem simulada concluida: retorno de {trip['destination']} a Brasília."
    completed = {"id": trip_id, "date": trip["started_on"], "country": trip["destination"],
                 "agenda": trip["agenda"], "cost_bi": trip["cost_bi"], "duration_days": trip["duration_days"],
                 "arrival_date": trip["arrival_date"], "status": "completed", "completed_on": arrival.isoformat(),
                 "simulated": True}
    diplomacy["visit_log"].insert(0, completed)
    diplomacy["visit_log"] = [item for index, item in enumerate(diplomacy["visit_log"]) if item.get("id") != trip_id or index == 0][:30]
    diplomacy["trip"] = None
    state.setdefault("simulated_news", []).insert(0, {"id": f"news-{trip_id}", "date": arrival.isoformat(),
        "title": "Missão diplomática concluida", "region": trip["destination"], "description": message, "simulated": True})
    state["simulated_news"] = state["simulated_news"][:20]
    return [message]
