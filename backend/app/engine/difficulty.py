"""Difficulty profiles for the deterministic, fictional simulation."""
from __future__ import annotations

from typing import Any


DIFFICULTIES: dict[str, dict[str, Any]] = {
    "tranquilo": {
        "label": "Tranquilo",
        "description": "Menos crises, menor oscilação econômica e mais espaço para acordos.",
        "event_pressure": 0.65,
        "opposition_pressure": 0.60,
        "coalition_flexibility": 1.30,
        "economic_volatility": 0.65,
    },
    "normal": {
        "label": "Normal",
        "description": "Parâmetros intermediários para aprender os sistemas do jogo.",
        "event_pressure": 1.0,
        "opposition_pressure": 1.0,
        "coalition_flexibility": 1.0,
        "economic_volatility": 1.0,
    },
    "dificil": {
        "label": "Difícil",
        "description": "Mais crises e resistência política, com maior oscilação econômica.",
        "event_pressure": 1.2,
        "opposition_pressure": 1.25,
        "coalition_flexibility": 0.85,
        "economic_volatility": 1.15,
    },
    "complicado": {
        "label": "Complicado",
        "description": "Crises frequentes, coalizão menos flexível e oposição mais forte.",
        "event_pressure": 1.45,
        "opposition_pressure": 1.5,
        "coalition_flexibility": 0.7,
        "economic_volatility": 1.35,
    },
    "realismo_puro": {
        "label": "Realismo Puro",
        "description": "Economia mais volátil e crises frequentes; eventos continuam sendo regras fictícias do jogo.",
        "event_pressure": 1.35,
        "opposition_pressure": 1.25,
        "coalition_flexibility": 0.8,
        "economic_volatility": 1.65,
    },
}


def get_difficulty(key: str) -> dict[str, Any]:
    return DIFFICULTIES.get(key, DIFFICULTIES["normal"]).copy()


def adjust_coalition_probability(probability: float, flexibility: float, sensitivity: float = 0.15) -> float:
    """Move passage/confirmation odds with coalition flexibility, then clamp."""
    return max(0.03, min(0.97, probability + (flexibility - 1.0) * sensitivity))


def election_margin(base: float, swing: float, opposition_pressure: float) -> float:
    """Apply political headwind and scale the seeded election swing."""
    return base - (opposition_pressure - 1.0) * 4.0 + swing * opposition_pressure


def event_severity_weights(event_pressure: float) -> tuple[float, float, float]:
    """Make severe events more likely as pressure rises without changing the event set."""
    pressure = max(0.4, min(2.0, event_pressure))
    return 45.0 / pressure, 38.0, 17.0 * pressure
