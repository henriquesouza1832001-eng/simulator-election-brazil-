"""Por que mudou? As principais causas da variação de cada indicador nacional.

O motor já muda os números em vários lugares (decisões, reações, crises, economia). Este módulo só anota *quem* mudou *quanto*,
numa janela que vai do fim do último avanço do calendário até o fim do avanço atual, e entrega as 3 maiores causas de cada
indicador. O que não foi anotado vira "Tendência da economia e do período", calculado como a diferença entre a variação total e
o que foi explicado, então a soma sempre fecha. Não altera nenhum cálculo do jogo.
"""
from __future__ import annotations

import sys
from contextlib import contextmanager
from typing import Any, Iterator

TRACKED = {
    "approval": ("Aprovação", "pp", True), "inflation": ("Inflação", "pp", False), "gdp_growth": ("Crescimento do PIB", "pp", True),
    "unemployment": ("Desemprego", "pp", False), "congress_support": ("Base no Congresso", "pp", True), "institutional_trust": ("Confiança institucional", "pts", True),
}
MODULE_LABEL = {"consequences": "Reações às suas decisões", "cpi": "CPI e investigações", "regulators": "Reguladores", "interviews": "Entrevistas e declarações",
                "companies": "Empresas e estatais", "events": "Crises e acontecimentos", "macro": "Economia e mercado", "story": "Acontecimentos do dia"}
REMAINDER = "Tendência da economia e do período"
_label: list[str] = []


@contextmanager
def because(label: str) -> Iterator[None]:
    """Tudo que mudar dentro do bloco é atribuído a esta causa (por exemplo, o nome da decisão)."""
    _label.append(label)
    try:
        yield
    finally:
        _label.pop()


def _snapshot(state: dict[str, Any]) -> dict[str, float]:
    m = state.get("metrics", {})
    return {key: float(m.get(key, 0.0)) for key in TRACKED}


def _window(state: dict[str, Any]) -> dict[str, Any]:
    window = state.get("why_window")
    if not isinstance(window, dict) or "start" not in window:
        window = {"start": _snapshot(state), "items": []}
        state["why_window"] = window
    return window


def open_window(state: dict[str, Any]) -> None:
    """Garante que a janela exista antes de qualquer mudança do avanço (guarda os valores de partida)."""
    _window(state)


def note(state: dict[str, Any], metric: str, delta: float, label: str | None = None, *, depth: int = 2) -> None:
    """Anota uma variação já aplicada. Sem rótulo explícito, usa o bloco `because` ativo ou o módulo de quem chamou."""
    if metric not in TRACKED or not delta or abs(delta) < 1e-9:
        return
    if label is None:
        if _label:
            label = _label[-1]
        else:
            try:
                module = sys._getframe(depth).f_globals.get("__name__", "").rsplit(".", 1)[-1]
            except ValueError:
                module = ""
            label = MODULE_LABEL.get(module, "Outros efeitos do período")
    items = _window(state)["items"]
    items.append({"metric": metric, "label": label, "delta": round(float(delta), 4)})
    if len(items) > 400:
        del items[:100]


def close(state: dict[str, Any], before: str, after: str) -> dict[str, Any]:
    """Fecha a janela: calcula a variação total, as causas e abre a próxima janela. O resultado fica em `state['why']`."""
    window = _window(state)
    now = _snapshot(state)
    result: dict[str, Any] = {"from": before, "to": after, "metrics": {}}
    for key, (label, unit, good_up) in TRACKED.items():
        total = round(now[key] - float(window["start"].get(key, now[key])), 3)
        grouped: dict[str, float] = {}
        for item in window["items"]:
            if item["metric"] == key:
                grouped[item["label"]] = grouped.get(item["label"], 0.0) + item["delta"]
        explained = sum(grouped.values())
        rest = round(total - explained, 3)
        if abs(rest) >= 0.005:
            grouped[REMAINDER] = grouped.get(REMAINDER, 0.0) + rest
        causes = sorted(({"label": name, "delta": round(value, 2)} for name, value in grouped.items() if abs(value) >= 0.005), key=lambda c: -abs(c["delta"]))
        result["metrics"][key] = {"label": label, "unit": unit, "good_when_up": good_up, "total": round(total, 2), "value": round(now[key], 2), "causes": causes[:3]}
    state["why"] = result
    state["why_window"] = {"start": now, "items": []}
    return result
