"""Reusable political-career and election loop for all simulated offices.

All candidates, polls, votes and people generated here belong to the fictional
simulation. The rules are deliberately explicit so the UI can explain outcomes.
"""
from __future__ import annotations

import random
import re
import unicodedata
from datetime import date, timedelta
from typing import Any

from .communications import ensure_communications_state
from .electoral_integrity import campaign_conduct_preview, resolve_campaign_conduct, settle_campaign_conduct


OFFICES: dict[str, dict[str, Any]] = {
    "vereador": {"label": "Vereador(a)", "scope": "municipal", "term_years": 4, "fund_mi": 0.45, "base_support": 36, "electorate": "Eleitorado do município", "powers": ["Propor leis municipais", "Fiscalizar a prefeitura", "Votar o orçamento municipal"]},
    "prefeito": {"label": "Prefeito(a)", "scope": "municipal", "term_years": 4, "fund_mi": 1.8, "base_support": 37, "electorate": "Eleitorado do município", "powers": ["Executar o orçamento municipal", "Organizar serviços locais", "Indicar secretários municipais"]},
    "deputado_estadual": {"label": "Deputado(a) estadual", "scope": "estadual", "term_years": 4, "fund_mi": 2.0, "base_support": 35, "electorate": "Eleitorado do estado", "powers": ["Propor leis estaduais", "Fiscalizar o governo estadual", "Votar o orçamento estadual"]},
    "deputado_federal": {"label": "Deputado(a) federal", "scope": "federal", "term_years": 4, "fund_mi": 2.8, "base_support": 34, "electorate": "Eleitorado do estado", "powers": ["Propor leis federais", "Fiscalizar ministérios", "Participar de comissões e votar o orçamento"]},
    "senador": {"label": "Senador(a)", "scope": "federal", "term_years": 8, "fund_mi": 4.0, "base_support": 35, "electorate": "Eleitorado do estado", "powers": ["Propor leis federais", "Representar o estado", "Votar autoridades e fiscalizar o Executivo"]},
    "governador": {"label": "Governador(a)", "scope": "estadual", "term_years": 4, "fund_mi": 5.0, "base_support": 36, "electorate": "Eleitorado do estado", "powers": ["Executar o orçamento estadual", "Gerir segurança e serviços estaduais", "Indicar secretários e propor leis"]},
    "presidente": {"label": "Presidente(a) da República", "scope": "federal", "term_years": 4, "fund_mi": 18.0, "base_support": 35, "electorate": "Eleitorado nacional", "powers": ["Dirigir o Executivo federal", "Propor orçamento e políticas nacionais", "Conduzir relações exteriores"]},
}

STATES = [
    ("AC", "Acre", "norte"), ("AL", "Alagoas", "nordeste"), ("AP", "Amapá", "norte"), ("AM", "Amazonas", "norte"),
    ("BA", "Bahia", "nordeste"), ("CE", "Ceará", "nordeste"), ("DF", "Distrito Federal", "centro_oeste"), ("ES", "Espírito Santo", "sudeste"),
    ("GO", "Goiás", "centro_oeste"), ("MA", "Maranhão", "nordeste"), ("MT", "Mato Grosso", "centro_oeste"), ("MS", "Mato Grosso do Sul", "centro_oeste"),
    ("MG", "Minas Gerais", "sudeste"), ("PA", "Pará", "norte"), ("PB", "Paraíba", "nordeste"), ("PR", "Paraná", "sul"),
    ("PE", "Pernambuco", "nordeste"), ("PI", "Piauí", "nordeste"), ("RJ", "Rio de Janeiro", "sudeste"), ("RN", "Rio Grande do Norte", "nordeste"),
    ("RS", "Rio Grande do Sul", "sul"), ("RO", "Rondônia", "norte"), ("RR", "Roraima", "norte"), ("SC", "Santa Catarina", "sul"),
    ("SP", "São Paulo", "sudeste"), ("SE", "Sergipe", "nordeste"), ("TO", "Tocantins", "norte"),
]
STATE_NAMES = {code: name for code, name, _ in STATES}
STATE_REGIONS = {code: region for code, _, region in STATES}
GROUPS = {
    "trabalhadores": "Trabalhadores", "empreendedores": "Pequenos negócios", "familias": "Famílias",
    "servidores": "Servidores públicos", "jovens": "Jovens", "rural": "População rural",
}
ISSUES = {
    "economia": {"label": "Emprego e custo de vida", "terms": {"emprego", "renda", "preço", "preco", "inflação", "inflacao", "empresa", "trabalho", "salário", "salario"}, "groups": ["trabalhadores", "empreendedores"]},
    "saude": {"label": "Saúde", "terms": {"saúde", "saude", "hospital", "posto", "médico", "medico", "vacina", "atendimento"}, "groups": ["familias", "servidores"]},
    "educacao": {"label": "Educação", "terms": {"escola", "educação", "educacao", "professor", "aluno", "creche", "universidade"}, "groups": ["familias", "jovens", "servidores"]},
    "seguranca": {"label": "Segurança", "terms": {"segurança", "seguranca", "crime", "polícia", "policia", "investigar", "violência", "violencia"}, "groups": ["familias", "empreendedores"]},
    "mobilidade": {"label": "Transporte e mobilidade", "terms": {"ônibus", "onibus", "transporte", "estrada", "trânsito", "transito", "mobilidade", "ferrovia"}, "groups": ["trabalhadores", "rural"]},
    "integridade": {"label": "Transparência", "terms": {"transparência", "transparencia", "auditoria", "contrato", "publicar", "fiscalizar", "prestação", "prestacao"}, "groups": ["jovens", "servidores"]},
}
ACTIVITIES = {
    "comicio": {"label": "Comício", "days": 2, "cost": 0.045, "reach": 1.35, "channel": "presencial"},
    "debate": {"label": "Debate", "days": 1, "cost": 0.025, "reach": 1.1, "channel": "imprensa"},
    "entrevista": {"label": "Entrevista", "days": 1, "cost": 0.018, "reach": 0.8, "channel": "imprensa"},
    "porta_a_porta": {"label": "Visita a bairros", "days": 2, "cost": 0.035, "reach": 1.2, "channel": "território"},
    "rede_conversa": {"label": "Roda · grupos de mensagem", "days": 1, "cost": 0.012, "reach": 0.72, "channel": "mensageria", "audience": ["familias", "trabalhadores"], "viral": .23},
    "rede_vitrine": {"label": "Vitrine · vídeo e imagem", "days": 1, "cost": 0.018, "reach": 0.92, "channel": "video_curto", "audience": ["jovens", "empreendedores"], "viral": .28},
    "rede_praca": {"label": "Praça · debate público", "days": 1, "cost": 0.016, "reach": 0.82, "channel": "rede_publica", "audience": ["jovens", "servidores"], "viral": .32},
}
APPOINTED_PATHS = {
    "ministro": {"label": "Ministro(a) de Estado", "requires": ["presidente"], "description": "Nomeação presidencial e apoio político; não é cargo eletivo."},
    "stf_indicado": {"label": "Indicação ao STF", "requires": ["presidente"], "description": "Indicação presidencial seguida de sabatina e votação no Senado; não é cargo eletivo."},
}
LEGISLATIVE_OFFICES = {"vereador", "deputado_estadual", "deputado_federal", "senador"}
SERVICE_AREAS = {
    "education": {"label": "Educação e escolas", "outcome": "education", "effect": 5.0},
    "health": {"label": "Saúde e atendimento", "outcome": "health", "effect": 5.0},
    "security": {"label": "Segurança pública", "outcome": "security", "effect": 4.0},
    "mobility": {"label": "Transporte e mobilidade", "outcome": "mobility", "effect": 4.0},
}
LEGISLATIVE_ACTIONS = [
    {"key": "proposal", "label": "Apresentar proposta de lei", "capital": 18, "days": 60, "summary": "A proposta entra em tramitação e enfrenta uma votação simulada."},
    {"key": "oversight", "label": "Fiscalizar contrato ou programa", "capital": 12, "days": 30, "summary": "A fiscalização pode revelar falha, melhorar controle ou abrir um caso político."},
    {"key": "hearing", "label": "Convocar audiência pública", "capital": 8, "days": 1, "summary": "Escuta setores afetados e aumenta a confiança quando há resposta pública."},
]


def _norm(text: str) -> str:
    raw = unicodedata.normalize("NFD", text.casefold())
    return "".join(ch for ch in raw if unicodedata.category(ch) != "Mn")


def _regular_election_day(office: str, after: date, minimum_year: int | None = None) -> date:
    """Return the next simulated Brazilian regular-election date for an office."""
    municipal = office in {"vereador", "prefeito"}
    anchor_year = 2028 if municipal else 2026
    cycle = 4
    first_year = max(anchor_year, minimum_year or anchor_year)
    cycle_year = anchor_year + max(0, (first_year - anchor_year + cycle - 1) // cycle) * cycle
    while True:
        october_first = date(cycle_year, 10, 1)
        first_sunday = october_first + timedelta(days=(6 - october_first.weekday()) % 7)
        if first_sunday > after:
            return first_sunday
        cycle_year += cycle


def _inauguration_date(office: str, election_day: date) -> date:
    year = election_day.year + 1
    # Since the 2027 transition, the President takes office on January 5.
    return date(year, 1, 5) if office == "presidente" else date(year, 1, 1)


def _term_end_date(office: str, inauguration: date, term_years: int) -> date:
    if office == "presidente":
        return date(inauguration.year + term_years, 1, 5) - timedelta(days=1)
    return date(inauguration.year + term_years, 1, 1) - timedelta(days=1)


def career_options(as_of: date | None = None) -> dict[str, Any]:
    as_of = as_of or date(2027, 1, 1)
    return {
        "offices": [{"key": key, **{name: value for name, value in role.items() if name != "fund_mi"}, "campaign_fund_mi": role["fund_mi"]} for key, role in OFFICES.items()],
        "calendar_previews": {key: {
            "election_date": _regular_election_day(key, as_of).isoformat(),
            "campaign_start": (_regular_election_day(key, as_of) - timedelta(days=90)).isoformat(),
            "inauguration_date": _inauguration_date(key, _regular_election_day(key, as_of)).isoformat(),
            "cycle_label": "Ciclo municipal" if key in {"vereador", "prefeito"} else "Ciclo geral",
        } for key in OFFICES},
        "states": [{"code": code, "name": name, "region": region} for code, name, region in STATES],
        "parties": ["Partido da Renovação", "Frente Popular", "União Cívica", "Aliança Trabalhista", "Movimento Verde", "Partido Municipalista"],
        "ideologies": ["Progressista", "Centro-esquerda", "Centro", "Centro-direita", "Conservadora", "Ecologista"],
        "issues": [{"key": key, "label": item["label"]} for key, item in ISSUES.items()],
        "activities": [{"key": key, "label": item["label"], "days": item["days"], "cost_mi": item["cost"]} for key, item in ACTIVITIES.items()],
        "appointment_paths": APPOINTED_PATHS,
        "service_areas": SERVICE_AREAS,
        "simulated_notice": "Candidatos, partidos, pesquisas e resultados desta carreira são criados para a simulação. Não representam pesquisa ou endosso real.",
    }


def start_career(state: dict[str, Any], office: str, state_code: str, municipality: str,
                 party: str, ideology: str, candidate_name: str) -> dict[str, Any]:
    if office not in OFFICES:
        raise ValueError("Escolha um cargo eletivo disponível.")
    if state_code not in STATE_NAMES:
        raise ValueError("Escolha uma unidade da federação válida.")
    if not municipality.strip():
        raise ValueError("Informe o município da candidatura.")
    today = date.fromisoformat(state["date"])
    role = OFFICES[office]
    previous = state.get("career") or {}
    previous_history = list(previous.get("history", []))
    previous_reputation = float(previous.get("reputation", 50.0))
    if previous.get("mode"):
        if previous.get("phase") not in {"opposition", "term_complete"}:
            raise ValueError("Conclua o mandato ou a transição atual antes de iniciar outra candidatura.")
        previous_history.append({
            "office": previous.get("office_label", previous.get("office", "Cargo")),
            "municipality": previous.get("municipality", ""), "state_code": previous.get("state_code", ""),
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
    election_day = _regular_election_day(office, today)
    campaign_start = election_day - timedelta(days=90)
    inauguration = _inauguration_date(office, election_day)
    term_end = _term_end_date(office, inauguration, role["term_years"])
    phase = "campaign" if today >= campaign_start else "pre_campaign"
    local_strength = 39.0 if office in {"vereador", "prefeito"} else 35.0
    initial_poll = _clamp(role["base_support"] + (previous_reputation - 50) * .22)
    state["career"] = {
        "mode": True, "version": 1, "office": office, "office_label": role["label"], "scope": role["scope"],
        "phase": phase, "candidate_name": candidate_name.strip() or "Candidatura do jogador", "party": party.strip() or "Partido da Renovação",
        "ideology": ideology, "state_code": state_code, "state_name": STATE_NAMES[state_code],
        "macroregion": STATE_REGIONS[state_code], "municipality": municipality.strip(), "electorate": role["electorate"],
        "powers": list(role["powers"]), "term_years": role["term_years"], "election_date": election_day.isoformat(),
        "inauguration_date": inauguration.isoformat(), "term_end": term_end.isoformat(),
        "campaign_start": campaign_start.isoformat(), "campaign_fund_mi": role["fund_mi"], "spent_mi": 0.0,
        "poll_support": initial_poll, "local_support": local_strength, "state_support": initial_poll,
        "national_support": initial_poll, "momentum": 0.0, "fatigue": 0,
        "history": previous_history[-20:], "reputation": round(previous_reputation, 1),
        "seed": int(today.strftime("%Y%m%d")) + sum(map(ord, office + state_code + municipality)),
        "group_support": {key: 45.0 for key in GROUPS}, "last_action_date": None, "activities": [],
        "conduct": {"attempts": 0, "detected": 0, "election_penalty": 0.0, "history": []},
        "result": None, "vote_share": None, "opponent_share": 50.0, "appointments": [], "governance": None,
        "simulated": True,
    }
    state["election"] = {}
    state["office_status"] = "candidate"
    state["career_status"] = "campaigning" if phase == "campaign" else "preparing_campaign"
    address = ensure_communications_state(state)["inauguration"]
    address.update({"required": False, "delivered": True, "legacy_save": False})
    state["term_start"] = today.isoformat()
    state["term"] = 0
    election_context = f"a campanha abre em {campaign_start.strftime('%d/%m/%Y')}" if phase == "pre_campaign" else "a campanha eleitoral começou"
    state.setdefault("simulated_news", []).insert(0, {
        "id": f"career-start-{today.isoformat()}", "date": today.isoformat(), "title": f"Campanha simulada: {role['label']}",
        "region": STATE_NAMES[state_code], "description": f"{candidate_name or 'Candidatura do jogador'} prepara a disputa em {municipality.strip()}/{state_code}; {election_context}.", "simulated": True,
    })
    state["simulated_news"] = state["simulated_news"][:20]
    return state


def _campaign(state: dict[str, Any]) -> dict[str, Any]:
    career = state.get("career") or {}
    if not career.get("mode"):
        raise ValueError("Esta partida ainda não iniciou uma carreira política.")
    return career


def _speech_score(issue: str, message: str) -> tuple[int, dict[str, int]]:
    normalized = _norm(message)
    words = re.findall(r"[\w'-]+", normalized)
    topic = ISSUES[issue]["terms"]
    relevance = min(25, sum(1 for term in topic if _norm(term) in normalized) * 5)
    concrete_terms = {"prazo", "meta", "publicar", "fiscalizar", "auditoria", "orçamento", "orcamento", "equipe", "plano", "entregar", "medir", "acompanhar", "reduzir", "ampliar", "bairro", "escola", "posto"}
    concrete = min(20, sum(1 for term in concrete_terms if _norm(term) in normalized) * 4)
    empathy_terms = {"família", "familia", "morador", "trabalhador", "aluno", "paciente", "bairro", "comunidade", "escutar", "ouvir", "respeito", "cuidado", "medo", "ônibus", "onibus"}
    empathy = min(15, sum(1 for term in empathy_terms if _norm(term) in normalized) * 3)
    length = 10 if 18 <= len(words) <= 90 else 4 if 10 <= len(words) <= 120 else -5
    exaggeration = 12 if any(p in normalized for p in ("resolver tudo", "nunca mais", "sem custo", "acabar com todo")) else 0
    attacks = 12 if any(p in normalized for p in ("lixo", "vagabundo", "traidor", "inimigo do povo")) else 0
    score = max(0, min(100, 40 + relevance + concrete + empathy + length - exaggeration - attacks))
    return score, {"pertinência do tema": relevance, "proposta verificável": concrete, "conexão local": empathy, "clareza": length, "promessa exagerada": -exaggeration, "ataque pessoal": -attacks}


def career_overview(state: dict[str, Any]) -> dict[str, Any] | None:
    career = state.get("career")
    if not career or not career.get("mode"):
        return None
    today = date.fromisoformat(state["date"])
    election_day = date.fromisoformat(career["election_date"])
    campaign_start = election_day - timedelta(days=90)
    last_action = career.get("last_action_date")
    wait = max(0, 7 - (today - date.fromisoformat(last_action)).days) if last_action else 0
    role = OFFICES[career["office"]]
    governance = career.get("governance") or {}
    executive_costs = {"prefeito": 22.0, "governador": 800.0, "presidente": 3200.0}
    if career["office"] in LEGISLATIVE_OFFICES:
        governance_actions = [dict(item) for item in LEGISLATIVE_ACTIONS]
    elif career["office"] in executive_costs:
        governance_actions = [{"key": f"service_{key}", "label": area["label"], "cost_mi": executive_costs[career["office"]], "days": 1,
                              "summary": f"Inicia um programa com entrega prevista em cerca de quatro meses."} for key, area in SERVICE_AREAS.items()]
        governance_actions += [{"key": "public_report", "label": "Publicar prestação de contas", "cost_mi": 0, "days": 1,
                                "summary": "Expõe metas, execução financeira e resultados para fiscalização pública."}]
    else:
        governance_actions = []
    governance_wait = max(0, 30 - (today - date.fromisoformat(governance.get("last_action_date", today.isoformat()))).days) if governance.get("last_action_date") else 0
    in_campaign = career["phase"] == "campaign" and campaign_start <= today <= election_day
    next_campaign = max(0, (campaign_start - today).days) if career["phase"] in {"office", "pre_campaign"} else 0
    return {
        "mode": True, "office": career["office"], "office_label": career["office_label"], "scope": career["scope"],
        "phase": career["phase"], "candidate_name": career["candidate_name"], "party": career["party"], "ideology": career["ideology"],
        "state_code": career["state_code"], "state_name": career["state_name"], "municipality": career["municipality"],
        "electorate": career["electorate"], "powers": career["powers"], "election_date": career["election_date"],
        "inauguration_date": career["inauguration_date"], "term_end": career["term_end"], "term_years": career["term_years"],
        "days_until_election": max(0, (election_day - today).days),
        "campaign_start_date": campaign_start.isoformat(),
        "days_until_campaign": next_campaign,
        "days_until_inauguration": max(0, (date.fromisoformat(career["inauguration_date"]) - today).days),
        "campaign_active": in_campaign,
        "can_act": in_campaign and wait == 0 and career["campaign_fund_mi"] >= 0.01,
        "days_until_action": wait, "poll_support": round(career["poll_support"], 1), "local_support": round(career["local_support"], 1),
        "state_support": round(career["state_support"], 1), "national_support": round(career["national_support"], 1),
        "reputation": round(float(career.get("reputation", 50)), 1), "history": list(reversed(career.get("history", [])[-12:])),
        "momentum": round(career["momentum"], 1), "fatigue": career["fatigue"],
        "campaign_fund_mi": round(career["campaign_fund_mi"], 3), "spent_mi": round(career["spent_mi"], 3),
        "opponent_share": round(career["opponent_share"], 1), "result": career.get("result"), "vote_share": career.get("vote_share"),
        "conduct_review": career.get("conduct_review"), "electoral_result": career.get("electoral_result"),
        "can_start_campaign": career.get("phase") in {"opposition", "term_complete"},
        "groups": [{"key": key, "label": label, "support": round(career["group_support"][key], 1)} for key, label in GROUPS.items()],
        "activities": list(reversed(career["activities"][-10:])),
        "activity_options": [{"key": key, "label": item["label"], "days": item["days"], "cost_mi": item["cost"]} for key, item in ACTIVITIES.items()],
        "issue_options": [{"key": key, "label": value["label"]} for key, value in ISSUES.items()],
        "appointment_paths": [{"key": key, **value, "available": career["office"] in value["requires"] and career["phase"] == "office"} for key, value in APPOINTED_PATHS.items()],
        "governance": career.get("governance"), "next_campaign_days": next_campaign,
        "governance_actions": governance_actions, "governance_wait_days": governance_wait,
        "governance_budget_mi": round(float(governance.get("budget_mi", 0)), 1),
        "political_capital": round(float(governance.get("political_capital", 0)), 1),
        "rules": {"campaign_window_days": 90, "activity_cooldown_days": 7, "election_and_vote_simulated": True, "government_keeps_running": True},
        "conduct_preview": campaign_conduct_preview(state, career),
        "inaugural_address": ensure_communications_state(state)["inauguration"],
        "notice": "Candidatos, partidos, pesquisas e resultados desta carreira são gerados para a simulação.",
    }


def perform_governance_action(state: dict[str, Any], action: str, service: str = "", issue: str = "") -> dict[str, Any]:
    career = _campaign(state)
    if career["phase"] != "office":
        raise ValueError("Você precisa estar empossado para tomar decisões neste cargo.")
    governance = career.setdefault("governance", {"budget_mi": 0.0, "trust": 50.0, "delivery": 0.0, "political_capital": 50.0, "actions": [], "pipeline": [], "outcomes": {}})
    last = governance.get("last_action_date")
    if last and (date.fromisoformat(state["date"]) - date.fromisoformat(last)).days < 30:
        wait = 30 - (date.fromisoformat(state["date"]) - date.fromisoformat(last)).days
        raise ValueError(f"A agenda do cargo foi usada. A próxima decisão abre em {wait} dia(s).")
    if career["office"] in LEGISLATIVE_OFFICES:
        selected = next((item for item in LEGISLATIVE_ACTIONS if item["key"] == action), None)
        if not selected:
            raise ValueError("Esta ação não pertence às atribuições legislativas do cargo.")
        if governance.get("political_capital", 0) < selected["capital"]:
            raise ValueError("Capital político insuficiente. Avance o calendário e negocie apoio.")
        governance["political_capital"] = round(governance["political_capital"] - selected["capital"], 1)
        if action == "proposal":
            governance.setdefault("pipeline", []).append({"id": f"bill-{state['date']}-{len(governance.get('actions', [])) + 1}", "kind": "bill", "title": issue.strip()[:100] or "Proposta de política pública", "due_date": (date.fromisoformat(state["date"]) + timedelta(days=selected["days"])).isoformat(), "status": "in_tramitation", "simulated": True})
            summary = selected["summary"]
        elif action == "oversight":
            governance["trust"] = _clamp(governance.get("trust", 50) + 1.5)
            governance.setdefault("pipeline", []).append({"id": f"oversight-{state['date']}-{len(governance.get('actions', [])) + 1}", "kind": "oversight", "title": issue.strip()[:100] or "Fiscalização pública", "due_date": (date.fromisoformat(state["date"]) + timedelta(days=selected["days"])).isoformat(), "status": "in_progress", "simulated": True})
            summary = selected["summary"]
        else:
            career["group_support"]["servidores"] = _clamp(career["group_support"].get("servidores", 45) + 1.2)
            career["local_support"] = _clamp(career["local_support"] + 1.0)
            governance["trust"] = _clamp(governance.get("trust", 50) + 1.2)
            summary = "Audiência concluída. Apoio de servidores, confiança e apoio local subiram um pouco; os efeitos são registrados na carreira simulada."
        cost = 0.0
    else:
        prefix, _, area_key = action.partition("_")
        if prefix == "service" and area_key in SERVICE_AREAS:
            area = SERVICE_AREAS[area_key]
            cost = {"prefeito": 22.0, "governador": 800.0, "presidente": 3200.0}.get(career["office"], 0.0)
            if governance.get("budget_mi", 0) < cost:
                raise ValueError("A reserva anual desta agenda não cobre o programa. Reavalie o orçamento ou aguarde o próximo ano.")
            governance["budget_mi"] = round(governance["budget_mi"] - cost, 1)
            governance.setdefault("pipeline", []).append({"id": f"service-{state['date']}-{len(governance.get('actions', [])) + 1}", "kind": "service", "area": area_key, "title": area["label"], "effect": area["effect"], "due_date": (date.fromisoformat(state["date"]) + timedelta(days=120)).isoformat(), "status": "in_progress", "simulated": True})
            summary = f"Programa de {area['label'].lower()} iniciado. Custo reservado: R$ {cost:,.1f} milhões. A entrega chega em aproximadamente 120 dias se não houver atraso."
        elif action == "public_report":
            cost = 0.0
            governance["trust"] = _clamp(governance.get("trust", 50) + 2.0)
            career["group_support"]["jovens"] = _clamp(career["group_support"].get("jovens", 45) + 1.0)
            summary = "Prestação de contas publicada na simulação. Transparência e confiança sobem; os números serão cobrados nas próximas decisões."
        else:
            raise ValueError("Esta ação não pertence às atribuições executivas deste cargo.")
    governance["last_action_date"] = state["date"]
    entry = {"id": f"office-{state['date']}-{len(governance.get('actions', [])) + 1}", "date": state["date"], "action": action,
             "title": issue.strip()[:100] or next((item["label"] for item in governance_actions_for(career) if item["key"] == action), action.replace("_", " ").title()),
             "summary": summary, "cost_mi": cost, "status": "active", "simulated": True}
    governance.setdefault("actions", []).append(entry)
    governance["actions"] = governance["actions"][-50:]
    return {"action": entry, "summary": summary, "governance": governance}


def governance_actions_for(career: dict[str, Any]) -> list[dict[str, Any]]:
    if career["office"] in LEGISLATIVE_OFFICES:
        return LEGISLATIVE_ACTIONS
    if career["office"] in {"prefeito", "governador", "presidente"}:
        return [{"key": f"service_{key}", "label": value["label"]} for key, value in SERVICE_AREAS.items()] + [{"key": "public_report", "label": "Publicar prestação de contas"}]
    return []


def perform_career_action(state: dict[str, Any], activity_type: str, issue: str, message: str,
                          conduct: str = "regular") -> dict[str, Any]:
    career = _campaign(state)
    overview = career_overview(state)
    if not overview["campaign_active"]:
        raise ValueError("A campanha não está aberta nesta data da simulação.")
    if not overview["can_act"]:
        if overview["days_until_action"]:
            raise ValueError(f"A agenda de campanha volta a abrir em {overview['days_until_action']} dia(s).")
        raise ValueError("O fundo de campanha simulado acabou.")
    if activity_type not in ACTIVITIES:
        raise ValueError("Escolha uma atividade de campanha válida.")
    if issue not in ISSUES:
        raise ValueError("Escolha um tema válido.")
    if len(message.strip()) < 12:
        raise ValueError("Escreva pelo menos 12 caracteres para a fala ou proposta.")
    activity = ACTIVITIES[activity_type]
    if career["campaign_fund_mi"] < activity["cost"]:
        raise ValueError("O saldo do fundo de campanha não cobre essa atividade.")
    score, rubric = _speech_score(issue, message)
    quality = (score - 55) / 45
    reach = activity["reach"]
    local_delta = max(-1.0, min(2.6, quality * reach + (0.45 if activity_type in {"comicio", "porta_a_porta"} else 0.1)))
    state_delta = local_delta * (0.4 if career["scope"] == "municipal" else 0.72)
    career["local_support"] = _clamp(career["local_support"] + local_delta)
    career["state_support"] = _clamp(career["state_support"] + state_delta)
    career["national_support"] = _clamp(career["national_support"] + state_delta * 0.25)
    group_delta = quality * reach * 0.65
    for group in ISSUES[issue]["groups"]:
        career["group_support"][group] = _clamp(career["group_support"][group] + group_delta)
    conduct_result = resolve_campaign_conduct(
        state, career, conduct, f"career-{len(career['activities']) + 1}-{activity_type}"
    )
    conduct_delta = conduct_result["immediate_support_delta"]
    career["poll_support"] = round(_clamp(career["poll_support"] + conduct_delta), 2)
    career["state_support"] = _clamp(career["state_support"] + conduct_delta * .55)
    career["local_support"] = _clamp(career["local_support"] + conduct_delta)
    if conduct_result["detected"]:
        career["reputation"] = _clamp(float(career.get("reputation", 50)) - 2.0)
    for group in ISSUES[issue]["groups"]:
        career["group_support"][group] = _clamp(career["group_support"][group] + conduct_delta * .35)
    career["poll_support"] = round(_clamp(career["poll_support"] + state_delta * 0.42 + group_delta * 0.24), 2)
    social_result = None
    if activity.get("audience"):
        rng = random.Random(f"{career.get('seed', 1)}:{state['date']}:{len(career['activities'])}:social")
        clarity_bonus = .08 if any(term in _norm(message) for term in ("fonte", "dados", "prazo", "resultado", "transparencia")) else 0
        exaggeration_penalty = .15 if any(term in _norm(message) for term in ("resolver tudo", "nunca mais", "sem custo")) else 0
        virality = max(.04, min(.78, activity["viral"] + (score - 60) * .008 + clarity_bonus - exaggeration_penalty - career["fatigue"] * .001))
        spread = rng.random() < virality
        if spread and score >= 60:
            effect = min(1.8, max(.25, (score - 55) * .035 * reach + .35))
            event = "ganhou alcance"
        elif spread or score < 48 or exaggeration_penalty:
            effect = -min(1.2, max(.25, (52 - score) * .035 + .25))
            event = "viralizou com reação crítica" if spread else "gerou reação crítica"
        else:
            effect = 0.0
            event = "teve alcance limitado"
        for audience in activity["audience"]:
            career["group_support"][audience] = _clamp(career["group_support"].get(audience, 45) + effect)
        career["poll_support"] = round(_clamp(career["poll_support"] + effect * .12), 2)
        social_result = {"platform": activity["label"].split(" · ")[0], "audience": [GROUPS[item] for item in activity["audience"]],
                         "virality_pct": round(virality * 100), "event": event, "group_effect": round(effect, 2),
                         "explanation": "A chance considera a nota da mensagem, clareza verificável, formato e fadiga da equipe."}
    career["momentum"] = round(max(-10, min(10, career["momentum"] * 0.8 + quality * 1.1)), 2)
    career["fatigue"] = min(100, career["fatigue"] + (8 if activity_type in {"comicio", "porta_a_porta"} else 4))
    career["campaign_fund_mi"] = round(career["campaign_fund_mi"] - activity["cost"], 4)
    career["spent_mi"] = round(career["spent_mi"] + activity["cost"], 4)
    career["last_action_date"] = state["date"]
    record = {
        "id": f"career-{state['date']}-{len(career['activities']) + 1}", "date": state["date"], "type": activity_type,
        "label": activity["label"], "channel": activity["channel"], "issue": issue, "issue_label": ISSUES[issue]["label"],
        "message": message.strip(), "score": score, "rubric": rubric, "local_change": round(local_delta + conduct_delta, 2),
        "state_change": round(state_delta + conduct_delta * .55, 2), "poll_support": career["poll_support"], "cost_mi": activity["cost"],
        "days_cost": activity["days"], "affected_groups": [GROUPS[group] for group in ISSUES[issue]["groups"]], "simulated": True,
        "social_result": social_result, "conduct": conduct_result,
    }
    career["activities"].append(record)
    career["activities"] = career["activities"][-60:]
    return {"activity": record, "score": score, "rubric": rubric, "days_cost": activity["days"], "poll_support": career["poll_support"],
            "local_support": career["local_support"], "state_support": career["state_support"], "campaign_fund_mi": career["campaign_fund_mi"],
            "social_result": social_result, "forecast": _forecast(career, score), "message": "Ação registrada. A atividade consome o tempo indicado e a campanha continua sujeita ao voto simulado."}


def _forecast(career: dict[str, Any], score: int) -> list[dict[str, Any]]:
    quality = (score - 55) / 45
    return [
        {"horizon": "Agora", "effect": f"Pesquisa do candidato em {career['poll_support']:.1f}% e apoio local em {career['local_support']:.1f}%"},
        {"horizon": "Próximas semanas", "effect": "Repetição de mensagem fortalece reconhecimento; fadiga e desgaste reduzem retorno de novas atividades." if career["fatigue"] < 65 else "A equipe está cansada; alternar formato e tema protege o alcance."},
        {"horizon": "Eleição", "effect": "O resultado compara intenção de voto, organização, apoio partidário e uma margem aleatória definida pela dificuldade."},
    ]


def _proportional_result(career: dict[str, Any], rng: random.Random, candidate_vote: float) -> dict[str, Any]:
    """Simplified open-list simulation: fictional party totals apportioned by D'Hondt."""
    seats = 13 if career["office"] == "vereador" else 24
    party_vote = _clamp(candidate_vote + rng.uniform(0.0, 7.0))
    weights = [rng.gammavariate(1.7, 1.0) for _ in range(9)]
    total_weight = sum(weights) or 1.0
    other_votes = [(100.0 - party_vote) * weight / total_weight for weight in weights]
    votes = [party_vote, *other_votes]
    allocations = [0] * len(votes)
    for _ in range(seats):
        winner = max(range(len(votes)), key=lambda index: votes[index] / (allocations[index] + 1))
        allocations[winner] += 1
    return {
        "system": "proporcional_simulado",
        "district_magnitude": seats,
        "party_vote_share": round(party_vote, 1),
        "party_seats": allocations[0],
        "candidate_list_rank": 1,
        "method": "D'Hondt entre legendas fictícias; candidatura do jogador ocupa a primeira posição simulada da lista.",
    }


def resolve_career_election(state: dict[str, Any], election_day: date) -> str:
    career = state.get("career") or {}
    if not career.get("mode") or career["phase"] != "campaign":
        return ""
    from .difficulty import get_difficulty
    difficulty = get_difficulty(state.get("difficulty", "normal"))
    seed = f"{career.get('seed', state.get('campaign_seed', 203001))}:career-election:{career['office']}:{election_day.isoformat()}"
    conduct_result = settle_campaign_conduct(state, career, seed)
    rng = random.Random(seed)
    organization = min(8.0, len(career["activities"]) * 0.55)
    fatigue_penalty = max(0, career["fatigue"] - 60) * 0.035
    volatility = 2.5 * difficulty.get("economic_volatility", 1)
    opposition_pressure = difficulty.get("opposition_pressure", 1)
    opposition_drag = (opposition_pressure - 1) * 2.0
    electoral_result = None
    if career["office"] in {"vereador", "deputado_estadual", "deputado_federal"}:
        vote_share = _clamp(career["poll_support"] * 0.78 + organization + career["momentum"] * 0.35 - fatigue_penalty - conduct_result["vote_penalty"] - opposition_drag + rng.uniform(-volatility, volatility) * opposition_pressure)
        electoral_result = _proportional_result(career, rng, vote_share)
        opposition_share = 100 - vote_share
        won = electoral_result["party_seats"] > 0
    else:
        vote_share = _clamp(25 + career["poll_support"] * 0.42 + organization + career["momentum"] * 0.4 - fatigue_penalty - conduct_result["vote_penalty"] - opposition_drag + rng.uniform(-volatility, volatility) * opposition_pressure)
        opposition_share = 100 - vote_share
        won = vote_share > opposition_share
    career["vote_share"] = round(vote_share, 1)
    career["opponent_share"] = round(opposition_share, 1)
    career["conduct_review"] = conduct_result
    career["electoral_result"] = electoral_result or {"system": "majoritário_simulado", "runoff": False}
    career["result"] = "won" if won else "lost"
    has_current_mandate = bool(career.get("office_start"))
    career["phase"] = "transition" if won else "outgoing" if has_current_mandate else "opposition"
    state["office_status"] = "elected_transition" if won else "incumbent_caretaker" if has_current_mandate else "opposition_candidate"
    state["career_status"] = "transition" if won else "outgoing" if has_current_mandate else "opposition"
    transition = election_day + timedelta(days=60)
    career["inauguration_date"] = transition.isoformat()
    career["transition_date"] = transition.isoformat()
    state.setdefault("simulated_news", []).insert(0, {
        "id": f"career-election-{election_day.isoformat()}", "date": election_day.isoformat(),
        "title": f"Resultado eleitoral simulado: {career['office_label']}", "region": career["state_name"],
        "description": f"{career['candidate_name']} recebeu {vote_share:.1f}% dos votos simulados. {career['result'].capitalize()}.", "simulated": True,
    })
    state["simulated_news"] = state["simulated_news"][:20]
    electoral_summary = (f"Sua legenda obteve {electoral_result['party_seats']} de {electoral_result['district_magnitude']} cadeiras simuladas." if electoral_result else "")
    return f"Resultado eleitoral simulado: {'vitória' if won else 'derrota'} com {vote_share:.1f}% dos votos. {electoral_summary} " + (f"A posse simulada está marcada para {transition.strftime('%d/%m/%Y')}." if won else "Você segue na oposição; a carreira pode continuar com outra disputa ou uma indicação política.")


def advance_career(state: dict[str, Any], before: date, after: date) -> list[str]:
    career = state.get("career") or {}
    if not career.get("mode"):
        return []
    messages: list[str] = []
    election_day = date.fromisoformat(career["election_date"])
    campaign_start = election_day - timedelta(days=90)
    if career["phase"] in {"office", "pre_campaign"} and before < campaign_start <= after:
        career["phase"] = "campaign"
        state["career_status"] = "campaigning"
        career["result"] = None
        career["vote_share"] = None
        career["last_action_date"] = None
        career["campaign_fund_mi"] = round(max(career["campaign_fund_mi"], OFFICES[career["office"]]["fund_mi"] * 0.45), 3)
        performance = career.get("governance") or {}
        performance_bonus = min(4.0, float(performance.get("delivery", 0)) * 0.12 + (float(performance.get("trust", 50)) - 50) * 0.08)
        career["poll_support"] = round(_clamp(33 + float(performance.get("trust", 50)) * 0.18 + performance_bonus), 2)
        messages.append("A janela eleitoral da reta final abriu. A avaliação do mandato e as novas atividades passam a afetar a tentativa de reeleição.")
    if career["phase"] == "campaign" and before < election_day <= after:
        messages.append(resolve_career_election(state, election_day))
    transition_date = career.get("transition_date")
    if career["phase"] == "transition" and transition_date and before < date.fromisoformat(transition_date) <= after:
        career["phase"] = "office"
        career["office_start"] = transition_date
        career["term_end"] = (date.fromisoformat(transition_date).replace(year=date.fromisoformat(transition_date).year + career["term_years"]) - timedelta(days=1)).isoformat()
        next_election_year = date.fromisoformat(transition_date).year + career["term_years"] - 1
        reelection_day = _regular_election_day(career["office"], date.fromisoformat(career["election_date"]), next_election_year)
        career["election_date"] = reelection_day.isoformat()
        executive_funds = {"prefeito": 350.0, "governador": 12000.0, "presidente": 100000.0}
        annual_budget = executive_funds.get(career["office"], 0.0)
        career["governance"] = {"budget_mi": annual_budget, "annual_budget_mi": annual_budget,
                                "budget_year": date.fromisoformat(transition_date).year, "trust": 50.0, "delivery": 0.0,
                                "political_capital": 50.0, "actions": [], "pipeline": [], "outcomes": {"education": 50.0, "health": 50.0, "security": 50.0, "mobility": 50.0}}
        state["office_status"] = "elected_official"
        state["career_status"] = "in_office"
        state["term_start"] = transition_date
        state["term"] = 1
        address = ensure_communications_state(state)["inauguration"]
        address.update({"required": True, "delivered": False, "legacy_save": False,
                        "date": None, "text": "", "score": None, "rubric": {}})
        messages.append(f"Posse simulada: você assume o cargo de {career['office_label']} em {career['municipality']}/{career['state_code']}.")
        messages.append("O primeiro pronunciamento de posse precisa ser registrado antes de novas decisões.")
    if career["phase"] == "office" and after.isoformat() >= career.get("term_end", "9999-12-31"):
        career["phase"] = "term_complete"
        state["office_status"] = "former_official"
        state["career_status"] = "term_complete"
        messages.append("O mandato simulado terminou. Seu histórico e as próximas opções de carreira continuam disponíveis.")
    if career["phase"] == "outgoing" and after.isoformat() >= career.get("term_end", "9999-12-31"):
        career["phase"] = "opposition"
        state["office_status"] = "former_official"
        state["career_status"] = "opposition"
        messages.append("A transição simulada foi concluída. Você deixa o cargo e segue na oposição; o histórico do mandato permanece salvo.")
    governance = career.get("governance") or {}
    if career.get("phase") == "office" and governance:
        budget_year = int(governance.get("budget_year", before.year))
        if after.year > budget_year:
            annual = float(governance.get("annual_budget_mi", 0))
            governance["budget_mi"] = round(min(annual, float(governance.get("budget_mi", 0)) + annual), 1)
            governance["budget_year"] = after.year
            if career["office"] in LEGISLATIVE_OFFICES:
                governance["political_capital"] = min(100.0, float(governance.get("political_capital", 50)) + 25.0)
            messages.append("O novo ano do mandato começou; a reserva anual simulada foi atualizada.")
        remaining = []
        for item in governance.get("pipeline", []):
            due = date.fromisoformat(item["due_date"])
            if not before < due <= after:
                remaining.append(item)
                continue
            if item["kind"] == "service":
                area = SERVICE_AREAS[item["area"]]
                outcomes = governance.setdefault("outcomes", {})
                outcomes[area["outcome"]] = _clamp(outcomes.get(area["outcome"], 50) + item["effect"])
                governance["delivery"] = float(governance.get("delivery", 0)) + 1
                governance["trust"] = _clamp(governance.get("trust", 50) + 1.5)
                item["status"] = "delivered"
                governance.setdefault("actions", []).append(item)
                messages.append(f"Entrega simulada concluída: {item['title']}. O indicador de serviço sobe para {outcomes[area['outcome']]:.1f}.")
            elif item["kind"] == "bill":
                support = float(state.get("metrics", {}).get("congress_support", 50)) if career["scope"] == "federal" else float(career.get("state_support", 50))
                rng = random.Random(f"{state.get('campaign_seed', 1)}:{item['id']}:vote")
                approved = rng.random() < max(.12, min(.88, .12 + support / 100 * .68))
                item["status"] = "approved" if approved else "rejected"
                if approved:
                    governance["delivery"] = float(governance.get("delivery", 0)) + 1
                    governance["trust"] = _clamp(governance.get("trust", 50) + 2.0)
                    career["local_support"] = _clamp(career.get("local_support", 50) + 1.0)
                    messages.append(f"Proposta legislativa aprovada na simulação: {item['title']}.")
                else:
                    governance["trust"] = _clamp(governance.get("trust", 50) - 1.0)
                    messages.append(f"Proposta legislativa rejeitada na simulação: {item['title']}.")
                governance.setdefault("actions", []).append(item)
            elif item["kind"] == "oversight":
                item["status"] = "concluded"
                governance["trust"] = _clamp(governance.get("trust", 50) + 1.5)
                governance.setdefault("actions", []).append(item)
                messages.append(f"Fiscalização simulada concluída: {item['title']}. O relatório foi publicado na agenda.")
        governance["pipeline"] = remaining
    return [message for message in messages if message]


def _clamp(value: float) -> float:
    return round(max(0.0, min(100.0, float(value))), 2)
