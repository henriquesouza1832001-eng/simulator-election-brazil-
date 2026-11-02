"""Retrieval layer for grounded game events and explanations.

This first pass uses lightweight local lexical retrieval in SQLite. The interface
returns source and date metadata so it can later move to Oracle Vector Search,
Qdrant or pgvector without changing the event/rules contract.
"""
import hashlib
import re
from typing import Any

from ..db import connect

STOPWORDS = {"para", "como", "mais", "sobre", "entre", "pela", "pelo", "com", "sem", "uma", "que", "dos", "das", "por", "nos", "nas", "the", "and", "from", "this", "that"}


def _tokens(text: str) -> set[str]:
    return {token for token in re.findall(r"[\wÀ-ÿ]{3,}", text.lower()) if token not in STOPWORDS}


def _chunks(text: str, size: int = 1100, overlap: int = 120) -> list[str]:
    normalized = re.sub(r"\s+", " ", text).strip()
    output, start = [], 0
    while start < len(normalized):
        end = min(len(normalized), start + size)
        if end < len(normalized):
            boundary = normalized.rfind(". ", start + size // 2, end)
            if boundary > start:
                end = boundary + 1
        output.append(normalized[start:end].strip())
        if end >= len(normalized):
            break
        start = max(start + 1, end - overlap)
    return output


def ingest_source(title: str, text: str, source_url: str, source_kind: str,
                  license_name: str, published_at: str | None = None) -> int:
    document_key = hashlib.sha256(f"{source_url}\n{title}".encode("utf-8")).hexdigest()
    chunks = _chunks(text)
    with connect() as db:
        db.execute("DELETE FROM knowledge_chunks WHERE document_key = ?", (document_key,))
        db.executemany("""
            INSERT INTO knowledge_chunks (document_key, title, chunk_number, text, source_url, source_kind, license_name, published_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, [(document_key, title, i, chunk, source_url, source_kind, license_name, published_at) for i, chunk in enumerate(chunks)])
    return len(chunks)


def retrieve(query: str, limit: int = 5) -> list[dict[str, Any]]:
    terms = _tokens(query)
    if not terms:
        return []
    with connect() as db:
        rows = db.execute("SELECT title, text, source_url, source_kind, license_name, published_at FROM knowledge_chunks").fetchall()
    scored = []
    for row in rows:
        content_terms = _tokens(row["title"] + " " + row["text"])
        overlap = terms & content_terms
        if not overlap:
            continue
        # BM25-like lightweight score; intentionally transparent and replaceable.
        score = sum(1 + (len(content_terms) / max(1, len(terms))) ** -0.5 for _ in overlap) / (1 + len(content_terms) / 900)
        scored.append((score, {**dict(row), "relevance": round(score, 3)}))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [item[1] for item in scored[:max(1, min(limit, 10))]]


def event_evidence_brief(topic: str, state: dict[str, Any], limit: int = 4) -> dict[str, Any]:
    metrics = state.get("metrics", {})
    context = retrieve(topic, limit)
    return {
        "instruction": "Use evidence only for real-world context. Any incident and choices created for this campaign are fictional game content.",
        "topic": topic,
        "game_date": state.get("date"),
        "campaign_metrics": {key: metrics[key] for key in ("gdp_growth", "inflation", "debt_gdp", "approval") if key in metrics},
        "evidence": [{"title": item["title"], "excerpt": item["text"], "source": item["source_url"], "source_type": item["source_kind"], "published_at": item["published_at"], "license": item["license_name"]} for item in context],
        "grounding_status": "grounded" if context else "no_matching_source",
    }
