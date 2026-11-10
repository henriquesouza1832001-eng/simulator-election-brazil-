"""Gerador de acontecimentos a partir de um corpus de fatos históricos.

Fluxo: corpus (JSONL com fonte) → Gemini (opcional) ou adaptação local → validação → arquivo **pendente de revisão**.
Nada gerado entra no jogo sem aprovação explícita (`review = "aprovado"`).

Regras de conteúdo (aplicadas na validação, não só no prompt):
- O evento é uma **ficção inspirada** no fato; cita papéis e instituições genéricos, nunca pessoas reais.
- Qualquer nome de candidato de maior visibilidade (TSE) no texto reprova o evento.
- Efeitos têm limites (ver `event_schema.EFFECT_LIMITS`); o motor decide os números, a IA propõe.
- A chave do Gemini fica só no backend (`GEMINI_API_KEY`). Sem chave, usa-se a adaptação local.

Uso:
  python -m app.ai.event_generator generate --corpus data/events/corpus/fatos.jsonl --limit 20
  python -m app.ai.event_generator generate --corpus ... --local          # sem Gemini
  python -m app.ai.event_generator approve data/events/generated/arquivo.json   # revisão humana feita
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Awaitable, Callable

import httpx

from ..engine import event_schema as schema
from ..engine.event_library import EVENTS_DIR, mentions_real_person

logger = logging.getLogger(__name__)
GENERATED_DIR = EVENTS_DIR / "generated"
DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
MODEL_PATTERN = re.compile(r"[A-Za-z0-9._-]{3,80}")

INSTRUCTIONS = """Você cria acontecimentos para um simulador político brasileiro FICTÍCIO e satírico.
Receberá fatos históricos resumidos (com fonte). Para cada fato, crie UM acontecimento de jogo em português do Brasil.
Regras obrigatórias:
- É uma ficção inspirada no tema do fato. NÃO cite pessoas reais, nem nomes de candidatos, nem atribua falas, crimes, doenças ou atos a pessoas reais.
  Use papéis genéricos (um ministro fictício, entidades fictícias, uma agência fictícia).
- Responda SOMENTE com JSON no esquema pedido.
- kind: decisao (prazo curto), oportunidade (prazo maior) ou info.
- Decisão/oportunidade: 2 a 4 opções com tons diferentes; info: 1 opção.
- effects usa só estas chaves: approval, congress_support, integrity, governability, institutional_trust, gdp_growth, inflation,
  unemployment, primary_balance, inst:<nome>, rel:<SIGLA>. Valores pequenos (aprovação entre -4 e +4; economia entre -0.5 e +0.5).
- cost_bi em bilhões de reais, de 0 a 8.
- Opções boas devem ter custo ou contrapartida; opções omissas devem ter custo de opinião.
- Título de 10 a 120 caracteres; texto de 40 a 600 caracteres; desfecho de cada opção em uma frase."""

OUTPUT_SCHEMA = {
    "type": "ARRAY",
    "items": {
        "type": "OBJECT",
        "properties": {
            "corpus_id": {"type": "STRING"}, "kind": {"type": "STRING"}, "level": {"type": "STRING"},
            "tags": {"type": "ARRAY", "items": {"type": "STRING"}}, "title": {"type": "STRING"}, "text": {"type": "STRING"},
            "choices": {"type": "ARRAY", "items": {"type": "OBJECT", "properties": {
                "id": {"type": "STRING"}, "label": {"type": "STRING"}, "hint": {"type": "STRING"}, "tone": {"type": "STRING"},
                "cost_bi": {"type": "NUMBER"}, "outcome": {"type": "STRING"},
                "effects": {"type": "OBJECT"}}, "required": ["id", "label", "outcome"]}},
        },
        "required": ["corpus_id", "kind", "title", "text", "choices"],
    },
}

Caller = Callable[[str, list[dict[str, Any]]], Awaitable[list[dict[str, Any]]]]


def load_corpus(path: Path, limit: int | None = None) -> list[dict[str, Any]]:
    """Lê JSONL: {id, date, title, summary, area, level?, source_name, source_url}. Linhas sem fonte são ignoradas."""
    items: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if item.get("id") and item.get("summary") and (item.get("source_url") or item.get("source_name")):
            items.append(item)
        if limit and len(items) >= limit:
            break
    return items


async def gemini_call(model: str, key: str, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Chama o Gemini com um lote do corpus e devolve a lista de eventos propostos (ainda não validados)."""
    if not MODEL_PATTERN.fullmatch(model):
        raise ValueError("Nome de modelo inválido.")
    payload = {
        "systemInstruction": {"parts": [{"text": INSTRUCTIONS}]},
        "contents": [{"role": "user", "parts": [{"text": "Fatos históricos (corpus):\n" + json.dumps(
            [{"corpus_id": i["id"], "data": i.get("date"), "area": i.get("area"), "titulo": i.get("title"), "resumo": i["summary"]} for i in items],
            ensure_ascii=False)}]}],
        "generationConfig": {"responseFormat": {"text": {"mimeType": "APPLICATION_JSON", "schema": OUTPUT_SCHEMA}},
                             "thinkingConfig": {"thinkingLevel": "low"}, "maxOutputTokens": 6000},
    }
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    async with httpx.AsyncClient(timeout=httpx.Timeout(connect=5, read=90, write=10, pool=5)) as client:
        response = await client.post(endpoint, headers={"x-goog-api-key": key}, json=payload)
    response.raise_for_status()
    data = response.json()
    parts = data["candidates"][0]["content"]["parts"]
    text = next(p["text"] for p in parts if isinstance(p, dict) and isinstance(p.get("text"), str))
    result = json.loads(text)
    return result if isinstance(result, list) else []


def local_adapt(item: dict[str, Any]) -> dict[str, Any] | None:
    """Adaptação sem IA: transforma o fato em um acontecimento genérico do mesmo assunto.

    Usa apenas a área e o título (sem nomes). Se o título tiver nome real, o item é descartado na validação.
    """
    area = (item.get("area") or "geral").lower()
    impact = {"economia": {"gdp_growth": -0.1, "inflation": 0.2}, "saude": {"approval": -0.8}, "seguranca": {"approval": -0.8},
              "clima": {"approval": -0.6, "gdp_growth": -0.05}, "trabalho": {"approval": -0.6}, "integridade": {"integrity": -1.5}}.get(area, {"approval": -0.6})
    title = (item.get("title") or "Fato relevante").strip()
    return {
        "corpus_id": item["id"], "kind": "decisao", "level": item.get("level", "federal"), "tags": [area, "historico"],
        "title": f"Situação semelhante a um fato recente: {title}"[:120],
        "text": (f"Um episódio parecido com um fato do noticiário ({area}) ganha repercussão no país fictício do jogo. "
                 f"Interlocutores pedem uma posição do governo sobre o tema.")[:600],
        "choices": [
            {"id": "agir", "label": "Agir com um plano e diálogo", "hint": "Custa dinheiro e atenção.", "tone": "dialogo", "cost_bi": 1.0,
             "effects": {"approval": 1.0, "governability": 0.8}, "outcome": "A resposta organizada melhora a percepção de gestão."},
            {"id": "omitir", "label": "Evitar se envolver", "hint": "Sem custo agora.", "tone": "passiva", "effects": impact,
             "outcome": "A omissão pesa na avaliação do governo."}],
    }


def to_event(raw: dict[str, Any], corpus: dict[str, dict[str, Any]], model: str | None) -> dict[str, Any]:
    src = corpus.get(raw.get("corpus_id", ""), {})
    digest = hashlib.sha1(f"{raw.get('corpus_id')}|{raw.get('title')}".encode()).hexdigest()[:10]
    level = raw.get("level") if raw.get("level") in schema.LEVELS else src.get("level", "federal")
    choices = []
    for ch in raw.get("choices", []):
        choices.append({"id": str(ch.get("id", "")).strip(), "label": str(ch.get("label", "")).strip(), "hint": str(ch.get("hint", "")).strip(),
                        "tone": ch.get("tone", "neutra") if ch.get("tone") in schema.TONES else "neutra",
                        "cost_bi": float(ch.get("cost_bi", 0) or 0), "effects": {k: float(v) for k, v in (ch.get("effects") or {}).items() if isinstance(v, (int, float))},
                        "outcome": str(ch.get("outcome", "")).strip(), "follow": []})
    return {
        "id": f"{'gemini' if model else 'local'}:{digest}", "kind": raw.get("kind", "decisao"), "tags": [str(t) for t in raw.get("tags", [])][:5] or ["historico"],
        "levels": [level], "weight": 0.8, "cooldown": 180, "family": f"hist:{src.get('area', 'geral')}", "title": str(raw.get("title", "")).strip(),
        "text": str(raw.get("text", "")).strip(), "choices": choices,
        "source": {"type": "gemini" if model else "historico_inspirado", "ref": src.get("source_url") or src.get("source_name"),
                   "corpus_id": raw.get("corpus_id"), "fact_date": src.get("date"), "model": model},
        "review": "pendente", "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def validate_generated(ev: dict[str, Any]) -> list[str]:
    problems = schema.validate_event(ev)
    blob = " ".join([ev.get("title", ""), ev.get("text", "")] + [c.get("label", "") + " " + c.get("outcome", "") + " " + c.get("hint", "") for c in ev.get("choices", [])])
    found = mentions_real_person(blob)
    if found:
        problems.append(f"menciona pessoa real: {found}")
    return problems


async def generate(corpus_path: Path, limit: int, use_gemini: bool, batch_size: int = 5, caller: Caller | None = None) -> dict[str, Any]:
    items = load_corpus(corpus_path, limit)
    by_id = {i["id"]: i for i in items}
    key = os.getenv("GEMINI_API_KEY", "").strip()
    model = DEFAULT_MODEL if (use_gemini and key) else None
    proposals: list[dict[str, Any]] = []
    errors: list[str] = []
    for start in range(0, len(items), batch_size):
        batch = items[start:start + batch_size]
        try:
            if caller is not None:
                proposals += await caller(model or "teste", batch)
            elif model:
                proposals += await gemini_call(model, key, batch)
            else:
                proposals += [p for p in (local_adapt(i) for i in batch) if p]
        except (httpx.HTTPError, KeyError, StopIteration, ValueError, json.JSONDecodeError) as problem:
            errors.append(f"lote {start // batch_size + 1}: {type(problem).__name__}")
            logger.warning("Falha ao gerar lote: %s", problem)
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for raw in proposals:
        ev = to_event(raw, by_id, model if (model or caller) else None)
        problems = validate_generated(ev)
        if ev["id"] in seen_ids:
            problems.append("id repetido no lote")
        if problems:
            rejected.append({"id": ev["id"], "title": ev["title"][:60], "problems": problems})
        else:
            seen_ids.add(ev["id"])
            accepted.append(ev)
    out_path = None
    if accepted:
        GENERATED_DIR.mkdir(parents=True, exist_ok=True)
        out_path = GENERATED_DIR / f"{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{'gemini' if model else 'local'}.json"
        out_path.write_text(json.dumps({"events": accepted}, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"mode": "gemini" if model else "local", "corpus_items": len(items), "proposed": len(proposals), "accepted_pending_review": len(accepted),
            "rejected": len(rejected), "rejected_examples": rejected[:5], "errors": errors, "file": str(out_path) if out_path else None}


def approve(path: Path) -> dict[str, Any]:
    """Marca como aprovados os eventos válidos de um arquivo. É um ato de revisão humana, nunca automático."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    items = payload["events"] if isinstance(payload, dict) else payload
    ok = bad = 0
    for ev in items:
        if validate_generated(ev):
            bad += 1
            continue
        ev["review"] = "aprovado"
        ev["reviewed_at"] = datetime.now(timezone.utc).isoformat()
        ok += 1
    path.write_text(json.dumps({"events": items}, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"approved": ok, "still_invalid": bad}


def main() -> None:
    parser = argparse.ArgumentParser(description="Gera acontecimentos a partir de um corpus histórico (saída pendente de revisão).")
    sub = parser.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("generate")
    g.add_argument("--corpus", type=Path, required=True)
    g.add_argument("--limit", type=int, default=20)
    g.add_argument("--local", action="store_true", help="não usar o Gemini")
    a = sub.add_parser("approve")
    a.add_argument("file", type=Path)
    args = parser.parse_args()
    if args.cmd == "generate":
        print(json.dumps(asyncio.run(generate(args.corpus, args.limit, not args.local)), ensure_ascii=False, indent=1))
    else:
        print(json.dumps(approve(args.file), ensure_ascii=False))


if __name__ == "__main__":
    main()
