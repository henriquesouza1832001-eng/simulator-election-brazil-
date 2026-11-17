"""Leitura de discurso de campanha pelo Gemini (modelo mínimo), com leitura local de reserva.

O Gemini só diz o que está escrito: temas, promessas (e se têm meta, prazo e fonte de recurso), tom, ataques e risco legal.
Quem converte isso em votos e nota é o motor (engine/speech_score.py). Se a chave não existir, o recurso "interpretar" estiver
desligado ou a chamada falhar, o jogo usa a leitura local por palavras-chave e segue sem erro.
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any

import httpx

from . import gateway

logger = logging.getLogger("civiciclo.speech")
INSTRUCTIONS = (
    "Você lê discursos de campanha para um simulador político fictício do Brasil. Extraia SOMENTE o que está escrito; não invente promessas, números nem alvos. "
    "Para cada promessa diga se tem meta numérica (measurable), prazo (has_deadline) e fonte de recurso (funding_stated), se está dentro das competências do "
    "cargo informado (within_competence) e se é realista para o território (realistic). Classifique o tom e os ataques (personal=true só para ofensa a pessoa, não "
    "crítica a proposta). Indique risco legal apenas se o texto claramente o contiver. Responda só com JSON válido no formato pedido, em português."
)


def _schema(issue_ids: list[str], group_ids: list[str], tones: list[str], legal: list[str], targets: list[str]) -> dict[str, Any]:
    return {"type": "object", "properties": {
        "summary": {"type": "string"},
        "themes": {"type": "array", "items": {"type": "string", "enum": issue_ids}, "maxItems": 4},
        "target_groups": {"type": "array", "items": {"type": "string", "enum": group_ids}, "maxItems": 4},
        "tone": {"type": "string", "enum": tones},
        "promises": {"type": "array", "maxItems": 4, "items": {"type": "object", "properties": {
            "text": {"type": "string"}, "measurable": {"type": "boolean"}, "has_deadline": {"type": "boolean"}, "funding_stated": {"type": "boolean"},
            "within_competence": {"type": "boolean"}, "realistic": {"type": "boolean"}},
            "required": ["text", "measurable", "has_deadline", "funding_stated", "within_competence", "realistic"]}},
        "attacks": {"type": "array", "maxItems": 3, "items": {"type": "object", "properties": {"target": {"type": "string", "enum": targets}, "personal": {"type": "boolean"}},
                                                      "required": ["target", "personal"]}},
        "legal_risk": {"type": "string", "enum": legal},
        "clarity": {"type": "number"}, "local_connection": {"type": "number"}},
        "required": ["summary", "themes", "tone", "promises", "attacks", "legal_risk", "clarity", "local_connection"]}


def _competences(office: str) -> str:
    try:
        from ..engine.powers_catalog import ROLES
        role = ROLES.get(office) or {}
        return f"Pode: {'; '.join(role.get('pode', [])[:8])}. Não pode: {'; '.join(role.get('nao_pode', [])[:6])}."
    except Exception:  # noqa: BLE001
        return ""


async def read(text: str, issue: str, career: dict[str, Any], issues: dict[str, Any], rivals: list[dict[str, Any]]) -> dict[str, Any]:
    from ..engine import speech_score

    rival_ids = [r["id"] for r in rivals]
    local = speech_score.local_reading(text, issue, career, issues)
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key or not gateway.enabled("interpretar"):
        return local
    model = os.getenv("GEMINI_MODEL", gateway.DEFAULT_MODEL).strip()
    groups = sorted({g for data in issues.values() for g in data.get("groups", [])})
    context = {"cargo": career.get("office_label") or career.get("office"), "territorio": career.get("municipality") or career.get("state_name") or "Brasil",
               "tema_escolhido": issue, "competencias": _competences(str(career.get("office"))),
               "rivais": [{"id": r["id"], "partido": r["party"], "foco": r["issue_focus"]} for r in rivals]}
    payload = {"systemInstruction": {"parts": [{"text": INSTRUCTIONS}]},
               "contents": [{"role": "user", "parts": [{"text": "Contexto (JSON):\n" + json.dumps(context, ensure_ascii=False) + "\n\nDiscurso do jogador:\n" + text[:600]}]}],
               "generationConfig": {"responseFormat": {"text": {"mimeType": "APPLICATION_JSON", "schema": _schema(
                   sorted(issues), groups, speech_score.TONES, speech_score.LEGAL, rival_ids + ["adversario", "governo", "imprensa", "instituicoes", "ninguem"])}},
                   "thinkingConfig": {"thinkingLevel": "low"}, "maxOutputTokens": 900}}
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(connect=5, read=15, write=5, pool=5)) as client:
            response = await client.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent", headers={"x-goog-api-key": key}, json=payload)
        if response.is_error:
            logger.warning("Gemini HTTP %s na leitura de discurso; usando leitura local.", response.status_code)
            return local
        parts = (response.json().get("candidates") or [{}])[0].get("content", {}).get("parts", [])
        raw = next((p["text"] for p in parts if isinstance(p, dict) and isinstance(p.get("text"), str)), None)
        if not raw:
            return local
        return speech_score.normalize(json.loads(raw), text, issue, issues, rival_ids)
    except (httpx.HTTPError, ValueError, KeyError, TypeError, AttributeError):
        logger.warning("Leitura de discurso pelo Gemini falhou; usando leitura local.")
        return local
