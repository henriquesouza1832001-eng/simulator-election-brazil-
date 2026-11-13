"""Tramitação legislativa em etapas: comissões, relator, negociação por bancada e urgência.

Cada projeto de competência do Presidente ganha etapas (comissão de mérito, CCJ, plenário, Senado), um relator
(deputado real, de um partido grande) e uma perspectiva de voto por partido. O jogador pode negociar com bancadas
(emendas, cargos, concessões no texto) e pedir urgência (CF art. 64, só projetos de lei). A votação nominal final
continua em `legislature.roll_call`; aqui se decide se o projeto sobrevive às comissões e com que texto chega ao plenário.
Probabilidades e pesos são parâmetros de design.
"""
from __future__ import annotations

import hashlib
from datetime import date, timedelta
from typing import Any

from . import consequences, ledger, legislature
from .consequences import LEAN

STAGES = {
    "pl": [("Protocolo", 0.0, False), ("Comissão de mérito", 0.25, True), ("CCJ", 0.5, True), ("Plenário da Câmara", 0.75, False), ("Senado", 1.0, False)],
    "pec": [("Protocolo", 0.0, False), ("CCJ — admissibilidade", 0.2, True), ("Comissão especial", 0.45, True), ("Plenário da Câmara (2 turnos)", 0.7, False), ("Senado (2 turnos)", 1.0, False)],
}
OFFERS = {
    "emendas": {"label": "Liberar emendas à bancada", "relation": 0.10, "primary": -0.01, "text": "Custa um pouco do resultado primário."},
    "cargo": {"label": "Oferecer cargo na administração", "relation": 0.18, "integrity": -0.3, "text": "Pesa mais, mas arranha a integridade."},
    "concessao": {"label": "Aceitar concessão no texto", "relation": 0.10, "dilution": 0.9, "text": "Reduz em 10% os efeitos do projeto."},
}
COMMITTEE_BASE = 0.80


def _roll(seed: str) -> float:
    return int(hashlib.sha256(seed.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF


def _kind(bill: dict[str, Any]) -> str:
    return "pec" if str(bill.get("instrument", "")).lower() == "pec" else "pl"


def _lean(bill: dict[str, Any]) -> float:
    return LEAN.get(str(bill.get("power_id", "")), 0.0)


def attach(state: dict[str, Any], bill: dict[str, Any]) -> None:
    """Cria etapas, relator e controle de negociação para o projeto."""
    start = date.fromisoformat(bill["submitted_date"])
    end = date.fromisoformat(bill["decision_date"])
    span = (end - start).days
    kind = _kind(bill)
    bill["process"] = {"stages": [{"name": n, "date": (start + timedelta(days=round(span * f))).isoformat(), "committee": c, "status": "pendente"} for n, f, c in STAGES[kind]],
                       "negotiated": {}, "dilution": 1.0, "urgency": False, "log": []}
    houses = legislature.composition(state)["camara"]
    big = {p["id"] for p in legislature.PARTIES if p["seats"] >= 20}
    candidates = [m for m in houses if m["party"] in big]
    pick = candidates[int(_roll(f"{state.get('campaign_seed', 1)}:relator:{bill['id']}") * len(candidates)) % len(candidates)]
    ideology = next(p["ideology"] for p in legislature.PARTIES if p["id"] == pick["party"])
    bill["process"]["relator"] = {"name": pick["name"], "party": pick["party"], "state": pick["state"], "ideology": ideology}
    bill["process"]["stages"][0]["status"] = "concluída"


def _alignment(bill: dict[str, Any]) -> float:
    lean = _lean(bill)
    if lean == 0.0:
        return 0.0
    return 1 - abs(bill["process"]["relator"]["ideology"] - lean)


def committee_chance(state: dict[str, Any], bill: dict[str, Any]) -> float:
    support = float(state.get("metrics", {}).get("congress_support", 50))
    p = COMMITTEE_BASE + (support - 50) / 200 + 0.15 * _alignment(bill) + 0.03 * sum(len(v) for v in bill["process"]["negotiated"].values())
    if bill["process"]["urgency"]:
        p -= 0.04
    return round(max(0.1, min(0.97, p)), 3)


def party_outlook(state: dict[str, Any], bill: dict[str, Any]) -> list[dict[str, Any]]:
    """Por partido: cadeiras, relação atual, probabilidade média de voto a favor e o que já foi oferecido."""
    houses = legislature.composition(state)["camara"]
    instrument = str(bill.get("instrument", "Projeto de Lei")).strip().lower()
    axes = legislature._bill_axes(bill)
    rows = []
    for party in legislature.PARTIES:
        members = [m for m in houses if m["party"] == party["id"]]
        if not members or party["seats"] < 5:
            continue
        p = sum(legislature._disposition(m, state, instrument, axes) for m in members) / len(members)
        rows.append({"party": party["id"], "name": party["name"], "seats": len(members), "ideology": party["ideology"], "spectrum": party["spectrum"],
                     "support_pct": round(p * 100), "relation": round(state.get("relation_delta", {}).get(party["id"], 0.0), 2),
                     "offered": list(bill["process"]["negotiated"].get(party["id"], []))})
    rows.sort(key=lambda r: -r["seats"])
    return rows


def negotiate(state: dict[str, Any], bill_id: str, party: str, offer: str) -> dict[str, Any]:
    bill = next((b for b in state["legislative_calendar"]["pending_bills"] if b["id"] == bill_id and b.get("process")), None)
    if bill is None:
        raise ValueError("Projeto não encontrado ou já votado.")
    if offer not in OFFERS:
        raise ValueError("Oferta desconhecida.")
    if party not in {p["id"] for p in legislature.PARTIES}:
        raise ValueError("Partido desconhecido.")
    done = bill["process"]["negotiated"].setdefault(party, [])
    if offer in done:
        raise PermissionError("Essa oferta já foi feita a este partido neste projeto.")
    spec = OFFERS[offer]
    delta = state.setdefault("relation_delta", {})
    delta[party] = round(delta.get(party, 0.0) + spec["relation"], 3)
    if spec.get("primary"):
        from .fiscal import record_policy_balance_delta
        record_policy_balance_delta(state, spec["primary"])
    if spec.get("integrity"):
        m = state.setdefault("metrics", {})
        m["integrity"] = round(max(0.0, float(m.get("integrity", 70)) + spec["integrity"]), 2)
    if spec.get("dilution"):
        bill["process"]["dilution"] = round(max(0.6, bill["process"]["dilution"] * spec["dilution"]), 3)
    done.append(offer)
    bill["process"]["log"].append({"date": state["date"], "text": f"{spec['label']} ({party})."})
    return {"bill": bill_id, "party": party, "offer": offer, "relation": delta[party], "dilution": bill["process"]["dilution"]}


def request_urgency(state: dict[str, Any], bill_id: str) -> dict[str, Any]:
    bill = next((b for b in state["legislative_calendar"]["pending_bills"] if b["id"] == bill_id and b.get("process")), None)
    if bill is None:
        raise ValueError("Projeto não encontrado ou já votado.")
    if _kind(bill) == "pec":
        raise PermissionError("Urgência constitucional (art. 64) vale para projetos de lei, não para PEC.")
    if bill["process"]["urgency"]:
        raise PermissionError("A urgência já foi pedida para este projeto.")
    today = date.fromisoformat(state["date"])
    end = date.fromisoformat(bill["decision_date"])
    remaining = max(0, (end - today).days)
    bill["decision_date"] = (today + timedelta(days=round(remaining * 0.6))).isoformat()
    bill["process"]["urgency"] = True
    for stage in bill["process"]["stages"]:
        if stage["status"] == "pendente" and stage["committee"]:
            stage["status"] = "dispensada (urgência)"
    delta = state.setdefault("relation_delta", {})
    for party in {p["id"] for p in legislature.PARTIES}:
        delta[party] = round(delta.get(party, 0.0) - 0.03, 3)
    bill["process"]["log"].append({"date": state["date"], "text": "Urgência constitucional pedida: prazo menor e desgaste com as bancadas."})
    return {"bill": bill_id, "decision_date": bill["decision_date"]}


def tick(state: dict[str, Any], before: date, after: date) -> list[str]:
    msgs: list[str] = []
    # a base no Congresso volta devagar ao ponto de equilíbrio: reações passam e alianças se refazem (3% ao mês)
    metrics = state.get("metrics", {})
    if "congress_support" in metrics:
        elapsed = max(0, (after - before).days)
        cs = float(metrics["congress_support"])
        metrics["congress_support"] = round(cs + (50.0 - cs) * min(1.0, 0.03 * elapsed / 30), 2)
    calendar = state.get("legislative_calendar", {})
    keep = []
    for bill in calendar.get("pending_bills", []):
        proc = bill.get("process")
        dead = False
        if proc:
            for stage in proc["stages"]:
                if stage["status"] != "pendente" or not (before < date.fromisoformat(stage["date"]) <= after) or date.fromisoformat(stage["date"]) >= date.fromisoformat(bill["decision_date"]):
                    continue
                if not stage["committee"]:
                    if stage["name"].startswith("Plenário"):
                        note = _plenary_events(state, bill, stage)
                        if note == "obstruída":
                            continue   # a votação foi adiada; a etapa volta a ser avaliada na nova data
                    stage["status"] = "concluída"
                    _news(state, bill, f"{bill['title']}: {stage['name']}.")
                    continue
                chance = committee_chance(state, bill)
                passed = _roll(f"{state.get('campaign_seed', 1)}:{bill['id']}:{stage['name']}") < chance
                rel = proc["relator"]
                if passed:
                    stage["status"] = "aprovada"
                    parecer = "com substitutivo" if _alignment(bill) < -0.2 and _roll(f"{bill['id']}:subst") < 0.6 else "favorável"
                    if parecer == "com substitutivo":
                        proc["dilution"] = round(max(0.6, proc["dilution"] * 0.85), 3)
                    stage["parecer"] = parecer
                    _news(state, bill, f"{bill['title']}: aprovado na {stage['name']} (relator {rel['name']}, {rel['party']}; parecer {parecer}).")
                    msgs.append(f"{bill['title']} avançou na {stage['name']}.")
                else:
                    stage["status"] = "rejeitada"
                    bill["status"] = "rejected"
                    calendar["laws_failed"] = int(calendar.get("laws_failed", 0)) + 1
                    _news(state, bill, f"{bill['title']}: rejeitado na {stage['name']} (relator {rel['name']}, {rel['party']}). O projeto foi arquivado.")
                    if bill.get("ledger_id"):
                        ledger.settle(state, bill["ledger_id"], {}, "rejeitado na comissão", f"Arquivado na {stage['name']}; nenhum efeito previsto foi aplicado.")
                    msgs.append(f"{bill['title']} foi arquivado na {stage['name']}.")
                    dead = True
                    break
        if not dead:
            keep.append(bill)
    calendar["pending_bills"] = keep
    return msgs


def opposition_share(bill: dict[str, Any]) -> float:
    """Parcela das cadeiras de partidos do lado ideológico oposto ao do projeto (0 a 1)."""
    lean = _lean(bill)
    if abs(lean) < 0.3:
        return 0.0
    seats = sum(p["seats"] for p in legislature.PARTIES if p["ideology"] * lean < 0 and abs(p["ideology"]) > 0.3)
    return seats / legislature.CHAMBER_SIZE


def _plenary_events(state: dict[str, Any], bill: dict[str, Any], stage: dict[str, Any]) -> str | None:
    """Obstrução (adia a votação uma vez) e destaque (retira parte do texto) quando a oposição é forte e o tema, polarizado."""
    proc = bill["process"]
    lean = abs(_lean(bill))
    if lean < 0.3:
        return None
    seed = f"{state.get('campaign_seed', 1)}:{bill['id']}"
    if not proc.get("obstructed"):
        p = 0.10 + 0.6 * lean * opposition_share(bill) - 0.05 * sum(len(v) for v in proc["negotiated"].values())
        if _roll(seed + ":obstrucao") < max(0.0, p):
            proc["obstructed"] = True
            for st in proc["stages"]:
                if st["status"] == "pendente":
                    st["date"] = (date.fromisoformat(st["date"]) + timedelta(days=14)).isoformat()
            bill["decision_date"] = (date.fromisoformat(bill["decision_date"]) + timedelta(days=14)).isoformat()
            proc["log"].append({"date": state["date"], "text": "A oposição obstruiu a pauta: votação adiada em 14 dias."})
            _news(state, bill, f"Oposição obstrui a votação de {bill['title']}; a pauta foi adiada em 14 dias.")
            return "obstruída"
    if not proc.get("destaque") and _roll(seed + ":destaque") < 0.25 * min(1.0, lean + 0.4):
        proc["destaque"] = True
        proc["dilution"] = round(max(0.6, proc["dilution"] * 0.9), 3)
        proc["log"].append({"date": state["date"], "text": "Destaque aprovado retirou parte do texto (10% dos efeitos)."})
        _news(state, bill, f"Destaque aprovado retira parte do texto de {bill['title']}.")
    return None


def _news(state: dict[str, Any], bill: dict[str, Any], text: str) -> None:
    book = consequences._book(state)
    consequences._post(book, state, {"id": f"tram-{bill['id']}-{len(book['feed'])}", "kind": "congresso", "headline": text, "body": "Tramitação simulada no Congresso.", "tone": "neutro", "action_id": bill.get("power_id", "")})


def overview(state: dict[str, Any]) -> dict[str, Any]:
    bills = []
    for b in state.get("legislative_calendar", {}).get("pending_bills", []):
        if not b.get("process"):
            continue
        proc = b["process"]
        bills.append({"id": b["id"], "title": b["title"], "instrument": b["instrument"], "decision_date": b["decision_date"], "stages": proc["stages"], "relator": proc["relator"],
                      "dilution": proc["dilution"], "urgency": proc["urgency"], "log": proc["log"][-6:], "committee_chance_pct": round(committee_chance(state, b) * 100),
                      "can_urgency": _kind(b) == "pl" and not proc["urgency"], "outlook": party_outlook(state, b), "lean": _lean(b)})
    local = [{"id": b["id"], "title": b["title"], "chamber": b["chamber"], "decision_date": b["decision_date"], "status": b["status"], "relator": b["relator"], "stages": b["stages"],
              "chance_pct": round(b["chance"] * 100)} for b in state.get("local_bills", [])[-8:]]
    return {"bills": bills, "local_bills": list(reversed(local)), "offers": [{"key": k, **{kk: vv for kk, vv in v.items() if kk in {"label", "text"}}} for k, v in OFFERS.items()],
            "note": "Etapas, relator e probabilidades são regras do jogo; a votação nominal final usa a composição real do Congresso com voto simulado."}
