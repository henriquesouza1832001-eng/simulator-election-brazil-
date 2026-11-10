"""Rotas do meta-jogo: Congresso, ranking, coleção e diário."""
from __future__ import annotations

import json
from typing import Any, Callable

from fastapi import APIRouter, HTTPException, Query

from .db import connect, current_campaign_id, current_player_id
from pydantic import BaseModel, Field

from .engine import campaign_debate, campaign_week, legislature, meta, story


class StoryChoice(BaseModel):
    choice: str = Field(min_length=2, max_length=40)


class DebateChoice(BaseModel):
    choice: str = Field(min_length=3, max_length=20)
    issue: str = Field(default="", max_length=40)
    message: str = Field(default="", max_length=1200)


class CommitmentResolve(BaseModel):
    fulfilled: bool


class WeekAction(BaseModel):
    action: str = Field(min_length=2, max_length=40)
    region: str | None = Field(default=None, max_length=40)
    jet: bool = False


QUADROS = {"geral", "semana", "aprovacao", "economia", "campanhas", "colecao", "dinastias"}


def build_router(get_state: Callable[[], dict[str, Any]], save: Callable[[dict[str, Any]], None]) -> APIRouter:
    router = APIRouter()

    def unlocked() -> set[str]:
        with connect() as db:
            rows = db.execute("SELECT stamp_id FROM stamps_unlocked WHERE player_id = ?", (current_player_id(),)).fetchall()
        return {r["stamp_id"] for r in rows}

    def sync_stamps(state: dict[str, Any]) -> list[str]:
        have = unlocked()
        new = [s for s in meta.evaluate_stamps(state) if s not in have]
        if new:
            with connect() as db:
                for sid in new:
                    db.execute("INSERT OR IGNORE INTO stamps_unlocked (player_id, stamp_id, campaign_id) VALUES (?, ?, ?)",
                               (current_player_id(), sid, current_campaign_id()))
        return new

    @router.get("/api/legislature")
    def legislature_overview() -> dict[str, Any]:
        return legislature.overview(get_state())

    @router.get("/api/score")
    def current_score() -> dict[str, Any]:
        state = get_state()
        return {**meta.score_mandate(state), "outcome": meta.mandate_outcome(state)}

    @router.get("/api/ranking")
    def ranking(quadro: str = Query("geral"), nota: str = Query("todas")) -> dict[str, Any]:
        if quadro not in QUADROS:
            raise HTTPException(status_code=422, detail="Quadro desconhecido.")
        with connect() as db:
            rows = db.execute("SELECT entry_json FROM hall_entries ORDER BY points DESC LIMIT 200").fetchall()
        entries = [json.loads(r["entry_json"]) for r in rows] + [dict(e) for e in meta.SEED_HALL]
        entries = [e for e in entries if e.get("ranqueavel", True)]
        if nota != "todas":
            entries = [e for e in entries if e.get("nota") == nota.upper()]
        if quadro == "aprovacao":
            entries.sort(key=lambda e: -float(e.get("aprovacao", 0)))
        elif quadro == "economia":
            entries.sort(key=lambda e: -float(e.get("partes", {}).get("pais", 0) if e.get("partes") else e.get("pib") or 0))
        elif quadro == "campanhas":
            entries = [e for e in entries if e.get("desfecho") == "reeleito"]
            entries.sort(key=lambda e: -e["pontos"])
        else:
            entries.sort(key=lambda e: -e["pontos"])
        lines = [{**e, "posicao": i} for i, e in enumerate(entries[:50], start=1)]
        return {"quadro": quadro, "linhas": lines,
                "aviso": "Entradas marcadas como simuladas são exemplos fictícios; o placar mostra só o presidente da ficção, nunca quem joga.",
                "regras": ["Dificuldade Tranquilo não conta para o ranking.", "Realismo Puro vale 13% a mais.",
                           "Um mandato por partida e por mandato numerado entra no placar."]}

    @router.post("/api/ranking/submit")
    def submit_to_ranking() -> dict[str, Any]:
        state = get_state()
        if int(state.get("day_of_mandate", 1)) < 365:
            raise HTTPException(status_code=409, detail="Governe ao menos 12 meses para entrar no placar.")
        if state.get("difficulty") == "tranquilo":
            raise HTTPException(status_code=409, detail="A dificuldade Tranquilo não conta para o ranking.")
        name = (state.get("player_character") or {}).get("name") or "Jogador"
        entry = meta.build_entry(state, current_campaign_id(), name.split()[0])
        with connect() as db:
            db.execute(
                "INSERT INTO hall_entries (player_id, campaign_id, term_number, entry_json, points) VALUES (?, ?, ?, ?, ?) "
                "ON CONFLICT(player_id, campaign_id, term_number) DO UPDATE SET entry_json=excluded.entry_json, points=excluded.points",
                (current_player_id(), current_campaign_id(), int(state.get("term", 1)), json.dumps(entry, ensure_ascii=False), entry["pontos"]))
        sync_stamps(state)
        return {"status": "saved", "entry": entry}

    @router.get("/api/collection")
    def collection() -> dict[str, Any]:
        state = get_state()
        new = sync_stamps(state)
        have = unlocked()
        catalog = meta.stamp_catalog(have)
        return {"total": len(catalog), "obtidos": len(have), "novos": new, "carimbos": catalog,
                "aviso": "Carimbos são desta reconstrução; a raridade é de design, não estatística real."}

    @router.get("/api/campaign-week")
    def campaign_week_overview() -> dict[str, Any]:
        state = get_state()
        data = campaign_week.overview(state)
        save(state)  # persiste o estado semanal inicializado
        return data

    @router.post("/api/campaign-week/act")
    def campaign_week_act(body: WeekAction) -> dict[str, Any]:
        state = get_state()
        try:
            result = campaign_week.perform(state, body.action, body.region, body.jet)
        except ValueError as problem:
            raise HTTPException(status_code=409, detail=str(problem))
        save(state)
        return result

    @router.post("/api/campaign-week/close")
    def campaign_week_close() -> dict[str, Any]:
        state = get_state()
        try:
            result = campaign_week.close_week(state)
        except ValueError as problem:
            raise HTTPException(status_code=409, detail=str(problem))
        save(state)
        return result

    @router.get("/api/story")
    def story_overview() -> dict[str, Any]:
        state = get_state()
        data = story.overview(state)
        save(state)
        return data

    @router.post("/api/story/{event_id}/respond")
    def story_respond(event_id: str, body: StoryChoice) -> dict[str, Any]:
        state = get_state()
        try:
            entry = story.respond(state, event_id, body.choice)
        except ValueError as problem:
            raise HTTPException(status_code=409, detail=str(problem))
        save(state)
        return {"entry": entry, "overview": story.overview(state), "metrics": state.get("metrics", {})}

    @router.get("/api/campaign-debate")
    def debate_overview() -> dict[str, Any]:
        state = get_state()
        data = campaign_debate.overview(state)
        save(state)
        return data

    @router.post("/api/campaign-debate/attend")
    def debate_attend(body: DebateChoice) -> dict[str, Any]:
        state = get_state()
        try:
            result = campaign_debate.attend(state, body.choice, body.issue, body.message)
        except ValueError as problem:
            raise HTTPException(status_code=409, detail=str(problem))
        save(state)
        return {"result": result, "overview": campaign_debate.overview(state), "week": campaign_week.overview(state)}

    @router.get("/api/commitments")
    def commitments() -> dict[str, Any]:
        state = get_state()
        return {"compromissos": state.get("commitments", []), "relation_delta": state.get("relation_delta", {})}

    @router.post("/api/commitments/{commitment_id}/resolve")
    def resolve(commitment_id: str, body: CommitmentResolve) -> dict[str, Any]:
        state = get_state()
        try:
            item = legislature.resolve_commitment(state, commitment_id, body.fulfilled)
        except ValueError as problem:
            raise HTTPException(status_code=409, detail=str(problem))
        save(state)
        return {"compromisso": item, "relation_delta": state.get("relation_delta", {})}

    @router.get("/api/diary")
    def diary() -> dict[str, Any]:
        return {"edicoes": meta.DIARY}

    return router
