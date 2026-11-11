"""Rotas do catálogo de competências por cargo."""
from __future__ import annotations

from datetime import date
from typing import Any, Callable

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .engine import ledger, powers
from .engine.career import is_career_governing


class PowerBody(BaseModel):
    action: str = Field(min_length=3, max_length=60)
    option: str | None = Field(default=None, max_length=80)


def build_router(get_state: Callable[[], dict[str, Any]], save: Callable[[dict[str, Any]], None],
                 public: Callable[[dict[str, Any]], dict[str, Any]]) -> APIRouter:
    router = APIRouter()

    def _office(state: dict[str, Any]) -> tuple[str, bool]:
        career = state.get("career") or {}
        if career.get("mode"):
            return str(career.get("office", "vereador")), bool(is_career_governing(career, date.fromisoformat(state["date"])))
        if state.get("mode") == "party_path" and (state.get("party_path") or {}).get("active"):
            return str(state["party_path"].get("stage", "militante")), False
        return "presidente", state.get("office_status", "incumbent") == "incumbent"

    @router.get("/api/powers")
    def list_powers() -> dict[str, Any]:
        state = get_state()
        office, governing = _office(state)
        return powers.catalog_for(state, office, governing)

    @router.get("/api/powers/roles")
    def roles() -> dict[str, Any]:
        from .engine.powers_catalog import ROLES
        return {"roles": ROLES}

    @router.post("/api/powers/execute")
    def execute(body: PowerBody) -> dict[str, Any]:
        state = get_state()
        office, governing = _office(state)
        if not governing:
            raise HTTPException(status_code=403, detail="Estas ações exigem estar empossado no cargo.")
        try:
            if office != "presidente":
                from .engine import office_powers
                result = office_powers.execute(state, body.action)
                result.setdefault("status", "applied")
            else:
                result = powers.execute(state, body.action, body.option)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except PermissionError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        save(state)
        return {**result, "state": public(state), "catalog": powers.catalog_for(state, office, governing)}

    @router.get("/api/ledger")
    def ledger_overview() -> dict[str, Any]:
        return {"entries": ledger.overview(get_state())}

    @router.post("/api/ledger/{entry_id}/narrate")
    async def narrate_entry(entry_id: str) -> dict[str, Any]:
        from .ai.narrator import narrate
        state = get_state()
        entry = next((e for e in ledger.overview(state, 200) if e["id"] == entry_id), None)
        if entry is None:
            raise HTTPException(status_code=404, detail="Registro não encontrado.")
        facts = {k: entry.get(k) for k in ("title", "status", "forecast", "result", "cost", "reason", "date")}
        out = await narrate(facts)
        entry["narrative"] = out
        save(state)
        return out

    return router
