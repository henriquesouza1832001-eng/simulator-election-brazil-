"""Perguntas que reproduzem como o país funciona: quem decide o quê, por qual instrumento e com qual limite.

Fontes do conteúdo (nada é escrito à mão sobre números):
  - indicadores atuais do país ou da cidade (motor unificado e Atlas);
  - alavancas de cada cargo no registro de indicadores (`levers`): a pergunta cita o instrumento real do cargo;
  - o Congresso: projetos em tramitação, quórum exigido e a base do governo;
  - "pegadinhas" de competência: perguntas sobre algo que o cargo não decide (ex.: prefeito e Selic), em que a boa
    resposta reconhece o limite e diz o que o cargo faz.
"""
from __future__ import annotations

import hashlib
from typing import Any

from .indicator_registry import REGISTRY

UNIT = {"%": "%", "% a.a.": "% ao ano", "% do PIB": "% do PIB", "0 a 100": " de 100", "0 a 1": "", "por mil": " por mil nascidos", "anos": " anos", "R$": " reais", "por 100 mil": " por 100 mil habitantes"}
QUORUM = {"pec": "3/5 dos votos em dois turnos nas duas casas", "projeto de lei complementar": "maioria absoluta nas duas casas", "projeto de lei": "maioria simples nas duas casas"}
TRAPS: dict[str, list[dict[str, Any]]] = {
    "vereador": [{"target": "juros", "prompt": "O senhor ou a senhora promete reduzir a taxa básica de juros do país?"},
                 {"target": "seguranca", "prompt": "Como o seu mandato vai reformar a polícia militar do estado?"}],
    "prefeito": [{"target": "inflacao", "prompt": "Qual será a sua meta de inflação para o país?"},
                 {"target": "seguranca", "prompt": "O senhor ou a senhora vai mudar a política de armas e munições?"}],
    "deputado_estadual": [{"target": "salario_minimo", "prompt": "O senhor ou a senhora vai definir o salário mínimo nacional?"},
                          {"target": "juros", "prompt": "O que a Assembleia fará para baixar a Selic?"}],
    "governador": [{"target": "balanca_comercial", "prompt": "O senhor ou a senhora vai negociar o acordo comercial com a China?"},
                   {"target": "juros", "prompt": "Qual será a sua política para os juros do Banco Central?"}],
    "deputado_federal": [{"target": "seguranca", "prompt": "O senhor ou a senhora vai assinar o decreto que muda a atuação da polícia no seu estado?"},
                         {"target": "saneamento_basico", "prompt": "O senhor ou a senhora vai executar as obras de esgoto da sua região?"}],
    "senador": [{"target": "saneamento_basico", "prompt": "O senhor ou a senhora vai executar as obras de saneamento do seu estado?"},
                {"target": "mobilidade", "prompt": "Como o seu mandato vai administrar o transporte público da capital?"}],
    "presidente": [{"target": "juros", "prompt": "O senhor ou a senhora vai reduzir a Selic por decreto?"},
                   {"target": "seguranca", "prompt": "O senhor ou a senhora vai comandar diretamente as polícias militares dos estados?"},
                   {"target": "confianca_institucional", "prompt": "O senhor ou a senhora vai mudar a Constituição por decreto, se o Congresso não aprovar?"}],
}


def _roll(seed: str) -> float:
    return int(hashlib.sha256(seed.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF


def current_values(state: dict[str, Any], ctx: dict[str, Any]) -> dict[str, float]:
    """Valores atuais por id do registro: país (motor unificado) ou cidade do cargo (Atlas + efeitos)."""
    if ctx["local"]:
        from . import territory
        mid = (state.get("career") or {}).get("municipality_id")
        try:
            return {i["id"]: float(i["value"]) for i in territory.city_indicators(state, mid)["indicators"]} if mid else {}
        except ValueError:
            return {}
    from . import indicator_engine
    return {k: float(v) for k, v in indicator_engine.ensure(state)["values"].items()}


def _fmt(key: str, value: float) -> str:
    meta = REGISTRY[key]
    digits = 3 if meta["unit"] == "0 a 1" else 1 if abs(value) < 100 else 0
    return f"{value:.{digits}f}{UNIT.get(meta['unit'], ' ' + meta['unit'])}".replace(".", ",")


def lever_questions(state: dict[str, Any], ctx: dict[str, Any], limit: int = 6) -> list[dict[str, Any]]:
    values = current_values(state, ctx)
    office = ctx["office"]
    seed = f"{state.get('campaign_seed', 1)}:{state.get('date')}:{office}"
    rows = []
    for key, meta in REGISTRY.items():
        instrument = meta["levers"].get(office)
        if not instrument or key not in values:
            continue
        rows.append((_roll(seed + key), key, meta, instrument))
    rows.sort()
    out = []
    for _, key, meta, instrument in rows[:limit]:
        value = values[key]
        out.append({"topic": meta["label"].lower(), "target": key, "trap": False, "fact": value,
                    "prompt": f"{meta['label']} está em {_fmt(key, value)}. Nesta função, o cargo age por: {instrument[0].lower() + instrument[1:]}. "
                              "O que o senhor ou a senhora fará, com que instrumento e em quanto tempo?"})
    return out


def process_question(state: dict[str, Any]) -> dict[str, Any] | None:
    bills = (state.get("legislative_calendar") or {}).get("pending_bills") or []
    if not bills:
        return None
    bill = bills[0]
    kind = str(bill.get("instrument", "Projeto de Lei")).lower()
    base = float(state.get("metrics", {}).get("congress_support", 50))
    return {"topic": "tramitação", "target": "base_legislativa", "trap": False, "fact": base,
            "prompt": f"O projeto “{bill['title']}” tramita no Congresso e exige {QUORUM.get(kind, 'maioria simples nas duas casas')}. Sua base está em {base:.0f}%. "
                      "Com quais partidos vai negociar e o que oferece em troca?"}


def trap_question(state: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any] | None:
    options = TRAPS.get(ctx["office"])
    if not options:
        return None
    pick = options[int(_roll(f"{state.get('campaign_seed', 1)}:{state.get('date')}:trap") * len(options)) % len(options)]
    return {"topic": "competência", "target": pick["target"], "trap": True, "fact": None, "prompt": pick["prompt"]}


def country_questions(state: dict[str, Any], ctx: dict[str, Any]) -> list[dict[str, Any]]:
    out = lever_questions(state, ctx)
    proc = process_question(state)
    if proc and not ctx["local"]:
        out.append(proc)
    trap = trap_question(state, ctx)
    if trap:
        out.append(trap)
    if ctx["local"] and ctx["office"] in {"vereador", "prefeito"}:
        from .historical import reference_election
        ref = reference_election(state.get("career") or {})
        if ref and ctx["office"] == "vereador":
            votes = ref["last_elected"]["votes"]
            out.append({"topic": "meta de votos", "target": None, "trap": False, "fact": float(votes),
                        "prompt": f"Em {ref['year']}, o último vereador eleito aqui teve {votes:,} votos. Qual é a sua meta de votos e como vai chegar a ela?".replace(",", ".")})
        elif ref and ctx["office"] == "prefeito":
            votes = ref["winner"]["votes"]
            out.append({"topic": "meta de votos", "target": None, "trap": False, "fact": float(votes),
                        "prompt": f"Em {ref['year']}, o prefeito eleito aqui teve {votes:,} votos. Que coalizão e que prioridades levam o senhor ou a senhora a esse patamar?".replace(",", ".")})
    return out
