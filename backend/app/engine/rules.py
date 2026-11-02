from typing import Any
from .fiscal import ensure_fiscal_state, record_policy_balance_delta

# All outcome numbers live here, not in the language model's response.
RULES: dict[str, dict[str, Any]] = {
    "fiscal_efficiency": {"fiscal": 0.15, "gdp": 0.01, "credibility": 1, "approval": 0.3, "label": "Eficiência fiscal"},
    "business_formalization": {"fiscal": 0.04, "gdp": 0.08, "credibility": 0, "approval": 0.5, "label": "Formalização de negócios"},
    "public_investment": {"fiscal": -0.12, "gdp": 0.12, "credibility": -0.2, "approval": 0.4, "label": "Investimento público"},
    "tax_change": {"fiscal": 0.1, "gdp": -0.04, "credibility": 0.1, "approval": -0.2, "label": "Mudança tributária"},
    "social_policy": {"fiscal": -0.08, "gdp": 0.03, "credibility": -0.1, "approval": 0.5, "label": "Política social"},
    "security": {"fiscal": -0.04, "gdp": 0.01, "credibility": 0, "approval": 0.3, "label": "Segurança pública"},
    "communication": {"fiscal": 0, "gdp": 0, "credibility": 0, "approval": 0.2, "label": "Comunicação institucional"},
    "other": {"fiscal": 0, "gdp": 0, "credibility": 0, "approval": 0, "label": "Medida geral"},
}


def forecast(state: dict[str, Any], interpretation: dict[str, Any]) -> list[dict[str, str]]:
    rule = RULES.get(interpretation.get("category", "other"), RULES["other"])
    duration = interpretation.get("duration_days") or 365
    factor = min(1.0, max(0.2, duration / 365))
    fiscal = rule["fiscal"] * factor
    gdp = rule["gdp"] * factor
    approval = rule["approval"]
    if interpretation.get("fiscal_cost_bi", 0) > 0:
        fiscal -= min(0.25, interpretation["fiscal_cost_bi"] / 1000)
    return [
        {"label": "Saldo fiscal anual", "value": f"{fiscal:+.2f} p.p. do PIB", "tone": "green" if fiscal >= 0 else "red"},
        {"label": "Crescimento do PIB", "value": f"{gdp:+.2f} p.p.", "tone": "green" if gdp >= 0 else "amber"},
        {"label": "Aprovação", "value": f"{approval:+.1f} p.p.", "tone": "green" if approval >= 0 else "red"},
    ]


def apply_effects(state: dict[str, Any], interpretation: dict[str, Any]) -> list[dict[str, Any]]:
    ensure_fiscal_state(state)
    rule = RULES.get(interpretation.get("category", "other"), RULES["other"])
    m = state["metrics"]
    previous_primary_balance = float(m["primary_balance"])
    # Fiscal and growth forecasts are annualized; state changes by a small fraction at adoption.
    m["primary_balance"] = round(m["primary_balance"] + rule["fiscal"] * 0.12, 2)
    m["gdp_growth"] = round(m["gdp_growth"] + rule["gdp"] * 0.15, 2)
    m["approval"] = round(min(100, max(0, m["approval"] + rule["approval"])), 1)
    m["governability"] = int(min(100, max(0, m["governability"] + (1 if interpretation.get("instrument") == "Ato do Executivo" else 0))))
    if interpretation.get("fiscal_cost_bi", 0) > 0:
        m["primary_balance"] = round(m["primary_balance"] - min(0.1, interpretation["fiscal_cost_bi"] / 10000), 2)
    record_policy_balance_delta(state, float(m["primary_balance"]) - previous_primary_balance)
    return [{"label": rule["label"], "fiscal_delta": rule["fiscal"], "gdp_delta": rule["gdp"], "approval_delta": rule["approval"]}]
