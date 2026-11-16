"""Rotas da apuração e das redes sociais fictícias."""
from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter

import json
from functools import lru_cache
from pathlib import Path

from fastapi import HTTPException, Response

from .engine import social_feed, tally, tally_municipal

MESH_DIR = Path(__file__).resolve().parents[1] / "data" / "malhas"


@lru_cache(maxsize=32)
def _mesh(uf: str) -> dict[str, Any]:
    return json.loads((MESH_DIR / f"{uf}.json").read_text(encoding="utf-8"))


def build_router(get_state: Callable[[], dict[str, Any]]) -> APIRouter:
    router = APIRouter()

    @router.get("/api/election/tally")
    def election_tally() -> dict[str, Any]:
        return tally.build(get_state())

    @router.get("/api/election/tally/municipal")
    def election_tally_municipal(uf: str = "") -> dict[str, Any]:
        state = get_state()
        ufs = tally_municipal.available_ufs(state)
        if not ufs:
            return {"available": False, "ufs": [], "reason": "O mapa por município aparece depois do resultado da eleição para presidente, governador ou senador."}
        chosen = uf.upper() if uf.upper() in ufs else ufs[0]
        return {**tally_municipal.build(state, chosen), "ufs": ufs}

    @router.get("/api/geo/municipios/{uf}")
    def municipal_mesh(uf: str, response: Response) -> dict[str, Any]:
        """Contorno dos municípios de um estado (malhas do IBGE), para o mapa de votação."""
        uf = uf.upper()
        if uf not in tally.UFS or not (MESH_DIR / f"{uf}.json").exists():
            raise HTTPException(status_code=404, detail="Malha não encontrada para este estado.")
        response.headers["Cache-Control"] = "public, max-age=86400"
        return _mesh(uf)

    @router.get("/api/social/feed")
    def social() -> dict[str, Any]:
        return social_feed.build(get_state())

    return router
