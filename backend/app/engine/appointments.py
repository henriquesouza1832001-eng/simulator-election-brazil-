"""Simulated cabinet formation and Supreme Court nomination mechanics.

All names and profiles generated here are fictional game characters, not real
officeholders or claims about real people.
"""
from __future__ import annotations

import random
from datetime import date, timedelta
from typing import Any

from .ministries import MINISTRIES
from .difficulty import adjust_coalition_probability, get_difficulty
from .career import FAMILY_GROUP_EFFECTS, SPECTRUM_GROUP_EFFECTS
from .campaign import GROUP_LABELS, ensure_campaign_state, refresh_support

FIRST_NAMES = ["Ana", "Beatriz", "Caio", "Daniel", "Elisa", "Felipe", "Gabriela", "João", "Lívia", "Marcos", "Nádia", "Otávio", "Paula", "Rafael", "Sofia", "Tiago"]
LAST_NAMES = ["Andrade", "Barbosa", "Campos", "Duarte", "Ferraz", "Gomes", "Lacerda", "Menezes", "Nogueira", "Prado", "Queiroz", "Ramos", "Siqueira", "Tavares", "Vasconcelos"]
BACKGROUNDS = ["gestão pública", "universidade e pesquisa", "governo estadual", "administração municipal", "setor produtivo", "carreira técnica"]
LEGAL_SPECIALTIES = ["Direito constitucional", "Direito público", "Direito penal", "Direitos humanos", "Direito econômico", "Processo civil"]
POLITICAL_SPECTRA = ["esquerda", "centro_esquerda", "centro", "centro_direita", "direita"]
FAMILY_BACKGROUNDS = list(FAMILY_GROUP_EFFECTS)
SPECTRUM_LABELS = {
    "esquerda": "Esquerda", "centro_esquerda": "Centro-esquerda", "centro": "Centro",
    "centro_direita": "Centro-direita", "direita": "Direita",
}
FAMILY_LABELS = {
    "trabalhadora": "Família trabalhadora", "classe_media": "Classe média",
    "empreendedora": "Pequeno negócio", "rural": "Origem rural",
    "servidora_publica": "Serviço público", "politica": "Família ligada à política",
    "educadora": "Educação e cuidado", "oficios": "Ofícios e comércio",
    "lideranca_comunitaria": "Liderança comunitária",
}
CAREER_TO_CAMPAIGN_GROUP = {
    "trabalhadores": "trabalhadores", "empreendedores": "pequenos_negocios",
    "familias": "familias", "servidores": "servidores", "jovens": "juventude", "rural": "rural",
}
CABINET_AFFINITY_SCALE = 0.22


def _clamp(value: float) -> float:
    return round(max(0.0, min(100.0, float(value))), 1)


def _safe_id(text: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "-" for ch in text).strip("-")


def _political_profile(state: dict[str, Any], candidate_id: str) -> dict[str, Any]:
    rng = random.Random(f"{state.get('campaign_seed', 203001)}:{candidate_id}:political-profile")
    spectrum = rng.choice(POLITICAL_SPECTRA)
    family = rng.choice(FAMILY_BACKGROUNDS)
    raw_effects = dict(SPECTRUM_GROUP_EFFECTS[spectrum])
    for group, amount in FAMILY_GROUP_EFFECTS[family].items():
        raw_effects[group] = raw_effects.get(group, 0.0) + amount
    effects = {}
    for group, amount in raw_effects.items():
        campaign_group = CAREER_TO_CAMPAIGN_GROUP[group]
        scaled = round(max(-0.75, min(0.75, amount * CABINET_AFFINITY_SCALE)), 2)
        if scaled:
            effects[campaign_group] = scaled
    return {
        "spectrum": spectrum,
        "spectrum_label": SPECTRUM_LABELS[spectrum],
        "family_background": family,
        "family_label": FAMILY_LABELS[family],
        "group_effects": effects,
        "simulated": True,
    }


def _ensure_political_profile(state: dict[str, Any], candidate: dict[str, Any]) -> None:
    if not isinstance(candidate.get("political_profile"), dict):
        candidate["political_profile"] = _political_profile(state, str(candidate.get("id", "candidate")))


def _apply_candidate_group_effects(state: dict[str, Any], previous: dict[str, Any] | None,
                                   candidate: dict[str, Any]) -> dict[str, dict[str, float]]:
    campaign = ensure_campaign_state(state)
    support = campaign["group_support"]
    changes: dict[str, dict[str, float]] = {}
    for person, direction in ((previous, -1), (candidate, 1)):
        if not person:
            continue
        profile = person.get("political_profile") or {}
        for group, amount in profile.get("group_effects", {}).items():
            if group not in GROUP_LABELS:
                continue
            before = float(support.get(group, 50.0))
            after = max(0.0, min(100.0, before + direction * float(amount)))
            support[group] = round(after, 2)
            delta = round(after - before, 2)
            if delta:
                changes.setdefault(group, {"label": GROUP_LABELS[group], "change": 0.0})
                changes[group]["change"] = round(changes[group]["change"] + delta, 2)
    refresh_support(campaign)
    return changes


def ensure_appointments_state(state: dict[str, Any]) -> dict[str, Any]:
    appointments = state.setdefault("government_appointments", {})
    if "cabinet" not in appointments:
        rng = random.Random(f"{state.get('campaign_seed', 203001)}:cabinet")
        cabinet: dict[str, Any] = {}
        for ministry in MINISTRIES:
            slug = _safe_id(ministry)
            candidates = []
            for index in range(5):
                name = f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"
                candidate = {
                    "id": f"{slug}-candidate-{index + 1}", "name": name,
                    "background": rng.choice(BACKGROUNDS), "experience_years": rng.randint(8, 32),
                    "technical_fit": rng.randint(48, 94), "coalition_support": rng.randint(35, 92),
                    "integrity": rng.randint(55, 97), "management": rng.randint(45, 92),
                    "risk": rng.randint(3, 34), "simulated": True,
                }
                _ensure_political_profile(state, candidate)
                candidates.append(candidate)
            cabinet[slug] = {"name": ministry, "minister": None, "candidates": candidates}
        appointments["cabinet"] = cabinet
        appointments["last_cabinet_action"] = None
    for slot in appointments["cabinet"].values():
        for candidate in slot.get("candidates", []):
            _ensure_political_profile(state, candidate)
        if isinstance(slot.get("minister"), dict):
            _ensure_political_profile(state, slot["minister"])
    judiciary = appointments.setdefault("judiciary", {})
    if "seats" not in judiciary:
        seats = [{"id": f"seat-{index + 1}", "status": "occupied", "label": f"Cadeira {index + 1}"} for index in range(10)]
        seats.append({"id": "seat-11", "status": "vacant", "label": "Cadeira 11", "opened_on": state["date"], "reason": "vaga aberta no cenário fictício"})
        judiciary["seats"] = seats
        judiciary["pending"] = []
        judiciary["confirmed"] = []
        judiciary["rejected"] = []
        judiciary["candidate_batches"] = {}
    judiciary.setdefault("pending", [])
    judiciary.setdefault("confirmed", [])
    judiciary.setdefault("rejected", [])
    judiciary.setdefault("candidate_batches", {})
    return appointments


def _judge_candidates(state: dict[str, Any], seat_id: str) -> list[dict[str, Any]]:
    appointments = ensure_appointments_state(state)
    judiciary = appointments["judiciary"]
    batches = judiciary["candidate_batches"]
    if seat_id not in batches:
        rng = random.Random(f"{state.get('campaign_seed', 203001)}:{seat_id}:nominees")
        batch = []
        for index in range(5):
            experience = rng.randint(15, 38)
            batch.append({
                "id": f"{seat_id}-nominee-{index + 1}",
                "name": f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)} {rng.choice(LAST_NAMES)}",
                "specialty": rng.choice(LEGAL_SPECIALTIES), "years_experience": experience,
                "technical_record": rng.randint(55, 97), "independence": rng.randint(45, 96),
                "senate_dialogue": rng.randint(35, 94), "controversy": rng.randint(0, 40), "simulated": True,
            })
        batches[seat_id] = batch
    return batches[seat_id]


def appointments_overview(state: dict[str, Any]) -> dict[str, Any]:
    data = ensure_appointments_state(state)
    campaign = ensure_campaign_state(state)
    cabinet = [{"id": key, "name": value["name"], "minister": value.get("minister"), "candidates": value["candidates"]}
               for key, value in data["cabinet"].items()]
    judiciary = data["judiciary"]
    vacant = next((seat for seat in judiciary["seats"] if seat["status"] == "vacant"), None)
    candidates = _judge_candidates(state, vacant["id"]) if vacant and not judiciary["pending"] else []
    for candidate in candidates:
        candidate["estimated_confirmation_pct"] = round(_confirmation_probability(state, candidate) * 100, 1)
    pending = []
    for item in judiciary["pending"]:
        pending.append({**item, "days_until_vote": max(0, (date.fromisoformat(item["vote_date"]) - date.fromisoformat(state["date"])).days)})
    return {
        "simulated": True,
        "authorized": _is_president_in_office(state),
        "notice": "Nomes, perfis, composição inicial e votações são fictícios e pertencem apenas a esta partida.",
        "cabinet": cabinet,
        "last_cabinet_action": data.get("last_cabinet_action"),
        "cabinet_days_until_action": _cooldown_days(state["date"], data.get("last_cabinet_action"), 7),
        "campaign_groups": [{"key": key, "label": GROUP_LABELS[key], "support": round(value, 1)}
                            for key, value in campaign["group_support"].items()],
        "judiciary": {"seats": judiciary["seats"], "vacant": vacant, "candidates": candidates,
                      "pending": pending, "confirmed": list(reversed(judiciary["confirmed"][-5:])),
                      "rejected": list(reversed(judiciary["rejected"][-5:]))},
    }


def _is_president_in_office(state: dict[str, Any]) -> bool:
    career = state.get("career") or {}
    if career.get("mode"):
        return career.get("office") == "presidente" and career.get("phase") == "office"
    return state.get("office_status") not in {"former_president", "detained_after_failed_rupture", "former_official"}


def _cooldown_days(today: str, last: str | None, cooldown: int) -> int:
    return max(0, cooldown - (date.fromisoformat(today) - date.fromisoformat(last)).days) if last else 0


def appoint_minister(state: dict[str, Any], ministry_id: str, candidate_id: str) -> dict[str, Any]:
    if not _is_president_in_office(state):
        raise ValueError("Nomear ministros exige estar no exercício da Presidência.")
    data = ensure_appointments_state(state)
    cabinet = data["cabinet"]
    if ministry_id not in cabinet:
        raise ValueError("Escolha uma pasta ministerial existente no catálogo oficial da simulação.")
    wait = _cooldown_days(state["date"], data.get("last_cabinet_action"), 7)
    if wait:
        raise ValueError(f"A próxima decisão de nomeação abre em {wait} dia(s).")
    slot = cabinet[ministry_id]
    candidate = next((item for item in slot["candidates"] if item["id"] == candidate_id), None)
    if not candidate:
        raise ValueError("A indicação escolhida não pertence às opções deste ministério.")
    previous = slot.get("minister")
    slot["minister"] = {**candidate, "appointed_on": state["date"]}
    data["last_cabinet_action"] = state["date"]
    group_changes = _apply_candidate_group_effects(state, previous, slot["minister"])
    state.setdefault("cabinet_history", []).append({"date": state["date"], "ministry": slot["name"], "candidate": candidate["name"],
                                                     "previous": previous.get("name") if previous else None, "simulated": True})
    state["cabinet_history"] = state["cabinet_history"][-100:]
    occupied = [item["minister"] for item in cabinet.values() if item.get("minister")]
    metrics = state.setdefault("metrics", {})
    gov_base = data.setdefault("governability_base", float(metrics.get("governability", 50)))
    trust_base = data.setdefault("institutional_trust_base", float(metrics.get("institutional_trust", 50)))
    avg_coalition = sum(item["coalition_support"] for item in occupied) / len(occupied)
    avg_integrity = sum(item["integrity"] for item in occupied) / len(occupied)
    metrics["governability"] = _clamp(gov_base + (avg_coalition - 50) * .12)
    metrics["institutional_trust"] = _clamp(trust_base + (avg_integrity - 50) * .08)
    return {"ministry": slot["name"], "appointed": slot["minister"], "replaced": previous, "cabinet_size": len(occupied),
            "average_coalition": round(avg_coalition, 1), "average_integrity": round(avg_integrity, 1),
            "campaign_group_changes": group_changes,
            "summary": f"{candidate['name']} foi nomeado(a) para {slot['name']}. A escolha afeta a coordenação política e a confiança institucional de forma gradual."}


def nominate_judge(state: dict[str, Any], candidate_id: str) -> dict[str, Any]:
    if not _is_president_in_office(state):
        raise ValueError("Indicar uma pessoa ao STF exige estar no exercício da Presidência.")
    data = ensure_appointments_state(state)
    judiciary = data["judiciary"]
    if judiciary["pending"]:
        raise ValueError("Já há uma indicação aguardando sabatina e votação no Senado.")
    vacancy = next((seat for seat in judiciary["seats"] if seat["status"] == "vacant"), None)
    if not vacancy:
        raise ValueError("Não existe vaga aberta no cenário neste momento.")
    candidate = next((item for item in _judge_candidates(state, vacancy["id"]) if item["id"] == candidate_id), None)
    if not candidate:
        raise ValueError("Escolha um dos cinco nomes gerados para a vaga aberta.")
    vote_date = date.fromisoformat(state["date"]) + timedelta(days=30)
    nomination = {**candidate, "seat_id": vacancy["id"], "seat_label": vacancy["label"], "nominated_on": state["date"],
                  "vote_date": vote_date.isoformat(), "status": "awaiting_senate", "simulated": True}
    judiciary["pending"] = [nomination]
    return {"nomination": nomination, "summary": f"{candidate['name']} foi indicado(a) para a vaga simulada. A sabatina e a votação estão previstas para {vote_date.strftime('%d/%m/%Y')}."}


def _confirmation_probability(state: dict[str, Any], nominee: dict[str, Any]) -> float:
    support = float(state.get("metrics", {}).get("congress_support", 50))
    credentials = float(nominee["technical_record"]) * .45 + float(nominee["senate_dialogue"]) * .35 + float(nominee["independence"]) * .20
    base = .08 + support / 100 * .46 + credentials / 100 * .38 - float(nominee["controversy"]) / 100 * .30
    flexibility = get_difficulty(state.get("difficulty", "normal"))["coalition_flexibility"]
    return adjust_coalition_probability(base, flexibility, sensitivity=.12)


def advance_appointments(state: dict[str, Any], before: date, after: date) -> list[str]:
    data = ensure_appointments_state(state)
    judiciary = data["judiciary"]
    messages = []
    remaining = []
    for nominee in judiciary.get("pending", []):
        vote_date = date.fromisoformat(nominee["vote_date"])
        if not before < vote_date <= after:
            remaining.append(nominee)
            continue
        metrics = state.get("metrics", {})
        chance = _confirmation_probability(state, nominee)
        rng = random.Random(f"{state.get('campaign_seed', 203001)}:{nominee['id']}:senate-vote")
        approved = rng.random() < chance
        seat = next((item for item in judiciary["seats"] if item["id"] == nominee["seat_id"]), None)
        nominee["status"] = "confirmed" if approved else "rejected"
        nominee["vote_probability"] = round(chance * 100, 1)
        nominee["resolved_on"] = vote_date.isoformat()
        if approved:
            if seat:
                seat["status"] = "occupied"
                seat["occupant"] = nominee["name"]
                seat["appointed_on"] = vote_date.isoformat()
            judiciary["confirmed"].append(nominee)
            trust = state.setdefault("metrics", {}).get("institutional_trust", 50)
            state["metrics"]["institutional_trust"] = _clamp(trust + 1)
            messages.append(f"Senado aprovou, na votação simulada, a indicação de {nominee['name']} ao STF.")
        else:
            judiciary["rejected"].append(nominee)
            messages.append(f"Senado rejeitou, na votação simulada, a indicação de {nominee['name']}. A vaga continua aberta para nova indicação.")
    judiciary["pending"] = remaining
    judiciary["confirmed"] = judiciary.get("confirmed", [])[-20:]
    judiciary["rejected"] = judiciary.get("rejected", [])[-20:]
    return messages
