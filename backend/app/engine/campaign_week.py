"""Campanha em semanas: energia, caixa e ações livres por semana.

Inspirado no que foi observado na tela de campanha do jogo de referência (catálogo de ações com
custo em dinheiro e energia, rendimento decrescente, penalidade abaixo de 35 de energia). Os
números de rendimento e as descrições são desta reconstrução e podem ser ajustados aqui.
"""
from __future__ import annotations

from typing import Any

from .campaign import REGIONS, ensure_campaign_state, refresh_support

ENERGY_MAX = 100
LOW_ENERGY_THRESHOLD = 35
LOW_ENERGY_FACTOR = 0.6
WEEKLY_REST_ENERGY = 20  # recuperação ao fechar a semana (design próprio)

# key: rótulo, custo em R$ milhões, custo de energia, rendimento-base em pontos de apoio regional,
# escopo ("regiao" mira uma região; "nacional" espalha), regras.
ACTIONS: dict[str, dict[str, Any]] = {
    "comicio": {"label": "Comício", "money_mi": 2.0, "energy": 15, "base": 1.6, "scope": "regiao",
                "text": "Forte numa região; rende pouco onde você ainda tem apoio muito baixo."},
    "caminhada": {"label": "Caminhada na capital", "money_mi": 0.3, "energy": 10, "base": 0.6, "scope": "regiao",
                  "text": "Barata e segura, com ganho pequeno."},
    "palanque_governador": {"label": "Palanque com o governador", "money_mi": 0.0, "energy": 8, "base": 1.2, "scope": "regiao",
                            "promise": True, "text": "Gasta uma promessa de campanha e dá ganho duradouro na região."},
    "cabos": {"label": "Cabos eleitorais", "money_mi": 2.5, "energy": 0, "base": 0.0, "scope": "nacional",
              "invest": 0.25, "text": "Investimento: rende um pouco a cada semana até a eleição."},
    "radio": {"label": "Rádio e outdoor", "money_mi": 1.5, "energy": 4, "base": 0.5, "scope": "nacional",
              "text": "Notoriedade ampla e sem risco."},
    "setor": {"label": "Reunião com um setor", "money_mi": 0.0, "energy": 8, "base": 0.9, "scope": "nacional",
              "text": "Conquista um grupo social por algumas semanas."},
    "culto": {"label": "Culto, missa ou romaria", "money_mi": 0.0, "energy": 6, "base": 0.7, "scope": "regiao",
              "text": "Voto religioso; parte dos jovens rejeita."},
    "obra": {"label": "Visitar obra ou tragédia", "money_mi": 0.0, "energy": 10, "base": 0.8, "scope": "regiao",
             "text": "Rende mais em semana de desastre."},
    "entrevista": {"label": "Entrevista ou podcast", "money_mi": 0.0, "energy": 12, "base": 1.0, "scope": "nacional",
                   "risk": 0.5, "text": "Maior risco e maior retorno."},
    "live": {"label": "Live", "money_mi": 0.0, "energy": 6, "base": 0.5, "scope": "nacional",
             "per_week": 1, "text": "Uma por semana."},
    "influenciador": {"label": "Procurar um influenciador", "money_mi": 0.0, "energy": 5, "base": 0.6, "scope": "nacional",
                      "text": "Endosso rende com os jovens."},
    "carreata": {"label": "Carreata", "money_mi": 0.8, "energy": 12, "base": 1.0, "scope": "regiao",
                 "text": "Meio-termo entre caminhada e comício."},
    "vaquinha": {"label": "Vaquinha", "money_mi": 0.0, "energy": 4, "base": 0.0, "scope": "nacional",
                 "cooldown_weeks": 2, "raise_mi": 0.8, "text": "Arrecada pouco, a cada duas semanas."},
    "corpo_a_corpo": {"label": "Corpo a corpo no metrô", "money_mi": 0.1, "energy": 8, "base": 0.5, "scope": "regiao",
                      "text": "Contato direto com quem usa transporte público."},
    "santinho": {"label": "Santinhos e bandeiras", "money_mi": 0.4, "energy": 2, "base": 0.3, "scope": "regiao",
                 "text": "Material de rua, barato em energia."},
    "descansar": {"label": "Descansar", "money_mi": 0.0, "energy": -25, "base": 0.0, "scope": "nacional",
                  "text": "Recupera 25 de energia."},
    "voto_util": {"label": "Apelo ao voto útil", "money_mi": 0.0, "energy": 6, "base": 1.1, "scope": "nacional",
                  "min_week": 8, "text": "Só existe a partir da semana 8."},
}


def free_actions_for_week(week: int) -> int:
    """Ações livres por semana: 1 na primeira, crescendo até 4 (observado 1 e 3; o meio é inferido)."""
    return max(1, min(4, 1 + week // 2))


def _free(week: dict[str, Any]) -> int:
    """Ações livres da semana atual, incluindo extras (ex.: ao recusar um debate)."""
    return free_actions_for_week(week["week"]) + int(week.get("bonus_actions", 0))


def ensure_week_state(state: dict[str, Any]) -> dict[str, Any]:
    campaign = ensure_campaign_state(state)
    week = state.setdefault("campaign_week", {})
    week.setdefault("week", 1)
    week.setdefault("energy", ENERGY_MAX)
    week.setdefault("used", [])            # ações desta semana
    week.setdefault("history", [])         # contagem por (ação, região) para rendimento decrescente
    week.setdefault("last_by_action", {})  # semana da última execução, para recarga
    week.setdefault("investments", {})     # cabos: região -> semanas ativas
    week.setdefault("promises", 3)
    week.setdefault("funds_mi", 25.0)  # caixa semanal em R$ milhões (design próprio)
    return week


GOVERNOR_THRESHOLD = 55.0    # apoio regional + "calor" necessários para o governador aceitar (design próprio)
GOVERNOR_WARMTH_STEP = 5.0
LOW_ENERGY_DEBATE_PENALTY = 8  # observado: energia baixa tira 8 de nota no debate

TRAVEL_SAME = 0
TRAVEL_OTHER_REGION = 5   # observado: "na região −5 energia" (aqui, outra macrorregião)
TRAVEL_JET = (9, 0.5)     # observado: jatinho −9 energia e R$ 0,5 mi


def travel_cost(week: dict[str, Any], region: str | None, jet: bool) -> tuple[int, float]:
    """Energia e dinheiro (R$ mi) para levar a agenda até a região da ação."""
    here = week.get("location")
    if region is None or here is None or here == region:
        return TRAVEL_SAME, 0.0
    return TRAVEL_JET if jet else (TRAVEL_OTHER_REGION, 0.0)


def _repeat_factor(week: dict[str, Any], action: str, region: str) -> float:
    count = sum(1 for h in week["history"] if h["action"] == action and h["region"] == region)
    return max(0.35, 0.8 ** count)  # rendimento decrescente (observado qualitativamente)


def overview(state: dict[str, Any]) -> dict[str, Any]:
    campaign = ensure_campaign_state(state)
    week = ensure_week_state(state)
    free = _free(week)
    used_this_week = len(week["used"])
    catalog = []
    for key, action in ACTIONS.items():
        reason = _blocked_reason(state, key, None)
        catalog.append({"key": key, "label": action["label"], "money_mi": action["money_mi"], "energy": action["energy"],
                        "text": action["text"], "scope": action["scope"], "available": reason is None, "reason": reason})
    return {
        "simulated": True, "week": week["week"], "energy": week["energy"], "energy_max": ENERGY_MAX,
        "funds_mi": round(week["funds_mi"], 2), "free_actions": free,
        "used_actions": used_this_week, "remaining_actions": max(0, free - used_this_week),
        "low_energy": week["energy"] < LOW_ENERGY_THRESHOLD, "promises": week["promises"], "location": week.get("location"),
        "travel": {"other_region_energy": TRAVEL_OTHER_REGION, "jet_energy": TRAVEL_JET[0], "jet_mi": TRAVEL_JET[1]},
        "regions": [{"key": k, "label": v["label"], "support": campaign["regional_support"].get(k)} for k, v in REGIONS.items()],
        "catalog": catalog, "this_week": week["used"], "national_support": campaign.get("national_support"),
    }


def _blocked_reason(state: dict[str, Any], key: str, region: str | None) -> str | None:
    campaign = ensure_campaign_state(state)
    week = ensure_week_state(state)
    action = ACTIONS[key]
    if week["week"] < action.get("min_week", 1):
        return f"Disponível a partir da semana {action['min_week']}."
    if len(week["used"]) >= _free(week):
        return "As ações livres desta semana acabaram. Feche a semana."
    if action["energy"] > 0 and week["energy"] < action["energy"]:
        return "Energia insuficiente. Descanse."
    if action["money_mi"] > week["funds_mi"] + 1e-9:
        return "Caixa insuficiente."
    if action.get("promise") and week["promises"] <= 0:
        return "Sem promessas de campanha para gastar."
    if action.get("per_week") and sum(1 for u in week["used"] if u["action"] == key) >= action["per_week"]:
        return "Só uma por semana."
    cooldown = action.get("cooldown_weeks")
    last = week["last_by_action"].get(key)
    if cooldown and last is not None and week["week"] - last < cooldown:
        return f"Disponível de novo na semana {last + cooldown}."
    return None


def perform(state: dict[str, Any], key: str, region: str | None, jet: bool = False) -> dict[str, Any]:
    if key not in ACTIONS:
        raise ValueError("Ação desconhecida.")
    action = ACTIONS[key]
    if action["scope"] == "regiao" and region not in REGIONS:
        raise ValueError("Escolha uma região para esta ação.")
    reason = _blocked_reason(state, key, region)
    if reason:
        raise ValueError(reason)
    campaign = ensure_campaign_state(state)
    week = ensure_week_state(state)
    trip_energy, trip_money = travel_cost(week, region if action["scope"] == "regiao" else None, jet)
    if week["energy"] < max(0, action["energy"]) + trip_energy:
        raise ValueError(f"Energia insuficiente para a ação e a viagem (viagem: {trip_energy}).")
    if week["funds_mi"] < action["money_mi"] + trip_money:
        raise ValueError("Caixa insuficiente para a ação e a viagem.")
    week["energy"] -= trip_energy
    week["funds_mi"] = round(week["funds_mi"] - trip_money, 2)
    if action["scope"] == "regiao":
        week["location"] = region
    target = region if action["scope"] == "regiao" else "nacional"
    energy_factor = LOW_ENERGY_FACTOR if week["energy"] < LOW_ENERGY_THRESHOLD else 1.0
    repeat = _repeat_factor(week, key, target)
    gain = action["base"] * energy_factor * repeat
    refused = False
    shortfall = 0.0
    if key == "palanque_governador":
        warmth = week.setdefault("warmth", {})
        disposition = float(campaign["regional_support"][region]) + warmth.get(region, 0.0)
        if disposition < GOVERNOR_THRESHOLD:
            refused = True
            shortfall = round(GOVERNOR_THRESHOLD - disposition, 1)
            warmth[region] = warmth.get(region, 0.0) + GOVERNOR_WARMTH_STEP  # fica mais receptivo
            gain = 0.0
    if key == "obra" and any(e.get("kind") == "disaster" for e in state.get("active_crises", []) or []):
        gain *= 1.8
    detail = {"action": key, "label": action["label"], "region": target, "gain": 0.0,
              "travel_energy": trip_energy, "travel_mi": trip_money}
    if action["scope"] == "regiao":
        campaign["regional_support"][region] = round(min(100, campaign["regional_support"][region] + gain), 2)
        detail["gain"] = round(gain, 2)
    elif gain:
        share = gain / len(REGIONS)
        for r in REGIONS:
            campaign["regional_support"][r] = round(min(100, campaign["regional_support"][r] + share), 2)
        detail["gain"] = round(gain, 2)
    if key == "cabos":
        week["investments"]["nacional"] = week["investments"].get("nacional", 0) + 1
    if action.get("raise_mi"):
        week["funds_mi"] = round(week["funds_mi"] + action["raise_mi"] * energy_factor, 2)
        detail["raised_mi"] = round(action["raise_mi"] * energy_factor, 2)
    if action.get("promise") and not refused:
        week["promises"] -= 1
    detail["refused"] = refused
    detail["shortfall"] = shortfall
    if key == "palanque_governador" and not refused:
        from .legislature import add_commitment, party_for_region
        item = add_commitment(state, "ministerio", party_for_region(region), region, week["week"])
        detail["commitment"] = item
    week["funds_mi"] = round(week["funds_mi"] - action["money_mi"], 2)
    week["energy"] = max(0, min(ENERGY_MAX, week["energy"] - action["energy"]))
    week["used"].append(detail)
    week["history"].append({"action": key, "region": target, "week": week["week"]})
    week["history"] = week["history"][-80:]
    week["last_by_action"][key] = week["week"]
    refresh_support(campaign)
    detail["low_energy_penalty"] = energy_factor < 1.0
    detail["repeat_factor"] = round(repeat, 2)
    return {"result": detail, "overview": overview(state)}


def close_week(state: dict[str, Any]) -> dict[str, Any]:
    campaign = ensure_campaign_state(state)
    week = ensure_week_state(state)
    if not week["used"]:
        raise ValueError("Use ao menos uma ação antes de fechar a semana.")
    bonus = 0.0
    if week["investments"].get("nacional"):
        per_week = ACTIONS["cabos"]["invest"] * week["investments"]["nacional"]
        for r in REGIONS:
            campaign["regional_support"][r] = round(min(100, campaign["regional_support"][r] + per_week / len(REGIONS)), 2)
        bonus = per_week
    gained = round(sum(u["gain"] for u in week["used"]) + bonus, 2)
    week["week"] += 1
    week["bonus_actions"] = 0
    week["energy"] = min(ENERGY_MAX, week["energy"] + WEEKLY_REST_ENERGY)
    closed = week["used"]
    week["used"] = []
    refresh_support(campaign)
    return {"closed_actions": closed, "points_gained": gained, "overview": overview(state)}
