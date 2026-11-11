"""Motor de indicadores: liga o painel nacional ao registro e espalha efeitos a cada avanço de tempo.

A cada passagem de tempo, mede-se quanto as métricas centrais (PIB, inflação, desemprego, dívida, resultado
primário, aprovação, confiança, integridade, governabilidade, base legislativa) mudaram desde a última medição.
Cada mudança vira uma variação padronizada, que o grafo do registro espalha (até 2 níveis) pelos indicadores
dependentes. O efeito aparece no estado nacional (`state["nation"]`) e, em parte, nos municípios (escopo "nation").
Pesos e escalas são escolhas de design; o registro (`indicator_registry.py`) é a fonte única das relações.
"""
from __future__ import annotations

from datetime import date
from typing import Any

from .indicator_registry import REGISTRY, propagate

# métrica do estado -> (indicador do registro, variação que conta como "1 unidade")
METRIC_MAP: dict[str, tuple[str, float]] = {
    "gdp_growth": ("crescimento_pib", 1.0), "inflation": ("inflacao", 1.0), "unemployment": ("desemprego", 1.0),
    "debt_gdp": ("divida_pib", 5.0), "primary_balance": ("resultado_primario", 0.5), "approval": ("aprovacao", 10.0),
    "institutional_trust": ("confianca_institucional", 10.0), "integrity": ("integridade", 10.0),
    "governability": ("governabilidade", 10.0), "congress_support": ("base_legislativa", 10.0),
}
MAPPED = {v[0] for v in METRIC_MAP.values()}
DEFAULTS = {"juros": 10.5, "cambio": 5.3, "risco_pais": 220.0, "balanca_comercial": 60.0, "salario_minimo": 1518.0, "transferencias": 1.6,
            "investimento_publico": 2.2, "gasto_pessoal": 45.0, "desoneracoes": 0.9, "carga_tributaria": 32.0, "expectativas": 4.0,
            "acordos_comerciais": 12.0, "desmatamento": 9000.0, "fiscalizacao_ambiental": 50.0, "emissoes": 2300.0, "energia_limpa": 48.0,
            "investimento_seguranca": 5.0, "logistica": 100.0, "autonomia_bc": 1.0, "homicidios": 22.0}
STEP = {"%": 0.5, "0 a 100": 1.0, "0 a 1": 0.005, "% a.a.": 0.5, "% do PIB": 0.3, "por mil": 0.5, "anos": 0.1, "por 100 mil": 0.5}
HISTORY_LIMIT = 72


def _initial(state: dict[str, Any]) -> dict[str, float]:
    from .territory import overview
    country = overview(state)["country"]["indicators"]
    values: dict[str, float] = {k: float(v) for k, v in country.items()}
    for k, v in DEFAULTS.items():
        values.setdefault(k, v)
    for key, (ind, _) in METRIC_MAP.items():
        if key in state.get("metrics", {}):
            values[ind] = float(state["metrics"][key])
    return values


def ensure(state: dict[str, Any]) -> dict[str, Any]:
    nation = state.setdefault("nation", {})
    if "values" not in nation:
        nation["values"] = _initial(state)
        nation["snapshot"] = {m: float(state.get("metrics", {}).get(m, 0)) for m in METRIC_MAP}
        nation["history"] = []
        nation["last_tick"] = state.get("date")
    return nation


def _scale(key: str, value: float) -> float:
    unit = REGISTRY.get(key, {}).get("unit", "")
    return STEP.get(unit, max(abs(value) * 0.005, 0.01))


def tick(state: dict[str, Any], before: date, after: date) -> list[str]:
    nation = ensure(state)
    metrics = state.get("metrics", {})
    changes: dict[str, float] = {}
    for metric, (ind, unit) in METRIC_MAP.items():
        if metric in metrics:
            changes[ind] = (float(metrics[metric]) - float(nation["snapshot"].get(metric, metrics[metric]))) / unit
            nation["values"][ind] = float(metrics[metric])
            nation["snapshot"][metric] = float(metrics[metric])
    changes = {k: v for k, v in changes.items() if abs(v) > 1e-9}
    if not changes:
        return []
    spread = propagate(changes, depth=2, decay=0.35)
    territory = state.setdefault("territory", {}).setdefault("deltas", {}).setdefault("nation", {})
    for key, units in spread.items():
        if key in MAPPED or key not in REGISTRY or key not in nation["values"]:
            continue
        move = units * _scale(key, nation["values"][key])
        nation["values"][key] = round(nation["values"][key] + move, 4)
        from .territory import _clamp
        nation["values"][key] = round(_clamp(key, nation["values"][key]), 4)
        if abs(move) > 0:
            territory[key] = round(territory.get(key, 0.0) + move * 0.5, 5)
    month = after.isoformat()[:7]
    history = nation["history"]
    if not history or history[-1]["month"] != month:
        history.append({"month": month, "values": {k: round(v, 3) for k, v in nation["values"].items()}})
        del history[:-HISTORY_LIMIT]
    nation["last_tick"] = after.isoformat()
    return []


def snapshot(state: dict[str, Any]) -> dict[str, Any]:
    nation = ensure(state)
    first = nation["history"][0]["values"] if nation["history"] else nation["values"]
    rows = []
    for key, value in nation["values"].items():
        meta = REGISTRY.get(key)
        if not meta or "pais" not in meta["scopes"]:
            continue
        rows.append({"id": key, "label": meta["label"], "unit": meta["unit"], "domain": meta["domain"], "better": meta["better"],
                     "value": round(value, 3), "change_since_start": round(value - first.get(key, value), 3)})
    return {"indicators": rows, "months_recorded": len(nation["history"])}
