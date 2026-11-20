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


def share(party: str | None, extra_parties: list[str] | None = None) -> dict[str, Any]:
    """Tempo de TV da legenda; numa coligação soma o tempo de todos os partidos da chapa (lei eleitoral: as legendas coligadas somam os tempos)."""
    parties = [p for p in legislature.PARTIES if p["seats"] > 0]
    total = sum(p["seats"] for p in parties) or 1
    equal_pool = (1 - PROPORTIONAL_PART) * 100
    count = len(parties) + (0 if any(p["id"] == party for p in parties) else 1)
    equal = equal_pool / max(1, count)
    chapa = [party] + [p for p in (extra_parties or []) if p != party]
    seats = sum(next((p["seats"] for p in parties if p["id"] == member), 0) for member in chapa)
    proportional = PROPORTIONAL_PART * 100 * seats / total
    pct = round(min(70.0, proportional + equal * len(chapa)), 2)
    baseline = 100 / max(1, count)
    factor = max(FACTOR_RANGE[0], min(FACTOR_RANGE[1], 1 + FACTOR_SENSITIVITY * (pct / baseline - 1)))
    pct_txt = str(round(pct, 1)).replace(".", ",")
    if len(chapa) > 1:
        text = f"Sua coligação ({', '.join(chapa)}) soma {seats} deputados federais e fica com cerca de {pct_txt}% do horário eleitoral gratuito."
    elif seats:
        text = f"Sua legenda tem {seats} deputados federais e fica com cerca de {pct_txt}% do horário eleitoral gratuito."
    else:
        text = f"Sua legenda não tem bancada na Câmara e fica só com a parte igual, cerca de {pct_txt}% do horário eleitoral gratuito."
    return {"share_pct": pct, "seats": seats, "total_seats": total, "equal_pct": round(equal * len(chapa), 2), "proportional_pct": round(proportional, 2),
            "parties": count, "factor": round(factor, 3), "coalition": chapa if len(chapa) > 1 else [], "text": text}


def apply(delta: float, party: str | None, extra_parties: list[str] | None = None) -> float:
    """Amplia (ou reduz) só o ganho positivo de uma atividade; perdas não mudam."""
    return delta * share(party, extra_parties)["factor"] if delta > 0 else delta
