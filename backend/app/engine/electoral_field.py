"""Campo de candidatos de uma eleição majoritária: quem disputa de verdade, com a força real de cada partido no território.

Antes, os rivais eram três partidos sorteados de uma lista fixa, e o que sobrava de "100 menos o apoio do jogador" era
dividido entre eles ao acaso (inclusive com candidato do mesmo partido do jogador). Agora:

- os rivais saem dos partidos que mais votaram na última eleição daquele cargo e território (votos do TSE, 2014 a 2024),
  sem o partido do jogador; são candidaturas simuladas, sem pessoas reais;
- cada rival tem posição no espectro (a mesma classificação editorial do Congresso) e um tema de foco;
- quando o jogador sobe nas pesquisas, perdem mais os rivais mais próximos dele no espectro (competição espacial);
- ataques do jogador a um rival (lidos do discurso) pressionam esse rival por algumas semanas.

A distribuição é simulação: a base real só define a força inicial de cada partido, não decide o resultado.
"""
from __future__ import annotations

import math
import random
from typing import Any

from . import elector
from .legislature import PARTY_PROFILE

MAJORITARIAN = {"prefeito", "governador", "senador", "presidente"}
MUNICIPAL_YEARS = (2024, 2020, 2016)
GENERAL_YEARS = (2022, 2018, 2014)
SPECTRUM = {"Esquerda": -1.0, "Centro-esquerda": -0.5, "Centro": 0.0, "Centro-direita": 0.5, "Direita": 1.0}
LABELS = [(-0.75, "Esquerda"), (-0.25, "Centro-esquerda"), (0.25, "Centro"), (0.75, "Centro-direita"), (9.0, "Direita")]
FOCUS = {"PRTB": "seguranca", "DC": "seguranca", "PT": "economia", "PSOL": "integridade", "PSB": "educacao", "MDB": "saude", "PSD": "mobilidade", "PP": "mobilidade", "PL": "seguranca",
         "NOVO": "economia", "PSDB": "saude", "UNIÃO": "seguranca", "UNIAO": "seguranca", "REPUBLICANOS": "seguranca", "PDT": "educacao", "PCdoB": "economia",
         "PRTB": "seguranca", "PODE": "seguranca", "CIDADANIA": "integridade", "AVANTE": "economia", "SOLIDARIEDADE": "economia", "PV": "integridade", "REDE": "integridade"}
FOCUS_LABEL = {"seguranca": "segurança pública", "economia": "economia e custo de vida", "integridade": "transparência e integridade", "educacao": "educação", "saude": "saúde",
               "mobilidade": "mobilidade", "trabalho": "trabalho e renda", "servicos": "serviços públicos"}
FALLBACK_POOL = ["PT", "MDB", "PSD", "PL", "PSB", "PP", "PSDB", "NOVO", "PSOL", "UNIÃO", "REPUBLICANOS", "PDT"]
DEFAULT_PLAYER_SHARE = 8.0
# Siglas fora da tabela do Congresso, com posição aproximada no espectro (classificação editorial, não oficial).
EXTRA_POSITION = {"PRTB": 0.85, "DC": 0.75, "PATRIOTA": 0.7, "PSC": 0.7, "PTB": 0.5, "AGIR": 0.4, "PMB": 0.2, "MOBILIZA": 0.1, "PMN": 0.0, "PROS": -0.2,
                  "PC do B": -0.85, "PCDOB": -0.85, "PCO": -1.0, "PSTU": -1.0, "UP": -1.0, "PCB": -1.0, "DEMOCRATA": 0.5}


def position(party: str | None, ideology: str | None = None) -> float:
    if party and party in PARTY_PROFILE:
        return float(PARTY_PROFILE[party][0])
    if party in EXTRA_POSITION:
        return EXTRA_POSITION[party]
    return SPECTRUM.get(ideology or "Centro", 0.0)


def label_of(pos: float) -> str:
    return next(name for limit, name in LABELS if pos < limit)


def focus_of(party: str, pos: float) -> str:
    if party in FOCUS:
        return FOCUS[party]
    return "economia" if pos < -0.25 else "seguranca" if pos > 0.25 else "saude"


def _scope(career: dict[str, Any]) -> dict[str, Any]:
    office = career.get("office")
    if office == "prefeito":
        return {"scope": "municipio", "uf": career.get("state_code"), "municipality_id": str(career.get("municipality_id") or ""), "municipality": career.get("municipality")}
    if office in {"governador", "senador"}:
        return {"scope": "uf", "uf": career.get("state_code")}
    return {"scope": "brasil"}


def real_party_shares(career: dict[str, Any]) -> tuple[int, dict[str, float]] | None:
    """Votos nominais do primeiro turno da última eleição disponível, somados por partido (% dos votos nominais)."""
    office = career.get("office")
    if office not in MAJORITARIAN:
        return None
    if office == "prefeito" and not (career.get("municipality") and career.get("municipality_id")):
        return None
    for year in (MUNICIPAL_YEARS if office == "prefeito" else GENERAL_YEARS):
        try:
            if not elector.votes_available(year):
                continue
            res = elector.official_results(year, office, _scope(career), 80)
        except Exception:  # base sem as tabelas do TSE
            return None
        if not res.get("available") or not res.get("rounds"):
            continue
        shares: dict[str, float] = {}
        for c in res["rounds"][0]["candidates"]:
            party = str(c.get("party") or "").strip()
            if party:
                shares[party] = shares.get(party, 0.0) + float(c.get("share_pct") or 0.0)
        if shares:
            return year, shares
    return None


def build_field(career: dict[str, Any]) -> list[dict[str, Any]]:
    player_party = career.get("party")
    seed = random.Random(f"{career.get('seed', 1)}:field:{career.get('office', '')}:{career.get('state_code', '')}:{career.get('municipality_id', '')}")
    real = real_party_shares(career)
    year = None
    if real:
        year, shares = real
        ranked = sorted(((p, s) for p, s in shares.items() if p != player_party and s >= 1.5), key=lambda item: -item[1])
        rivals = ranked[:5]
        p0 = shares.get(player_party) or DEFAULT_PLAYER_SHARE
        if len(rivals) < 3:  # base com poucos partidos: completa com partidos fortes que não estão na lista
            extra = [p for p in FALLBACK_POOL if p != player_party and p not in dict(rivals)]
            seed.shuffle(extra)
            rivals += [(p, 4.0) for p in extra[: 3 - len(rivals)]]
    else:
        pool = [p for p in FALLBACK_POOL if p != player_party]
        seed.shuffle(pool)
        rivals = [(p, seed.uniform(12, 30)) for p in pool[:3]]
        p0 = DEFAULT_PLAYER_SHARE
    p0 = max(5.0, min(35.0, float(p0)))
    total = sum(s for _, s in rivals) or 1.0
    scale = (100.0 - p0) / total
    my_pos = position(player_party, career.get("ideology"))
    field = []
    for index, (party, share) in enumerate(rivals):
        pos = position(party)
        field.append({"id": f"opponent-{index + 1}", "name": f"Candidato(a) do {party}", "party": party, "ideology": label_of(pos), "position": round(pos, 2),
                      "issue_focus": focus_of(party, pos), "support_weight": round(share * scale, 3), "real_share_pct": round(share, 2),
                      "proximity": round(1 - abs(pos - my_pos) / 2, 3), "pressure": 0.0, "simulated": True})
    career["field_baseline"] = round(p0, 2)
    career["field_reference_year"] = year
    return field


def ensure_field(career: dict[str, Any]) -> list[dict[str, Any]]:
    field = career.get("opponents")
    if isinstance(field, list) and field and career.get("field_v2"):
        return field
    field = build_field(career)
    career["opponents"] = field
    career["field_v2"] = True
    return field


def apply_pressure(career: dict[str, Any], rival_id: str, amount: float) -> None:
    """Ataque que pega (positivo) enfraquece o rival; ataque que gera reação contrária (negativo) o fortalece."""
    for rival in ensure_field(career):
        if rival["id"] == rival_id:
            rival["pressure"] = round(max(-2.0, min(4.0, float(rival.get("pressure", 0.0)) + amount)), 2)


def decay_pressure(career: dict[str, Any], factor: float = 0.92) -> None:
    for rival in ensure_field(career):
        rival["pressure"] = round(float(rival.get("pressure", 0.0)) * factor, 3)


def shares(career: dict[str, Any], player_support: float) -> list[dict[str, Any]]:
    """Divide entre os rivais o que o jogador não tem: os mais próximos dele no espectro perdem mais quando ele cresce."""
    field = ensure_field(career)
    p = max(1.0, min(95.0, float(player_support)))
    p0 = float(career.get("field_baseline") or DEFAULT_PLAYER_SHARE)
    weights = [float(r["support_weight"]) * math.exp(-0.04 * (p - p0) * float(r.get("proximity", 0.5))) * math.exp(-0.12 * float(r.get("pressure", 0.0))) for r in field]
    total_w = sum(weights) or 1.0
    room = round(100.0 - p, 1)
    out, allocated = [], 0.0
    for index, (rival, weight) in enumerate(zip(field, weights)):
        support = round(room - allocated, 1) if index == len(field) - 1 else round(room * weight / total_w, 1)
        allocated += support
        out.append({"id": rival["id"], "name": rival["name"], "party": rival["party"], "ideology": rival["ideology"], "issue_focus": rival["issue_focus"],
                    "support": support, "real_share_pct": rival.get("real_share_pct"), "pressure": rival.get("pressure", 0.0), "simulated": True})
    return out
