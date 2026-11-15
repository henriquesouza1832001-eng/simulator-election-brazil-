"""Apuração da eleição, urna a urna em boletins: o motor já decidiu o resultado; aqui ele só é "contado" aos poucos.

Dado o resultado nacional (parcela do jogador e do adversário), o motor distribui os votos pelos estados com viés
regional estável (semente da partida) e solta boletins ao longo da noite. Os estados fecham por fuso e tamanho, e o
início da contagem pode enganar (viés de urnas que chegam primeiro), de modo que a virada acontece quando há motivo.
Pesos de eleitorado por estado são estimativas do jogo (arredondadas), não dados oficiais.
"""
from __future__ import annotations

import hashlib
from typing import Any

# UF -> (macrorregião, peso aproximado do eleitorado em %, horário local em que a contagem começa a andar)
UFS: dict[str, tuple[str, float, int]] = {
    "AC": ("norte", 0.4, 0), "AL": ("nordeste", 1.5, 0), "AM": ("norte", 1.9, 1), "AP": ("norte", 0.4, 0), "BA": ("nordeste", 7.0, 0),
    "CE": ("nordeste", 4.3, 0), "DF": ("centro_oeste", 1.4, 0), "ES": ("sudeste", 2.0, 0), "GO": ("centro_oeste", 3.2, 0), "MA": ("nordeste", 3.3, 0),
    "MG": ("sudeste", 10.1, 0), "MS": ("centro_oeste", 1.4, 1), "MT": ("centro_oeste", 1.7, 1), "PA": ("norte", 3.9, 0), "PB": ("nordeste", 2.0, 0),
    "PE": ("nordeste", 4.5, 0), "PI": ("nordeste", 1.6, 0), "PR": ("sul", 5.5, 0), "RJ": ("sudeste", 8.3, 0), "RN": ("nordeste", 1.7, 0),
    "RO": ("norte", 0.9, 1), "RR": ("norte", 0.3, 1), "RS": ("sul", 5.4, 0), "SC": ("sul", 3.6, 0), "SE": ("nordeste", 1.1, 0),
    "SP": ("sudeste", 22.4, 0), "TO": ("norte", 0.9, 0),
}
STEPS = [("17:00", 0.0), ("18:00", 0.18), ("19:00", 0.45), ("20:00", 0.7), ("21:00", 0.88), ("22:00", 0.97), ("23:30", 1.0)]


def _rnd(seed: str) -> float:
    return int(hashlib.sha256(seed.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF


def _regions(state: dict[str, Any]) -> dict[str, float]:
    return {k: float(v) for k, v in ((state.get("campaign") or {}).get("regional_support") or {}).items()}


def _national(state: dict[str, Any]) -> dict[str, Any] | None:
    """Resultado do jogador no cargo majoritário nacional, ou None quando não há o que apurar aqui."""
    career = state.get("career") or {}
    if career.get("mode"):
        if career.get("office") != "presidente" or not career.get("result"):
            return {"kind": "resumo", "career": career} if career.get("result") else None
        share = float(career.get("vote_share") or 0.0)
        return {"kind": "mapa", "player": share, "date": str(career.get("election_date") or state.get("date")), "result": career.get("result"),
                "regions": _regions(state)}
    election = state.get("election") or {}
    if not election.get("result"):
        return None
    player = max(5.0, min(95.0, 50.0 + float(election.get("margin", 0.0)) / 2))
    return {"kind": "mapa", "player": player, "date": str(election.get("date") or state.get("date")), "result": election["result"],
            "regions": _regions(state)}


def _final_by_uf(national: dict[str, Any], seed: int) -> dict[str, float]:
    """Parcela do jogador em cada UF: viés regional + ruído estável, recentrada para bater com o total nacional."""
    regions = national["regions"]
    avg_region = sum(regions.values()) / len(regions) if regions else 50.0
    raw: dict[str, float] = {}
    for uf, (region, _, _) in UFS.items():
        regional = (regions.get(region, avg_region) - avg_region) * 0.6
        spread = (_rnd(f"{seed}:{region}:r") - 0.5) * 14          # cada região tem sua tendência
        local = (_rnd(f"{seed}:{uf}:u") - 0.5) * 10               # cada estado, um pouco da sua
        raw[uf] = regional + spread + local
    total_w = sum(w for _, w, _ in UFS.values())
    mean = sum(raw[uf] * UFS[uf][1] for uf in UFS) / total_w
    out = {uf: max(4.0, min(96.0, national["player"] + raw[uf] - mean)) for uf in UFS}
    # recentra de novo depois do corte nos extremos
    gap = national["player"] - sum(out[uf] * UFS[uf][1] for uf in UFS) / total_w
    return {uf: round(max(3.0, min(97.0, v + gap)), 2) for uf, v in out.items()}


def build(state: dict[str, Any]) -> dict[str, Any]:
    national = _national(state)
    if national is None:
        return {"available": False, "reason": "A apuração acontece no dia da eleição. Quando houver resultado, ele aparece aqui, urna a urna."}
    if national["kind"] == "resumo":
        career = national["career"]
        return {"available": True, "kind": "resumo", "office": career.get("office"), "result": career.get("result"), "vote_share": career.get("vote_share"),
                "opponent_share": career.get("opponent_share"), "electoral_result": career.get("electoral_result"),
                "note": "Neste cargo o resultado não se divide por estado: veja a posição na lista ou a disputa na cidade."}
    seed = int(state.get("campaign_seed", 1))
    final = _final_by_uf(national, seed)
    total_w = sum(w for _, w, _ in UFS.values())
    steps = []
    for label, frac in STEPS:
        ufs: dict[str, Any] = {}
        for uf, (region, weight, delay) in UFS.items():
            speed = 0.75 + 0.5 * _rnd(f"{seed}:{uf}:s")
            counted = 0.0 if frac == 0 else max(0.0, min(1.0, (frac * speed - 0.06 * delay) / 0.97))
            if frac >= 1.0:
                counted = 1.0
            # urnas que chegam primeiro tendem a destoar do final; o desvio some conforme a contagem avança
            early = (_rnd(f"{seed}:{uf}:e") - 0.5) * 16 * (1 - counted)
            share = final[uf] if counted >= 1 else max(1.0, min(99.0, final[uf] + early))
            ufs[uf] = {"counted": round(counted * 100, 1), "player": round(share, 2) if counted > 0 else None}
        votes_w = sum(weight * ufs[uf]["counted"] for uf, (_, weight, _) in UFS.items()) / total_w
        player_votes = sum(weight * ufs[uf]["counted"] * (ufs[uf]["player"] or 0) for uf, (_, weight, _) in UFS.items())
        counted_total = sum(weight * ufs[uf]["counted"] for uf, (_, weight, _) in UFS.items())
        national_now = round(player_votes / counted_total, 2) if counted_total else None
        steps.append({"time": label, "counted": round(votes_w, 1), "national_player": national_now,
                      "ufs": ufs, "closed": sorted(uf for uf, v in ufs.items() if v["counted"] >= 100)})
    # ponto de virada: primeiro boletim em que o líder muda em relação ao anterior (entre os que já têm contagem)
    lead = [None if s["national_player"] is None else s["national_player"] >= 50 for s in steps]
    turn = next((i for i in range(1, len(lead)) if lead[i] is not None and lead[i - 1] is not None and lead[i] != lead[i - 1]), None)
    return {"available": True, "kind": "mapa", "date": national["date"], "result": national["result"],
            "player_final": round(national["player"], 2), "opponent_final": round(100 - national["player"], 2),
            "steps": steps, "turning_point": steps[turn]["time"] if turn is not None else None,
            "weights": {uf: w for uf, (_, w, _) in UFS.items()}, "regions": {uf: r for uf, (r, _, _) in UFS.items()},
            "note": "Boletins simulados. Pesos de eleitorado por estado são estimativas do jogo; o resultado final é o que o motor decidiu."}
