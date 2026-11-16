"""Régua de escala: o motor confere o tamanho do que o texto afirma, em proporção ao país.

A IA entende o que o jogador quer; o custo só vale se aparecer no texto (measure_validation). Esta régua mede esse
valor contra o PIB de referência e o orçamento de investimento da partida, avisa quando a proposta é grande demais
para o instrumento e confere o benefício declarado ("gera R$ 15 bi de renda") contra o que o custo costuma render.
Faixas e multiplicadores são parâmetros de design, não estimativas econômicas.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any

# Faixas de custo em % do PIB de referência: (limite superior, rótulo, descrição)
TIERS = [
    (0.02, "pequeno", "cabe em um orçamento corrente"),
    (0.20, "medio", "exige remanejar recursos e acompanhar a execução"),
    (0.80, "grande", "exige fonte de custeio clara e aprovação do Congresso"),
    (2.00, "muito_grande", "é um programa de Estado: pede lei, fonte de custeio e anos de execução"),
]
LEGAL_INSTRUMENTS = {"Projeto de Lei", "Projeto de Lei Complementar", "PEC"}


def _plain(text: str) -> str:
    return "".join(ch for ch in unicodedata.normalize("NFD", text.lower()) if unicodedata.category(ch) != "Mn")


def _br(value: float, digits: int = 1) -> str:
    return f"{value:,.{digits}f}".replace(",", "X").replace(".", ",").replace("X", ".")


_NUM = r"(\d+(?:\.\d{3})*(?:,\d+)?|\d+(?:\.\d+)?)"
_UNIT = r"\s*(bilh\w+|bi|milh\w+|mi)\b"
_BEFORE = re.compile(r"\b(?:gera\w*|rend\w*|ganho\w*|retorno\w*|arrecad\w*|aumento\w*)\s+(?:de\s+)?(?:renda\s+|receita\s+)?(?:de\s+)?(?:r\$\s*)?" + _NUM + _UNIT)
_AFTER = re.compile(r"(?:r\$\s*)?" + _NUM + _UNIT + r"\s+(?:de|em)\s+(?:renda|receita|arrecadacao|beneficio)")


def _number(raw: str) -> float:
    return float(raw.replace(".", "").replace(",", ".")) if "," in raw or re.fullmatch(r"\d+(?:\.\d{3})+", raw) else float(raw)


def benefit_number_starts(plain: str) -> set[int]:
    """Posições (no texto já normalizado) dos números ligados a benefício: eles nunca contam como custo."""
    return {m.start(1) for pattern in (_BEFORE, _AFTER) for m in pattern.finditer(plain)}


def declared_benefit_bi(text: str) -> float:
    """Soma valores ligados a benefício ("gera R$ 15 bi", "15 bilhões de renda"), em R$ bilhões. O custo não entra."""
    source = _plain(text)
    found: dict[int, float] = {}
    for pattern in (_BEFORE, _AFTER):
        for match in pattern.finditer(source):
            value = _number(match.group(1))
            found[match.start(1)] = value if match.group(2).startswith(("bi", "bilh")) else value / 1000
    return round(sum(found.values()), 3)


def check(cost_bi: float, duration_days: int, instrument: str, text: str, *, gdp_bi: float, investment_bi: float) -> dict[str, Any]:
    cost = max(0.0, float(cost_bi or 0))
    benefit = declared_benefit_bi(text)
    warnings: list[str] = []
    share = cost / gdp_bi * 100 if gdp_bi else 0.0
    verdict, meaning = "sem_custo", "nenhum valor foi declarado; o motor usa custo zero"
    if cost > 0:
        verdict, meaning = "fora_de_escala", "passa de 2% do PIB de uma só vez; nenhum governo faz isso em um ato"
        for limit, label, text_ in TIERS:
            if share <= limit:
                verdict, meaning = label, text_
                break
    message = ""
    if cost > 0:
        message = f"R$ {_br(cost, 1 if cost < 100 else 0)} bi equivalem a {_br(share, 2)}% do PIB de referência: {meaning}."
        if investment_bi and cost >= investment_bi:
            warnings.append(f"É {_br(cost / investment_bi, 1)} vez(es) o orçamento anual de investimento da partida (R$ {_br(investment_bi, 0)} bi): sem remanejamento ou novas receitas, não fecha.")
        if verdict in {"grande", "muito_grande", "fora_de_escala"} and instrument not in LEGAL_INSTRUMENTS:
            warnings.append("Um valor desse tamanho costuma exigir lei ou emenda constitucional; um ato executivo isolado não basta.")
        if verdict in {"muito_grande", "fora_de_escala"} and duration_days and duration_days < 365:
            warnings.append("Gastar isso em menos de um ano não é realista; programas desse porte levam anos para executar.")
    ratio = None
    if benefit > 0 and cost > 0:
        ratio = round(benefit / cost, 2)
        if ratio > 3:
            warnings.append(f"O texto promete R$ {_br(benefit, 1)} bi de benefício para R$ {_br(cost, 1)} bi de custo ({_br(ratio, 1)} vezes). Programas reais ficam, em geral, entre 0,5 e 2 vezes; o motor usa a própria régua de efeitos e não aceita o número do texto.")
    elif benefit > 0:
        message = (message + " " if message else "") + f"O texto cita R$ {_br(benefit, 1)} bi de benefício, mas nenhum custo: o motor não conta benefício sem custo declarado."
    return {"verdict": verdict, "message": message, "cost_bi": round(cost, 3), "share_of_gdp_pct": round(share, 3), "declared_benefit_bi": benefit,
            "benefit_to_cost": ratio, "warnings": warnings, "reference_gdp_bi": gdp_bi}
