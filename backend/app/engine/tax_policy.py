"""Readable tax levers. Changes affect modelled incidence, revenue and activity separately."""

TAX_BASELINE = {
    "families_low_income": 32.0,
    "families_middle_income": 28.0,
    "families_high_income": 21.0,
    "business_agro": 21.0,
    "business_industry": 30.0,
    "business_services": 29.0,
    "business_finance": 45.0,
    "business_digital": 18.0,
}
TAX_LEVERS = {
    "families_low_income": {"label": "Famílias de baixa renda", "base": "consumption_and_payroll"},
    "families_middle_income": {"label": "Famílias de renda média", "base": "income_and_consumption"},
    "families_high_income": {"label": "Famílias de renda alta", "base": "income_and_property"},
    "business_agro": {"label": "Agronegócio", "base": "business_profit"},
    "business_industry": {"label": "Indústria", "base": "business_profit"},
    "business_services": {"label": "Comércio e serviços", "base": "business_profit"},
    "business_finance": {"label": "Bancos e seguros", "base": "business_profit"},
    "business_digital": {"label": "Tecnologia e digital", "base": "business_profit"},
}


def change_tax(state: dict, lever: str, points: float) -> dict:
    if lever not in TAX_LEVERS:
        raise ValueError("Faixa tributária desconhecida")
    points = max(-5.0, min(5.0, round(float(points), 1)))
    state.setdefault("tax_policy", TAX_BASELINE.copy())
    before = state["tax_policy"].get(lever, TAX_BASELINE[lever])
    state["tax_policy"][lever] = round(max(0.0, before + points), 1)
    # Deliberately returns a transparent proposal; fiscal microsimulation is a later layer.
    return {"lever": lever, "before": before, "after": state["tax_policy"][lever], "points": points, "needs_forecast_rule": True}
