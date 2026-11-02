"""Public addresses and other presidential communication actions.

Public-facing speech scores are deterministic game rules. Text is never used
to change institutional powers or bypass the game's legal constraints.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any


def ensure_communications_state(state: dict[str, Any]) -> dict[str, Any]:
    communications = state.setdefault("communications", {})
    # Old saves are not forced to deliver a ceremonial speech retroactively.
    communications.setdefault("inauguration", {
        "required": False, "delivered": True, "legacy_save": True,
        "date": None, "text": "", "score": None, "rubric": {},
    })
    return communications


def _normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text.casefold())
    return "".join(char for char in decomposed if unicodedata.category(char) != "Mn")


def submit_inaugural_address(state: dict[str, Any], text: str) -> dict[str, Any]:
    communications = ensure_communications_state(state)
    address = communications["inauguration"]
    if not address.get("required") or address.get("delivered"):
        raise ValueError("Não há pronunciamento de posse pendente nesta etapa.")
    clean = " ".join(text.split())
    if len(clean) < 80:
        raise ValueError("Escreva ao menos 80 caracteres para o pronunciamento de posse.")

    normalized = _normalize(clean)
    words = re.findall(r"[\w'-]+", normalized)
    rubric = {
        "fala ao país": 2 if any(term in normalized for term in ("brasil", "povo", "pais", "brasileir")) else 0,
        "compromisso verificável": 2 if any(term in normalized for term in ("meta", "prazo", "publicar", "prestar contas", "acompanhar")) else 0,
        "vida cotidiana": 2 if any(term in normalized for term in ("trabalho", "familia", "escola", "saude", "bairro", "renda")) else 0,
        "instituições e direitos": 2 if any(term in normalized for term in ("constituicao", "lei", "congresso", "direito", "instituicao")) else 0,
        "clareza": 2 if 35 <= len(words) <= 180 else 1 if 20 <= len(words) <= 240 else 0,
        "tom de responsabilidade": 2 if any(term in normalized for term in ("responsabilidade", "transparencia", "dialogo", "respeito", "trabalhar")) else 0,
    }
    score = sum(rubric.values())
    metrics = state.setdefault("metrics", {})
    trust_delta = round((score - 6) * 0.22, 1)
    approval_delta = round((score - 6) * 0.12, 1)
    metrics["institutional_trust"] = round(max(0, min(100, float(metrics.get("institutional_trust", 50)) + trust_delta)), 1)
    metrics["approval"] = round(max(0, min(100, float(metrics.get("approval", 50)) + approval_delta)), 1)
    institutions = state.setdefault("institutions", {})
    institutions["civilian_legitimacy"] = round(max(0, min(100, float(institutions.get("civilian_legitimacy", 50)) + trust_delta)), 1)

    address.update({"required": False, "delivered": True, "legacy_save": False,
                    "date": state["date"], "text": clean, "score": score, "rubric": rubric,
                    "effects": {"institutional_trust": trust_delta, "approval": approval_delta,
                                "civilian_legitimacy": trust_delta}})
    state.setdefault("simulated_news", []).insert(0, {
        "id": f"inaugural-address-{state['date']}", "date": state["date"],
        "title": "Pronunciamento de posse", "region": "Nacional",
        "description": f"O novo governo fez seu primeiro pronunciamento. Avaliação simulada: {score}/12.",
        "simulated": True,
    })
    state["simulated_news"] = state["simulated_news"][:20]
    return {"score": score, "rubric": rubric, "effects": address["effects"],
            "message": f"Pronunciamento registrado. Nota {score}/12; confiança institucional {trust_delta:+.1f} e aprovação {approval_delta:+.1f} p.p. simuladas."}


def require_inaugural_address(state: dict[str, Any]) -> bool:
    inauguration = ensure_communications_state(state)["inauguration"]
    return bool(inauguration.get("required") and not inauguration.get("delivered"))
