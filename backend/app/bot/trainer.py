"""Train a small transparent tabular policy against synthetic game states.

Run from the backend folder: python -m app.bot.trainer --episodes 3000
This is a foundation for the in-game Python agent, not an economic forecast.
"""
import argparse
import json
import random
from pathlib import Path

from ..engine.rules import RULES, apply_effects
from ..engine.state import new_game
from .agent import reward, state_key


def train(episodes: int, seed: int = 41) -> dict:
    random.seed(seed)
    actions = list(RULES)
    q: dict[str, dict[str, float]] = {}
    alpha, gamma = 0.18, 0.82
    for episode in range(episodes):
        state = new_game()
        metrics = state["metrics"]
        metrics["approval"] = random.uniform(28, 78)
        metrics["gdp_growth"] = random.uniform(-0.5, 5.0)
        metrics["primary_balance"] = random.uniform(-5.0, 1.5)
        epsilon = max(0.04, 0.7 * (1 - episode / max(1, episodes)))
        for _ in range(18):
            key = state_key(state)
            values = q.setdefault(key, {action: 0.0 for action in actions})
            action = random.choice(actions) if random.random() < epsilon else max(values, key=values.get)
            old_score = reward(state)
            apply_effects(state, {"category": action, "instrument": "Ato do Executivo", "fiscal_cost_bi": 0})
            next_key = state_key(state)
            next_values = q.setdefault(next_key, {candidate: 0.0 for candidate in actions})
            delta = reward(state) - old_score
            # Small penalty discourages repeatedly selecting costly social/investment actions in a deficit.
            if state["metrics"]["primary_balance"] < -2 and action in {"public_investment", "social_policy"}:
                delta -= 0.08
            values[action] += alpha * (delta + gamma * max(next_values.values()) - values[action])

    policy = {key: max(values, key=values.get) for key, values in q.items()}
    output = Path(__file__).resolve().parents[3] / "data" / "policy.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"episodes": episodes, "seed": seed, "best_action_by_state": policy, "q_values": q}, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"episodes": episodes, "states_learned": len(policy), "output": str(output)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Treina o agente tabular Mandato em cenários sintéticos.")
    parser.add_argument("--episodes", type=int, default=3000)
    parser.add_argument("--seed", type=int, default=41)
    args = parser.parse_args()
    print(json.dumps(train(max(1, args.episodes), args.seed), ensure_ascii=False))


if __name__ == "__main__":
    main()
