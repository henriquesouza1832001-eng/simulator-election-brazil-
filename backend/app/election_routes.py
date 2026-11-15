"""Rotas da apuração e das redes sociais fictícias."""
from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter

from .engine import social_feed, tally


def build_router(get_state: Callable[[], dict[str, Any]]) -> APIRouter:
    router = APIRouter()

    @router.get("/api/election/tally")
    def election_tally() -> dict[str, Any]:
        return tally.build(get_state())

    @router.get("/api/social/feed")
    def social() -> dict[str, Any]:
        return social_feed.build(get_state())

    return router
