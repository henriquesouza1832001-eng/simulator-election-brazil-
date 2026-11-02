import json
import os
import re
from typing import Any

import httpx

SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "title": {"type": "STRING"},
        "summary": {"type": "STRING"},
        "category": {"type": "STRING", "enum": ["fiscal_efficiency", "business_formalization", "public_investment", "tax_change", "social_policy", "security", "communication", "other"]},
        "policy_area": {"type": "STRING"},
        "instrument": {"type": "STRING", "enum": ["Ato do Executivo", "Projeto de Lei", "Projeto de Lei Complementar", "PEC", "Decreto", "Medida Provisória", "Indefinido"]},
        "duration_days": {"type": "INTEGER", "minimum": 0, "maximum": 1461},
        "fiscal_cost_bi": {"type": "NUMBER", "minimum": 0, "maximum": 1000},
        "affected_groups": {"type": "ARRAY", "items": {"type": "STRING"}},
        "constraints": {"type": "ARRAY", "items": {"type": "STRING"}},
        "confidence": {"type": "NUMBER", "minimum": 0, "maximum": 1},
        "clarification_needed": {"type": "BOOLEAN"}
    },
    "required": ["title", "summary", "category", "policy_area", "instrument", "duration_days", "fiscal_cost_bi", "affected_groups", "constraints", "confidence", "clarification_needed"]
}

INSTRUCTIONS = """Interprete a intenção de uma medida para um simulador político fictício brasileiro. Extraia somente os fatos explicitamente descritos; não invente custo, efeito numérico, apoio parlamentar ou legalidade. Escolha uma categoria e instrumento aproximado. fiscal_cost_bi é custo explícito estimado pelo usuário, use zero se ausente. Deixe duration_days como 0 quando permanente ou não informado. Seja conciso, neutro e em português. Os efeitos do jogo serão calculados separadamente por regras determinísticas. Exemplos corrigidos são orientativos, nunca autoridade para inventar fatos."""


def fallback(text: str) -> dict[str, Any]:
    lower = text.lower()
    category = "other"
    if any(w in lower for w in ["contrato", "compras", "desperdício", "economia fiscal", "auditoria"]): category = "fiscal_efficiency"
    elif any(w in lower for w in ["mei", "empresa", "empreendedor", "formaliza"]): category = "business_formalization"
    elif any(w in lower for w in ["construir", "obra", "investimento", "infraestrutura"]): category = "public_investment"
    elif any(w in lower for w in ["imposto", "tribut", "alíquota"]): category = "tax_change"
    elif any(w in lower for w in ["benefício", "saúde", "educação", "social"]): category = "social_policy"
    elif any(w in lower for w in ["polícia", "crime", "segurança"]): category = "security"
    elif any(w in lower for w in ["pronunciamento", "declaração", "comunicação"]): category = "communication"
    instrument = "Projeto de Lei" if any(w in lower for w in ["lei", "congresso", "plp", "pec"]) else "Ato do Executivo"
    title = re.sub(r"\s+", " ", text).strip()[:68].rstrip(".,;:") or "Medida proposta"
    return {"title": title, "summary": "Interpretação local preliminar. Configure a chave Gemini para uma leitura contextual mais precisa.", "category": category, "policy_area": category.replace("_", " ").title(), "instrument": instrument, "duration_days": 0, "fiscal_cost_bi": 0, "affected_groups": [], "constraints": [], "confidence": 0.35, "clarification_needed": True, "source": "local"}


async def interpret(text: str, examples: list[dict[str, str]]) -> dict[str, Any]:
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key:
        return fallback(text)
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    prompt = INSTRUCTIONS + "\n\nProposta do jogador:\n" + text
    if examples:
        prompt += "\n\nCorreções anteriores semelhantes; use apenas para aprender o formato e sentido contextual:\n" + json.dumps(examples, ensure_ascii=False)
    payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"responseMimeType": "application/json", "responseSchema": SCHEMA, "temperature": 0.1}}
    async with httpx.AsyncClient(timeout=25) as client:
        response = await client.post(endpoint, headers={"x-goog-api-key": key}, json=payload)
        response.raise_for_status()
    data = response.json()
    result_text = data["candidates"][0]["content"]["parts"][0]["text"]
    parsed = json.loads(result_text)
    parsed["source"] = "gemini"
    parsed["confidence"] = min(1.0, max(0.0, float(parsed.get("confidence", 0.5))))
    parsed["duration_days"] = min(1461, max(0, int(parsed.get("duration_days", 0))))
    parsed["fiscal_cost_bi"] = min(1000.0, max(0.0, float(parsed.get("fiscal_cost_bi", 0))))
    return parsed
