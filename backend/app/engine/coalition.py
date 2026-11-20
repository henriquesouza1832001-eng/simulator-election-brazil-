"""Coligações pré-eleitorais para eleições majoritárias (prefeito, governador, senador, presidente).

Antes da campanha acabar, o jogador pode convidar partidos para a chapa. Cada partido aceita ou recusa conforme a distância no
espectro, o preço oferecido e a força do jogador na pesquisa. Quem aceita:
- soma o tempo de TV da própria bancada ao da chapa (`tv_time.share(..., extra_parties=…)`);
- retira o candidato próprio da disputa (o rival some do campo) e transfere parte dos votos que teria (`coalition_bonus`, com teto);
- cobra o preço combinado: vice, secretarias ou pontos do programa, que viram compromissos e desgastam a reputação se a distância ideológica for grande.
O motor decide aceitação e efeitos; os parâmetros são de design e não representam negociações reais.
"""
from __future__ import annotations

import hashlib
from typing import Any

from . import electoral_field, legislature, tv_time

MAX_PARTNERS = 3
MIN_SEATS = 5               # só partidos com bancada na Câmara entram na conversa
TRANSFER_RATE = 0.55        # fração dos votos que o partido teria que acompanha a chapa
BONUS_CAP = 12.0            # teto do ganho em pontos percentuais de intenção de voto
OFFERS = {
    "vice": {"label": "Indicar o vice da chapa", "short": "Vice", "price": 1.0, "text": "O maior atrativo. Só um partido por chapa, e o vice passa a ter peso no governo."},
    "secretarias": {"label": "Prometer secretarias no governo", "short": "Secretarias", "price": 0.6, "text": "Vira compromisso com o partido se você vencer."},
    "programa": {"label": "Incorporar pontos do programa do partido", "short": "Programa", "price": 0.35, "text": "Custa pouco, mas dilui um pouco o seu discurso."},
}


def _roll(seed: str) -> float:
    return int(hashlib.sha256(seed.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF


def _state(career: dict[str, Any]) -> dict[str, Any]:
    return career.setdefault("coalition", {"partners": [], "obligations": [], "log": []})


def eligible(career: dict[str, Any]) -> bool:
    return career.get("office") in electoral_field.MAJORITARIAN and career.get("phase") in {"pre_campaign", "campaign"}


def partner_parties(career: dict[str, Any]) -> list[str]:
    return [p["party"] for p in _state(career)["partners"]]


def _own_strength(career: dict[str, Any], party: str) -> float:
    """O que o partido pesa na disputa (% dos votos): vem do rival correspondente no campo, quando existe."""
    for rival in career.get("opponents") or []:
        if rival.get("party") == party:
            return float(rival.get("real_share_pct") or 0.0)
    return 0.0


def _distance(career: dict[str, Any], party: str) -> float:
    return abs(electoral_field.position(party) - electoral_field.position(career.get("party"), career.get("ideology"))) / 2   # 0 a 1


def acceptance(career: dict[str, Any], party: str, offer: str, player_support: float) -> float:
    """Chance de o partido aceitar: pesa preço, distância ideológica, a força do jogador e a do próprio partido na disputa."""
    price = OFFERS[offer]["price"]
    own = _own_strength(career, party)
    leading = max(0.0, own - float(player_support))   # partido bem à frente do jogador não abre mão da própria candidatura
    chance = 0.10 + 0.45 * price - 0.8 * _distance(career, party) + 0.008 * float(player_support) - 0.04 * leading
    return round(max(0.03, min(0.95, chance)), 3)


def view(state: dict[str, Any], career: dict[str, Any], player_support: float = 30.0) -> dict[str, Any] | None:
    if career.get("office") not in electoral_field.MAJORITARIAN:
        return None
    co = _state(career)
    parties = partner_parties(career)
    rows = []
    if eligible(career) and len(parties) < MAX_PARTNERS:
        for party in legislature.PARTIES:
            if party["id"] == career.get("party") or party["id"] in parties or party["seats"] < MIN_SEATS:
                continue
            offers = [{"id": key, "label": o["label"], "short": o["short"], "text": o["text"], "chance_pct": round(acceptance(career, party["id"], key, player_support) * 100),
                       "available": not (key == "vice" and any(p["offer"] == "vice" for p in co["partners"]))} for key, o in OFFERS.items()]
            rows.append({"party": party["id"], "seats": party["seats"], "spectrum": party["spectrum"], "tv_pct": tv_time.share(party["id"])["share_pct"],
                         "own_pct": _own_strength(career, party["id"]), "distance_pct": round(_distance(career, party["id"]) * 100), "offers": offers})
        rows.sort(key=lambda r: -r["seats"])
    tv = tv_time.share(career.get("party"), extra_parties=parties)
    return {"can_invite": eligible(career) and len(parties) < MAX_PARTNERS, "partners": co["partners"], "obligations": co["obligations"], "log": co["log"][-6:],
            "bonus_pp": round(float(career.get("coalition_bonus", 0.0)), 1), "tv": tv, "candidates": rows[:10], "max_partners": MAX_PARTNERS}


def invite(state: dict[str, Any], career: dict[str, Any], party: str, offer: str, player_support: float) -> dict[str, Any]:
    if not eligible(career):
        raise ValueError("Coligações só podem ser formadas em eleições majoritárias, antes do fim da campanha.")
    if offer not in OFFERS:
        raise ValueError("Oferta desconhecida.")
    co = _state(career)
    if len(co["partners"]) >= MAX_PARTNERS:
        raise PermissionError(f"A chapa já tem {MAX_PARTNERS} partidos coligados.")
    if party in partner_parties(career):
        raise PermissionError("Esse partido já está na chapa.")
    if offer == "vice" and any(p["offer"] == "vice" for p in co["partners"]):
        raise PermissionError("O vice já foi prometido a outro partido.")
    known = {p["id"]: p for p in legislature.PARTIES}
    if party not in known or party == career.get("party") or known[party]["seats"] < MIN_SEATS:
        raise ValueError("Esse partido não tem bancada para entrar na conversa.")
    chance = acceptance(career, party, offer, player_support)
    attempts = int(co.setdefault("attempts", {}).get(party, 0))
    accepted = _roll(f"{career.get('seed', 1)}:coalition:{party}:{offer}:{attempts}") < chance
    co["attempts"][party] = attempts + 1
    if not accepted:
        co["log"].append({"date": state["date"], "text": f"{party} recusou o convite ({OFFERS[offer]['label'].lower()})."})
        return {"accepted": False, "party": party, "offer": offer, "chance_pct": round(chance * 100), "message": f"{party} recusou. Uma nova proposta pode mudar a resposta."}
    own = _own_strength(career, party)
    transfer = min(BONUS_CAP - float(career.get("coalition_bonus", 0.0)), own * TRANSFER_RATE) if own else 0.6   # partido sem candidato forte traz pouco
    career["coalition_bonus"] = round(float(career.get("coalition_bonus", 0.0)) + max(0.0, transfer), 2)
    for rival in career.get("opponents") or []:   # o candidato próprio do partido sai da disputa
        if rival.get("party") == party:
            rival["support_weight"] = 0.001
            rival["coalition"] = True
    co["partners"].append({"party": party, "offer": offer, "date": state["date"], "transfer_pp": round(max(0.0, transfer), 1), "distance_pct": round(_distance(career, party) * 100)})
    if offer in {"vice", "secretarias"}:
        co["obligations"].append({"party": party, "what": "a vice-chapa" if offer == "vice" else "secretarias no governo", "status": "pendente"})
    gap = _distance(career, party)
    if gap > 0.4:   # aliança distante do seu campo custa reputação
        career["reputation"] = round(max(0.0, float(career.get("reputation", 50)) - 3.0 * (gap - 0.4) / 0.6 - 0.5), 2)
    co["log"].append({"date": state["date"], "text": f"{party} entrou na chapa ({OFFERS[offer]['label'].lower()}); soma {round(max(0.0, transfer), 1)} p.p. e o tempo de TV da legenda."})
    return {"accepted": True, "party": party, "offer": offer, "chance_pct": round(chance * 100), "transfer_pp": round(max(0.0, transfer), 1),
            "message": f"{party} entrou na chapa. A intenção de voto sobe cerca de {str(round(max(0.0, transfer), 1)).replace('.', ',')} ponto(s) e o tempo de TV da coligação aumenta."}
