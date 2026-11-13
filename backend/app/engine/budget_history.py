"""Histórico mensal do orçamento de investimento por função: previsto × executado.

Previsto = dotação anual da função ÷ 12. Executado = previsto + gastos extras do mês ligados à função (estouro das obras
de transporte, e custos únicos de ações de competência mapeadas por área) ± o que foi remanejado. Os valores do jogo são
em R$ bilhões e são parâmetros de design, não a execução orçamentária oficial.
"""
from __future__ import annotations

from datetime import date
from typing import Any

from .ministries import INVESTMENT_AREAS

DOMAIN_TO_FUNCTION = {"infraestrutura": "logistics", "defesa": "security", "seguranca": "security", "saneamento": "sanitation", "saude": "health", "educacao": "education"}
LIMIT = 60


def _st(state: dict[str, Any]) -> dict[str, Any]:
    h = state.setdefault("budget_history", {})
    h.setdefault("months", [])
    h.setdefault("extra", {})
    h.setdefault("month_key", state.get("date", "2027-01-01")[:7])
    return h


def add_extra(state: dict[str, Any], domain: str, amount_bi: float) -> None:
    """Registra gasto extra de um custo único, na função correspondente ao domínio da ação (se houver)."""
    fn = DOMAIN_TO_FUNCTION.get(domain)
    if fn and amount_bi > 0:
        h = _st(state)
        h["extra"][fn] = round(h["extra"].get(fn, 0.0) + amount_bi, 3)


def tick(state: dict[str, Any], before: date, after: date) -> list[str]:
    h = _st(state)
    month = after.isoformat()[:7]
    if month == h["month_key"]:
        return []
    allocations = state.get("budget", {}).get("allocations", {})
    works = state.get("budget", {}).get("works", {})
    rows = {}
    for key, area in INVESTMENT_AREAS.items():
        planned = float(allocations.get(key, area["budget"])) / 12
        extra = float(h["extra"].get(key, 0.0))
        if key == "logistics":
            extra += float(works.get("annual_overrun_bi", 0.0)) / 12
        rows[key] = {"label": area["label"], "planned": round(planned, 3), "executed": round(planned + extra, 3)}
    fiscal = state.get("fiscal", {})
    h["months"].append({"month": h["month_key"], "functions": rows, "primary_result_bi": round(float(fiscal.get("primary_result_bi", 0.0)), 1),
                        "debt_bi": round(float(fiscal.get("debt_stock_bi", 0.0)), 1)})
    del h["months"][:-LIMIT]
    h["extra"] = {}
    h["month_key"] = month
    return []


def overview(state: dict[str, Any]) -> dict[str, Any]:
    h = _st(state)
    months = h["months"]
    year = (months[-1]["month"][:4] if months else state.get("date", "2027")[:4])
    ytd: dict[str, dict[str, Any]] = {}
    for m in months:
        if m["month"][:4] != year:
            continue
        for key, row in m["functions"].items():
            a = ytd.setdefault(key, {"label": row["label"], "planned": 0.0, "executed": 0.0})
            a["planned"] += row["planned"]
            a["executed"] += row["executed"]
    summary = [{"function": k, "label": v["label"], "planned_bi": round(v["planned"], 2), "executed_bi": round(v["executed"], 2),
                "difference_bi": round(v["executed"] - v["planned"], 2)} for k, v in ytd.items()]
    return {"year": year, "months": months[-24:], "ytd": summary,
            "note": "Valores em R$ bilhões do orçamento de investimento do jogo (previsto = dotação ÷ 12). Não é a execução orçamentária oficial."}
