"""Apuração da eleição (majoritária e proporcional) e avanço do calendário da carreira.

Parte do ciclo de carreira (antes tudo em career.py; ver career.py, que reexporta estes nomes).
"""
from __future__ import annotations

from . import seats as seats_for

import random
from datetime import date, timedelta
from typing import Any

from .electoral_integrity import settle_campaign_conduct
from .geography import get_municipality
from .career_base import _clamp, _inauguration_date
from .career_polls import _ensure_opponents, _opponent_supports, _requires_second_round, _runoff_vote_results


# Lista aberta simulada (ajustável). Colegas de lista têm força sorteada em torno de LIST_MATE_MEAN;
# a força do jogador vem da campanha (apoio, organização, embalo, desgaste). Elege-se quem fica dentro
# das cadeiras da legenda. Calibrado para: sem campanha ≈ derrota provável; campanha consistente ≈ disputa
# aberta; campanha forte ≈ vitória provável.
LIST_MATE_MEAN = 31.0


LIST_MATE_SD = 11.0


LEGEND_VOTE_SHARE = 0.12       # parte dos votos da legenda que não vai a nenhum nome


TURNOUT_VALID = 0.70           # comparecimento × votos válidos (estimativa do jogo)


def _list_mate_names(rng: random.Random, count: int) -> list[str]:
    return [f"Candidato(a) simulado(a) {i}" for i in range(1, count + 1)]


def _proportional_electorate(career: dict[str, Any]) -> int | None:
    profile = get_municipality(career.get("municipality_id")) if career.get("municipality_id") and career.get("office") == "vereador" else None
    if profile and profile.get("electorate_count"):
        return int(profile["electorate_count"])
    return None


def _proportional_result(career: dict[str, Any], rng: random.Random, strength: float) -> dict[str, Any]:
    """Lista aberta simulada: D'Hondt entre legendas fictícias e ordem interna por votos nominais."""
    profile = get_municipality(career.get("municipality_id")) if career.get("municipality_id") and career.get("office") == "vereador" else None
    seats = seats_for.for_office(career["office"], career.get("state_code"), int(profile["population_estimate"]) if profile else None)
    party_vote = max(3.0, min(60.0, 6.0 + strength * 0.32 + rng.uniform(-2.0, 3.0)))
    weights = [rng.gammavariate(1.7, 1.0) for _ in range(9)]
    total_weight = sum(weights) or 1.0
    votes = [party_vote, *[(100.0 - party_vote) * weight / total_weight for weight in weights]]
    allocations = [0] * len(votes)
    for _ in range(seats):
        winner = max(range(len(votes)), key=lambda index: votes[index] / (allocations[index] + 1))
        allocations[winner] += 1
    party_seats = allocations[0]

    mates = [max(5.0, rng.gauss(LIST_MATE_MEAN, LIST_MATE_SD)) for _ in range(seats)]
    names = _list_mate_names(rng, seats)
    entries = [{"name": career.get("candidate_name") or "Você", "score": max(5.0, float(strength)), "is_player": True},
               *[{"name": names[i], "score": mates[i], "is_player": False} for i in range(seats)]]
    cube_total = sum(e["score"] ** 3 for e in entries)
    nominal = party_vote * (1 - LEGEND_VOTE_SHARE)
    electorate = _proportional_electorate(career)
    valid_votes = int(electorate * TURNOUT_VALID) if electorate else None
    for e in entries:
        e["vote_share"] = round(nominal * e["score"] ** 3 / cube_total, 2)
        e["votes"] = int(valid_votes * e["vote_share"] / 100) if valid_votes else None
    entries.sort(key=lambda e: (e["score"], e["is_player"]), reverse=True)
    for position, e in enumerate(entries, start=1):
        e["rank"] = position
        e["elected"] = position <= party_seats
        e["simulated"] = True
    for e in entries:
        e.pop("score")
    player = next(e for e in entries if e["is_player"])
    last_in = entries[party_seats - 1] if party_seats else None
    first_out = entries[party_seats] if party_seats < len(entries) else None
    if player["elected"]:
        margin_share = round(player["vote_share"] - (first_out["vote_share"] if first_out else 0.0), 2)
    else:
        margin_share = round((last_in["vote_share"] if last_in else party_vote) - player["vote_share"], 2)
    shown = max(party_seats + 2, 5)
    return {
        "system": "proporcional_simulado", "district_magnitude": seats,
        "party_vote_share": round(party_vote, 1), "party_seats": party_seats,
        "candidate_list_rank": player["rank"], "candidate_vote_share": player["vote_share"], "candidate_votes": player["votes"],
        "list_size": len(entries), "elected": player["elected"], "margin_share": margin_share,
        "margin_votes": int(valid_votes * margin_share / 100) if valid_votes else None,
        "valid_votes": valid_votes, "list": entries[:shown] + ([player] if player["rank"] > shown else []),
        "method": "Lista aberta simulada: cadeiras por D'Hondt entre legendas fictícias; dentro da legenda, elegem-se os mais votados. "
                  "Nomes, votos e comparecimento são estimativas do jogo.",
        "simulated": True,
    }


def resolve_career_election(state: dict[str, Any], election_day: date) -> str:
    career = state.get("career") or {}
    phase = career.get("phase")
    if not career.get("mode") or phase not in {"campaign", "runoff_campaign", "runoff_observer"}:
        return ""
    from .difficulty import get_difficulty

    difficulty = get_difficulty(state.get("difficulty", "normal"))
    round_number = 2 if phase in {"runoff_campaign", "runoff_observer"} else 1
    seed = f"{career.get('seed', state.get('campaign_seed', 203001))}:career-election:{career['office']}:{election_day.isoformat()}:round-{round_number}"
    conduct_result = (
        career.get("conduct_review") or {"attempts": 0, "detected": 0, "reviewed": False, "vote_penalty": 0.0}
        if phase in {"runoff_campaign", "runoff_observer"}
        else settle_campaign_conduct(state, career, seed)
    )
    rng = random.Random(seed)
    _ensure_opponents(career)
    organization = min(8.0, len(career["activities"]) * 0.55 + float(career.get("pre_campaign_organization", 0)))
    fatigue_penalty = max(0, career["fatigue"] - 60) * 0.035
    volatility = 2.5 * difficulty.get("economic_volatility", 1)
    opposition_pressure = difficulty.get("opposition_pressure", 1)
    opposition_drag = (opposition_pressure - 1) * 2.0
    electoral_result: dict[str, Any] | None = None
    candidate_results: list[dict[str, Any]] = []
    runoff_results: list[dict[str, Any]] = []

    if career["office"] in {"vereador", "deputado_estadual", "deputado_federal"}:
        strength = _clamp(career["poll_support"] * 0.78 + organization + career["momentum"] * 0.35
                          - fatigue_penalty - conduct_result["vote_penalty"] - opposition_drag
                          + rng.uniform(-volatility, volatility) * opposition_pressure)
        electoral_result = _proportional_result(career, rng, strength)
        won = bool(electoral_result["elected"])
        vote_share = electoral_result["candidate_vote_share"]   # voto nominal do jogador (% dos válidos)
        opposition_share = 100 - electoral_result["party_vote_share"]
    elif round_number == 1:
        vote_share = round(_clamp(career["poll_support"] * 0.82 + organization + career["momentum"] * 0.35 + float(career.get("coalition_bonus", 0.0))
                                  - fatigue_penalty - conduct_result["vote_penalty"] - opposition_drag
                                  + rng.uniform(-volatility, volatility) * opposition_pressure), 1)
        opposition_results = _opponent_supports(career, vote_share)
        candidate_results = [{
            "id": "player", "name": career["candidate_name"], "party": career["party"],
            "ideology": career["ideology"], "support": vote_share, "is_player": True, "simulated": True,
        }, *[{
            "id": item["id"], "name": item["name"], "party": item["party"],
            "ideology": item["ideology"], "issue_focus": item["issue_focus"],
            "issue_focus_label": item["issue_focus_label"], "support": item["support"],
            "is_player": False, "simulated": True,
        } for item in opposition_results]]
        candidate_results.sort(key=lambda item: item["support"], reverse=True)
        winner = candidate_results[0]
        if _requires_second_round(career) and float(winner["support"]) <= 50.0:
            runoff_date = election_day + timedelta(days=28)
            finalists = candidate_results[:2]
            career["first_round_date"] = election_day.isoformat()
            career["first_round_poll_support"] = float(career["poll_support"])
            career["first_round_vote_share"] = next(item["support"] for item in candidate_results if item["is_player"])
            career["first_round_results"] = candidate_results
            career["candidate_results"] = candidate_results
            career["runoff_finalists"] = finalists
            career["runoff_results"] = []
            career["runoff_date"] = runoff_date.isoformat()
            career["election_date"] = runoff_date.isoformat()
            career["phase"] = "runoff_campaign" if any(item["is_player"] for item in finalists) else "runoff_observer"
            career["electoral_result"] = {
                "system": "majoritario_simulado", "runoff": True, "round": 1,
                "first_round": candidate_results, "finalists": finalists,
                "runoff_date": runoff_date.isoformat(), "simulated": True,
            }
            career["conduct_review"] = conduct_result
            career["vote_share"] = career["first_round_vote_share"]
            career["opponent_share"] = max(item["support"] for item in candidate_results if not item["is_player"])
            career["result"] = None
            state["career_status"] = "runoff_campaign" if career["phase"] == "runoff_campaign" else "runoff_observer"
            state["office_status"] = "incumbent_caretaker" if career.get("office_start") else "opposition_candidate"
            state.setdefault("simulated_news", []).insert(0, {
                "id": f"career-first-round-{election_day.isoformat()}", "date": election_day.isoformat(),
                "title": "Apura\u00e7\u00e3o simulada: segundo turno", "region": career["state_name"],
                "description": f"{finalists[0]['name']} e {finalists[1]['name']} avan\u00e7aram para a rodada final em {runoff_date.strftime('%d/%m/%Y')}.",
                "simulated": True,
            })
            state["simulated_news"] = state["simulated_news"][:20]
            if career["phase"] == "runoff_campaign":
                return f"Primeiro turno simulado: voc\u00ea avan\u00e7ou para o segundo turno em {runoff_date.strftime('%d/%m/%Y')}. A campanha continua e o mandato segue em funcionamento."
            return f"Primeiro turno simulado: voc\u00ea n\u00e3o avan\u00e7ou. {finalists[0]['name']} e {finalists[1]['name']} disputar\u00e3o o segundo turno em {runoff_date.strftime('%d/%m/%Y')}; a transi\u00e7\u00e3o ainda n\u00e3o terminou."
        won = bool(winner["is_player"])
        opposition_share = max((item["support"] for item in candidate_results if not item["is_player"]), default=0.0)
        career["winning_candidate_name"] = winner["name"]
        electoral_result = {
            "system": "majoritario_simulado", "runoff": False, "round": 1,
            "candidates": candidate_results, "winner_name": winner["name"], "simulated": True,
        }
    else:
        runoff_results = _runoff_vote_results(career)
        if len(runoff_results) != 2:
            return ""
        runoff_noise = rng.uniform(-volatility, volatility) * opposition_pressure
        player_result = next((item for item in runoff_results if item.get("is_player")), None)
        if player_result:
            player_support = round(max(0.0, min(100.0, player_result["support"] - conduct_result["vote_penalty"] + runoff_noise)), 1)
            other_result = next(item for item in runoff_results if not item.get("is_player"))
            runoff_results = sorted([
                {**player_result, "support": player_support},
                {**other_result, "support": round(100 - player_support, 1)},
            ], key=lambda item: item["support"], reverse=True)
        else:
            first_support = round(max(0.0, min(100.0, runoff_results[0]["support"] + runoff_noise)), 1)
            runoff_results = [
                {**runoff_results[0], "support": first_support},
                {**runoff_results[1], "support": round(100 - first_support, 1)},
            ]
        winner = runoff_results[0]
        won = bool(winner.get("is_player"))
        career["winning_candidate_name"] = winner["name"]
        career["runoff_results"] = runoff_results
        candidate_results = career.get("first_round_results", [])
        electoral_result = {
            "system": "majoritario_simulado", "runoff": True, "round": 2,
            "first_round": candidate_results, "final_round": runoff_results,
            "winner_name": winner["name"], "runoff_date": election_day.isoformat(), "simulated": True,
        }
        if player_result:
            vote_share = player_support
            opposition_share = next(item["support"] for item in runoff_results if not item.get("is_player"))
        else:
            vote_share = float(career.get("first_round_vote_share", 0))
            opposition_share = max((item["support"] for item in candidate_results if not item.get("is_player")), default=0.0)

    career["candidate_results"] = candidate_results
    career["vote_share"] = round(vote_share, 1)
    career["opponent_share"] = round(opposition_share, 1)
    career["conduct_review"] = conduct_result
    career["electoral_result"] = electoral_result or {"system": "majoritario_simulado", "runoff": False}
    career["result"] = "won" if won else "lost"
    has_current_mandate = bool(career.get("office_start"))
    career["phase"] = "transition" if won else "outgoing" if has_current_mandate else "opposition"
    state["office_status"] = "elected_transition" if won else "incumbent_caretaker" if has_current_mandate else "opposition_candidate"
    state["career_status"] = "transition" if won else "outgoing" if has_current_mandate else "opposition"
    transition = _inauguration_date(career["office"], election_day)
    career["inauguration_date"] = transition.isoformat()
    career["transition_date"] = transition.isoformat()
    state.setdefault("simulated_news", []).insert(0, {
        "id": f"career-election-{election_day.isoformat()}", "date": election_day.isoformat(),
        "title": f"Resultado eleitoral simulado: {career['office_label']}", "region": career["state_name"],
        "description": f"{career['candidate_name']} recebeu {vote_share:.2f}% dos votos simulados. {'Eleito(a)' if won else 'Não eleito(a)'}.",
        "simulated": True,
    })
    state["simulated_news"] = state["simulated_news"][:20]
    if runoff_results:
        electoral_summary = f"{career.get('winning_candidate_name')} venceu a rodada final simulada entre duas candidaturas."
    elif candidate_results:
        electoral_summary = f"{career.get('winning_candidate_name')} liderou a apura\u00e7\u00e3o simulada com m\u00faltiplas candidaturas."
    else:
        electoral_summary = ""
        if electoral_result:
            er = electoral_result
            electoral_summary = (f"Sua legenda fez {er['party_vote_share']:.1f}% e obteve {er['party_seats']} de {er['district_magnitude']} cadeiras simuladas; "
                                 f"você ficou em {er['candidate_list_rank']}º entre {er['list_size']} nomes da lista. ")
            if er["elected"]:
                electoral_summary += f"Folga sobre o primeiro não eleito: {er['margin_share']:.2f} ponto(s)."
            elif er["party_seats"]:
                electoral_summary += f"Faltaram {er['margin_share']:.2f} ponto(s) para alcançar o último eleito da legenda."
            else:
                electoral_summary += "A legenda não atingiu votos para uma cadeira."
    term_end_label = date.fromisoformat(career["term_end"]).strftime("%d/%m/%Y") if career.get("term_end") else "o fim do mandato atual"
    if won and has_current_mandate:
        continuity = f"A nova posse simulada est\u00e1 marcada para {transition.strftime('%d/%m/%Y')}; o mandato atual segue at\u00e9 {term_end_label}."
    elif won:
        continuity = f"A posse simulada est\u00e1 marcada para {transition.strftime('%d/%m/%Y')}."
    elif has_current_mandate:
        continuity = f"Voc\u00ea permanece no cargo at\u00e9 {term_end_label} e depois segue na oposi\u00e7\u00e3o."
    elif runoff_results and not any(item.get("is_player") for item in runoff_results):
        continuity = "Voc\u00ea segue na oposi\u00e7\u00e3o; a carreira pode continuar com outra disputa ou uma indica\u00e7\u00e3o pol\u00edtica."
    else:
        continuity = "Voc\u00ea segue na oposi\u00e7\u00e3o; a carreira pode continuar com outra disputa ou uma indica\u00e7\u00e3o pol\u00edtica."
    if runoff_results and not any(item.get("is_player") for item in runoff_results):
        return f"Resultado final simulado: sua candidatura ficou fora do segundo turno com {vote_share:.1f}% no primeiro turno. {electoral_summary} {continuity}"
    result_label = "vit\u00f3ria" if won else "derrota"
    if runoff_results:
        return f"Resultado eleitoral simulado no segundo turno: {result_label} com {vote_share:.1f}% dos votos. {electoral_summary} {continuity}"
    proportional = bool(electoral_result and electoral_result.get("system") == "proporcional_simulado")
    share_label = f"{vote_share:.2f}% dos votos válidos em seu nome" if proportional else f"{vote_share:.1f}% dos votos"
    return f"Resultado eleitoral simulado: {result_label} com {share_label}. {electoral_summary} {continuity}"
