from datetime import date, timedelta
from typing import Any

from .difficulty import adjust_coalition_probability, get_difficulty
from .events import ensure_event_state, process_events
from .politics import election_date, process_election
from .ministries import INVESTMENT_AREAS
from .fiscal import advance_fiscal, ensure_fiscal_state
from .diplomacy import advance_diplomacy, ensure_diplomacy_state
from .works import advance_works, ensure_works_state
from .appointments import advance_appointments, ensure_appointments_state
from .campaign import ensure_campaign_state
from .communications import ensure_communications_state
from .politics import campaign_active as is_campaign_active
from .social import advance_social_indicators, ensure_social_indicators
from .indicators import record_indicator_snapshot

START_DATE = date(2027, 1, 1)
TERM_DAYS = 1461
REGION_BASELINES = {
    "norte": {"support": 48, "infrastructure": 66, "economic_activity": 74, "priority": "Saneamento, conectividade e logística fluvial"},
    "nordeste": {"support": 50, "infrastructure": 63, "economic_activity": 78, "priority": "Água, emprego e acesso a serviços"},
    "centro_oeste": {"support": 54, "infrastructure": 77, "economic_activity": 90, "priority": "Escoamento, armazenagem e proteção ambiental"},
    "sudeste": {"support": 53, "infrastructure": 82, "economic_activity": 94, "priority": "Mobilidade, habitação e produtividade urbana"},
    "sul": {"support": 52, "infrastructure": 84, "economic_activity": 87, "priority": "Resiliência climática e indústria"},
}


def new_game() -> dict[str, Any]:
    state = {
        "term": 1, "term_start": START_DATE.isoformat(), "campaign_seed": 203001,
        "setup_pending": True,
        "difficulty": "normal",
        "dashboard_cards": ["gdp_growth", "inflation", "unemployment", "debt_gdp", "primary_balance", "approval"],
        "day_of_mandate": 1, "date": START_DATE.isoformat(), "regime": "democratic",
        "office_status": "incumbent", "career_status": "active", "election": {}, "rupture_attempts": 0,
        "communications": {"inauguration": {"required": True, "delivered": False, "legacy_save": False,
            "date": None, "text": "", "score": None, "rubric": {}}},
        "institutions": {"military_loyalty": 60, "constitutional_order": 65, "civilian_legitimacy": 55, "institutional_resistance": 50},
        "legislative_calendar": {"last_submission": None, "pending_bills": [], "laws_enacted": 0, "laws_failed": 0},
        "executive_calendar": {"last_action": None},
        "budget": {"last_reallocation": None, "annual_investment_bi": 100.0,
                   "allocations": {key: area["budget"] for key, area in INVESTMENT_AREAS.items()},
                   "pipeline": [], "outcomes": {"education": 50.0, "health": 50.0, "security": 50.0,
                     "infrastructure": 50.0, "productivity": 50.0, "rural_resilience": 50.0},
                    "operating": {"last_review": None, "travel_cut_pct": 0, "residence_cut_pct": 0,
                        "lines": {"official_travel": {"label": "Viagens oficiais e delegações", "annual_cost_bi": 2.4,
                            "description": "Deslocamentos institucionais, missões e delegações do Executivo."},
                            "official_residence": {"label": "Residência oficial e manutenção", "annual_cost_bi": 0.6,
                            "description": "Manutenção, serviços e funcionamento das residências oficiais."}}}},
        "regional_metrics": {key: dict(value) for key, value in REGION_BASELINES.items()},
        "metrics": {"gdp_growth": 2.1, "inflation": 4.5, "unemployment": 7.2, "debt_gdp": 78.0,
                    "primary_balance": -1.5, "approval": 52.0, "governability": 55, "congress_support": 52,
                    "institutional_trust": 58, "integrity": 70, "regional_infrastructure": 85},
        "events": [
            {"id": "budget-2027", "date": "2027-02-15", "title": "Primeira revisão do orçamento", "description": "A equipe econômica apresenta o quadro fiscal atualizado.", "simulated": True},
            {"id": "congress-100", "date": "2027-04-10", "title": "Balanço dos primeiros cem dias", "description": "Lideranças cobram prioridades e entregas do governo.", "simulated": True},
            {"id": "municipal-2028", "date": "2028-10-01", "title": "Eleições municipais", "description": "A votação muda o equilíbrio político nos estados e municípios.", "simulated": True},
        ],
    }
    ensure_event_state(state)
    return refresh_calendar_fields(state)


def refresh_calendar_fields(state: dict[str, Any]) -> dict[str, Any]:
    current = date.fromisoformat(state["date"])
    term_start = date.fromisoformat(state.get("term_start", START_DATE.isoformat()))
    state["day_of_mandate"] = max(1, (current - term_start).days + 1)
    state["month"] = max(1, (current.year - term_start.year) * 12 + current.month - term_start.month + 1)
    state["days_in_term"] = TERM_DAYS
    state["election_date"] = election_date(state).isoformat()
    ensure_campaign_state(state)
    state["campaign_active"] = (is_campaign_active(state, current) if not (state.get("career") or {}).get("mode")
                                else (state.get("career", {}).get("phase") in {"campaign", "runoff_campaign"} and current <= election_date(state)))
    ensure_event_state(state)
    state.setdefault("legislative_calendar", {"last_submission": None, "pending_bills": [], "laws_enacted": 0, "laws_failed": 0})
    state.setdefault("executive_calendar", {"last_action": None})
    state.setdefault("budget", {"last_reallocation": None, "annual_investment_bi": 100.0,
        "allocations": {key: area["budget"] for key, area in INVESTMENT_AREAS.items()}, "pipeline": [],
        "outcomes": {"education": 50.0, "health": 50.0, "security": 50.0, "infrastructure": 50.0,
                     "productivity": 50.0, "rural_resilience": 50.0}})
    # Migration for existing saves: operating expenses are part of the federal cash
    # account and the estimates are explicitly game abstractions, not official totals.
    operating = state["budget"].setdefault("operating", {})
    operating.setdefault("last_review", None)
    operating.setdefault("travel_cut_pct", 0)
    operating.setdefault("residence_cut_pct", 0)
    lines = operating.setdefault("lines", {})
    lines.setdefault("official_travel", {"label": "Viagens oficiais e delegações", "annual_cost_bi": 2.4,
        "description": "Deslocamentos institucionais, missões e delegações do Executivo."})
    lines.setdefault("official_residence", {"label": "Residência oficial e manutenção", "annual_cost_bi": 0.6,
        "description": "Manutenção, serviços e funcionamento das residências oficiais."})
    ensure_fiscal_state(state)
    ensure_diplomacy_state(state)
    ensure_works_state(state)
    ensure_appointments_state(state)
    ensure_communications_state(state)
    ensure_social_indicators(state)
    regional = state.setdefault("regional_metrics", {})
    for key, defaults in REGION_BASELINES.items():
        regional.setdefault(key, dict(defaults))
        for metric, value in defaults.items():
            regional[key].setdefault(metric, value)
    record_indicator_snapshot(state)
    return state


def advance_state(state: dict[str, Any], days: int) -> tuple[dict[str, Any], str]:
    days = max(1, min(int(days), 90))
    before = date.fromisoformat(state["date"])
    from .indicator_engine import ensure as _ensure_nation
    _ensure_nation(state)
    after = before + timedelta(days=days)
    next_election = election_date(state)
    if before < next_election < after:
        after = next_election
    transition = state.get("election", {}).get("transition_date")
    if transition:
        transition_day = date.fromisoformat(transition)
        if before < transition_day < after:
            after = transition_day
    elapsed = (after - before).days
    state["date"] = after.isoformat()
    refresh_calendar_fields(state)
    m = state["metrics"]
    difficulty = get_difficulty(state.get("difficulty", "normal"))
    volatility = difficulty["economic_volatility"]
    m["inflation"] = round(max(0.5, m["inflation"] + (2.4 - m["inflation"]) * elapsed / 5000 * volatility), 2)
    m["unemployment"] = round(max(2.0, m["unemployment"] + (5.5 - m["unemployment"]) * elapsed / 7000 * volatility), 2)
    work_messages = advance_works(state, before, after)
    diplomacy_messages = advance_diplomacy(state, before, after)
    advance_fiscal(state, elapsed, volatility)
    appointment_messages = advance_appointments(state, before, after)
    messages = work_messages + diplomacy_messages + appointment_messages + process_events(state, before, after)
    messages.extend(process_election(state, before, after))
    messages.extend(process_legislation(state, before, after))
    messages.extend(process_investments(state, before, after))
    from .territory import advance as territory_advance
    messages.extend(territory_advance(state, before, after))
    from .regulators import tick as regulators_tick
    messages.extend(regulators_tick(state, before, after))
    from .subnational_fiscal import tick as fiscal_tick
    messages.extend(fiscal_tick(state, before, after))
    if state.get("party_path"):
        from .party_path import sync_with_career
        messages.extend(sync_with_career(state))
    if state.get("party_path", {}).get("active"):
        from .party_path import tick as party_tick
        messages.extend(party_tick(state, before, after))
    from .story import tick as story_tick
    messages.extend(story_tick(state, before, after))
    advance_social_indicators(state, elapsed)
    from .indicator_engine import tick as nation_tick
    messages.extend(nation_tick(state, before, after))
    event_names = [e["title"] for e in state.get("events", []) if before < date.fromisoformat(e["date"]) <= after]
    if event_names:
        messages.append("Agenda simulada: " + ", ".join(event_names) + ".")
    if not messages:
        messages.append(f"Calendário simulado avançou {elapsed} dia(s).")
    return refresh_calendar_fields(state), " ".join(messages)


def process_legislation(state: dict[str, Any], before: date, after: date) -> list[str]:
    import random
    calendar = state.setdefault("legislative_calendar", {"last_submission": None, "pending_bills": [], "laws_enacted": 0, "laws_failed": 0})
    messages = []
    remaining = []
    for bill in calendar.get("pending_bills", []):
        decision_day = date.fromisoformat(bill["decision_date"])
        if before < decision_day <= after:
            from .legislature import roll_call
            result = roll_call(state, bill)
            history = calendar.setdefault("vote_history", [])
            entry = {"bill_id": bill["id"], "title": bill["title"], "instrument": bill.get("instrument"),
                     "date": decision_day.isoformat(), "aprovado": result["aprovado"], "resultado": result}
            history.insert(0, entry)
            for old in history[3:]:  # só os três mais recentes guardam voto nominal
                old.get("resultado", {}).get("camara", {}).pop("votos", None)
            del history[40:]
            bill["vote"] = {"camara": {k: v for k, v in result["camara"].items() if k not in {"votos", "por_partido"}},
                            "senado": result.get("senado") and {k: v for k, v in result["senado"].items() if k != "por_partido"}}
            from .powers import resolve_bill
            if result["aprovado"]:
                from .rules import apply_effects
                power_effects = resolve_bill(state, bill, True) if bill.get("power_id") else None
                effects = power_effects if power_effects is not None else apply_effects(state, bill["interpretation"])
                calendar["laws_enacted"] = int(calendar.get("laws_enacted", 0)) + 1
                bill["status"] = "approved"
                bill["effects"] = effects
                messages.append(f"Congresso aprovou, na simulação, o projeto: {bill['title']}.")
            else:
                calendar["laws_failed"] = int(calendar.get("laws_failed", 0)) + 1
                bill["status"] = "rejected"
                if bill.get("power_id"):
                    resolve_bill(state, bill, False)
                messages.append(f"Congresso rejeitou, na simulação, o projeto: {bill['title']}.")
            state.setdefault("simulated_news", []).insert(0, {"id": bill["id"], "date": decision_day.isoformat(), "title": f"Votação: {bill['title']}", "region": "Nacional", "description": f"Resultado fictício: {bill['status']}.", "simulated": True})
            state["simulated_news"] = state["simulated_news"][:20]
        else:
            remaining.append(bill)
    calendar["pending_bills"] = remaining
    return messages


def process_investments(state: dict[str, Any], before: date, after: date) -> list[str]:
    budget = state.setdefault("budget", {"pipeline": [], "outcomes": {}})
    remaining = []
    messages = []
    for project in budget.get("pipeline", []):
        completion = date.fromisoformat(project["completion_date"])
        if before < completion <= after:
            area = INVESTMENT_AREAS[project["area"]]
            scale = min(2.5, project["annual_increase_bi"] / 5)
            effects = dict(area["effects"])
            source_area = INVESTMENT_AREAS.get(project.get("source_area", ""))
            if source_area:
                for metric, delta in source_area["effects"].items():
                    effects[metric] = effects.get(metric, 0) - delta
            for metric, delta in effects.items():
                if metric in {"gdp_growth", "approval"}:
                    updated = state["metrics"].get(metric, 0) + delta * scale
                    state["metrics"][metric] = round(max(0, min(100, updated)) if metric == "approval" else max(-10, min(20, updated)), 2)
                else:
                    budget.setdefault("outcomes", {})[metric] = max(0, min(100, budget.setdefault("outcomes", {}).get(metric, 50) + delta * scale))
            messages.append(f"Entrega simulada: {area['label']} recebe o reforço e {source_area['label'] if source_area else 'a área de origem'} sente a redução.")
        else:
            remaining.append(project)
    budget["pipeline"] = remaining
    return messages
