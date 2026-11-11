"""Rotas de território (cidade, estado, região), registro de indicadores e projetos de transporte e urbanismo."""
from __future__ import annotations

from datetime import date
from typing import Any, Callable

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from .engine import indicator_engine, territory
from .engine.career import is_career_governing
from .engine.indicator_registry import DOMAINS, REGISTRY, explain, for_office


class StartBody(BaseModel):
    project_id: str = Field(min_length=3, max_length=40)
    uf: str = Field(min_length=2, max_length=2)
    city: str | None = Field(default=None, pattern=r"^\d{7}$")


def build_router(get_state: Callable[[], dict[str, Any]], save: Callable[[dict[str, Any]], None],
                 public: Callable[[dict[str, Any]], dict[str, Any]]) -> APIRouter:
    router = APIRouter()

    def _office(state: dict[str, Any]) -> tuple[str, bool]:
        career = state.get("career") or {}
        if career.get("mode"):
            return str(career.get("office", "vereador")), bool(is_career_governing(career, date.fromisoformat(state["date"])))
        if state.get("mode") == "party_path":
            return "militante", False
        return "presidente", state.get("office_status", "incumbent") == "incumbent"

    @router.get("/api/indicators/registry")
    def registry(domain: str | None = None, office: str | None = None) -> dict[str, Any]:
        items = [explain(k) for k in REGISTRY if (not domain or REGISTRY[k]["domain"] == domain)]
        if office:
            items = [i for i in items if office in i["levers"]]
        return {"domains": DOMAINS, "count": len(items), "indicators": items}

    @router.get("/api/indicators/office/{office}")
    def by_office(office: str) -> dict[str, Any]:
        return {"office": office, "indicators": for_office(office)}

    @router.get("/api/territory")
    def overview() -> dict[str, Any]:
        state = get_state()
        return {**territory.overview(state), "nation": indicator_engine.snapshot(state)}

    @router.get("/api/indicators/nation/history")
    def nation_history(keys: str = Query(default="", max_length=300)) -> dict[str, Any]:
        wanted = [k for k in keys.split(",") if k in REGISTRY]
        nation = indicator_engine.ensure(get_state())
        return {"series": [{"month": h["month"], **{k: h["values"].get(k) for k in wanted}} for h in nation["history"]]}

    @router.get("/api/territory/search")
    def search(q: str = Query(min_length=2, max_length=60), uf: str | None = Query(default=None, max_length=2)) -> dict[str, Any]:
        return {"items": territory.search(q, uf)}

    @router.get("/api/territory/city/{ibge}")
    def city(ibge: str) -> dict[str, Any]:
        try:
            return territory.city_indicators(get_state(), ibge)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.get("/api/territory/projects")
    def projects() -> dict[str, Any]:
        state = get_state()
        office, governing = _office(state)
        return {"office": office, "can_start": governing, "catalog": territory.catalog(state, office), "projects": territory.ensure(state)["projects"]}

    @router.post("/api/territory/projects/start")
    def start(body: StartBody) -> dict[str, Any]:
        state = get_state()
        office, governing = _office(state)
        if not governing:
            raise HTTPException(status_code=403, detail="Obras exigem estar no exercício de um cargo executivo.")
        try:
            item = territory.start(state, body.project_id, office, body.uf.upper(), body.city)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except PermissionError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        save(state)
        return {"project": item, "state": public(state)}

    return router
