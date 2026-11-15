"""Apuração da eleição, urna a urna em boletins: o motor já decidiu o resultado; aqui ele só é "contado" aos poucos.

Três formatos, conforme o cargo:
- mapa (Presidência): votos distribuídos pelos 27 estados, com viés regional estável (semente da partida);
- zonas (prefeito, governador, senador): votos distribuídos por zonas da cidade ou regiões do estado;
- lista (vereador, deputado): voto proporcional; cadeiras por quociente (D'Hondt) entre legendas fictícias e ordem por votos nominais.

Os boletins saem ao longo da noite; o início da contagem pode enganar (urnas que chegam primeiro destoam do final),
e a virada acontece quando há motivo. Pesos de eleitorado são estimativas do jogo (arredondadas), não dados oficiais.
"""
from __future__ import annotations

import hashlib
import random
from typing import Any

# UF -> (macrorregião, peso aproximado do eleitorado em %, atraso de fuso)
UFS: dict[str, tuple[str, float, int]] = {
    "AC": ("norte", 0.4, 0), "AL": ("nordeste", 1.5, 0), "AM": ("norte", 1.9, 1), "AP": ("norte", 0.4, 0), "BA": ("nordeste", 7.0, 0),
    "CE": ("nordeste", 4.3, 0), "DF": ("centro_oeste", 1.4, 0), "ES": ("sudeste", 2.0, 0), "GO": ("centro_oeste", 3.2, 0), "MA": ("nordeste", 3.3, 0),
    "MG": ("sudeste", 10.1, 0), "MS": ("centro_oeste", 1.4, 1), "MT": ("centro_oeste", 1.7, 1), "PA": ("norte", 3.9, 0), "PB": ("nordeste", 2.0, 0),
    "PE": ("nordeste", 4.5, 0), "PI": ("nordeste", 1.6, 0), "PR": ("sul", 5.5, 0), "RJ": ("sudeste", 8.3, 0), "RN": ("nordeste", 1.7, 0),
    "RO": ("norte", 0.9, 1), "RR": ("norte", 0.3, 1), "RS": ("sul", 5.4, 0), "SC": ("sul", 3.6, 0), "SE": ("nordeste", 1.1, 0),
    "SP": ("sudeste", 22.4, 0), "TO": ("norte", 0.9, 0),
}
CITY_ZONES = [("Centro", 16.0), ("Zona Norte", 15.0), ("Zona Sul", 17.0), ("Zona Leste", 16.0), ("Zona Oeste", 14.0), ("Periferia", 14.0), ("Área rural", 8.0)]
STATE_ZONES = [("Capital", 22.0), ("Grande capital", 20.0), ("Interior norte", 15.0), ("Interior sul", 15.0), ("Interior leste", 14.0), ("Interior oeste", 14.0)]
STEPS = [("17:00", 0.0), ("18:00", 0.18), ("19:00", 0.45), ("20:00", 0.7), ("21:00", 0.88), ("22:00", 0.97), ("23:30", 1.0)]
PROPORTIONAL = {"vereador", "deputado_estadual", "deputado_federal"}
ZONED = {"prefeito", "governador", "senador"}
ASSEMBLY_FALLBACK = {"vereador": 13, "deputado_estadual": 24, "deputado_federal": 24}
OTHER_PARTIES = ["Legenda A", "Legenda B", "Legenda C", "Legenda D", "Legenda E", "Legenda F", "Legenda G", "Legenda H", "Legenda I"]


def _rnd(seed: str) -> float:
    return int(hashlib.sha256(seed.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF


def _regions(state: dict[str, Any]) -> dict[str, float]:
    return {k: float(v) for k, v in ((state.get("campaign") or {}).get("regional_support") or {}).items()}


def _recenter(raw: dict[str, float], weights: dict[str, float], target: float) -> dict[str, float]:
    total = sum(weights.values())
    mean = sum(raw[k] * weights[k] for k in raw) / total
    out = {k: max(4.0, min(96.0, target + raw[k] - mean)) for k in raw}
    gap = target - sum(out[k] * weights[k] for k in out) / total
    return {k: round(max(3.0, min(97.0, v + gap)), 2) for k, v in out.items()}


def _final_by_uf(player: float, regions: dict[str, float], seed: int) -> dict[str, float]:
    """Parcela do jogador em cada UF: viés regional + ruído estável, recentrada para bater com o total nacional."""
    avg_region = sum(regions.values()) / len(regions) if regions else 50.0
    raw = {}
    for uf, (region, _, _) in UFS.items():
        regional = (regions.get(region, avg_region) - avg_region) * 0.6
        raw[uf] = regional + (_rnd(f"{seed}:{region}:r") - 0.5) * 14 + (_rnd(f"{seed}:{uf}:u") - 0.5) * 10
    return _recenter(raw, {uf: w for uf, (_, w, _) in UFS.items()}, player)


def _steps(units: dict[str, float], delays: dict[str, int], final: dict[str, float], seed: int) -> list[dict[str, Any]]:
    total_w = sum(units.values())
    steps = []
    for label, frac in STEPS:
        out: dict[str, Any] = {}
        for key, weight in units.items():
            speed = 0.75 + 0.5 * _rnd(f"{seed}:{key}:s")
            counted = 0.0 if frac == 0 else max(0.0, min(1.0, (frac * speed - 0.06 * delays.get(key, 0)) / 0.97))
            if frac >= 1.0:
                counted = 1.0
            early = (_rnd(f"{seed}:{key}:e") - 0.5) * 16 * (1 - counted)  # urnas que chegam primeiro destoam do final
            share = final[key] if counted >= 1 else max(1.0, min(99.0, final[key] + early))
            out[key] = {"counted": round(counted * 100, 1), "player": round(share, 2) if counted > 0 else None}
        counted_total = sum(units[k] * out[k]["counted"] for k in units)
        player_votes = sum(units[k] * out[k]["counted"] * (out[k]["player"] or 0) for k in units)
        steps.append({"time": label, "counted": round(counted_total / total_w, 1), "national_player": round(player_votes / counted_total, 2) if counted_total else None,
                      "units": out, "ufs": out, "closed": sorted(k for k, v in out.items() if v["counted"] >= 100)})
    return steps


def _turning_point(steps: list[dict[str, Any]]) -> str | None:
    lead = [None if s["national_player"] is None else s["national_player"] >= 50 for s in steps]
    turn = next((i for i in range(1, len(lead)) if lead[i] is not None and lead[i - 1] is not None and lead[i] != lead[i - 1]), None)
    return steps[turn]["time"] if turn is not None else None


def _dhondt(votes: dict[str, float], seats: int) -> dict[str, int]:
    got = {k: 0 for k in votes}
    for _ in range(seats):
        winner = max(votes, key=lambda k: votes[k] / (got[k] + 1))
        got[winner] += 1
    return got


def _lista(state: dict[str, Any], career: dict[str, Any]) -> dict[str, Any]:
    result = career.get("electoral_result") or {}
    seed = int(state.get("campaign_seed", 1))
    magnitude = int(result.get("district_magnitude") or ASSEMBLY_FALLBACK.get(str(career.get("office")), 13))
    mine = float(result.get("party_vote_share") or 10.0)
    my_seats = int(result.get("party_seats") or 0)
    rng = random.Random(f"{seed}:lista")
    weights = [rng.gammavariate(1.7, 1.0) for _ in OTHER_PARTIES]
    shares = {"Sua legenda": mine, **{name: (100.0 - mine) * w / (sum(weights) or 1.0) for name, w in zip(OTHER_PARTIES, weights)}}
    others = _dhondt({k: v for k, v in shares.items() if k != "Sua legenda"}, max(0, magnitude - my_seats))
    final_seats = {"Sua legenda": my_seats, **others}
    valid = result.get("valid_votes")
    steps = []
    for label, frac in STEPS:
        c = frac
        partial = {k: max(0.2, v + (_rnd(f"{seed}:{k}:p") - 0.5) * 10 * (1 - c)) for k, v in shares.items()} if c > 0 else {k: 0.0 for k in shares}
        total = sum(partial.values()) or 1.0
        partial = {k: round(100 * v / total, 2) for k, v in partial.items()}
        seats = final_seats if c >= 1 else (_dhondt(partial, magnitude) if c > 0 else {k: 0 for k in shares})
        steps.append({"time": label, "counted": round(c * 100, 1), "parties": [{"name": k, "share": partial[k], "seats": seats[k], "mine": k == "Sua legenda"} for k in sorted(shares, key=lambda n: -partial[n])],
                      "quotient_votes": int(valid * c / magnitude) if valid else None})
    first = steps[-1]
    entries = result.get("list") or []
    return {"available": True, "kind": "lista", "office": career.get("office"), "result": career.get("result"), "magnitude": magnitude,
            "steps": steps, "elected": bool(result.get("elected")), "player_rank": result.get("candidate_list_rank"), "player_votes": result.get("candidate_votes"),
            "player_share": result.get("candidate_vote_share"), "party_seats": my_seats, "valid_votes": valid,
            "quotient": int(valid / magnitude) if valid else None, "list": entries, "winner": first["parties"][0]["name"],
            "note": "Cadeiras por quociente (D'Hondt) entre legendas fictícias; dentro da legenda elegem-se os mais votados. Votos e nomes são estimativas do jogo."}


def _zonas(state: dict[str, Any], career: dict[str, Any]) -> dict[str, Any]:
    seed = int(state.get("campaign_seed", 1))
    zones = CITY_ZONES if career.get("office") == "prefeito" else STATE_ZONES
    weights = {name: w for name, w in zones}
    player = max(5.0, min(95.0, float(career.get("vote_share") or 0.0) * 100 / max(1.0, float(career.get("vote_share") or 0.0) + float(career.get("opponent_share") or 0.0))))
    raw = {name: (_rnd(f"{seed}:{name}:z") - 0.5) * 22 for name in weights}
    final = _recenter(raw, weights, player)
    steps = _steps(weights, {}, final, seed)
    rival = next((c for c in (career.get("candidate_results") or []) if not c.get("is_player")), None)
    return {"available": True, "kind": "zonas", "office": career.get("office"), "result": career.get("result"), "steps": steps, "weights": weights,
            "player_final": round(player, 2), "opponent_final": round(100 - player, 2), "turning_point": _turning_point(steps),
            "rival": {"name": rival.get("name"), "party": rival.get("party")} if rival else None,
            "note": "Boletins simulados por região. O resultado final é o que o motor decidiu; os pesos das regiões são estimativas do jogo."}


def build(state: dict[str, Any]) -> dict[str, Any]:
    career = state.get("career") or {}
    seed = int(state.get("campaign_seed", 1))
    if career.get("mode"):
        if not career.get("result"):
            return {"available": False, "reason": "A apuração acontece no dia da eleição. Quando houver resultado, ele aparece aqui, urna a urna."}
        office = str(career.get("office"))
        if office in PROPORTIONAL:
            return _lista(state, career)
        if office in ZONED:
            return _zonas(state, career)
        player = max(5.0, min(95.0, float(career.get("vote_share") or 0.0)))
        date_ = str(career.get("election_date") or state.get("date"))
        result = career["result"]
    else:
        election = state.get("election") or {}
        if not election.get("result"):
            return {"available": False, "reason": "A apuração acontece no dia da eleição. Quando houver resultado, ele aparece aqui, urna a urna."}
        player = max(5.0, min(95.0, 50.0 + float(election.get("margin", 0.0)) / 2))
        date_ = str(election.get("date") or state.get("date"))
        result = election["result"]
    final = _final_by_uf(player, _regions(state), seed)
    steps = _steps({uf: w for uf, (_, w, _) in UFS.items()}, {uf: d for uf, (_, _, d) in UFS.items()}, final, seed)
    return {"available": True, "kind": "mapa", "date": date_, "result": result, "player_final": round(player, 2), "opponent_final": round(100 - player, 2),
            "steps": steps, "turning_point": _turning_point(steps), "weights": {uf: w for uf, (_, w, _) in UFS.items()}, "regions": {uf: r for uf, (r, _, _) in UFS.items()},
            "note": "Boletins simulados. Pesos de eleitorado por estado são estimativas do jogo; o resultado final é o que o motor decidiu."}
