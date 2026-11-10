"""Debates e sabatinas da campanha semanal.

Três escolhas observadas na referência: participar ("sentar na bancada": a nota vira momentum),
recusar (−1 de momentum e +1 ação de rua) ou assistir de casa (nota fixa 45, sem risco).
A nota da fala usa a rubrica já existente da campanha; o resto é design próprio e ajustável.
"""
from __future__ import annotations

from typing import Any

from .campaign import ISSUES, _speech_score, ensure_campaign_state
from .campaign_week import LOW_ENERGY_DEBATE_PENALTY, LOW_ENERGY_THRESHOLD, ensure_week_state

CHOICES = {"participar", "recusar", "casa"}
FIXED_HOME_SCORE = 45
MOMENTUM_BY_SCORE = 0.08  # momentum por ponto acima/abaixo de 55 (design próprio)
MOMENTUM_REFUSAL = -1.0


def debate_calendar_weeks() -> set[int]:
    """Semanas com debate (design próprio, inspirado em debates nas semanas 5 e 7 observados)."""
    return {5, 7, 10, 12}


def overview(state: dict[str, Any]) -> dict[str, Any]:
    week = ensure_week_state(state)
    n = week["week"]
    done = week.setdefault("debates_done", [])
    scheduled = n in debate_calendar_weeks() and n not in done
    return {"simulated": True, "week": n, "scheduled": scheduled, "done_weeks": done,
            "choices": [
                {"key": "participar", "label": "Sentar na bancada", "text": "A nota da sua fala vira momentum. Energia baixa tira pontos."},
                {"key": "recusar", "label": "Recusar", "text": "Custa 1 de momentum e libera uma ação de rua extra nesta semana."},
                {"key": "casa", "label": "Assistir de casa", "text": f"Nota {FIXED_HOME_SCORE} fixa, sem risco."}],
            "issues": [{"key": k, "label": v["label"]} for k, v in ISSUES.items()]}


def attend(state: dict[str, Any], choice: str, issue: str = "", message: str = "") -> dict[str, Any]:
    if choice not in CHOICES:
        raise ValueError("Escolha inválida.")
    campaign = ensure_campaign_state(state)
    week = ensure_week_state(state)
    n = week["week"]
    if n not in debate_calendar_weeks() or n in week.setdefault("debates_done", []):
        raise ValueError("Não há debate pendente nesta semana.")
    result: dict[str, Any] = {"choice": choice, "week": n}
    if choice == "recusar":
        campaign["momentum"] = round(max(-10, min(10, campaign["momentum"] + MOMENTUM_REFUSAL)), 2)
        week["bonus_actions"] = week.get("bonus_actions", 0) + 1
        result.update(score=None, momentum_delta=MOMENTUM_REFUSAL, bonus_action=True)
    elif choice == "casa":
        score = FIXED_HOME_SCORE
        delta = round((score - 55) * MOMENTUM_BY_SCORE, 2)
        campaign["momentum"] = round(max(-10, min(10, campaign["momentum"] + delta)), 2)
        result.update(score=score, momentum_delta=delta, bonus_action=False)
    else:
        if issue not in ISSUES:
            raise ValueError("Escolha o tema da sua fala.")
        if len(message.strip()) < 40:
            raise ValueError("Escreva ao menos 40 caracteres para a sua resposta no debate.")
        score, rubric = _speech_score(issue, message)
        penalty = LOW_ENERGY_DEBATE_PENALTY if week["energy"] < LOW_ENERGY_THRESHOLD else 0
        score = max(0, score - penalty)
        delta = round((score - 55) * MOMENTUM_BY_SCORE, 2)
        campaign["momentum"] = round(max(-10, min(10, campaign["momentum"] + delta)), 2)
        result.update(score=score, rubric=rubric, momentum_delta=delta, low_energy_penalty=penalty, bonus_action=False)
    week["debates_done"].append(n)
    result["momentum"] = campaign["momentum"]
    return result
