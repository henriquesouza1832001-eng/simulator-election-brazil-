"""Criação de uma nova carreira.

Parte do ciclo de carreira (antes tudo em career.py; ver career.py, que reexporta estes nomes).
"""
from __future__ import annotations


from datetime import date, timedelta
from typing import Any

from .communications import ensure_communications_state
from .geography import get_municipality, resolve_municipality
from .career_base import (
    FAMILY_GROUP_EFFECTS,
    GROUPS,
    IDEOLOGY_SPECTRUM,
    OFFICES,
    SPECTRUM_GROUP_EFFECTS,
    SPECTRUM_ORDER,
    STATE_CAPITALS,
    STATE_NAMES,
    STATE_REGIONS,
    _clamp,
    _inauguration_date,
    _regular_election_day,
    _term_end_date,
)
from .career_setup import (
    validate_party_name,
)
from .career_polls import (
    _ensure_opponents,
    _record_public_poll,
)


def start_career(state: dict[str, Any], office: str, state_code: str, municipality: str,
                 party: str, ideology: str, candidate_name: str,
                 character: dict[str, Any] | None = None,
                 municipality_id: str | None = None, election_year: int | None = None) -> dict[str, Any]:
    if office not in OFFICES:
        raise ValueError("Escolha um cargo eletivo disponível.")
    if state_code not in STATE_NAMES:
        raise ValueError("Escolha uma unidade da federação válida.")
    role = OFFICES[office]
    party = validate_party_name(party)
    if ideology not in IDEOLOGY_SPECTRUM:
        raise ValueError("Escolha uma linha partidária disponível na simulação.")
    municipality = (municipality or "").strip()
    municipality_profile = get_municipality(municipality_id) if municipality_id else None
    if municipality_id and not municipality_profile:
        raise ValueError("O código IBGE do município não existe no catálogo carregado.")
    if municipality_profile and municipality_profile["state_code"] != state_code:
        raise ValueError("O município escolhido não pertence ao estado da candidatura.")
    if municipality_profile:
        municipality = municipality_profile["name"]
    elif municipality:
        municipality_profile = resolve_municipality(state_code, municipality)
        if not municipality_profile:
            raise ValueError("Escolha um município válido no catálogo oficial; texto livre não identifica uma cidade.")
        municipality_id = municipality_profile["ibge_code"]
        municipality = municipality_profile["name"]
    elif role["scope"] == "municipal":
        raise ValueError("Para vereador e prefeito, escolha o município da candidatura.")
    today = date.fromisoformat(state["date"])
    character = character or {}
    spectrum = character.get("political_spectrum", "centro")
    family = character.get("family_background", "classe_media")
    traits = [trait for trait in character.get("traits", []) if trait in {"carismatica", "tecnica", "conciliadora", "combativa", "gestora", "comunitaria"}][:2]
    customs = [custom for custom in character.get("customs", []) if custom in {"vida_comunitaria", "vida_urbana", "vida_rural", "fe_presente", "cultura_popular", "vida_sindical", "voluntariado", "esporte_local", "migracao"}][:3]
    birthplace_id = character.get("birth_municipality_id") or (character.get("birthplace") or {}).get("municipality_id")
    birthplace_state = str(character.get("birth_state_code") or (character.get("birthplace") or {}).get("state_code") or "").upper()
    birthplace_profile = get_municipality(birthplace_id) if birthplace_id else None
    if birthplace_id and not birthplace_profile:
        raise ValueError("A cidade natal precisa ser selecionada no catálogo do IBGE.")
    if birthplace_id and birthplace_state != birthplace_profile["state_code"]:
        raise ValueError("A cidade natal selecionada não pertence à UF informada.")
    if birthplace_state and birthplace_state not in STATE_NAMES:
        raise ValueError("Escolha uma UF válida para a cidade natal.")
    if bool(birthplace_state) != bool(birthplace_id):
        raise ValueError("Informe a UF e a cidade natal juntas, ou deixe ambas em branco.")
    character = {"name": (character.get("name") or candidate_name or "").strip()[:80],
                 "political_spectrum": spectrum if spectrum in SPECTRUM_GROUP_EFFECTS else "centro",
                 "family_background": family if family in FAMILY_GROUP_EFFECTS else "classe_media",
                 "economic_axis": character.get("economic_axis") if character.get("economic_axis") in {"estado_social", "equilibrio", "mercado"} else "equilibrio",
                 "social_axis": character.get("social_axis") if character.get("social_axis") in {"liberdades", "comunidade", "tradicao"} else "liberdades",
                 "territorial_axis": character.get("territorial_axis") if character.get("territorial_axis") in {"municipalista", "federativa", "nacional"} else "federativa",
                 "birth_state_code": birthplace_state,
                 "birth_municipality_id": birthplace_profile["ibge_code"] if birthplace_profile else None,
                 "birthplace": ({"municipality": birthplace_profile["name"], "state_code": birthplace_state,
                                  "municipality_id": birthplace_profile["ibge_code"]} if birthplace_profile else None),
                 "customs": customs, "traits": traits, "biography": str(character.get("biography", ""))[:400]}
    previous = state.get("career") or {}
    previous_history = list(previous.get("history", []))
    previous_promises = list(previous.get("campaign_promises", []))
    previous_reputation = float(previous.get("reputation", 50.0))
    if previous.get("mode"):
        if previous.get("phase") not in {"opposition", "term_complete"}:
            raise ValueError("Conclua o mandato ou a transição atual antes de iniciar outra candidatura.")
        previous_history.append({
            "office": previous.get("office_label", previous.get("office", "Cargo")),
            "municipality": previous.get("municipality", ""), "municipality_id": previous.get("municipality_id"),
            "territory": previous.get("municipality") or ("Brasil" if previous.get("office") == "presidente" else previous.get("state_name", previous.get("state_code", ""))),
            "state_code": previous.get("state_code", ""),
            "result": previous.get("result"), "vote_share": previous.get("vote_share"),
            "term_years": previous.get("term_years", 0), "reputation": round(previous_reputation, 1),
            "date": state["date"], "simulated": True,
        })
        if previous.get("result") == "won":
            previous_reputation = _clamp(previous_reputation + 5 + min(4, float((previous.get("governance") or {}).get("delivery", 0)) * .25))
        elif previous.get("result") == "lost":
            previous_reputation = _clamp(previous_reputation - 2 + float(previous.get("vote_share") or 0) * .04)
        candidate_name = candidate_name.strip() or previous.get("candidate_name", "")
        party = party.strip() or previous.get("party", "")
        ideology = ideology or previous.get("ideology", "Centro")
    election_day = _regular_election_day(office, today, force_year=election_year)
    campaign_start = election_day - timedelta(days=90)
    inauguration = _inauguration_date(office, election_day)
    term_end = _term_end_date(office, inauguration, role["term_years"])
    phase = "campaign" if today >= campaign_start else "pre_campaign"
    local_strength = 39.0 if office in {"vereador", "prefeito"} else 35.0
    party_spectrum = IDEOLOGY_SPECTRUM.get(ideology, "centro")
    spectrum_gap = abs(SPECTRUM_ORDER.index(character["political_spectrum"]) - SPECTRUM_ORDER.index(party_spectrum))
    initial_poll = _clamp(role["base_support"] + (previous_reputation - 50) * .22 + (.5 if "carismatica" in traits else 0) - spectrum_gap * .45)
    group_support = {key: 45.0 for key in GROUPS}
    for adjustment, weight in ((SPECTRUM_GROUP_EFFECTS[character["political_spectrum"]], 4.0), (FAMILY_GROUP_EFFECTS[character["family_background"]], 3.0)):
        for group, amount in adjustment.items():  # diferenças entre grupos: quem cada perfil alcança melhor (só exibição; o voto sai da projeção única)
            group_support[group] = _clamp(group_support[group] + amount * weight)
    state["career"] = {
        "mode": True, "version": 1, "office": office, "office_label": role["label"], "scope": role["scope"],
        "phase": phase, "candidate_name": candidate_name.strip() or "Candidatura do jogador", "party": party,
        "ideology": ideology, "party_alignment_gap": spectrum_gap, "state_code": state_code, "state_name": STATE_NAMES[state_code],
        "character": character,
        "macroregion": STATE_REGIONS[state_code], "municipality": municipality,
        "municipality_id": municipality_id,
        "municipality_profile": municipality_profile,
        "electorate": role["electorate"],
        "powers": list(role["powers"]), "term_years": role["term_years"], "election_date": election_day.isoformat(),
        "first_round_date": election_day.isoformat(), "runoff_date": None, "first_round_poll_support": None,
        "first_round_results": [], "runoff_finalists": [], "runoff_results": [],
        "inauguration_date": inauguration.isoformat(), "term_end": term_end.isoformat(),
        "campaign_start": campaign_start.isoformat(), "campaign_fund_mi": role["fund_mi"], "spent_mi": 0.0,
        "poll_support": initial_poll, "local_support": local_strength, "campaign_base_local_support": local_strength,
        "state_support": initial_poll,
        "national_support": initial_poll, "momentum": 0.0, "fatigue": 0,
        "history": previous_history[-20:], "campaign_promises": previous_promises[-30:], "reputation": round(previous_reputation, 1),
        "seed": int(today.strftime("%Y%m%d")) + sum(map(ord, office + state_code + (municipality_id or municipality))),
        "campaign_team_municipality_id": municipality_id if role["scope"] == "municipal" else municipality_id or STATE_CAPITALS[state_code],
        "group_support": group_support, "last_action_date": None, "activities": [],
        "pre_campaign_organization": 0.0, "last_preparation_date": None, "preparations": [], "public_polls": [],
        "conduct": {"attempts": 0, "detected": 0, "election_penalty": 0.0, "history": []},
        "result": None, "vote_share": None, "opponent_share": 50.0, "appointments": [], "governance": None,
        "simulated": True,
    }
    _ensure_opponents(state["career"])
    if phase == "campaign":
        _record_public_poll(state, state["career"], today)
    state["election"] = {}
    state["office_status"] = "candidate"
    state["career_status"] = "campaigning" if phase == "campaign" else "preparing_campaign"
    address = ensure_communications_state(state)["inauguration"]
    address.update({"required": False, "delivered": True, "legacy_save": False})
    state["term_start"] = today.isoformat()
    state["term"] = 0
    election_context = f"a campanha abre em {campaign_start.strftime('%d/%m/%Y')}" if phase == "pre_campaign" else "a campanha eleitoral começou"
    campaign_territory = "Brasil" if office == "presidente" else municipality or STATE_NAMES[state_code]
    state.setdefault("simulated_news", []).insert(0, {
        "id": f"career-start-{today.isoformat()}", "date": today.isoformat(), "title": f"Campanha simulada: {role['label']}",
        "region": campaign_territory, "description": f"{candidate_name or 'Candidatura do jogador'} prepara a disputa em {campaign_territory}; {election_context}.", "simulated": True,
    })
    state["simulated_news"] = state["simulated_news"][:20]
    return state
