"""Livro-razão de decisões: previsão e resultado lado a lado, com a diferença explicada.

Toda ação de competência (Presidência, cargos locais e legislativos) e toda obra do território registram aqui:
o que foi prometido antes de confirmar, o que de fato aconteceu e, se houver diferença, por quê.
"""
from __future__ import annotations

from typing import Any

LIMIT = 200


def _book(state: dict[str, Any]) -> list[dict[str, Any]]:
    return state.setdefault("ledger", [])


def record(state: dict[str, Any], source: str, title: str, forecast: dict[str, float], result: dict[str, float] | None = None, *,
           status: str = "feito", cost: str | None = None, reason: str | None = None) -> dict[str, Any]:
    book = _book(state)
    entry = {"id": f"led-{len(book) + 1}-{state.get('date')}", "date": state.get("date"), "source": source, "title": title, "forecast": forecast,
             "result": result, "status": status, "cost": cost, "reason": reason, "narrative": None}
    book.insert(0, entry)
    del book[LIMIT:]
    return entry


def settle(state: dict[str, Any], entry_id: str, result: dict[str, float], status: str = "concluído", reason: str | None = None) -> None:
    for entry in _book(state):
        if entry["id"] == entry_id:
            entry["result"], entry["status"], entry["reason"] = result, status, reason
            entry["gap"] = gap(entry["forecast"], result)
            return


def gap(forecast: dict[str, float], result: dict[str, float] | None) -> dict[str, float]:
    if result is None:
        return {}
    keys = set(forecast) | set(result)
    return {k: round(float(result.get(k, 0)) - float(forecast.get(k, 0)), 4) for k in keys if abs(float(result.get(k, 0)) - float(forecast.get(k, 0))) > 1e-9}


def explain_gap(forecast: dict[str, float], result: dict[str, float] | None, approved: bool | None = None) -> str | None:
    if result is None:
        return None
    if approved is False:
        return "A proposta foi rejeitada na votação; nenhum efeito previsto foi aplicado."
    difference = gap(forecast, result)
    if not difference:
        return "O resultado coincidiu com a previsão."
    return "Diferença entre previsto e realizado: " + ", ".join(f"{k} {v:+g}" for k, v in sorted(difference.items())) + "."


def overview(state: dict[str, Any], limit: int = 40) -> list[dict[str, Any]]:
    return _book(state)[:limit]
