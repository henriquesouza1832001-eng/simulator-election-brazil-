"""Policy bot. Training episodes use the deterministic engine and never call an LLM."""
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..engine.rules import RULES


@dataclass
class Decision:
    action: str
    rationale: str


def choose_action(state: dict[str, Any]) -> Decision:
    metrics = state["metrics"]
    policy_path = Path(__file__).resolve().parents[3] / "data" / "policy.json"
    if policy_path.exists():
        try:
            policy = json.loads(policy_path.read_text(encoding="utf-8"))
            learned = policy.get("best_action_by_state", {}).get(state_key(state))
            if learned in RULES:
                return Decision(learned, "Ação escolhida pela política tabular treinada em cenários sintéticos.")
        except (OSError, ValueError):
            pass
    if metrics["primary_balance"] < -2.0:
        return Decision("fiscal_efficiency", "Conter o déficit reduz pressão fiscal no longo prazo.")
    if metrics["approval"] < 45:
        return Decision("communication", "Recuperar confiança pública antes de assumir novo custo.")
    if metrics["gdp_growth"] < 1.0:
        return Decision("business_formalization", "Estimular atividade e formalização com baixo custo fiscal.")
    return Decision("fiscal_efficiency", "Priorizar medidas de eficiência com custo controlado.")


def reward(state: dict[str, Any]) -> float:
    """Transparent starter objective; weights can be tuned from play feedback."""
    m = state["metrics"]
    return (m["approval"] * 0.25 + m["gdp_growth"] * 8 + m["primary_balance"] * 7
            - max(0, m["inflation"] - 3) * 4 - max(0, m["debt_gdp"] - 70) * 0.5
            + m["governability"] * 0.15 + m["integrity"] * 0.2)


def state_key(state: dict[str, Any]) -> str:
    m = state["metrics"]
    fiscal = "deficit" if m["primary_balance"] < -1 else "near" if m["primary_balance"] < 0 else "surplus"
    approval = "low" if m["approval"] < 45 else "mid" if m["approval"] < 60 else "high"
    growth = "slow" if m["gdp_growth"] < 1.5 else "steady" if m["gdp_growth"] < 3.0 else "fast"
    return f"{fiscal}|{approval}|{growth}"
