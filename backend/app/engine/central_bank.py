"""Banco Central e Copom: a Selic é decidida a cada 45 dias por uma regra, e o governo só influencia pela estrutura.

O motor decide: o Copom compara a inflação com a meta, calcula a taxa que buscaria sem pressão e anda no máximo
0,5 ponto por reunião (1,0 se o desvio for grande). Quanto menos autônomo o Banco Central, mais ele puxa a taxa para
o que o governo quer (juros menores), com ganho curto de atividade e custo em inflação e credibilidade.
Pesos e escalas são escolhas de design; o jogador age pela autonomia, pelos diretores e por declarações (Competências).
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from . import ledger

MEETING_DAYS = 45
NEUTRAL_REAL = 4.5
INFLATION_TARGET = 3.0
AUTONOMY_WEIGHT = {"autonomo_constitucional": 1.0, "autonomo_lei": 0.85, "subordinado": 0.25}
AUTONOMY_LABEL = {"autonomo_constitucional": "autonomia na Constituição", "autonomo_lei": "autonomia por lei complementar", "subordinado": "subordinado ao governo"}
PRESSURE_TITLE = "Criticar publicamente os juros"
PRESSURE_WINDOW_DAYS = 120


def _is_presidency(state: dict[str, Any]) -> bool:
    career = state.get("career") or {}
    return not career.get("mode") or career.get("office") == "presidente"


def ensure(state: dict[str, Any]) -> dict[str, Any]:
    copom = state.setdefault("copom", {})
    if "selic" not in copom:
        nation = (state.get("nation") or {}).get("values") or {}
        start = date.fromisoformat(state["date"])
        copom.update({"selic": round(float(nation.get("juros", 10.5)), 2), "next_meeting": (start + timedelta(days=MEETING_DAYS)).isoformat(),
                      "credibility": 70.0, "history": []})
    return copom


def _structure(state: dict[str, Any]) -> str:
    from .powers import structure
    return str(structure(state).get("central_bank", "autonomo_lei"))


def pressure_count(state: dict[str, Any], today: date) -> int:
    count = 0
    for entry in state.get("ledger", []):
        if entry.get("source") == "presidencia" and str(entry.get("title", "")).startswith(PRESSURE_TITLE):
            try:
                if 0 <= (today - date.fromisoformat(entry["date"])).days <= PRESSURE_WINDOW_DAYS:
                    count += 1
            except (TypeError, ValueError):
                continue
    return count


def desired_rate(state: dict[str, Any]) -> float:
    inflation = float(state.get("metrics", {}).get("inflation", 4.5))
    return round(max(2.0, min(20.0, inflation + NEUTRAL_REAL + 0.5 * (inflation - INFLATION_TARGET))), 2)


def _target(state: dict[str, Any], selic: float, today: date) -> tuple[float, float]:
    base = AUTONOMY_WEIGHT.get(_structure(state), 0.85)
    weight = max(0.1, base - min(4, pressure_count(state, today)) * 0.05)
    desired = desired_rate(state)
    wish = max(2.0, selic - 1.0)
    return weight * desired + (1 - weight) * wish, weight


def _step(diff: float) -> float:
    if abs(diff) < 0.25:
        return 0.0
    size = 1.0 if abs(diff) >= 2.0 else 0.5
    move = min(size, round(abs(diff) / 0.25) * 0.25)
    return move if diff > 0 else -move


def _apply(state: dict[str, Any], delta: float, below_desired: float) -> None:
    from .fiscal import record_policy_balance_delta
    from .powers import _bump
    copom = ensure(state)
    if delta:
        _bump(state, "gdp_growth", -0.04 * delta)
        _bump(state, "unemployment", 0.02 * delta)
        _bump(state, "inflation", -0.06 * delta)
        record_policy_balance_delta(state, -0.02 * delta)
    if below_desired > 1.5:
        copom["credibility"] = round(max(0.0, copom["credibility"] - 3.0), 2)
        _bump(state, "inflation", 0.05)
    elif below_desired < 0.5:
        copom["credibility"] = round(min(100.0, copom["credibility"] + 1.0), 2)


def meet(state: dict[str, Any], day: date) -> dict[str, Any]:
    copom = ensure(state)
    before = float(copom["selic"])
    target, weight = _target(state, before, day)
    delta = _step(target - before)
    after = round(max(2.0, min(20.0, before + delta)), 2)
    copom["selic"] = after
    below = desired_rate(state) - after
    _apply(state, after - before, below)
    verb = "elevou" if after > before else "reduziu" if after < before else "manteve"
    text = f"Copom {verb} a Selic" + (f" de {before:.2f}% para {after:.2f}% a.a." if after != before else f" em {after:.2f}% a.a.")
    entry = {"date": day.isoformat(), "from": before, "to": after, "desired": desired_rate(state), "autonomy_weight": round(weight, 2), "text": text}
    copom["history"].insert(0, entry)
    del copom["history"][12:]
    ledger.record(state, "copom", text, {}, {"juros": round(after - before, 2)}, status="decidido")
    return entry


def tick(state: dict[str, Any], before: date, after: date) -> list[str]:
    if not _is_presidency(state):
        return []
    copom = ensure(state)
    messages: list[str] = []
    guard = 0
    while date.fromisoformat(copom["next_meeting"]) <= after and guard < 12:
        day = date.fromisoformat(copom["next_meeting"])
        messages.append(meet(state, day)["text"] + ".")
        copom["next_meeting"] = (day + timedelta(days=MEETING_DAYS)).isoformat()
        guard += 1
    nation = (state.get("nation") or {}).get("values")
    if nation is not None:
        nation["juros"] = round(float(copom["selic"]), 4)
    return messages


def overview(state: dict[str, Any]) -> dict[str, Any]:
    copom = ensure(state)
    today = date.fromisoformat(state["date"])
    structure = _structure(state)
    pressure = pressure_count(state, today)
    return {
        "selic": copom["selic"], "desired": desired_rate(state), "next_meeting": copom["next_meeting"],
        "days_to_meeting": max(0, (date.fromisoformat(copom["next_meeting"]) - today).days),
        "credibility": copom["credibility"], "autonomy": structure, "autonomy_label": AUTONOMY_LABEL.get(structure, structure),
        "autonomy_weight": AUTONOMY_WEIGHT.get(structure, 0.85), "pressure": pressure, "history": copom["history"], "target": INFLATION_TARGET,
        "inflation": float(state.get("metrics", {}).get("inflation", 0.0)),
        "note": "Quem decide a Selic é o Copom. O governo influencia pela autonomia do Banco Central, pelos diretores indicados e por declarações; quanto menor a autonomia, mais o Copom corta juros, com custo em inflação e credibilidade.",
        "applies": _is_presidency(state),
    }
