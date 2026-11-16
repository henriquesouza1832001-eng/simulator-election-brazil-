"""Rotas da apuração e das redes sociais fictícias."""
from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter

from .engine import social_feed, tally, tally_municipal


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

    @router.get("/api/social/feed")
    def social() -> dict[str, Any]:
        return social_feed.build(get_state())

    return router
