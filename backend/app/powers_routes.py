"""Rotas do catálogo de competências por cargo."""
from __future__ import annotations

from datetime import date
from typing import Any, Callable

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from .engine import ledger, powers
from .engine.career import is_career_governing


class InterpretBody(BaseModel):
    text: str = Field(min_length=4, max_length=400)


class AnswerBody(BaseModel):
    text: str = Field(min_length=4, max_length=6000)


class StartInterviewBody(BaseModel):
    kind: str = Field(min_length=3, max_length=20)


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

    @router.post("/api/powers/interpret")
    async def interpret_text(body: InterpretBody) -> dict[str, Any]:
        """Entende uma frase livre e a liga a ações do catálogo do cargo atual. O Gemini só entra se houver ambiguidade."""
        from .ai.mapper_ai import refine
        from .engine import action_mapper
        from .learning_actions import similar_choices
        state = get_state()
        office, governing = _office(state)
        catalog = powers.catalog_for(state, office, governing)
        confirmed = similar_choices(body.text)
        matches = action_mapper.rank(body.text, catalog.get("actions", []), confirmed)
        questions = action_mapper.questions_for(body.text, matches)
        source = "local"
        if action_mapper.needs_ai(matches):
            candidates = matches or [{"id": a["id"], "title": a["title"]} for a in catalog.get("actions", [])[:40]]
            ai = await refine(body.text, candidates, confirmed)
            if ai["source"] == "gemini":
                source = "gemini"
                if ai["choice"]:
                    matches.sort(key=lambda m: m["id"] != ai["choice"])
                questions = (ai["questions"] or questions)[:2]
        learned = [{"text": c["text"], "action_id": c["action_id"]} for c in confirmed[:3]]
        if learned and not questions and matches and matches[0]["id"] != learned[0]["action_id"]:
            questions.append("Da última vez, uma frase parecida virou outra ação. Confirme qual você quer agora.")
        return {"office": office, "matches": matches, "questions": questions, "source": source, "learned": learned,
                "note": "O motor decide competência, aprovação e efeitos. A IA, quando usada, só escolhe entre as ações listadas e sugere perguntas."}

    @router.post("/api/powers/confirm")
    def confirm_choice(body: InterpretBody, action: str = Query(min_length=3, max_length=60), option: str | None = Query(default=None, max_length=80)) -> dict[str, Any]:
        from .learning_actions import record_choice
        record_choice(body.text, action, option)
        return {"saved": True}

    @router.get("/api/interviews")
    def interviews_overview() -> dict[str, Any]:
        from .engine import interviews
        return interviews.overview(get_state())

    @router.post("/api/interviews/start")
    def interviews_start(body: StartInterviewBody) -> dict[str, Any]:
        from .engine import interviews
        state = get_state()
        try:
            out = interviews.start(state, body.kind)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except PermissionError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        save(state)
        return out

    @router.post("/api/interviews/answer")
    def interviews_answer(body: AnswerBody) -> dict[str, Any]:
        from .engine import interviews
        state = get_state()
        try:
            out = interviews.answer(state, body.text)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except PermissionError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        save(state)
        return {**out, "state": public(state)}

    @router.get("/api/consequences")
    def consequences_overview() -> dict[str, Any]:
        from .engine import consequences
        return consequences.overview(get_state())

    @router.post("/api/consequences/{crisis_id}/respond")
    def consequences_respond(crisis_id: str, option: str = Query(min_length=2, max_length=30)) -> dict[str, Any]:
        from .engine import consequences
        state = get_state()
        try:
            result = consequences.respond(state, crisis_id, option)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        save(state)
        return {**result, "overview": consequences.overview(state), "state": public(state)}

    @router.get("/api/regulators")
    def regulators_overview() -> dict[str, Any]:
        from .engine import regulators
        return regulators.overview(get_state())

    @router.get("/api/fiscal/local")
    def local_fiscal() -> dict[str, Any]:
        from .engine import subnational_fiscal
        status = subnational_fiscal.status(get_state())
        return {"available": status is not None, "fiscal": status}

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
