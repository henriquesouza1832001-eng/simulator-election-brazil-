"""Difficulty profiles scale the same underlying simulation rules."""

DIFFICULTIES = {
    "tranquilo": {"label": "Tranquilo", "event_pressure": 0.65, "opposition_pressure": 0.60, "coalition_flexibility": 1.30, "economic_volatility": 0.65, "forecast_help": True},
    "normal": {"label": "Normal", "event_pressure": 1.00, "opposition_pressure": 1.00, "coalition_flexibility": 1.00, "economic_volatility": 1.00, "forecast_help": True},
    "dificil": {"label": "Difícil", "event_pressure": 1.20, "opposition_pressure": 1.25, "coalition_flexibility": 0.85, "economic_volatility": 1.15, "forecast_help": True},
    "complicado": {"label": "Complicado", "event_pressure": 1.45, "opposition_pressure": 1.50, "coalition_flexibility": 0.70, "economic_volatility": 1.35, "forecast_help": False},
    "realismo_puro": {"label": "Realismo Puro", "event_pressure": 1.0, "opposition_pressure": 1.0, "coalition_flexibility": 1.0, "economic_volatility": 1.0, "forecast_help": False, "empirical_events": True},
}


def get_difficulty(key: str) -> dict:
    return DIFFICULTIES.get(key, DIFFICULTIES["normal"]).copy()
