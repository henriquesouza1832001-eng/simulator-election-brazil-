"""Exposição geográfica e sazonal das crises: o que acontece depende de onde o jogador governa e da época do ano.

Cada crise tem estados em risco e meses típicos. Quem governa um estado ou município só recebe a crise se o lugar
estiver na lista (e na estação certa); quem governa o país recebe a crise em um dos estados expostos. As áreas de
risco resumem a geografia real do país (encostas do Sudeste, semiárido do Nordeste, bacias do Sul, barragens de
mineração de Minas e do Pará). Não é previsão de risco nem cadastro oficial.
"""
from __future__ import annotations

import hashlib
from datetime import date
from typing import Any

from .event_templates import IN, OF, STATES

UF_NAME = {uf: name for name, uf, _ in STATES}
NAME_UF = {name: uf for uf, name in UF_NAME.items()}
REGION_OF = {
    **{uf: "norte" for uf in ("AC", "AM", "AP", "PA", "RO", "RR", "TO")},
    **{uf: "nordeste" for uf in ("AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE")},
    **{uf: "centro_oeste" for uf in ("DF", "GO", "MS", "MT")},
    **{uf: "sudeste" for uf in ("ES", "MG", "RJ", "SP")},
    **{uf: "sul" for uf in ("PR", "RS", "SC")},
}
ALL_MONTHS = list(range(1, 13))

# Crises que já vêm do corpus de fatos reais (casadas pelo título): estados expostos e meses típicos.
RULES: list[tuple[str, dict[str, Any]]] = [
    ("rompimento de barragem", {"states": ["MG", "PA", "GO", "BA", "MT", "MS"]}),
    ("enchentes históricas no rio grande do sul", {"states": ["RS", "SC", "PR"], "months": [4, 5, 9, 10, 11]}),
    ("alagamentos", {"months": [11, 12, 1, 2, 3, 4]}),
    ("queimadas", {"states": ["MT", "MS", "GO", "TO", "PA", "AM", "RO", "AC", "MA", "RR", "AP"], "months": [7, 8, 9, 10]}),
    ("crise hídrica", {"states": ["SP", "RJ", "MG", "DF", "GO", "ES"], "months": [6, 7, 8, 9, 10, 11]}),
    ("óleo atinge praias", {"states": ["BA", "SE", "AL", "PE", "PB", "RN", "CE", "PI", "MA"]}),
    ("falta de oxigênio em hospitais de manaus", {"states": ["AM", "RR", "PA", "AC", "RO", "AP"]}),
    ("recorde de casos de dengue", {"states": ["SP", "MG", "GO", "PR", "DF", "RJ", "ES", "MT", "MS"], "months": [1, 2, 3, 4, 5]}),
    ("vendaval deixa milhões sem energia", {"states": ["SP", "RJ", "MG", "RS", "PR", "DF", "SC"], "months": [9, 10, 11, 12]}),
    ("emergência de saúde em território indígena", {"states": ["RR", "AM", "MT", "PA", "MA", "AC", "TO"]}),
]


def exposure(definition: dict[str, Any]) -> dict[str, Any] | None:
    """Estados e meses da crise: o campo `where` do próprio evento ou uma regra pelo título do fato histórico."""
    explicit = definition.get("where")
    if isinstance(explicit, dict):
        return explicit
    title = str(definition.get("title", "")).lower()
    for keyword, rule in RULES:
        if keyword in title:
            return rule
    return None


def player_place(state: dict[str, Any]) -> tuple[str | None, str | None]:
    """UF e município de quem governa um estado ou município; (None, None) para a Presidência."""
    career = state.get("career") or {}
    if not career.get("mode") or career.get("office") in (None, "presidente"):
        return None, None
    uf = str(career.get("state_code") or "").upper() or None
    municipality = career.get("municipality")
    if isinstance(municipality, dict):
        municipality = municipality.get("name")
    return uf, (str(municipality) if municipality else None)


def allowed(definition: dict[str, Any], state: dict[str, Any], day: date) -> bool:
    exp = exposure(definition)
    if not exp:
        return True
    months = exp.get("months")
    if months and day.month not in months:
        return False
    states = exp.get("states")
    uf, _ = player_place(state)
    if states and uf and uf not in states:
        return False
    return True


def weight_factor(definition: dict[str, Any], state: dict[str, Any]) -> float:
    """Quem está numa área exposta vê a crise com mais frequência."""
    exp = exposure(definition)
    uf, _ = player_place(state)
    if exp and exp.get("states") and uf and uf in exp["states"]:
        return 1.8
    return 1.0


def preferred_places(definition: dict[str, Any], state: dict[str, Any]) -> list[str] | None:
    """Estados (por nome) em que o evento pode acontecer nesta partida, para o remix de fatos históricos."""
    exp = exposure(definition)
    if not exp or not exp.get("states"):
        return None
    uf, _ = player_place(state)
    if uf and uf in exp["states"]:
        return [UF_NAME[uf]]
    return [UF_NAME[u] for u in exp["states"] if u in UF_NAME]


def _pick(state: dict[str, Any], key: str, options: list[str]) -> str:
    digest = hashlib.sha256(f"{state.get('campaign_seed', 203001)}|crise|{key}".encode()).digest()
    return options[int.from_bytes(digest[:8], "big") % len(options)]


def place_for(definition: dict[str, Any], state: dict[str, Any], day: date) -> dict[str, str]:
    """Lugar da crise nesta partida: o município e o estado de quem governa, ou um estado exposto (Presidência)."""
    uf, municipality = player_place(state)
    exp = exposure(definition) or {}
    if not uf:
        uf = _pick(state, f"{definition.get('id')}|{day.isoformat()}", [u for u in (exp.get("states") or list(UF_NAME)) if u in UF_NAME])
    name = UF_NAME[uf]
    career_office = (state.get("career") or {}).get("office")
    local = municipality if (municipality and career_office in ("vereador", "prefeito")) else None
    return {"uf": uf, "estado": name, "lugar": local or name, "em_lugar": f"em {local}" if local else IN[name], "de_lugar": f"de {local}" if local else OF[name]}


def fill(text: str, definition: dict[str, Any], state: dict[str, Any], day: date) -> str:
    if "{" not in text:
        return text
    place = place_for(definition, state, day)
    for key in ("em_lugar", "de_lugar", "lugar", "estado", "uf"):
        text = text.replace("{" + key + "}", place[key])
    return text
