import json
import os
import sqlite3
from contextvars import ContextVar
from pathlib import Path
from typing import Any


_player_id: ContextVar[str] = ContextVar("player_id", default="local")


def set_player_id(player_id: str):
    return _player_id.set(player_id)


def reset_player_id(token) -> None:
    _player_id.reset(token)


def current_player_id() -> str:
    return _player_id.get()


def database_path() -> Path:
    configured = os.getenv("DATABASE_PATH", "./data/game.sqlite3")
    path = Path(configured)
    if not path.is_absolute():
        path = Path(__file__).resolve().parents[2] / path
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def connect() -> sqlite3.Connection:
    connection = sqlite3.connect(database_path())
    connection.row_factory = sqlite3.Row
    return connection


def initialize() -> None:
    with connect() as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS game_save (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                state_json TEXT NOT NULL,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS game_saves (
                player_id TEXT PRIMARY KEY,
                state_json TEXT NOT NULL,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                kind TEXT NOT NULL,
                title TEXT NOT NULL,
                source_text TEXT NOT NULL,
                interpretation_json TEXT NOT NULL,
                effects_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS interpretation_corrections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_text TEXT NOT NULL,
                corrected_interpretation TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS knowledge_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_key TEXT NOT NULL,
                title TEXT NOT NULL,
                chunk_number INTEGER NOT NULL,
                text TEXT NOT NULL,
                source_url TEXT NOT NULL,
                source_kind TEXT NOT NULL,
                license_name TEXT NOT NULL,
                published_at TEXT,
                ingested_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(document_key, chunk_number)
            );
        """)
        # Preserve the existing single-player save when moving to player-scoped storage.
        legacy = db.execute("SELECT state_json FROM game_save WHERE id = 1").fetchone()
        if legacy:
            db.execute("INSERT OR IGNORE INTO game_saves (player_id, state_json) VALUES ('local', ?)",
                       (legacy["state_json"],))
        for table in ("actions", "interpretation_corrections"):
            columns = {row["name"] for row in db.execute(f"PRAGMA table_info({table})").fetchall()}
            if "player_id" not in columns:
                db.execute(f"ALTER TABLE {table} ADD COLUMN player_id TEXT NOT NULL DEFAULT 'local'")
        db.execute("CREATE INDEX IF NOT EXISTS idx_actions_player_id ON actions(player_id, id DESC)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_corrections_player_id ON interpretation_corrections(player_id, id DESC)")


def load_state() -> dict[str, Any] | None:
    with connect() as db:
        row = db.execute("SELECT state_json FROM game_saves WHERE player_id = ?", (current_player_id(),)).fetchone()
    return json.loads(row["state_json"]) if row else None


def save_state(state: dict[str, Any]) -> None:
    with connect() as db:
        db.execute(
            "INSERT INTO game_saves (player_id, state_json, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP) "
            "ON CONFLICT(player_id) DO UPDATE SET state_json=excluded.state_json, updated_at=CURRENT_TIMESTAMP",
            (current_player_id(), json.dumps(state, ensure_ascii=False)),
        )


def record_action(date: str, kind: str, title: str, source_text: str,
                  interpretation: dict[str, Any], effects: list[dict[str, Any]]) -> None:
    with connect() as db:
        db.execute(
            "INSERT INTO actions (date, kind, title, source_text, interpretation_json, effects_json, player_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (date, kind, title, source_text, json.dumps(interpretation, ensure_ascii=False), json.dumps(effects, ensure_ascii=False), current_player_id()),
        )


def recent_actions(limit: int = 10) -> list[dict[str, Any]]:
    with connect() as db:
        rows = db.execute("SELECT id, date, kind, title FROM actions WHERE player_id = ? ORDER BY id DESC LIMIT ?", (current_player_id(), limit)).fetchall()
    return [dict(row) for row in rows]


def add_correction(original_text: str, corrected_interpretation: str) -> None:
    with connect() as db:
        db.execute(
            "INSERT INTO interpretation_corrections (original_text, corrected_interpretation, player_id) VALUES (?, ?, ?)",
            (original_text, corrected_interpretation, current_player_id()),
        )


def useful_corrections(text: str, limit: int = 3) -> list[dict[str, str]]:
    """Small lexical retrieval for examples; later replaceable by local embeddings."""
    words = {w for w in text.lower().split() if len(w) > 4}
    with connect() as db:
        rows = db.execute("SELECT original_text, corrected_interpretation FROM interpretation_corrections WHERE player_id = ? ORDER BY id DESC LIMIT 200", (current_player_id(),)).fetchall()
    scored = []
    for row in rows:
        other = {w for w in row["original_text"].lower().split() if len(w) > 4}
        score = len(words & other)
        if score:
            scored.append((score, {"example": row["original_text"], "correction": row["corrected_interpretation"]}))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [item[1] for item in scored[:limit]]


def correction_count() -> int:
    with connect() as db:
        row = db.execute("SELECT COUNT(*) AS total FROM interpretation_corrections WHERE player_id = ?", (current_player_id(),)).fetchone()
    return int(row["total"])
