"""Opções de cargo e validação do nome do partido.

Parte do ciclo de carreira (antes tudo em career.py; ver career.py, que reexporta estes nomes).
"""
from __future__ import annotations


import re
import unicodedata
import json
from datetime import date, timedelta
from typing import Any

from .career_base import (
    ACTIVITIES,
    APPOINTED_PATHS,
    CUSTOM_PARTY_BLOCKLIST,
    IDEOLOGY_SPECTRUM,
    ISSUES,
    OFFICES,
    PARTY_CATALOG_PATH,
    SERVICE_AREAS,
    STATES,
    _inauguration_date,
    _regular_election_day,
)


def career_options(as_of: date | None = None) -> dict[str, Any]:
    as_of = as_of or date(2027, 1, 1)
    party_data = json.loads(PARTY_CATALOG_PATH.read_text(encoding="utf-8"))
    return {
        "offices": [{"key": key, **{name: value for name, value in role.items() if name != "fund_mi"}, "campaign_fund_mi": role["fund_mi"]} for key, role in OFFICES.items()],
        "calendar_previews": {key: {
            "election_date": _regular_election_day(key, as_of).isoformat(),
            "campaign_start": (_regular_election_day(key, as_of) - timedelta(days=90)).isoformat(),
            "inauguration_date": _inauguration_date(key, _regular_election_day(key, as_of)).isoformat(),
            "cycle_label": "Ciclo municipal" if key in {"vereador", "prefeito"} else "Ciclo geral",
        } for key in OFFICES},
        "states": [{"code": code, "name": name, "region": region} for code, name, region in STATES],
        "parties": [f"{item['acronym']} — {item['name']}" for item in party_data["parties"]],
        "party_source": {"label": "Partidos registrados no TSE", "url": party_data["metadata"]["source_url"], "checked_on": party_data["metadata"]["checked_on"]},
        "ideologies": list(IDEOLOGY_SPECTRUM),
        "issues": [{"key": key, "label": item["label"]} for key, item in ISSUES.items()],
        "activities": [{"key": key, "label": item["label"], "days": item["days"], "cost_mi": item["cost"]} for key, item in ACTIVITIES.items()],
        "appointment_paths": APPOINTED_PATHS,
        "service_areas": SERVICE_AREAS,
        "simulated_notice": "Candidatos, partidos, pesquisas e resultados desta carreira são criados para a simulação. Não representam pesquisa ou endosso real.",
    }


def validate_party_name(party: str) -> str:
    party = re.sub(r"\s+", " ", str(party or "")).strip()
    normalized = unicodedata.normalize("NFKD", party).encode("ascii", "ignore").decode("ascii").lower()
    if len(party) < 3 or len(party) > 80:
        raise ValueError("O nome do partido precisa ter de 3 a 80 caracteres.")
    if any(term in normalized for term in CUSTOM_PARTY_BLOCKLIST):
        raise ValueError("Esse nome não está disponível para partidos personalizados.")
    return party
