"""Versioned municipality catalog and deterministic city-size game rules."""

from __future__ import annotations

import json
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any


CATALOG_PATH = Path(__file__).resolve().parents[1] / "data" / "municipalities.json"
REGION_NAMES = {
    "N": "norte",
    "NE": "nordeste",
    "CO": "centro_oeste",
    "SE": "sudeste",
    "S": "sul",
}
CITY_SIZE_BANDS = (
    (50_000, "pequeno", "Pequeno porte", 1.15),
    (200_000, "medio", "Médio porte", 1.0),
    (1_000_000, "grande", "Grande porte", 0.85),
    (float("inf"), "metropole", "Metrópole", 0.70),
)


def _normalize(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", value.casefold())
    return "".join(character for character in decomposed if unicodedata.category(character) != "Mn")


@lru_cache(maxsize=1)
def _catalog() -> dict[str, Any]:
    if not CATALOG_PATH.exists():
        raise RuntimeError(f"O catálogo municipal não foi encontrado: {CATALOG_PATH}")
    data = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    return data


@lru_cache(maxsize=1)
def _by_code() -> dict[str, dict[str, Any]]:
    return {str(item["ibge_code"]): item for item in _catalog()["municipalities"]}


@lru_cache(maxsize=1)
def _by_state_and_name() -> dict[tuple[str, str], list[dict[str, Any]]]:
    index: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for item in _catalog()["municipalities"]:
        key = (item["state_code"], _normalize(item["name"]))
        index.setdefault(key, []).append(item)
    return index


def _profile(item: dict[str, Any]) -> dict[str, Any]:
    population = int(item["population_estimate"])
    _, size_key, size_label, reach_multiplier = next(
        band for band in CITY_SIZE_BANDS if population <= band[0]
    )
    return {
        "ibge_code": str(item["ibge_code"]),
        "name": item["name"],
        "state_code": item["state_code"],
        "state_name": item["state_name"],
        "macroregion": REGION_NAMES[item["region_code"]],
        "population_estimate": population,
        "population_reference_year": int(item["population_reference_year"]),
        "city_size": size_key,
        "city_size_label": size_label,
        "municipal_campaign_reach_multiplier": reach_multiplier,
        "anchor_issues": {},
        "data_source": item["population_source"],
    }


def get_municipality(ibge_code: str | int) -> dict[str, Any] | None:
    item = _by_code().get(str(ibge_code))
    return _profile(item) if item else None


def resolve_municipality(state_code: str, name: str) -> dict[str, Any] | None:
    """Resolve a legacy free-text name only when it maps uniquely within the UF."""
    matches = _by_state_and_name().get((state_code.upper(), _normalize(name.strip())), [])
    return _profile(matches[0]) if len(matches) == 1 else None


def municipality_options(state_code: str = "", query: str = "", limit: int = 20) -> list[dict[str, Any]]:
    state_code = state_code.upper().strip()
    normalized_query = _normalize(query.strip())
    if not state_code and len(normalized_query) < 2:
        return []

    matches = []
    for item in _catalog()["municipalities"]:
        if state_code and item["state_code"] != state_code:
            continue
        normalized_name = _normalize(item["name"])
        if normalized_query and normalized_query not in normalized_name:
            continue
        matches.append(item)

    if normalized_query:
        matches.sort(key=lambda item: (
            0 if _normalize(item["name"]) == normalized_query else
            1 if _normalize(item["name"]).startswith(normalized_query) else 2,
            _normalize(item["name"]),
        ))
    return [_profile(item) for item in matches[:max(1, min(limit, 50))]]


def catalog_metadata() -> dict[str, Any]:
    metadata = _catalog()["metadata"]
    return {
        "source": metadata["population_source"],
        "reference_date": metadata["population_reference_date"],
        "count": len(_catalog()["municipalities"]),
    }
