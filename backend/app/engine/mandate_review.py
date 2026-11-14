"""Balanço do mandato: o que mudou do primeiro ao último dia, o que foi decidido e uma nota geral.

Tudo vem do estado do jogo (indicadores, livro de previsto × realizado, CPIs, reguladores). A nota é uma regra fixa e
simples, não uma opinião de IA: cada critério vale pontos e o texto de cada linha cita o número que a gerou.
"""
from __future__ import annotations

from datetime import date
from typing import Any

# chave, rótulo, unidade, melhor quando (up/down)
TRACKED = [
    ("approval", "Aprovação do governo", "%", "up"),
    ("congress_support", "Base no Congresso", "%", "up"),
    ("institutional_trust", "Confiança institucional", "/100", "up"),
    ("integrity", "Integridade pública", "/100", "up"),
    ("gdp_growth", "Crescimento do PIB", "% a.a.", "up"),
    ("inflation", "Inflação", "% a.a.", "down"),
    ("unemployment", "Desemprego", "%", "down"),
    ("debt_gdp", "Dívida pública", "% do PIB", "down"),
]
TERM_DAYS = 1461


def tick(state: dict[str, Any], before: date, after: date) -> list[str]:
    """Guarda o ponto de partida na primeira passagem do tempo."""
    if "mandate_baseline" not in state and not state.get("setup_pending"):
        state["mandate_baseline"] = {"date": state["date"], "metrics": {k: float(state.get("metrics", {}).get(k, 0)) for k, *_ in TRACKED}}
    return []


def _score(state: dict[str, Any], base: dict[str, float]) -> tuple[int, list[str]]:
    m = state.get("metrics", {})
    notes: list[str] = []
    points = 0.0
    approval = float(m.get("approval", 50))
    points += min(30.0, approval * 0.4)
    notes.append(f"Aprovação final de {approval:.0f}%")
    integrity = float(m.get("integrity", 60))
    points += min(20.0, integrity * 0.25)
    trust = float(m.get("institutional_trust", 50))
    points += min(15.0, trust * 0.2)
    # economia: melhora em relação ao início
    for key, weight, better in (("gdp_growth", 4.0, "up"), ("unemployment", 4.0, "down"), ("inflation", 4.0, "down"), ("debt_gdp", 3.0, "down")):
        delta = float(m.get(key, 0)) - float(base.get(key, m.get(key, 0)))
        good = delta if better == "up" else -delta
        points += max(-weight, min(weight, good * (weight / 3.0)))
    points += 5.0  # chegou ao fim do mandato
    return max(0, min(100, round(points))), notes


def _letter(score: int) -> tuple[str, str]:
    for floor, letter, text in ((80, "A", "Mandato de destaque"), (65, "B", "Mandato sólido"), (50, "C", "Mandato regular"), (35, "D", "Mandato frágil")):
        if score >= floor:
            return letter, text
    return "E", "Mandato em crise"


def review(state: dict[str, Any]) -> dict[str, Any]:
    base = state.get("mandate_baseline")
    if not base:
        from .state import new_game  # partidas antigas: os valores iniciais do jogo são constantes
        initial = new_game().get("metrics", {})
        base = {"date": state.get("term_start", state["date"]), "metrics": {k: float(initial[k]) for k, *_ in TRACKED if k in initial}}
    m = state.get("metrics", {})
    rows = []
    for key, label, unit, better in TRACKED:
        start = base["metrics"].get(key)
        now = float(m.get(key, 0))
        delta = None if start is None else round(now - start, 2)
        good = None if delta is None or abs(delta) < 0.05 else (delta > 0) == (better == "up")
        rows.append({"key": key, "label": label, "unit": unit, "start": None if start is None else round(start, 1), "now": round(now, 1), "delta": delta, "good": good})
    ledger = state.get("ledger", [])
    settled = [e for e in ledger if e.get("status") not in ("em tramitação", None)]
    approved = [e for e in ledger if str(e.get("status", "")).startswith("aprovad")]
    rejected = [e for e in ledger if "rejeit" in str(e.get("status", "")) or "agravada" in str(e.get("status", ""))]
    cpis = state.get("cpis", [])
    score, notes = _score(state, base["metrics"])
    letter, headline = _letter(score)
    try:
        days = (date.fromisoformat(state["date"]) - date.fromisoformat(state.get("term_start", state["date"]))).days
    except ValueError:
        days = 0
    final = days >= TERM_DAYS - 1 or state.get("office_status") == "former_president"
    return {"final": final, "days": days, "months": min(48, days // 30), "since": base["date"], "metrics": rows,
            "decisions": {"recorded": len(ledger), "settled": len(settled), "approved": len(approved), "setbacks": len(rejected)},
            "cpis": {"total": len(cpis), "against_government": len([c for c in cpis if c["author"] == "oposicao"]), "with_indictments": len([c for c in cpis if c.get("verdict") == "pede indiciamentos"])},
            "score": score, "letter": letter, "headline": headline, "notes": notes,
            "note": "Nota calculada por regra fixa: aprovação (até 30), integridade (20), confiança institucional (15), economia em relação ao início (até 15) e 5 por concluir o mandato."}
