"""Rotas de cenários eleitorais (calendário e regras) e do Modo Eleitor."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from .engine import election_rules as er
from .engine import elector


class Selection(BaseModel):
    year: int
    office: str = Field(min_length=3, max_length=30)
    uf: str | None = Field(default=None, max_length=2)
    municipality_id: str | None = Field(default=None, max_length=7)


class VoteBody(Selection):
    choice: str = Field(min_length=1, max_length=40)


def _scope(sel: Selection | tuple) -> dict[str, Any]:
    try:
        return er.validate_selection(sel.year, sel.office, sel.uf, sel.municipality_id)
    except ValueError as problem:
        raise HTTPException(status_code=422, detail=str(problem))


def build_router() -> APIRouter:
    router = APIRouter()

    @router.get("/api/scenarios")
    def scenarios() -> dict[str, Any]:
        items = []
        for scenario in er.scenarios():
            items.append({**scenario, "data": elector.availability(scenario["year"])})
        return {"scenarios": items, "modes": [
            {"key": "eleitor", "label": "Modo Eleitor", "text": "Consulte candidatos oficiais de um pleito e dê um voto simulado."},
            {"key": "carreira", "label": "Campanha e carreira", "text": "Jogue como candidato: campanha, eleição, posse ou derrota e continuação."},
            {"key": "posse", "label": "Posse direta na Presidência", "text": "Comece governando, sem etapa de campanha."}],
            "notice": "O jogo é uma sátira/simulação e não é um serviço eleitoral."}

    @router.get("/api/scenarios/{year}")
    def scenario(year: int) -> dict[str, Any]:
        try:
            rules = er.ruleset_for(year)
        except ValueError as problem:
            raise HTTPException(status_code=404, detail=str(problem))
        return {"rules": rules, "data": elector.availability(year), "sources": er.SOURCES}

    @router.post("/api/scenarios/validate")
    def validate(body: Selection) -> dict[str, Any]:
        return {"ok": True, "scope": _scope(body), "year": body.year, "office": body.office}

    @router.get("/api/elector/candidates")
    def candidates(year: int, office: str, uf: str | None = None, municipality_id: str | None = None,
                   q: str = Query("", max_length=60), page: int = Query(1, ge=1), page_size: int = Query(30, ge=1, le=100)) -> dict[str, Any]:
        scope = _scope(Selection(year=year, office=office, uf=uf, municipality_id=municipality_id))
        data = elector.list_candidates(year, office, scope, q, page, page_size)
        data.update(notice=elector.SIMULATED_VOTE_NOTICE, scope=scope)
        return data

    @router.get("/api/elector/results")
    def results(year: int, office: str, uf: str | None = None, municipality_id: str | None = None, limit: int = Query(12, ge=1, le=50)) -> dict[str, Any]:
        scope = _scope(Selection(year=year, office=office, uf=uf, municipality_id=municipality_id))
        data = elector.official_results(year, office, scope, limit)
        data.update(scope=scope)
        return data

    @router.post("/api/elector/vote")
    def vote(body: VoteBody) -> dict[str, Any]:
        scope = _scope(body)
        try:
            return elector.cast_vote(body.year, body.office, scope, body.choice)
        except ValueError as problem:
            raise HTTPException(status_code=404, detail=str(problem))

    @router.get("/api/elector/votes")
    def votes() -> dict[str, Any]:
        return {"votes": elector.my_votes(), "notice": elector.SIMULATED_VOTE_NOTICE}

    return router
