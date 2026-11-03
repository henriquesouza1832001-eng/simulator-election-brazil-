"""Deterministic, simplified federal cash-flow model for the game."""
from __future__ import annotations

from typing import Any

REFERENCE_NOMINAL_GDP_BI = 15000.0
BASE_EFFECTIVE_INTEREST_RATE = 0.045

REVENUE_LINES = {
    "income_profit": {"label": "Renda e lucro", "annual_bi": 920.0},
    "consumption": {"label": "Consumo e producao", "annual_bi": 940.0},
    "social_contributions": {"label": "Contribuicoes sociais", "annual_bi": 820.0},
    "other_revenue": {"label": "Outras receitas", "annual_bi": 320.0},
}

MANDATORY_LINES = {
    "social_and_pensions": {"label": "Previdencia e assistencia", "share": 0.50},
    "payroll": {"label": "Folha e encargos", "share": 0.155},
    "state_transfers": {"label": "Transferencias federativas", "share": 0.1725},
    "essential_services": {"label": "Servicos essenciais e pisos", "share": 0.1725},
}


def _ensure_operating_price_lines(state: dict[str, Any]) -> dict[str, Any]:
    operating = state.setdefault("budget", {}).setdefault("operating", {})
    operating.setdefault("last_review", None)
    operating.setdefault("travel_cut_pct", 0)
    operating.setdefault("residence_cut_pct", 0)
    lines = operating.setdefault("lines", {})
    defaults = {
        "official_travel": {"label": "Viagens oficiais e delegacoes", "annual_cost_bi": 2.4,
                            "description": "Deslocamentos institucionais, missoes e delegacoes do Executivo."},
        "official_residence": {"label": "Residencia oficial e manutencao", "annual_cost_bi": 0.6,
                                "description": "Manutencao, servicos e funcionamento das residencias oficiais."},
    }
    for key, default in defaults.items():
        line = lines.setdefault(key, dict(default))
        current = max(0.0, float(line.get("annual_cost_bi", default["annual_cost_bi"])))
        base = max(0.01, float(line.setdefault("base_annual_cost_bi", current)))
        line.setdefault("price_index", max(0.01, current / base))
    return lines


def ensure_fiscal_state(state: dict[str, Any]) -> dict[str, Any]:
    """Initialize/migrate the cash ledger while preserving the saved primary balance."""
    fiscal = state.setdefault("fiscal", {})
    _ensure_operating_price_lines(state)
    if fiscal.get("initialized"):
        return fiscal

    metrics = state.setdefault("metrics", {})
    gdp = float(fiscal.get("nominal_gdp_bi", REFERENCE_NOMINAL_GDP_BI))
    revenue = float(fiscal.get("annual_revenue_bi", sum(x["annual_bi"] for x in REVENUE_LINES.values())))
    budget = state.setdefault("budget", {})
    investments = float(budget.get("annual_investment_bi", 100.0))
    operating = budget.setdefault("operating", {})
    operating.setdefault("last_review", None)
    operating.setdefault("travel_cut_pct", 0)
    operating.setdefault("residence_cut_pct", 0)
    lines = operating.setdefault("lines", {})
    lines.setdefault("official_travel", {"label": "Viagens oficiais e delegacoes", "annual_cost_bi": 2.4,
        "description": "Deslocamentos institucionais, missoes e delegacoes do Executivo."})
    lines.setdefault("official_residence", {"label": "Residencia oficial e manutencao", "annual_cost_bi": 0.6,
        "description": "Manutenção, serviços e funcionamento das residências oficiais."})

    # For old saves, derive a residual mandatory-spending baseline that exactly
    # preserves the saved primary balance, then break it into visible categories.
    primary_pct = float(metrics.get("primary_balance", -1.5))
    target_spending = max(0.0, revenue - primary_pct * gdp / 100)
    ops = _operating_cost_bi(operating)
    nonmandatory = float(fiscal.get("procurement_bi", 222.0)) + investments + ops
    mandatory_total = max(0.0, target_spending - nonmandatory)
    fiscal.update({
        "initialized": True,
        "nominal_gdp_bi": gdp,
        "debt_stock_bi": float(metrics.get("debt_gdp", 78.0)) * gdp / 100,
        "revenue_lines": {key: {**line} for key, line in REVENUE_LINES.items()},
        "mandatory_lines": {key: {"label": line["label"], "annual_bi": mandatory_total * line["share"]}
                            for key, line in MANDATORY_LINES.items()},
        "procurement_bi": float(fiscal.get("procurement_bi", 222.0)),
        "policy_adjustment_bi": 0.0,
        "annual_revenue_bi": revenue,
        "annual_primary_spending_bi": target_spending,
        "annual_interest_bi": float(fiscal.get("annual_interest_bi", 965.0)),
        "interest_rate_pct": float(fiscal.get("interest_rate_pct", 7.8)),
        "current_year_extra_spending_bi": 0.0,
        "current_year": int(str(state.get("date", "2027-01-01"))[:4]),
    })
    refresh_fiscal_metrics(state)
    return fiscal


def _operating_cost_bi(operating: dict[str, Any]) -> float:
    lines = operating.get("lines", {})
    travel = float(lines.get("official_travel", {}).get("annual_cost_bi", 2.4))
    residence = float(lines.get("official_residence", {}).get("annual_cost_bi", 0.6))
    travel *= 1 - float(operating.get("travel_cut_pct", 0)) / 100
    residence *= 1 - float(operating.get("residence_cut_pct", 0)) / 100
    return max(0.0, travel + residence)


def primary_spending_bi(state: dict[str, Any]) -> float:
    fiscal = state["fiscal"]
    budget = state["budget"]
    mandatory = sum(float(line["annual_bi"]) for line in fiscal["mandatory_lines"].values())
    investments = float(budget.get("annual_investment_bi", 100.0))
    operating = _operating_cost_bi(budget.get("operating", {}))
    works_overrun = float(budget.get("works", {}).get("annual_overrun_bi", 0))
    return max(0.0, mandatory + float(fiscal.get("procurement_bi", 0)) + investments + operating
               + works_overrun - float(fiscal.get("policy_adjustment_bi", 0)))


def refresh_fiscal_metrics(state: dict[str, Any]) -> dict[str, Any]:
    fiscal = state["fiscal"]
    metrics = state["metrics"]
    gdp = max(1.0, float(fiscal.get("nominal_gdp_bi", REFERENCE_NOMINAL_GDP_BI)))
    debt = max(0.0, float(fiscal.get("debt_stock_bi", metrics.get("debt_gdp", 78) * gdp / 100)))
    revenue = sum(float(line["annual_bi"]) for line in fiscal["revenue_lines"].values())
    primary_spending = primary_spending_bi(state)
    primary_pct = (revenue - primary_spending) / gdp * 100
    debt_pct = debt / gdp * 100
    credibility = max(0.0, min(100.0, 70 - max(0.0, debt_pct - 60) * .65 + primary_pct * 2))
    risk = max(70.0, min(900.0, 100 + (100 - credibility) * 3 + max(0.0, debt_pct - 60) * 2 + max(0.0, -primary_pct) * 5))
    rate = BASE_EFFECTIVE_INTEREST_RATE * 100 + risk * .01
    interest = debt * rate / 100
    nominal_result = revenue - primary_spending - interest

    fiscal.update({"nominal_gdp_bi": gdp, "debt_stock_bi": debt, "annual_revenue_bi": revenue,
                   "annual_primary_spending_bi": primary_spending, "annual_interest_bi": interest,
                   "interest_rate_pct": rate, "annual_nominal_result_bi": nominal_result,
                   "primary_result_bi": revenue - primary_spending, "fiscal_credibility": credibility,
                   "country_risk": risk})
    metrics["primary_balance"] = round(primary_pct, 3)
    metrics["debt_gdp"] = round(debt_pct, 2)
    metrics["fiscal_credibility"] = round(credibility, 1)
    metrics["country_risk"] = round(risk)
    metrics["nominal_result"] = round(nominal_result / gdp * 100, 2)
    return fiscal


def fiscal_overview(state: dict[str, Any]) -> dict[str, Any]:
    fiscal = ensure_fiscal_state(state)
    refresh_fiscal_metrics(state)
    budget = state["budget"]
    operating = budget.get("operating", {})
    lines = operating.get("lines", {})
    travel_cut = float(operating.get("travel_cut_pct", 0))
    residence_cut = float(operating.get("residence_cut_pct", 0))
    primary_spending = [{"key": key, "label": line["label"], "annual_bi": float(line["annual_bi"])}
                        for key, line in fiscal["mandatory_lines"].items()]
    primary_spending.extend([
        {"key": "procurement", "label": "Compras e contratos", "annual_bi": float(fiscal["procurement_bi"])},
        {"key": "investment", "label": "Investimentos", "annual_bi": float(budget.get("annual_investment_bi", 100))},
        {"key": "official_travel", "label": "Viagens oficiais", "annual_bi": float(lines.get("official_travel", {}).get("annual_cost_bi", 0)) * (1 - travel_cut / 100)},
        {"key": "official_residence", "label": "Residencias oficiais", "annual_bi": float(lines.get("official_residence", {}).get("annual_cost_bi", 0)) * (1 - residence_cut / 100)},
    ])
    executive_investment = None
    career = state.get("career") or {}
    governance = career.get("governance") or {}
    if career.get("office") == "presidente" and governance and state.get("office_status") == "elected_official":
        annual_cap_bi = float(budget.get("annual_investment_bi", 100.0))
        legacy_annual_mi = float(governance.get("annual_budget_mi", annual_cap_bi * 1000))
        legacy_available_mi = float(governance.get("budget_mi", legacy_annual_mi))
        committed_mi = max(0.0, float(governance.get("investment_commitment_mi", legacy_annual_mi - legacy_available_mi)))
        executive_investment = {
            "annual_cap_bi": annual_cap_bi,
            "committed_bi": committed_mi / 1000,
            "available_bi": max(0.0, annual_cap_bi * 1000 - committed_mi) / 1000,
            "overcommitted_bi": max(0.0, committed_mi - annual_cap_bi * 1000) / 1000,
            "simulated": True,
        }
    return {"currency": "R$ bi por ano", "nominal_gdp_bi": float(fiscal["nominal_gdp_bi"]),
            "revenue": [{"key": key, "label": line["label"], "annual_bi": float(line["annual_bi"])} for key, line in fiscal["revenue_lines"].items()],
            "primary_spending": primary_spending, "annual_revenue_bi": float(fiscal["annual_revenue_bi"]),
            "annual_primary_spending_bi": float(fiscal["annual_primary_spending_bi"]),
            "primary_result_bi": float(fiscal["primary_result_bi"]),
            "annual_interest_bi": float(fiscal["annual_interest_bi"]),
            "annual_nominal_result_bi": float(fiscal["annual_nominal_result_bi"]),
            "current_year_extra_spending_bi": float(fiscal.get("current_year_extra_spending_bi", 0)),
            "debt_stock_bi": float(fiscal["debt_stock_bi"]), "interest_rate_pct": float(fiscal["interest_rate_pct"]),
            "primary_balance_pct_gdp": float(state["metrics"]["primary_balance"]),
            "nominal_result_pct_gdp": float(state["metrics"]["nominal_result"]),
            "debt_pct_gdp": float(state["metrics"]["debt_gdp"]),
            "fiscal_credibility": float(state["metrics"]["fiscal_credibility"]),
            "country_risk": float(state["metrics"]["country_risk"]),
            "executive_investment": executive_investment,
            "note": "Estimativas simplificadas do simulador; nao sao execucao oficial do orcamento."
                    + (" Programas presidenciais comprometidos estao incluidos na rubrica Investimentos e nao sao somados novamente." if executive_investment else "")}


def record_policy_balance_delta(state: dict[str, Any], delta_pct_gdp: float) -> None:
    fiscal = ensure_fiscal_state(state)
    fiscal["policy_adjustment_bi"] = float(fiscal.get("policy_adjustment_bi", 0)) + delta_pct_gdp * float(fiscal["nominal_gdp_bi"]) / 100
    refresh_fiscal_metrics(state)


def record_one_off_spending(state: dict[str, Any], amount_bi: float) -> None:
    fiscal = ensure_fiscal_state(state)
    fiscal["debt_stock_bi"] = max(0.0, float(fiscal["debt_stock_bi"]) + amount_bi)
    year = int(str(state.get("date", "2027-01-01"))[:4])
    if int(fiscal.get("current_year", year)) != year:
        fiscal["current_year"] = year
        fiscal["current_year_extra_spending_bi"] = 0.0
    fiscal["current_year_extra_spending_bi"] = float(fiscal.get("current_year_extra_spending_bi", 0)) + amount_bi
    refresh_fiscal_metrics(state)


def advance_fiscal(state: dict[str, Any], elapsed_days: int, volatility: float = 1.0) -> None:
    fiscal = ensure_fiscal_state(state)
    if elapsed_days <= 0:
        return
    year = int(str(state.get("date", "2027-01-01"))[:4])
    if int(fiscal.get("current_year", year)) != year:
        fiscal["current_year"] = year
        fiscal["current_year_extra_spending_bi"] = 0.0
    metrics = state["metrics"]
    old_gdp = max(1.0, float(fiscal["nominal_gdp_bi"]))
    old_debt = max(0.0, float(fiscal["debt_stock_bi"]))
    real_growth = float(metrics.get("gdp_growth", 0))
    inflation = float(metrics.get("inflation", 0))
    nominal_growth = max(-.15, (real_growth + inflation) / 100 * volatility)
    factor = max(.8, 1 + nominal_growth) ** (elapsed_days / 365)
    fiscal["nominal_gdp_bi"] = old_gdp * factor
    for line in fiscal["revenue_lines"].values():
        line["annual_bi"] *= factor
    expense_factor = max(.8, 1 + max(-.1, inflation / 100)) ** (elapsed_days / 365)
    for line in fiscal["mandatory_lines"].values():
        line["annual_bi"] *= expense_factor
    fiscal["procurement_bi"] = float(fiscal["procurement_bi"]) * expense_factor
    operating_lines = _ensure_operating_price_lines(state)
    for line_key in ("official_travel", "official_residence"):
        line = operating_lines.get(line_key)
        if line is not None:
            line["price_index"] = max(0.01, float(line.get("price_index", 1.0)) * expense_factor)
            line["annual_cost_bi"] = max(
                0.0,
                float(line.get("base_annual_cost_bi", line.get("annual_cost_bi", 0))) * line["price_index"],
            )

    refresh_fiscal_metrics(state)
    annual_primary_deficit = float(fiscal["annual_primary_spending_bi"]) - float(fiscal["annual_revenue_bi"])
    annual_interest = float(fiscal["annual_interest_bi"])
    fiscal["debt_stock_bi"] = max(0.0, old_debt + (annual_primary_deficit + annual_interest) * elapsed_days / 365)
    refresh_fiscal_metrics(state)
