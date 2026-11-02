"""Add a reviewed local text export or official document to the local RAG corpus.

Usage: python -m app.data.ingest_source --title ... --url ... --kind official --license ... --file document.txt
"""
import argparse
from pathlib import Path

from ..ai.rag import ingest_source
from ..db import initialize


def main() -> None:
    parser = argparse.ArgumentParser(description="Indexa texto com proveniência no corpus local.")
    parser.add_argument("--title", required=True)
    parser.add_argument("--url", required=True)
    parser.add_argument("--kind", required=True, choices=["tse", "legislacao", "congresso", "governo", "estatistica", "outro"])
    parser.add_argument("--license", required=True)
    parser.add_argument("--published-at")
    parser.add_argument("--file", required=True, type=Path)
    args = parser.parse_args()
    initialize()
    chunks = ingest_source(args.title, args.file.read_text(encoding="utf-8"), args.url, args.kind, args.license, args.published_at)
    print(f"Documento indexado em {chunks} trechos; fonte guardada: {args.url}")


if __name__ == "__main__":
    main()
