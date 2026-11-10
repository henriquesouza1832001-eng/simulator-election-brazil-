"""Meta-jogo: nota do mandato, ranking (Placar da História) e coleção de carimbos.

A fórmula de pontos e a lista de carimbos são desta reconstrução (inspiradas na
descrição pública do jogo de referência, não na regra real, que não foi observada).
Tudo é ajustável nas constantes abaixo.
"""
from __future__ import annotations

from typing import Any, Callable

# Bloco → peso máximo em pontos. Soma 2000 sem o bloco de preço, que só desconta.
WEIGHTS = {"pais": 500, "popularidade": 300, "governar": 300, "mundo": 200, "integridade": 250, "promessas": 250, "preco": 300}
GRADES = [("S", 1500), ("A", 1250), ("B", 1000), ("C", 750), ("D", 500), ("F", -10**9)]
GRADE_TITLES = {"S": "Estadista histórico", "A": "Presidente de peso", "B": "Mandato sólido", "C": "Governo mediano",
                "D": "Mandato frágil", "F": "Desastre nacional"}
DIFFICULTY_MULTIPLIER = {"realismo_puro": 1.13, "complicado": 1.08, "dificil": 1.04, "normal": 1.0, "tranquilo": 0.0}


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def score_mandate(state: dict[str, Any]) -> dict[str, Any]:
    m = state.get("metrics", {})
    soc = state.get("social_indicators", {})
    inst = state.get("institutions", {})
    cal = state.get("legislative_calendar", {})
    pais = (_clamp((soc.get("human_development_index", .785) - .6) / .3) * .3
            + _clamp(1 - soc.get("poverty_rate_pct", 28) / 50) * .25
            + _clamp((soc.get("school_completion_pct", 72) - 50) / 50) * .15
            + _clamp(1 - soc.get("homicide_rate_per_100k", 17) / 40) * .15
            + _clamp((soc.get("sanitation_coverage_pct", 58) - 40) / 60) * .15)
    popularidade = _clamp(float(m.get("approval", 50)) / 100)
    laws = int(cal.get("laws_enacted", 0)); failed = int(cal.get("laws_failed", 0))
    governar = _clamp(float(m.get("governability", 50)) / 100) * .6 + _clamp(laws / max(1, laws + failed + 1)) * .4
    mundo = _clamp(float(m.get("institutional_trust", 50)) / 100)
    integridade = _clamp(float(m.get("integrity", 70)) / 100) * .7 + _clamp(float(inst.get("constitutional_order", 60)) / 100) * .3
    promessas = _clamp(float(m.get("congress_support", 50)) / 100) * .5 + _clamp(float(m.get("gdp_growth", 2)) / 5) * .5
    preco = (_clamp((float(m.get("inflation", 4.5)) - 3) / 10) * .3
             + _clamp((float(m.get("unemployment", 7)) - 6) / 10) * .3
             + _clamp((float(m.get("debt_gdp", 78)) - 70) / 50) * .4)
    blocks = {"pais": pais, "popularidade": popularidade, "governar": governar, "mundo": mundo,
              "integridade": integridade, "promessas": promessas}
    parts = {key: round(WEIGHTS[key] * value) for key, value in blocks.items()}
    parts["preco"] = -round(WEIGHTS["preco"] * preco)
    difficulty = state.get("difficulty", "normal")
    multiplier = DIFFICULTY_MULTIPLIER.get(difficulty, 1.0)
    raw = sum(parts.values())
    points = round(raw * multiplier) if multiplier else 0
    grade = next(letter for letter, floor in GRADES if points >= floor)
    return {"parts": parts, "raw": raw, "multiplier": multiplier, "points": points, "grade": grade,
            "title": GRADE_TITLES[grade], "ranked": multiplier > 0}


def mandate_outcome(state: dict[str, Any]) -> dict[str, str]:
    status = state.get("office_status", "incumbent")
    if status == "detained_after_failed_rupture":
        return {"code": "preso", "title": "Preso após ruptura fracassada"}
    if state.get("regime") != "democratic":
        return {"code": "ruptura", "title": "Governo de fato"}
    election = state.get("election", {}) or {}
    result = election.get("result")
    # O motor guarda o resultado como texto ("won"/"lost"); aceita também um dicionário.
    if isinstance(result, dict):
        won = bool(result.get("won") or result.get("winner") == "player")
        lost = bool(result.get("lost"))
    else:
        won, lost = result == "won", result == "lost"
    if won:
        return {"code": "reeleito", "title": "Reeleito"}
    if lost:
        return {"code": "derrotado", "title": f"Derrotado na eleição (margem {election.get('margin')})" if election.get("margin") is not None else "Derrotado na eleição"}
    if status == "former_president":
        return {"code": "ex", "title": "Fim do mandato"}
    return {"code": "em_curso", "title": "Mandato em curso"}


def build_entry(state: dict[str, Any], campaign_id: str, player_name: str) -> dict[str, Any]:
    character = state.get("player_character") or {}
    score = score_mandate(state)
    outcome = mandate_outcome(state)
    return {
        "chave": f"{campaign_id}:{state.get('term', 1)}",
        "presidente": character.get("name") or "Presidente sem nome",
        "partido": (character.get("party") or "—"),
        "jogador": player_name,
        "nota": score["grade"], "titulo": score["title"], "pontos": score["points"], "partes": score["parts"],
        "aprovacao": round(float(state.get("metrics", {}).get("approval", 0))),
        "pib": state.get("metrics", {}).get("gdp_growth"), "inflacao": state.get("metrics", {}).get("inflation"),
        "dificuldade": state.get("difficulty", "normal"),
        "desfecho": outcome["code"], "desfechoTitulo": outcome["title"],
        "meses": int(state.get("month", 1)), "mandato": int(state.get("term", 1)),
        "ranqueavel": score["ranked"], "simulado": False,
    }


# Entradas de exemplo, claramente fictícias, para o placar não nascer vazio.
SEED_HALL = [
    {"presidente": n, "partido": p, "jogador": "Simulado", "nota": g, "pontos": pts, "aprovacao": a, "dificuldade": d,
     "desfecho": "reeleito" if pts > 1300 else "ex", "desfechoTitulo": "Entrada de exemplo", "meses": 48, "mandato": 1,
     "ranqueavel": True, "simulado": True, "chave": f"seed:{i}"}
    for i, (n, p, g, pts, a, d) in enumerate([
        ("Aurora Menezes", "MDC", "S", 1642, 78, "realismo_puro"), ("Bento Salgado", "PRP", "S", 1588, 74, "complicado"),
        ("Clarice Veiga", "PTR", "A", 1431, 69, "dificil"), ("Domingos Reis", "PSN", "A", 1390, 66, "normal"),
        ("Eunice Prado", "UDB", "A", 1302, 63, "complicado"), ("Fausto Leme", "PLB", "B", 1188, 58, "normal"),
        ("Gláucia Torres", "PSU", "B", 1104, 55, "dificil"), ("Heitor Alcântara", "PAG", "B", 1041, 52, "normal"),
        ("Irene Bastos", "PVE", "C", 890, 47, "normal"), ("Joaquim Pestana", "NVO", "C", 812, 44, "dificil"),
        ("Kátia Macedo", "PDE", "D", 640, 36, "normal"), ("Lauro Siqueira", "PLB", "F", 310, 22, "complicado"),
    ])
]

# Carimbos (coleção). id, título, descrição, raridade (0-100 % de jogadores, estimativa de design), teste.
Test = Callable[[dict[str, Any]], bool]


def _m(state: dict[str, Any], key: str, default: float = 0) -> float:
    return float(state.get("metrics", {}).get(key, default))


STAMPS: list[tuple[str, str, str, str, Test]] = [
    ("primeiro-dia", "Primeiro dia", "Avançou o calendário pela primeira vez.", "comum", lambda s: int(s.get("day_of_mandate", 1)) > 1),
    ("posse-feita", "Faixa no peito", "Registrou o pronunciamento de posse.", "comum",
     lambda s: bool((s.get("communications", {}).get("inauguration", {}) or {}).get("delivered"))),
    ("cem-dias", "Cem dias", "Chegou ao centésimo dia de mandato.", "comum", lambda s: int(s.get("day_of_mandate", 1)) >= 100),
    ("um-ano", "Um ano de Planalto", "Completou 12 meses.", "comum", lambda s: int(s.get("month", 1)) >= 13),
    ("metade", "Meio caminho", "Chegou ao 25º mês.", "incomum", lambda s: int(s.get("month", 1)) >= 25),
    ("quase-la", "Reta final", "Chegou ao 43º mês.", "incomum", lambda s: int(s.get("month", 1)) >= 43),
    ("mandato-completo", "Quatro anos", "Completou os 48 meses.", "incomum", lambda s: int(s.get("day_of_mandate", 1)) >= 1461),
    ("primeira-lei", "Primeira lei", "Teve um projeto aprovado no Congresso.", "comum",
     lambda s: int(s.get("legislative_calendar", {}).get("laws_enacted", 0)) >= 1),
    ("legislador", "Articulador", "Aprovou cinco projetos.", "incomum", lambda s: int(s.get("legislative_calendar", {}).get("laws_enacted", 0)) >= 5),
    ("derrota-plenario", "Derrota no plenário", "Teve um projeto rejeitado.", "comum",
     lambda s: int(s.get("legislative_calendar", {}).get("laws_failed", 0)) >= 1),
    ("pec-aprovada", "Emenda histórica", "Aprovou uma PEC.", "raro",
     lambda s: any(v.get("aprovado") and str(v.get("instrument", "")).lower() == "pec" for v in s.get("legislative_calendar", {}).get("vote_history", []))),
    ("popular", "Popular", "Aprovação acima de 70.", "incomum", lambda s: _m(s, "approval") >= 70),
    ("queridinho", "Queridinho", "Aprovação acima de 85.", "raro", lambda s: _m(s, "approval") >= 85),
    ("impopular", "Vaiado", "Aprovação abaixo de 25.", "incomum", lambda s: _m(s, "approval", 50) <= 25),
    ("fiscal", "O fiscal voltou", "Resultado primário positivo.", "raro", lambda s: _m(s, "primary_balance") > 0),
    ("divida-baixa", "Dívida sob controle", "Dívida abaixo de 70% do PIB.", "raro", lambda s: _m(s, "debt_gdp", 99) < 70),
    ("inflacao-baixa", "Preço estável", "Inflação abaixo de 3%.", "incomum", lambda s: _m(s, "inflation", 99) < 3),
    ("pleno-emprego", "Pleno emprego", "Desemprego abaixo de 5%.", "raro", lambda s: _m(s, "unemployment", 99) < 5),
    ("pibao", "Pibão", "Crescimento do PIB acima de 4%.", "raro", lambda s: _m(s, "gdp_growth") > 4),
    ("recessao", "Recessão", "PIB negativo.", "incomum", lambda s: _m(s, "gdp_growth") < 0),
    ("integro", "Ficha limpa", "Integridade acima de 85.", "raro", lambda s: _m(s, "integrity") > 85),
    ("base-ampla", "Base ampla", "Apoio no Congresso acima de 75.", "raro", lambda s: _m(s, "congress_support") > 75),
    ("sem-base", "Sem base", "Apoio no Congresso abaixo de 30.", "incomum", lambda s: _m(s, "congress_support", 50) < 30),
    ("pobreza-menor", "Menos pobreza", "Pobreza abaixo de 20%.", "raro", lambda s: float(s.get("social_indicators", {}).get("poverty_rate_pct", 99)) < 20),
    ("idh-alto", "IDH em alta", "IDH acima de 0,82.", "raro", lambda s: float(s.get("social_indicators", {}).get("human_development_index", 0)) > .82),
    ("viajante", "Mala pronta", "Fez uma visita diplomática.", "comum", lambda s: bool((s.get("diplomacy", {}) or {}).get("visits"))),
    ("ministerio", "Esplanada montada", "Nomeou um ministro.", "comum",
     lambda s: bool((s.get("appointments", {}) or {}).get("ministers"))),
    ("ruptura", "Tentou o impensável", "Tentou ruptura institucional (cenário fictício).", "raro", lambda s: int(s.get("rupture_attempts", 0)) >= 1),
    ("reeleito", "Mais quatro anos", "Foi reeleito.", "raro", lambda s: mandate_outcome(s)["code"] == "reeleito"),
    ("nota-s", "Estadista", "Fechou o mandato com nota S.", "lendario", lambda s: score_mandate(s)["grade"] == "S" and int(s.get("day_of_mandate", 1)) >= 1461),
    ("brutal", "Sem facilidade", "Jogou no Realismo Puro.", "incomum", lambda s: s.get("difficulty") == "realismo_puro"),
    ("nota-f", "O pior da história", "Fechou o mandato com nota F.", "raro", lambda s: score_mandate(s)["grade"] == "F" and int(s.get("day_of_mandate", 1)) >= 1461),
]


def evaluate_stamps(state: dict[str, Any]) -> list[str]:
    earned = []
    for stamp_id, _title, _desc, _rarity, test in STAMPS:
        try:
            if test(state):
                earned.append(stamp_id)
        except Exception:
            continue
    return earned


def stamp_catalog(unlocked: set[str]) -> list[dict[str, Any]]:
    return [{"id": sid, "titulo": title, "descricao": desc, "raridade": rarity, "obtido": sid in unlocked}
            for sid, title, desc, rarity, _t in STAMPS]


# Diário de atualizações desta reconstrução (não é o diário do jogo de referência).
DIARY: list[dict[str, Any]] = [
    {"versao": "0.3", "data": "2026-11-09", "notas": [
        {"tipo": "novo", "texto": "Câmara com 513 deputados e Senado com 81, com votação nominal e placar por partido."},
        {"tipo": "novo", "texto": "Placar da História com nota de S a F, filtros e detalhamento dos pontos."},
        {"tipo": "novo", "texto": "Coleção de carimbos desbloqueados pelo que acontece no mandato."},
        {"tipo": "novo", "texto": "Diário, planos, termos, créditos e página do Legado."}]},
    {"versao": "0.2", "data": "2026-10-20", "notas": [
        {"tipo": "melhor", "texto": "Orçamento dividido em contas, investimentos e obras."},
        {"tipo": "melhor", "texto": "Campanha de carreira ligada ao calendário."}]},
    {"versao": "0.1", "data": "2026-09-30", "notas": [
        {"tipo": "novo", "texto": "Primeira versão jogável: mandato presidencial, calendário diário e prévia de medidas."}]},
]
