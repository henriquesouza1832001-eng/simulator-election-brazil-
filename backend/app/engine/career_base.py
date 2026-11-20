"""Constantes, tabelas e datas compartilhadas pelo ciclo de carreira.

Parte do ciclo de carreira (antes tudo em career.py; ver career.py, que reexporta estes nomes).
"""
from __future__ import annotations


import unicodedata
from datetime import date, timedelta
from pathlib import Path
from typing import Any

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
    # Partidos reais; os adversários são candidaturas simuladas, sem pessoas reais.
    {"party": "PSB", "ideology": "Centro-esquerda", "issue_focus": "educacao"},
    {"party": "PT", "ideology": "Esquerda", "issue_focus": "economia"},
    {"party": "MDB", "ideology": "Centro", "issue_focus": "saude"},
    {"party": "PSD", "ideology": "Centro", "issue_focus": "mobilidade"},
    {"party": "PP", "ideology": "Centro-direita", "issue_focus": "mobilidade"},
    {"party": "PL", "ideology": "Direita", "issue_focus": "seguranca"},
    {"party": "NOVO", "ideology": "Direita", "issue_focus": "economia"},
    {"party": "PSOL", "ideology": "Esquerda", "issue_focus": "integridade"},
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


def _regular_election_day(office: str, after: date, minimum_year: int | None = None, force_year: int | None = None) -> date:
    """Return the next simulated Brazilian regular-election date for an office."""
    if force_year:  # eleição passada jogável: primeiro domingo de outubro do ano pedido
        october_first = date(force_year, 10, 1)
        return october_first + timedelta(days=(6 - october_first.weekday()) % 7)
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


def _clamp(value: float) -> float:
    return round(max(0.0, min(100.0, float(value))), 2)
