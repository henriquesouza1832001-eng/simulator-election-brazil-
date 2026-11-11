"""Narrador: transforma fatos já decididos pelo motor em texto. A IA nunca decide números nem inventa nomes.

Modo local (padrão): texto determinístico por modelo. Com GEMINI_API_KEY no servidor, o Gemini reescreve os mesmos
fatos; a saída só é aceita se todos os números e nomes próprios do texto já constarem nos fatos. Caso contrário, volta ao local.
"""
from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

import httpx

logger = logging.getLogger("civiciclo.narrator")
MODEL_PATTERN = re.compile(r"^[A-Za-z0-9._-]{3,80}$")
DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
INSTRUCTIONS = (
    "Você escreve notícias curtas e neutras em português do Brasil para um simulador político. "
    "Use SOMENTE os fatos fornecidos. Não invente números, nomes, datas, citações ou causas. "
    "Escreva de 2 a 4 frases. Diga o que foi decidido, o que o motor previu, o que aconteceu e o que muda. "
    "Deixe claro que se trata de simulação."
)
LABELS = {"trust": "confiança", "reputation": "reputação", "mobilidade": "mobilidade", "seguranca": "segurança", "saude_atencao": "saúde",
          "approval": "aprovação", "gdp_growth": "PIB", "inflation": "inflação", "institutional_trust": "confiança institucional"}


def _effects(effects: dict[str, float] | None) -> str:
    if not effects:
        return "nenhum efeito registrado"
    return ", ".join(f"{LABELS.get(k, k.replace('_', ' '))} {v:+g}" for k, v in effects.items())


def local(facts: dict[str, Any]) -> str:
    title, status = facts.get("title", "A decisão"), facts.get("status", "feito")
    forecast, result = facts.get("forecast"), facts.get("result")
    text = f"Na simulação, {title.lower() if title[:1].isupper() else title}"
    if status == "em andamento":
        text += f" está em andamento. O motor previu: {_effects(forecast)}. Os resultados aparecem quando terminar."
    elif facts.get("reason"):
        text += f". {facts['reason']} Previsto: {_effects(forecast)}. Realizado: {_effects(result)}."
    else:
        text += f". Previsto: {_effects(forecast)}. Realizado: {_effects(result)}."
    if facts.get("cost"):
        text += f" Custo: {facts['cost']}."
    return text


def _numbers(text: str) -> set[str]:
    return set(re.findall(r"\d+(?:[.,]\d+)?", text))


def _acceptable(output: str, facts: dict[str, Any]) -> bool:
    source = json.dumps(facts, ensure_ascii=False)
    if not _numbers(output) <= _numbers(source) | {"2", "3", "4"}:
        return False
    names = set(re.findall(r"\b[A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+\b", output))
    allowed = set(re.findall(r"\b[A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+\b", source)) | {"Na", "Simulação", "O", "A", "Os", "As", "Em", "Isso", "Com", "Mas", "Por", "Não", "Se", "Esse", "Essa", "No", "Uma", "Um"}
    return names <= allowed and 40 <= len(output) <= 700


async def narrate(facts: dict[str, Any]) -> dict[str, str]:
    key = os.getenv("GEMINI_API_KEY", "").strip()
    fallback = {"text": local(facts), "source": "local"}
    if not key:
        return fallback
    model = os.getenv("GEMINI_MODEL", DEFAULT_MODEL).strip()
    if not MODEL_PATTERN.fullmatch(model):
        return fallback
    payload = {"systemInstruction": {"parts": [{"text": INSTRUCTIONS}]},
               "contents": [{"role": "user", "parts": [{"text": "Fatos do motor (JSON):\n" + json.dumps(facts, ensure_ascii=False)}]}],
               "generationConfig": {"maxOutputTokens": 400, "thinkingConfig": {"thinkingLevel": "low"}}}
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(connect=5, read=15, write=5, pool=5)) as client:
            response = await client.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                                         headers={"x-goog-api-key": key}, json=payload)
        if response.is_error:
            return fallback
        parts = (response.json().get("candidates") or [{}])[0].get("content", {}).get("parts", [])
        text = next((p["text"] for p in parts if isinstance(p, dict) and isinstance(p.get("text"), str)), "").strip()
        if text and _acceptable(text, facts):
            return {"text": text, "source": "gemini"}
        logger.warning("Narração do Gemini descartada por conter fatos fora do motor.")
    except (httpx.HTTPError, ValueError, KeyError, TypeError, AttributeError):
        logger.warning("Narrador Gemini indisponível; usando texto local.")
    return fallback
