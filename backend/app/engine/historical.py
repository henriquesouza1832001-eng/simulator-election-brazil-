"""Referência histórica real para a carreira: o que foi preciso para vencer a eleição anterior no mesmo território.

Usa os votos nominais do TSE (tabela `tse_votes`, importada com `python -m app.data.tse_votes`). Sem dados importados,
devolve None e o jogo segue sem a referência. Não altera a simulação: serve de régua para o jogador.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Any

from . import election_rules as er
from . import elector

MUNICIPAL_YEARS = (2024, 2020, 2016)


@lru_cache(maxsize=256)
def _benchmark(office: str, uf: str, municipality_id: str, municipality: str) -> dict[str, Any] | None:
    for year in MUNICIPAL_YEARS:
        if not elector.votes_available(year):
            continue
        scope = {"scope": "municipio", "uf": uf, "municipality_id": municipality_id, "municipality": municipality}
        res = elector.official_results(year, office, scope, 60)
        if not res["available"]:
            continue
        first = res["rounds"][0]
        elected = [c for c in first["candidates"] if str(c["result"]).upper().startswith("ELEITO")]
        if office == "vereador":
            if not elected:
                continue
            last = min(elected, key=lambda c: c["votes"])
            return {"year": year, "office": office, "seats": len(elected), "nominal_votes": first["nominal_votes"], "candidates": first["candidates_count"],
                    "last_elected": {"name": last["name"], "party": last["party"], "votes": last["votes"], "share_pct": last["share_pct"]},
                    "top": {"name": first["candidates"][0]["name"], "party": first["candidates"][0]["party"], "votes": first["candidates"][0]["votes"]}}
        final = res["rounds"][-1]
        winner = final["candidates"][0]
        runner = final["candidates"][1] if len(final["candidates"]) > 1 else None
        return {"year": year, "office": office, "rounds": len(res["rounds"]), "nominal_votes": final["nominal_votes"],
                "winner": {"name": winner["name"], "party": winner["party"], "votes": winner["votes"], "share_pct": winner["share_pct"]},
                "runner_up": runner and {"name": runner["name"], "party": runner["party"], "votes": runner["votes"], "share_pct": runner["share_pct"]},
                "candidates": first["candidates_count"]}
    return None


def reference_election(career: dict[str, Any]) -> dict[str, Any] | None:
    office = career.get("office")
    if office not in {"vereador", "prefeito"} or not career.get("municipality_id") or not career.get("municipality") or not career.get("state_code"):
        return None
    try:
        bench = _benchmark(office, career["state_code"], str(career["municipality_id"]), career["municipality"])
    except Exception:  # base ainda sem as tabelas do TSE
        return None
    if not bench:
        return None
    if office == "vereador":
        text = (f"Em {bench['year']}, {career['municipality']} elegeu {bench['seats']} vereadores entre {bench['candidates']} candidaturas. "
                f"O último eleito ({bench['last_elected']['name']}, {bench['last_elected']['party']}) teve {bench['last_elected']['votes']:,} votos "
                f"({bench['last_elected']['share_pct']}% dos votos nominais).").replace(",", ".")
    else:
        w, r = bench["winner"], bench.get("runner_up")
        text = (f"Em {bench['year']}, {w['name']} ({w['party']}) venceu em {career['municipality']} com {w['votes']:,} votos ({w['share_pct']}%)"
                + (f"; em segundo, {r['name']} ({r['party']}) teve {r['votes']:,} ({r['share_pct']}%)." if r else ".")).replace(",", ".")
    return {**bench, "text": text, "source": "TSE, votos nominais (dados abertos). Referência histórica; a simulação do jogo não usa estes números para decidir o resultado."}
