"""Atividades de campanha e preparação (discurso, comício, debate) e seus efeitos.

Parte do ciclo de carreira (antes tudo em career.py; ver career.py, que reexporta estes nomes).
"""
from __future__ import annotations

from . import tv_time

import random
from datetime import date
from typing import Any

from .electoral_integrity import resolve_campaign_conduct
from .geography import get_municipality
from .career_base import (
    ACTIVITIES,
    DEBATE_REPLIES,
    GROUPS,
    ISSUES,
    MAX_PRE_CAMPAIGN_ORGANIZATION,
    PRE_CAMPAIGN_ACTIONS,
    TRAVEL_ACTIVITIES,
    _clamp,
    _norm,
)
from .career_access import (
    _campaign,
    _campaign_team_location_id,
    _speech_score,
)
from .career_polls import (
    _ensure_opponents,
)
from .career_promises import (
    _record_campaign_promise,
)
from .career_governance import (
    career_debate_prompt,
)
from .career_overview import (
    career_overview,
)


def perform_career_preparation(state: dict[str, Any], action_type: str) -> dict[str, Any]:
    """Prepare the campaign team before the official window, without voter-facing effects."""
    career = _campaign(state)
    if action_type not in PRE_CAMPAIGN_ACTIONS:
        raise ValueError("Escolha uma atividade de organização pré-campanha disponível.")
    today = date.fromisoformat(state["date"])
    campaign_start = date.fromisoformat(career["campaign_start"])
    if career.get("phase") != "pre_campaign" or today >= campaign_start:
        raise ValueError("A organização interna só está disponível antes da abertura oficial da campanha.")
    last_preparation = career.get("last_preparation_date")
    if last_preparation:
        wait = max(0, 30 - (today - date.fromisoformat(last_preparation)).days)
        if wait:
            raise ValueError(f"A próxima atividade de organização fica disponível em {wait} dia(s).")
    organization = float(career.get("pre_campaign_organization", 0))
    if organization >= MAX_PRE_CAMPAIGN_ORGANIZATION:
        raise ValueError("A equipe já atingiu o limite de organização pré-campanha desta partida.")
    action = PRE_CAMPAIGN_ACTIONS[action_type]
    cost = float(action["cost"])
    if float(career.get("campaign_fund_mi", 0)) < cost:
        raise ValueError("O fundo da candidatura não cobre esta atividade de organização.")
    gain = min(float(action["organization"]), MAX_PRE_CAMPAIGN_ORGANIZATION - organization)
    career["pre_campaign_organization"] = round(organization + gain, 2)
    career["campaign_fund_mi"] = round(float(career["campaign_fund_mi"]) - cost, 4)
    career["spent_mi"] = round(float(career.get("spent_mi", 0)) + cost, 4)
    career["last_preparation_date"] = state["date"]
    record = {
        "id": f"career-preparation-{state['date']}-{len(career.get('preparations', [])) + 1}",
        "date": state["date"], "type": action_type, "label": action["label"],
        "summary": action["summary"], "organization_gain": round(gain, 2),
        "organization_total": career["pre_campaign_organization"], "cost_mi": cost,
        "days_cost": int(action["days"]), "simulated": True,
    }
    career.setdefault("preparations", []).append(record)
    career["preparations"] = career["preparations"][-30:]
    return {
        "preparation": record,
        "organization": career["pre_campaign_organization"],
        "campaign_fund_mi": career["campaign_fund_mi"],
        "days_cost": record["days_cost"],
        "message": f"{action['label']} concluída. A organização da equipe aumentou {gain:.2f} pontos; a pesquisa não muda antes da campanha.",
    }


def perform_career_action(state: dict[str, Any], activity_type: str, issue: str, message: str,
                          conduct: str = "regular", municipality_id: str | None = None, reading: dict[str, Any] | None = None) -> dict[str, Any]:
    career = _campaign(state)
    overview = career_overview(state)
    if not overview["campaign_active"]:
        raise ValueError("A campanha não está aberta nesta data da simulação.")
    if not overview["can_act"]:
        if overview["days_until_action"]:
            raise ValueError(f"A agenda de campanha volta a abrir em {overview['days_until_action']} dia(s).")
        raise ValueError("O fundo de campanha simulado acabou.")
    if activity_type not in ACTIVITIES:
        raise ValueError("Escolha uma atividade de campanha válida.")
    if issue not in ISSUES:
        raise ValueError("Escolha um tema válido.")
    if len(message.strip()) < 12:
        raise ValueError("Escreva pelo menos 12 caracteres para a fala ou proposta.")
    activity = ACTIVITIES[activity_type]
    target_municipality = None
    if career["scope"] == "municipal":
        home_city_id = career.get("municipality_id")
        if municipality_id and municipality_id != home_city_id:
            raise ValueError("Campanha municipal só pode fazer atividades no município da candidatura.")
        target_municipality = get_municipality(home_city_id) if home_city_id else None
        if not target_municipality:
            raise ValueError("A cidade da candidatura não está vinculada ao catálogo do IBGE.")
    elif municipality_id:
        target_municipality = get_municipality(municipality_id)
        if not target_municipality:
            raise ValueError("Escolha uma cidade válida no catálogo do IBGE.")
        if career["office"] != "presidente" and target_municipality["state_code"] != career["state_code"]:
            raise ValueError("Essa atividade precisa ocorrer no estado da candidatura.")
    elif career["office"] != "presidente" and career.get("municipality_id"):
        target_municipality = get_municipality(career["municipality_id"])
    municipality_support = career.get("municipality_support", {})
    target_city_support_before = (
        float(municipality_support.get(
            target_municipality["ibge_code"],
            career.get("campaign_base_local_support", career.get("local_support", 45.0)),
        ))
        if target_municipality else None
    )
    travel_from = None
    travel_days = 0
    if activity_type in TRAVEL_ACTIVITIES and target_municipality:
        source_city_id = _campaign_team_location_id(career)
        travel_from = get_municipality(source_city_id) if source_city_id else None
        if travel_from and travel_from["ibge_code"] != target_municipality["ibge_code"]:
            if travel_from["state_code"] == target_municipality["state_code"] or travel_from["macroregion"] == target_municipality["macroregion"]:
                travel_days = 1
            else:
                travel_days = 2
    days_cost = activity["days"] + travel_days
    traits = (career.get("character") or {}).get("traits", [])
    action_cost = activity["cost"] * (.9 if "gestora" in traits else 1.0)
    if career["campaign_fund_mi"] < action_cost:
        raise ValueError("O saldo do fundo de campanha não cobre essa atividade.")
    score, rubric = _speech_score(issue, message)
    reading_public = None
    if reading is not None:  # leitura estruturada do discurso (Gemini ou local): o motor converte em nota e em pressão sobre rivais
        from . import electoral_field, speech_score
        score, rubric = speech_score.score_reading(reading, issue)
        names = {r["id"]: r["name"] for r in _ensure_opponents(career)}
        if career.get("office") in electoral_field.MAJORITARIAN:
            quality = (score - 55) / 45
            for attack in reading.get("attacks", []):
                if attack.get("target") in names:
                    electoral_field.apply_pressure(career, attack["target"], -0.6 if attack.get("personal") else max(0.0, 1.2 * quality))
            electoral_field.decay_pressure(career)
        reading_public = speech_score.public(reading, ISSUES, names)
    if "tecnica" in traits and rubric.get("proposta verificável", 0) > 0:
        score = min(100, score + 3)
        rubric["bônus de proposta técnica"] = 3
    debate_result = None
    if activity_type == "debate":
        prompt = career_debate_prompt(career, issue)
        normalized_message = _norm(message)
        topic_hits = sum(1 for term in ISSUES[issue]["terms"] if _norm(term) in normalized_message)
        directness = 4 if topic_hits and rubric.get("proposta verificável", 0) > 0 else 1 if topic_hits else -5
        score = max(0, min(100, score + directness))
        rubric["resposta direta à pergunta"] = directness
        from .difficulty import get_difficulty
        difficulty = get_difficulty(state.get("difficulty", "normal"))
        rng = random.Random(f"{career.get('seed', 1)}:{state['date']}:{issue}:{len(career['activities'])}:debate")
        opponent_score = round(max(35, min(90, 58 + (difficulty["opposition_pressure"] - 1) * 10 + rng.uniform(-9, 9))))
        if score >= opponent_score + 4:
            outcome, support_delta = "won", 0.6
            explanation = "A resposta foi mais clara e verificável que a réplica simulada."
        elif score <= opponent_score - 4:
            outcome, support_delta = "lost", -0.5
            explanation = "A réplica simulada foi mais convincente; a resposta perdeu apoio na pesquisa."
        else:
            outcome, support_delta = "tied", 0.1
            explanation = "As duas respostas tiveram desempenho próximo; o debate quase não alterou a pesquisa."
        debate_result = {
            "moderator": prompt["moderator"], "question": prompt["question"], "scope": prompt["scope"],
            "opponent_reply": DEBATE_REPLIES[issue], "player_score": score, "opponent_score": opponent_score, "outcome": outcome,
            "support_delta": support_delta, "explanation": explanation, "simulated": True,
        }
    quality = (score - 55) / 45
    reach = activity["reach"] + (.08 if "combativa" in traits else 0)
    city_reach_multiplier = 1.0
    electorate_share_of_state = None
    electorate_share_of_national = None
    if target_municipality:
        city_reach_multiplier = float(target_municipality["municipal_campaign_reach_multiplier"])
        electorate_share_of_state = target_municipality.get("electorate_share_of_state")
        electorate_share_of_national = target_municipality.get("electorate_share_of_national")
    reach *= city_reach_multiplier
    local_delta = max(-1.0, min(2.6, quality * reach + (0.45 if activity_type in {"comicio", "porta_a_porta"} else 0.1) + (.15 if "carismatica" in traits else 0)))
    local_delta = tv_time.apply(local_delta, career.get("party"))  # horário eleitoral: bancada maior amplia o ganho
    # A city visit changes support locally. Its contribution to a larger
    # electorate is weighted by that city's share of the relevant electorate.
    # Municipal races are entirely inside their selected municipality.
    state_weight = 1.0 if not target_municipality or career["scope"] == "municipal" else float(electorate_share_of_state or 1.0)
    state_delta = local_delta * (0.4 if career["scope"] == "municipal" else 0.72) * state_weight
    national_delta = (
        local_delta * float(electorate_share_of_national)
        if target_municipality and electorate_share_of_national is not None
        else state_delta * 0.25
    )
    poll_territory_delta = (
        local_delta if career["scope"] == "municipal"
        else national_delta if career["office"] == "presidente" and target_municipality
        else state_delta
    )
    career["local_support"] = _clamp(career["local_support"] + local_delta)
    career["state_support"] = _clamp(career["state_support"] + state_delta)
    career["national_support"] = _clamp(career["national_support"] + national_delta)
    group_delta = quality * reach * 0.65 + (.15 if "conciliadora" in traits else 0) + (.2 if "comunitaria" in traits else 0)
    for group in ISSUES[issue]["groups"]:
        career["group_support"][group] = _clamp(career["group_support"][group] + group_delta)
    conduct_result = resolve_campaign_conduct(
        state, career, conduct, f"career-{len(career['activities']) + 1}-{activity_type}"
    )
    conduct_delta = conduct_result["immediate_support_delta"]
    career["poll_support"] = round(_clamp(career["poll_support"] + conduct_delta), 2)
    career["state_support"] = _clamp(career["state_support"] + conduct_delta * .55)
    career["local_support"] = _clamp(career["local_support"] + conduct_delta)
    if conduct_result["detected"]:
        career["reputation"] = _clamp(float(career.get("reputation", 50)) - 2.0)
    for group in ISSUES[issue]["groups"]:
        career["group_support"][group] = _clamp(career["group_support"][group] + conduct_delta * .35)
    career["poll_support"] = round(_clamp(career["poll_support"] + poll_territory_delta * 0.42 + group_delta * 0.24), 2)
    social_result = None
    if activity.get("audience"):
        rng = random.Random(f"{career.get('seed', 1)}:{state['date']}:{len(career['activities'])}:social")
        clarity_bonus = .08 if any(term in _norm(message) for term in ("fonte", "dados", "prazo", "resultado", "transparencia")) else 0
        exaggeration_penalty = .15 if any(term in _norm(message) for term in ("resolver tudo", "nunca mais", "sem custo")) else 0
        virality = max(.04, min(.78, activity["viral"] + (score - 60) * .008 + clarity_bonus - exaggeration_penalty - career["fatigue"] * .001))
        spread = rng.random() < virality
        if spread and score >= 60:
            effect = min(1.8, max(.25, (score - 55) * .035 * reach + .35))
            event = "ganhou alcance"
        elif spread or score < 48 or exaggeration_penalty:
            effect = -min(1.2, max(.25, (52 - score) * .035 + .25))
            event = "viralizou com reação crítica" if spread else "gerou reação crítica"
        else:
            effect = 0.0
            event = "teve alcance limitado"
        for audience in activity["audience"]:
            career["group_support"][audience] = _clamp(career["group_support"].get(audience, 45) + effect)
        career["poll_support"] = round(_clamp(career["poll_support"] + effect * .12), 2)
        social_result = {"platform": activity["label"].split(" · ")[0], "audience": [GROUPS[item] for item in activity["audience"]],
                         "virality_pct": round(virality * 100), "event": event, "group_effect": round(effect, 2),
                         "explanation": "A chance considera a nota da mensagem, clareza verificável, formato e fadiga da equipe."}
    if debate_result:
        career["poll_support"] = round(_clamp(career["poll_support"] + debate_result["support_delta"]), 2)
        career["local_support"] = _clamp(career["local_support"] + debate_result["support_delta"] * .55)
        career["state_support"] = _clamp(career["state_support"] + debate_result["support_delta"] * .3)
        for group in ISSUES[issue]["groups"]:
            career["group_support"][group] = _clamp(career["group_support"][group] + debate_result["support_delta"] * .35)
    target_city_support = None
    if target_municipality:
        city_delta = local_delta + conduct_delta + (debate_result["support_delta"] * .55 if debate_result else 0.0)
        target_city_support = round(_clamp(target_city_support_before + city_delta), 2)
        career.setdefault("municipality_support", {})[target_municipality["ibge_code"]] = target_city_support
    career["momentum"] = round(max(-10, min(10, career["momentum"] * 0.8 + quality * 1.1)), 2)
    career["fatigue"] = min(100, career["fatigue"] + (8 if activity_type in {"comicio", "porta_a_porta"} else 4) + (2 if "combativa" in traits else 0))
    career["campaign_fund_mi"] = round(career["campaign_fund_mi"] - action_cost, 4)
    career["spent_mi"] = round(career["spent_mi"] + action_cost, 4)
    career["last_action_date"] = state["date"]
    if activity_type in TRAVEL_ACTIVITIES and target_municipality:
        career["campaign_team_municipality_id"] = target_municipality["ibge_code"]
    campaign_promise = _record_campaign_promise(state, career, issue, message)
    record = {
        "id": f"career-{state['date']}-{len(career['activities']) + 1}", "date": state["date"], "type": activity_type,
        "label": activity["label"], "channel": activity["channel"], "issue": issue, "issue_label": ISSUES[issue]["label"],
        "municipality_id": target_municipality["ibge_code"] if target_municipality else None,
        "municipality_name": target_municipality["name"] if target_municipality else None,
        "municipality_state_code": target_municipality["state_code"] if target_municipality else None,
        "municipality_macroregion": target_municipality["macroregion"] if target_municipality else None,
        "municipality_support": target_city_support,
        "electorate_share_of_state": electorate_share_of_state,
        "electorate_share_of_national": electorate_share_of_national,
        "territorial_weight": round(state_weight, 8),
        "municipality_change": round(target_city_support - target_city_support_before, 2)
        if target_city_support is not None else None,
        "travel_days": travel_days,
        "travel_from_municipality_id": travel_from["ibge_code"] if travel_from else None,
        "travel_from_municipality_name": travel_from["name"] if travel_from else None,
        "city_reach_multiplier": city_reach_multiplier,
        "message": message.strip(), "score": score, "rubric": rubric, "reading": reading_public, "local_change": round(local_delta + conduct_delta, 2),
        "state_change": round(state_delta + conduct_delta * .55, 2),
        "national_change": round(national_delta, 4),
        "poll_support": career["poll_support"], "cost_mi": round(action_cost, 4),
        "days_cost": days_cost, "affected_groups": [GROUPS[group] for group in ISSUES[issue]["groups"]], "simulated": True,
        "social_result": social_result, "debate": debate_result, "conduct": conduct_result,
        "campaign_promise_id": campaign_promise.get("id") if campaign_promise and campaign_promise.get("id") else None,
        "character_effects": [f"{trait}: efeito aplicado nesta ação" for trait in traits],
    }
    career["activities"].append(record)
    career["activities"] = career["activities"][-60:]
    result_message = "Ação registrada. A atividade consome o tempo indicado e a campanha continua sujeita ao voto simulado."
    if travel_days:
        result_message += f" O deslocamento de {travel_from['name']} até {target_municipality['name']} consumiu mais {travel_days} dia(s)."
    return {"activity": record, "campaign_promise": campaign_promise, "score": score, "rubric": rubric, "reading": reading_public, "days_cost": days_cost, "poll_support": career["poll_support"],
            "local_support": career["local_support"], "state_support": career["state_support"], "campaign_fund_mi": career["campaign_fund_mi"],
            "municipality_support": target_city_support,
            "social_result": social_result, "debate": debate_result, "forecast": _forecast(career, score), "message": result_message}


def _forecast(career: dict[str, Any], score: int) -> list[dict[str, Any]]:
    quality = (score - 55) / 45
    return [
        {"horizon": "Agora", "effect": f"Pesquisa do candidato em {career['poll_support']:.1f}% e apoio local em {career['local_support']:.1f}%"},
        {"horizon": "Próximas semanas", "effect": "Repetição de mensagem fortalece reconhecimento; fadiga e desgaste reduzem retorno de novas atividades." if career["fatigue"] < 65 else "A equipe está cansada; alternar formato e tema protege o alcance."},
        {"horizon": "Eleição", "effect": "O resultado compara intenção de voto, organização, apoio partidário e uma margem aleatória definida pela dificuldade."},
    ]
