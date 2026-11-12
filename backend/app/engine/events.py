"""Deterministic monthly event generator and consequence resolver.

News, people, incidents and outcomes are fictional elements of the game. A
month is drawn from the save seed so advancing one day or several days gives
the same event sequence.
"""
from __future__ import annotations

import random
from copy import deepcopy
from datetime import date, timedelta
from typing import Any

from .difficulty import event_severity_weights, get_difficulty
from .fiscal import record_one_off_spending


def ensure_event_state(state: dict[str, Any]) -> None:
    state.setdefault("campaign_seed", 203001)
    state.setdefault("active_crises", [])
    state.setdefault("simulated_news", [])
    state.setdefault("event_history", [])
    state.setdefault("event_memories", [])
    state.setdefault("event_months_checked", [])


EVENTS: dict[str, dict[str, Any]] = {
    "flood": {"title": "Enchentes no Sul", "region": "Sul", "region_keys": ["sul"],
        "description": "Chuvas intensas interrompem estradas, serviços e parte da produção regional.",
        "monthly": {"gdp_growth": -.035, "regional_infrastructure": -.7, "approval": -.12},
        "regional_monthly": {"infrastructure": -.7, "economic_activity": -.55, "support": -.12},
        "options": [("rescue", "Mobilizar resposta e abrigos", 2.0), ("rebuild", "Priorizar estradas e reconstrução", 4.0), ("coordinate", "Coordenar estados e publicar plano", .5)]},
    "drought": {"title": "Seca pressiona a produção no Nordeste", "region": "Nordeste", "region_keys": ["nordeste"],
        "description": "Chuva abaixo da média afeta reservatórios, pequenas lavouras e o preço de alimentos em municípios do semiárido.",
        "monthly": {"gdp_growth": -.025, "inflation": .055, "rural_resilience": -.7, "approval": -.1},
        "regional_monthly": {"economic_activity": -.45, "support": -.1},
        "options": [("water", "Levar água e apoio técnico às áreas críticas", 1.8), ("coordinate", "Coordenar estados e publicar mapa de abastecimento", .45), ("wait", "Aguardar a próxima previsão de chuva", 0.0)]},
    "health": {"title": "Aumento de casos pressiona unidades de saúde", "region": "Nordeste e Sudeste", "region_keys": ["nordeste", "sudeste"],
        "description": "A procura por atendimento supera a capacidade de algumas unidades, e municípios cobram equipes e insumos.",
        "monthly": {"health": -.7, "approval": -.12, "gdp_growth": -.012},
        "regional_monthly": {"support": -.08},
        "options": [("teams", "Enviar equipes móveis e insumos às unidades lotadas", 1.5), ("protocol", "Publicar protocolo e apoiar vigilância municipal", .35), ("wait", "Aguardar os dados consolidados", 0.0)]},
    "service_outage": {"title": "Falha interrompe um serviço público digital", "region": "Nacional", "region_keys": ["norte", "nordeste", "centro_oeste", "sudeste", "sul"],
        "description": "Uma falha técnica suspende agendamentos e consultas em parte da rede federal; o contrato de manutenção entra em revisão.",
        "monthly": {"institutional_trust": -.5, "integrity": -.18, "approval": -.1},
        "options": [("restore", "Ativar contingência e reparar os sistemas", .75), ("audit", "Auditar o contrato e publicar prazo de retorno", .25), ("wait", "Aguardar a contratada normalizar o serviço", 0.0)]},
    "integrity": {"title": "Contrato público entra sob questionamento", "region": "Nacional", "region_keys": ["norte", "nordeste", "centro_oeste", "sudeste", "sul"],
        "description": "Documentos de um contrato federal geram dúvidas sobre preço e fiscalização. Ainda não há conclusão nem culpa atribuída.",
        "monthly": {"integrity": -.65, "institutional_trust": -.4, "approval": -.08},
        "options": [("independent_audit", "Abrir apuração independente e preservar documentos", .3), ("publish", "Publicar contrato, aditivos e responsáveis pela fiscalização", .05), ("wait", "Aguardar a conclusão interna", 0.0)]},
}


def _options_with_forecasts(state: dict[str, Any], kind: str, severity: int,
                            options: list[tuple[str, str, float]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for key, label, cost in options:
        preview_state = deepcopy(state)
        cost, gdp, approval, infrastructure, explanation = _resolve_effects(
            preview_state, {"kind": kind, "severity": severity}, key)
        follow_up = "Se adiar, este problema pode voltar à pauta em cerca de 90 dias." if key == "wait" and kind in FOLLOW_UP_TITLES else "Encerrar a crise interrompe o acúmulo dos efeitos mensais."
        result.append({"id": key, "label": label, "cost_bi": cost,
                       "forecast": {"gdp_pp": round(gdp, 2), "approval_pp": round(approval, 2),
                                    "infrastructure": round(infrastructure, 2), "summary": explanation,
                                    "future": follow_up}})
    return result


def _make_event(state: dict[str, Any], current: date, rng: random.Random,
                event_pressure: float = 1.0) -> dict[str, Any]:
    metrics = state.get("metrics", {})
    outcomes = state.get("budget", {}).get("outcomes", {})
    kinds = list(EVENTS)
    weights_by_kind = {kind: 20 for kind in kinds}
    regional = state.get("regional_metrics", {})
    south = regional.get("sul", {})
    northeast = regional.get("nordeste", {})
    # The event draw is seeded per save and month, but climate and service
    # indicators change the odds instead of making every month equivalent.
    if current.month in {10, 11, 12, 1, 2, 3}:
        weights_by_kind["flood"] += 18
    if float(south.get("infrastructure", 70)) < 70:
        weights_by_kind["flood"] += min(18, int((70 - float(south.get("infrastructure", 70))) * .6))
    if current.month in {8, 9, 10, 11, 12}:
        weights_by_kind["drought"] += 16
    if float(outcomes.get("rural_resilience", 50)) < 50 or float(northeast.get("economic_activity", 80)) < 65:
        weights_by_kind["drought"] += 12
    if current.month in {1, 2, 3, 4}:
        weights_by_kind["health"] += 12
    if float(metrics.get("integrity", 70)) < 45:
        weights_by_kind["integrity"] += 16
    if float(outcomes.get("health", 50)) < 45:
        weights_by_kind["health"] += 12
    if float(metrics.get("regional_infrastructure", 85)) < 50:
        weights_by_kind["service_outage"] += 12
    weights = [weights_by_kind[kind] for kind in kinds]
    kind = rng.choices(kinds, weights=weights, k=1)[0]
    template = EVENTS[kind]
    severity = 1 + rng.choices([0, 1, 2], weights=event_severity_weights(event_pressure), k=1)[0]
    options = _options_with_forecasts(state, kind, severity, template["options"])
    return {"id": f"{kind}-{current:%Y%m}", "kind": kind, "date": current.isoformat(), "title": template["title"],
            "region": template["region"], "severity": severity, "status": "active", "days_active": 0,
            "region_keys": template.get("region_keys", []), "regional_monthly_effects": template.get("regional_monthly", {}),
            "description": f"Evento fictício do simulador: {template['description']}", "monthly_effects": template["monthly"],
            "options": options, "simulated": True}


FOLLOW_UP_TITLES = {
    "drought": "A seca retorna à pauta após a resposta insuficiente",
    "health": "A fila na saúde volta a pressionar o governo",
    "service_outage": "Nova falha reabre a crise do serviço digital",
    "integrity": "Novos documentos reabrem o questionamento do contrato",
}


def _make_follow_up(state: dict[str, Any], current: date, rng: random.Random) -> dict[str, Any] | None:
    active_kinds = {item.get("kind") for item in state.get("active_crises", []) if item.get("status") == "active"}
    due = [item for item in state["event_memories"]
           if item.get("status") == "pending" and item.get("kind") in FOLLOW_UP_TITLES
           and date.fromisoformat(item["due_date"]) <= current and item.get("kind") not in active_kinds
           and int(item.get("follow_up_count", 0)) < int(item.get("max_follow_ups", 2))]
    if not due:
        return None
    memory = sorted(due, key=lambda item: (item["due_date"], item["id"]))[0]
    event_pressure = get_difficulty(state.get("difficulty", "normal"))["event_pressure"]
    if rng.random() >= min(.9, .62 * event_pressure):
        return None
    template = EVENTS[memory["kind"]]
    count = int(memory.get("follow_up_count", 0)) + 1
    severity = max(1, int(memory.get("severity", 1)) - (count - 1))
    options = _options_with_forecasts(state, memory["kind"], severity, template["options"])
    memory["status"] = "active"
    memory["follow_up_count"] = count
    event_id = f"{memory['kind']}-retorno-{current:%Y%m}-{count}"
    return {"id": event_id, "kind": memory["kind"], "date": current.isoformat(),
            "title": FOLLOW_UP_TITLES[memory["kind"]], "region": template["region"],
            "severity": severity, "status": "active",
            "region_keys": template.get("region_keys", []), "regional_monthly_effects": template.get("regional_monthly", {}),
            "description": (f"Evento fictício do simulador: o problema voltou à pauta depois da resposta dada a "
                            f"'{memory['original_title']}' em {memory['source_date']}. A equipe precisa decidir se corrige a causa."),
            "monthly_effects": template["monthly"], "options": options, "simulated": True,
            "follow_up_of": memory["id"], "follow_up_number": count}


def _add_news(state: dict[str, Any], event: dict[str, Any]) -> None:
    state["simulated_news"].insert(0, {"id": event["id"], "date": event["date"], "title": event["title"],
        "region": event.get("region", "Nacional"), "description": event["description"], "simulated": True})
    state["simulated_news"] = state["simulated_news"][:20]
    state["event_history"].append({"id": event["id"], "date": event["date"], "title": event["title"], "outcome": "em andamento"})
    state["event_history"] = state["event_history"][-100:]


CRISIS_MAX_DAYS = 180


def _adjust(target: dict[str, Any], key: str, delta: float, lower: float = 0, upper: float = 100) -> None:
    target[key] = round(max(lower, min(upper, float(target.get(key, 50)) + delta)), 2)


def process_events(state: dict[str, Any], before: date, after: date) -> list[str]:
    ensure_event_state(state)
    messages: list[str] = []
    cursor = date(before.year, before.month, 1)
    if cursor <= before:
        cursor = (cursor.replace(day=28) + timedelta(days=4)).replace(day=1)
    while cursor <= after:
        month_key = cursor.strftime("%Y-%m")
        if month_key not in state["event_months_checked"]:
            state["event_months_checked"].append(month_key)
            rng = random.Random(f"{state['campaign_seed']}:monthly-event:{month_key}")
            pressure = get_difficulty(state.get("difficulty", "normal"))["event_pressure"]
            chance = max(.05, min(.65, .24 * pressure))
            active_count = sum(item.get("status") == "active" for item in state["active_crises"])
            if active_count < 2 and rng.random() < chance:
                event = _make_follow_up(state, cursor, rng) or _make_event(state, cursor, rng, pressure)
                state["active_crises"].append(event)
                _add_news(state, event)
                messages.append(f"Evento simulado: {event['title'].lower()}.")
        cursor = (cursor.replace(day=28) + timedelta(days=4)).replace(day=1)

    for crisis in state["active_crises"]:
        if crisis.get("status") != "active":
            continue
        crisis_start = date.fromisoformat(crisis["date"])
        active_days = max(0, (after - max(before, crisis_start)).days)
        crisis["days_active"] = int(crisis.get("days_active", 0)) + active_days
        if not active_days:
            continue
        scale = active_days / 30 * float(crisis.get("severity", 1))
        for key, monthly_delta in crisis.get("monthly_effects", {}).items():
            if key in {"health", "rural_resilience"}:
                target = state.setdefault("budget", {}).setdefault("outcomes", {})
                _adjust(target, key, monthly_delta * scale)
            elif key == "institutional_trust":
                _adjust(state.setdefault("metrics", {}), key, monthly_delta * scale)
            else:
                floor = -10 if key == "gdp_growth" else .5 if key == "inflation" else 0
                _adjust(state.setdefault("metrics", {}), key, monthly_delta * scale, floor, 100)
        regional = state.setdefault("regional_metrics", {})
        for region_key in crisis.get("region_keys", []):
            region = regional.setdefault(region_key, {"support": 50, "infrastructure": 70, "economic_activity": 80})
            for key, monthly_delta in crisis.get("regional_monthly_effects", {}).items():
                maximum = 150 if key == "economic_activity" else 100
                _adjust(region, key, monthly_delta * scale, 0, maximum)
        # Uma crise sem resposta não drena o país para sempre: depois de seis meses ela perde força
        # (a pressão se dissipa), mas deixa o registro de que o governo não agiu.
        if int(crisis.get("days_active", 0)) >= CRISIS_MAX_DAYS:
            crisis["status"] = "expired"
            for entry in state.get("event_history", []):
                if entry.get("id") == crisis["id"]:
                    entry["outcome"] = "encerrada sem resposta do governo"
            messages.append(f"A crise perdeu força depois de seis meses sem resposta: {crisis['title'].lower()}.")
    return messages


def _resolve_effects(state: dict[str, Any], crisis: dict[str, Any], choice: str) -> tuple[float, float, float, float, str]:
    kind = crisis.get("kind", "flood")
    severity = float(crisis.get("severity", 1))
    effects: dict[tuple[str, str], tuple[float, float, float, float, str]] = {
        ("flood", "rescue"): (2.0, .10, 1.5, 2, "Equipes de resposta e abrigos foram mobilizados; perdas e interrupções caem."),
        ("flood", "rebuild"): (4.0, .30, 1.0, 8, "Reconstrução prioritária acelerou a recuperação de estradas e da atividade regional."),
        ("flood", "coordinate"): (.5, .06, .7, 3, "Estados coordenam abrigos, rotas e informação; a recuperação será mais lenta, mas organizada."),
        ("drought", "water"): (1.8, .13, 1.25, 0, "Apoio técnico e abastecimento chegaram às áreas prioritárias; a pressão sobre produção e preços diminui."),
        ("drought", "coordinate"): (.45, .05, .65, 0, "Estados coordenam reservatórios e divulgam o mapa de abastecimento; a recuperação será gradual."),
        ("health", "teams"): (1.5, .04, 1.1, 0, "Equipes móveis e insumos aliviaram as unidades com maior fila; o atendimento começa a normalizar."),
        ("health", "protocol"): (.35, .02, .55, 0, "Vigilância e protocolo foram integrados aos municípios, com efeito mais lento e abrangente."),
        ("service_outage", "restore"): (.75, .03, .9, 0, "Contingência e reparo restabeleceram o serviço; o contrato segue sob acompanhamento."),
        ("service_outage", "audit"): (.25, .01, .6, 0, "A auditoria e o cronograma de retorno foram publicados; a normalização será mais lenta e transparente."),
        ("integrity", "independent_audit"): (.3, 0, .75, 0, "Apuração independente preservou documentos e publicou o escopo; nenhuma responsabilidade foi presumida."),
        ("integrity", "publish"): (.05, 0, .55, 0, "Contrato, aditivos e responsáveis pela fiscalização foram publicados para controle social."),
        ("drought", "wait"): (0, 0, 0, 0, "O governo aguarda a próxima previsão; os danos acumulados permanecem."),
        ("health", "wait"): (0, 0, 0, 0, "O governo aguarda dados consolidados; a fila e a pressão sobre as unidades permanecem."),
        ("service_outage", "wait"): (0, 0, 0, 0, "O governo aguarda a contratada; o serviço e a confiança seguem sob pressão."),
        ("integrity", "wait"): (0, 0, 0, 0, "A apuração aguarda conclusão interna; as dúvidas seguem sem resposta pública."),
    }
    selected = effects.get((kind, choice))
    if not selected:
        raise ValueError("Escolha de resposta inválida para este evento.")
    cost, gdp_scale, approval_scale, infra_scale, result = selected
    gdp = gdp_scale * severity
    approval = approval_scale * severity
    infrastructure = infra_scale * severity
    budget = state.setdefault("budget", {}).setdefault("outcomes", {})
    metrics = state.setdefault("metrics", {})
    if kind == "drought" and choice in {"water", "coordinate"}:
        _adjust(budget, "rural_resilience", 3.0 * severity if choice == "water" else 1.1 * severity)
        _adjust(metrics, "inflation", -.08 * severity if choice == "water" else -.025 * severity, .5, 100)
    elif kind == "health" and choice in {"teams", "protocol"}:
        _adjust(budget, "health", (3.2 if choice == "teams" else 1.2) * severity)
    elif kind == "service_outage":
        _adjust(metrics, "institutional_trust", 1.5 if choice == "restore" else .4)
        if choice == "audit":
            _adjust(metrics, "integrity", 1.5)
    elif kind == "integrity":
        _adjust(metrics, "integrity", 3.0 if choice == "independent_audit" else 1.8)
        if choice == "independent_audit":
            _adjust(metrics, "institutional_trust", 1.2)
    return cost, gdp, approval, infrastructure, result


def respond_to_event(state: dict[str, Any], event_id: str, choice: str) -> dict[str, Any]:
    ensure_event_state(state)
    crisis = next((item for item in state["active_crises"] if item["id"] == event_id and item.get("status") == "active"), None)
    if not crisis:
        raise ValueError("Este evento não está mais ativo.")
    cost, gdp, approval, infrastructure, result = _resolve_effects(state, crisis, choice)
    record_one_off_spending(state, cost)
    metrics = state.setdefault("metrics", {})
    _adjust(metrics, "gdp_growth", gdp, -10, 20)
    _adjust(metrics, "approval", approval)
    _adjust(metrics, "regional_infrastructure", infrastructure)
    for region_key in crisis.get("region_keys", []):
        region = state.setdefault("regional_metrics", {}).setdefault(region_key, {"support": 50, "infrastructure": 70, "economic_activity": 80})
        _adjust(region, "support", approval * .65)
        if infrastructure:
            _adjust(region, "infrastructure", infrastructure, 0, 100)
    crisis["status"] = "contained"
    crisis["response"] = choice
    crisis["resolved_date"] = state["date"]
    follow_up = crisis.get("follow_up_of")
    if follow_up:
        memory = next((item for item in state["event_memories"] if item.get("id") == follow_up), None)
        if memory:
            if choice == "wait" and int(memory.get("follow_up_count", 0)) < int(memory.get("max_follow_ups", 2)):
                memory["status"] = "pending"
                memory["due_date"] = (date.fromisoformat(state["date"]) + timedelta(days=90)).isoformat()
            else:
                memory["status"] = "closed"
                memory["closed_date"] = state["date"]
    elif choice == "wait" and crisis.get("kind") in FOLLOW_UP_TITLES:
        state["event_memories"].append({"id": event_id, "kind": crisis["kind"], "original_title": crisis["title"],
            "source_date": crisis["date"], "due_date": (date.fromisoformat(state["date"]) + timedelta(days=90)).isoformat(),
            "severity": int(crisis.get("severity", 1)), "follow_up_count": 0, "max_follow_ups": 2, "status": "pending"})
        state["event_memories"] = state["event_memories"][-50:]
    for item in state["event_history"]:
        if item["id"] == event_id:
            item["outcome"] = result
    state.setdefault("simulated_news", []).insert(0, {"id": f"response-{event_id}", "date": state["date"],
        "title": f"Resposta: {crisis['title']}", "region": crisis.get("region", "Nacional"),
        "description": result, "simulated": True})
    state["simulated_news"] = state["simulated_news"][:20]
    return {"result": result, "cost_bi": cost, "gdp_delta": gdp, "approval_delta": approval,
            "regional_infrastructure_delta": infrastructure, "simulated": True}
