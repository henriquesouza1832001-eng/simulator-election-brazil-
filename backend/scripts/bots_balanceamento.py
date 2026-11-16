"""Bots que jogam mandatos inteiros (48 meses) para achar desequilíbrios no motor.

Uso (na pasta backend):
    .venv/Scripts/python.exe scripts/bots_balanceamento.py                 # 6 partidas por estratégia
    .venv/Scripts/python.exe scripts/bots_balanceamento.py --partidas 20 --semente 7 --saida relatorio.json

Não muda o jogo: só mede. Cada estratégia joga com sementes diferentes; o relatório mostra a distribuição dos
indicadores no fim do mandato, quantas ações foram executadas ou bloqueadas e problemas como indicador fora da
faixa plausível, exceção inesperada ou estratégia que ganha sempre. Os limites de "plausível" são de design.
"""
from __future__ import annotations

import argparse
import json
import random
import statistics
import sys
import time
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    _s.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.engine import events as crises, powers, story  # noqa: E402
from app.engine.state import advance_state, new_game  # noqa: E402

METRICS = ("approval", "inflation", "unemployment", "gdp_growth", "institutional_trust", "integrity", "congress_support", "governability")
PLAUSIBLE = {"approval": (3, 97), "inflation": (-1, 30), "unemployment": (2, 25), "gdp_growth": (-6, 10), "institutional_trust": (3, 97), "integrity": (3, 97)}
EXPECTED_BLOCK = (PermissionError, RuntimeError, ValueError)


def candidates(state):
    return [a for a in powers.ACTIONS if powers.status(state, a)["available"]]


def choose(strategy: str, state, rng: random.Random):
    options = candidates(state)
    if strategy == "passivo" or not options:
        return None
    if strategy == "ativista":
        return rng.choice(options)
    if strategy == "governante":
        good = [a for a in options if sum(a["effects"].get(k, 0) for k in ("approval", "institutional_trust", "integrity", "gdp_growth")) > 0 and a["cost_bi"] <= 8]
        return rng.choice(good) if good else None
    if strategy == "cauteloso":
        safe = [a for a in options if a["cost_bi"] <= 3 and a["effects"].get("approval", 0) >= 0 and a["approval"] in {"decreto", "pl"}]
        return rng.choice(safe) if safe else None
    if strategy == "populista":
        ranked = sorted(options, key=lambda a: -a["effects"].get("approval", 0))
        return rng.choice(ranked[:5])
    raise ValueError(strategy)


def respond(strategy: str, state, rng: random.Random) -> None:
    """Responde a crises e acontecimentos pendentes, do jeito de cada estratégia. O passivo ignora tudo."""
    if strategy == "passivo":
        return
    for crisis in [c for c in state.get("active_crises", []) if c.get("status") == "active"]:
        options = crisis.get("options") or []
        if not options:
            continue
        if strategy == "ativista":
            pick = rng.choice(options)
        else:  # os demais escolhem a opção de maior efeito esperado na aprovação (governante também pesa o custo)
            pick = max(options, key=lambda o: o["forecast"].get("approval_pp", 0) - (0.5 * o.get("cost_bi", 0) if strategy == "governante" else 0))
        try:
            crises.respond_to_event(state, crisis["id"], pick["id"])
        except EXPECTED_BLOCK:
            pass
    for ev in list(state.get("story", {}).get("pending", [])):
        choices = ev.get("choices") or []
        if not choices:
            continue
        pick = rng.choice(choices) if strategy in ("ativista",) else choices[0] if strategy == "cauteloso" else rng.choice(choices[:2])
        try:
            story.respond(state, ev["id"], pick["id"])
        except EXPECTED_BLOCK:
            pass


def play(strategy: str, seed: int, months: int = 48) -> dict:
    rng = random.Random(seed)
    state = new_game()
    state.pop("setup_pending", None)
    state["campaign_seed"] = seed
    done, blocked, unexpected = 0, 0, []
    low = {m: float(state["metrics"].get(m, 0)) for m in METRICS}
    high = dict(low)
    for month in range(months):
        respond(strategy, state, rng)
        action = choose(strategy, state, rng)
        if action is not None:
            option = rng.choice(action["options"]) if action["options"] else None
            try:
                powers.execute(state, action["id"], option)
                done += 1
            except EXPECTED_BLOCK:
                blocked += 1
            except Exception as exc:  # noqa: BLE001 - o relatório existe para achar isto
                unexpected.append(f"{action['id']}: {type(exc).__name__}: {exc}"[:160])
        try:
            state, _ = advance_state(state, 30)
        except Exception as exc:  # noqa: BLE001
            unexpected.append(f"advance mês {month + 1}: {type(exc).__name__}: {exc}"[:160])
            break
        for m in METRICS:
            value = float(state["metrics"].get(m, 0))
            low[m], high[m] = min(low[m], value), max(high[m], value)
    final = {m: round(float(state["metrics"].get(m, 0)), 2) for m in METRICS}
    return {"strategy": strategy, "seed": seed, "final": final, "min": {m: round(v, 2) for m, v in low.items()}, "max": {m: round(v, 2) for m, v in high.items()},
            "actions_done": done, "actions_blocked": blocked, "unexpected": unexpected, "date": state["date"]}


def summarize(results: list[dict]) -> dict:
    out = {}
    for strategy in sorted({r["strategy"] for r in results}):
        rows = [r for r in results if r["strategy"] == strategy]
        out[strategy] = {m: {"media": round(statistics.mean(r["final"][m] for r in rows), 1), "min": min(r["final"][m] for r in rows), "max": max(r["final"][m] for r in rows)} for m in METRICS}
        out[strategy]["acoes_executadas"] = round(statistics.mean(r["actions_done"] for r in rows), 1)
        out[strategy]["acoes_bloqueadas"] = round(statistics.mean(r["actions_blocked"] for r in rows), 1)
        out[strategy]["partidas"] = len(rows)
    return out


def problems(results: list[dict]) -> list[str]:
    found = []
    for r in results:
        for m, (lo, hi) in PLAUSIBLE.items():
            if not lo <= r["final"][m] <= hi:
                found.append(f"{r['strategy']} semente {r['seed']}: {m} terminou em {r['final'][m]} (plausível {lo} a {hi})")
        for u in r["unexpected"]:
            found.append(f"{r['strategy']} semente {r['seed']}: exceção inesperada: {u}")
    by = {}
    for r in results:
        by.setdefault(r["strategy"], []).append(r["final"]["approval"])
    means = {s: statistics.mean(v) for s, v in by.items()}
    if means and max(means.values()) - min(means.values()) > 45:
        found.append(f"estratégias muito desiguais na aprovação final: {', '.join(f'{s} {v:.0f}' for s, v in means.items())}")
    for metric, minimum in (("inflation", 0.8), ("unemployment", 0.8), ("gdp_growth", 0.5)):
        values = {}
        for r in results:
            values.setdefault(r["strategy"], []).append(r["final"][metric])
        spread = max(statistics.mean(v) for v in values.values()) - min(statistics.mean(v) for v in values.values())
        if len(values) > 1 and spread < minimum:
            found.append(f"{metric} quase não responde ao jogador: as médias das estratégias diferem só {spread:.2f} (esperado pelo menos {minimum}). Os efeitos das ações são pequenos frente à deriva do motor")
    if "passivo" in means and "ativista" in means and means["passivo"] >= means["ativista"] + 10:
        found.append("governar sem fazer nada termina melhor que governar ativamente: revisar custos políticos das ações")
    return found


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--partidas", type=int, default=6, help="partidas por estratégia")
    parser.add_argument("--semente", type=int, default=1)
    parser.add_argument("--estrategias", default="passivo,ativista,cauteloso,populista,governante")
    parser.add_argument("--saida", help="grava o relatório completo em JSON")
    args = parser.parse_args()
    results, started = [], time.perf_counter()
    for strategy in args.estrategias.split(","):
        for k in range(args.partidas):
            results.append(play(strategy, args.semente * 1000 + k))
        print(f"{strategy}: {args.partidas} partidas prontas ({time.perf_counter() - started:.0f}s)", flush=True)
    summary = summarize(results)
    print("\n== Fim do mandato (média, mínimo e máximo)")
    header = f"{'estratégia':11}" + "".join(f"{m[:9]:>16}" for m in ("approval", "inflation", "unemployment", "gdp_growth", "institutional_trust"))
    print(header)
    for strategy, row in summary.items():
        cells = "".join(f"{row[m]['media']:>7.1f} ({row[m]['min']:.0f}-{row[m]['max']:.0f})".rjust(16) for m in ("approval", "inflation", "unemployment", "gdp_growth", "institutional_trust"))
        print(f"{strategy:11}{cells}   ações {row['acoes_executadas']} feitas, {row['acoes_bloqueadas']} bloqueadas")
    issues = problems(results)
    print("\n== Problemas encontrados" if issues else "\n== Nenhum problema encontrado")
    for issue in issues[:40]:
        print(" -", issue)
    if args.saida:
        Path(args.saida).write_text(json.dumps({"resumo": summary, "problemas": issues, "partidas": results}, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nRelatório completo em {args.saida}")
    return 1 if any("exceção inesperada" in i for i in issues) else 0


if __name__ == "__main__":
    raise SystemExit(main())
