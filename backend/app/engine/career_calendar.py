"""Calendário da carreira: avanço do tempo (abertura da campanha, pesquisas, eleição, posse).

Parte do ciclo de carreira (ver career.py, que reexporta estes nomes).
"""
from __future__ import annotations


import random
from datetime import date, timedelta
from typing import Any

from .communications import ensure_communications_state
from .career_base import EXECUTIVE_BUDGET_BASELINES, LEGISLATIVE_OFFICES, OFFICES, SERVICE_AREAS, _clamp, _regular_election_day
from .career_access import (
    is_career_governing,
)
from .career_polls import _campaign_poll_schedule, _record_public_poll
from .career_promises import (
    _activate_campaign_promises,
    _review_campaign_promises,
)
from .career_governance import (
    _ensure_scaled_governance_budget,
    _executive_annual_budget_mi,
    _executive_population_basis,
    _presidential_investment_cap_mi,
    governance_territory_for,
)
from .career_election import resolve_career_election


def advance_career(state: dict[str, Any], before: date, after: date) -> list[str]:
    career = state.get("career") or {}
    if not career.get("mode"):
        return []
    messages: list[str] = []
    election_day = date.fromisoformat(career["election_date"])
    campaign_start = date.fromisoformat(career.get("campaign_start", (election_day - timedelta(days=90)).isoformat()))
    if career["phase"] in {"office", "pre_campaign"} and before < campaign_start <= after:
        career["phase"] = "campaign"
        state["career_status"] = "campaigning"
        career["result"] = None
        career["vote_share"] = None
        career["last_action_date"] = None
        career["campaign_fund_mi"] = round(max(career["campaign_fund_mi"], OFFICES[career["office"]]["fund_mi"] * 0.45), 3)
        performance = career.get("governance") or {}
        performance_bonus = min(4.0, float(performance.get("delivery", 0)) * 0.12 + (float(performance.get("trust", 50)) - 50) * 0.08)
        career["poll_support"] = round(_clamp(33 + float(performance.get("trust", 50)) * 0.18 + performance_bonus), 2)
        _record_public_poll(state, career, campaign_start)
        messages.append("A janela eleitoral da reta final abriu. A avaliação do mandato e as novas atividades passam a afetar a tentativa de reeleição.")
    if career["phase"] in {"campaign", "runoff_campaign"}:
        from . import campaign_events
        messages.extend(campaign_events.tick_rivals(state, career, before, after))
        for poll_date in _campaign_poll_schedule(career):
            if before < poll_date <= after:
                _record_public_poll(state, career, poll_date)
    if career["phase"] in {"campaign", "runoff_campaign", "runoff_observer"} and before < election_day <= after:
        messages.append(resolve_career_election(state, election_day))
    transition_date = career.get("transition_date")
    if career["phase"] == "transition" and transition_date and before < date.fromisoformat(transition_date) <= after:
        career["phase"] = "office"
        career["office_start"] = transition_date
        career["term_end"] = (date.fromisoformat(transition_date).replace(year=date.fromisoformat(transition_date).year + career["term_years"]) - timedelta(days=1)).isoformat()
        next_election_year = date.fromisoformat(transition_date).year + career["term_years"] - 1
        reelection_day = _regular_election_day(career["office"], date.fromisoformat(career["election_date"]), next_election_year)
        career["election_date"] = reelection_day.isoformat()
        annual_budget = (_presidential_investment_cap_mi(state) if career["office"] == "presidente"
                         else _executive_annual_budget_mi(career) if career["office"] in EXECUTIVE_BUDGET_BASELINES else 0.0)
        population_basis = _executive_population_basis(career)
        career["governance"] = {"budget_mi": annual_budget, "annual_budget_mi": annual_budget,
                                "budget_year": date.fromisoformat(transition_date).year, "trust": 50.0, "delivery": 0.0,
                                "budget_price_index": 1.0, "political_capital": 50.0, "actions": [], "pipeline": [],
                                "budget_source": "federal_investment" if career["office"] == "presidente" else "career_reserve",
                                "budget_scale_version": 1 if career["office"] in EXECUTIVE_BUDGET_BASELINES else 0,
                                "budget_population": population_basis["population"] if career["office"] in EXECUTIVE_BUDGET_BASELINES else None,
                                "budget_population_reference_year": population_basis["reference_year"] if career["office"] in EXECUTIVE_BUDGET_BASELINES else None,
                                "investment_commitment_mi": 0.0,
                                "outcomes": {"education": 50.0, "health": 50.0, "security": 50.0, "mobility": 50.0,
                                             "sanitation": 50.0, "infrastructure": 50.0, "employment": 50.0}}
        _activate_campaign_promises(state, career, date.fromisoformat(transition_date), reset_existing=True)
        state["office_status"] = "elected_official"
        state["career_status"] = "in_office"
        state["term_start"] = transition_date
        state["term"] = 1
        address = ensure_communications_state(state)["inauguration"]
        address.update({"required": True, "delivered": False, "legacy_save": False,
                        "date": None, "text": "", "score": None, "rubric": {}})
        territory = career.get("municipality") or ("Brasil" if career.get("office") == "presidente" else career.get("state_name", career.get("state_code", "")))
        messages.append(f"Posse simulada: você assume o cargo de {career['office_label']} em {territory}.")
        messages.append("O primeiro pronunciamento de posse precisa ser registrado antes de novas decisões.")
    if career["phase"] == "office" and after.isoformat() > career.get("term_end", "9999-12-31"):
        career["phase"] = "term_complete"
        state["office_status"] = "former_official"
        state["career_status"] = "term_complete"
        messages.append("O mandato simulado terminou. Seu histórico e as próximas opções de carreira continuam disponíveis.")
    if career["phase"] == "outgoing" and after.isoformat() > career.get("term_end", "9999-12-31"):
        career["phase"] = "opposition"
        state["office_status"] = "former_official"
        state["career_status"] = "opposition"
        messages.append("A transição simulada foi concluída. Você deixa o cargo e segue na oposição; o histórico do mandato permanece salvo.")
    governance = career.get("governance") or {}
    _ensure_scaled_governance_budget(career, governance)
    if is_career_governing(career, after) and governance:
        budget_year = int(governance.get("budget_year", before.year))
        if after.year > budget_year:
            price_index = float(governance.get("budget_price_index", 1.0))
            inflation_pct = float(state.get("metrics", {}).get("inflation", 4.5))
            annual_price_change = min(0.25, max(0.0, inflation_pct / 100.0))
            for _ in range(after.year - budget_year):
                price_index *= 1.0 + annual_price_change
            governance["budget_price_index"] = round(price_index, 4)
            if career["office"] == "presidente":
                annual = _presidential_investment_cap_mi(state)
                governance["investment_commitment_mi"] = 0.0
                governance["budget_source"] = "federal_investment"
                governance["budget_mi"] = round(annual, 1)
                governance["annual_budget_mi"] = round(annual, 1)
            elif career["office"] in EXECUTIVE_BUDGET_BASELINES:
                annual = _executive_annual_budget_mi(career, price_index)
                basis = _executive_population_basis(career)
                governance["budget_mi"] = annual
                governance["annual_budget_mi"] = annual
                governance["budget_population"] = basis["population"]
                governance["budget_population_reference_year"] = basis["reference_year"]
            else:
                annual = float(governance.get("annual_budget_mi", 0))
                governance["budget_mi"] = round(min(annual, float(governance.get("budget_mi", 0)) + annual), 1)
            governance["budget_scale_version"] = 1 if career["office"] in EXECUTIVE_BUDGET_BASELINES else governance.get("budget_scale_version", 0)
            governance["budget_year"] = after.year
            if career["office"] in LEGISLATIVE_OFFICES:
                governance["political_capital"] = min(100.0, float(governance.get("political_capital", 50)) + 25.0)
            reserve_name = "a dotação federal de investimentos" if career["office"] == "presidente" else "a reserva anual simulada"
            messages.append(f"O novo ano começou: {reserve_name} foi atualizada e o custo-base dos programas subiu {annual_price_change * 100:.1f}% pela inflação do cenário.")
        remaining = []
        for item in governance.get("pipeline", []):
            due = date.fromisoformat(item["due_date"])
            if not before < due <= after:
                remaining.append(item)
                continue
            if item["kind"] == "service":
                area = SERVICE_AREAS[item["area"]]
                outcomes = governance.setdefault("outcomes", {})
                outcomes[area["outcome"]] = _clamp(outcomes.get(area["outcome"], 50) + item["effect"])
                if item.get("area") == "employment" and career.get("office") == "presidente":
                    metrics = state.setdefault("metrics", {})
                    metrics["unemployment"] = round(max(2.0, float(metrics.get("unemployment", 7.2)) - .25), 2)
                    metrics["gdp_growth"] = round(float(metrics.get("gdp_growth", 2.1)) + .1, 2)
                governance["delivery"] = float(governance.get("delivery", 0)) + 1
                governance["trust"] = _clamp(governance.get("trust", 50) + 1.5)
                item["status"] = "delivered"
                item["completed_at"] = due.isoformat()
                governance.setdefault("actions", []).append(item)
                territory = item.get("territory") or governance_territory_for(career)["name"]
                messages.append(f"Entrega simulada concluída: {item['title']} em {territory}. O indicador de serviço sobe para {outcomes[area['outcome']]:.1f}.")
            elif item["kind"] == "bill":
                support = float(state.get("metrics", {}).get("congress_support", 50)) if career["scope"] == "federal" else float(career.get("state_support", 50))
                rng = random.Random(f"{state.get('campaign_seed', 1)}:{item['id']}:vote")
                approved = rng.random() < max(.12, min(.88, .12 + support / 100 * .68))
                item["status"] = "approved" if approved else "rejected"
                if approved:
                    governance["delivery"] = float(governance.get("delivery", 0)) + 1
                    governance["trust"] = _clamp(governance.get("trust", 50) + 2.0)
                    career["local_support"] = _clamp(career.get("local_support", 50) + 1.0)
                    messages.append(f"Proposta legislativa aprovada na simulação: {item['title']}.")
                else:
                    governance["trust"] = _clamp(governance.get("trust", 50) - 1.0)
                    messages.append(f"Proposta legislativa rejeitada na simulação: {item['title']}.")
                governance.setdefault("actions", []).append(item)
            elif item["kind"] == "oversight":
                item["status"] = "concluded"
                governance["trust"] = _clamp(governance.get("trust", 50) + 1.5)
                governance.setdefault("actions", []).append(item)
                messages.append(f"Fiscalização simulada concluída: {item['title']}. O relatório foi publicado na agenda.")
        governance["pipeline"] = remaining
    messages.extend(_review_campaign_promises(state, career, before, after))
    return [message for message in messages if message]
