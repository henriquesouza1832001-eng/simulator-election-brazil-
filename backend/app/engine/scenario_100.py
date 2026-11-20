"""Cenário curto "Os primeiros 100 dias": governo federal com a partida já em dificuldade e cinco metas para fechar o balanço.

É a porta de entrada do jogo (cerca de 15 minutos): ensina a ler os indicadores, assinar decisões, responder crises e negociar no
Congresso. Não cria regra nova: usa o mesmo motor da presidência, só muda o ponto de partida e passa a medir cinco metas.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any

SCENARIO_ID = "cem_dias"
APPROVAL_GOAL = 47.0
DAYS = 100
START_METRICS = {"approval": 44.0, "inflation": 6.1, "unemployment": 8.0, "congress_support": 41.0, "governability": 48.0,
                 "institutional_trust": 52.0, "primary_balance": -2.0}


def apply(state: dict[str, Any]) -> dict[str, Any]:
    """Põe a partida no ponto de partida do cenário: números piores que o normal e um calendário de 100 dias."""
    metrics = state.setdefault("metrics", {})
    metrics.update(START_METRICS)
    start = date.fromisoformat(str(state["date"]))
    state["scenario"] = {"id": SCENARIO_ID, "title": "Os primeiros 100 dias", "start": start.isoformat(), "end": (start + timedelta(days=DAYS)).isoformat(),
                         "status": "em_andamento", "result": None}
    state["campaign_name"] = state.get("campaign_name") or "Primeiros 100 dias"
    return state["scenario"]


def _decisions_since(state: dict[str, Any], start: str) -> int:
    return sum(1 for e in state.get("ledger") or [] if str(e.get("date") or "") >= start and e.get("source") == "presidencia")


def goals(state: dict[str, Any]) -> list[dict[str, Any]]:
    sc = state.get("scenario") or {}
    if sc.get("id") != SCENARIO_ID:
        return []
    m = state.get("metrics", {})
    start = sc["start"]
    aggravated = sum(1 for e in state.get("ledger") or [] if str(e.get("date") or "") >= start and "agrav" in str(e.get("status") or "").lower())
    cal = state.get("legislative_calendar") or {}
    sent = len(cal.get("pending_bills") or []) + int(cal.get("laws_enacted", 0))   # a votação leva mais de 100 dias: a meta é enviar e negociar, não esperar o resultado
    pending_overdue = sum(1 for c in (state.get("consequences") or {}).get("pending", []) if str(c.get("deadline") or "9999") < state["date"])
    n = lambda v: f"{float(v):.1f}".replace(".", ",")  # noqa: E731
    return [
        {"id": "aprovacao", "label": "Fechar os 100 dias com aprovação de 47% ou mais", "detail": "Decisões populares ajudam; a economia pesa todo mês.", "done": float(m.get("approval", 0)) >= APPROVAL_GOAL,
         "progress": f"{n(m.get('approval', 0))}% agora", "tab": "Indicadores"},
        {"id": "fiscal", "label": "Melhorar o resultado primário em pelo menos 0,1 ponto do PIB", "detail": "Use uma alavanca fiscal em Orçamento; a inflação e o mercado reagem às contas públicas.",
         "done": float(m.get("primary_balance", -99)) >= float(START_METRICS["primary_balance"]) + 0.1,
         "progress": f"{n(m.get('primary_balance', 0))}% do PIB (partida: {n(START_METRICS['primary_balance'])}%)", "tab": "Orçamento"},
        {"id": "decisoes", "label": "Assinar pelo menos 2 decisões do seu cargo", "detail": "Decretos e medidas provisórias estão em Medidas.", "done": _decisions_since(state, start) >= 2,
         "progress": f"{min(_decisions_since(state, start), 2)}/2", "tab": "Medidas"},
        {"id": "lei", "label": "Enviar um projeto de lei ao Congresso", "detail": "A votação leva meses: envie o projeto e negocie com as bancadas em Tramitação.", "done": sent >= 1,
         "progress": f"{sent} projeto(s) enviado(s)", "tab": "Tramitação"},
        {"id": "crises", "label": "Não deixar nenhuma crise sem resposta", "detail": "Responda dentro do prazo; sem resposta vale a pior opção.", "done": aggravated == 0 and pending_overdue == 0,
         "progress": "em dia" if aggravated == 0 and pending_overdue == 0 else f"{aggravated + pending_overdue} sem resposta", "tab": "Imprensa"},
    ]


GRADES = [(5, "Governo de primeira linha", "Você virou o jogo: os números e as instituições respondem."), (4, "Bom começo", "O governo ganhou fôlego; falta consolidar."),
          (3, "Começo instável", "Dá para melhorar: olhe as metas que ficaram de fora."), (2, "Início difícil", "A conta chegou. Revise as decisões e tente outro caminho."),
          (0, "Governo à deriva", "As crises mandaram na agenda. Leia 'Por que mudou?' e tente de novo.")]


def tick(state: dict[str, Any]) -> list[str]:
    """Ao chegar no 100º dia, fecha o balanço (uma vez)."""
    sc = state.get("scenario")
    if not sc or sc.get("id") != SCENARIO_ID or sc.get("status") != "em_andamento":
        return []
    if str(state["date"]) < sc["end"]:
        return []
    done = sum(1 for g in goals(state) if g["done"])
    title, text = next((t, x) for need, t, x in GRADES if done >= need)
    sc["status"] = "concluido"
    sc["result"] = {"done": done, "total": 5, "title": title, "text": text}
    return [f"Balanço dos 100 dias: {title} ({done} de 5 metas)."]


def public(state: dict[str, Any]) -> dict[str, Any] | None:
    sc = state.get("scenario")
    if not sc or sc.get("id") != SCENARIO_ID:
        return None
    start, end = date.fromisoformat(sc["start"]), date.fromisoformat(sc["end"])
    today = date.fromisoformat(str(state["date"]))
    day = min(DAYS, max(0, (today - start).days) + 1)   # mesma contagem do cabeçalho: o primeiro dia é o dia 1
    return {**sc, "days_left": max(0, (end - today).days), "day": day, "goals": goals(state)}
