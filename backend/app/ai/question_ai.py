"""Perguntas de entrevista geradas com apoio do Gemini (via gateway ou chave local), validadas pelo motor.

Entrada: fatos do jogo (texto com números) e temas em que o jogador foi mal (aprendizado). A saída só vale se cada
pergunta terminar em '?', tiver tamanho razoável e citar apenas números presentes nos fatos. Sem IA, devolve [].
"""
from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

import httpx

from . import gateway

logger = logging.getLogger("civiciclo.question_ai")
NUMBER = re.compile(r"\d+(?:[.,]\d+)?")
SYSTEM = ("Você escreve perguntas de jornalistas e mediadores para um simulador político, em português do Brasil. Use SOMENTE os fatos fornecidos "
          "(números e nomes). Cada pergunta tem no máximo 280 caracteres, termina com '?', é neutra e específica. Priorize os temas em que o jogador foi pior.")


def _numbers(text: str) -> set[str]:
    return {n.replace(",", ".") for n in NUMBER.findall(text)}


def validate(raw: Any, facts: list[dict[str, str]], count: int) -> list[dict[str, str]]:
    items = raw.get("questions") if isinstance(raw, dict) else None
    if not isinstance(items, list):
        return []
    allowed = _numbers(" ".join(f["text"] for f in facts))
    out = []
    for q in items:
        if not isinstance(q, dict) or not isinstance(q.get("prompt"), str) or not isinstance(q.get("topic"), str):
            continue
        prompt = q["prompt"].strip()
        if not (20 <= len(prompt) <= 300) or not prompt.endswith("?") or not _numbers(prompt) <= allowed:
            continue
        out.append({"topic": q["topic"].strip()[:40], "prompt": prompt})
        if len(out) >= count:
            break
    return out


async def generate(facts: list[dict[str, str]], weak_topics: list[str], kind: str, office: str, count: int = 2) -> dict[str, Any]:
    none = {"questions": [], "source": "local"}
    if not facts:
        return none
    payload = {"facts": facts[:8], "weak_topics": weak_topics[:5], "kind": kind, "office": office, "count": count}
    via_gateway = await gateway.post("/v1/questions", payload)
    if via_gateway:
        qs = validate(via_gateway, facts, count)
        return {"questions": qs, "source": "gemini"} if qs else none
    key = os.getenv("GEMINI_API_KEY", "").strip()
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
    if not key or gateway.configured() or not re.fullmatch(r"[A-Za-z0-9._-]{3,80}", model):
        return none
    schema = {"type": "OBJECT", "properties": {"questions": {"type": "ARRAY", "maxItems": count, "items": {"type": "OBJECT", "properties": {"topic": {"type": "STRING"}, "prompt": {"type": "STRING"}}, "required": ["topic", "prompt"]}}}, "required": ["questions"]}
    body = {"systemInstruction": {"parts": [{"text": SYSTEM}]},
            "contents": [{"role": "user", "parts": [{"text": json.dumps({"fatos": facts[:8], "temas_fracos": weak_topics[:5], "formato": kind, "quantidade": count}, ensure_ascii=False)}]}],
            "generationConfig": {"responseFormat": {"text": {"mimeType": "APPLICATION_JSON", "schema": schema}}, "thinkingConfig": {"thinkingLevel": "low"}, "maxOutputTokens": 700}}
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(connect=5, read=15, write=5, pool=5)) as client:
            response = await client.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent", headers={"x-goog-api-key": key}, json=body)
        if response.is_error:
            return none
        parts = (response.json().get("candidates") or [{}])[0].get("content", {}).get("parts", [])
        raw = next((p["text"] for p in parts if isinstance(p, dict) and isinstance(p.get("text"), str)), None)
        qs = validate(json.loads(raw), facts, count) if raw else []
        return {"questions": qs, "source": "gemini"} if qs else none
    except (httpx.HTTPError, ValueError, KeyError, TypeError, AttributeError):
        logger.warning("Geração de perguntas indisponível; usando as perguntas do motor.")
        return none
