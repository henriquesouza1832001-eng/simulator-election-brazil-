"""Mapa de votação por município (cartograma em mosaico).

O resultado de cada estado vem do motor (tally); aqui ele é distribuído entre os municípios do estado, com a soma
ponderada pelo eleitorado batendo com o total estadual. A distribuição usa ruído estável da semente da partida e um
efeito leve da renda do município (o sinal muda de partida para partida). É simulação: o perfil do município não
decide o voto de verdade nesta versão, e os números não representam nenhuma pesquisa ou eleição real.
"""
from __future__ import annotations

import math
from typing import Any

from . import geography, tally

NOISE_PP = 5.5
INCOME_PP = 3.0


def _normal(seed: str) -> float:
    """Aproximação de uma normal padrão por soma de quatro uniformes (determinística)."""
    return (sum(tally._rnd(f"{seed}:{k}") for k in range(4)) - 2.0) / math.sqrt(4 / 12)


def _state_share(state: dict[str, Any], uf: str) -> float | None:
    career = state.get("career") or {}
    seed = int(state.get("campaign_seed", 1))
    if career.get("mode"):
        if not career.get("result"):
            return None
        office = str(career.get("office"))
        if office == "presidente":
            player = max(5.0, min(95.0, float(career.get("vote_share") or 0.0)))
            return tally._final_by_uf(player, tally._regions(state), seed).get(uf)
        if office in ("governador", "senador") and str(career.get("state_code", "")).upper() == uf:
            mine, theirs = float(career.get("vote_share") or 0.0), float(career.get("opponent_share") or 0.0)
            return max(5.0, min(95.0, mine * 100 / max(1.0, mine + theirs)))
        return None
    election = state.get("election") or {}
    if not election.get("result"):
        return None
    player = max(5.0, min(95.0, 50.0 + float(election.get("margin", 0.0)) / 2))
    return tally._final_by_uf(player, tally._regions(state), seed).get(uf)


def available_ufs(state: dict[str, Any]) -> list[str]:
    career = state.get("career") or {}
    if career.get("mode") and career.get("office") in ("governador", "senador"):
        return [str(career.get("state_code", "")).upper()] if career.get("result") else []
    if career.get("mode") and career.get("office") != "presidente":
        return []
    return sorted(tally.UFS) if (career.get("result") or (state.get("election") or {}).get("result")) else []


def build(state: dict[str, Any], uf: str) -> dict[str, Any]:
    uf = (uf or "").upper()
    if uf not in tally.UFS:
        return {"available": False, "reason": "Escolha um estado."}
    base = _state_share(state, uf)
    if base is None:
        return {"available": False, "reason": "O mapa por município aparece depois do resultado da eleição para presidente, governador ou senador."}
    seed = int(state.get("campaign_seed", 1))
    rows = [m for m in geography._catalog()["municipalities"] if m["state_code"] == uf]
    if not rows:
        return {"available": False, "reason": "Sem dados de municípios para este estado."}
    incomes = [math.log(max(1.0, float((m.get("economic_profile") or {}).get("gdp_per_capita_brl") or 1.0))) for m in rows]
    mean = sum(incomes) / len(incomes)
    spread = math.sqrt(sum((x - mean) ** 2 for x in incomes) / len(incomes)) or 1.0
    lean = (tally._rnd(f"{seed}:{uf}:renda") - 0.5) * 2  # sinal e força do efeito da renda nesta partida
    raw, weights = {}, {}
    for m, income in zip(rows, incomes):
        code = m["ibge_code"]
        raw[code] = lean * INCOME_PP * (income - mean) / spread + NOISE_PP * _normal(f"{seed}:{code}:voto")
        weights[code] = float(m.get("electorate_count") or (m.get("population_estimate") or 1000) * 0.75)
    shares = tally._recenter(raw, weights, base)
    tiles = []
    for m in rows:
        share = shares[m["ibge_code"]]
        tiles.append({"id": m["ibge_code"], "name": m["name"], "population": m.get("population_estimate"), "electorate": int(weights[m["ibge_code"]]),
                      "share": round(share, 1), "winner": "player" if share >= 50 else "opponent"})
    tiles.sort(key=lambda t: -t["electorate"])
    won = [t for t in tiles if t["winner"] == "player"]
    total_electorate = sum(t["electorate"] for t in tiles)
    return {"available": True, "uf": uf, "state_share": round(base, 1), "tiles": tiles, "municipalities": len(tiles), "won": len(won),
            "won_electorate_pct": round(100 * sum(t["electorate"] for t in won) / total_electorate, 1) if total_electorate else 0.0,
            "note": "Cada quadrado é um município, com tamanho pelo eleitorado. A soma bate com o total do estado. Distribuição simulada pelo jogo."}
