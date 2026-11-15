"""Horário eleitoral gratuito: o tempo de rádio e TV de cada legenda.

Regra simplificada da lei eleitoral: 90% do tempo é dividido em proporção à bancada da legenda na Câmara dos
Deputados e 10% é dividido igualmente entre as legendas com representação. Quem não tem bancada fica só com a parte
igual. O efeito no jogo é pequeno e limitado: o tempo de TV amplia (ou reduz) um pouco o alcance positivo das
atividades de campanha; não decide a eleição sozinho. Os números de cadeiras vêm da Câmara carregada no jogo.
"""
from __future__ import annotations

from typing import Any

from . import legislature

PROPORTIONAL_PART = 0.90
FACTOR_RANGE = (0.92, 1.12)
FACTOR_SENSITIVITY = 0.12


def share(party: str | None) -> dict[str, Any]:
    parties = [p for p in legislature.PARTIES if p["seats"] > 0]
    total = sum(p["seats"] for p in parties) or 1
    equal_pool = (1 - PROPORTIONAL_PART) * 100
    count = len(parties) + (0 if any(p["id"] == party for p in parties) else 1)
    equal = equal_pool / max(1, count)
    seats = next((p["seats"] for p in parties if p["id"] == party), 0)
    proportional = PROPORTIONAL_PART * 100 * seats / total
    pct = round(proportional + equal, 2)
    baseline = 100 / max(1, count)
    factor = max(FACTOR_RANGE[0], min(FACTOR_RANGE[1], 1 + FACTOR_SENSITIVITY * (pct / baseline - 1)))
    return {"share_pct": pct, "seats": seats, "total_seats": total, "equal_pct": round(equal, 2), "proportional_pct": round(proportional, 2),
            "parties": count, "factor": round(factor, 3),
            "text": (f"Sua legenda tem {seats} deputados federais e fica com cerca de {str(round(pct, 1)).replace('.', ',')}% do horário eleitoral gratuito."
                     if seats else f"Sua legenda não tem bancada na Câmara e fica só com a parte igual, cerca de {str(round(pct, 1)).replace('.', ',')}% do horário eleitoral gratuito.")}


def apply(delta: float, party: str | None) -> float:
    """Amplia (ou reduz) só o ganho positivo de uma atividade; perdas não mudam."""
    return delta * share(party)["factor"] if delta > 0 else delta
