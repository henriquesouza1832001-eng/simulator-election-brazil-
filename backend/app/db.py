import hashlib
import json
import os
import secrets
import sqlite3
from contextvars import ContextVar
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


_player_id: ContextVar[str] = ContextVar("player_id", default="local")
_campaign_id: ContextVar[str] = ContextVar("campaign_id", default="default")


class _ClosingConnection(sqlite3.Connection):
    """Keep transaction context behavior while always releasing the file handle."""

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            return super().__exit__(exc_type, exc_value, traceback)
        finally:
            self.close()


def set_player_id(player_id: str):
    return _player_id.set(player_id)


def reset_player_id(token) -> None:
    _player_id.reset(token)


def current_player_id() -> str:
    return _player_id.get()


def set_campaign_id(campaign_id: str):
    return _campaign_id.set(campaign_id)


def reset_campaign_id(token) -> None:
    _campaign_id.reset(token)


def current_campaign_id() -> str:
    return _campaign_id.get()


def create_guest_session() -> tuple[str, str]:
    """Create a high-entropy browser session without requiring a player account."""
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    player_id = f"guest:{token_hash}"
    expires_at = (datetime.now(timezone.utc) + timedelta(days=365)).strftime("%Y-%m-%d %H:%M:%S")
    with connect() as db:
        db.execute("DELETE FROM guest_sessions WHERE expires_at <= CURRENT_TIMESTAMP")
        db.execute("INSERT INTO guest_sessions (token_hash, player_id, expires_at) VALUES (?, ?, ?)",
                   (token_hash, player_id, expires_at))
    return token, player_id


def guest_player_id(token: str | None) -> str | None:
    if not token:
        return None
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    with connect() as db:
        row = db.execute("SELECT player_id FROM guest_sessions WHERE token_hash = ? AND expires_at > CURRENT_TIMESTAMP",
                         (token_hash,)).fetchone()
    return str(row["player_id"]) if row else None


def database_path() -> Path:
    configured = os.getenv("DATABASE_PATH", "./data/game.sqlite3")
    path = Path(configured)
    if not path.is_absolute():
        path = Path(__file__).resolve().parents[2] / path
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def connect() -> sqlite3.Connection:
    connection = sqlite3.connect(database_path(), factory=_ClosingConnection)
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
            CREATE TABLE IF NOT EXISTS game_campaigns (
                player_id TEXT NOT NULL,
                campaign_id TEXT NOT NULL,
                campaign_name TEXT NOT NULL,
                state_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (player_id, campaign_id)
            );
            CREATE TABLE IF NOT EXISTS guest_sessions (
                token_hash TEXT PRIMARY KEY,
                player_id TEXT NOT NULL UNIQUE,
                expires_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS game_archives (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id TEXT NOT NULL,
                campaign_id TEXT NOT NULL DEFAULT 'default',
                title TEXT NOT NULL,
                state_json TEXT NOT NULL,
                archived_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
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
                interpretation_log_id INTEGER,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS interpretation_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id TEXT NOT NULL,
                task TEXT NOT NULL DEFAULT 'policy_interpretation',
                input_text TEXT NOT NULL,
                result_json TEXT NOT NULL,
                source TEXT NOT NULL,
                model_name TEXT NOT NULL,
                prompt_version TEXT NOT NULL,
                confidence REAL NOT NULL,
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
        # Keep each existing player's active save as their first named campaign.
        for row in db.execute("SELECT player_id, state_json FROM game_saves").fetchall():
            try:
                saved_state = json.loads(row["state_json"])
            except (TypeError, json.JSONDecodeError):
                saved_state = {}
            career = saved_state.get("career") or {}
            character = saved_state.get("player_character") or {}
            campaign_name = saved_state.get("campaign_name")
            if not campaign_name:
                if career.get("office_label"):
                    campaign_name = f"{character.get('name') or 'Carreira'} · {career['office_label']}"
                else:
                    campaign_name = f"Governo federal · {character.get('name')}" if character.get("name") else "Governo federal"
            db.execute(
                "INSERT OR IGNORE INTO game_campaigns (player_id, campaign_id, campaign_name, state_json, updated_at) "
                "VALUES (?, 'default', ?, ?, COALESCE((SELECT updated_at FROM game_saves WHERE player_id = ?), CURRENT_TIMESTAMP))",
                (row["player_id"], str(campaign_name)[:80], row["state_json"], row["player_id"]),
            )
        for table in ("actions", "interpretation_corrections"):
            columns = {row["name"] for row in db.execute(f"PRAGMA table_info({table})").fetchall()}
            if "player_id" not in columns:
                db.execute(f"ALTER TABLE {table} ADD COLUMN player_id TEXT NOT NULL DEFAULT 'local'")
        action_columns = {row["name"] for row in db.execute("PRAGMA table_info(actions)").fetchall()}
        if "campaign_id" not in action_columns:
            db.execute("ALTER TABLE actions ADD COLUMN campaign_id TEXT NOT NULL DEFAULT 'default'")
        archive_columns = {row["name"] for row in db.execute("PRAGMA table_info(game_archives)").fetchall()}
        if "campaign_id" not in archive_columns:
            db.execute("ALTER TABLE game_archives ADD COLUMN campaign_id TEXT NOT NULL DEFAULT 'default'")
        correction_columns = {row["name"] for row in db.execute("PRAGMA table_info(interpretation_corrections)").fetchall()}
        if "interpretation_log_id" not in correction_columns:
            db.execute("ALTER TABLE interpretation_corrections ADD COLUMN interpretation_log_id INTEGER")
        db.execute("CREATE INDEX IF NOT EXISTS idx_actions_player_id ON actions(player_id, id DESC)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_actions_player_campaign ON actions(player_id, campaign_id, id DESC)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_corrections_player_id ON interpretation_corrections(player_id, id DESC)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_interpretation_log_player_id ON interpretation_log(player_id, id DESC)")


def load_state() -> dict[str, Any] | None:
    with connect() as db:
        row = db.execute(
            "SELECT state_json FROM game_campaigns WHERE player_id = ? AND campaign_id = ?",
            (current_player_id(), current_campaign_id()),
        ).fetchone()
        if row is None and current_campaign_id() == "default":
            legacy = db.execute("SELECT state_json FROM game_saves WHERE player_id = ?", (current_player_id(),)).fetchone()
            row = legacy
    return json.loads(row["state_json"]) if row else None


def save_state(state: dict[str, Any]) -> None:
    career = state.get("career") or {}
    character = state.get("player_character") or {}
    campaign_name = state.get("campaign_name")
    if not campaign_name:
        if career.get("office_label"):
            campaign_name = f"{character.get('name') or 'Carreira'} · {career['office_label']}"
        else:
            campaign_name = f"Governo federal · {character.get('name')}" if character.get("name") else "Governo federal"
    with connect() as db:
        db.execute(
            "INSERT INTO game_campaigns (player_id, campaign_id, campaign_name, state_json) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(player_id, campaign_id) DO UPDATE SET campaign_name=excluded.campaign_name, "
            "state_json=excluded.state_json, updated_at=CURRENT_TIMESTAMP",
            (current_player_id(), current_campaign_id(), str(campaign_name)[:80], json.dumps(state, ensure_ascii=False)),
        )


def campaign_exists(campaign_id: str) -> bool:
    with connect() as db:
        row = db.execute(
            "SELECT 1 FROM game_campaigns WHERE player_id = ? AND campaign_id = ?",
            (current_player_id(), campaign_id),
        ).fetchone()
    return row is not None


def list_campaigns() -> list[dict[str, Any]]:
    with connect() as db:
        rows = db.execute(
            "SELECT campaign_id, campaign_name, state_json, updated_at FROM game_campaigns "
            "WHERE player_id = ? ORDER BY updated_at DESC, created_at DESC",
            (current_player_id(),),
        ).fetchall()
    campaigns: list[dict[str, Any]] = []
    for row in rows:
        try:
            state = json.loads(row["state_json"])
        except (TypeError, json.JSONDecodeError):
            continue
        if state.get("setup_pending"):
            continue
        career = state.get("career") or {}
        campaigns.append({
            "campaign_id": str(row["campaign_id"]),
            "name": str(row["campaign_name"]),
            "date": str(state.get("date", "")),
            "office": str(career.get("office_label") or "Presidência"),
            "phase": str(career.get("phase") or ("governo" if career.get("mode") else "mandato")),
            "difficulty": str(state.get("difficulty", "normal")),
            "updated_at": str(row["updated_at"]),
        })
    return campaigns


def campaign_name(campaign_id: str | None = None) -> str:
    with connect() as db:
        row = db.execute(
            "SELECT campaign_name FROM game_campaigns WHERE player_id = ? AND campaign_id = ?",
            (current_player_id(), campaign_id or current_campaign_id()),
        ).fetchone()
    return str(row["campaign_name"]) if row else "Governo federal"


def archive_state(state: dict[str, Any], title: str) -> int:
    """Keep a recoverable snapshot before switching a player to another career."""
    with connect() as db:
        last_action = db.execute(
            "SELECT COALESCE(MAX(id), 0) AS last_id FROM actions WHERE player_id = ? AND campaign_id = ?",
            (current_player_id(), current_campaign_id()),
        ).fetchone()["last_id"]
        state.setdefault("action_log_end_id", int(last_action))
        cursor = db.execute(
            "INSERT INTO game_archives (player_id, campaign_id, title, state_json) VALUES (?, ?, ?, ?)",
            (current_player_id(), current_campaign_id(), title[:160], json.dumps(state, ensure_ascii=False)),
        )
        # Keep a small rolling set so repeated experiments cannot grow saves forever.
        db.execute(
            "DELETE FROM game_archives WHERE player_id = ? AND campaign_id = ? AND id NOT IN "
            "(SELECT id FROM game_archives WHERE player_id = ? AND campaign_id = ? ORDER BY id DESC LIMIT 12)",
            (current_player_id(), current_campaign_id(), current_player_id(), current_campaign_id()),
        )
        return int(cursor.lastrowid)


def list_archives() -> list[dict[str, Any]]:
    with connect() as db:
        rows = db.execute(
            "SELECT id, title, archived_at FROM game_archives WHERE player_id = ? AND campaign_id = ? ORDER BY id DESC",
            (current_player_id(), current_campaign_id()),
        ).fetchall()
    return [dict(row) for row in rows]


def restore_archive(archive_id: int) -> dict[str, Any] | None:
    with connect() as db:
        row = db.execute(
            "SELECT state_json FROM game_archives WHERE id = ? AND player_id = ? AND campaign_id = ?",
            (archive_id, current_player_id(), current_campaign_id()),
        ).fetchone()
    return json.loads(row["state_json"]) if row else None


def record_action(date: str, kind: str, title: str, source_text: str,
                  interpretation: dict[str, Any], effects: list[dict[str, Any]]) -> int:
    with connect() as db:
        cursor = db.execute(
            "INSERT INTO actions (date, kind, title, source_text, interpretation_json, effects_json, player_id, campaign_id) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (date, kind, title, source_text, json.dumps(interpretation, ensure_ascii=False),
             json.dumps(effects, ensure_ascii=False), current_player_id(), current_campaign_id()),
        )
        return int(cursor.lastrowid)


def recent_actions(limit: int = 10, after_id: int | None = None, through_id: int | None = None) -> list[dict[str, Any]]:
    clauses = ["player_id = ?", "campaign_id = ?"]
    values: list[Any] = [current_player_id(), current_campaign_id()]
    if after_id is not None:
        clauses.append("id >= ?"); values.append(after_id)
    if through_id is not None:
        clauses.append("id <= ?"); values.append(through_id)
    values.append(limit)
    with connect() as db:
        rows = db.execute(f"SELECT id, date, kind, title FROM actions WHERE {' AND '.join(clauses)} ORDER BY id DESC LIMIT ?", values).fetchall()
    return [dict(row) for row in rows]


def add_correction(original_text: str, corrected_interpretation: str) -> None:
    with connect() as db:
        logged = db.execute(
            "SELECT id FROM interpretation_log WHERE player_id = ? AND input_text = ? ORDER BY id DESC LIMIT 1",
            (current_player_id(), original_text),
        ).fetchone()
        db.execute(
            "INSERT INTO interpretation_corrections (original_text, corrected_interpretation, interpretation_log_id, player_id) VALUES (?, ?, ?, ?)",
            (original_text, corrected_interpretation, logged["id"] if logged else None, current_player_id()),
        )


def record_interpretation(text: str, result: dict[str, Any], model_name: str, prompt_version: str) -> int:
    """Keep a player-scoped audit trail; unreviewed outputs are not training labels."""
    source = str(result.get("source", "local"))[:40]
    confidence = result.get("confidence", 0)
    try:
        confidence_value = float(confidence)
    except (TypeError, ValueError):
        confidence_value = 0.0
    if confidence_value != confidence_value or confidence_value in (float("inf"), float("-inf")):
        confidence_value = 0.0
    confidence_value = min(1.0, max(0.0, confidence_value))
    with connect() as db:
        cursor = db.execute(
            "INSERT INTO interpretation_log "
            "(player_id, task, input_text, result_json, source, model_name, prompt_version, confidence) "
            "VALUES (?, 'policy_interpretation', ?, ?, ?, ?, ?, ?)",
            (current_player_id(), text, json.dumps(result, ensure_ascii=False), source,
             model_name[:100], prompt_version[:80], confidence_value),
        )
        return int(cursor.lastrowid)


def load_interpretation(interpretation_id: int) -> dict[str, Any] | None:
    with connect() as db:
        row = db.execute(
            "SELECT input_text, result_json FROM interpretation_log WHERE id = ? AND player_id = ?",
            (interpretation_id, current_player_id()),
        ).fetchone()
    if not row:
        return None
    return {"input_text": str(row["input_text"]), "result": json.loads(row["result_json"])}


def interpretation_count() -> int:
    with connect() as db:
        row = db.execute("SELECT COUNT(*) AS total FROM interpretation_log WHERE player_id = ?", (current_player_id(),)).fetchone()
    return int(row["total"])


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
