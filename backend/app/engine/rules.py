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


def _measure_result(state: dict[str, Any], interpretation: dict[str, Any]) -> dict[str, float]:
    """Return the exact one-time metric changes that apply_effects will record."""
    rule = RULES.get(interpretation.get("category", "other"), RULES["other"])
    metrics = state.get("metrics", {})
    balance = float(metrics.get("primary_balance", 0))
    growth = float(metrics.get("gdp_growth", 0))
    approval = float(metrics.get("approval", 0))
    cost = max(0.0, float(interpretation.get("fiscal_cost_bi", 0) or 0))
    return {
        "primary_balance": round(balance + rule["fiscal"] * 0.12 - min(0.1, cost / 10000), 2),
        "gdp_growth": round(growth + rule["gdp"] * 0.15, 2),
        "approval": round(min(100, max(0, approval + rule["approval"])), 1),
    }


def forecast(state: dict[str, Any], interpretation: dict[str, Any]) -> dict[str, Any]:
    """Project the isolated direct result by horizon; do not invent passage odds."""
    from datetime import date, timedelta

    baseline = {
        "primary_balance": float(state.get("metrics", {}).get("primary_balance", 0)),
        "gdp_growth": float(state.get("metrics", {}).get("gdp_growth", 0)),
        "approval": float(state.get("metrics", {}).get("approval", 0)),
    }
    result = _measure_result(state, interpretation)
    names = {
        "primary_balance": ("Resultado primário", "p.p. do PIB"),
        "gdp_growth": ("Crescimento do PIB", "p.p."),
        "approval": ("Aprovação", "p.p."),
    }
    metric_rows = lambda values: [
        {"key": key, "label": names[key][0], "unit": names[key][1],
         "before": baseline[key], "after": values[key],
         "delta": round(values[key] - baseline[key], 2 if key != "approval" else 1)}
        for key in names
    ]
    instrument = str(interpretation.get("instrument", "")).strip().lower()
    legal_days = {
        "projeto de lei": 90,
        "projeto de lei complementar": 150,
        "pec": 150,
    }
    decision_days = legal_days.get(instrument, 0)
    try:
        today = date.fromisoformat(state.get("date", date.today().isoformat()))
    except (TypeError, ValueError):
        today = date.today()
    decision_date = (today + timedelta(days=decision_days)).isoformat() if decision_days else None

    timeline = []
    for day, label in [(0, "Agora"), (90, "Em 3 meses"), (180, "Em 6 meses"), (365, "Em 12 meses")]:
        pending = decision_days > day
        conditional = decision_days > 0 and not pending
        projected = baseline if pending else result
        if decision_days == 0:
            status = "Efeito direto se assinar agora" if day == 0 else "Impacto inicial mantido, isolando outros eventos"
        elif pending:
            status = f"Em tramitação; votação simulada prevista para {decision_date}"
        else:
            status = "Se aprovada; se rejeitada, permanece sem este efeito"
        timeline.append({
            "day": day,
            "label": label,
            "status": status,
            "conditional_on_approval": conditional,
            "metrics": metric_rows(projected),
        })

    return {
        "impact_if_applied": metric_rows(result),
        "timeline": timeline,
        "notes": [
            "Projeção isolada desta decisão: eventos, economia e novas medidas podem alterar os indicadores.",
            "O impacto é registrado uma vez; os horizontes não somam o mesmo ganho a cada mês.",
            "A tramitação não recebe probabilidade de aprovação nesta versão.",
        ],
    }

def apply_effects(state: dict[str, Any], interpretation: dict[str, Any]) -> list[dict[str, Any]]:
    ensure_fiscal_state(state)
    rule = RULES.get(interpretation.get("category", "other"), RULES["other"])
    m = state["metrics"]
    previous_primary_balance = float(m["primary_balance"])
    projected = _measure_result(state, interpretation)
    m["primary_balance"] = projected["primary_balance"]
    m["gdp_growth"] = projected["gdp_growth"]
    m["approval"] = projected["approval"]
    m["governability"] = int(min(100, max(0, m["governability"] + (1 if interpretation.get("instrument") == "Ato do Executivo" else 0))))
    record_policy_balance_delta(state, float(m["primary_balance"]) - previous_primary_balance)
    return [{"label": rule["label"], "fiscal_delta": rule["fiscal"], "gdp_delta": rule["gdp"], "approval_delta": rule["approval"]}]
