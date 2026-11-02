"""Slow-moving social indicators derived from the simulation's service outcomes."""
from __future__ import annotations

from typing import Any


SOCIAL_BASELINE = {
    "population_millions": 203.1,
    "human_development_index": 0.785,
    "gini_index": 0.523,
    "poverty_rate_pct": 28.3,
    "life_expectancy_years": 76.5,
    "infant_mortality_per_1000": 12.6,
    "homicide_rate_per_100k": 17.3,
    "sanitation_coverage_pct": 58.3,
    "school_completion_pct": 72.0,
}


def ensure_social_indicators(state: dict[str, Any]) -> dict[str, float]:
    indicators = state.setdefault("social_indicators", {})
    for key, value in SOCIAL_BASELINE.items():
        indicators.setdefault(key, value)
    return indicators


def advance_social_indicators(state: dict[str, Any], elapsed_days: int) -> None:
    indicators = ensure_social_indicators(state)
    outcomes = state.get("budget", {}).get("outcomes", {})
    metrics = state.get("metrics", {})
    months = max(0.0, elapsed_days / 30.4375)
    education = float(outcomes.get("education", 50))
    health = float(outcomes.get("health", 50))
    security = float(outcomes.get("security", 50))
    infrastructure = float(outcomes.get("infrastructure", 50))
    productivity = float(outcomes.get("productivity", 50))
    growth = float(metrics.get("gdp_growth", 2.1))
    unemployment = float(metrics.get("unemployment", 7.2))

    indicators["population_millions"] = min(250.0, indicators["population_millions"] * (1 + .002 * elapsed_days / 365.25))
    indicators["sanitation_coverage_pct"] = min(99.0, indicators["sanitation_coverage_pct"] + .008 * ((infrastructure - 50) / 10) * months)
    indicators["school_completion_pct"] = min(99.5, indicators["school_completion_pct"] + .008 * ((education - 50) / 10) * months)

    poverty_change = (-.03 * (growth - 2.1) + .025 * (unemployment - 7.2) - .015 * ((education - 50) / 10)) * months
    indicators["poverty_rate_pct"] = max(3.0, min(65.0, indicators["poverty_rate_pct"] + poverty_change))
    indicators["gini_index"] = max(.30, min(.70, indicators["gini_index"] + poverty_change * .00045 - .000015 * ((education - 50) / 10) * months))
    indicators["human_development_index"] = max(.55, min(.95, indicators["human_development_index"] + .00012 * (((education + health + productivity) / 3 - 50) / 10) * months))
    indicators["life_expectancy_years"] = max(60.0, min(90.0, indicators["life_expectancy_years"] + .0003 * ((health - 50) - .4 * (indicators["homicide_rate_per_100k"] - 17.3)) * months))
    indicators["infant_mortality_per_1000"] = max(2.0, min(60.0, indicators["infant_mortality_per_1000"] - (.03 * ((health - 50) / 10) + .015 * ((indicators["sanitation_coverage_pct"] - 58.3) / 10)) * months))
    indicators["homicide_rate_per_100k"] = max(3.0, min(80.0, indicators["homicide_rate_per_100k"] + (-.04 * ((security - 50) / 10) + .02 * (unemployment - 7.2)) * months))

    for key, value in indicators.items():
        indicators[key] = round(value, 3)
