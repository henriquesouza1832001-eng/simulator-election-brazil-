"""Abstract electoral-integrity rules for the fictional political simulation.

Irregular conduct is represented only as a high-level game choice. The engine
does not describe real-world methods for breaking election law.
"""
from __future__ import annotations

import random
from typing import Any


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, float(value)))


def electoral_oversight(state: dict[str, Any]) -> dict[str, float]:
    metrics = state.get("metrics", {})
    institutions = state.get("institutions", {})
    appointments = state.get("appointments", {}).get("judiciary", {})
    confirmed = appointments.get("confirmed", [])
    independence_scores = [float(item.get("independence", 65)) for item in confirmed if item.get("independence") is not None]
    judicial_independence = sum(independence_scores) / len(independence_scores) if independence_scores else 65.0
    integrity = float(metrics.get("integrity", 60))
    resistance = float(institutions.get("institutional_resistance", 50))
    trust = float(metrics.get("institutional_trust", 50))
    detection = _clamp(15 + integrity * .21 + resistance * .16 + trust * .09 + judicial_independence * .12, 12, 82)
    return {
        "integrity": round(_clamp(integrity), 1),
        "institutional_resistance": round(_clamp(resistance), 1),
        "judicial_independence": round(_clamp(judicial_independence), 1),
        "detection_pct": round(detection, 1),
    }


def campaign_conduct_preview(state: dict[str, Any], campaign: dict[str, Any]) -> dict[str, Any]:
    conduct = campaign.get("conduct") or {}
    oversight = electoral_oversight(state)
    attempts = int(conduct.get("attempts", 0))
    detected = int(conduct.get("detected", 0))
    judicial_factor = .55 + oversight["judicial_independence"] / 200
    review_pct = min(78.0, (attempts * 8 + detected * 14) * judicial_factor)
    review_if_not_detected = min(78.0, ((attempts + 1) * 8 + detected * 14) * judicial_factor)
    review_if_detected = min(78.0, ((attempts + 1) * 8 + (detected + 1) * 14) * judicial_factor)
    return {
        "options": [
            {"key": "regular", "label": "Conduta dentro das regras", "summary": "Sem risco adicional de sanção eleitoral."},
            {"key": "irregular", "label": "Atalho irregular (simulação)", "summary": "Pode render apoio imediato, mas deixa exposição para fiscalização e julgamento eleitoral."},
        ],
        "detection_pct": oversight["detection_pct"],
        "review_pct": round(review_pct, 1),
        "review_if_not_detected_pct": round(review_if_not_detected, 1),
        "review_if_detected_pct": round(review_if_detected, 1),
        "attempts": attempts,
        "detected": detected,
        "notice": "Atalhos irregulares são abstrações fictícias; a tela não descreve métodos reais. Fiscalização e Justiça Eleitoral variam com a integridade institucional.",
    }


def resolve_campaign_conduct(state: dict[str, Any], campaign: dict[str, Any], conduct_key: str,
                             action_id: str) -> dict[str, Any]:
    if conduct_key not in {"regular", "irregular"}:
        raise ValueError("Escolha uma forma de conduzir a campanha disponível.")
    if conduct_key == "regular":
        return {"key": "regular", "label": "Conduta dentro das regras", "detected": False,
                "detection_pct": 0.0, "immediate_support_delta": 0.0, "summary": "A atividade foi registrada dentro das regras; não há risco eleitoral adicional."}

    preview = campaign_conduct_preview(state, campaign)
    data = campaign.setdefault("conduct", {"attempts": 0, "detected": 0, "election_penalty": 0.0, "history": []})
    data.setdefault("attempts", 0)
    data.setdefault("detected", 0)
    data.setdefault("election_penalty", 0.0)
    data.setdefault("history", [])
    rng = random.Random(f"{state.get('campaign_seed', 1)}:{state['date']}:{action_id}:electoral-integrity")
    detected = rng.random() * 100 < preview["detection_pct"]
    data["attempts"] += 1
    data["detected"] += int(detected)
    immediate_delta = -3.0 if detected else 0.6
    data["election_penalty"] = round(float(data["election_penalty"]) + (3.0 if detected else 1.0), 2)
    result = {
        "key": "irregular", "label": "Atalho irregular (simulação)", "detected": detected,
        "detection_pct": preview["detection_pct"], "immediate_support_delta": immediate_delta,
        "summary": ("Detectada: apoio cai 3 p.p. agora, confiança institucional cai e a penalidade eleitoral futura aumenta." if detected
                    else "Não detectada agora: apoio sobe apenas 0,6 p.p.; a exposição e a penalidade futura continuam registradas."),
    }
    data["history"].append({"date": state["date"], "activity_id": action_id, "detected": detected,
                            "detection_pct": preview["detection_pct"], "simulated": True})
    data["history"] = data["history"][-30:]
    metrics = state.setdefault("metrics", {})
    metrics["integrity"] = round(_clamp(float(metrics.get("integrity", 60)) - (.8 if detected else .4)), 1)
    if detected:
        metrics["institutional_trust"] = round(_clamp(float(metrics.get("institutional_trust", 50)) - .8), 1)
    result["election_review_pct"] = campaign_conduct_preview(state, campaign)["review_pct"]
    return result


def settle_campaign_conduct(state: dict[str, Any], campaign: dict[str, Any], seed: str) -> dict[str, Any]:
    data = campaign.get("conduct") or {}
    attempts = int(data.get("attempts", 0))
    detected = int(data.get("detected", 0))
    if not attempts:
        return {"attempts": 0, "detected": 0, "reviewed": False, "vote_penalty": 0.0, "review_pct": 0.0}
    preview = campaign_conduct_preview(state, campaign)
    review_pct = preview["review_pct"]
    rng = random.Random(f"{seed}:final-electoral-review")
    reviewed = rng.random() * 100 < review_pct
    penalty = float(data.get("election_penalty", attempts)) + (8.0 if reviewed else 0.0)
    return {"attempts": attempts, "detected": detected, "reviewed": reviewed,
            "vote_penalty": round(penalty, 1), "review_pct": review_pct}
