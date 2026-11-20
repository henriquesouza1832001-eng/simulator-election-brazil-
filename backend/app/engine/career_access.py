"""Acesso à campanha do jogador, nota do discurso e checagem de mandato em exercício.

Parte do ciclo de carreira (antes tudo em career.py; ver career.py, que reexporta estes nomes).
"""
from __future__ import annotations


import re
from datetime import date
from typing import Any

from .career_base import (
    ISSUES,
    OFFICES,
    STATE_CAPITALS,
    _norm,
    _term_end_date,
)


def _campaign(state: dict[str, Any]) -> dict[str, Any]:
    career = state.get("career") or {}
    if not career.get("mode"):
        raise ValueError("Esta partida ainda não iniciou uma carreira política.")
    return career


def _campaign_team_location_id(career: dict[str, Any]) -> str | None:
    current = career.get("campaign_team_municipality_id")
    if current:
        return str(current)
    if career.get("scope") == "municipal":
        return career.get("municipality_id")
    return STATE_CAPITALS.get(career.get("state_code", ""))


def is_career_governing(career: dict[str, Any], today: date) -> bool:
    """Whether this character still holds the elected office on this date."""
    phase = career.get("phase")
    office_start = career.get("office_start")
    if phase not in {"office", "campaign", "runoff_campaign", "runoff_observer", "outgoing", "transition"}:
        return False
    if phase != "office" and not office_start:
        return False
    term_end = career.get("term_end")
    if not term_end:
        if not office_start:
            return phase == "office"
        role = OFFICES.get(career.get("office"), {})
        term_years = int(career.get("term_years") or role.get("term_years", 4))
        term_end = _term_end_date(career["office"], date.fromisoformat(office_start), term_years).isoformat()
    return today <= date.fromisoformat(term_end)


def _speech_score(issue: str, message: str) -> tuple[int, dict[str, int]]:
    normalized = _norm(message)
    words = re.findall(r"[\w'-]+", normalized)
    topic = ISSUES[issue]["terms"]
    relevance = min(25, sum(1 for term in topic if _norm(term) in normalized) * 5)
    concrete_terms = {"prazo", "meta", "publicar", "fiscalizar", "auditoria", "orçamento", "orcamento", "equipe", "plano", "entregar", "medir", "acompanhar", "reduzir", "ampliar", "bairro", "escola", "posto"}
    concrete = min(20, sum(1 for term in concrete_terms if _norm(term) in normalized) * 4)
    empathy_terms = {"família", "familia", "morador", "trabalhador", "aluno", "paciente", "bairro", "comunidade", "escutar", "ouvir", "respeito", "cuidado", "medo", "ônibus", "onibus"}
    empathy = min(15, sum(1 for term in empathy_terms if _norm(term) in normalized) * 3)
    length = 10 if 18 <= len(words) <= 90 else 4 if 10 <= len(words) <= 120 else -5
    exaggeration = 12 if any(p in normalized for p in ("resolver tudo", "nunca mais", "sem custo", "acabar com todo")) else 0
    attacks = 12 if any(p in normalized for p in ("lixo", "vagabundo", "traidor", "inimigo do povo")) else 0
    score = max(0, min(100, 40 + relevance + concrete + empathy + length - exaggeration - attacks))
    return score, {"pertinência do tema": relevance, "proposta verificável": concrete, "conexão local": empathy, "clareza": length, "promessa exagerada": -exaggeration, "ataque pessoal": -attacks}
