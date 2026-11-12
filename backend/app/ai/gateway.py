"""Cliente do gateway do Gemini na Cloudflare (cloudflare/gemini-gateway). Opcional.

Com GEMINI_GATEWAY_URL e GEMINI_GATEWAY_TOKEN definidos, o backend não fala com o Google: pede ao gateway,
onde fica a chave. Qualquer falha devolve None e o jogo segue com as regras locais.
"""
from __future__ import annotations

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger("civiciclo.gateway")


def configured() -> bool:
    return bool(os.getenv("GEMINI_GATEWAY_URL", "").strip() and os.getenv("GEMINI_GATEWAY_TOKEN", "").strip())


async def post(path: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    if not configured():
        return None
    base = os.getenv("GEMINI_GATEWAY_URL", "").strip().rstrip("/")
    if not base.startswith("https://"):
        logger.warning("GEMINI_GATEWAY_URL precisa ser https; ignorando o gateway.")
        return None
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(connect=5, read=15, write=5, pool=5)) as client:
            response = await client.post(base + path, json=payload, headers={"Authorization": f"Bearer {os.getenv('GEMINI_GATEWAY_TOKEN', '').strip()}"})
        if response.is_error:
            return None
        data = response.json()
        return data if isinstance(data, dict) and data.get("source") == "gemini" else None
    except (httpx.HTTPError, ValueError):
        logger.warning("Gateway do Gemini indisponível; usando regras locais.")
        return None
