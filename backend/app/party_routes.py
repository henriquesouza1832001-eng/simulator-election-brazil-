"""Rotas da trajetória partidária (militante, partidário, pré-candidato) e da biblioteca de acontecimentos."""
from __future__ import annotations

from typing import Any, Callable
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .db import reset_campaign_id, save_state, set_campaign_id
from .engine import party_path
from .engine.event_library import get_library
from .engine.geography import get_municipality
from .engine.state import new_game

SPECTRUMS = {"esquerda", "centro_esquerda", "centro", "centro_direita", "direita"}


class StartBody(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    state_code: str = Field(min_length=2, max_length=2)
    municipality_id: str = Field(pattern=r"^\d{7}$")
    spectrum: str = "centro"
    cause: str = Field(min_length=3, max_length=20)
    campaign_name: str = Field(default="", max_length=80)


class ActBody(BaseModel):
    action: str = Field(min_length=3, max_length=40)


class AffiliateBody(BaseModel):
    party: str = Field(min_length=2, max_length=80)
    ideology: str = Field(min_length=2, max_length=40)


def build_router(get_state: Callable[[], dict[str, Any]], public: Callable[[dict[str, Any]], dict[str, Any]]) -> APIRouter:
    router = APIRouter()

    def run(fn):
        state = get_state()
        try:
            result = fn(state)
        except ValueError as problem:
            raise HTTPException(status_code=409, detail=str(problem))
        save_state(state)
        return result

    @router.post("/api/party-path/start")
    def start(body: StartBody) -> dict[str, Any]:
        city = get_municipality(body.municipality_id)
        if not city:
            raise HTTPException(status_code=422, detail="Município não encontrado no catálogo oficial do IBGE.")
        if city["state_code"] != body.state_code.upper():
            raise HTTPException(status_code=422, detail="O município não pertence à UF informada.")
        if body.spectrum not in SPECTRUMS:
            raise HTTPException(status_code=422, detail="Escolha uma posição política válida.")
        token = set_campaign_id(uuid4().hex)
        try:
            state = new_game()
            state.pop("setup_pending", None)
            state["player_character"] = {"name": body.name.strip(), "political_spectrum": body.spectrum, "birthplace": None, "traits": [], "customs": []}
            state["campaign_name"] = body.campaign_name.strip() or f"Trajetória de {body.name.strip()}"
            try:
                party_path.init_state(state, name=body.name.strip(), state_code=city["state_code"], municipality_id=city["ibge_code"],
                                      municipality=city["name"], spectrum=body.spectrum, cause=body.cause)
            except ValueError as problem:
                raise HTTPException(status_code=422, detail=str(problem))
            save_state(state)
            return public(state)
        finally:
            reset_campaign_id(token)

    @router.get("/api/party-path")
    def overview() -> dict[str, Any]:
        return party_path.overview(get_state())

    @router.post("/api/party-path/act")
    def act(body: ActBody) -> dict[str, Any]:
        return run(lambda s: party_path.perform(s, body.action))

    @router.post("/api/party-path/affiliate")
    def affiliate(body: AffiliateBody) -> dict[str, Any]:
        return run(lambda s: party_path.request_affiliation(s, body.party, body.ideology))

    @router.post("/api/party-path/run-post")
    def run_post() -> dict[str, Any]:
        return run(party_path.run_for_party_post)

    @router.post("/api/party-path/launch")
    def launch() -> dict[str, Any]:
        def go(s):
            result = party_path.launch_candidacy(s)
            return {**result, "state": public(s)}
        return run(go)

    @router.get("/api/story/library")
    def library_stats() -> dict[str, Any]:
        return get_library().stats()

    return router
