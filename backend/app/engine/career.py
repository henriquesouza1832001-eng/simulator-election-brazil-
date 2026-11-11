"""Reusable political-career and election loop for all simulated offices.

All candidates, polls, votes and people generated here belong to the fictional
simulation. The rules are deliberately explicit so the UI can explain outcomes.
"""
from __future__ import annotations

import random
import re
import unicodedata
import json
from math import sqrt
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from .communications import ensure_communications_state
from .electoral_integrity import campaign_conduct_preview, resolve_campaign_conduct, settle_campaign_conduct
from .geography import get_municipality, get_state_population, resolve_municipality
from .issues import ISSUE_LABELS


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
STATE_CAPITALS = {
    "AC": "1200401", "AL": "2704302", "AP": "1600303", "AM": "1302603", "BA": "2927408",
    "CE": "2304400", "DF": "5300108", "ES": "3205309", "GO": "5208707", "MA": "2111300",
    "MT": "5103403", "MS": "5002704", "MG": "3106200", "PA": "1501402", "PB": "2507507",
    "PR": "4106902", "PE": "2611606", "PI": "2211001", "RJ": "3304557", "RN": "2408102",
    "RS": "4314902", "RO": "1100205", "RR": "1400100", "SC": "4205407", "SP": "3550308",
    "SE": "2800308", "TO": "1721000",
}
GROUPS = {
    "trabalhadores": "Trabalhadores", "empreendedores": "Pequenos negócios", "familias": "Famílias",
    "servidores": "Servidores públicos", "jovens": "Jovens", "rural": "População rural",
}
SPECTRUM_GROUP_EFFECTS = {
    "esquerda": {"trabalhadores": 2.0, "servidores": 1.0, "empreendedores": -1.0},
    "centro_esquerda": {"trabalhadores": 1.2, "familias": .7},
    "centro": {"familias": .4},
    "centro_direita": {"empreendedores": 1.0, "rural": .6},
    "direita": {"empreendedores": 1.8, "rural": 1.0, "servidores": -.6},
}
FAMILY_GROUP_EFFECTS = {
    "trabalhadora": {"trabalhadores": 1.2, "familias": .5},
    "classe_media": {"familias": .6, "empreendedores": .4},
    "empreendedora": {"empreendedores": 1.2},
    "rural": {"rural": 1.4, "trabalhadores": .3},
    "servidora_publica": {"servidores": 1.2, "familias": .3},
    "politica": {"servidores": .3, "empreendedores": .3},
    "educadora": {"familias": .7, "servidores": .6},
    "oficios": {"trabalhadores": .8, "empreendedores": .4},
    "lideranca_comunitaria": {"familias": .5, "trabalhadores": .5},
}
IDEOLOGY_SPECTRUM = {
    "Esquerda": "esquerda", "Centro-esquerda": "centro_esquerda", "Centro": "centro",
    "Centro-direita": "centro_direita", "Direita": "direita",
}
SPECTRUM_ORDER = ["esquerda", "centro_esquerda", "centro", "centro_direita", "direita"]
PARTY_CATALOG_PATH = Path(__file__).resolve().parents[1] / "data" / "parties.json"
CUSTOM_PARTY_BLOCKLIST = {"nazista", "nazismo", "fascista", "fascismo", "nsdap"}
ISSUES = {
    "economia": {"label": ISSUE_LABELS["economia"], "terms": {"emprego", "renda", "preço", "preco", "inflação", "inflacao", "empresa", "trabalho", "salário", "salario"}, "groups": ["trabalhadores", "empreendedores"]},
    "saude": {"label": ISSUE_LABELS["saude"], "terms": {"saúde", "saude", "hospital", "posto", "médico", "medico", "vacina", "atendimento"}, "groups": ["familias", "servidores"]},
    "educacao": {"label": ISSUE_LABELS["educacao"], "terms": {"escola", "educação", "educacao", "professor", "aluno", "creche", "universidade"}, "groups": ["familias", "jovens", "servidores"]},
    "seguranca": {"label": ISSUE_LABELS["seguranca"], "terms": {"segurança", "seguranca", "crime", "polícia", "policia", "investigar", "violência", "violencia"}, "groups": ["familias", "empreendedores"]},
    "mobilidade": {"label": ISSUE_LABELS["mobilidade"], "terms": {"ônibus", "onibus", "transporte", "estrada", "trânsito", "transito", "mobilidade", "ferrovia"}, "groups": ["trabalhadores", "rural"]},
    "integridade": {"label": ISSUE_LABELS["integridade"], "terms": {"transparência", "transparencia", "auditoria", "contrato", "publicar", "fiscalizar", "prestação", "prestacao"}, "groups": ["jovens", "servidores"]},
}
DEBATE_QUESTIONS = {
    "economia": "Seu plano promete emprego e renda. Qual decisão concreta, com que fonte de recursos e prazo, o eleitor poderá cobrar?",
    "saude": "A fila de atendimento continua longa. Qual mudança você prioriza e como vai medir se o serviço melhorou?",
    "educacao": "Os resultados da escola variam muito entre bairros. Qual meta e qual prazo você assume para reduzir essa diferença?",
    "seguranca": "As famílias querem mais segurança sem abuso. Que ação está ao alcance do cargo e como será fiscalizada?",
    "mobilidade": "O deslocamento diário custa tempo e dinheiro. Qual trecho ou serviço será priorizado e quando haverá resultado?",
    "integridade": "O eleitor quer transparência antes que apareça um escândalo. Que dado será publicado e quem poderá fiscalizar?",
}
DEBATE_REPLIES = {
    "economia": "A meta parece boa, mas ainda precisamos saber de onde sai o recurso e quando o emprego aparece.",
    "saude": "O prazo precisa vir acompanhado de equipe, atendimento disponível e prestação de contas.",
    "educacao": "Uma promessa de melhoria não explica como a escola mais distante também será atendida.",
    "seguranca": "A proposta precisa mostrar como protege moradores e mantém fiscalização sobre os agentes públicos.",
    "mobilidade": "O plano precisa mostrar qual trajeto muda primeiro e como a população vai perceber a diferença.",
    "integridade": "Publicar dados ajuda, mas é preciso explicar quem verifica a informação e o que acontece diante de irregularidade.",
}
OPPONENT_CANDIDATE_POOL = [
    {"name": "Lia Sabiá", "party": "Movimento Horizonte", "ideology": "Centro-esquerda", "issue_focus": "educacao"},
    {"name": "Bento do Vale", "party": "Frente do Trabalho", "ideology": "Esquerda", "issue_focus": "economia"},
    {"name": "Nara Campos", "party": "União Cívica", "ideology": "Centro", "issue_focus": "saude"},
    {"name": "Raul Monteiro", "party": "Aliança Regional", "ideology": "Centro-direita", "issue_focus": "mobilidade"},
    {"name": "Ivo Nascimento", "party": "Partido Popular Renovador", "ideology": "Direita", "issue_focus": "seguranca"},
    {"name": "Dora Veredas", "party": "Rede da Comunidade", "ideology": "Centro-esquerda", "issue_focus": "integridade"},
]
ACTIVITIES = {
    "comicio": {"label": "Comício", "days": 2, "cost": 0.045, "reach": 1.35, "channel": "presencial"},
    "debate": {"label": "Debate", "days": 1, "cost": 0.025, "reach": 1.1, "channel": "imprensa"},
    "entrevista": {"label": "Entrevista", "days": 1, "cost": 0.018, "reach": 0.8, "channel": "imprensa"},
    "porta_a_porta": {"label": "Visita a bairros", "days": 2, "cost": 0.035, "reach": 1.2, "channel": "território"},
    "rede_conversa": {"label": "Roda · grupos de mensagem", "days": 1, "cost": 0.012, "reach": 0.72, "channel": "mensageria", "audience": ["familias", "trabalhadores"], "viral": .23},
    "rede_vitrine": {"label": "Vitrine · vídeo e imagem", "days": 1, "cost": 0.018, "reach": 0.92, "channel": "video_curto", "audience": ["jovens", "empreendedores"], "viral": .28},
    "rede_praca": {"label": "Praça · debate público", "days": 1, "cost": 0.016, "reach": 0.82, "channel": "rede_publica", "audience": ["jovens", "servidores"], "viral": .32},
}
TRAVEL_ACTIVITIES = {"comicio", "porta_a_porta"}
PRE_CAMPAIGN_ACTIONS = {
    "mobilizar_voluntariado": {"label": "Organizar voluntariado", "days": 2, "cost": 0.05, "organization": 0.75,
        "summary": "Organiza turnos, contatos e treinamento interno; não publica propaganda nem altera a pesquisa."},
    "reunir_partido": {"label": "Reunir direção partidária", "days": 3, "cost": 0.12, "organization": 1.5,
        "summary": "Alinha responsabilidades da equipe; não altera apoio eleitoral antes da campanha."},
    "mapear_prioridades": {"label": "Mapear prioridades do território", "days": 1, "cost": 0.04, "organization": 0.75,
        "summary": "Prepara um diagnóstico interno sem pedir voto nem publicar promessas."},
}
MAX_PRE_CAMPAIGN_ORGANIZATION = 4.5
APPOINTED_PATHS = {
    "ministro": {"label": "Ministro(a) de Estado", "requires": ["presidente"], "description": "Nomeação presidencial e apoio político; não é cargo eletivo."},
    "stf_indicado": {"label": "Indicação ao STF", "requires": ["presidente"], "description": "Indicação presidencial seguida de sabatina e votação no Senado; não é cargo eletivo."},
}
LEGISLATIVE_OFFICES = {"vereador", "deputado_estadual", "deputado_federal", "senador"}
SERVICE_AREAS = {
    "education": {"label": "Educação básica", "outcome": "education", "effect": 5.0, "days": 180},
    "health": {"label": "Saúde e atendimento", "outcome": "health", "effect": 5.0, "days": 120},
    "security": {"label": "Segurança pública", "outcome": "security", "effect": 4.0, "days": 120},
    "mobility": {"label": "Transporte e mobilidade", "outcome": "mobility", "effect": 4.0, "days": 240},
    "sanitation": {"label": "Saneamento básico", "outcome": "sanitation", "effect": 4.0, "days": 300},
    "infrastructure": {"label": "Infraestrutura e obras", "outcome": "infrastructure", "effect": 3.5, "days": 365},
    "employment": {"label": "Emprego e renda", "outcome": "employment", "effect": 3.0, "days": 180},
}
EXECUTIVE_SERVICE_ACCESS = {
    "prefeito": {"education", "health", "mobility", "sanitation", "employment"},
    "governador": {"education", "health", "security", "mobility", "sanitation", "infrastructure", "employment"},
    "presidente": set(SERVICE_AREAS),
}
EXECUTIVE_SERVICE_BASE_COSTS = {
    "prefeito": {"education": 18.0, "health": 22.0, "mobility": 14.0, "sanitation": 20.0, "employment": 16.0},
    "governador": {"education": 400.0, "health": 500.0, "security": 380.0, "mobility": 650.0, "sanitation": 470.0, "infrastructure": 900.0, "employment": 350.0},
    "presidente": {"education": 4500.0, "health": 6500.0, "security": 5000.0, "mobility": 8500.0, "sanitation": 6000.0, "infrastructure": 12000.0, "employment": 4200.0},
}
EXECUTIVE_BUDGET_BASELINES = {
    "prefeito": {"population": 100_000, "annual_budget_mi": 350.0},
    "governador": {"population": 5_000_000, "annual_budget_mi": 12_000.0},
}
PROMISE_OUTCOMES = {
    "economia": "employment", "saude": "health", "educacao": "education",
    "seguranca": "security", "mobilidade": "mobility",
}
PROMISE_MINIMUM_CHANGE = {"employment": 2.0, "health": 3.0, "education": 3.0, "security": 2.5, "mobility": 2.5}
PROMISE_LIMIT = 6
PROMISE_REVIEW_DAYS = 365
PROMISE_LANGUAGE_PATTERNS = (
    r"\bprometo\b", r"\bprometemos\b", r"\bme comprometo\b", r"\bnos comprometemos\b",
    r"\bassumo o compromisso\b", r"\bcomprometo-me\b", r"\b(?:minha|nossa) meta e\b", r"\b(?:meu|nosso) compromisso e\b",
    r"\b(?:vou|vamos) (?:reduzir|ampliar|aumentar|criar|garantir|entregar|construir|melhorar|implantar|investir|publicar|abrir|diminuir|baixar|zerar|combater|proteger|fortalecer|expandir|contratar|assegurar|apoiar|reformar|priorizar|defender|promover|desenvolver|executar|implementar|preservar)\b",
    r"\b(?:reduzirei|reduziremos|ampliarei|ampliaremos|aumentarei|aumentaremos|criarei|criaremos|garantirei|garantiremos|entregarei|entregaremos|construirei|construiremos|melhorarei|melhoraremos|implantarei|implantaremos|investirei|investiremos|publicarei|publicaremos)\b",
)
LEGISLATIVE_ACTIONS = [
    {"key": "proposal", "label": "Apresentar proposta de lei", "capital": 18, "days": 60, "summary": "A proposta entra em tramitação e enfrenta uma votação simulada."},
    {"key": "oversight", "label": "Fiscalizar contrato ou programa", "capital": 12, "days": 30, "summary": "A fiscalização pode revelar falha, melhorar controle ou abrir um caso político."},
    {"key": "hearing", "label": "Convocar audiência pública", "capital": 8, "days": 1, "summary": "Escuta setores afetados e aumenta a confiança quando há resposta pública."},
]
LEGISLATIVE_ACTIONS_BY_OFFICE = {
    "vereador": [
        {"key": "proposal", "label": "Apresentar projeto de lei municipal", "capital": 10, "days": 45, "summary": "A proposta segue para análise e votação simulada na Câmara Municipal."},
        {"key": "oversight", "label": "Fiscalizar serviço ou contrato da prefeitura", "capital": 7, "days": 21, "summary": "A fiscalização acompanha um serviço municipal e pode revelar falhas ou gerar resposta pública."},
        {"key": "hearing", "label": "Ouvir moradores em audiência pública", "capital": 5, "days": 1, "summary": "A audiência registra demandas do município e amplia a prestação de contas local."},
    ],
    "deputado_estadual": [
        {"key": "proposal", "label": "Apresentar projeto de lei estadual", "capital": 14, "days": 50, "summary": "A proposta segue para comissão e votação simulada na Assembleia Legislativa."},
        {"key": "oversight", "label": "Fiscalizar programa ou contrato estadual", "capital": 9, "days": 30, "summary": "A fiscalização acompanha a execução de uma política estadual e pode abrir cobrança pública."},
        {"key": "hearing", "label": "Realizar audiência na Assembleia", "capital": 7, "days": 1, "summary": "A audiência reúne setores afetados por uma política estadual e registra encaminhamentos."},
    ],
    "deputado_federal": [
        {"key": "proposal", "label": "Apresentar projeto de lei federal", "capital": 18, "days": 60, "summary": "A proposta segue para comissão e tramitação simulada na Câmara dos Deputados."},
        {"key": "oversight", "label": "Fiscalizar ministério ou programa federal", "capital": 12, "days": 30, "summary": "A fiscalização acompanha uma política federal e pode gerar prestação de informações ou cobrança pública."},
        {"key": "hearing", "label": "Convocar audiência em comissão", "capital": 8, "days": 1, "summary": "A comissão ouve setores afetados e registra encaminhamentos sobre a política federal."},
    ],
    "senador": [
        {"key": "proposal", "label": "Apresentar projeto de lei no Senado", "capital": 20, "days": 75, "summary": "A proposta segue para comissão e tramitação simulada no Senado Federal."},
        {"key": "oversight", "label": "Fiscalizar ato ou programa do Executivo", "capital": 14, "days": 45, "summary": "A fiscalização acompanha uma política federal e registra a cobrança institucional do Senado."},
        {"key": "hearing", "label": "Realizar audiência de interesse nacional", "capital": 10, "days": 1, "summary": "A audiência reúne setores afetados e registra recomendações para a atuação do Senado."},
    ],
}


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


def _campaign_poll_schedule(career: dict[str, Any]) -> list[date]:
    start = date.fromisoformat(career["campaign_start"])
    election = date.fromisoformat(career["election_date"])
    scheduled = [start]
    for offset in (30, 60):
        poll_date = start + timedelta(days=offset)
        if poll_date < election:
            scheduled.append(poll_date)
    final_poll = election - timedelta(days=3)
    if final_poll > scheduled[-1]:
        scheduled.append(final_poll)
    return scheduled


def _public_poll_sample_size(career: dict[str, Any]) -> int:
    if career.get("scope") == "municipal":
        population = float((career.get("municipality_profile") or {}).get("population_estimate", 0))
        return max(350, min(1200, round(sqrt(population) * 0.8))) if population > 0 else 600
    if career.get("office") == "presidente":
        return 1800
    if career.get("scope") == "estadual":
        return 1000
    return 1200


def _projected_public_poll_support(state: dict[str, Any], career: dict[str, Any]) -> float:
    from .difficulty import get_difficulty

    difficulty = get_difficulty(state.get("difficulty", "normal"))
    organization = min(8.0, len(career.get("activities", [])) * 0.55 + float(career.get("pre_campaign_organization", 0)))
    fatigue_penalty = max(0, float(career.get("fatigue", 0)) - 60) * 0.035
    opposition_drag = (difficulty.get("opposition_pressure", 1) - 1) * 2.0
    conduct_penalty = float((career.get("conduct") or {}).get("election_penalty", 0))
    if career.get("office") in {"vereador", "deputado_estadual", "deputado_federal"}:
        estimate = float(career.get("poll_support", 0)) * 0.78 + organization + float(career.get("momentum", 0)) * 0.35
    else:
        estimate = float(career.get("poll_support", 0)) * 0.82 + organization + float(career.get("momentum", 0)) * 0.35
    return _clamp(estimate - fatigue_penalty - conduct_penalty - opposition_drag)


def _ensure_opponents(career: dict[str, Any]) -> list[dict[str, Any]]:
    opponents = career.get("opponents")
    if isinstance(opponents, list) and len(opponents) == 3:
        return opponents
    seed = f"{career.get('seed', 1)}:opponents:{career.get('office', '')}:{career.get('state_code', '')}"
    rng = random.Random(seed)
    selected = rng.sample(OPPONENT_CANDIDATE_POOL, 3)
    opponents = [
        {
            "id": f"opponent-{index + 1}",
            **profile,
            "support_weight": round(rng.uniform(0.85, 1.15), 2),
            "simulated": True,
        }
        for index, profile in enumerate(selected)
    ]
    career["opponents"] = opponents
    return opponents


def _opponent_supports(career: dict[str, Any], candidate_support: float) -> list[dict[str, Any]]:
    opponents = _ensure_opponents(career)
    opposition_total = round(max(0.0, 100.0 - float(candidate_support)), 1)
    total_weight = sum(float(item.get("support_weight", 1.0)) for item in opponents) or 1.0
    shares: list[dict[str, Any]] = []
    allocated = 0.0
    for index, opponent in enumerate(opponents):
        if index == len(opponents) - 1:
            support = round(opposition_total - allocated, 1)
        else:
            support = round(opposition_total * float(opponent.get("support_weight", 1.0)) / total_weight, 1)
            allocated += support
        shares.append({
            "id": opponent["id"],
            "name": opponent["name"],
            "party": opponent["party"],
            "ideology": opponent["ideology"],
            "issue_focus": opponent["issue_focus"],
            "issue_focus_label": ISSUES[opponent["issue_focus"]]["label"],
            "support": support,
            "simulated": True,
        })
    return shares


def _requires_second_round(career: dict[str, Any]) -> bool:
    office = career.get("office")
    if office in {"presidente", "governador"}:
        return True
    if office != "prefeito":
        return False
    # The game catalogue has resident-population estimates, not voter rolls. Use
    # this only as a clearly marked proxy for the municipal runoff threshold.
    population = float((career.get("municipality_profile") or {}).get("population_estimate", 0))
    return population > 200_000


def _spectrum_index(candidate: dict[str, Any]) -> int:
    spectrum = IDEOLOGY_SPECTRUM.get(candidate.get("ideology", "Centro"), "centro")
    return SPECTRUM_ORDER.index(spectrum)


def _runoff_vote_results(career: dict[str, Any], poll_support: float | None = None,
                         noise: float = 0.0) -> list[dict[str, Any]]:
    first_round = career.get("first_round_results") or []
    finalists = career.get("runoff_finalists") or sorted(
        first_round, key=lambda item: float(item.get("support", 0)), reverse=True,
    )[:2]
    if len(finalists) < 2:
        return []
    first, second = finalists
    first_share = float(first.get("support", 0))
    second_share = float(second.get("support", 0))
    first_distance = _spectrum_index(first)
    second_distance = _spectrum_index(second)
    for eliminated in first_round:
        if eliminated.get("id") in {first.get("id"), second.get("id")}:
            continue
        eliminated_share = float(eliminated.get("support", 0))
        eliminated_distance = _spectrum_index(eliminated)
        first_affinity = 1 / (1 + abs(eliminated_distance - first_distance))
        second_affinity = 1 / (1 + abs(eliminated_distance - second_distance))
        first_transfer = first_affinity / (first_affinity + second_affinity)
        first_transfer = max(.15, min(.85, first_transfer))
        first_share += eliminated_share * first_transfer
        second_share += eliminated_share * (1 - first_transfer)

    if first.get("is_player") or second.get("is_player"):
        baseline = float(career.get("first_round_poll_support", career.get("poll_support", 0)))
        current = float(career.get("poll_support", 0) if poll_support is None else poll_support)
        shift = max(-5.0, min(5.0, (current - baseline) * .3 + float(career.get("momentum", 0)) * .15))
        if first.get("is_player"):
            first_share += shift
            second_share -= shift
        else:
            second_share += shift
            first_share -= shift
    if first.get("is_player"):
        first_share += noise
        second_share -= noise
    elif second.get("is_player"):
        second_share += noise
        first_share -= noise
    else:
        first_share += noise
        second_share -= noise

    first_final = round(max(0.0, min(100.0, first_share)), 1)
    first_result = {**first, "support": first_final, "round": 2, "simulated": True}
    second_result = {**second, "support": round(100 - first_final, 1), "round": 2, "simulated": True}
    return sorted([first_result, second_result], key=lambda item: item["support"], reverse=True)


def _record_public_poll(state: dict[str, Any], career: dict[str, Any], field_date: date) -> dict[str, Any] | None:
    polls = career.setdefault("public_polls", [])
    if any(item.get("date") == field_date.isoformat() for item in polls):
        return None
    sample_size = _public_poll_sample_size(career)
    margin = round(1.96 * sqrt(0.25 / sample_size) * 100, 1)
    seed = f"{career.get('seed', 1)}:public-poll:{field_date.isoformat()}"
    noise = random.Random(seed).uniform(-margin, margin)
    if career.get("phase") == "runoff_campaign":
        runoff_results = _runoff_vote_results(career, noise=noise)
        player_result = next((item for item in runoff_results if item.get("is_player")), None)
        if not player_result:
            return None
        candidate_support = player_result["support"]
        opponents = [{
            "id": item["id"], "name": item["name"], "party": item["party"],
            "ideology": item.get("ideology", "Centro"), "issue_focus": item.get("issue_focus", "integridade"),
            "issue_focus_label": ISSUES[item.get("issue_focus", "integridade")]["label"],
            "support": item["support"], "simulated": True,
        } for item in runoff_results if not item.get("is_player")]
    else:
        candidate_support = round(_clamp(_projected_public_poll_support(state, career) + noise), 1)
        opponents = _opponent_supports(career, candidate_support)
    career["opponent_share"] = max((item["support"] for item in opponents), default=0.0)
    record = {
        "date": field_date.isoformat(),
        "round": 2 if career.get("phase") == "runoff_campaign" else 1,
        "candidate_name": career.get("candidate_name", "Candidatura do jogador"),
        "candidate_support": candidate_support,
        "other_candidates_support": round(100 - candidate_support, 1),
        "opponents": opponents,
        "margin_of_error": margin,
        "sample_size": sample_size,
        "simulated": True,
    }
    polls.append(record)
    career["public_polls"] = polls[-12:]
    return record


def start_career(state: dict[str, Any], office: str, state_code: str, municipality: str,
                 party: str, ideology: str, candidate_name: str,
                 character: dict[str, Any] | None = None,
                 municipality_id: str | None = None) -> dict[str, Any]:
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
    election_day = _regular_election_day(office, today)
    campaign_start = election_day - timedelta(days=90)
    inauguration = _inauguration_date(office, election_day)
    term_end = _term_end_date(office, inauguration, role["term_years"])
    phase = "campaign" if today >= campaign_start else "pre_campaign"
    local_strength = 39.0 if office in {"vereador", "prefeito"} else 35.0
    party_spectrum = IDEOLOGY_SPECTRUM.get(ideology, "centro")
    spectrum_gap = abs(SPECTRUM_ORDER.index(character["political_spectrum"]) - SPECTRUM_ORDER.index(party_spectrum))
    initial_poll = _clamp(role["base_support"] + (previous_reputation - 50) * .22 + (.5 if "carismatica" in traits else 0) - spectrum_gap * .45)
    group_support = {key: 45.0 for key in GROUPS}
    for adjustment in (SPECTRUM_GROUP_EFFECTS[character["political_spectrum"]], FAMILY_GROUP_EFFECTS[character["family_background"]]):
        for group, amount in adjustment.items():
            group_support[group] = _clamp(group_support[group] + amount)
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


def _campaign(state: dict[str, Any]) -> dict[str, Any]:
    career = state.get("career") or {}
    if not career.get("mode"):
        raise ValueError("Esta partida ainda não iniciou uma carreira política.")
    return career


def _campaign_team_location_id(career: dict[str, Any]) -> str | None:
    current = career.get("campaign_team_municipality_id")
    if current:
        return str(current)
    if career.get("scope") == "municipal":
        return career.get("municipality_id")
    return STATE_CAPITALS.get(career.get("state_code", ""))


def is_career_governing(career: dict[str, Any], today: date) -> bool:
    """Whether this character still holds the elected office on this date."""
    phase = career.get("phase")
    office_start = career.get("office_start")
    if phase not in {"office", "campaign", "runoff_campaign", "runoff_observer", "outgoing", "transition"}:
        return False
    if phase != "office" and not office_start:
        return False
    term_end = career.get("term_end")
    if not term_end:
        if not office_start:
            return phase == "office"
        role = OFFICES.get(career.get("office"), {})
        term_years = int(career.get("term_years") or role.get("term_years", 4))
        term_end = _term_end_date(career["office"], date.fromisoformat(office_start), term_years).isoformat()
    return today <= date.fromisoformat(term_end)


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


def _promise_rule(issue: str, message: str, career: dict[str, Any]) -> dict[str, Any]:
    """Select a visible, deterministic piece of in-game evidence for a promise."""
    normalized = _norm(message)
    if issue == "economia" and career.get("office") == "presidente":
        metric = next((key for terms, key in (
            ({"inflacao", "preco", "precos", "custo de vida"}, "inflation"),
            ({"desemprego", "emprego", "trabalho"}, "unemployment"),
            ({"crescimento", "pib", "economia"}, "gdp_growth"),
        ) if any(_norm(term) in normalized for term in terms)), None)
        if metric:
            metric_labels = {"inflation": "inflação anual", "unemployment": "desemprego", "gdp_growth": "crescimento do PIB"}
            direction = "up" if metric == "gdp_growth" else "down"
            return {"kind": "metric", "key": metric, "label": metric_labels[metric], "direction": direction,
                    "minimum_change": 0.2, "rule": f"o indicador simulado de {metric_labels[metric]} precisa melhorar ao menos 0,2 ponto."}
    if issue == "seguranca" and career.get("office") == "prefeito":
        return {"kind": "unsupported", "key": "security", "label": "segurança municipal",
                "direction": "evidence", "minimum_change": 0.0,
                "rule": "o recorte atual ainda não modela um indicador municipal de segurança; a promessa será registrada, sem avaliação ou penalidade."}
    outcome = PROMISE_OUTCOMES.get(issue)
    if outcome and career.get("office") not in LEGISLATIVE_OFFICES:
        return {"kind": "outcome", "key": outcome, "label": SERVICE_AREAS[outcome]["label"],
                "direction": "up", "minimum_change": PROMISE_MINIMUM_CHANGE[outcome],
                "rule": f"o indicador de {SERVICE_AREAS[outcome]['label'].lower()} precisa subir ao menos {PROMISE_MINIMUM_CHANGE[outcome]:.1f} pontos com uma entrega concluída."}
    if issue == "integridade":
        evidence = "prestação de contas pública" if career.get("office") not in LEGISLATIVE_OFFICES else "fiscalização concluída ou projeto relacionado aprovado"
        return {"kind": "integrity", "key": "trust", "label": "confiança e transparência", "direction": "up",
                "minimum_change": 1.5, "rule": f"é preciso registrar {evidence} depois da promessa e preservar ao menos 1,5 ponto de confiança."}
    issue_label = ISSUES[issue]["label"].lower()
    return {"kind": "bill", "key": issue, "label": f"entrega legislativa em {issue_label}", "direction": "evidence",
            "minimum_change": 1.0, "rule": f"ao menos um projeto relacionado a {issue_label} precisa ser aprovado na simulação."}


def _promise_baseline(state: dict[str, Any], career: dict[str, Any], rule: dict[str, Any]) -> float:
    rule_kind = rule.get("kind", rule.get("metric_kind"))
    rule_key = rule.get("key", rule.get("metric_key"))
    if rule_kind == "metric":
        return float(state.get("metrics", {}).get(rule_key, state.get("social_indicators", {}).get(rule_key, 0.0)))
    governance = career.get("governance") or {}
    if rule_kind == "outcome":
        return float((governance.get("outcomes") or {}).get(rule_key, 50.0))
    return float(governance.get("trust", 50.0))


def _is_explicit_promise(message: str) -> bool:
    normalized = _norm(message)
    if re.search(r"\bnao\s+(?:(?:vou|vamos)\s+|prometo\b|prometemos\b|me comprometo\b|nos comprometemos\b)", normalized):
        return False
    return any(re.search(pattern, normalized) for pattern in PROMISE_LANGUAGE_PATTERNS)


def _record_campaign_promise(state: dict[str, Any], career: dict[str, Any], issue: str,
                             message: str) -> dict[str, Any] | None:
    if not _is_explicit_promise(message):
        return None
    promises = career.setdefault("campaign_promises", [])
    election_cycle = career.get("election_date")
    if any(item.get("status") == "pending" and item.get("issue") == issue
           and item.get("election_date") == election_cycle for item in promises):
        return {"status": "not_recorded", "issue_label": ISSUES[issue]["label"],
                "statement": message.strip()[:600],
                "evidence_rule": "Já existe uma promessa pendente sobre esse tema neste ciclo eleitoral.",
                "review_date": None}
    if sum(item.get("status") == "pending" for item in promises) >= PROMISE_LIMIT:
        return {"status": "not_recorded", "issue_label": ISSUES[issue]["label"],
                "statement": message.strip()[:600],
                "evidence_rule": f"O limite de {PROMISE_LIMIT} promessas pendentes já foi atingido.",
                "review_date": None}
    today = date.fromisoformat(state["date"])
    governing = is_career_governing(career, today)
    rule = _promise_rule(issue, message, career)
    office_start = career.get("office_start") if governing else None
    review_date = None
    baseline = None
    reference_date = None
    if governing:
        review_day = today + timedelta(days=PROMISE_REVIEW_DAYS)
        term_end = date.fromisoformat(career.get("term_end", review_day.isoformat()))
        review_date = min(review_day, term_end).isoformat()
        baseline = _promise_baseline(state, career, rule)
        reference_date = today.isoformat()
    promise = {
        "id": f"pledge-{today.isoformat()}-{issue}-{len(promises) + 1}",
        "date": today.isoformat(), "election_date": election_cycle,
        "issue": issue, "issue_label": ISSUES[issue]["label"],
        "statement": message.strip()[:600], "status": "pending",
        "review_date": review_date, "reference_date": reference_date,
        "baseline": baseline, "metric_kind": rule["kind"], "metric_key": rule["key"],
        "metric_label": rule["label"], "direction": rule["direction"],
        "minimum_change": rule["minimum_change"], "evidence_rule": rule["rule"],
        "office": career.get("office"), "simulated": True,
    }
    promises.append(promise)
    career["campaign_promises"] = promises[-30:]
    return promise


def _activate_campaign_promises(state: dict[str, Any], career: dict[str, Any], office_start: date,
                                *, reset_existing: bool = False) -> None:
    for promise in career.get("campaign_promises", []):
        if promise.get("status") != "pending":
            continue
        review_date = promise.get("review_date")
        if review_date and not reset_existing:
            continue
        promise["reference_date"] = office_start.isoformat()
        promise["baseline"] = _promise_baseline(state, career, promise)
        promise["office"] = career.get("office")
        limit = office_start + timedelta(days=PROMISE_REVIEW_DAYS)
        term_end = date.fromisoformat(career.get("term_end", limit.isoformat()))
        promise["review_date"] = min(limit, term_end).isoformat()
        promise["activated_at"] = office_start.isoformat()
        promise["baseline_source"] = "indicador registrado na posse simulada"


def _promise_evidence(state: dict[str, Any], career: dict[str, Any], promise: dict[str, Any]) -> tuple[float, bool]:
    rule_kind = promise.get("metric_kind")
    key = promise.get("metric_key")
    reference_date = promise.get("reference_date") or promise.get("date", "9999-12-31")
    if rule_kind == "metric":
        observed = float(state.get("metrics", {}).get(key, state.get("social_indicators", {}).get(key, 0.0)))
        baseline = float(promise.get("baseline", observed))
        delta = observed - baseline if promise.get("direction") == "up" else baseline - observed
        return round(delta, 3), delta >= float(promise.get("minimum_change", 0.2))
    governance = career.get("governance") or {}
    if rule_kind == "outcome":
        observed = float((governance.get("outcomes") or {}).get(key, promise.get("baseline", 50.0)))
        baseline = float(promise.get("baseline", observed))
        delta = observed - baseline
        return round(delta, 2), delta >= float(promise.get("minimum_change", 1.0))
    actions = list(governance.get("actions", []))
    reports = list(governance.get("public_reports", []))
    if rule_kind == "integrity":
        relevant_reports = [item for item in reports if item.get("date", "") > reference_date]
        relevant_oversight = [item for item in actions if item.get("kind") == "oversight"
                              and item.get("status") == "concluded"
                              and (item.get("completed_at") or item.get("due_date") or "") > reference_date]
        trust_delta = float(governance.get("trust", 50.0)) - float(promise.get("baseline", 50.0))
        return round(trust_delta, 2), bool(relevant_reports or relevant_oversight) and trust_delta >= float(promise.get("minimum_change", 1.5))
    terms = [_norm(term) for term in ISSUES.get(key, {}).get("terms", set())]
    approved = [item for item in actions if item.get("kind") == "bill" and item.get("status") == "approved"
                and (item.get("completed_at") or item.get("due_date") or "") > reference_date
                and any(term and term in _norm(str(item.get("title", ""))) for term in terms)]
    return (1.0 if approved else 0.0), bool(approved)


def _review_campaign_promises(state: dict[str, Any], career: dict[str, Any], before: date,
                              after: date) -> list[str]:
    messages: list[str] = []
    governance = career.get("governance") or {}
    for promise in career.get("campaign_promises", []):
        if promise.get("status") != "pending" or not promise.get("review_date"):
            continue
        review_date = date.fromisoformat(promise["review_date"])
        if not before < review_date <= after:
            continue
        office_start = career.get("office_start")
        term_end = career.get("term_end")
        if not office_start or review_date < date.fromisoformat(office_start):
            continue
        if term_end and review_date > date.fromisoformat(term_end):
            continue
        if promise.get("metric_kind") == "unsupported":
            promise.update({"status": "not_assessed", "reviewed_on": review_date.isoformat(),
                            "observed_change": 0.0, "review_office": career.get("office"), "simulated": True})
            territory = career.get("municipality") or career.get("state_name", "")
            state.setdefault("simulated_news", []).insert(0, {
                "id": f"{promise['id']}-review", "date": review_date.isoformat(),
                "title": f"Compromisso sem indicador municipal: {promise['issue_label']}",
                "region": territory,
                "description": f"A promessa foi registrada, mas {promise['evidence_rule']} Nenhum efeito de reputação foi aplicado.",
                "simulated": True,
            })
            promise["news_id"] = f"{promise['id']}-review"
            messages.append(f"O simulador registrou a promessa sobre {promise['issue_label'].lower()}, mas ainda não dispõe de indicador municipal para avaliá-la.")
            continue
        delta, fulfilled = _promise_evidence(state, career, promise)
        promise.update({"status": "fulfilled" if fulfilled else "questioned", "reviewed_on": review_date.isoformat(),
                        "observed_change": delta, "review_office": career.get("office"),
                        "simulated": True})
        impact = 1.2 if fulfilled else -1.2
        career["reputation"] = _clamp(float(career.get("reputation", 50.0)) + impact)
        career["poll_support"] = round(_clamp(float(career.get("poll_support", 50.0)) + impact * .6), 2)
        for group in ISSUES[promise["issue"]]["groups"]:
            career.setdefault("group_support", {})[group] = _clamp(
                career.get("group_support", {}).get(group, 45.0) + impact * .4
            )
        territory = career.get("municipality") or ("Brasil" if career.get("office") == "presidente" else career.get("state_name", ""))
        if fulfilled:
            headline = f"Promessa de campanha cumprida: {promise['issue_label']}"
            if promise.get("metric_kind") == "bill":
                evidence_text = "A simulação registrou a aprovação de uma proposta legislativa relacionada ao tema."
            elif promise.get("metric_kind") == "integrity":
                evidence_text = f"A confiança simulada variou {delta:+.1f} ponto(s) e houve uma ação pública de transparência ou fiscalização."
            else:
                evidence_text = f"O indicador de {promise['metric_label']} avançou {delta:.1f} ponto(s) desde a referência registrada."
            description = f"A prestação de contas simulada registra o compromisso: {promise['statement']} {evidence_text}"
            messages.append(f"Cobrança simulada concluída: a promessa sobre {promise['issue_label'].lower()} foi atendida.")
        else:
            headline = f"Cobrança de campanha: {promise['issue_label']}"
            description = (f"A promessa registrada foi: {promise['statement']} "
                           f"A simulação não encontrou evidência suficiente até {review_date.strftime('%d/%m/%Y')}: {promise['evidence_rule']}")
            messages.append(f"Cobrança simulada: não houve evidência suficiente para a promessa sobre {promise['issue_label'].lower()}.")
        state.setdefault("simulated_news", []).insert(0, {
            "id": f"{promise['id']}-review", "date": review_date.isoformat(), "title": headline,
            "region": territory, "description": description, "simulated": True,
        })
        promise["news_id"] = f"{promise['id']}-review"
    state["simulated_news"] = state.get("simulated_news", [])[:20]
    return messages


def career_overview(state: dict[str, Any]) -> dict[str, Any] | None:
    career = state.get("career")
    if not career or not career.get("mode"):
        return None
    municipality_profile = career.get("municipality_profile")
    if municipality_profile is None:
        municipality_profile = resolve_municipality(career.get("state_code", ""), career.get("municipality", ""))
        if municipality_profile:
            career["municipality_id"] = municipality_profile["ibge_code"]
            career["municipality_profile"] = municipality_profile
    team_city_id = _campaign_team_location_id(career)
    team_city_profile = get_municipality(team_city_id) if team_city_id else None
    today = date.fromisoformat(state["date"])
    election_day = date.fromisoformat(career["election_date"])
    campaign_start = date.fromisoformat(career.get("campaign_start", (election_day - timedelta(days=90)).isoformat()))
    last_action = career.get("last_action_date")
    wait = max(0, 7 - (today - date.fromisoformat(last_action)).days) if last_action else 0
    opponents = _ensure_opponents(career)
    role = OFFICES[career["office"]]
    governance = career.get("governance") or {}
    _ensure_scaled_governance_budget(career, governance)
    governance_budget_mi = round(float(governance.get("budget_mi", 0)), 1)
    governance_annual_budget_mi = round(float(governance.get("annual_budget_mi", 0)), 1)
    governance_budget_source = "career_reserve"
    governance_investment_commitment_mi = round(float(governance.get("investment_commitment_mi", 0)), 1)
    if career.get("office") == "presidente" and governance:
        governance_annual_budget_mi = round(_presidential_investment_cap_mi(state), 1)
        governance_investment_commitment_mi = round(_presidential_investment_commitment_mi(governance), 1)
        governance_budget_mi = round(max(0.0, governance_annual_budget_mi - governance_investment_commitment_mi), 1)
        governance_budget_source = "federal_investment"
    governing = is_career_governing(career, today)
    governance_actions = governance_actions_for(career, governance) if governing else []
    governance_territory = governance_territory_for(career)
    governance_wait = max(0, 30 - (today - date.fromisoformat(governance.get("last_action_date", today.isoformat()))).days) if governance.get("last_action_date") else 0
    in_campaign = career["phase"] in {"campaign", "runoff_campaign"} and campaign_start <= today <= election_day
    next_campaign = max(0, (campaign_start - today).days) if career["phase"] in {"office", "pre_campaign"} else 0
    city_support = career.get("municipality_support", {})
    recent_city_ids = []
    for activity in reversed(career.get("activities", [])):
        city_id = activity.get("municipality_id")
        if city_id and city_id not in recent_city_ids:
            recent_city_ids.append(city_id)
        if len(recent_city_ids) >= 6:
            break
    campaign_city_support = []
    for city_id in recent_city_ids:
        profile = get_municipality(city_id)
        if profile and city_id in city_support:
            campaign_city_support.append({
                "municipality_id": city_id,
                "municipality_name": profile["name"],
                "state_code": profile["state_code"],
                "support": round(float(city_support[city_id]), 1),
            })
    return {
        "mode": True, "office": career["office"], "office_label": career["office_label"], "scope": career["scope"],
        "phase": career["phase"], "candidate_name": career["candidate_name"], "party": career["party"], "ideology": career["ideology"],
        "governing": governing,
        "party_alignment_gap": career.get("party_alignment_gap", 0),
        "character": career.get("character", {}),
        "state_code": career["state_code"], "state_name": career["state_name"], "municipality": career["municipality"],
        "campaign_territory": career.get("municipality") or ("Brasil" if career.get("office") == "presidente" else career["state_name"]),
        "municipality_id": career.get("municipality_id"), "municipality_profile": municipality_profile,
        "campaign_team_location": ({
            "municipality_id": team_city_profile["ibge_code"], "name": team_city_profile["name"],
            "state_code": team_city_profile["state_code"], "macroregion": team_city_profile["macroregion"],
        } if team_city_profile else None),
        "electorate": career["electorate"], "powers": career["powers"], "election_date": career["election_date"],
        "inauguration_date": career["inauguration_date"], "term_end": career["term_end"], "term_years": career["term_years"],
        "days_until_election": max(0, (election_day - today).days),
        "campaign_start_date": campaign_start.isoformat(),
        "days_until_campaign": next_campaign,
        "days_until_inauguration": max(0, (date.fromisoformat(career["inauguration_date"]) - today).days),
        "campaign_active": in_campaign,
        "runoff_active": career.get("phase") in {"runoff_campaign", "runoff_observer"},
        "first_round_date": career.get("first_round_date"), "runoff_date": career.get("runoff_date"),
        "first_round_vote_share": career.get("first_round_vote_share"),
        "first_round_results": career.get("first_round_results", []),
        "runoff_finalists": career.get("runoff_finalists", []),
        "runoff_results": career.get("runoff_results", []),
        "runoff_projection": _runoff_vote_results(career) if career.get("phase") == "runoff_campaign" else [],
        "can_act": in_campaign and wait == 0 and career["campaign_fund_mi"] >= 0.01,
        "pre_campaign_organization": round(float(career.get("pre_campaign_organization", 0)), 2),
        "pre_campaign_organization_cap": MAX_PRE_CAMPAIGN_ORGANIZATION,
        "pre_campaign_preparations": list(reversed(career.get("preparations", [])[-8:])),
        "preparation_wait_days": max(0, 30 - (today - date.fromisoformat(career["last_preparation_date"])).days) if career.get("last_preparation_date") else 0,
        "can_prepare": (
            career.get("phase") == "pre_campaign" and today < campaign_start
            and float(career.get("pre_campaign_organization", 0)) < MAX_PRE_CAMPAIGN_ORGANIZATION
            and (not career.get("last_preparation_date") or (today - date.fromisoformat(career["last_preparation_date"])).days >= 30)
            and any(career.get("campaign_fund_mi", 0) >= action["cost"] for action in PRE_CAMPAIGN_ACTIONS.values())
        ),
        "preparation_options": [{"key": key, **action, "affordable": career.get("campaign_fund_mi", 0) >= action["cost"]} for key, action in PRE_CAMPAIGN_ACTIONS.items()],
        "public_polls": list(reversed(career.get("public_polls", [])[-8:])),
        "latest_public_poll": (career.get("public_polls") or [None])[-1],
        "days_until_action": wait, "poll_support": round(career["poll_support"], 1), "local_support": round(career["local_support"], 1),
        "state_support": round(career["state_support"], 1), "national_support": round(career["national_support"], 1),
        "reputation": round(float(career.get("reputation", 50)), 1), "history": list(reversed(career.get("history", [])[-12:])),
        "campaign_promises": list(reversed(career.get("campaign_promises", [])[-12:])),
        "pending_campaign_promises": sum(item.get("status") == "pending" for item in career.get("campaign_promises", [])),
        "momentum": round(career["momentum"], 1), "fatigue": career["fatigue"],
        "campaign_fund_mi": round(career["campaign_fund_mi"], 3), "spent_mi": round(career["spent_mi"], 3),
        "opponent_share": round(career["opponent_share"], 1), "opponents": [
            {"id": item["id"], "name": item["name"], "party": item["party"], "ideology": item["ideology"],
             "issue_focus": item["issue_focus"], "issue_focus_label": ISSUES[item["issue_focus"]]["label"], "simulated": True}
            for item in opponents
        ], "candidate_results": career.get("candidate_results", []),
        "result": career.get("result"), "vote_share": career.get("vote_share"),
        "conduct_review": career.get("conduct_review"), "electoral_result": career.get("electoral_result"),
        "can_start_campaign": career.get("phase") in {"opposition", "term_complete"},
        "groups": [{"key": key, "label": label, "support": round(career["group_support"][key], 1)} for key, label in GROUPS.items()],
        "activities": list(reversed(career["activities"][-10:])),
        "campaign_city_support": campaign_city_support,
        "debate_prompts": {key: career_debate_prompt(career, key) for key in ISSUES},
        "activity_options": [{"key": key, "label": item["label"], "days": item["days"], "requires_travel": key in TRAVEL_ACTIVITIES, "cost_mi": round(item["cost"] * (.9 if "gestora" in (career.get("character") or {}).get("traits", []) else 1.0), 4)} for key, item in ACTIVITIES.items()],
        "issue_options": [{"key": key, "label": value["label"]} for key, value in ISSUES.items()],
        "appointment_paths": [{"key": key, **value, "available": career["office"] in value["requires"] and governing} for key, value in APPOINTED_PATHS.items()],
        "governance": career.get("governance"), "next_campaign_days": next_campaign,
        "public_reports": list(reversed((governance.get("public_reports") or [])[-8:])),
        "governance_actions": governance_actions, "governance_wait_days": governance_wait,
        "governance_territory": governance_territory,
        "governance_budget_mi": governance_budget_mi,
        "governance_annual_budget_mi": governance_annual_budget_mi,
        "governance_budget_source": governance_budget_source,
        "governance_investment_commitment_mi": governance_investment_commitment_mi,
        "governance_budget_price_index": round(float(governance.get("budget_price_index", 1.0)), 3),
        "governance_budget_year": int(governance.get("budget_year", today.year)),
        "political_capital": round(float(governance.get("political_capital", 0)), 1),
        "rules": {"campaign_window_days": 90, "activity_cooldown_days": 7, "election_and_vote_simulated": True,
                  "government_keeps_running": True, "player_governs_until_term_end": governing},
        "conduct_preview": campaign_conduct_preview(state, career),
        "inaugural_address": ensure_communications_state(state)["inauguration"],
        "notice": "Candidatos, partidos, pesquisas e resultados desta carreira são gerados para a simulação.",
    }


def perform_governance_action(state: dict[str, Any], action: str, service: str = "", issue: str = "") -> dict[str, Any]:
    career = _campaign(state)
    if not is_career_governing(career, date.fromisoformat(state["date"])):
        raise ValueError("Você precisa estar empossado para tomar decisões neste cargo.")
    governance = career.setdefault("governance", {"budget_mi": 0.0, "trust": 50.0, "delivery": 0.0, "political_capital": 50.0, "actions": [], "pipeline": [], "outcomes": {}})
    _ensure_scaled_governance_budget(career, governance)
    if career["office"] == "presidente":
        annual_investment_mi = _presidential_investment_cap_mi(state)
        committed_mi = _presidential_investment_commitment_mi(governance)
        governance["annual_budget_mi"] = annual_investment_mi
        governance["investment_commitment_mi"] = round(committed_mi, 1)
        governance["budget_source"] = "federal_investment"
        governance["budget_mi"] = round(max(0.0, annual_investment_mi - committed_mi), 1)
    last = governance.get("last_action_date")
    if last and (date.fromisoformat(state["date"]) - date.fromisoformat(last)).days < 30:
        wait = 30 - (date.fromisoformat(state["date"]) - date.fromisoformat(last)).days
        raise ValueError(f"A agenda do cargo foi usada. A próxima decisão abre em {wait} dia(s).")
    public_report = None
    selected = None
    if career["office"] in LEGISLATIVE_OFFICES:
        selected = next((item for item in governance_actions_for(career, governance) if item["key"] == action), None)
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
        selected = next((item for item in governance_actions_for(career, governance) if item["key"] == action), None)
        if selected and action.startswith("service_"):
            area_key = selected["area"]
            area = SERVICE_AREAS[area_key]
            cost = selected["cost_mi"]
            if governance.get("budget_mi", 0) < cost:
                raise ValueError("A reserva anual desta agenda não cobre o programa. Reavalie o orçamento ou aguarde o próximo ano.")
            governance["budget_mi"] = round(governance["budget_mi"] - cost, 1)
            if career["office"] == "presidente":
                governance["investment_commitment_mi"] = round(
                    _presidential_investment_commitment_mi(governance) + cost, 1
                )
            due_date = date.fromisoformat(state["date"]) + timedelta(days=area["days"])
            territory = governance_territory_for(career)
            governance.setdefault("pipeline", []).append({"id": f"service-{state['date']}-{len(governance.get('actions', [])) + 1}", "kind": "service", "area": area_key, "title": area["label"], "territory": territory["name"], "territory_scope": territory["scope"], "municipality_id": territory.get("municipality_id"), "effect": area["effect"], "cost_mi": cost, "cost_basis": selected.get("cost_basis"), "started_at": state["date"], "due_date": due_date.isoformat(), "status": "in_progress", "simulated": True})
            summary = f"Programa de {area['label'].lower()} iniciado para {territory['name']}. Custo reservado: R$ {cost:,.1f} milhões; entrega prevista para {due_date.strftime('%d/%m/%Y')} se não houver atraso."
        elif action == "public_report":
            cost = 0.0
            public_report = _publish_governance_report(state, career, governance)
            governance["trust"] = _clamp(governance.get("trust", 50) + 2.0)
            career["group_support"]["jovens"] = _clamp(career["group_support"].get("jovens", 45) + 1.0)
            summary = (f"Prestação de contas simulada publicada para {public_report['period_start']} a {public_report['period_end']}: "
                       f"R$ {public_report['programs_reserved_mi']:.1f} milhões reservados, "
                       f"{public_report['programs_completed']} programa(s) concluído(s) e "
                       f"{public_report['programs_in_progress']} em andamento.")
        else:
            raise ValueError("Esta ação não pertence às atribuições executivas deste cargo.")
    governance["last_action_date"] = state["date"]
    entry = {"id": f"office-{state['date']}-{len(governance.get('actions', [])) + 1}", "date": state["date"], "action": action,
             "title": issue.strip()[:100] or next((item["label"] for item in governance_actions_for(career) if item["key"] == action), action.replace("_", " ").title()),
             "summary": summary, "cost_mi": cost, "cost_basis": selected.get("cost_basis") if selected else None,
             "status": "active", "simulated": True}
    if public_report:
        entry["report_id"] = public_report["id"]
    governance.setdefault("actions", []).append(entry)
    governance["actions"] = governance["actions"][-50:]
    return {"action": entry, "summary": summary, "governance": governance,
            "public_report": public_report, "days_cost": 1}


def _publish_governance_report(state: dict[str, Any], career: dict[str, Any],
                               governance: dict[str, Any]) -> dict[str, Any]:
    """Save an auditable, simulated snapshot of this executive's recorded work."""
    today = date.fromisoformat(state["date"])
    previous_report_date = governance.get("last_public_report_date")
    period_start = (
        date.fromisoformat(previous_report_date) + timedelta(days=1)
        if previous_report_date
        else date.fromisoformat(career.get("office_start") or career.get("inauguration_date") or state["date"])
    )
    if period_start > today:
        period_start = today
    period_start_label = period_start.strftime("%Y-%m-%d")
    period_end_label = today.isoformat()
    actions = governance.get("actions", [])
    period_actions = [
        item for item in actions
        if item.get("date") and period_start_label <= item["date"] <= period_end_label
        and item.get("action") != "public_report"
    ]
    completed = [
        item for item in actions
        if item.get("kind") == "service" and item.get("status") == "delivered"
        and period_start_label <= item.get("completed_at", "") <= period_end_label
    ]
    current_programs = [item for item in governance.get("pipeline", []) if item.get("kind") == "service"]
    territory = governance_territory_for(career)
    annual_budget = float(governance.get("annual_budget_mi", governance.get("budget_mi", 0)))
    budget_available = float(governance.get("budget_mi", 0))
    if career.get("office") == "presidente":
        committed = _presidential_investment_commitment_mi(governance)
        committed_label = "Dotação federal comprometida neste ano"
    else:
        committed = sum(float(item.get("cost_mi", 0)) for item in current_programs)
        committed_label = "Custo previsto dos programas em andamento"
    report = {
        "id": f"report-{today.isoformat()}-{len(governance.get('public_reports', [])) + 1}",
        "date": today.isoformat(),
        "period_start": period_start_label,
        "period_end": period_end_label,
        "office": career.get("office_label", career.get("office", "")),
        "territory": territory["name"],
        "annual_budget_mi": round(annual_budget, 1),
        "budget_available_mi": round(budget_available, 1),
        "budget_committed_mi": round(committed, 1),
        "budget_committed_label": committed_label,
        "programs_reserved_mi": round(sum(float(item.get("cost_mi", 0)) for item in period_actions
                                           if str(item.get("action", "")).startswith("service_")), 1),
        "programs_started": sum(1 for item in period_actions if str(item.get("action", "")).startswith("service_")),
        "programs_completed": len(completed),
        "programs_in_progress": len(current_programs),
        "outcomes": {key: round(float(value), 1) for key, value in (governance.get("outcomes") or {}).items()},
        "simulated": True,
    }
    governance.setdefault("public_reports", []).append(report)
    governance["public_reports"] = governance["public_reports"][-12:]
    governance["last_public_report_date"] = today.isoformat()
    return report


def governance_actions_for(career: dict[str, Any], governance: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    if career["office"] in LEGISLATIVE_OFFICES:
        return [dict(item) for item in LEGISLATIVE_ACTIONS_BY_OFFICE.get(career["office"], LEGISLATIVE_ACTIONS)]
    office = career["office"]
    if office in EXECUTIVE_SERVICE_ACCESS:
        active_governance = governance or career.get("governance") or {}
        index = float(active_governance.get("budget_price_index", 1.0))
        population_basis = _executive_population_basis(career)
        cost_basis = (
            f"População IBGE {population_basis['reference_year']}: "
            f"{_format_population_count(population_basis['population'])} habitantes; "
            f"referência do parâmetro: {_format_population_count(population_basis['reference_population'])} habitantes; "
            f"índice de preços acumulado ×{index:.3f}."
            if office in EXECUTIVE_BUDGET_BASELINES else
            f"Escala federal do jogo; índice de preços acumulado ×{index:.3f}."
        )
        actions = []
        for area_key in SERVICE_AREAS:
            if area_key not in EXECUTIVE_SERVICE_ACCESS[office]:
                continue
            area = SERVICE_AREAS[area_key]
            base_cost = EXECUTIVE_SERVICE_BASE_COSTS[office][area_key]
            scale = population_basis["scale"] if office in EXECUTIVE_BUDGET_BASELINES else 1.0
            actions.append({"key": f"service_{area_key}", "area": area_key, "label": area["label"],
                            "cost_mi": round(base_cost * scale * index, 1), "cost_basis": cost_basis, "days": area["days"],
                            "summary": f"Entrega prevista em {area['days']} dias; o efeito aparece no indicador de {area['label'].lower()} ao concluir."})
        actions.append({"key": "public_report", "label": "Publicar prestação de contas", "cost_mi": 0.0, "days": 1,
                        "summary": "Expõe metas, execução financeira e resultados para fiscalização pública."})
        return actions
    return []


def _executive_population_basis(career: dict[str, Any]) -> dict[str, Any]:
    office = career.get("office")
    baseline = EXECUTIVE_BUDGET_BASELINES.get(office)
    if not baseline:
        return {"population": 0, "reference_population": 0, "scale": 1.0, "reference_year": None}
    if office == "prefeito":
        profile = career.get("municipality_profile")
        if not profile and career.get("municipality_id"):
            profile = get_municipality(career["municipality_id"])
        population = int((profile or {}).get("population_estimate", 0))
        reference_year = int((profile or {}).get("population_reference_year", 2026))
    else:
        population = get_state_population(career.get("state_code", ""))
        reference_year = 2026
    population = population or int(baseline["population"])
    return {
        "population": population,
        "reference_population": int(baseline["population"]),
        "scale": population / int(baseline["population"]),
        "reference_year": reference_year,
    }


def _executive_annual_budget_mi(career: dict[str, Any], price_index: float = 1.0) -> float:
    baseline = EXECUTIVE_BUDGET_BASELINES.get(career.get("office"))
    if not baseline:
        return 0.0
    basis = _executive_population_basis(career)
    return round(float(baseline["annual_budget_mi"]) * basis["scale"] * price_index, 1)


def _format_population_count(value: int) -> str:
    return f"{value:,}".replace(",", ".")


def _ensure_scaled_governance_budget(career: dict[str, Any], governance: dict[str, Any]) -> None:
    if career.get("office") not in EXECUTIVE_BUDGET_BASELINES or governance.get("budget_scale_version") == 1:
        return
    price_index = max(0.01, float(governance.get("budget_price_index", 1.0)))
    old_annual = float(governance.get("annual_budget_mi", EXECUTIVE_BUDGET_BASELINES[career["office"]]["annual_budget_mi"]))
    old_available = max(0.0, float(governance.get("budget_mi", old_annual)))
    remaining_share = min(1.0, old_available / old_annual) if old_annual > 0 else 1.0
    annual = _executive_annual_budget_mi(career, price_index)
    basis = _executive_population_basis(career)
    governance.update({
        "annual_budget_mi": annual,
        "budget_mi": round(annual * remaining_share, 1),
        "budget_population": basis["population"],
        "budget_population_reference_year": basis["reference_year"],
        "budget_scale_version": 1,
    })


def governance_territory_for(career: dict[str, Any]) -> dict[str, Any]:
    office = career.get("office")
    if office == "prefeito":
        return {"scope": "Município", "name": f"{career.get('municipality') or career.get('state_name', '')} · {career.get('state_code', '')}",
                "municipality_id": career.get("municipality_id")}
    if office == "governador":
        return {"scope": "Estado", "name": career.get("state_name") or career.get("state_code", "")}
    if office == "presidente":
        return {"scope": "País", "name": "Brasil"}
    return {"scope": "Representação legislativa", "name": career.get("municipality") or career.get("state_name") or "Brasil"}


def _presidential_investment_cap_mi(state: dict[str, Any]) -> float:
    """Presidential programs use the existing federal investment appropriation."""
    return max(0.0, float((state.get("budget") or {}).get("annual_investment_bi", 100.0)) * 1000)


def _presidential_investment_commitment_mi(governance: dict[str, Any]) -> float:
    committed = governance.get("investment_commitment_mi")
    if committed is not None:
        return max(0.0, float(committed))
    # Derive the committed amount when opening a save from the previous version.
    annual = float(governance.get("annual_budget_mi", governance.get("budget_mi", 0)))
    available = float(governance.get("budget_mi", annual))
    return max(0.0, annual - available)


def career_debate_prompt(career: dict[str, Any], issue: str) -> dict[str, str]:
    office = career.get("office")
    scope = "municipal" if office in {"vereador", "prefeito"} else "estadual" if office in {"deputado_estadual", "governador"} else "federal"
    question = DEBATE_QUESTIONS[issue]
    if office in LEGISLATIVE_OFFICES:
        question += " Como você transformará essa proposta em fiscalização, audiência ou votação na sua casa legislativa?"
    return {"moderator": "Bancada de debate simulada", "question": question, "scope": scope,
            "instruction": "Responda ao ponto, indique uma ação possível para o cargo e diga como o resultado será acompanhado."}


def perform_career_preparation(state: dict[str, Any], action_type: str) -> dict[str, Any]:
    """Prepare the campaign team before the official window, without voter-facing effects."""
    career = _campaign(state)
    if action_type not in PRE_CAMPAIGN_ACTIONS:
        raise ValueError("Escolha uma atividade de organização pré-campanha disponível.")
    today = date.fromisoformat(state["date"])
    campaign_start = date.fromisoformat(career["campaign_start"])
    if career.get("phase") != "pre_campaign" or today >= campaign_start:
        raise ValueError("A organização interna só está disponível antes da abertura oficial da campanha.")
    last_preparation = career.get("last_preparation_date")
    if last_preparation:
        wait = max(0, 30 - (today - date.fromisoformat(last_preparation)).days)
        if wait:
            raise ValueError(f"A próxima atividade de organização fica disponível em {wait} dia(s).")
    organization = float(career.get("pre_campaign_organization", 0))
    if organization >= MAX_PRE_CAMPAIGN_ORGANIZATION:
        raise ValueError("A equipe já atingiu o limite de organização pré-campanha desta partida.")
    action = PRE_CAMPAIGN_ACTIONS[action_type]
    cost = float(action["cost"])
    if float(career.get("campaign_fund_mi", 0)) < cost:
        raise ValueError("O fundo da candidatura não cobre esta atividade de organização.")
    gain = min(float(action["organization"]), MAX_PRE_CAMPAIGN_ORGANIZATION - organization)
    career["pre_campaign_organization"] = round(organization + gain, 2)
    career["campaign_fund_mi"] = round(float(career["campaign_fund_mi"]) - cost, 4)
    career["spent_mi"] = round(float(career.get("spent_mi", 0)) + cost, 4)
    career["last_preparation_date"] = state["date"]
    record = {
        "id": f"career-preparation-{state['date']}-{len(career.get('preparations', [])) + 1}",
        "date": state["date"], "type": action_type, "label": action["label"],
        "summary": action["summary"], "organization_gain": round(gain, 2),
        "organization_total": career["pre_campaign_organization"], "cost_mi": cost,
        "days_cost": int(action["days"]), "simulated": True,
    }
    career.setdefault("preparations", []).append(record)
    career["preparations"] = career["preparations"][-30:]
    return {
        "preparation": record,
        "organization": career["pre_campaign_organization"],
        "campaign_fund_mi": career["campaign_fund_mi"],
        "days_cost": record["days_cost"],
        "message": f"{action['label']} concluída. A organização da equipe aumentou {gain:.2f} pontos; a pesquisa não muda antes da campanha.",
    }


def perform_career_action(state: dict[str, Any], activity_type: str, issue: str, message: str,
                          conduct: str = "regular", municipality_id: str | None = None) -> dict[str, Any]:
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
    target_municipality = None
    if career["scope"] == "municipal":
        home_city_id = career.get("municipality_id")
        if municipality_id and municipality_id != home_city_id:
            raise ValueError("Campanha municipal só pode fazer atividades no município da candidatura.")
        target_municipality = get_municipality(home_city_id) if home_city_id else None
        if not target_municipality:
            raise ValueError("A cidade da candidatura não está vinculada ao catálogo do IBGE.")
    elif municipality_id:
        target_municipality = get_municipality(municipality_id)
        if not target_municipality:
            raise ValueError("Escolha uma cidade válida no catálogo do IBGE.")
        if career["office"] != "presidente" and target_municipality["state_code"] != career["state_code"]:
            raise ValueError("Essa atividade precisa ocorrer no estado da candidatura.")
    elif career["office"] != "presidente" and career.get("municipality_id"):
        target_municipality = get_municipality(career["municipality_id"])
    municipality_support = career.get("municipality_support", {})
    target_city_support_before = (
        float(municipality_support.get(
            target_municipality["ibge_code"],
            career.get("campaign_base_local_support", career.get("local_support", 45.0)),
        ))
        if target_municipality else None
    )
    travel_from = None
    travel_days = 0
    if activity_type in TRAVEL_ACTIVITIES and target_municipality:
        source_city_id = _campaign_team_location_id(career)
        travel_from = get_municipality(source_city_id) if source_city_id else None
        if travel_from and travel_from["ibge_code"] != target_municipality["ibge_code"]:
            if travel_from["state_code"] == target_municipality["state_code"] or travel_from["macroregion"] == target_municipality["macroregion"]:
                travel_days = 1
            else:
                travel_days = 2
    days_cost = activity["days"] + travel_days
    traits = (career.get("character") or {}).get("traits", [])
    action_cost = activity["cost"] * (.9 if "gestora" in traits else 1.0)
    if career["campaign_fund_mi"] < action_cost:
        raise ValueError("O saldo do fundo de campanha não cobre essa atividade.")
    score, rubric = _speech_score(issue, message)
    if "tecnica" in traits and rubric.get("proposta verificável", 0) > 0:
        score = min(100, score + 3)
        rubric["bônus de proposta técnica"] = 3
    debate_result = None
    if activity_type == "debate":
        prompt = career_debate_prompt(career, issue)
        normalized_message = _norm(message)
        topic_hits = sum(1 for term in ISSUES[issue]["terms"] if _norm(term) in normalized_message)
        directness = 4 if topic_hits and rubric.get("proposta verificável", 0) > 0 else 1 if topic_hits else -5
        score = max(0, min(100, score + directness))
        rubric["resposta direta à pergunta"] = directness
        from .difficulty import get_difficulty
        difficulty = get_difficulty(state.get("difficulty", "normal"))
        rng = random.Random(f"{career.get('seed', 1)}:{state['date']}:{issue}:{len(career['activities'])}:debate")
        opponent_score = round(max(35, min(90, 58 + (difficulty["opposition_pressure"] - 1) * 10 + rng.uniform(-9, 9))))
        if score >= opponent_score + 4:
            outcome, support_delta = "won", 0.6
            explanation = "A resposta foi mais clara e verificável que a réplica simulada."
        elif score <= opponent_score - 4:
            outcome, support_delta = "lost", -0.5
            explanation = "A réplica simulada foi mais convincente; a resposta perdeu apoio na pesquisa."
        else:
            outcome, support_delta = "tied", 0.1
            explanation = "As duas respostas tiveram desempenho próximo; o debate quase não alterou a pesquisa."
        debate_result = {
            "moderator": prompt["moderator"], "question": prompt["question"], "scope": prompt["scope"],
            "opponent_reply": DEBATE_REPLIES[issue], "player_score": score, "opponent_score": opponent_score, "outcome": outcome,
            "support_delta": support_delta, "explanation": explanation, "simulated": True,
        }
    quality = (score - 55) / 45
    reach = activity["reach"] + (.08 if "combativa" in traits else 0)
    city_reach_multiplier = 1.0
    electorate_share_of_state = None
    electorate_share_of_national = None
    if target_municipality:
        city_reach_multiplier = float(target_municipality["municipal_campaign_reach_multiplier"])
        electorate_share_of_state = target_municipality.get("electorate_share_of_state")
        electorate_share_of_national = target_municipality.get("electorate_share_of_national")
    reach *= city_reach_multiplier
    local_delta = max(-1.0, min(2.6, quality * reach + (0.45 if activity_type in {"comicio", "porta_a_porta"} else 0.1) + (.15 if "carismatica" in traits else 0)))
    # A city visit changes support locally. Its contribution to a larger
    # electorate is weighted by that city's share of the relevant electorate.
    # Municipal races are entirely inside their selected municipality.
    state_weight = 1.0 if not target_municipality or career["scope"] == "municipal" else float(electorate_share_of_state or 1.0)
    state_delta = local_delta * (0.4 if career["scope"] == "municipal" else 0.72) * state_weight
    national_delta = (
        local_delta * float(electorate_share_of_national)
        if target_municipality and electorate_share_of_national is not None
        else state_delta * 0.25
    )
    poll_territory_delta = (
        local_delta if career["scope"] == "municipal"
        else national_delta if career["office"] == "presidente" and target_municipality
        else state_delta
    )
    career["local_support"] = _clamp(career["local_support"] + local_delta)
    career["state_support"] = _clamp(career["state_support"] + state_delta)
    career["national_support"] = _clamp(career["national_support"] + national_delta)
    group_delta = quality * reach * 0.65 + (.15 if "conciliadora" in traits else 0) + (.2 if "comunitaria" in traits else 0)
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
    career["poll_support"] = round(_clamp(career["poll_support"] + poll_territory_delta * 0.42 + group_delta * 0.24), 2)
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
    if debate_result:
        career["poll_support"] = round(_clamp(career["poll_support"] + debate_result["support_delta"]), 2)
        career["local_support"] = _clamp(career["local_support"] + debate_result["support_delta"] * .55)
        career["state_support"] = _clamp(career["state_support"] + debate_result["support_delta"] * .3)
        for group in ISSUES[issue]["groups"]:
            career["group_support"][group] = _clamp(career["group_support"][group] + debate_result["support_delta"] * .35)
    target_city_support = None
    if target_municipality:
        city_delta = local_delta + conduct_delta + (debate_result["support_delta"] * .55 if debate_result else 0.0)
        target_city_support = round(_clamp(target_city_support_before + city_delta), 2)
        career.setdefault("municipality_support", {})[target_municipality["ibge_code"]] = target_city_support
    career["momentum"] = round(max(-10, min(10, career["momentum"] * 0.8 + quality * 1.1)), 2)
    career["fatigue"] = min(100, career["fatigue"] + (8 if activity_type in {"comicio", "porta_a_porta"} else 4) + (2 if "combativa" in traits else 0))
    career["campaign_fund_mi"] = round(career["campaign_fund_mi"] - action_cost, 4)
    career["spent_mi"] = round(career["spent_mi"] + action_cost, 4)
    career["last_action_date"] = state["date"]
    if activity_type in TRAVEL_ACTIVITIES and target_municipality:
        career["campaign_team_municipality_id"] = target_municipality["ibge_code"]
    campaign_promise = _record_campaign_promise(state, career, issue, message)
    record = {
        "id": f"career-{state['date']}-{len(career['activities']) + 1}", "date": state["date"], "type": activity_type,
        "label": activity["label"], "channel": activity["channel"], "issue": issue, "issue_label": ISSUES[issue]["label"],
        "municipality_id": target_municipality["ibge_code"] if target_municipality else None,
        "municipality_name": target_municipality["name"] if target_municipality else None,
        "municipality_state_code": target_municipality["state_code"] if target_municipality else None,
        "municipality_macroregion": target_municipality["macroregion"] if target_municipality else None,
        "municipality_support": target_city_support,
        "electorate_share_of_state": electorate_share_of_state,
        "electorate_share_of_national": electorate_share_of_national,
        "territorial_weight": round(state_weight, 8),
        "municipality_change": round(target_city_support - target_city_support_before, 2)
        if target_city_support is not None else None,
        "travel_days": travel_days,
        "travel_from_municipality_id": travel_from["ibge_code"] if travel_from else None,
        "travel_from_municipality_name": travel_from["name"] if travel_from else None,
        "city_reach_multiplier": city_reach_multiplier,
        "message": message.strip(), "score": score, "rubric": rubric, "local_change": round(local_delta + conduct_delta, 2),
        "state_change": round(state_delta + conduct_delta * .55, 2),
        "national_change": round(national_delta, 4),
        "poll_support": career["poll_support"], "cost_mi": round(action_cost, 4),
        "days_cost": days_cost, "affected_groups": [GROUPS[group] for group in ISSUES[issue]["groups"]], "simulated": True,
        "social_result": social_result, "debate": debate_result, "conduct": conduct_result,
        "campaign_promise_id": campaign_promise.get("id") if campaign_promise and campaign_promise.get("id") else None,
        "character_effects": [f"{trait}: efeito aplicado nesta ação" for trait in traits],
    }
    career["activities"].append(record)
    career["activities"] = career["activities"][-60:]
    result_message = "Ação registrada. A atividade consome o tempo indicado e a campanha continua sujeita ao voto simulado."
    if travel_days:
        result_message += f" O deslocamento de {travel_from['name']} até {target_municipality['name']} consumiu mais {travel_days} dia(s)."
    return {"activity": record, "campaign_promise": campaign_promise, "score": score, "rubric": rubric, "days_cost": days_cost, "poll_support": career["poll_support"],
            "local_support": career["local_support"], "state_support": career["state_support"], "campaign_fund_mi": career["campaign_fund_mi"],
            "municipality_support": target_city_support,
            "social_result": social_result, "debate": debate_result, "forecast": _forecast(career, score), "message": result_message}


def _forecast(career: dict[str, Any], score: int) -> list[dict[str, Any]]:
    quality = (score - 55) / 45
    return [
        {"horizon": "Agora", "effect": f"Pesquisa do candidato em {career['poll_support']:.1f}% e apoio local em {career['local_support']:.1f}%"},
        {"horizon": "Próximas semanas", "effect": "Repetição de mensagem fortalece reconhecimento; fadiga e desgaste reduzem retorno de novas atividades." if career["fatigue"] < 65 else "A equipe está cansada; alternar formato e tema protege o alcance."},
        {"horizon": "Eleição", "effect": "O resultado compara intenção de voto, organização, apoio partidário e uma margem aleatória definida pela dificuldade."},
    ]


# Lista aberta simulada (ajustável). Colegas de lista têm força sorteada em torno de LIST_MATE_MEAN;
# a força do jogador vem da campanha (apoio, organização, embalo, desgaste). Elege-se quem fica dentro
# das cadeiras da legenda. Calibrado para: sem campanha ≈ derrota provável; campanha consistente ≈ disputa
# aberta; campanha forte ≈ vitória provável.
LIST_MATE_MEAN = 31.0
LIST_MATE_SD = 11.0
LEGEND_VOTE_SHARE = 0.12       # parte dos votos da legenda que não vai a nenhum nome
TURNOUT_VALID = 0.70           # comparecimento × votos válidos (estimativa do jogo)


def _list_mate_names(rng: random.Random, count: int) -> list[str]:
    from .legislature import _FIRST, _LAST
    names: list[str] = []
    while len(names) < count:
        name = f"{rng.choice(_FIRST)} {rng.choice(_LAST)}"
        if name not in names:
            names.append(name)
    return names


def _proportional_electorate(career: dict[str, Any]) -> int | None:
    profile = get_municipality(career.get("municipality_id")) if career.get("municipality_id") and career.get("office") == "vereador" else None
    if profile and profile.get("electorate_count"):
        return int(profile["electorate_count"])
    return None


def _proportional_result(career: dict[str, Any], rng: random.Random, strength: float) -> dict[str, Any]:
    """Lista aberta simulada: D'Hondt entre legendas fictícias e ordem interna por votos nominais."""
    seats = 13 if career["office"] == "vereador" else 24
    party_vote = max(3.0, min(60.0, 6.0 + strength * 0.32 + rng.uniform(-2.0, 3.0)))
    weights = [rng.gammavariate(1.7, 1.0) for _ in range(9)]
    total_weight = sum(weights) or 1.0
    votes = [party_vote, *[(100.0 - party_vote) * weight / total_weight for weight in weights]]
    allocations = [0] * len(votes)
    for _ in range(seats):
        winner = max(range(len(votes)), key=lambda index: votes[index] / (allocations[index] + 1))
        allocations[winner] += 1
    party_seats = allocations[0]

    mates = [max(5.0, rng.gauss(LIST_MATE_MEAN, LIST_MATE_SD)) for _ in range(seats)]
    names = _list_mate_names(rng, seats)
    entries = [{"name": career.get("candidate_name") or "Você", "score": max(5.0, float(strength)), "is_player": True},
               *[{"name": names[i], "score": mates[i], "is_player": False} for i in range(seats)]]
    cube_total = sum(e["score"] ** 3 for e in entries)
    nominal = party_vote * (1 - LEGEND_VOTE_SHARE)
    electorate = _proportional_electorate(career)
    valid_votes = int(electorate * TURNOUT_VALID) if electorate else None
    for e in entries:
        e["vote_share"] = round(nominal * e["score"] ** 3 / cube_total, 2)
        e["votes"] = int(valid_votes * e["vote_share"] / 100) if valid_votes else None
    entries.sort(key=lambda e: (e["score"], e["is_player"]), reverse=True)
    for position, e in enumerate(entries, start=1):
        e["rank"] = position
        e["elected"] = position <= party_seats
        e["simulated"] = True
    for e in entries:
        e.pop("score")
    player = next(e for e in entries if e["is_player"])
    last_in = entries[party_seats - 1] if party_seats else None
    first_out = entries[party_seats] if party_seats < len(entries) else None
    if player["elected"]:
        margin_share = round(player["vote_share"] - (first_out["vote_share"] if first_out else 0.0), 2)
    else:
        margin_share = round((last_in["vote_share"] if last_in else party_vote) - player["vote_share"], 2)
    shown = max(party_seats + 2, 5)
    return {
        "system": "proporcional_simulado", "district_magnitude": seats,
        "party_vote_share": round(party_vote, 1), "party_seats": party_seats,
        "candidate_list_rank": player["rank"], "candidate_vote_share": player["vote_share"], "candidate_votes": player["votes"],
        "list_size": len(entries), "elected": player["elected"], "margin_share": margin_share,
        "margin_votes": int(valid_votes * margin_share / 100) if valid_votes else None,
        "valid_votes": valid_votes, "list": entries[:shown] + ([player] if player["rank"] > shown else []),
        "method": "Lista aberta simulada: cadeiras por D'Hondt entre legendas fictícias; dentro da legenda, elegem-se os mais votados. "
                  "Nomes, votos e comparecimento são estimativas do jogo.",
        "simulated": True,
    }


def resolve_career_election(state: dict[str, Any], election_day: date) -> str:
    career = state.get("career") or {}
    phase = career.get("phase")
    if not career.get("mode") or phase not in {"campaign", "runoff_campaign", "runoff_observer"}:
        return ""
    from .difficulty import get_difficulty

    difficulty = get_difficulty(state.get("difficulty", "normal"))
    round_number = 2 if phase in {"runoff_campaign", "runoff_observer"} else 1
    seed = f"{career.get('seed', state.get('campaign_seed', 203001))}:career-election:{career['office']}:{election_day.isoformat()}:round-{round_number}"
    conduct_result = (
        career.get("conduct_review") or {"attempts": 0, "detected": 0, "reviewed": False, "vote_penalty": 0.0}
        if phase in {"runoff_campaign", "runoff_observer"}
        else settle_campaign_conduct(state, career, seed)
    )
    rng = random.Random(seed)
    _ensure_opponents(career)
    organization = min(8.0, len(career["activities"]) * 0.55 + float(career.get("pre_campaign_organization", 0)))
    fatigue_penalty = max(0, career["fatigue"] - 60) * 0.035
    volatility = 2.5 * difficulty.get("economic_volatility", 1)
    opposition_pressure = difficulty.get("opposition_pressure", 1)
    opposition_drag = (opposition_pressure - 1) * 2.0
    electoral_result: dict[str, Any] | None = None
    candidate_results: list[dict[str, Any]] = []
    runoff_results: list[dict[str, Any]] = []

    if career["office"] in {"vereador", "deputado_estadual", "deputado_federal"}:
        strength = _clamp(career["poll_support"] * 0.78 + organization + career["momentum"] * 0.35
                          - fatigue_penalty - conduct_result["vote_penalty"] - opposition_drag
                          + rng.uniform(-volatility, volatility) * opposition_pressure)
        electoral_result = _proportional_result(career, rng, strength)
        won = bool(electoral_result["elected"])
        vote_share = electoral_result["candidate_vote_share"]   # voto nominal do jogador (% dos válidos)
        opposition_share = 100 - electoral_result["party_vote_share"]
    elif round_number == 1:
        vote_share = round(_clamp(career["poll_support"] * 0.82 + organization + career["momentum"] * 0.35
                                  - fatigue_penalty - conduct_result["vote_penalty"] - opposition_drag
                                  + rng.uniform(-volatility, volatility) * opposition_pressure), 1)
        opposition_results = _opponent_supports(career, vote_share)
        candidate_results = [{
            "id": "player", "name": career["candidate_name"], "party": career["party"],
            "ideology": career["ideology"], "support": vote_share, "is_player": True, "simulated": True,
        }, *[{
            "id": item["id"], "name": item["name"], "party": item["party"],
            "ideology": item["ideology"], "issue_focus": item["issue_focus"],
            "issue_focus_label": item["issue_focus_label"], "support": item["support"],
            "is_player": False, "simulated": True,
        } for item in opposition_results]]
        candidate_results.sort(key=lambda item: item["support"], reverse=True)
        winner = candidate_results[0]
        if _requires_second_round(career) and float(winner["support"]) <= 50.0:
            runoff_date = election_day + timedelta(days=28)
            finalists = candidate_results[:2]
            career["first_round_date"] = election_day.isoformat()
            career["first_round_poll_support"] = float(career["poll_support"])
            career["first_round_vote_share"] = next(item["support"] for item in candidate_results if item["is_player"])
            career["first_round_results"] = candidate_results
            career["candidate_results"] = candidate_results
            career["runoff_finalists"] = finalists
            career["runoff_results"] = []
            career["runoff_date"] = runoff_date.isoformat()
            career["election_date"] = runoff_date.isoformat()
            career["phase"] = "runoff_campaign" if any(item["is_player"] for item in finalists) else "runoff_observer"
            career["electoral_result"] = {
                "system": "majoritario_simulado", "runoff": True, "round": 1,
                "first_round": candidate_results, "finalists": finalists,
                "runoff_date": runoff_date.isoformat(), "simulated": True,
            }
            career["conduct_review"] = conduct_result
            career["vote_share"] = career["first_round_vote_share"]
            career["opponent_share"] = max(item["support"] for item in candidate_results if not item["is_player"])
            career["result"] = None
            state["career_status"] = "runoff_campaign" if career["phase"] == "runoff_campaign" else "runoff_observer"
            state["office_status"] = "incumbent_caretaker" if career.get("office_start") else "opposition_candidate"
            state.setdefault("simulated_news", []).insert(0, {
                "id": f"career-first-round-{election_day.isoformat()}", "date": election_day.isoformat(),
                "title": "Apura\u00e7\u00e3o simulada: segundo turno", "region": career["state_name"],
                "description": f"{finalists[0]['name']} e {finalists[1]['name']} avan\u00e7aram para a rodada final em {runoff_date.strftime('%d/%m/%Y')}.",
                "simulated": True,
            })
            state["simulated_news"] = state["simulated_news"][:20]
            if career["phase"] == "runoff_campaign":
                return f"Primeiro turno simulado: voc\u00ea avan\u00e7ou para o segundo turno em {runoff_date.strftime('%d/%m/%Y')}. A campanha continua e o mandato segue em funcionamento."
            return f"Primeiro turno simulado: voc\u00ea n\u00e3o avan\u00e7ou. {finalists[0]['name']} e {finalists[1]['name']} disputar\u00e3o o segundo turno em {runoff_date.strftime('%d/%m/%Y')}; a transi\u00e7\u00e3o ainda n\u00e3o terminou."
        won = bool(winner["is_player"])
        opposition_share = max((item["support"] for item in candidate_results if not item["is_player"]), default=0.0)
        career["winning_candidate_name"] = winner["name"]
        electoral_result = {
            "system": "majoritario_simulado", "runoff": False, "round": 1,
            "candidates": candidate_results, "winner_name": winner["name"], "simulated": True,
        }
    else:
        runoff_results = _runoff_vote_results(career)
        if len(runoff_results) != 2:
            return ""
        runoff_noise = rng.uniform(-volatility, volatility) * opposition_pressure
        player_result = next((item for item in runoff_results if item.get("is_player")), None)
        if player_result:
            player_support = round(max(0.0, min(100.0, player_result["support"] - conduct_result["vote_penalty"] + runoff_noise)), 1)
            other_result = next(item for item in runoff_results if not item.get("is_player"))
            runoff_results = sorted([
                {**player_result, "support": player_support},
                {**other_result, "support": round(100 - player_support, 1)},
            ], key=lambda item: item["support"], reverse=True)
        else:
            first_support = round(max(0.0, min(100.0, runoff_results[0]["support"] + runoff_noise)), 1)
            runoff_results = [
                {**runoff_results[0], "support": first_support},
                {**runoff_results[1], "support": round(100 - first_support, 1)},
            ]
        winner = runoff_results[0]
        won = bool(winner.get("is_player"))
        career["winning_candidate_name"] = winner["name"]
        career["runoff_results"] = runoff_results
        candidate_results = career.get("first_round_results", [])
        electoral_result = {
            "system": "majoritario_simulado", "runoff": True, "round": 2,
            "first_round": candidate_results, "final_round": runoff_results,
            "winner_name": winner["name"], "runoff_date": election_day.isoformat(), "simulated": True,
        }
        if player_result:
            vote_share = player_support
            opposition_share = next(item["support"] for item in runoff_results if not item.get("is_player"))
        else:
            vote_share = float(career.get("first_round_vote_share", 0))
            opposition_share = max((item["support"] for item in candidate_results if not item.get("is_player")), default=0.0)

    career["candidate_results"] = candidate_results
    career["vote_share"] = round(vote_share, 1)
    career["opponent_share"] = round(opposition_share, 1)
    career["conduct_review"] = conduct_result
    career["electoral_result"] = electoral_result or {"system": "majoritario_simulado", "runoff": False}
    career["result"] = "won" if won else "lost"
    has_current_mandate = bool(career.get("office_start"))
    career["phase"] = "transition" if won else "outgoing" if has_current_mandate else "opposition"
    state["office_status"] = "elected_transition" if won else "incumbent_caretaker" if has_current_mandate else "opposition_candidate"
    state["career_status"] = "transition" if won else "outgoing" if has_current_mandate else "opposition"
    transition = _inauguration_date(career["office"], election_day)
    career["inauguration_date"] = transition.isoformat()
    career["transition_date"] = transition.isoformat()
    state.setdefault("simulated_news", []).insert(0, {
        "id": f"career-election-{election_day.isoformat()}", "date": election_day.isoformat(),
        "title": f"Resultado eleitoral simulado: {career['office_label']}", "region": career["state_name"],
        "description": f"{career['candidate_name']} recebeu {vote_share:.2f}% dos votos simulados. {'Eleito(a)' if won else 'Não eleito(a)'}.",
        "simulated": True,
    })
    state["simulated_news"] = state["simulated_news"][:20]
    if runoff_results:
        electoral_summary = f"{career.get('winning_candidate_name')} venceu a rodada final simulada entre duas candidaturas."
    elif candidate_results:
        electoral_summary = f"{career.get('winning_candidate_name')} liderou a apura\u00e7\u00e3o simulada com m\u00faltiplas candidaturas."
    else:
        electoral_summary = ""
        if electoral_result:
            er = electoral_result
            electoral_summary = (f"Sua legenda fez {er['party_vote_share']:.1f}% e obteve {er['party_seats']} de {er['district_magnitude']} cadeiras simuladas; "
                                 f"você ficou em {er['candidate_list_rank']}º entre {er['list_size']} nomes da lista. ")
            if er["elected"]:
                electoral_summary += f"Folga sobre o primeiro não eleito: {er['margin_share']:.2f} ponto(s)."
            elif er["party_seats"]:
                electoral_summary += f"Faltaram {er['margin_share']:.2f} ponto(s) para alcançar o último eleito da legenda."
            else:
                electoral_summary += "A legenda não atingiu votos para uma cadeira."
    term_end_label = date.fromisoformat(career["term_end"]).strftime("%d/%m/%Y") if career.get("term_end") else "o fim do mandato atual"
    if won and has_current_mandate:
        continuity = f"A nova posse simulada est\u00e1 marcada para {transition.strftime('%d/%m/%Y')}; o mandato atual segue at\u00e9 {term_end_label}."
    elif won:
        continuity = f"A posse simulada est\u00e1 marcada para {transition.strftime('%d/%m/%Y')}."
    elif has_current_mandate:
        continuity = f"Voc\u00ea permanece no cargo at\u00e9 {term_end_label} e depois segue na oposi\u00e7\u00e3o."
    elif runoff_results and not any(item.get("is_player") for item in runoff_results):
        continuity = "Voc\u00ea segue na oposi\u00e7\u00e3o; a carreira pode continuar com outra disputa ou uma indica\u00e7\u00e3o pol\u00edtica."
    else:
        continuity = "Voc\u00ea segue na oposi\u00e7\u00e3o; a carreira pode continuar com outra disputa ou uma indica\u00e7\u00e3o pol\u00edtica."
    if runoff_results and not any(item.get("is_player") for item in runoff_results):
        return f"Resultado final simulado: sua candidatura ficou fora do segundo turno com {vote_share:.1f}% no primeiro turno. {electoral_summary} {continuity}"
    result_label = "vit\u00f3ria" if won else "derrota"
    if runoff_results:
        return f"Resultado eleitoral simulado no segundo turno: {result_label} com {vote_share:.1f}% dos votos. {electoral_summary} {continuity}"
    proportional = bool(electoral_result and electoral_result.get("system") == "proporcional_simulado")
    share_label = f"{vote_share:.2f}% dos votos válidos em seu nome" if proportional else f"{vote_share:.1f}% dos votos"
    return f"Resultado eleitoral simulado: {result_label} com {share_label}. {electoral_summary} {continuity}"


def advance_career(state: dict[str, Any], before: date, after: date) -> list[str]:
    career = state.get("career") or {}
    if not career.get("mode"):
        return []
    messages: list[str] = []
    election_day = date.fromisoformat(career["election_date"])
    campaign_start = date.fromisoformat(career.get("campaign_start", (election_day - timedelta(days=90)).isoformat()))
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
        _record_public_poll(state, career, campaign_start)
        messages.append("A janela eleitoral da reta final abriu. A avaliação do mandato e as novas atividades passam a afetar a tentativa de reeleição.")
    if career["phase"] in {"campaign", "runoff_campaign"}:
        for poll_date in _campaign_poll_schedule(career):
            if before < poll_date <= after:
                _record_public_poll(state, career, poll_date)
    if career["phase"] in {"campaign", "runoff_campaign", "runoff_observer"} and before < election_day <= after:
        messages.append(resolve_career_election(state, election_day))
    transition_date = career.get("transition_date")
    if career["phase"] == "transition" and transition_date and before < date.fromisoformat(transition_date) <= after:
        career["phase"] = "office"
        career["office_start"] = transition_date
        career["term_end"] = (date.fromisoformat(transition_date).replace(year=date.fromisoformat(transition_date).year + career["term_years"]) - timedelta(days=1)).isoformat()
        next_election_year = date.fromisoformat(transition_date).year + career["term_years"] - 1
        reelection_day = _regular_election_day(career["office"], date.fromisoformat(career["election_date"]), next_election_year)
        career["election_date"] = reelection_day.isoformat()
        annual_budget = (_presidential_investment_cap_mi(state) if career["office"] == "presidente"
                         else _executive_annual_budget_mi(career) if career["office"] in EXECUTIVE_BUDGET_BASELINES else 0.0)
        population_basis = _executive_population_basis(career)
        career["governance"] = {"budget_mi": annual_budget, "annual_budget_mi": annual_budget,
                                "budget_year": date.fromisoformat(transition_date).year, "trust": 50.0, "delivery": 0.0,
                                "budget_price_index": 1.0, "political_capital": 50.0, "actions": [], "pipeline": [],
                                "budget_source": "federal_investment" if career["office"] == "presidente" else "career_reserve",
                                "budget_scale_version": 1 if career["office"] in EXECUTIVE_BUDGET_BASELINES else 0,
                                "budget_population": population_basis["population"] if career["office"] in EXECUTIVE_BUDGET_BASELINES else None,
                                "budget_population_reference_year": population_basis["reference_year"] if career["office"] in EXECUTIVE_BUDGET_BASELINES else None,
                                "investment_commitment_mi": 0.0,
                                "outcomes": {"education": 50.0, "health": 50.0, "security": 50.0, "mobility": 50.0,
                                             "sanitation": 50.0, "infrastructure": 50.0, "employment": 50.0}}
        _activate_campaign_promises(state, career, date.fromisoformat(transition_date), reset_existing=True)
        state["office_status"] = "elected_official"
        state["career_status"] = "in_office"
        state["term_start"] = transition_date
        state["term"] = 1
        address = ensure_communications_state(state)["inauguration"]
        address.update({"required": True, "delivered": False, "legacy_save": False,
                        "date": None, "text": "", "score": None, "rubric": {}})
        territory = career.get("municipality") or ("Brasil" if career.get("office") == "presidente" else career.get("state_name", career.get("state_code", "")))
        messages.append(f"Posse simulada: você assume o cargo de {career['office_label']} em {territory}.")
        messages.append("O primeiro pronunciamento de posse precisa ser registrado antes de novas decisões.")
    if career["phase"] == "office" and after.isoformat() > career.get("term_end", "9999-12-31"):
        career["phase"] = "term_complete"
        state["office_status"] = "former_official"
        state["career_status"] = "term_complete"
        messages.append("O mandato simulado terminou. Seu histórico e as próximas opções de carreira continuam disponíveis.")
    if career["phase"] == "outgoing" and after.isoformat() > career.get("term_end", "9999-12-31"):
        career["phase"] = "opposition"
        state["office_status"] = "former_official"
        state["career_status"] = "opposition"
        messages.append("A transição simulada foi concluída. Você deixa o cargo e segue na oposição; o histórico do mandato permanece salvo.")
    governance = career.get("governance") or {}
    _ensure_scaled_governance_budget(career, governance)
    if is_career_governing(career, after) and governance:
        budget_year = int(governance.get("budget_year", before.year))
        if after.year > budget_year:
            price_index = float(governance.get("budget_price_index", 1.0))
            inflation_pct = float(state.get("metrics", {}).get("inflation", 4.5))
            annual_price_change = min(0.25, max(0.0, inflation_pct / 100.0))
            for _ in range(after.year - budget_year):
                price_index *= 1.0 + annual_price_change
            governance["budget_price_index"] = round(price_index, 4)
            if career["office"] == "presidente":
                annual = _presidential_investment_cap_mi(state)
                governance["investment_commitment_mi"] = 0.0
                governance["budget_source"] = "federal_investment"
                governance["budget_mi"] = round(annual, 1)
                governance["annual_budget_mi"] = round(annual, 1)
            elif career["office"] in EXECUTIVE_BUDGET_BASELINES:
                annual = _executive_annual_budget_mi(career, price_index)
                basis = _executive_population_basis(career)
                governance["budget_mi"] = annual
                governance["annual_budget_mi"] = annual
                governance["budget_population"] = basis["population"]
                governance["budget_population_reference_year"] = basis["reference_year"]
            else:
                annual = float(governance.get("annual_budget_mi", 0))
                governance["budget_mi"] = round(min(annual, float(governance.get("budget_mi", 0)) + annual), 1)
            governance["budget_scale_version"] = 1 if career["office"] in EXECUTIVE_BUDGET_BASELINES else governance.get("budget_scale_version", 0)
            governance["budget_year"] = after.year
            if career["office"] in LEGISLATIVE_OFFICES:
                governance["political_capital"] = min(100.0, float(governance.get("political_capital", 50)) + 25.0)
            reserve_name = "a dotação federal de investimentos" if career["office"] == "presidente" else "a reserva anual simulada"
            messages.append(f"O novo ano começou: {reserve_name} foi atualizada e o custo-base dos programas subiu {annual_price_change * 100:.1f}% pela inflação do cenário.")
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
                if item.get("area") == "employment" and career.get("office") == "presidente":
                    metrics = state.setdefault("metrics", {})
                    metrics["unemployment"] = round(max(2.0, float(metrics.get("unemployment", 7.2)) - .25), 2)
                    metrics["gdp_growth"] = round(float(metrics.get("gdp_growth", 2.1)) + .1, 2)
                governance["delivery"] = float(governance.get("delivery", 0)) + 1
                governance["trust"] = _clamp(governance.get("trust", 50) + 1.5)
                item["status"] = "delivered"
                item["completed_at"] = due.isoformat()
                governance.setdefault("actions", []).append(item)
                territory = item.get("territory") or governance_territory_for(career)["name"]
                messages.append(f"Entrega simulada concluída: {item['title']} em {territory}. O indicador de serviço sobe para {outcomes[area['outcome']]:.1f}.")
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
    messages.extend(_review_campaign_promises(state, career, before, after))
    return [message for message in messages if message]


def _clamp(value: float) -> float:
    return round(max(0.0, min(100.0, float(value))), 2)
