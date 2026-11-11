"""Aprendizado do mapeamento texto -> ação: guarda o que o jogador confirmou e recupera frases parecidas."""
from __future__ import annotations

from typing import Any

from .db import connect, current_player_id
from .engine.action_mapper import tokens

_READY = False


def _ensure() -> None:
    global _READY
    with connect() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS action_choices (
            id INTEGER PRIMARY KEY AUTOINCREMENT, player_id TEXT NOT NULL, text TEXT NOT NULL, action_id TEXT NOT NULL,
            option TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)""")
        db.execute("CREATE INDEX IF NOT EXISTS idx_action_choices_player ON action_choices(player_id, id DESC)")
    _READY = True


def record_choice(text: str, action_id: str, option: str | None = None) -> None:
    _ensure()
    with connect() as db:
        db.execute("INSERT INTO action_choices (player_id, text, action_id, option) VALUES (?, ?, ?, ?)",
                   (current_player_id(), text[:400], action_id[:60], option))


def similar_choices(text: str, limit: int = 5) -> list[dict[str, Any]]:
    _ensure()
    mine = set(tokens(text))
    if not mine:
        return []
    with connect() as db:
        rows = db.execute("SELECT text, action_id, option FROM action_choices WHERE player_id = ? ORDER BY id DESC LIMIT 200", (current_player_id(),)).fetchall()
    scored = []
    for r in rows:
        other = set(tokens(r["text"]))
        if not other:
            continue
        sim = len(mine & other) / len(mine | other)
        if sim >= 0.5:
            scored.append((sim, {"text": r["text"], "action_id": r["action_id"], "option": r["option"]}))
    scored.sort(key=lambda t: -t[0])
    return [item for _, item in scored[:limit]]
