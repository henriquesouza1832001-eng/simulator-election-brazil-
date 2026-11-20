"""Mandato: ações de governo, orçamento escalado, prestação de contas e território.

Parte do ciclo de carreira (antes tudo em career.py; ver career.py, que reexporta estes nomes).
"""
from __future__ import annotations


from datetime import date, timedelta
from typing import Any

from .geography import get_municipality, get_state_population
from .career_base import (
    DEBATE_QUESTIONS,
    EXECUTIVE_BUDGET_BASELINES,
    EXECUTIVE_SERVICE_ACCESS,
    EXECUTIVE_SERVICE_BASE_COSTS,
    LEGISLATIVE_ACTIONS,
    LEGISLATIVE_ACTIONS_BY_OFFICE,
    LEGISLATIVE_OFFICES,
    SERVICE_AREAS,
    _clamp,
)
from .career_access import (
    _campaign,
    is_career_governing,
)


def perform_governance_action(state: dict[str, Any], action: str, service: str = "", issue: str = "") -> dict[str, Any]:
    career = _campaign(state)
    if not is_career_governing(career, date.fromisoformat(state["date"])):
        raise ValueError("Você precisa estar empossado para tomar decisões neste cargo.")
    governance = career.setdefault("governance", {"budget_mi": 0.0, "trust": 50.0, "delivery": 0.0, "political_capital": 50.0, "actions": [], "pipeline": [], "outcomes": {}})
    _ensure_scaled_governance_budget(career, governance)
    if career["office"] == "presidente":
        annual_investment_mi = _presidential_investment_cap_mi(state)
        committed_mi = _presidential_investment_commitment_mi(governance)
        governance["annual_budget_mi"] = annual_investment_mi
        governance["investment_commitment_mi"] = round(committed_mi, 1)
        governance["budget_source"] = "federal_investment"
        governance["budget_mi"] = round(max(0.0, annual_investment_mi - committed_mi), 1)
    last = governance.get("last_action_date")
    if last and (date.fromisoformat(state["date"]) - date.fromisoformat(last)).days < 30:
        wait = 30 - (date.fromisoformat(state["date"]) - date.fromisoformat(last)).days
        raise ValueError(f"A agenda do cargo foi usada. A próxima decisão abre em {wait} dia(s).")
    public_report = None
    selected = None
    if career["office"] in LEGISLATIVE_OFFICES:
        selected = next((item for item in governance_actions_for(career, governance) if item["key"] == action), None)
        if not selected:
            raise ValueError("Esta ação não pertence às atribuições legislativas do cargo.")
        if governance.get("political_capital", 0) < selected["capital"]:
            raise ValueError("Capital político insuficiente. Avance o calendário e negocie apoio.")
        governance["political_capital"] = round(governance["political_capital"] - selected["capital"], 1)
        if action == "proposal":
            governance.setdefault("pipeline", []).append({"id": f"bill-{state['date']}-{len(governance.get('actions', [])) + 1}", "kind": "bill", "title": issue.strip()[:100] or "Proposta de política pública", "due_date": (date.fromisoformat(state["date"]) + timedelta(days=selected["days"])).isoformat(), "status": "in_tramitation", "simulated": True})
            summary = selected["summary"]
        elif action == "oversight":
            governance["trust"] = _clamp(governance.get("trust", 50) + 1.5)
            governance.setdefault("pipeline", []).append({"id": f"oversight-{state['date']}-{len(governance.get('actions', [])) + 1}", "kind": "oversight", "title": issue.strip()[:100] or "Fiscalização pública", "due_date": (date.fromisoformat(state["date"]) + timedelta(days=selected["days"])).isoformat(), "status": "in_progress", "simulated": True})
            summary = selected["summary"]
        else:
            career["group_support"]["servidores"] = _clamp(career["group_support"].get("servidores", 45) + 1.2)
            career["local_support"] = _clamp(career["local_support"] + 1.0)
            governance["trust"] = _clamp(governance.get("trust", 50) + 1.2)
            summary = "Audiência concluída. Apoio de servidores, confiança e apoio local subiram um pouco; os efeitos são registrados na carreira simulada."
        cost = 0.0
    else:
        selected = next((item for item in governance_actions_for(career, governance) if item["key"] == action), None)
        if selected and action.startswith("service_"):
            area_key = selected["area"]
            area = SERVICE_AREAS[area_key]
            cost = selected["cost_mi"]
            if governance.get("budget_mi", 0) < cost:
                raise ValueError("A reserva anual desta agenda não cobre o programa. Reavalie o orçamento ou aguarde o próximo ano.")
            governance["budget_mi"] = round(governance["budget_mi"] - cost, 1)
            if career["office"] == "presidente":
                governance["investment_commitment_mi"] = round(
                    _presidential_investment_commitment_mi(governance) + cost, 1
                )
            due_date = date.fromisoformat(state["date"]) + timedelta(days=area["days"])
            territory = governance_territory_for(career)
            governance.setdefault("pipeline", []).append({"id": f"service-{state['date']}-{len(governance.get('actions', [])) + 1}", "kind": "service", "area": area_key, "title": area["label"], "territory": territory["name"], "territory_scope": territory["scope"], "municipality_id": territory.get("municipality_id"), "effect": area["effect"], "cost_mi": cost, "cost_basis": selected.get("cost_basis"), "started_at": state["date"], "due_date": due_date.isoformat(), "status": "in_progress", "simulated": True})
            summary = f"Programa de {area['label'].lower()} iniciado para {territory['name']}. Custo reservado: R$ {cost:,.1f} milhões; entrega prevista para {due_date.strftime('%d/%m/%Y')} se não houver atraso."
        elif action == "public_report":
            cost = 0.0
            public_report = _publish_governance_report(state, career, governance)
            governance["trust"] = _clamp(governance.get("trust", 50) + 2.0)
            career["group_support"]["jovens"] = _clamp(career["group_support"].get("jovens", 45) + 1.0)
            summary = (f"Prestação de contas simulada publicada para {public_report['period_start']} a {public_report['period_end']}: "
                       f"R$ {public_report['programs_reserved_mi']:.1f} milhões reservados, "
                       f"{public_report['programs_completed']} programa(s) concluído(s) e "
                       f"{public_report['programs_in_progress']} em andamento.")
        else:
            raise ValueError("Esta ação não pertence às atribuições executivas deste cargo.")
    governance["last_action_date"] = state["date"]
    entry = {"id": f"office-{state['date']}-{len(governance.get('actions', [])) + 1}", "date": state["date"], "action": action,
             "title": issue.strip()[:100] or next((item["label"] for item in governance_actions_for(career) if item["key"] == action), action.replace("_", " ").title()),
             "summary": summary, "cost_mi": cost, "cost_basis": selected.get("cost_basis") if selected else None,
             "status": "active", "simulated": True}
    if public_report:
        entry["report_id"] = public_report["id"]
    governance.setdefault("actions", []).append(entry)
    governance["actions"] = governance["actions"][-50:]
    return {"action": entry, "summary": summary, "governance": governance,
            "public_report": public_report, "days_cost": 1}


def _publish_governance_report(state: dict[str, Any], career: dict[str, Any],
                               governance: dict[str, Any]) -> dict[str, Any]:
    """Save an auditable, simulated snapshot of this executive's recorded work."""
    today = date.fromisoformat(state["date"])
    previous_report_date = governance.get("last_public_report_date")
    period_start = (
        date.fromisoformat(previous_report_date) + timedelta(days=1)
        if previous_report_date
        else date.fromisoformat(career.get("office_start") or career.get("inauguration_date") or state["date"])
    )
    if period_start > today:
        period_start = today
    period_start_label = period_start.strftime("%Y-%m-%d")
    period_end_label = today.isoformat()
    actions = governance.get("actions", [])
    period_actions = [
        item for item in actions
        if item.get("date") and period_start_label <= item["date"] <= period_end_label
        and item.get("action") != "public_report"
    ]
    completed = [
        item for item in actions
        if item.get("kind") == "service" and item.get("status") == "delivered"
        and period_start_label <= item.get("completed_at", "") <= period_end_label
    ]
    current_programs = [item for item in governance.get("pipeline", []) if item.get("kind") == "service"]
    territory = governance_territory_for(career)
    annual_budget = float(governance.get("annual_budget_mi", governance.get("budget_mi", 0)))
    budget_available = float(governance.get("budget_mi", 0))
    if career.get("office") == "presidente":
        committed = _presidential_investment_commitment_mi(governance)
        committed_label = "Dotação federal comprometida neste ano"
    else:
        committed = sum(float(item.get("cost_mi", 0)) for item in current_programs)
        committed_label = "Custo previsto dos programas em andamento"
    report = {
        "id": f"report-{today.isoformat()}-{len(governance.get('public_reports', [])) + 1}",
        "date": today.isoformat(),
        "period_start": period_start_label,
        "period_end": period_end_label,
        "office": career.get("office_label", career.get("office", "")),
        "territory": territory["name"],
        "annual_budget_mi": round(annual_budget, 1),
        "budget_available_mi": round(budget_available, 1),
        "budget_committed_mi": round(committed, 1),
        "budget_committed_label": committed_label,
        "programs_reserved_mi": round(sum(float(item.get("cost_mi", 0)) for item in period_actions
                                           if str(item.get("action", "")).startswith("service_")), 1),
        "programs_started": sum(1 for item in period_actions if str(item.get("action", "")).startswith("service_")),
        "programs_completed": len(completed),
        "programs_in_progress": len(current_programs),
        "outcomes": {key: round(float(value), 1) for key, value in (governance.get("outcomes") or {}).items()},
        "simulated": True,
    }
    governance.setdefault("public_reports", []).append(report)
    governance["public_reports"] = governance["public_reports"][-12:]
    governance["last_public_report_date"] = today.isoformat()
    return report


def governance_actions_for(career: dict[str, Any], governance: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    if career["office"] in LEGISLATIVE_OFFICES:
        return [dict(item) for item in LEGISLATIVE_ACTIONS_BY_OFFICE.get(career["office"], LEGISLATIVE_ACTIONS)]
    office = career["office"]
    if office in EXECUTIVE_SERVICE_ACCESS:
        active_governance = governance or career.get("governance") or {}
        index = float(active_governance.get("budget_price_index", 1.0))
        population_basis = _executive_population_basis(career)
        cost_basis = (
            f"População IBGE {population_basis['reference_year']}: "
            f"{_format_population_count(population_basis['population'])} habitantes; "
            f"referência do parâmetro: {_format_population_count(population_basis['reference_population'])} habitantes; "
            f"índice de preços acumulado ×{index:.3f}."
            if office in EXECUTIVE_BUDGET_BASELINES else
            f"Escala federal do jogo; índice de preços acumulado ×{index:.3f}."
        )
        actions = []
        for area_key in SERVICE_AREAS:
            if area_key not in EXECUTIVE_SERVICE_ACCESS[office]:
                continue
            area = SERVICE_AREAS[area_key]
            base_cost = EXECUTIVE_SERVICE_BASE_COSTS[office][area_key]
            scale = population_basis["scale"] if office in EXECUTIVE_BUDGET_BASELINES else 1.0
            actions.append({"key": f"service_{area_key}", "area": area_key, "label": area["label"],
                            "cost_mi": round(base_cost * scale * index, 1), "cost_basis": cost_basis, "days": area["days"],
                            "summary": f"Entrega prevista em {area['days']} dias; o efeito aparece no indicador de {area['label'].lower()} ao concluir."})
        actions.append({"key": "public_report", "label": "Publicar prestação de contas", "cost_mi": 0.0, "days": 1,
                        "summary": "Expõe metas, execução financeira e resultados para fiscalização pública."})
        return actions
    return []


def _executive_population_basis(career: dict[str, Any]) -> dict[str, Any]:
    office = career.get("office")
    baseline = EXECUTIVE_BUDGET_BASELINES.get(office)
    if not baseline:
        return {"population": 0, "reference_population": 0, "scale": 1.0, "reference_year": None}
    if office == "prefeito":
        profile = career.get("municipality_profile")
        if not profile and career.get("municipality_id"):
            profile = get_municipality(career["municipality_id"])
        population = int((profile or {}).get("population_estimate", 0))
        reference_year = int((profile or {}).get("population_reference_year", 2026))
    else:
        population = get_state_population(career.get("state_code", ""))
        reference_year = 2026
    population = population or int(baseline["population"])
    return {
        "population": population,
        "reference_population": int(baseline["population"]),
        "scale": population / int(baseline["population"]),
        "reference_year": reference_year,
    }


def _executive_annual_budget_mi(career: dict[str, Any], price_index: float = 1.0) -> float:
    baseline = EXECUTIVE_BUDGET_BASELINES.get(career.get("office"))
    if not baseline:
        return 0.0
    basis = _executive_population_basis(career)
    return round(float(baseline["annual_budget_mi"]) * basis["scale"] * price_index, 1)


def _format_population_count(value: int) -> str:
    return f"{value:,}".replace(",", ".")


def _ensure_scaled_governance_budget(career: dict[str, Any], governance: dict[str, Any]) -> None:
    if career.get("office") not in EXECUTIVE_BUDGET_BASELINES or governance.get("budget_scale_version") == 1:
        return
    price_index = max(0.01, float(governance.get("budget_price_index", 1.0)))
    old_annual = float(governance.get("annual_budget_mi", EXECUTIVE_BUDGET_BASELINES[career["office"]]["annual_budget_mi"]))
    old_available = max(0.0, float(governance.get("budget_mi", old_annual)))
    remaining_share = min(1.0, old_available / old_annual) if old_annual > 0 else 1.0
    annual = _executive_annual_budget_mi(career, price_index)
    basis = _executive_population_basis(career)
    governance.update({
        "annual_budget_mi": annual,
        "budget_mi": round(annual * remaining_share, 1),
        "budget_population": basis["population"],
        "budget_population_reference_year": basis["reference_year"],
        "budget_scale_version": 1,
    })


def _historical_compare(career: dict[str, Any]) -> dict[str, Any] | None:
    try:
        from .historical_play import compare
        return compare(career)
    except Exception:
        return None


def _reference_election(career: dict[str, Any]) -> dict[str, Any] | None:
    try:
        from .historical import reference_election
        return reference_election(career)
    except Exception:
        return None


def governance_territory_for(career: dict[str, Any]) -> dict[str, Any]:
    office = career.get("office")
    if office == "prefeito":
        return {"scope": "Município", "name": f"{career.get('municipality') or career.get('state_name', '')} · {career.get('state_code', '')}",
                "municipality_id": career.get("municipality_id")}
    if office == "governador":
        return {"scope": "Estado", "name": career.get("state_name") or career.get("state_code", "")}
    if office == "presidente":
        return {"scope": "País", "name": "Brasil"}
    return {"scope": "Representação legislativa", "name": career.get("municipality") or career.get("state_name") or "Brasil"}


def _presidential_investment_cap_mi(state: dict[str, Any]) -> float:
    """Presidential programs use the existing federal investment appropriation."""
    return max(0.0, float((state.get("budget") or {}).get("annual_investment_bi", 100.0)) * 1000)


def _presidential_investment_commitment_mi(governance: dict[str, Any]) -> float:
    committed = governance.get("investment_commitment_mi")
    if committed is not None:
        return max(0.0, float(committed))
    # Derive the committed amount when opening a save from the previous version.
    annual = float(governance.get("annual_budget_mi", governance.get("budget_mi", 0)))
    available = float(governance.get("budget_mi", annual))
    return max(0.0, annual - available)


def career_debate_prompt(career: dict[str, Any], issue: str) -> dict[str, str]:
    office = career.get("office")
    scope = "municipal" if office in {"vereador", "prefeito"} else "estadual" if office in {"deputado_estadual", "governador"} else "federal"
    question = DEBATE_QUESTIONS[issue]
    if office in LEGISLATIVE_OFFICES:
        question += " Como você transformará essa proposta em fiscalização, audiência ou votação na sua casa legislativa?"
    return {"moderator": "Bancada de debate simulada", "question": question, "scope": scope,
            "instruction": "Responda ao ponto, indique uma ação possível para o cargo e diga como o resultado será acompanhado."}
