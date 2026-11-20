"""Promessas de campanha: registro, regra de evidência e cobrança depois de um ano no cargo.

Parte do ciclo de carreira (antes tudo em career.py; ver career.py, que reexporta estes nomes).
"""
from __future__ import annotations


import re
from datetime import date, timedelta
from typing import Any

from .career_base import (
    ISSUES,
    LEGISLATIVE_OFFICES,
    PROMISE_LANGUAGE_PATTERNS,
    PROMISE_LIMIT,
    PROMISE_MINIMUM_CHANGE,
    PROMISE_OUTCOMES,
    PROMISE_REVIEW_DAYS,
    SERVICE_AREAS,
    _clamp,
    _norm,
)
from .career_access import (
    is_career_governing,
)


def _promise_rule(issue: str, message: str, career: dict[str, Any]) -> dict[str, Any]:
    """Select a visible, deterministic piece of in-game evidence for a promise."""
    normalized = _norm(message)
    if issue == "economia" and career.get("office") == "presidente":
        metric = next((key for terms, key in (
            ({"inflacao", "preco", "precos", "custo de vida"}, "inflation"),
            ({"desemprego", "emprego", "trabalho"}, "unemployment"),
            ({"crescimento", "pib", "economia"}, "gdp_growth"),
        ) if any(_norm(term) in normalized for term in terms)), None)
        if metric:
            metric_labels = {"inflation": "inflação anual", "unemployment": "desemprego", "gdp_growth": "crescimento do PIB"}
            direction = "up" if metric == "gdp_growth" else "down"
            return {"kind": "metric", "key": metric, "label": metric_labels[metric], "direction": direction,
                    "minimum_change": 0.2, "rule": f"o indicador simulado de {metric_labels[metric]} precisa melhorar ao menos 0,2 ponto."}
    if issue == "seguranca" and career.get("office") == "prefeito":
        return {"kind": "unsupported", "key": "security", "label": "segurança municipal",
                "direction": "evidence", "minimum_change": 0.0,
                "rule": "o recorte atual ainda não modela um indicador municipal de segurança; a promessa será registrada, sem avaliação ou penalidade."}
    outcome = PROMISE_OUTCOMES.get(issue)
    if outcome and career.get("office") not in LEGISLATIVE_OFFICES:
        return {"kind": "outcome", "key": outcome, "label": SERVICE_AREAS[outcome]["label"],
                "direction": "up", "minimum_change": PROMISE_MINIMUM_CHANGE[outcome],
                "rule": f"o indicador de {SERVICE_AREAS[outcome]['label'].lower()} precisa subir ao menos {PROMISE_MINIMUM_CHANGE[outcome]:.1f} pontos com uma entrega concluída."}
    if issue == "integridade":
        evidence = "prestação de contas pública" if career.get("office") not in LEGISLATIVE_OFFICES else "fiscalização concluída ou projeto relacionado aprovado"
        return {"kind": "integrity", "key": "trust", "label": "confiança e transparência", "direction": "up",
                "minimum_change": 1.5, "rule": f"é preciso registrar {evidence} depois da promessa e preservar ao menos 1,5 ponto de confiança."}
    issue_label = ISSUES[issue]["label"].lower()
    return {"kind": "bill", "key": issue, "label": f"entrega legislativa em {issue_label}", "direction": "evidence",
            "minimum_change": 1.0, "rule": f"ao menos um projeto relacionado a {issue_label} precisa ser aprovado na simulação."}


def _promise_baseline(state: dict[str, Any], career: dict[str, Any], rule: dict[str, Any]) -> float:
    rule_kind = rule.get("kind", rule.get("metric_kind"))
    rule_key = rule.get("key", rule.get("metric_key"))
    if rule_kind == "metric":
        return float(state.get("metrics", {}).get(rule_key, state.get("social_indicators", {}).get(rule_key, 0.0)))
    governance = career.get("governance") or {}
    if rule_kind == "outcome":
        return float((governance.get("outcomes") or {}).get(rule_key, 50.0))
    return float(governance.get("trust", 50.0))


def _is_explicit_promise(message: str) -> bool:
    normalized = _norm(message)
    if re.search(r"\bnao\s+(?:(?:vou|vamos)\s+|prometo\b|prometemos\b|me comprometo\b|nos comprometemos\b)", normalized):
        return False
    return any(re.search(pattern, normalized) for pattern in PROMISE_LANGUAGE_PATTERNS)


def _record_campaign_promise(state: dict[str, Any], career: dict[str, Any], issue: str,
                             message: str) -> dict[str, Any] | None:
    if not _is_explicit_promise(message):
        return None
    promises = career.setdefault("campaign_promises", [])
    election_cycle = career.get("election_date")
    if any(item.get("status") == "pending" and item.get("issue") == issue
           and item.get("election_date") == election_cycle for item in promises):
        return {"status": "not_recorded", "issue_label": ISSUES[issue]["label"],
                "statement": message.strip()[:600],
                "evidence_rule": "Já existe uma promessa pendente sobre esse tema neste ciclo eleitoral.",
                "review_date": None}
    if sum(item.get("status") == "pending" for item in promises) >= PROMISE_LIMIT:
        return {"status": "not_recorded", "issue_label": ISSUES[issue]["label"],
                "statement": message.strip()[:600],
                "evidence_rule": f"O limite de {PROMISE_LIMIT} promessas pendentes já foi atingido.",
                "review_date": None}
    today = date.fromisoformat(state["date"])
    governing = is_career_governing(career, today)
    rule = _promise_rule(issue, message, career)
    office_start = career.get("office_start") if governing else None
    review_date = None
    baseline = None
    reference_date = None
    if governing:
        review_day = today + timedelta(days=PROMISE_REVIEW_DAYS)
        term_end = date.fromisoformat(career.get("term_end", review_day.isoformat()))
        review_date = min(review_day, term_end).isoformat()
        baseline = _promise_baseline(state, career, rule)
        reference_date = today.isoformat()
    promise = {
        "id": f"pledge-{today.isoformat()}-{issue}-{len(promises) + 1}",
        "date": today.isoformat(), "election_date": election_cycle,
        "issue": issue, "issue_label": ISSUES[issue]["label"],
        "statement": message.strip()[:600], "status": "pending",
        "review_date": review_date, "reference_date": reference_date,
        "baseline": baseline, "metric_kind": rule["kind"], "metric_key": rule["key"],
        "metric_label": rule["label"], "direction": rule["direction"],
        "minimum_change": rule["minimum_change"], "evidence_rule": rule["rule"],
        "office": career.get("office"), "simulated": True,
    }
    promises.append(promise)
    career["campaign_promises"] = promises[-30:]
    return promise


def _activate_campaign_promises(state: dict[str, Any], career: dict[str, Any], office_start: date,
                                *, reset_existing: bool = False) -> None:
    for promise in career.get("campaign_promises", []):
        if promise.get("status") != "pending":
            continue
        review_date = promise.get("review_date")
        if review_date and not reset_existing:
            continue
        promise["reference_date"] = office_start.isoformat()
        promise["baseline"] = _promise_baseline(state, career, promise)
        promise["office"] = career.get("office")
        limit = office_start + timedelta(days=PROMISE_REVIEW_DAYS)
        term_end = date.fromisoformat(career.get("term_end", limit.isoformat()))
        promise["review_date"] = min(limit, term_end).isoformat()
        promise["activated_at"] = office_start.isoformat()
        promise["baseline_source"] = "indicador registrado na posse simulada"


def _promise_evidence(state: dict[str, Any], career: dict[str, Any], promise: dict[str, Any]) -> tuple[float, bool]:
    rule_kind = promise.get("metric_kind")
    key = promise.get("metric_key")
    reference_date = promise.get("reference_date") or promise.get("date", "9999-12-31")
    if rule_kind == "metric":
        observed = float(state.get("metrics", {}).get(key, state.get("social_indicators", {}).get(key, 0.0)))
        baseline = float(promise.get("baseline", observed))
        delta = observed - baseline if promise.get("direction") == "up" else baseline - observed
        return round(delta, 3), delta >= float(promise.get("minimum_change", 0.2))
    governance = career.get("governance") or {}
    if rule_kind == "outcome":
        observed = float((governance.get("outcomes") or {}).get(key, promise.get("baseline", 50.0)))
        baseline = float(promise.get("baseline", observed))
        delta = observed - baseline
        return round(delta, 2), delta >= float(promise.get("minimum_change", 1.0))
    actions = list(governance.get("actions", []))
    reports = list(governance.get("public_reports", []))
    if rule_kind == "integrity":
        relevant_reports = [item for item in reports if item.get("date", "") > reference_date]
        relevant_oversight = [item for item in actions if item.get("kind") == "oversight"
                              and item.get("status") == "concluded"
                              and (item.get("completed_at") or item.get("due_date") or "") > reference_date]
        trust_delta = float(governance.get("trust", 50.0)) - float(promise.get("baseline", 50.0))
        return round(trust_delta, 2), bool(relevant_reports or relevant_oversight) and trust_delta >= float(promise.get("minimum_change", 1.5))
    terms = [_norm(term) for term in ISSUES.get(key, {}).get("terms", set())]
    approved = [item for item in actions if item.get("kind") == "bill" and item.get("status") == "approved"
                and (item.get("completed_at") or item.get("due_date") or "") > reference_date
                and any(term and term in _norm(str(item.get("title", ""))) for term in terms)]
    return (1.0 if approved else 0.0), bool(approved)


def _review_campaign_promises(state: dict[str, Any], career: dict[str, Any], before: date,
                              after: date) -> list[str]:
    messages: list[str] = []
    governance = career.get("governance") or {}
    for promise in career.get("campaign_promises", []):
        if promise.get("status") != "pending" or not promise.get("review_date"):
            continue
        review_date = date.fromisoformat(promise["review_date"])
        if not before < review_date <= after:
            continue
        office_start = career.get("office_start")
        term_end = career.get("term_end")
        if not office_start or review_date < date.fromisoformat(office_start):
            continue
        if term_end and review_date > date.fromisoformat(term_end):
            continue
        if promise.get("metric_kind") == "unsupported":
            promise.update({"status": "not_assessed", "reviewed_on": review_date.isoformat(),
                            "observed_change": 0.0, "review_office": career.get("office"), "simulated": True})
            territory = career.get("municipality") or career.get("state_name", "")
            state.setdefault("simulated_news", []).insert(0, {
                "id": f"{promise['id']}-review", "date": review_date.isoformat(),
                "title": f"Compromisso sem indicador municipal: {promise['issue_label']}",
                "region": territory,
                "description": f"A promessa foi registrada, mas {promise['evidence_rule']} Nenhum efeito de reputação foi aplicado.",
                "simulated": True,
            })
            promise["news_id"] = f"{promise['id']}-review"
            messages.append(f"O simulador registrou a promessa sobre {promise['issue_label'].lower()}, mas ainda não dispõe de indicador municipal para avaliá-la.")
            continue
        delta, fulfilled = _promise_evidence(state, career, promise)
        promise.update({"status": "fulfilled" if fulfilled else "questioned", "reviewed_on": review_date.isoformat(),
                        "observed_change": delta, "review_office": career.get("office"),
                        "simulated": True})
        impact = 1.2 if fulfilled else -1.2
        career["reputation"] = _clamp(float(career.get("reputation", 50.0)) + impact)
        career["poll_support"] = round(_clamp(float(career.get("poll_support", 50.0)) + impact * .6), 2)
        for group in ISSUES[promise["issue"]]["groups"]:
            career.setdefault("group_support", {})[group] = _clamp(
                career.get("group_support", {}).get(group, 45.0) + impact * .4
            )
        territory = career.get("municipality") or ("Brasil" if career.get("office") == "presidente" else career.get("state_name", ""))
        if fulfilled:
            headline = f"Promessa de campanha cumprida: {promise['issue_label']}"
            if promise.get("metric_kind") == "bill":
                evidence_text = "A simulação registrou a aprovação de uma proposta legislativa relacionada ao tema."
            elif promise.get("metric_kind") == "integrity":
                evidence_text = f"A confiança simulada variou {delta:+.1f} ponto(s) e houve uma ação pública de transparência ou fiscalização."
            else:
                evidence_text = f"O indicador de {promise['metric_label']} avançou {delta:.1f} ponto(s) desde a referência registrada."
            description = f"A prestação de contas simulada registra o compromisso: {promise['statement']} {evidence_text}"
            messages.append(f"Cobrança simulada concluída: a promessa sobre {promise['issue_label'].lower()} foi atendida.")
        else:
            headline = f"Cobrança de campanha: {promise['issue_label']}"
            description = (f"A promessa registrada foi: {promise['statement']} "
                           f"A simulação não encontrou evidência suficiente até {review_date.strftime('%d/%m/%Y')}: {promise['evidence_rule']}")
            messages.append(f"Cobrança simulada: não houve evidência suficiente para a promessa sobre {promise['issue_label'].lower()}.")
        state.setdefault("simulated_news", []).insert(0, {
            "id": f"{promise['id']}-review", "date": review_date.isoformat(), "title": headline,
            "region": territory, "description": description, "simulated": True,
        })
        promise["news_id"] = f"{promise['id']}-review"
    state["simulated_news"] = state.get("simulated_news", [])[:20]
    return messages
