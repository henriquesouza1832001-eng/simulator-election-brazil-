"""Train per-player interpretation candidates and report held-out accuracy.

Run from backend: python -m app.ai.trainer
Artifacts stay beside the SQLite database and are never read by live traffic.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..db import connect, database_path, initialize
from .interpreter import CATEGORIES, INSTRUMENTS
from .local_interpreter import ALGORITHM, evaluate_field


TRAINABLE_FIELDS = ("category", "instrument")


def load_reviewed_examples(player_id: str | None = None) -> dict[str, list[dict[str, Any]]]:
    initialize()
    with connect() as db:
        if player_id is None:
            rows = db.execute(
                "SELECT player_id, original_text, labels_json FROM interpretation_corrections "
                "WHERE labels_json IS NOT NULL ORDER BY id"
            ).fetchall()
        else:
            rows = db.execute(
                "SELECT player_id, original_text, labels_json FROM interpretation_corrections "
                "WHERE labels_json IS NOT NULL AND player_id = ? ORDER BY id",
                (player_id,),
            ).fetchall()

    per_player: dict[str, dict[str, dict[str, Any]]] = {}
    for row in rows:
        try:
            labels = json.loads(row["labels_json"])
        except (TypeError, json.JSONDecodeError):
            continue
        if not isinstance(labels, dict):
            continue
        clean_labels = {
            field: labels[field] for field in TRAINABLE_FIELDS
            if (field in labels and isinstance(labels[field], str)
                and labels[field] in (CATEGORIES if field == "category" else INSTRUMENTS))
        }
        text = str(row["original_text"] or "").strip()[:3000]
        if not clean_labels or len(text) < 5:
            continue
        player_id = str(row["player_id"])
        # For a repeated proposal, the most recent reviewed label wins.
        player_examples = per_player.setdefault(player_id, {})
        key = text.casefold()
        example = player_examples.setdefault(key, {"text": text, "labels": {}})
        # Category and instrument can be reviewed separately. Keep the newest
        # value per field instead of discarding an earlier label.
        example["text"] = text
        example["labels"].update(clean_labels)
    return {
        player_id: list(examples.values())
        for player_id, examples in per_player.items()
    }


def _write_candidate(output_dir: Path, player_hash: str, field: str,
                     result: dict[str, Any]) -> str | None:
    model = result.get("model")
    if not model:
        return None
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{player_hash}.{field}.candidate.json"
    artifact = {
        "format_version": 1,
        "algorithm": ALGORITHM,
        "player_key": player_hash,
        "field": field,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "validation": {key: value for key, value in result.items() if key != "model"},
        "model": model,
        "activation": "offline_candidate_only",
    }
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)
    return str(path)


def train(output_dir: Path | None = None, *, player_id: str | None = None) -> dict[str, Any]:
    examples_by_player = load_reviewed_examples(player_id)
    destination = output_dir or Path(os.getenv(
        "INTERPRETER_MODEL_DIR", str(database_path().parent / "interpreter_models")
    ))
    reports = []
    for player_id, examples in sorted(examples_by_player.items()):
        player_hash = hashlib.sha256(player_id.encode("utf-8")).hexdigest()[:20]
        fields = {}
        for field in TRAINABLE_FIELDS:
            result = evaluate_field(examples, field)
            result["artifact"] = _write_candidate(destination, player_hash, field, result)
            fields[field] = result
        reports.append({
            "player_key": player_hash,
            "reviewed_proposals": len(examples),
            "fields": fields,
        })
    return {
        "status": "completed" if reports else "no_structured_labels",
        "players": len(reports),
        "artifacts_directory": str(destination),
        "live_interpreter_changed": False,
        "reports": reports,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Avalia e treina candidatos locais com correções confirmadas por jogador.")
    parser.add_argument("--output-dir", type=Path, help="Pasta de saída; padrão: ao lado do banco SQLite.")
    args = parser.parse_args()
    print(json.dumps(train(args.output_dir), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
