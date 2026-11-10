"""Remix determinístico de eventos inspirados em fatos reais.

Objetivo: o mesmo episódio histórico nunca se repete igual em duas partidas. Ao disparar um evento de origem
histórica, a instância ganha lugar, intensidade e redação próprios, calculados por hash da semente da partida,
do evento e do dia. Resultado: imprevisível para quem conhece a história real, reproduzível para a mesma partida.

- Estados reais citados no texto são trocados por outro estado (preposição ajustada).
- Cidades específicas viram referências genéricas.
- Anos explícitos são removidos (o evento não pertence a uma época).
- A intensidade (leve, média, grave) escala efeitos e custo.
"""
from __future__ import annotations

import hashlib
import re
from typing import Any

from .event_schema import EFFECT_LIMITS, INST_LIMIT, PP_ENERGY_LIMIT, PP_LIMIT, REL_LIMIT
from .event_templates import IN, OF, STATES

HISTORICAL_SOURCES = {"historico_inspirado", "gemini"}
INTENSITIES = [("leve", 0.7, 0.30), ("média", 1.0, 0.45), ("grave", 1.5, 0.25)]   # rótulo, multiplicador, peso
CITY_REPLACEMENTS = [
    (r"\b(em|de|no|na|do|da) Manaus\b", lambda m: {"em": "em uma capital", "no": "em uma capital", "na": "em uma capital"}.get(m.group(1), "de uma capital")),
    (r"\bManaus\b", lambda m: "uma capital"),
    (r"\b(em|de|no|na|do|da) Brumadinho\b", lambda m: "em uma cidade do interior" if m.group(1) in ("em", "no", "na") else "de uma cidade do interior"),
    (r"\bBrumadinho\b", lambda m: "uma cidade do interior"),
]
_STATE_NAMES = sorted((n for n, _, _ in STATES), key=len, reverse=True)
_STATE_RE = re.compile(r"\b(?:(em|no|na|do|da|de) )?(" + "|".join(re.escape(n) for n in _STATE_NAMES) + r")\b")
_YEAR_RE = re.compile(r"\s*\b(19|20)\d{2}\b")


def _u(state: dict[str, Any], key: str) -> float:
    digest = hashlib.sha256(f"{state.get('campaign_seed', 203001)}|remix|{key}".encode()).digest()
    return int.from_bytes(digest[:8], "big") / 2 ** 64


def is_historical(definition: dict[str, Any]) -> bool:
    return definition.get("source", {}).get("type") in HISTORICAL_SOURCES


def _pick_intensity(state: dict[str, Any], key: str) -> tuple[str, float]:
    r = _u(state, key + "|intensity")
    acc = 0.0
    for label, mult, weight in INTENSITIES:
        acc += weight
        if r < acc:
            return label, mult
    return INTENSITIES[-1][0], INTENSITIES[-1][1]


def remap_places(text: str, state: dict[str, Any], key: str, mapping: dict[str, str]) -> str:
    """Troca estados reais por outros estados, de forma consistente dentro do mesmo evento."""
    names = [n for n, _, _ in STATES]

    def pick(original: str) -> str:
        if original not in mapping:
            options = [n for n in names if n != original and n not in mapping.values()] or [n for n in names if n != original]
            mapping[original] = options[int(_u(state, f"{key}|place|{original}") * len(options)) % len(options)]
        return mapping[original]

    def repl(m: re.Match) -> str:
        prep, original = m.group(1), m.group(2)
        alt = pick(original)
        if prep in ("em", "no", "na"):
            return IN[alt]
        if prep in ("do", "da", "de"):
            return OF[alt]
        return alt

    text = _STATE_RE.sub(repl, text)
    for pattern, fn in CITY_REPLACEMENTS:
        text = re.sub(pattern, fn, text)
    return _YEAR_RE.sub("", text)


def _cap(key: str, value: float) -> float:
    if key.startswith("inst:"):
        limit = INST_LIMIT
    elif key.startswith("rel:"):
        limit = REL_LIMIT
    elif key == "pp:energy":
        limit = PP_ENERGY_LIMIT
    elif key.startswith("pp:"):
        limit = PP_LIMIT
    else:
        limit = EFFECT_LIMITS.get(key, 99.0)
    return max(-limit, min(limit, value))


def scale_effects(effects: dict[str, float], k: float) -> dict[str, float]:
    return {key: round(_cap(key, value * k), 3) for key, value in effects.items() if round(value * k, 3)}


def remix(definition: dict[str, Any], state: dict[str, Any], day_iso: str) -> dict[str, Any]:
    """Devolve título, texto, intensidade e mapa de lugares próprios desta instância."""
    key = f"{definition['id']}|{day_iso}"
    mapping: dict[str, str] = {}
    label, mult = _pick_intensity(state, key)
    title = remap_places(definition["title"], state, key, mapping)
    text = remap_places(definition["text"], state, key, mapping)
    suffix = {"leve": " O episódio tem proporção contida.", "média": "", "grave": " O episódio ganha proporção grave e atrai atenção nacional."}[label]
    return {"title": title.strip(), "text": (text + suffix).strip(), "intensity": mult, "intensity_label": label, "places": mapping}
