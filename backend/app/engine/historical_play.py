"""Eleições passadas jogáveis: disputar uma eleição real (2014 a 2024) e comparar com o resultado oficial.

O jogador entra como candidato adicional na data real do pleito. Os adversários usam o partido e a força eleitoral
reais dos mais votados (votos nominais do TSE); o comportamento deles é simulado, e seus nomes no jogo são genéricos
("Candidato(a) do PL"). Depois da apuração, o jogo mostra o resultado oficial ao lado do simulado, com nomes e votos
reais (informação pública). Exige votos importados (`python -m app.data.tse_votes`).
"""
from __future__ import annotations

from datetime import date
from typing import Any

from . import election_rules as er
from . import elector
from .legislature import PARTY_PROFILE

YEARS = {"municipal": (2016, 2020, 2024), "geral": (2014, 2018, 2022)}
SPECTRUM_LABEL = {"extrema-esquerda": "Esquerda", "esquerda": "Esquerda", "centro-esquerda": "Centro-esquerda", "centro": "Centro", "centro-direita": "Centro-direita", "direita": "Direita"}
ISSUES = ["economia", "saude", "educacao", "seguranca", "mobilidade", "integridade"]


def eligible_years(office: str) -> list[int]:
    kind = "municipal" if office in {"vereador", "prefeito"} else "geral"
    return [y for y in YEARS[kind] if elector.votes_available(y)]


def _scope(year: int, office: str, uf: str, municipality_id: str | None) -> dict[str, Any]:
    return er.validate_selection(year, office, None if office == "presidente" else uf, municipality_id if office in {"vereador", "prefeito"} else None)


def real_results(year: int, office: str, uf: str, municipality_id: str | None, limit: int = 8) -> dict[str, Any]:
    return elector.official_results(year, office, _scope(year, office, uf, municipality_id), limit)


def real_opponents(year: int, office: str, uf: str, municipality_id: str | None) -> list[dict[str, Any]]:
    res = real_results(year, office, uf, municipality_id, 6)
    if not res["available"]:
        return []
    first = res["rounds"][0]["candidates"][:3]
    mean = sum(c["share_pct"] for c in first) / max(len(first), 1) or 1.0
    out = []
    for i, c in enumerate(first):
        label = SPECTRUM_LABEL.get(PARTY_PROFILE.get(_party_key(c["party"]), (0, "centro", 0))[1], "Centro")
        out.append({"id": f"opponent-{i + 1}", "name": f"Candidato(a) do {c['party']}", "party": c["party"], "ideology": label, "issue_focus": ISSUES[(i * 2 + year) % len(ISSUES)],
                    "support_weight": round(max(0.6, min(1.6, c["share_pct"] / mean)), 2), "historical_votes": c["votes"], "simulated": True})
    return out


def _party_key(party: str) -> str:
    return {"UNIAO": "UNIÃO", "MISSAO": "MISSÃO", "PC do B": "PCdoB", "PCDOB": "PCdoB"}.get(party.upper().replace("Ã", "A"), party)


def decorate(state: dict[str, Any], year: int, uf: str, municipality_id: str | None) -> None:
    career = state["career"]
    opponents = real_opponents(year, career["office"], uf, municipality_id)
    if len(opponents) == 3:
        career["opponents"] = opponents
    career["historical"] = {"year": year, "uf": uf, "municipality_id": municipality_id}


def compare(career: dict[str, Any]) -> dict[str, Any] | None:
    """Resultado oficial ao lado do simulado; só depois da apuração."""
    h = career.get("historical")
    if not h or career.get("result") is None:
        return None
    try:
        res = real_results(h["year"], career["office"], h["uf"], h.get("municipality_id"), 8)
    except ValueError:
        return None
    if not res["available"]:
        return None
    final = res["rounds"][-1]
    er_ = career.get("electoral_result") or {}
    mine = {"result": career.get("result"), "vote_share_pct": career.get("vote_share")}
    if career["office"] == "vereador":
        elected = [c for c in res["rounds"][0]["candidates"] if str(c["result"]).upper().startswith("ELEITO")]
        last = min(elected, key=lambda c: c["votes"]) if elected else None
        mine["estimated_votes"] = er_.get("candidate_votes")
        return {"year": h["year"], "kind": "proporcional", "mine": mine, "real_top": res["rounds"][0]["candidates"][:5], "real_last_elected": last,
                "nominal_votes": res["rounds"][0]["nominal_votes"],
                "text": ("Seu desempenho simulado teve " + (f"cerca de {int(er_['candidate_votes']):,} votos".replace(",", ".") if er_.get("candidate_votes") else "votação não estimada")
                         + (f"; o último eleito de verdade teve {last['votes']:,} votos.".replace(",", ".") if last else "."))}
    winner = final["candidates"][0]
    return {"year": h["year"], "kind": "majoritaria", "mine": mine, "real_top": final["candidates"][:5], "real_winner": winner, "nominal_votes": final["nominal_votes"],
            "text": f"Na eleição de verdade, {winner['name']} ({winner['party']}) venceu com {winner['share_pct']}% dos votos nominais. Seu desempenho simulado: "
                    f"{career.get('vote_share')}% ({'vitória' if career.get('result') == 'won' else 'derrota'})."}
