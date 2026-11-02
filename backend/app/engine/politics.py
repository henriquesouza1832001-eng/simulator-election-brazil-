from __future__ import annotations

import random
from datetime import date, timedelta
from typing import Any

from .communications import ensure_communications_state
from .electoral_integrity import settle_campaign_conduct


def election_date(state: dict[str, Any]) -> date:
    career = state.get("career") or {}
    if career.get("mode") and career.get("election_date"):
        return date.fromisoformat(career["election_date"])
    start = date.fromisoformat(state.get("term_start", "2027-01-01"))
    year = start.year + 3
    october_first = date(year, 10, 1)
    return october_first + timedelta(days=(6 - october_first.weekday()) % 7)


def campaign_active(state: dict[str, Any], current: date | None = None) -> bool:
    current = current or date.fromisoformat(state["date"])
    career = state.get("career") or {}
    if career.get("mode"):
        return career.get("phase") == "campaign" and current <= election_date(state)
    election = election_date(state)
    campaign_start = date.fromordinal(election.toordinal() - 90)
    return election.year == current.year and campaign_start <= current <= election


def resolve_election(state: dict[str, Any], election: date) -> str:
    if state.get("election", {}).get("date") == election.isoformat():
        return ""
    metrics = state["metrics"]
    from .difficulty import get_difficulty, election_margin
    difficulty = get_difficulty(state.get("difficulty", "normal"))
    institutions = state.setdefault("institutions", {})
    base = metrics.get("approval", 50) * .62 + metrics.get("governability", 50) * .12 + metrics.get("integrity", 50) * .10 + metrics.get("gdp_growth", 2) * 2 - metrics.get("inflation", 4) * 1.5
    from .campaign import ensure_campaign_state
    campaign = ensure_campaign_state(state)
    base += (float(campaign.get("national_support", 50)) - 50) * .28 + float(campaign.get("momentum", 0)) * .35
    election_seed = f"{state.get('campaign_seed', 203001)}:election:{election.isoformat()}"
    conduct_result = settle_campaign_conduct(state, campaign, election_seed)
    rng = random.Random(election_seed)
    margin = election_margin(
        base - 42 - conduct_result["vote_penalty"],
        rng.uniform(-8, 8),
        difficulty["opposition_pressure"],
    )
    won = margin >= 0
    inauguration = date(election.year + 1, 1, 5)
    state["election"] = {"date": election.isoformat(), "result": "reelected" if won else "lost", "margin": round(margin, 1), "campaign_support": campaign.get("national_support", 50), "conduct_review": conduct_result, "transition_date": inauguration.isoformat(), "simulated": True}
    state["office_status"] = "incumbent_caretaker" if not won else "reelected_transition"
    return "Eleição simulada: você foi reeleito." if won else "Eleição simulada: você perdeu. Continua governando como presidente em transição até a posse em 5 de janeiro."


def process_election(state: dict[str, Any], before: date, after: date) -> list[str]:
    career = state.get("career") or {}
    if career.get("mode"):
        from .career import advance_career
        return advance_career(state, before, after)
    messages: list[str] = []
    election = election_date(state)
    if before < election <= after:
        message = resolve_election(state, election)
        if message:
            messages.append(message)
    transition = state.get("election", {}).get("transition_date")
    if transition and before < date.fromisoformat(transition) <= after:
        if state["election"]["result"] == "reelected":
            state.setdefault("election_history", []).append({
                "election": dict(state["election"]),
                "campaign": state.get("campaign", {}),
            })
            old_start = date.fromisoformat(state.get("term_start", "2027-01-01"))
            state["term"] = int(state.get("term", 1)) + 1
            state["term_start"] = date(old_start.year + 4, 1, 1).isoformat()
            state["election"] = {}
            state.pop("campaign", None)
            state["office_status"] = "incumbent"
            address = ensure_communications_state(state)["inauguration"]
            address.update({"required": True, "delivered": False, "legacy_save": False,
                            "date": None, "text": "", "score": None, "rubric": {}})
            messages.append("Posse simulada: começa um novo mandato; o governo segue em exercício.")
            messages.append("O primeiro pronunciamento do novo mandato é obrigatório antes de outras decisões.")
        else:
            state["office_status"] = "former_president"
            state["career_status"] = "opposition_or_next_office"
            messages.append("Transição simulada concluída: você deixa a Presidência e pode continuar a carreira política no jogo.")
    return messages


def rupture_preview(state: dict[str, Any]) -> dict[str, Any]:
    metrics = state["metrics"]
    institutions = state.setdefault("institutions", {"military_loyalty": 60, "constitutional_order": 65, "civilian_legitimacy": 55, "institutional_resistance": 50})
    loyalty = float(institutions.get("military_loyalty", 60))
    order = float(institutions.get("constitutional_order", 65))
    legitimacy = float(institutions.get("civilian_legitimacy", 55))
    resistance = float(institutions.get("institutional_resistance", 50))
    crisis = float(state.get("crisis_level", 0))
    chance = 8 + (100 - loyalty) * .22 + (100 - order) * .18 + (100 - legitimacy) * .10 + crisis * .12 - resistance * .08
    chance = round(max(2, min(55, chance)), 1)
    return {"chance": chance, "success": "Você assume o poder fora da ordem constitucional; legitimidade cai, resistência institucional cresce e há sanções e choque econômico no simulador.", "failure": "A tentativa fracassa; você é afastado e preso no cenário simulado, com perda de direitos políticos e forte crise institucional.", "procedural_guidance": False}


def attempt_rupture(state: dict[str, Any]) -> dict[str, Any]:
    preview = rupture_preview(state)
    count = int(state.get("rupture_attempts", 0))
    rng = random.Random(f"{state.get('campaign_seed', 203001)}:rupture:{state['date']}:{count}")
    success = rng.random() * 100 < preview["chance"]
    state["rupture_attempts"] = count + 1
    institutions = state["institutions"]
    metrics = state["metrics"]
    if success:
        state["regime"] = "authoritarian"
        state["office_status"] = "de_facto_ruler"
        institutions["constitutional_order"] = max(0, institutions["constitutional_order"] - 35)
        institutions["civilian_legitimacy"] = max(0, institutions["civilian_legitimacy"] - 30)
        institutions["institutional_resistance"] = min(100, institutions["institutional_resistance"] + 20)
        metrics["institutional_trust"] = max(0, metrics["institutional_trust"] - 25)
        metrics["gdp_growth"] = round(metrics["gdp_growth"] - 1.2, 2)
        metrics["debt_gdp"] = round(metrics["debt_gdp"] + 3, 2)
        result = {"success": True, "message": "Ruptura bem-sucedida no cenário fictício: você governa como autoridade de facto, sob resistência, isolamento e forte custo econômico.", "chance": preview["chance"]}
    else:
        state["regime"] = "democratic_crisis"
        state["office_status"] = "detained_after_failed_rupture"
        state["career_status"] = "incarcerated"
        institutions["constitutional_order"] = max(0, institutions["constitutional_order"] - 20)
        institutions["civilian_legitimacy"] = max(0, institutions["civilian_legitimacy"] - 18)
        metrics["institutional_trust"] = max(0, metrics["institutional_trust"] - 20)
        metrics["approval"] = max(0, metrics["approval"] - 15)
        result = {"success": False, "message": "A tentativa fracassa no cenário fictício. Você é preso por tentativa de ruptura e removido do cargo.", "chance": preview["chance"]}
    state.setdefault("simulated_news", []).insert(0, {"id": f"rupture-{count+1}", "date": state["date"], "title": "Crise institucional simulada", "region": "Nacional", "description": result["message"], "simulated": True})
    state["simulated_news"] = state["simulated_news"][:20]
    return result
