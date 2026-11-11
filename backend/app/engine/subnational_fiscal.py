"""Contas de prefeituras e governos estaduais: folha, dívida, limites da LRF e resumo mensal.

Modelo simplificado e rotulado como tal: a receita corrente líquida (RCL) é derivada da reserva anual do cargo
(`annual_budget_mi` x RCL_FACTOR). Os limites seguem a LRF (LC 101/2000, art. 20 e 22) e a Resolução 40/2001 do Senado,
mas os valores iniciais de folha e dívida são parâmetros de design, não dados do ente.
"""
from __future__ import annotations

from datetime import date
from typing import Any

from .career import is_career_governing

RCL_FACTOR = 8.0   # RCL = reserva anual x 8 (a reserva de programas equivale a ~12,5% da receita)
LIMITS = {
    "prefeito": {"personnel": 54.0, "debt": 120.0, "basis": "LRF art. 20, III, b (54% da RCL no Executivo municipal); Res. Senado 40/2001 (dívida de 1,2 RCL)"},
    "governador": {"personnel": 49.0, "debt": 200.0, "basis": "LRF art. 20, II, c (49% da RCL no Executivo estadual); Res. Senado 40/2001 (dívida de 2,0 RCL)"},
}
START = {"prefeito": {"personnel": 45.0, "debt": 40.0}, "governador": {"personnel": 42.0, "debt": 90.0}}
ALERT, PRUDENTIAL = 0.90, 0.95      # LRF art. 59, §1º, II e art. 22, parágrafo único
HISTORY = 24


def _gov(state: dict[str, Any]) -> dict[str, Any] | None:
    career = state.get("career") or {}
    if career.get("mode") and career.get("office") in LIMITS and is_career_governing(career, date.fromisoformat(state["date"])):
        return career.setdefault("governance", {})
    return None


def ensure(state: dict[str, Any]) -> dict[str, Any] | None:
    gov = _gov(state)
    if gov is None:
        return None
    office = state["career"]["office"]
    fiscal = gov.setdefault("fiscal", {"personnel_pct": START[office]["personnel"], "debt_pct": START[office]["debt"], "year": int(state["date"][:4]),
                                       "month_key": state["date"][:7], "month_spent_mi": 0.0, "summaries": [], "commitments": []})
    return fiscal


def rcl_mi(gov: dict[str, Any]) -> float:
    return round(float(gov.get("annual_budget_mi", 0)) * RCL_FACTOR, 1)


def status(state: dict[str, Any]) -> dict[str, Any] | None:
    fiscal = ensure(state)
    if fiscal is None:
        return None
    gov = state["career"]["governance"]
    limit = LIMITS[state["career"]["office"]]
    p, d = fiscal["personnel_pct"], fiscal["debt_pct"]
    level = "excedido" if p > limit["personnel"] else "prudencial" if p > limit["personnel"] * PRUDENTIAL else "alerta" if p > limit["personnel"] * ALERT else "regular"
    return {"rcl_mi": rcl_mi(gov), "annual_reserve_mi": round(float(gov.get("annual_budget_mi", 0)), 1), "reserve_available_mi": round(float(gov.get("budget_mi", 0)), 1),
            "personnel_pct": round(p, 1), "personnel_limit": limit["personnel"], "personnel_level": level,
            "debt_pct": round(d, 1), "debt_limit": limit["debt"], "basis": limit["basis"],
            "commitments": fiscal["commitments"], "summaries": fiscal["summaries"][-12:],
            "note": "Modelo simplificado: RCL e valores iniciais são parâmetros do jogo, não dados oficiais do ente."}


def check_can_spend(state: dict[str, Any], kind: str = "programa") -> str | None:
    """Bloqueio da LRF: acima do limite de pessoal, o ente não pode ampliar despesa com pessoal."""
    s = status(state)
    if s is None:
        return None
    if kind == "pessoal" and s["personnel_level"] in {"prudencial", "excedido"}:
        return f"LRF: folha em {s['personnel_pct']}% da RCL, acima do limite prudencial. Reduza despesa com pessoal antes de ampliá-la."
    if kind == "credito" and s["debt_pct"] >= s["debt_limit"]:
        return "Limite de endividamento atingido (Resolução 40/2001 do Senado)."
    return None


def apply(state: dict[str, Any], *, personnel: float = 0.0, debt: float = 0.0, reserve_pct: float = 0.0) -> dict[str, float]:
    fiscal = ensure(state)
    if fiscal is None:
        return {}
    gov = state["career"]["governance"]
    fiscal["personnel_pct"] = round(max(20.0, fiscal["personnel_pct"] + personnel), 2)
    fiscal["debt_pct"] = round(max(0.0, fiscal["debt_pct"] + debt), 2)
    if reserve_pct:
        gov["budget_mi"] = round(float(gov.get("budget_mi", 0)) + float(gov.get("annual_budget_mi", 0)) * reserve_pct, 2)
    return {"personnel_pct": personnel, "debt_pct": debt, "reserve_pct": reserve_pct}


def commit_project(state: dict[str, Any], item: dict[str, Any], months: int, total_mi: float) -> str | None:
    """Obra de território: o custo anualizado sai da reserva do cargo e se repete a cada ano até a entrega."""
    fiscal = ensure(state)
    if fiscal is None:
        return None
    gov = state["career"]["governance"]
    annual = round(total_mi / max(months / 12, 1), 1)
    if annual > float(gov.get("budget_mi", 0)):
        return f"A reserva do cargo (R$ {gov.get('budget_mi', 0):,.1f} mi) não cobre a parcela anual de R$ {annual:,.1f} mi desta obra."
    gov["budget_mi"] = round(float(gov["budget_mi"]) - annual, 1)
    fiscal["month_spent_mi"] += annual
    fiscal["commitments"].append({"id": item["id"], "name": item["name"], "annual_mi": annual, "end": item["end"]})
    return None


def tick(state: dict[str, Any], before: date, after: date) -> list[str]:
    fiscal = ensure(state)
    if fiscal is None:
        return []
    gov = state["career"]["governance"]
    messages: list[str] = []
    # virada de ano: compromissos de obras em andamento recomprometem parte da nova reserva
    if after.year != fiscal["year"]:
        fiscal["year"] = after.year
        live = [c for c in fiscal["commitments"] if date.fromisoformat(c["end"]) > after]
        fiscal["commitments"] = live
        for c in live:
            gov["budget_mi"] = round(max(0.0, float(gov.get("budget_mi", 0)) - c["annual_mi"]), 1)
        if live:
            messages.append(f"Nova reserva anual: R$ {sum(c['annual_mi'] for c in live):,.1f} mi já comprometidos com {len(live)} obra(s) em andamento.")
    month = after.isoformat()[:7]
    if month != fiscal["month_key"]:
        s = status(state)
        limit = LIMITS[state["career"]["office"]]["personnel"]
        fiscal["summaries"].append({"month": fiscal["month_key"], "rcl_mi": s["rcl_mi"], "personnel_pct": s["personnel_pct"], "debt_pct": s["debt_pct"],
                                    "executed_mi": round(fiscal["month_spent_mi"], 1), "reserve_left_mi": s["reserve_available_mi"], "level": s["personnel_level"]})
        del fiscal["summaries"][:-HISTORY]
        fiscal["month_key"], fiscal["month_spent_mi"] = month, 0.0
        # a folha cresce devagar com o tempo (vegetativo) e a dívida acompanha juros; limites ruins custam confiança
        fiscal["personnel_pct"] = round(fiscal["personnel_pct"] + 0.04, 2)
        fiscal["debt_pct"] = round(fiscal["debt_pct"] + 0.05, 2)
        if fiscal["personnel_pct"] > limit:
            gov["trust"] = round(max(0.0, float(gov.get("trust", 50)) - 0.6), 2)
            messages.append(f"LRF: folha de {fiscal['personnel_pct']}% da RCL acima do limite de {limit}%. A confiança cai até a correção.")
        elif fiscal["personnel_pct"] > limit * ALERT and s["personnel_level"] != "alerta":
            messages.append(f"LRF: alerta, folha em {fiscal['personnel_pct']}% da RCL (limite {limit}%).")
    return messages
