"""Metas da fase e visão geral da carreira entregue à interface.

Parte do ciclo de carreira (antes tudo em career.py; ver career.py, que reexporta estes nomes).
"""
from __future__ import annotations

from . import coalition, tv_time

from datetime import date, timedelta
from typing import Any

from .communications import ensure_communications_state
from .electoral_integrity import campaign_conduct_preview
from .geography import get_municipality, resolve_municipality
from .career_base import (
    ACTIVITIES,
    APPOINTED_PATHS,
    GROUPS,
    ISSUES,
    MAX_PRE_CAMPAIGN_ORGANIZATION,
    OFFICES,
    PRE_CAMPAIGN_ACTIONS,
    TRAVEL_ACTIVITIES,
    _clamp,
)
from .career_access import (
    _campaign_team_location_id,
    is_career_governing,
)
from .career_polls import (
    _ensure_opponents,
    _opponent_supports,
    _projected_public_poll_support,
    _runoff_vote_results,
)
from .career_governance import (
    _ensure_scaled_governance_budget,
    _historical_compare,
    _presidential_investment_cap_mi,
    _presidential_investment_commitment_mi,
    _reference_election,
    career_debate_prompt,
    governance_actions_for,
    governance_territory_for,
)


def _goals(career: dict[str, Any], vote_intent: float, rivals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Metas da fase atual: o que fazer agora, com o quanto já foi feito. Servem à Agenda; não alteram o jogo."""
    phase = career.get("phase")
    acts = career.get("activities", [])
    pending = sum(1 for item in career.get("campaign_promises", []) if item.get("status") == "pending")
    n = lambda value: f"{float(value):.1f}".replace(".", ",")  # noqa: E731 - número no padrão brasileiro
    if phase == "pre_campaign":
        return [{"id": "base", "label": "Montar a base antes da campanha", "detail": "Use as ações de preparação (equipe, mapeamento, aliados).", "done": len(acts) >= 3, "progress": f"{min(len(acts), 3)}/3 ações", "tab": "Carreira"}]
    if phase in {"campaign", "runoff_campaign"}:
        top = max(rivals, key=lambda r: r["support"], default=None)
        goals = [
            {"id": "visitas", "label": "Fazer campanha de rua e de imprensa", "detail": "Comício, porta a porta e entrevistas movem a intenção de voto; o corpo da equipe cansa.", "done": len(acts) >= 6, "progress": f"{min(len(acts), 6)}/6 atividades", "tab": "Carreira"},
            {"id": "debate", "label": "Participar de um debate", "detail": "Debate muda a imagem dos candidatos; exige tema e proposta claros.", "done": any(item.get("type") == "debate" for item in acts), "progress": "feito" if any(item.get("type") == "debate" for item in acts) else "ainda não", "tab": "Carreira"},
        ]
        if top:
            goals.insert(0, {"id": "lider", "label": f"Passar {top['party']} na intenção de voto", "detail": f"Você tem {n(vote_intent)}%; o maior rival tem {n(top['support'])}%.", "done": vote_intent > top["support"], "progress": f"{n(vote_intent)}% contra {n(top['support'])}%", "tab": "Apuração"})
        return goals
    if career.get("governing") or phase == "office":
        return [
            {"id": "promessas", "label": "Cumprir as promessas de campanha", "detail": "O jogo confere as promessas depois de um ano no cargo.", "done": pending == 0, "progress": f"{pending} pendente(s)", "tab": "Carreira"},
            {"id": "aprovacao", "label": "Manter aprovação acima de 50%", "detail": f"Hoje: {n(career.get('poll_support', 0))}%.", "done": float(career.get("poll_support", 0)) >= 50, "progress": f"{n(career.get('poll_support', 0))}%", "tab": "Indicadores"},
        ]
    return [{"id": "proxima", "label": "Escolher a próxima candidatura ou cargo", "detail": "A carreira continua; veja as opções na tela Carreira.", "done": False, "progress": "", "tab": "Carreira"}]


def career_overview(state: dict[str, Any]) -> dict[str, Any] | None:
    career = state.get("career")
    if not career or not career.get("mode"):
        return None
    municipality_profile = career.get("municipality_profile")
    if municipality_profile is None:
        municipality_profile = resolve_municipality(career.get("state_code", ""), career.get("municipality", ""))
        if municipality_profile:
            career["municipality_id"] = municipality_profile["ibge_code"]
            career["municipality_profile"] = municipality_profile
    team_city_id = _campaign_team_location_id(career)
    team_city_profile = get_municipality(team_city_id) if team_city_id else None
    today = date.fromisoformat(state["date"])
    election_day = date.fromisoformat(career["election_date"])
    campaign_start = date.fromisoformat(career.get("campaign_start", (election_day - timedelta(days=90)).isoformat()))
    last_action = career.get("last_action_date")
    wait = max(0, 7 - (today - date.fromisoformat(last_action)).days) if last_action else 0
    opponents = _ensure_opponents(career)
    # Um só número de intenção de voto: a projeção que o motor usa para decidir a eleição (sem o ruído da pesquisa pública).
    vote_intent = round(_projected_public_poll_support(state, career), 1)
    group_mean = sum(float(career["group_support"][key]) for key in GROUPS) / len(GROUPS)
    rivals_now = [{"id": r["id"], "name": r["name"], "party": r["party"], "ideology": r["ideology"], "issue_focus_label": r.get("issue_focus_label"), "support": r["support"],
                   "real_share_pct": r.get("real_share_pct")} for r in _opponent_supports(career, vote_intent)] if career.get("phase") in {"pre_campaign", "campaign"} else []
    role = OFFICES[career["office"]]
    governance = career.get("governance") or {}
    _ensure_scaled_governance_budget(career, governance)
    governance_budget_mi = round(float(governance.get("budget_mi", 0)), 1)
    governance_annual_budget_mi = round(float(governance.get("annual_budget_mi", 0)), 1)
    governance_budget_source = "career_reserve"
    governance_investment_commitment_mi = round(float(governance.get("investment_commitment_mi", 0)), 1)
    if career.get("office") == "presidente" and governance:
        governance_annual_budget_mi = round(_presidential_investment_cap_mi(state), 1)
        governance_investment_commitment_mi = round(_presidential_investment_commitment_mi(governance), 1)
        governance_budget_mi = round(max(0.0, governance_annual_budget_mi - governance_investment_commitment_mi), 1)
        governance_budget_source = "federal_investment"
    governing = is_career_governing(career, today)
    governance_actions = governance_actions_for(career, governance) if governing else []
    governance_territory = governance_territory_for(career)
    governance_wait = max(0, 30 - (today - date.fromisoformat(governance.get("last_action_date", today.isoformat()))).days) if governance.get("last_action_date") else 0
    in_campaign = career["phase"] in {"campaign", "runoff_campaign"} and campaign_start <= today <= election_day
    next_campaign = max(0, (campaign_start - today).days) if career["phase"] in {"office", "pre_campaign"} else 0
    city_support = career.get("municipality_support", {})
    recent_city_ids = []
    for activity in reversed(career.get("activities", [])):
        city_id = activity.get("municipality_id")
        if city_id and city_id not in recent_city_ids:
            recent_city_ids.append(city_id)
        if len(recent_city_ids) >= 6:
            break
    campaign_city_support = []
    for city_id in recent_city_ids:
        profile = get_municipality(city_id)
        if profile and city_id in city_support:
            campaign_city_support.append({
                "municipality_id": city_id,
                "municipality_name": profile["name"],
                "state_code": profile["state_code"],
                "support": round(float(city_support[city_id]), 1),
            })
    return {
        "mode": True, "office": career["office"], "office_label": career["office_label"], "scope": career["scope"],
        "phase": career["phase"], "candidate_name": career["candidate_name"], "party": career["party"], "ideology": career["ideology"],
        "governing": governing,
        "party_alignment_gap": career.get("party_alignment_gap", 0),
        "character": career.get("character", {}),
        "state_code": career["state_code"], "state_name": career["state_name"], "municipality": career["municipality"],
        "campaign_territory": career.get("municipality") or ("Brasil" if career.get("office") == "presidente" else career["state_name"]),
        "municipality_id": career.get("municipality_id"), "municipality_profile": municipality_profile,
        "reference_election": _reference_election(career),
        "historical_compare": _historical_compare(career),
        "campaign_team_location": ({
            "municipality_id": team_city_profile["ibge_code"], "name": team_city_profile["name"],
            "state_code": team_city_profile["state_code"], "macroregion": team_city_profile["macroregion"],
        } if team_city_profile else None),
        "electorate": career["electorate"], "powers": career["powers"], "election_date": career["election_date"],
        "inauguration_date": career["inauguration_date"], "term_end": career["term_end"], "term_years": career["term_years"],
        "days_until_election": max(0, (election_day - today).days),
        "campaign_start_date": campaign_start.isoformat(),
        "days_until_campaign": next_campaign,
        "days_until_inauguration": max(0, (date.fromisoformat(career["inauguration_date"]) - today).days),
        "campaign_active": in_campaign,
        "runoff_active": career.get("phase") in {"runoff_campaign", "runoff_observer"},
        "first_round_date": career.get("first_round_date"), "runoff_date": career.get("runoff_date"),
        "first_round_vote_share": career.get("first_round_vote_share"),
        "first_round_results": career.get("first_round_results", []),
        "runoff_finalists": career.get("runoff_finalists", []),
        "runoff_results": career.get("runoff_results", []),
        "runoff_projection": _runoff_vote_results(career) if career.get("phase") == "runoff_campaign" else [],
        "can_act": in_campaign and wait == 0 and career["campaign_fund_mi"] >= 0.01,
        "pre_campaign_organization": round(float(career.get("pre_campaign_organization", 0)), 2),
        "pre_campaign_organization_cap": MAX_PRE_CAMPAIGN_ORGANIZATION,
        "pre_campaign_preparations": list(reversed(career.get("preparations", [])[-8:])),
        "preparation_wait_days": max(0, 30 - (today - date.fromisoformat(career["last_preparation_date"])).days) if career.get("last_preparation_date") else 0,
        "can_prepare": (
            career.get("phase") == "pre_campaign" and today < campaign_start
            and float(career.get("pre_campaign_organization", 0)) < MAX_PRE_CAMPAIGN_ORGANIZATION
            and (not career.get("last_preparation_date") or (today - date.fromisoformat(career["last_preparation_date"])).days >= 30)
            and any(career.get("campaign_fund_mi", 0) >= action["cost"] for action in PRE_CAMPAIGN_ACTIONS.values())
        ),
        "preparation_options": [{"key": key, **action, "affordable": career.get("campaign_fund_mi", 0) >= action["cost"]} for key, action in PRE_CAMPAIGN_ACTIONS.items()],
        "public_polls": list(reversed(career.get("public_polls", [])[-8:])),
        "latest_public_poll": (career.get("public_polls") or [None])[-1],
        "days_until_action": wait, "poll_support": round(career["poll_support"], 1), "local_support": round(career["local_support"], 1),
        "state_support": round(career["state_support"], 1), "national_support": round(career["national_support"], 1),
        "reputation": round(float(career.get("reputation", 50)), 1), "history": list(reversed(career.get("history", [])[-12:])),
        "campaign_promises": list(reversed(career.get("campaign_promises", [])[-12:])),
        "pending_campaign_promises": sum(item.get("status") == "pending" for item in career.get("campaign_promises", [])),
        "momentum": round(career["momentum"], 1), "fatigue": career["fatigue"],
        "campaign_fund_mi": round(career["campaign_fund_mi"], 3), "spent_mi": round(career["spent_mi"], 3),
        "spending_cap_mi": OFFICES[career["office"]]["fund_mi"], "tv": tv_time.share(career.get("party"), coalition.partner_parties(career)), "coalition": coalition.view(state, career, vote_intent),
        "vote_intent": vote_intent, "rivals": rivals_now, "rival_events": list(career.get("rival_events", []))[:6], "goals": _goals(career, vote_intent, rivals_now), "opponent_share": round(career["opponent_share"], 1), "opponents": [
            {"id": item["id"], "name": item["name"], "party": item["party"], "ideology": item["ideology"],
             "issue_focus": item["issue_focus"], "issue_focus_label": ISSUES[item["issue_focus"]]["label"], "simulated": True}
            for item in opponents
        ], "candidate_results": career.get("candidate_results", []),
        "result": career.get("result"), "vote_share": career.get("vote_share"),
        "conduct_review": career.get("conduct_review"), "electoral_result": career.get("electoral_result"),
        "can_start_campaign": career.get("phase") in {"opposition", "term_complete"},
        "groups": [{"key": key, "label": label, "support": round(_clamp(vote_intent + (career["group_support"][key] - group_mean)), 1)} for key, label in GROUPS.items()],
        "activities": list(reversed(career["activities"][-10:])),
        "campaign_city_support": campaign_city_support,
        "debate_prompts": {key: career_debate_prompt(career, key) for key in ISSUES},
        "activity_options": [{"key": key, "label": item["label"], "days": item["days"], "requires_travel": key in TRAVEL_ACTIVITIES, "cost_mi": round(item["cost"] * (.9 if "gestora" in (career.get("character") or {}).get("traits", []) else 1.0), 4)} for key, item in ACTIVITIES.items()],
        "issue_options": [{"key": key, "label": value["label"]} for key, value in ISSUES.items()],
        "appointment_paths": [{"key": key, **value, "available": career["office"] in value["requires"] and governing} for key, value in APPOINTED_PATHS.items()],
        "governance": career.get("governance"), "next_campaign_days": next_campaign,
        "public_reports": list(reversed((governance.get("public_reports") or [])[-8:])),
        "governance_actions": governance_actions, "governance_wait_days": governance_wait,
        "governance_territory": governance_territory,
        "governance_budget_mi": governance_budget_mi,
        "governance_annual_budget_mi": governance_annual_budget_mi,
        "governance_budget_source": governance_budget_source,
        "governance_investment_commitment_mi": governance_investment_commitment_mi,
        "governance_budget_price_index": round(float(governance.get("budget_price_index", 1.0)), 3),
        "governance_budget_year": int(governance.get("budget_year", today.year)),
        "political_capital": round(float(governance.get("political_capital", 0)), 1),
        "rules": {"campaign_window_days": 90, "activity_cooldown_days": 7, "election_and_vote_simulated": True,
                  "government_keeps_running": True, "player_governs_until_term_end": governing},
        "conduct_preview": campaign_conduct_preview(state, career),
        "inaugural_address": ensure_communications_state(state)["inauguration"],
        "notice": "Candidatos, partidos, pesquisas e resultados desta carreira são gerados para a simulação.",
    }
