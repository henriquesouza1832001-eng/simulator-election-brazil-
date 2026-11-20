"""Rivais, pesquisas públicas, segundo turno e projeção de voto.

Parte do ciclo de carreira (antes tudo em career.py; ver career.py, que reexporta estes nomes).
"""
from __future__ import annotations


import random
from math import sqrt
from datetime import date, timedelta
from typing import Any

from .career_base import (
    IDEOLOGY_SPECTRUM,
    ISSUES,
    OPPONENT_CANDIDATE_POOL,
    SPECTRUM_ORDER,
    _clamp,
)


def _campaign_poll_schedule(career: dict[str, Any]) -> list[date]:
    start = date.fromisoformat(career["campaign_start"])
    election = date.fromisoformat(career["election_date"])
    scheduled = [start]
    for offset in (30, 60):
        poll_date = start + timedelta(days=offset)
        if poll_date < election:
            scheduled.append(poll_date)
    final_poll = election - timedelta(days=3)
    if final_poll > scheduled[-1]:
        scheduled.append(final_poll)
    return scheduled


def _public_poll_sample_size(career: dict[str, Any]) -> int:
    if career.get("scope") == "municipal":
        population = float((career.get("municipality_profile") or {}).get("population_estimate", 0))
        return max(350, min(1200, round(sqrt(population) * 0.8))) if population > 0 else 600
    if career.get("office") == "presidente":
        return 1800
    if career.get("scope") == "estadual":
        return 1000
    return 1200


def _projected_public_poll_support(state: dict[str, Any], career: dict[str, Any]) -> float:
    from .difficulty import get_difficulty

    difficulty = get_difficulty(state.get("difficulty", "normal"))
    organization = min(8.0, len(career.get("activities", [])) * 0.55 + float(career.get("pre_campaign_organization", 0)))
    fatigue_penalty = max(0, float(career.get("fatigue", 0)) - 60) * 0.035
    opposition_drag = (difficulty.get("opposition_pressure", 1) - 1) * 2.0
    conduct_penalty = float((career.get("conduct") or {}).get("election_penalty", 0))
    if career.get("office") in {"vereador", "deputado_estadual", "deputado_federal"}:
        estimate = float(career.get("poll_support", 0)) * 0.78 + organization + float(career.get("momentum", 0)) * 0.35
    else:
        estimate = float(career.get("poll_support", 0)) * 0.82 + organization + float(career.get("momentum", 0)) * 0.35
    return _clamp(estimate - fatigue_penalty - conduct_penalty - opposition_drag)


def _ensure_opponents(career: dict[str, Any]) -> list[dict[str, Any]]:
    from . import electoral_field
    if career.get("office") in electoral_field.MAJORITARIAN:  # campo real: partidos que disputaram o território (TSE), sem o partido do jogador
        return electoral_field.ensure_field(career)
    opponents = career.get("opponents")
    if isinstance(opponents, list) and len(opponents) == 3:
        return opponents
    seed = f"{career.get('seed', 1)}:opponents:{career.get('office', '')}:{career.get('state_code', '')}"
    rng = random.Random(seed)
    selected = rng.sample(OPPONENT_CANDIDATE_POOL, 3)
    opponents = [
        {
            "id": f"opponent-{index + 1}",
            "name": f"Candidato(a) do {profile['party']}",
            **profile,
            "support_weight": round(rng.uniform(0.85, 1.15), 2),
            "simulated": True,
        }
        for index, profile in enumerate(selected)
    ]
    career["opponents"] = opponents
    return opponents


def _opponent_supports(career: dict[str, Any], candidate_support: float) -> list[dict[str, Any]]:
    from . import electoral_field
    if career.get("office") in electoral_field.MAJORITARIAN:
        rows = electoral_field.shares(career, candidate_support)
        return [{**row, "issue_focus_label": ISSUES[row["issue_focus"]]["label"] if row["issue_focus"] in ISSUES else row["issue_focus"]} for row in rows]
    opponents = _ensure_opponents(career)
    opposition_total = round(max(0.0, 100.0 - float(candidate_support)), 1)
    total_weight = sum(float(item.get("support_weight", 1.0)) for item in opponents) or 1.0
    shares: list[dict[str, Any]] = []
    allocated = 0.0
    for index, opponent in enumerate(opponents):
        if index == len(opponents) - 1:
            support = round(opposition_total - allocated, 1)
        else:
            support = round(opposition_total * float(opponent.get("support_weight", 1.0)) / total_weight, 1)
            allocated += support
        shares.append({
            "id": opponent["id"],
            "name": opponent["name"],
            "party": opponent["party"],
            "ideology": opponent["ideology"],
            "issue_focus": opponent["issue_focus"],
            "issue_focus_label": ISSUES[opponent["issue_focus"]]["label"],
            "support": support,
            "simulated": True,
        })
    return shares


def _requires_second_round(career: dict[str, Any]) -> bool:
    office = career.get("office")
    if office in {"presidente", "governador"}:
        return True
    if office != "prefeito":
        return False
    # The game catalogue has resident-population estimates, not voter rolls. Use
    # this only as a clearly marked proxy for the municipal runoff threshold.
    population = float((career.get("municipality_profile") or {}).get("population_estimate", 0))
    return population > 200_000


def _spectrum_index(candidate: dict[str, Any]) -> int:
    spectrum = IDEOLOGY_SPECTRUM.get(candidate.get("ideology", "Centro"), "centro")
    return SPECTRUM_ORDER.index(spectrum)


def _runoff_vote_results(career: dict[str, Any], poll_support: float | None = None,
                         noise: float = 0.0) -> list[dict[str, Any]]:
    first_round = career.get("first_round_results") or []
    finalists = career.get("runoff_finalists") or sorted(
        first_round, key=lambda item: float(item.get("support", 0)), reverse=True,
    )[:2]
    if len(finalists) < 2:
        return []
    first, second = finalists
    first_share = float(first.get("support", 0))
    second_share = float(second.get("support", 0))
    first_distance = _spectrum_index(first)
    second_distance = _spectrum_index(second)
    for eliminated in first_round:
        if eliminated.get("id") in {first.get("id"), second.get("id")}:
            continue
        eliminated_share = float(eliminated.get("support", 0))
        eliminated_distance = _spectrum_index(eliminated)
        first_affinity = 1 / (1 + abs(eliminated_distance - first_distance))
        second_affinity = 1 / (1 + abs(eliminated_distance - second_distance))
        first_transfer = first_affinity / (first_affinity + second_affinity)
        first_transfer = max(.15, min(.85, first_transfer))
        first_share += eliminated_share * first_transfer
        second_share += eliminated_share * (1 - first_transfer)

    if first.get("is_player") or second.get("is_player"):
        baseline = float(career.get("first_round_poll_support", career.get("poll_support", 0)))
        current = float(career.get("poll_support", 0) if poll_support is None else poll_support)
        shift = max(-5.0, min(5.0, (current - baseline) * .3 + float(career.get("momentum", 0)) * .15))
        if first.get("is_player"):
            first_share += shift
            second_share -= shift
        else:
            second_share += shift
            first_share -= shift
    if first.get("is_player"):
        first_share += noise
        second_share -= noise
    elif second.get("is_player"):
        second_share += noise
        first_share -= noise
    else:
        first_share += noise
        second_share -= noise

    first_final = round(max(0.0, min(100.0, first_share)), 1)
    first_result = {**first, "support": first_final, "round": 2, "simulated": True}
    second_result = {**second, "support": round(100 - first_final, 1), "round": 2, "simulated": True}
    return sorted([first_result, second_result], key=lambda item: item["support"], reverse=True)


def _record_public_poll(state: dict[str, Any], career: dict[str, Any], field_date: date) -> dict[str, Any] | None:
    polls = career.setdefault("public_polls", [])
    if any(item.get("date") == field_date.isoformat() for item in polls):
        return None
    from . import campaign_events, electoral_field
    institute = campaign_events.institute_for(len(polls))
    sample_size = max(300, round(_public_poll_sample_size(career) * institute["sample_factor"]))
    margin = round(1.96 * sqrt(0.25 / sample_size) * 100, 1)
    house = campaign_events.house_effect(institute, electoral_field.position(career.get("party"), career.get("ideology")))
    seed = f"{career.get('seed', 1)}:public-poll:{field_date.isoformat()}"
    noise = random.Random(seed).uniform(-margin, margin)
    if career.get("phase") == "runoff_campaign":
        runoff_results = _runoff_vote_results(career, noise=noise)
        player_result = next((item for item in runoff_results if item.get("is_player")), None)
        if not player_result:
            return None
        candidate_support = player_result["support"]
        opponents = [{
            "id": item["id"], "name": item["name"], "party": item["party"],
            "ideology": item.get("ideology", "Centro"), "issue_focus": item.get("issue_focus", "integridade"),
            "issue_focus_label": ISSUES[item.get("issue_focus", "integridade")]["label"],
            "support": item["support"], "simulated": True,
        } for item in runoff_results if not item.get("is_player")]
    else:
        candidate_support = round(_clamp(_projected_public_poll_support(state, career) + noise + house), 1)
        opponents = _opponent_supports(career, candidate_support)
    career["opponent_share"] = max((item["support"] for item in opponents), default=0.0)
    record = {
        "date": field_date.isoformat(),
        "round": 2 if career.get("phase") == "runoff_campaign" else 1,
        "candidate_name": career.get("candidate_name", "Candidatura do jogador"),
        "candidate_support": candidate_support,
        "other_candidates_support": round(100 - candidate_support, 1),
        "opponents": opponents,
        "margin_of_error": margin,
        "sample_size": sample_size,
        "institute": institute["name"], "house_effect": house,
        "simulated": True,
    }
    polls.append(record)
    career["public_polls"] = polls[-12:]
    try:   # a imprensa noticia cada pesquisa publicada (a tela de Imprensa nunca fica vazia em campanha)
        from . import voice
        from .consequences import _book, _post
        top = max(opponents, key=lambda o: o["support"], default=None)
        if top and career.get("phase") in {"campaign", "runoff_campaign"}:
            leading = candidate_support >= top["support"]
            _post(_book(state), state, {"id": f"poll-{field_date.isoformat()}", "kind": "imprensa", "tone": "positivo" if leading else "negativo",
                  "headline": f"Pesquisa {institute['name']}: {str(career.get('candidate_name') or 'você')} tem {candidate_support:.1f}% e {top['party']} tem {top['support']:.1f}% (±{margin:.1f})".replace(".", ","),
                  "body": voice.pick(voice.POLL_LEAD if leading else voice.POLL_TRAIL, f"{career.get('seed', 1)}:{field_date.isoformat()}")})
    except Exception:  # noqa: BLE001 - a notícia é acessória
        pass
    return record
