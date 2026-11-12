"""Última camada de IA do mapeamento de ações: desempata candidatos e sugere perguntas. Gemini opcional.

Entrada limitada: o texto do jogador, os candidatos já calculados pelas regras locais (id e título) e exemplos que
o próprio jogador confirmou. A saída só vale se o id escolhido estiver entre os candidatos; perguntas passam por
filtro de tamanho. Qualquer falha devolve vazio e o jogo segue com as regras locais.
"""
from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

import httpx

from . import gateway

logger = logging.getLogger("civiciclo.mapper_ai")
MODEL_PATTERN = re.compile(r"^[A-Za-z0-9._-]{3,80}$")
DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
INSTRUCTIONS = (
    "Você ajuda um simulador político a entender o que o jogador quis fazer. Escolha no máximo UM id da lista de candidatos "
    "ou 'nenhum'. Se estiver em dúvida, sugira até duas perguntas curtas em português do Brasil que ajudem a decidir. "
    "Não crie ações novas, não cite números, não explique leis. Use os exemplos confirmados pelo jogador como pista."
)


def _schema(ids: list[str]) -> dict[str, Any]:
    return {"type": "OBJECT", "properties": {"choice": {"type": "STRING", "enum": ids + ["nenhum"]},
                                              "questions": {"type": "ARRAY", "items": {"type": "STRING"}, "maxItems": 2}},
            "required": ["choice", "questions"]}


def validate(raw: Any, ids: list[str]) -> dict[str, Any]:
    if not isinstance(raw, dict):
        return {"choice": None, "questions": []}
    choice = raw.get("choice")
    questions = [q.strip() for q in raw.get("questions", []) if isinstance(q, str) and 8 <= len(q.strip()) <= 160 and q.strip().endswith("?")][:2]
    return {"choice": choice if choice in ids else None, "questions": questions}


async def refine(text: str, candidates: list[dict[str, Any]], confirmed: list[dict[str, Any]]) -> dict[str, Any]:
    empty = {"choice": None, "questions": [], "source": "local"}
    key = os.getenv("GEMINI_API_KEY", "").strip()
    ids = [c["id"] for c in candidates]
    if ids and gateway.configured():
        via = await gateway.post("/v1/interpret-action", {"text": text[:400], "candidates": [{"id": c["id"], "title": c["title"]} for c in candidates[:8]],
                                                           "confirmed": [{"texto": e["text"][:120], "id": e["action_id"]} for e in confirmed[:3]]})
        out = validate(via, ids) if via else {"choice": None, "questions": []}
        return {**out, "source": "gemini"} if (out["choice"] or out["questions"]) else empty
    if not key or not ids:
        return empty
    model = os.getenv("GEMINI_MODEL", DEFAULT_MODEL).strip()
    if not MODEL_PATTERN.fullmatch(model):
        return empty
    prompt = {"texto_do_jogador": text[:400], "candidatos": [{"id": c["id"], "titulo": c["title"]} for c in candidates[:6]],
              "exemplos_confirmados": [{"texto": e["text"][:120], "id": e["action_id"]} for e in confirmed[:3]]}
    payload = {"systemInstruction": {"parts": [{"text": INSTRUCTIONS}]},
               "contents": [{"role": "user", "parts": [{"text": json.dumps(prompt, ensure_ascii=False)}]}],
               "generationConfig": {"responseFormat": {"text": {"mimeType": "APPLICATION_JSON", "schema": _schema(ids)}},
                                    "thinkingConfig": {"thinkingLevel": "low"}, "maxOutputTokens": 300}}
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(connect=5, read=12, write=5, pool=5)) as client:
            response = await client.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                                         headers={"x-goog-api-key": key}, json=payload)
        if response.is_error:
            return empty
        parts = (response.json().get("candidates") or [{}])[0].get("content", {}).get("parts", [])
        raw = next((p["text"] for p in parts if isinstance(p, dict) and isinstance(p.get("text"), str)), None)
        if not raw:
            return empty
        out = validate(json.loads(raw), ids)
        return {**out, "source": "gemini"}
    except (httpx.HTTPError, ValueError, KeyError, TypeError, AttributeError):
        logger.warning("Gemini indisponível no mapeamento de ações; usando regras locais.")
        return empty
