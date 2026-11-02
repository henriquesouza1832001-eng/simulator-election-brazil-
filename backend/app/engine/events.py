from __future__ import annotations

import random
from datetime import date, timedelta
from typing import Any

from .difficulty import get_difficulty
from .fiscal import record_one_off_spending


def ensure_event_state(state: dict[str, Any]) -> None:
    state.setdefault("campaign_seed", 203001)
    state.setdefault("active_crises", [])
    state.setdefault("simulated_news", [])
    state.setdefault("event_history", [])
    state.setdefault("event_months_checked", [])


def _make_flood(state: dict[str, Any], current: date) -> dict[str, Any]:
    severity = 1 + random.Random(f"{state['campaign_seed']}:south-flood:{current:%Y-%m}").randint(0, 2)
    return {
        "id": f"enchente-sul-{current:%Y%m}", "kind": "flood", "date": current.isoformat(),
        "title": "Enchentes no Sul", "region": "Sul", "severity": severity,
        "status": "active", "days_active": 0, "simulated": True,
        "description": "Evento fictício do simulador: chuvas intensas interrompem estradas, serviços e parte da produção regional.",
        "options": [
            {"id": "rescue", "label": "Mobilizar resposta e abrigos", "cost_bi": 2.0},
            {"id": "rebuild", "label": "Priorizar estradas e reconstrução", "cost_bi": 4.0},
            {"id": "coordinate", "label": "Coordenar estados e publicar plano", "cost_bi": 0.5},
        ],
    }


def _add_news(state: dict[str, Any], event: dict[str, Any]) -> None:
    state["simulated_news"].insert(0, {"id": event["id"], "date": event["date"], "title": event["title"],
        "region": event.get("region", "Nacional"), "description": event["description"], "simulated": True})
    state["simulated_news"] = state["simulated_news"][:20]
    state["event_history"].append({"id": event["id"], "date": event["date"], "title": event["title"], "outcome": "em andamento"})


def process_events(state: dict[str, Any], before: date, after: date) -> list[str]:
    ensure_event_state(state)
    messages: list[str] = []
    # Draw once on the first of each month. Hash-seeded draws make batch and daily time steps equivalent.
    cursor = date(before.year, before.month, 1)
    if cursor <= before:
        cursor = (cursor.replace(day=28) + timedelta(days=4)).replace(day=1)
    while cursor <= after:
        month_key = cursor.strftime("%Y-%m")
        if month_key not in state["event_months_checked"]:
            state["event_months_checked"].append(month_key)
            rng = random.Random(f"{state['campaign_seed']}:monthly-event:{month_key}")
            pressure = get_difficulty(state.get("difficulty", "normal"))["event_pressure"]
            chance = max(.05, min(.65, .24 * pressure))
            # Floods are a recurring hazard, not a one-off screen; the active crisis persists until addressed.
            if not any(c.get("kind") == "flood" and c.get("status") == "active" for c in state["active_crises"]):
                if rng.random() < chance:
                    event = _make_flood(state, cursor)
                    state["active_crises"].append(event)
                    _add_news(state, event)
                    messages.append("Evento simulado: enchentes no Sul exigem resposta do governo.")
        cursor = (cursor.replace(day=28) + timedelta(days=4)).replace(day=1)

    elapsed = max(0, (after - before).days)
    metrics = state["metrics"]
    for crisis in state["active_crises"]:
        if crisis.get("status") != "active":
            continue
        crisis_start = date.fromisoformat(crisis["date"])
        active_days = max(0, (after - max(before, crisis_start)).days)
        crisis["days_active"] = int(crisis.get("days_active", 0)) + active_days
        if crisis.get("kind") == "flood" and elapsed:
            severity = crisis["severity"]
            # Persistent losses: output and infrastructure recover slowly unless an intervention is chosen.
            metrics["gdp_growth"] = round(metrics["gdp_growth"] - .04 * severity * active_days / 30, 2)
            metrics["regional_infrastructure"] = round(max(0, metrics.get("regional_infrastructure", 100) - .8 * severity * active_days / 30), 1)
            metrics["approval"] = round(max(0, metrics["approval"] - .35 * severity * active_days / 30), 1)
    return messages


def respond_to_event(state: dict[str, Any], event_id: str, choice: str) -> dict[str, Any]:
    ensure_event_state(state)
    crisis = next((c for c in state["active_crises"] if c["id"] == event_id and c.get("status") == "active"), None)
    if not crisis:
        raise ValueError("Este evento não está mais ativo.")
    if crisis.get("kind") != "flood":
        raise ValueError("Não há resposta disponível para este evento.")
    metrics = state["metrics"]
    severity = crisis["severity"]
    if choice == "rescue":
        cost, gdp, approval, infrastructure = 2.0, .10 * severity, 1.5, 2 * severity
        result = "Equipes de resposta e abrigos foram mobilizados; perdas humanas e interrupções caem."
    elif choice == "rebuild":
        cost, gdp, approval, infrastructure = 4.0, .30 * severity, 1.0, 8 * severity
        result = "Reconstrução prioritária acelerou a recuperação de estradas e da atividade regional."
    elif choice == "coordinate":
        cost, gdp, approval, infrastructure = .5, .06 * severity, .7, 3 * severity
        result = "Estados coordenam abrigos, rotas e informação; a recuperação será mais lenta, mas organizada."
    else:
        raise ValueError("Escolha de resposta inválida.")
    record_one_off_spending(state, cost)
    metrics["gdp_growth"] = round(metrics["gdp_growth"] + gdp, 2)
    metrics["approval"] = round(min(100, metrics["approval"] + approval), 1)
    metrics["regional_infrastructure"] = round(min(100, metrics.get("regional_infrastructure", 85) + infrastructure), 1)
    crisis["status"] = "contained"
    crisis["response"] = choice
    crisis["resolved_date"] = state["date"]
    for item in state["event_history"]:
        if item["id"] == event_id:
            item["outcome"] = result
    _add_news(state, {**crisis, "id": f"resposta-{event_id}", "date": state["date"], "title": f"Resposta: {crisis['title']}", "description": result})
    return {"result": result, "cost_bi": cost, "gdp_delta": gdp, "approval_delta": approval}
