from __future__ import annotations

import re
import unicodedata
from datetime import date
from typing import Any

from .politics import campaign_active, election_date
from .electoral_integrity import campaign_conduct_preview, resolve_campaign_conduct
from .geography import get_municipality
from .issues import ISSUE_LABELS, canonical_issue_ids, issue_label


REGIONS = {
    "norte": {"label": "Norte", "weight": 0.09},
    "nordeste": {"label": "Nordeste", "weight": 0.27},
    "centro_oeste": {"label": "Centro-Oeste", "weight": 0.08},
    "sudeste": {"label": "Sudeste", "weight": 0.42},
    "sul": {"label": "Sul", "weight": 0.14},
}

ISSUES = {
    "economia": {"label": ISSUE_LABELS["economia"], "groups": ["trabalhadores", "pequenos_negocios", "classe_media"]},
    "seguranca": {"label": ISSUE_LABELS["seguranca"], "groups": ["familias", "juventude", "profissionais_seguranca"]},
    "saude": {"label": ISSUE_LABELS["saude"], "groups": ["familias", "servidores"]},
    "educacao": {"label": ISSUE_LABELS["educacao"], "groups": ["familias", "servidores", "juventude"]},
    # Old presidential campaign saves can still submit this combined topic.
    "servicos": {"label": issue_label("servicos"), "groups": ["familias", "servidores", "juventude"]},
    "trabalho": {"label": ISSUE_LABELS["trabalho"], "groups": ["trabalhadores", "pequenos_negocios", "juventude"]},
    "integridade": {"label": ISSUE_LABELS["integridade"], "groups": ["classe_media", "juventude", "servidores"]},
}

GROUP_LABELS = {
    "trabalhadores": "Trabalhadores",
    "pequenos_negocios": "Pequenos negócios",
    "classe_media": "Classe média",
    "familias": "Famílias",
    "juventude": "Jovens",
    "profissionais_seguranca": "Profissionais de segurança",
    "servidores": "Servidores públicos",
    "rural": "População rural",
}

ACTIVITIES = {
    "comicio": {"label": "Comício", "days": 2, "cost_bi": 0.08, "reach": 1.0},
    "entrevista": {"label": "Entrevista", "days": 1, "cost_bi": 0.015, "reach": 0.55},
    "debate": {"label": "Debate", "days": 1, "cost_bi": 0.03, "reach": 0.8},
    "encontro": {"label": "Encontro regional", "days": 1, "cost_bi": 0.02, "reach": 0.65},
}
TRAVEL_ACTIVITIES = {"comicio", "encontro"}
CAMPAIGN_BASE_CITY_ID = "5300108"  # Brasília, início da campanha nacional

TOPIC_TERMS = {
    "economia": {"preco", "precos", "inflacao", "renda", "imposto", "credito", "custo", "economia", "salario", "conta", "divida"},
    "seguranca": {"seguranca", "crime", "policia", "investigacao", "violencia", "vitima", "faccao"},
    "saude": {"saude", "hospital", "medico", "posto", "atendimento", "vacina"},
    "educacao": {"escola", "educacao", "professor", "aluno", "universidade", "creche"},
    "servicos": {"saude", "hospital", "medico", "escola", "educacao", "professor", "atendimento", "vacina"},
    "trabalho": {"emprego", "trabalho", "trabalhador", "salario", "qualificacao", "pequeno negocio", "empresa", "renda"},
    "integridade": {"transparencia", "auditoria", "contrato", "publicar", "controle", "corrupcao", "investigar", "prestacao de contas"},
}

CONCRETE_TERMS = {"prazo", "publicar", "metas", "fiscalizar", "auditoria", "equipe", "orçamento", "orcamento", "proposta", "entregar", "investigar", "plano", "medir", "relatório", "relatorio", "financiar", "treinar", "construir", "ampliar", "reduzir"}
EMPATHY_TERMS = {"família", "familia", "famílias", "familias", "medo", "dor", "respeito", "escutar", "ouvir", "comunidade", "vítima", "vitima", "trabalhador", "paciente", "aluno", "cuidado"}
ACCOUNTABILITY_TERMS = {"reconheço", "reconheco", "errei", "responsabilidade", "prestação de contas", "prestacao de contas", "resultado", "cobrar", "acompanhar"}
PROMISE_TERMS = {"garanto tudo", "resolver tudo", "acabar com todo", "nunca mais", "sem custo", "em 24 horas"}
ATTACK_TERMS = {"lixo", "bandido" , "inimigo do povo", "vagabundo", "traidor"}


def _normal(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text.casefold())
    return "".join(char for char in decomposed if unicodedata.category(char) != "Mn")


def _terms(text: str, terms: set[str]) -> int:
    normalized = _normal(text)
    return sum(1 for term in terms if _normal(term) in normalized)


def ensure_campaign_state(state: dict[str, Any]) -> dict[str, Any]:
    campaign = state.setdefault("campaign", {})
    campaign.setdefault("version", 1)
    campaign.setdefault("regional_support", {key: 50.0 for key in REGIONS})
    campaign.setdefault("group_support", {key: 50.0 for key in GROUP_LABELS})
    campaign.setdefault("funds_bi", 1.2)
    campaign.setdefault("fatigue", 0)
    campaign.setdefault("momentum", 0.0)
    campaign.setdefault("last_action_date", None)
    campaign.setdefault("activities", [])
    campaign.setdefault("municipality_support", {})
    campaign.setdefault("preparation", {"organization": 35.0, "program_detail": 30.0, "coalition": 35.0})
    campaign.setdefault("conduct", {"attempts": 0, "detected": 0, "election_penalty": 0.0, "history": []})
    # Keep saves created before the campaign engine usable.
    for key in REGIONS:
        campaign["regional_support"].setdefault(key, 50.0)
    for key in GROUP_LABELS:
        campaign["group_support"].setdefault(key, 50.0)
    refresh_support(campaign)
    return campaign


def refresh_support(campaign: dict[str, Any]) -> None:
    region_value = sum(campaign["regional_support"][key] * item["weight"] for key, item in REGIONS.items())
    group_value = sum(campaign["group_support"].values()) / max(1, len(campaign["group_support"]))
    campaign["national_support"] = round(max(0.0, min(100.0, region_value * 0.75 + group_value * 0.25)), 1)


def campaign_overview(state: dict[str, Any]) -> dict[str, Any]:
    campaign = ensure_campaign_state(state)
    today = date.fromisoformat(state["date"])
    election = election_date(state)
    active = campaign_active(state, today) and not state.get("election", {}).get("result")
    election_result = state.get("election", {}).get("result")
    transition_date = state.get("election", {}).get("transition_date")
    last_action = campaign.get("last_action_date")
    wait = max(0, 7 - (today - date.fromisoformat(last_action)).days) if last_action else 0
    campaign_start = election.fromordinal(election.toordinal() - 90)
    recent_city_ids = []
    for activity in reversed(campaign["activities"]):
        city_id = activity.get("municipality_id")
        if city_id and city_id not in recent_city_ids:
            recent_city_ids.append(city_id)
        if len(recent_city_ids) >= 8:
            break
    city_support = []
    for city_id in recent_city_ids:
        profile = get_municipality(city_id)
        if profile:
            city_support.append({
                "municipality_id": city_id,
                "municipality_name": profile["name"],
                "state_code": profile["state_code"],
                "electorate_count": profile.get("electorate_count"),
                "electorate_reference_year": profile.get("electorate_reference_year"),
                "support": round(float(campaign["municipality_support"].get(city_id, 50.0)), 1),
            })
    return {
        "active": active,
        "finished": bool(election_result),
        "result": election_result,
        "conduct_review": state.get("election", {}).get("conduct_review"),
        "transition_date": transition_date,
        "transition_complete": bool(transition_date and today >= date.fromisoformat(transition_date)),
        "election_date": election.isoformat(),
        "campaign_start": campaign_start.isoformat(),
        "days_until_election": max(0, (election - today).days),
        "days_until_campaign": max(0, (campaign_start - today).days),
        "days_until_action": wait,
        "can_act": active and wait == 0,
        "national_support": campaign["national_support"],
        "momentum": campaign["momentum"],
        "fatigue": campaign["fatigue"],
        "funds_bi": round(campaign["funds_bi"], 3),
        "preparation": campaign["preparation"],
        "regions": [{"key": key, **region, "support": round(campaign["regional_support"][key], 1)} for key, region in REGIONS.items()],
        "municipalities": city_support,
        "groups": [{"key": key, "label": GROUP_LABELS[key], "support": round(value, 1)} for key, value in campaign["group_support"].items()],
        "activities": list(reversed(campaign["activities"][-8:])),
        "activity_options": [{"key": key, "label": item["label"], "days": item["days"], "cost_bi": item["cost_bi"]} for key, item in ACTIVITIES.items()],
        "region_options": [{"key": key, "label": item["label"]} for key, item in REGIONS.items()],
        "issue_options": [{"key": key, "label": item["label"]} for key, item in ISSUES.items() if key != "servicos"],
        "rules": {"weekly_action_limit": 1, "government_keeps_running": True, "election_is_simulated": True},
        "conduct_preview": campaign_conduct_preview(state, campaign),
    }


def _speech_score(issue: str, message: str) -> tuple[int, dict[str, int]]:
    words = re.findall(r"[\wÀ-ÿ'-]+", message.casefold())
    lower = message.casefold()
    relevance = min(25, _terms(message, TOPIC_TERMS[issue]) * 9)
    concrete = min(22, _terms(message, CONCRETE_TERMS) * 7)
    empathy = min(14, _terms(message, EMPATHY_TERMS) * 7)
    accountability = min(12, _terms(message, ACCOUNTABILITY_TERMS) * 6)
    length = 8 if 25 <= len(words) <= 95 else 3 if 14 <= len(words) <= 130 else -8
    overpromise = min(18, sum(9 for phrase in PROMISE_TERMS if _normal(phrase) in _normal(lower)))
    personal_attack = min(12, sum(6 for phrase in ATTACK_TERMS if _normal(phrase) in _normal(lower)))
    score = max(0, min(100, 39 + relevance + concrete + empathy + accountability + length - overpromise - personal_attack))
    return score, {"tema": relevance, "proposta concreta": concrete, "conexão humana": empathy,
                   "responsabilidade": accountability, "clareza": length, "promessas vagas": -overpromise,
                   "ataques pessoais": -personal_attack}


def perform_campaign_action(state: dict[str, Any], activity_type: str, region: str,
                            issue: str, message: str, conduct: str = "regular",
                            municipality_id: str | None = None) -> dict[str, Any]:
    today = date.fromisoformat(state["date"])
    campaign = ensure_campaign_state(state)
    overview = campaign_overview(state)
    if not overview["active"]:
        raise ValueError("A campanha presidencial ainda não está aberta no calendário da partida.")
    if activity_type not in ACTIVITIES:
        raise ValueError("Escolha um formato de campanha válido.")
    target_municipality = get_municipality(municipality_id) if municipality_id else None
    if municipality_id and not target_municipality:
        raise ValueError("Cidade nao encontrada no catalogo oficial do IBGE.")
    if target_municipality:
        region = target_municipality["macroregion"]
    if region not in REGIONS:
        raise ValueError("Escolha uma região válida.")
    if issue not in ISSUES:
        raise ValueError("Escolha um tema válido.")
    if len(message.strip()) < 12:
        raise ValueError("Escreva ao menos 12 caracteres para o discurso ou resposta.")
    if overview["days_until_action"] > 0:
        raise ValueError(f"A agenda de campanha já foi usada. Aguarde {overview['days_until_action']} dia(s).")
    activity = ACTIVITIES[activity_type]
    if campaign["funds_bi"] < activity["cost_bi"]:
        raise ValueError("O caixa simulado da campanha não cobre esta atividade.")

    travel_from = None
    travel_days = 0
    if target_municipality and activity_type in TRAVEL_ACTIVITIES:
        previous_city_id = next((item.get("municipality_id") for item in reversed(campaign["activities"])
                                 if item.get("type") in TRAVEL_ACTIVITIES and item.get("municipality_id")), CAMPAIGN_BASE_CITY_ID)
        travel_from = get_municipality(previous_city_id)
        if travel_from and travel_from["ibge_code"] != target_municipality["ibge_code"]:
            travel_days = 1 if (
                travel_from["state_code"] == target_municipality["state_code"]
                or travel_from["macroregion"] == target_municipality["macroregion"]
            ) else 2
    days_cost = activity["days"] + travel_days

    score, rubric = _speech_score(issue, message)
    quality = (score - 55) / 45
    regional = campaign["regional_support"]
    groups = campaign["group_support"]
    reach_multiplier = float(target_municipality["municipal_campaign_reach_multiplier"]) if target_municipality else 1.0
    local_delta = quality * 0.75 * activity["reach"] * reach_multiplier + (0.12 if activity_type == "comicio" else 0.04)
    electorate_share = float(target_municipality.get("electorate_share_of_macroregion") or 0.0) if target_municipality else 0.0
    regional_delta = local_delta * electorate_share if target_municipality else local_delta
    city_support = campaign["municipality_support"]
    city_id = target_municipality["ibge_code"] if target_municipality else None
    if target_municipality:
        city_support.setdefault(city_id, float(regional[region]))
        city_support[city_id] = round(max(0, min(100, city_support[city_id] + local_delta)), 2)
    regional[region] = round(max(0, min(100, regional[region] + regional_delta)), 2)
    group_delta = quality * 0.42 * activity["reach"]
    affected = ISSUES[issue]["groups"]
    for group in affected:
        groups[group] = round(max(0, min(100, groups[group] + group_delta)), 2)
    conduct_result = resolve_campaign_conduct(
        state, campaign, conduct, f"campaign-{len(campaign['activities']) + 1}-{activity_type}"
    )
    regional[region] = round(max(0, min(100, regional[region] + conduct_result["immediate_support_delta"])), 2)
    if target_municipality:
        city_support[city_id] = round(max(0, min(100, city_support[city_id] + conduct_result["immediate_support_delta"])), 2)
    for group in affected:
        groups[group] = round(max(0, min(100, groups[group] + conduct_result["immediate_support_delta"] * .35)), 2)
    campaign["momentum"] = round(max(-10, min(10, campaign["momentum"] * 0.85 + quality * 0.48)), 2)
    campaign["fatigue"] = min(100, int(campaign["fatigue"]) + (9 if activity_type == "comicio" else 5))
    campaign["funds_bi"] = round(campaign["funds_bi"] - activity["cost_bi"], 3)
    campaign["last_action_date"] = today.isoformat()
    refresh_support(campaign)
    activity_record = {
        "id": f"campaign-{today.isoformat()}-{len(campaign['activities']) + 1}",
        "date": today.isoformat(), "type": activity_type, "label": activity["label"],
        "region": region, "region_label": REGIONS[region]["label"],
        "municipality_id": city_id,
        "municipality_name": target_municipality["name"] if target_municipality else None,
        "municipality_state_code": target_municipality["state_code"] if target_municipality else None,
        "electorate_count": target_municipality.get("electorate_count") if target_municipality else None,
        "electorate_reference_year": target_municipality.get("electorate_reference_year") if target_municipality else None,
        "electorate_share_of_macroregion": electorate_share if target_municipality else None,
        "municipal_reach_multiplier": reach_multiplier if target_municipality else None,
        "municipality_support": round(city_support[city_id], 1) if target_municipality else None,
        "issue": issue, "issue_label": ISSUES[issue]["label"],
        "canonical_issue_ids": list(canonical_issue_ids(issue)),
        "message": message.strip(), "score": score, "rubric": rubric,
        "support_change": round((regional_delta + conduct_result["immediate_support_delta"]) * REGIONS[region]["weight"], 2),
        "regional_change": round(regional_delta + conduct_result["immediate_support_delta"], 2),
        "municipal_change": round(local_delta + conduct_result["immediate_support_delta"], 2) if target_municipality else None,
        "groups_affected": [GROUP_LABELS[key] for key in affected],
        "cost_bi": activity["cost_bi"], "days_cost": days_cost,
        "activity_days": activity["days"], "travel_days": travel_days,
        "travel_from": travel_from["name"] if travel_from and travel_days else None,
        "in_person": activity_type in TRAVEL_ACTIVITIES and bool(target_municipality),
        "simulated": True,
        "conduct": conduct_result,
    }
    campaign["activities"].append(activity_record)
    campaign["activities"] = campaign["activities"][-40:]
    return {"activity": activity_record, "score": score, "rubric": rubric,
            "national_support": campaign["national_support"], "regional_support": round(regional[region], 1),
            "momentum": campaign["momentum"], "days_cost": days_cost,
            "cost_bi": activity["cost_bi"], "message": "A atividade foi registrada; o calendário do governo também avança durante a campanha."}


def campaign_config() -> dict[str, Any]:
    return {"activities": [{"key": key, "label": item["label"], "days": item["days"], "cost_bi": item["cost_bi"]} for key, item in ACTIVITIES.items()],
            "regions": [{"key": key, "label": item["label"]} for key, item in REGIONS.items()],
            "issues": [{"key": key, "label": item["label"]} for key, item in ISSUES.items() if key != "servicos"]}
