"""Deterministic validation for monetary amounts in free-text measures."""
from __future__ import annotations

import re
import unicodedata


_AMOUNT = re.compile(
    r"(?P<currency>R\$\s*)?"
    r"(?P<number>\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:[.,]\d+)?)"
    r"\s*(?P<unit>bilhoes?|bi|milhoes?|mi|mil|reais?)?\b",
    re.IGNORECASE,
)
_COST_CONTEXT = re.compile(
    r"\b(custo(?:s)?|cust(?:a|ar|ara)|gasto(?:s)?|gastar|investir|investimento(?:s)?|"
    r"destinar|destinacao|aplicar|aporte|alocar|alocacao|orcamento|despesa(?:s)?|"
    r"impacto fiscal|financiar|financiamento|subsidio|compensacao|recomposicao)\b",
    re.IGNORECASE,
)
_SAVING_CONTEXT = re.compile(
    r"\b(cortar|corte|reduzir|reducao|economizar|economia|poupar)\b", re.IGNORECASE
)
_SPENDING_CUT = re.compile(
    r"\b(?:cortar|corte|reduzir|reducao|economizar|economia|poupar)\b"
    r"[^.!?\n]{0,48}\b(?:subsidio|despesa|gasto|gastos|custo|custos|orcamento)\b",
    re.IGNORECASE,
)
_TAX_REVENUE_LOSS = re.compile(
    r"\b(?:reduzir|reducao|cortar|corte|isentar|isencao|desonerar|desoneracao|"
    r"renunciar|renuncia|abrir mao de)\b[^.!?\n]{0,52}\b"
    r"(?:imposto(?:s)?|tributo(?:s)?|aliquota(?:s)?|arrecadacao|receita(?:s)?)\b"
    r"|\b(?:imposto(?:s)?|tributo(?:s)?|aliquota(?:s)?|arrecadacao|receita(?:s)?)\b"
    r"[^.!?\n]{0,52}\b(?:reducao|renuncia|isencao|desoneracao)\b",
    re.IGNORECASE,
)
_EXPLICIT_ZERO = re.compile(
    r"\b(?:sem custo fiscal|custo fiscal zero|impacto fiscal neutro|sem impacto fiscal|"
    r"sem custo adicional|sem despesa adicional)\b",
    re.IGNORECASE,
)
_PERSONAL_THRESHOLD = re.compile(
    r"\b(?:ganha|ganham|recebe|recebem|renda|salario|faturamento|rendimentos?)\b"
    r"[^.!?\n]{0,32}\bate\b[^.!?\n]{0,16}$",
    re.IGNORECASE,
)


def _plain(text: str) -> str:
    return "".join(
        char for char in unicodedata.normalize("NFKD", text)
        if not unicodedata.combining(char)
    )


def _number(raw: str) -> float:
    if "," in raw:
        return float(raw.replace(".", "").replace(",", "."))
    if re.fullmatch(r"\d{1,3}(?:\.\d{3})+", raw):
        return float(raw.replace(".", ""))
    return float(raw)


def _nearest_distance(pattern: re.Pattern[str], text: str, amount_start: int, amount_end: int) -> int | None:
    distances: list[int] = []
    for signal in pattern.finditer(text):
        if signal.end() <= amount_start:
            distances.append(amount_start - signal.end())
        elif signal.start() >= amount_end:
            distances.append(signal.start() - amount_end)
        else:
            distances.append(0)
    return min(distances) if distances else None


def extract_explicit_policy_cost_bi(text: str) -> tuple[float, bool]:
    """Return a stated policy expense in R$ billions and whether it was stated.

    This deliberately recognizes only explicit amounts near fiscal-cost language.
    Savings from cutting spending are excluded; tax cuts count as revenue loss.
    It does not estimate a cost when the proposal omits a monetary amount.
    """
    source = _plain(text)
    factors = {
        "bilhao": 1.0, "bilhoes": 1.0, "bi": 1.0,
        "milhao": 0.001, "milhoes": 0.001, "mi": 0.001,
        "mil": 0.000001,
        "real": 0.000000001, "reais": 0.000000001,
    }
    total_bi = 0.0
    found = False
    for match in _AMOUNT.finditer(source):
        currency = match.group("currency")
        unit = (match.group("unit") or "").lower()
        if not currency and not unit:
            continue

        context_start = max(0, match.start() - 64)
        context_end = min(len(source), match.end() + 48)
        context = source[context_start:context_end]
        amount_start = match.start() - context_start
        amount_end = match.end() - context_start
        prefix = source[max(0, match.start() - 48):match.start()]
        if _PERSONAL_THRESHOLD.search(prefix):
            continue
        tax_loss = bool(_TAX_REVENUE_LOSS.search(context))

        if not tax_loss:
            if _SPENDING_CUT.search(source[max(0, match.start() - 64):match.end()]):
                continue
            cost_distance = _nearest_distance(_COST_CONTEXT, context, amount_start, amount_end)
            saving_distance = _nearest_distance(_SAVING_CONTEXT, context, amount_start, amount_end)
            if cost_distance is None or (saving_distance is not None and saving_distance <= cost_distance):
                continue

        amount = _number(match.group("number"))
        factor = factors.get(unit)
        if factor is None:
            factor = factors["reais"] if currency else 1.0
        total_bi += amount * factor
        found = True

    if found:
        return round(min(total_bi, 1000.0), 6), True
    if _EXPLICIT_ZERO.search(source):
        return 0.0, True
    return 0.0, False
