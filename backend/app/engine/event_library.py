"""Biblioteca de acontecimentos: catálogo antigo + geradores por famílias + arquivos JSON (aprovados).

Eventos em `backend/data/events/*.json` entram só se `review == "aprovado"`, salvo se a variável
`EVENTS_INCLUDE_PENDING=1`. Eventos gerados por IA nascem como `pendente` (ver `app/ai/event_generator.py`).
Qualquer evento inválido é descartado e contado; encadeamentos para eventos inexistentes são cortados.
"""
from __future__ import annotations

import json
import logging
import os
from collections import Counter
from pathlib import Path
from typing import Any

from . import event_schema as schema
from .event_templates import generate_all
from .story_catalog import EVENTS as LEGACY_EVENTS

logger = logging.getLogger(__name__)
EVENTS_DIR = Path(__file__).resolve().parents[2] / "data" / "events"
_cache: "Library | None" = None
_real_names: set[str] | None = None


def _normalize_name(text: str) -> str:
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFKD", text or "") if not unicodedata.combining(c)).upper().strip()


def real_person_names() -> set[str]:
    """Nomes de urna de candidatos de maior visibilidade (TSE) que **nunca** podem aparecer em eventos gerados."""
    global _real_names
    if _real_names is not None:
        return _real_names
    names: set[str] = set()
    try:
        from ..db import connect
        with connect() as db:
            rows = db.execute("SELECT DISTINCT ballot_name FROM tse_candidacies WHERE office IN "
                              "('PRESIDENTE','VICE-PRESIDENTE','GOVERNADOR','VICE-GOVERNADOR','SENADOR','DEPUTADO FEDERAL') "
                              "AND election_year >= 2014 AND ballot_name IS NOT NULL").fetchall()
        for row in rows:
            name = _normalize_name(row[0])
            if len(name.split()) >= 2 and len(name) >= 8:
                names.add(name)
    except Exception as problem:  # banco ausente em testes isolados: a trava fica vazia, mas é registrada
        logger.warning("Trava de nomes reais indisponível: %s", problem)
    _real_names = names
    return names


def mentions_real_person(text: str) -> str | None:
    """Devolve o primeiro nome real encontrado no texto (maiúsculas, sem acento), ou None."""
    haystack = f" {_normalize_name(text)} "
    for name in real_person_names():
        if f" {name} " in haystack or f" {name}," in haystack or f" {name}." in haystack:
            return name
    return None


def _from_legacy(def_id: str, d: dict[str, Any]) -> dict[str, Any]:
    ev = {"id": def_id, "kind": d["kind"], "tags": d.get("tags", []), "levels": ["federal"], "weight": d.get("weight", 1.0),
          "cooldown": d.get("cooldown", 120), "title": d["title"], "text": d["text"], "fallback": d.get("fallback"),
          "choices": [{**c, "follow": [list(f) for f in c.get("follow", [])]} for c in d["choices"]],
          "source": {"type": "manual", "ref": "catálogo inicial"}, "review": "aprovado", "family": "base"}
    ev["when"] = d["when"]  # condição em código (catálogo inicial); eventos novos usam dados
    return ev


class Library:
    def __init__(self) -> None:
        self.events: dict[str, dict[str, Any]] = {}
        self.report: dict[str, Any] = {"invalid": 0, "invalid_examples": [], "rejected_real_person": 0, "dropped_follow": 0, "pending_skipped": 0}

    def add(self, raw: dict[str, Any], *, guard_real: bool = False) -> bool:
        problems = schema.validate_event(raw) if "when" not in raw else schema.validate_event({k: v for k, v in raw.items() if k != "when"})
        if guard_real:
            blob = " ".join([raw.get("title", ""), raw.get("text", "")] + [c.get("label", "") + " " + c.get("outcome", "") for c in raw.get("choices", [])])
            found = mentions_real_person(blob)
            if found:
                problems.append(f"menciona pessoa real: {found}")
                self.report["rejected_real_person"] += 1
        if problems or raw["id"] in self.events:
            self.report["invalid"] += 1
            if len(self.report["invalid_examples"]) < 5:
                self.report["invalid_examples"].append({"id": raw.get("id"), "problems": problems or ["id repetido"]})
            return False
        ev = dict(raw)
        if "when" not in ev:
            ev = schema.normalize_event(ev)
        else:
            ev.setdefault("family", "base")
        self.events[ev["id"]] = ev
        return True

    def finalize(self) -> None:
        """Corta encadeamentos para eventos que não existem."""
        for ev in self.events.values():
            for choice in ev["choices"]:
                kept = [f for f in choice.get("follow", []) if f[0] in self.events]
                self.report["dropped_follow"] += len(choice.get("follow", [])) - len(kept)
                choice["follow"] = kept

    def get(self, def_id: str) -> dict[str, Any] | None:
        return self.events.get(def_id)

    def stats(self) -> dict[str, Any]:
        evs = list(self.events.values())
        edges = sum(len(c.get("follow", [])) for e in evs for c in e["choices"])
        return {"total": len(evs), "by_source": dict(Counter(e["source"]["type"] for e in evs)), "by_kind": dict(Counter(e["kind"] for e in evs)),
                "by_level": dict(Counter(l for e in evs for l in e["levels"])), "families": len({e["family"] for e in evs}),
                "chained_events": sum(1 for e in evs if any(c.get("follow") for c in e["choices"])), "chain_links": edges,
                "entry_events": sum(1 for e in evs if e.get("weight", 1.0) > 0), "report": self.report}


def _load_json_events(lib: Library) -> None:
    include_pending = os.getenv("EVENTS_INCLUDE_PENDING") == "1"
    if not EVENTS_DIR.exists():
        return
    for path in sorted(EVENTS_DIR.rglob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            lib.report["invalid"] += 1
            continue
        items = payload.get("events", []) if isinstance(payload, dict) else payload
        for item in items:
            if not isinstance(item, dict):
                continue
            if item.get("review", "pendente") != "aprovado" and not include_pending:
                lib.report["pending_skipped"] += 1
                continue
            lib.add(item, guard_real=True)


def build_library() -> Library:
    lib = Library()
    for def_id, d in LEGACY_EVENTS.items():
        lib.add(_from_legacy(def_id, d))
    for raw in generate_all():
        lib.add(raw)
    _load_json_events(lib)
    lib.finalize()
    return lib


def get_library(reload: bool = False) -> Library:
    global _cache
    if _cache is None or reload:
        _cache = build_library()
    return _cache


def _main() -> int:
    """`python -m app.engine.event_library`: valida a biblioteca e sai com erro se houver evento inválido."""
    import sys
    lib = build_library()
    stats = lib.stats()
    print(json.dumps({k: stats[k] for k in ("total", "entry_events", "chained_events", "families", "by_source", "by_level")}, ensure_ascii=False))
    problems = stats["report"]
    if problems["invalid"] or problems["dropped_follow"] or problems["rejected_real_person"]:
        print("Eventos inválidos:", json.dumps(problems, ensure_ascii=False), file=sys.stderr)
        return 1
    if stats["total"] < 2000:
        print("A biblioteca tem menos de 2.000 eventos válidos.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
