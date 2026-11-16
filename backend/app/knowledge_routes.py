"""Leis e história do Brasil: base de conhecimento usada como régua e como memória do jogo."""
from __future__ import annotations

import json
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import APIRouter

from .engine import powers_catalog

DATA = Path(__file__).resolve().parents[1] / "data" / "conhecimento"


@lru_cache(maxsize=1)
def _load(name: str) -> dict[str, Any]:
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def _plain(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", text.lower()) if unicodedata.category(c) != "Mn")


def actions_citing(norm: dict[str, Any]) -> list[dict[str, str]]:
    """Ações do catálogo de competências que citam a norma na base legal ou no precedente."""
    keys = [k for k in norm.get("match", []) if k]
    if not keys:
        return []
    found = []
    for action in powers_catalog.ACTIONS:
        haystack = f"{action.get('basis', '')} {action.get('precedent') or ''}"
        if any(k in haystack for k in keys):
            found.append({"id": action["id"], "title": action["title"]})
    return found


def build_router() -> APIRouter:
    router = APIRouter()

    @router.get("/api/knowledge/laws")
    def laws(q: str = "", tipo: str = "") -> dict[str, Any]:
        data = _load("normas.json")
        term = _plain(q.strip())
        items = []
        for norm in data["normas"]:
            if tipo and norm["tipo"] != tipo:
                continue
            if term and term not in _plain(f"{norm['citacao']} {norm['nome']} {norm['assunto']} {norm['resumo']}"):
                continue
            actions = actions_citing(norm)
            items.append({k: v for k, v in norm.items() if k != "match"} | {"acoes": actions})
        return {"aviso": data["aviso"], "total": len(data["normas"]), "tipos": sorted({n["tipo"] for n in data["normas"]}), "normas": items}

    @router.get("/api/knowledge/memory")
    def memory() -> dict[str, Any]:
        data = _load("memoria.json")
        titles = {a["id"]: a["title"] for a in powers_catalog.ACTIONS}
        facts = [{**f, "acoes": [{"id": i, "title": titles[i]} for i in f.get("no_jogo", []) if i in titles]} for f in data["fatos"]]
        return {"aviso": data["aviso"], "categorias": sorted({f["categoria"] for f in facts}), "fatos": facts}

    return router
