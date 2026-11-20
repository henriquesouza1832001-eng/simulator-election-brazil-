"""Movimentos dos rivais durante a campanha e institutos de pesquisa.

Os rivais (engine/electoral_field.py) agora agem: atacam o jogador, lançam propostas, se envolvem em escândalos ou recebem apoio
de outros partidos. Cada movimento tem efeito pequeno e limitado no motor e vira notícia na Imprensa. Os institutos de pesquisa
têm tamanho de amostra e viés próprios, então duas pesquisas do mesmo dia podem divergir sem que ninguém esteja "errado".
Tudo é simulação; nomes de institutos e candidaturas são fictícios.
"""
from __future__ import annotations

import random
from datetime import date
from typing import Any

from . import electoral_field, voice

# "lean": para onde o instituto tende (-1 esquerda, +1 direita). O viés favorece quem está do lado do instituto.
INSTITUTES = [
    {"id": "datafato", "name": "Datafato", "lean": 0.0, "sample_factor": 1.0},
    {"id": "vox", "name": "Vox Pública", "lean": -0.6, "sample_factor": 0.7},
    {"id": "brasilreal", "name": "Brasil Real", "lean": 0.6, "sample_factor": 0.7},
]
HOUSE_EFFECT_PP = 1.6   # viés máximo de um instituto, em pontos percentuais
EVENT_CHANCE_PER_WEEK = 0.45
MAX_EVENTS_KEPT = 12

KINDS = {
    "ataque": {"weight": 3, "momentum": -0.8, "head": "{party} parte para o ataque",
               "texts": ["{party} faz ataque ao seu campo em ato de campanha: “{focus}” vira assunto do dia.",
                         "O {party} escolheu o seu flanco: em {focus}, a crítica veio com microfone e câmera.",
                         "Comício do {party} gasta mais tempo falando de você do que das próprias propostas, de olho em {focus}."]},
    "proposta": {"weight": 3, "boost": 1.03, "head": "{party} lança pacote de propostas",
                 "texts": ["{party} apresenta pacote de propostas em {focus} e sobe no debate.",
                           "O {party} tira da gaveta um plano para {focus}; falta saber quem paga, mas o slide está bonito.",
                           "Campanha do {party} aposta em {focus} e promete detalhar a conta 'em breve'."]},
    "escandalo": {"weight": 1.5, "pressure": 1.4, "head": "Denúncia atinge campanha do {party}",
                  "texts": ["Denúncia atinge a campanha de {party}; o partido nega e pede calma.",
                            "O {party} amanhece com uma notícia incômoda e uma nota oficial de três linhas.",
                            "Bastidor do {party} vaza e a campanha passa o dia explicando o que não foi dito."]},
    "apoio": {"weight": 1.5, "boost": 1.05, "head": "{party} ganha novo apoio",
              "texts": ["{party} recebe apoio de aliados e amplia o tempo de rua.",
                        "Liderança local declara voto no {party} e a foto do aperto de mão já circula.",
                        "O {party} fecha um acordo de palanque e promete 'unidade' até a próxima divergência."]},
}


def institute_for(index: int) -> dict[str, Any]:
    """Os institutos se revezam; a mesma partida sempre vê a mesma ordem."""
    return INSTITUTES[index % len(INSTITUTES)]


def house_effect(institute: dict[str, Any], player_position: float) -> float:
    """Pontos a mais (ou a menos) que o instituto dá ao jogador, conforme a proximidade entre ambos no espectro."""
    return round(HOUSE_EFFECT_PP * float(institute["lean"]) * float(player_position), 2)


def tick_rivals(state: dict[str, Any], career: dict[str, Any], before: date, after: date) -> list[str]:
    """Uma chance por semana de algum rival fazer um movimento. Só em eleições majoritárias."""
    if career.get("office") not in electoral_field.MAJORITARIAN or career.get("phase") not in {"campaign", "runoff_campaign"}:
        return []
    field = electoral_field.ensure_field(career)
    if not field:
        return []
    messages: list[str] = []
    events = career.setdefault("rival_events", [])
    # um sorteio por semana, no dia da semana fixo em que cai o ordinal (assim avançar 1 ou 30 dias dá o mesmo resultado)
    days = [d for d in range(before.toordinal() + 1, after.toordinal() + 1) if d % 7 == 3]
    for ordinal in days:
        w = ordinal // 7
        rng = random.Random(f"{career.get('seed', 1)}:rival-move:{w}")
        if rng.random() >= EVENT_CHANCE_PER_WEEK:
            continue
        rival = rng.choice(field)
        kind = rng.choices(list(KINDS), weights=[KINDS[k]["weight"] for k in KINDS], k=1)[0]
        spec = KINDS[kind]
        focus = electoral_field.FOCUS_LABEL.get(rival["issue_focus"], rival["issue_focus"])
        if "momentum" in spec and float(rival.get("proximity", 0.5)) >= 0.45:   # só ataca o jogador quem disputa o mesmo eleitorado
            career["momentum"] = round(max(-10.0, float(career.get("momentum", 0)) + spec["momentum"] * float(rival.get("proximity", 0.5)) * 1.6), 2)
        elif "momentum" in spec:
            kind, spec = "proposta", KINDS["proposta"]
        if "boost" in spec:
            base = rival.setdefault("base_weight", float(rival["support_weight"]))
            rival["support_weight"] = round(min(base * 1.4, float(rival["support_weight"]) * spec["boost"]), 3)   # movimentos somam, mas com teto
        if "pressure" in spec:
            electoral_field.apply_pressure(career, rival["id"], spec["pressure"])
        text = voice.pick(spec["texts"], f"{career.get('seed', 1)}:{w}:{kind}").format(party=rival["party"], focus=focus)
        day = date.fromordinal(ordinal)
        events.insert(0, {"date": day.isoformat(), "rival_id": rival["id"], "party": rival["party"], "kind": kind, "text": text})
        messages.append(text)
        try:
            from .consequences import _book, _post
            _post(_book(state), state, {"id": f"rival-{w}", "kind": "imprensa", "headline": spec["head"].format(party=rival["party"]), "body": text, "tone": "neutro", "date": day.isoformat()})
        except Exception:  # noqa: BLE001 - a notícia é acessória; nunca derruba o avanço do dia
            pass
    del events[MAX_EVENTS_KEPT:]
    return messages
