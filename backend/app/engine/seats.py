"""Cadeiras em disputa nas eleições proporcionais, pelas regras vigentes.

- Deputados federais: bancada de cada estado (513 no total).
- Deputados estaduais: três vezes a bancada federal até 12 federais; acima disso, a bancada federal mais 24
  (mínimo de 24), como na Constituição (art. 27).
- Vereadores: escala da Constituição (art. 29, IV) pela população do município, de 9 a 55.
Os números de bancada são os da distribuição em vigor desde 2022.
"""
from __future__ import annotations

FEDERAL_SEATS = {
    "SP": 70, "MG": 53, "RJ": 46, "BA": 39, "RS": 31, "PR": 30, "PE": 25, "CE": 22, "PA": 17, "SC": 16, "GO": 17, "MA": 18,
    "PB": 12, "ES": 10, "AM": 8, "RN": 8, "MT": 8, "AL": 9, "PI": 10, "DF": 8, "MS": 8, "SE": 8, "RO": 8, "TO": 8, "AC": 8,
    "AP": 8, "RR": 8,
}
# (população até, vereadores)
VEREADOR_SCALE = [
    (15_000, 9), (30_000, 11), (50_000, 13), (80_000, 15), (120_000, 17), (160_000, 19), (300_000, 21), (450_000, 23),
    (600_000, 25), (750_000, 27), (900_000, 29), (1_050_000, 31), (1_200_000, 33), (1_350_000, 35), (1_500_000, 37),
    (1_800_000, 39), (2_400_000, 41), (3_000_000, 43), (4_000_000, 45), (5_000_000, 47), (6_000_000, 49), (7_000_000, 51),
    (8_000_000, 53),
]
FALLBACK = {"vereador": 13, "deputado_estadual": 24, "deputado_federal": 24}


def vereadores(population: int | None) -> int:
    if not population:
        return FALLBACK["vereador"]
    return next((seats for limit, seats in VEREADOR_SCALE if population <= limit), 55)


def federal(uf: str | None) -> int:
    return FEDERAL_SEATS.get(str(uf or "").upper(), FALLBACK["deputado_federal"])


def estadual(uf: str | None) -> int:
    fed = federal(uf)
    if fed <= 8:
        return 24
    return 3 * fed if fed <= 12 else fed + 24


def for_office(office: str, uf: str | None = None, population: int | None = None) -> int:
    if office == "vereador":
        return vereadores(population)
    if office == "deputado_federal":
        return federal(uf)
    if office == "deputado_estadual":
        return estadual(uf)
    return FALLBACK.get(office, 13)
