"""Monthly snapshots for indicator trend labels in the grouped dashboard."""
from __future__ import annotations

from copy import deepcopy
from typing import Any


def record_indicator_snapshot(state: dict[str, Any]) -> None:
    current = {
        "date": state.get("date"),
        "metrics": deepcopy(state.get("metrics", {})),
        "institutions": deepcopy(state.get("institutions", {})),
        "social_indicators": deepcopy(state.get("social_indicators", {})),
        "fiscal": deepcopy(state.get("fiscal", {})),
        "diplomacy": deepcopy(state.get("diplomacy", {})),
        "regional_metrics": deepcopy(state.get("regional_metrics", {})),
        "budget": {
            "outcomes": deepcopy(state.get("budget", {}).get("outcomes", {})),
            "annual_investment_bi": state.get("budget", {}).get("annual_investment_bi"),
        },
    }
    history = state.setdefault("indicator_history", [])
    current_month = str(current["date"] or "")[:7]
    same_month = history and str(history[-1].get("date", ""))[:7] == current_month
    if same_month and len(history) > 1:
        history[-1] = current
    elif not same_month:
        history.append(current)
    state["indicator_history"] = history[-60:]
