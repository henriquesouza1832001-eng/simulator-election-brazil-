"""Debate em formato de debate de TV: mediador, adversários que respondem, réplica, pergunta ao adversário e checagem.

Sete etapas, cada uma exige uma fala do jogador. Entre as falas, o mediador e os adversários falam (textos
determinísticos, montados com fatos do jogo e a posição ideológica real do partido de cada adversário).
Se o jogador cita um número muito diferente do dado oficial do jogo, o mediador faz a checagem e a nota cai.
No fim, a nota do jogador é comparada com a dos adversários e a pesquisa se move.
"""
from __future__ import annotations

import hashlib
from typing import Any

from .legislature import PARTIES

STEPS = ["Abertura", "Bloco 1", "Réplica", "Bloco 2", "Pergunta ao adversário", "Resposta ao adversário", "Considerações finais"]
TEMPO = {"Abertura": 600, "Bloco 1": 900, "Réplica": 500, "Bloco 2": 900, "Pergunta ao adversário": 300, "Resposta ao adversário": 600, "Considerações finais": 500}


def _roll(seed: str) -> float:
    return int(hashlib.sha256(seed.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF


def pick_opponents(state: dict[str, Any], n: int = 2) -> list[dict[str, Any]]:
    career = state.get("career") or {}
    profiles = {p["id"]: p for p in PARTIES}
    out: list[dict[str, Any]] = []
    for o in (career.get("opponents") or [])[:n]:
        party = o.get("party")
        out.append({"name": o.get("name") or f"Candidato(a) do {party}", "party": party, "lean": profiles.get(party, {"ideology": 0.0})["ideology"]})
    for party in ("PL", "PT", "MDB", "PSD", "NOVO", "PSB"):
        if len(out) >= n:
            break
        if party not in {o["party"] for o in out}:
            out.append({"name": f"Candidato(a) do {party}", "party": party, "lean": profiles[party]["ideology"]})
    return out[:n]


def _line(opp: dict[str, Any], step: str, topic: str, fact: float | None, seed: str) -> str:
    lean, party = opp["lean"], opp["party"]
    r = _roll(seed + opp["party"] + step)
    pools = {
        "right": ["Precisamos de um Estado menor, segurança jurídica e responsabilidade com o gasto público.", "O caminho é destravar o setor privado, simplificar impostos e cortar desperdício.",
                  "Quem produz precisa de previsibilidade; o governo não pode gastar mais do que arrecada."],
        "left": ["É preciso proteger quem mais precisa: investimento social, salário digno e serviço público forte.", "Sem combater a desigualdade, não há crescimento que dure; o Estado tem papel central.",
                 "A prioridade é emprego e renda, com participação dos trabalhadores e controle sobre abusos."],
        "center": ["Precisamos de diálogo, metas claras e gestão profissional, sem radicalismo.", "O país exige equilíbrio entre responsabilidade fiscal e proteção social.",
                   "Vou governar com base técnica e construir maioria no Congresso."],
    }
    side = "right" if lean > 0.3 else "left" if lean < -0.3 else "center"
    base = pools[side][int(r * len(pools[side])) % len(pools[side])]
    fact_txt = f" O dado que temos, de {fact:.1f}, mostra o tamanho do desafio em {topic}." if fact is not None else ""
    return f"({party}) {base}{fact_txt}" if step in {"Abertura", "Bloco 1", "Bloco 2", "Considerações finais"} else f"({party}) {base}"


def attack(opp: dict[str, Any], weakest: str, last_decision: dict[str, Any] | None) -> str:
    base = {"relevancia": "O senhor ou a senhora não ligou a resposta ao problema que foi perguntado.",
            "viabilidade": "Isso não é atribuição do seu cargo ou não passa pela lei. Como pretende fazer?",
            "dados": "Faltaram números: quanto custa e de onde vem o dinheiro?",
            "compromisso": "Fala bonita, mas sem prazo nem responsável. Quem cobra depois?"}.get(weakest, "A resposta não convenceu.")
    if last_decision and last_decision.get("result") is not None:
        return f"{opp['name']}: {base} E sobre “{last_decision['title']}”, o governo prometeu um resultado e entregou outro."
    return f"{opp['name']}: {base}"


def fact_check(text: str, fact: float | None) -> str | None:
    """Mediador confere o número citado contra o dado do jogo; None se nada a corrigir."""
    import re
    if fact is None or fact == 0:
        return None
    nums = [float(x.replace(",", ".")) for x in re.findall(r"\d+(?:[.,]\d+)?", text)]
    off = [n for n in nums if n > 0 and (n > fact * 1.5 or n < fact * 0.5) and abs(n - fact) > 2.0 and n < 1000]
    if off and not any(abs(n - fact) <= max(fact * 0.3, 1.5) for n in nums):
        return f"Mediador (checagem): o dado oficial é {fact:.1f}, e não {off[0]:g}."
    return None


def opponent_score(opp: dict[str, Any], step: str, seed: str) -> float:
    return round(52 + 28 * _roll(seed + opp["party"] + step + "score"), 1)


def poll_move(player_avg: float, opponent_avgs: list[float]) -> float:
    rival = sum(opponent_avgs) / max(len(opponent_avgs), 1)
    return round(max(-3.0, min(3.0, (player_avg - rival) * 0.06)), 2)
