"""Empresas públicas e estratégicas: relação do governo, saúde da empresa, visitas, reuniões e política de controle.

Catálogo de instituições e empresas reais, só com atributos qualitativos (setor, sede, tipo de controle). Os
índices de saúde e de relação com o governo são do jogo (0 a 100), não dados financeiros. Compra e venda continuam
nas competências (privatizar, estatizar), que exigem lei; aqui ficam as decisões de gestão que o Executivo pode tomar.
"""
from __future__ import annotations

import hashlib
from datetime import date, timedelta
from typing import Any

from . import consequences, ledger

CATALOG: dict[str, dict[str, Any]] = {
    "petrobras": {"name": "Petrobras", "sector": "Petróleo e gás", "hq": "RJ", "level": "federal", "control": "mista, controle da União", "strategic": True,
                  "note": "O monopólio da União sobre petróleo (CF art. 177) é exercido por contratação; a venda do controle exige lei.", "privatize_key": "Petrobras"},
    "bb": {"name": "Banco do Brasil", "sector": "Banco", "hq": "DF", "level": "federal", "control": "mista, controle da União", "strategic": True,
           "note": "Banco múltiplo com papel no crédito rural e na política de crédito.", "privatize_key": "Banco do Brasil"},
    "caixa": {"name": "Caixa Econômica Federal", "sector": "Banco", "hq": "DF", "level": "federal", "control": "empresa pública", "strategic": True,
              "note": "Operador de habitação, FGTS e programas sociais.", "privatize_key": "Caixa Econômica Federal"},
    "bndes": {"name": "BNDES", "sector": "Banco de desenvolvimento", "hq": "RJ", "level": "federal", "control": "empresa pública", "strategic": True,
              "note": "Financia investimento e infraestrutura.", "privatize_key": "BNDES"},
    "correios": {"name": "Correios", "sector": "Logística postal", "hq": "DF", "level": "federal", "control": "empresa pública", "strategic": False,
                 "note": "Serviço postal é competência da União (CF art. 21, X).", "privatize_key": "Correios"},
    "eletronuclear": {"name": "Eletronuclear", "sector": "Energia nuclear", "hq": "RJ", "level": "federal", "control": "subsidiária estatal", "strategic": True,
                      "note": "Atividade nuclear só para fins pacíficos e com aprovação do Congresso (CF art. 21, XXIII).", "privatize_key": "Eletronuclear"},
    "eletrobras": {"name": "Eletrobras", "sector": "Energia elétrica", "hq": "RJ", "level": "federal", "control": "privada, União minoritária", "strategic": True,
                   "note": "Privatizada em 2022; a União mantém participação e limite de voto.", "privatize_key": None},
    "embraer": {"name": "Embraer", "sector": "Aeronáutica", "hq": "SP", "level": "federal", "control": "privada, ação de classe especial da União", "strategic": True,
                "note": "A União tem poder de veto sobre decisões estratégicas (ação de classe especial).", "privatize_key": None},
    "vale": {"name": "Vale", "sector": "Mineração", "hq": "RJ", "level": "federal", "control": "privada", "strategic": True,
             "note": "Privatizada em 1997; minerais são bens da União e lavra depende de concessão (CF art. 176).", "privatize_key": None},
    "telebras": {"name": "Telebras", "sector": "Telecomunicações", "hq": "DF", "level": "federal", "control": "mista, controle da União", "strategic": False,
                 "note": "Opera infraestrutura de conectividade do governo.", "privatize_key": None},
    "cemig": {"name": "Cemig", "sector": "Energia elétrica", "hq": "MG", "level": "estadual", "control": "mista, controle do estado de Minas Gerais", "strategic": False,
              "note": "Privatizar estatal estadual exige lei da Assembleia (e, em MG, referendo previsto na constituição estadual).", "privatize_key": None},
    "sabesp": {"name": "Sabesp", "sector": "Saneamento", "hq": "SP", "level": "estadual", "control": "mista", "strategic": False,
               "note": "Saneamento é regulado pelo Marco Legal (Lei 14.026/2020).", "privatize_key": None},
    "bnb": {"name": "Banco do Nordeste", "sector": "Banco de desenvolvimento", "hq": "CE", "level": "federal", "control": "mista, controle da União", "strategic": False,
                  "note": "Opera o crédito de fomento regional e o Fundo Constitucional do Nordeste.", "privatize_key": None},
    "basa": {"name": "Banco da Amazônia", "sector": "Banco de desenvolvimento", "hq": "PA", "level": "federal", "control": "mista, controle da União", "strategic": False,
                  "note": "Opera o crédito de fomento regional e o Fundo Constitucional do Norte.", "privatize_key": None},
    "finep": {"name": "Finep", "sector": "Fomento à inovação", "hq": "RJ", "level": "federal", "control": "empresa pública", "strategic": False,
                  "note": "Financia ciência, tecnologia e inovação nas empresas.", "privatize_key": None},
    "serpro": {"name": "Serpro", "sector": "Tecnologia da informação", "hq": "DF", "level": "federal", "control": "empresa pública", "strategic": False,
                  "note": "Presta serviços de tecnologia e dados ao governo federal.", "privatize_key": None},
    "dataprev": {"name": "Dataprev", "sector": "Tecnologia da informação", "hq": "DF", "level": "federal", "control": "empresa pública", "strategic": False,
                  "note": "Processa os dados da Previdência e de benefícios sociais.", "privatize_key": None},
    "ebc": {"name": "EBC", "sector": "Comunicação pública", "hq": "DF", "level": "federal", "control": "empresa pública", "strategic": False,
                  "note": "Gestora da comunicação pública federal; a independência editorial é debate recorrente.", "privatize_key": None},
    "embrapa": {"name": "Embrapa", "sector": "Pesquisa agropecuária", "hq": "DF", "level": "federal", "control": "empresa pública", "strategic": True,
                  "note": "Pesquisa agropecuária que sustenta a produtividade do campo.", "privatize_key": None},
    "ppsa": {"name": "Pré-Sal Petróleo (PPSA)", "sector": "Petróleo e gás", "hq": "RJ", "level": "federal", "control": "empresa pública", "strategic": True,
                  "note": "Representa a União nos contratos de partilha do pré-sal e comercializa o petróleo da União.", "privatize_key": None},
    "transpetro": {"name": "Transpetro", "sector": "Transporte de petróleo", "hq": "RJ", "level": "federal", "control": "subsidiária estatal", "strategic": False,
                  "note": "Subsidiária da Petrobras para dutos e navegação de petróleo e derivados.", "privatize_key": None},
    "itaipu": {"name": "Itaipu Binacional", "sector": "Energia elétrica", "hq": "PR", "level": "federal", "control": "binacional, Brasil e Paraguai", "strategic": True,
                  "note": "Usina binacional regida por tratado; tarifa e dívida dependem de negociação diplomática.", "privatize_key": None},
    "infraero": {"name": "Infraero", "sector": "Aeroportos", "hq": "DF", "level": "federal", "control": "empresa pública", "strategic": False,
                  "note": "Administra aeroportos que ficaram fora das concessões.", "privatize_key": None},
    "itau": {"name": "Itaú Unibanco", "sector": "Banco", "hq": "SP", "level": "federal", "control": "privada", "strategic": True,
                  "note": "Maior banco privado do país; sensível a juros, crédito e regulação do Banco Central.", "privatize_key": None},
    "bradesco": {"name": "Bradesco", "sector": "Banco", "hq": "SP", "level": "federal", "control": "privada", "strategic": True,
                  "note": "Grande banco privado com forte presença no varejo e em seguros.", "privatize_key": None},
    "santander": {"name": "Santander Brasil", "sector": "Banco", "hq": "SP", "level": "federal", "control": "privada", "strategic": False,
                  "note": "Banco privado, subsidiária de grupo espanhol.", "privatize_key": None},
    "btg": {"name": "BTG Pactual", "sector": "Banco de investimento", "hq": "SP", "level": "federal", "control": "privada", "strategic": False,
                  "note": "Banco de investimento e gestão de recursos; reage ao mercado de capitais.", "privatize_key": None},
    "b3": {"name": "B3", "sector": "Bolsa de valores", "hq": "SP", "level": "federal", "control": "privada", "strategic": True,
                  "note": "Bolsa brasileira; infraestrutura do mercado de capitais, supervisionada pela CVM.", "privatize_key": None},
    "nubank": {"name": "Nubank", "sector": "Banco digital", "hq": "SP", "level": "federal", "control": "privada", "strategic": False,
                  "note": "Maior banco digital do país; símbolo da concorrência no sistema financeiro.", "privatize_key": None},
    "ambev": {"name": "Ambev", "sector": "Bebidas", "hq": "SP", "level": "federal", "control": "privada", "strategic": False,
                  "note": "Cervejas e refrigerantes; alta carga de impostos sobre consumo.", "privatize_key": None},
    "jbs": {"name": "JBS", "sector": "Alimentos", "hq": "SP", "level": "federal", "control": "privada", "strategic": False,
                  "note": "Uma das maiores processadoras de carne do mundo; exportadora.", "privatize_key": None},
    "brf": {"name": "BRF", "sector": "Alimentos", "hq": "SP", "level": "federal", "control": "privada", "strategic": False,
                  "note": "Aves e suínos processados; exportadora e sensível a barreiras sanitárias.", "privatize_key": None},
    "marfrig": {"name": "Marfrig", "sector": "Alimentos", "hq": "SP", "level": "federal", "control": "privada", "strategic": False,
                  "note": "Carne bovina; exposta ao desmatamento e à regulação ambiental.", "privatize_key": None},
    "suzano": {"name": "Suzano", "sector": "Papel e celulose", "hq": "SP", "level": "federal", "control": "privada", "strategic": False,
                  "note": "Líder mundial em celulose de eucalipto; exportadora.", "privatize_key": None},
    "klabin": {"name": "Klabin", "sector": "Papel e celulose", "hq": "SP", "level": "federal", "control": "privada", "strategic": False,
                  "note": "Papéis e embalagens; plantio florestal.", "privatize_key": None},
    "gerdau": {"name": "Gerdau", "sector": "Siderurgia", "hq": "RS", "level": "federal", "control": "privada", "strategic": False,
                  "note": "Aço longo e reciclagem de sucata; sensível a importações de aço.", "privatize_key": None},
    "csn": {"name": "CSN", "sector": "Siderurgia e mineração", "hq": "RJ", "level": "federal", "control": "privada", "strategic": False,
                  "note": "Aço, minério de ferro e cimento.", "privatize_key": None},
    "usiminas": {"name": "Usiminas", "sector": "Siderurgia", "hq": "MG", "level": "federal", "control": "privada", "strategic": False,
                  "note": "Aços planos para automóveis e construção.", "privatize_key": None},
    "braskem": {"name": "Braskem", "sector": "Petroquímica", "hq": "BA", "level": "federal", "control": "privada, Petrobras acionista", "strategic": True,
                  "note": "Maior petroquímica das Américas; tem a Petrobras como acionista.", "privatize_key": None},
    "weg": {"name": "WEG", "sector": "Equipamentos elétricos", "hq": "SC", "level": "federal", "control": "privada", "strategic": False,
                  "note": "Motores e equipamentos elétricos; exportadora industrial.", "privatize_key": None},
    "natura": {"name": "Natura &Co", "sector": "Cosméticos", "hq": "SP", "level": "federal", "control": "privada", "strategic": False,
                  "note": "Cosméticos e venda direta; marca ligada à Amazônia.", "privatize_key": None},
    "magalu": {"name": "Magazine Luiza", "sector": "Varejo", "hq": "SP", "level": "federal", "control": "privada", "strategic": False,
                  "note": "Varejo físico e digital; sensível ao crédito e ao consumo.", "privatize_key": None},
    "mercadolivre": {"name": "Mercado Livre", "sector": "Comércio eletrônico", "hq": "SP", "level": "federal", "control": "privada", "strategic": False,
                  "note": "Plataforma de comércio eletrônico e pagamentos na América Latina.", "privatize_key": None},
    "carrefour": {"name": "Carrefour Brasil", "sector": "Varejo alimentar", "hq": "SP", "level": "federal", "control": "privada", "strategic": False,
                  "note": "Supermercados; sensível à inflação de alimentos.", "privatize_key": None},
    "pao": {"name": "Grupo Pão de Açúcar", "sector": "Varejo alimentar", "hq": "SP", "level": "federal", "control": "privada", "strategic": False,
                  "note": "Rede de supermercados; sensível ao poder de compra.", "privatize_key": None},
    "rumo": {"name": "Rumo", "sector": "Ferrovias e logística", "hq": "SP", "level": "federal", "control": "privada", "strategic": False,
                  "note": "Ferrovias para escoar grãos; operadora de concessões ferroviárias.", "privatize_key": None},
    "ccr": {"name": "CCR", "sector": "Concessões de infraestrutura", "hq": "SP", "level": "federal", "control": "privada", "strategic": False,
                  "note": "Rodovias, mobilidade urbana e aeroportos em concessão.", "privatize_key": None},
    "localiza": {"name": "Localiza", "sector": "Aluguel de veículos", "hq": "MG", "level": "federal", "control": "privada", "strategic": False,
                  "note": "Locação de carros; sensível a juros e ao preço de veículos.", "privatize_key": None},
    "azul": {"name": "Azul", "sector": "Aviação", "hq": "SP", "level": "federal", "control": "privada", "strategic": False,
                  "note": "Companhia aérea; sensível ao câmbio e ao querosene de aviação.", "privatize_key": None},
    "latam": {"name": "LATAM Brasil", "sector": "Aviação", "hq": "SP", "level": "federal", "control": "privada", "strategic": False,
                  "note": "Companhia aérea de grupo latino-americano; sensível ao câmbio.", "privatize_key": None},
    "gol": {"name": "Gol", "sector": "Aviação", "hq": "SP", "level": "federal", "control": "privada", "strategic": False,
                  "note": "Companhia aérea de baixo custo; sensível ao câmbio.", "privatize_key": None},
    "vivo": {"name": "Vivo (Telefônica Brasil)", "sector": "Telecomunicações", "hq": "SP", "level": "federal", "control": "privada", "strategic": False,
                  "note": "Maior operadora móvel do país; regulada pela Anatel.", "privatize_key": None},
    "claro": {"name": "Claro", "sector": "Telecomunicações", "hq": "SP", "level": "federal", "control": "privada", "strategic": False,
                  "note": "Operadora de telefonia, banda larga e TV; regulada pela Anatel.", "privatize_key": None},
    "tim": {"name": "TIM Brasil", "sector": "Telecomunicações", "hq": "RJ", "level": "federal", "control": "privada", "strategic": False,
                  "note": "Operadora móvel; regulada pela Anatel.", "privatize_key": None},
    "raizen": {"name": "Raízen", "sector": "Energia e combustíveis", "hq": "SP", "level": "federal", "control": "privada", "strategic": True,
                  "note": "Etanol, açúcar e distribuição de combustíveis.", "privatize_key": None},
    "vibra": {"name": "Vibra Energia", "sector": "Distribuição de combustíveis", "hq": "RJ", "level": "federal", "control": "privada", "strategic": False,
                  "note": "Distribuidora de combustíveis, ex-BR Distribuidora (privatizada em 2019).", "privatize_key": None},
    "ultrapar": {"name": "Ultrapar (Ipiranga)", "sector": "Distribuição de combustíveis", "hq": "SP", "level": "federal", "control": "privada", "strategic": False,
                  "note": "Combustíveis, gás e químicos.", "privatize_key": None},
    "cosan": {"name": "Cosan", "sector": "Energia e logística", "hq": "SP", "level": "federal", "control": "privada", "strategic": False,
                  "note": "Holding de energia, combustíveis, ferrovia e terras.", "privatize_key": None},
    "stellantis": {"name": "Stellantis Brasil", "sector": "Automóveis", "hq": "MG", "level": "federal", "control": "privada", "strategic": False,
                  "note": "Montadora com fábricas em MG e PE; depende de incentivos e crédito.", "privatize_key": None},
    "vw": {"name": "Volkswagen do Brasil", "sector": "Automóveis", "hq": "SP", "level": "federal", "control": "privada", "strategic": False,
                  "note": "Montadora com fábricas em SP e PR; depende de incentivos e crédito.", "privatize_key": None},
    "gm": {"name": "General Motors do Brasil", "sector": "Automóveis", "hq": "SP", "level": "federal", "control": "privada", "strategic": False,
                  "note": "Montadora com fábricas em SP e RS; depende de incentivos e crédito.", "privatize_key": None},
    "copel": {"name": "Copel", "sector": "Energia elétrica", "hq": "PR", "level": "estadual", "control": "privada, Paraná acionista", "strategic": False,
                  "note": "Privatizada em 2023; o estado do Paraná mantém ação de classe especial.", "privatize_key": None},
    "copasa": {"name": "Copasa", "sector": "Saneamento", "hq": "MG", "level": "estadual", "control": "mista, controle do estado de Minas Gerais", "strategic": False,
                  "note": "Saneamento mineiro; regulado pelo Marco Legal.", "privatize_key": None},
    "sanepar": {"name": "Sanepar", "sector": "Saneamento", "hq": "PR", "level": "estadual", "control": "mista, controle do estado do Paraná", "strategic": False,
                  "note": "Saneamento paranaense; regulado pelo Marco Legal.", "privatize_key": None},
    "banrisul": {"name": "Banrisul", "sector": "Banco", "hq": "RS", "level": "estadual", "control": "mista, controle do estado do Rio Grande do Sul", "strategic": False,
                  "note": "Banco estadual gaúcho com crédito ao servidor e ao agro.", "privatize_key": None},
    "brb": {"name": "BRB", "sector": "Banco", "hq": "DF", "level": "estadual", "control": "mista, controle do Distrito Federal", "strategic": False,
                  "note": "Banco do Distrito Federal, com folha dos servidores e crédito.", "privatize_key": None},
    "banestes": {"name": "Banestes", "sector": "Banco", "hq": "ES", "level": "estadual", "control": "mista, controle do estado do Espírito Santo", "strategic": False,
                  "note": "Banco estadual capixaba.", "privatize_key": None},
    "celesc": {"name": "Celesc", "sector": "Energia elétrica", "hq": "SC", "level": "estadual", "control": "mista, controle do estado de Santa Catarina", "strategic": False,
                  "note": "Distribuidora de energia catarinense.", "privatize_key": None},
    "metrosp": {"name": "Metrô de São Paulo", "sector": "Transporte metroviário", "hq": "SP", "level": "estadual", "control": "empresa pública estadual", "strategic": False,
                  "note": "Rede metroviária paulista; parte das linhas passou à concessão.", "privatize_key": None},
    "cptm": {"name": "Trens metropolitanos (CPTM)", "sector": "Transporte ferroviário urbano", "hq": "SP", "level": "estadual", "control": "empresa pública estadual", "strategic": False,
                  "note": "Linhas de trens metropolitanos paulistas; várias linhas foram concedidas.", "privatize_key": None},
    "cedae": {"name": "Cedae", "sector": "Saneamento", "hq": "RJ", "level": "estadual", "control": "mista, controle do estado do Rio de Janeiro", "strategic": False,
                  "note": "Saneamento fluminense; parte dos serviços foi concedida em 2021.", "privatize_key": None},
}

# Participação da União (% do capital com voto, estimativa do jogo) e valor de mercado de referência (R$ bi, fictício).
# Só empresas federais com participação da União entram na compra e venda de ações.
STAKES: dict[str, tuple[float, float]] = {
    "petrobras": (53.0, 450.0), "bb": (55.0, 140.0), "caixa": (100.0, 190.0), "bndes": (100.0, 160.0), "correios": (100.0, 20.0),
    "eletronuclear": (100.0, 25.0), "eletrobras": (10.0, 100.0), "telebras": (100.0, 3.0),
    "bnb": (93.0, 20.0), "basa": (95.0, 5.0), "finep": (100.0, 15.0), "serpro": (100.0, 8.0), "dataprev": (100.0, 3.0), "ppsa": (100.0, 2.0), "transpetro": (100.0, 12.0),
}
CONTROL_LINE = 50.0
STAKE_OPTIONS = ["5 pontos percentuais", "10 pontos percentuais"]
STAKE_COOLDOWN = 120

ACTIONS = {
    "visit": {"label": "Visitar a empresa", "who": "all", "cooldown": 45, "text": "Agenda pública na sede ou em uma unidade; melhora a relação e pode render anúncio de investimento.", "options": []},
    "meeting": {"label": "Reunião com a diretoria", "who": "all", "cooldown": 30, "text": "Negocie uma prioridade com a diretoria.",
                "options": ["Pedir investimento", "Pedir contenção de preços", "Pedir mais empregos locais"]},
    "dividends": {"label": "Política de dividendos", "who": "controlled", "cooldown": 90, "text": "Quanto do lucro volta ao Tesouro e quanto fica na empresa.",
                  "options": ["Pedir mais dividendos", "Reter lucros para investir"]},
    "prices": {"label": "Política de preços", "who": "petrobras", "cooldown": 60, "text": "Segurar ou alinhar os preços de combustíveis ao mercado.",
               "options": ["Segurar preços", "Alinhar ao mercado"]},
    "sell_stake": {"label": "Vender participação", "who": "stake", "cooldown": STAKE_COOLDOWN, "text": "Vende ações no mercado e usa a receita para abater a dívida. Não cruza a linha do controle (50%): isso exige lei.", "options": STAKE_OPTIONS},
    "buy_stake": {"label": "Comprar participação", "who": "stake", "cooldown": STAKE_COOLDOWN, "text": "Compra ações com recursos do Tesouro (aumenta a dívida). Não cruza a linha do controle (50%): isso exige lei.", "options": STAKE_OPTIONS},
    "leadership": {"label": "Escolher o comando", "who": "controlled", "cooldown": 180, "text": "Trocar a presidência: técnico independente ou aliado político.",
                   "options": ["Nome técnico independente", "Aliado político"]},
}
# (opção) -> efeitos {relation, health, metric deltas}
EFFECTS: dict[str, dict[str, float]] = {
    "visit": {"relation": 6.0, "approval": 0.3},
    "Pedir investimento": {"relation": 2.0, "health": -1.0, "gdp_growth": 0.02},
    "Pedir contenção de preços": {"relation": -4.0, "health": -3.0, "inflation": -0.08, "approval": 0.2},
    "Pedir mais empregos locais": {"relation": -2.0, "health": -1.0, "unemployment": -0.03, "approval": 0.2},
    "Pedir mais dividendos": {"relation": -5.0, "health": -3.0, "primary_balance": 0.03},
    "Reter lucros para investir": {"relation": 3.0, "health": 3.0, "primary_balance": -0.02},
    "Segurar preços": {"relation": -6.0, "health": -6.0, "inflation": -0.12, "approval": 0.6},
    "Alinhar ao mercado": {"relation": 4.0, "health": 4.0, "inflation": 0.1, "approval": -0.5},
    "Nome técnico independente": {"relation": 4.0, "health": 3.0, "integrity": 0.5, "congress_support": -0.4},
    "Aliado político": {"relation": 1.0, "health": -2.0, "integrity": -0.8, "congress_support": 0.6},
}


def _roll(seed: str) -> float:
    return int(hashlib.sha256(seed.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF


def ensure(state: dict[str, Any]) -> dict[str, Any]:
    comp = state.setdefault("company_state", {})
    for key, c in CATALOG.items():
        comp.setdefault(key, {"control": c["control"], "health": 60.0 + 20 * _roll(f"{state.get('campaign_seed', 1)}:{key}:h"), "relation": 50.0, "last": {}, "last_crisis": None})
        if key in STAKES and "stake" not in comp[key]:
            comp[key]["stake"] = STAKES[key][0]
    from .powers import structure
    for key, c in CATALOG.items():
        if c.get("privatize_key") and structure(state)["companies"].get(c["privatize_key"]) == "privada" and not comp[key]["control"].startswith("privada"):
            comp[key]["control"] = "privada (vendida pelo governo)"
    return comp


def _office(state: dict[str, Any]) -> tuple[str, bool]:
    from .career import is_career_governing
    career = state.get("career") or {}
    if career.get("mode"):
        return str(career.get("office")), bool(is_career_governing(career, date.fromisoformat(state["date"])))
    return "presidente", state.get("office_status", "incumbent") == "incumbent"


def _controlled(entry: dict[str, Any]) -> bool:
    return not entry["control"].startswith("privada")


def _scope_ok(state: dict[str, Any], key: str) -> str | None:
    office, governing = _office(state)
    c = CATALOG[key]
    if not governing:
        return "Disponível quando você estiver no exercício do cargo."
    if office == "presidente":
        return None
    if office == "governador" and c["level"] == "estadual" and c["hq"] == (state.get("career") or {}).get("state_code"):
        return None
    return "Esta empresa não está sob a competência do seu cargo."


def _value_bi(key: str, e: dict[str, Any]) -> float:
    return round(STAKES[key][1] * (0.7 + 0.6 * float(e["health"]) / 100), 1)


def _stake_check(key: str, e: dict[str, Any], action: str, option: str | None) -> tuple[str | None, float]:
    """Motivo de bloqueio (ou None) e quantos pontos percentuais a operação move."""
    if key not in STAKES:
        return "A União não tem participação negociável nesta empresa.", 0.0
    pp = 10.0 if option == STAKE_OPTIONS[1] else 5.0
    stake = float(e["stake"])
    controlled = stake >= CONTROL_LINE
    if action == "sell_stake":
        if stake - pp < 0:
            return "A União não tem essa participação.", pp
        if controlled and stake - pp < CONTROL_LINE:
            return "Vender abaixo de 50% é perder o controle: isso exige lei (aba Competências).", pp
    else:
        if stake + pp > 100:
            return "Passaria de 100% do capital.", pp
        if not controlled and stake + pp >= CONTROL_LINE:
            return "Comprar até o controle exige lei de estatização (aba Competências).", pp
    return None, pp


def overview(state: dict[str, Any]) -> dict[str, Any]:
    comp = ensure(state)
    today = date.fromisoformat(state["date"])
    items = []
    for key, c in CATALOG.items():
        e = comp[key]
        scope = _scope_ok(state, key)
        acts = []
        for akey, a in ACTIONS.items():
            reason = scope
            if not reason:
                if a["who"] == "controlled" and not _controlled(e):
                    reason = "A empresa não é controlada pelo governo."
                elif a["who"] == "stake" and key not in STAKES:
                    continue
                elif a["who"] == "petrobras" and key != "petrobras":
                    continue
                elif (last := e["last"].get(akey)) and (today - date.fromisoformat(last)).days < a["cooldown"]:
                    reason = f"Disponível em {a['cooldown'] - (today - date.fromisoformat(last)).days} dia(s)."
            if not reason and a["who"] == "stake":
                if c["level"] != "federal":
                    reason = "Só participações da União."
                elif akey == "buy_stake" and (_stake_check(key, e, akey, STAKE_OPTIONS[0])[0] is not None):
                    reason = _stake_check(key, e, akey, STAKE_OPTIONS[0])[0]
                elif akey == "sell_stake" and (_stake_check(key, e, akey, STAKE_OPTIONS[0])[0] is not None):
                    reason = _stake_check(key, e, akey, STAKE_OPTIONS[0])[0]
            acts.append({"key": akey, "label": a["label"], "text": a["text"], "options": a["options"], "available": reason is None, "reason": reason})
        items.append({"id": key, **{k: c[k] for k in ("name", "sector", "hq", "level", "strategic", "note")}, "control": e["control"], "controlled": _controlled(e),
                      "health": round(e["health"], 1), "relation": round(e["relation"], 1), "actions": acts,
                      "stake": e.get("stake"), "value_bi": _value_bi(key, e) if key in STAKES else None,
                      "can_privatize": bool(c.get("privatize_key")) and _controlled(e) and c["level"] == "federal", "privatize_key": c.get("privatize_key")})
    return {"companies": items, "note": "Saúde e relação são índices do jogo. A venda ou compra de empresas exige lei e fica na aba Competências."}


def act(state: dict[str, Any], key: str, action: str, option: str | None = None) -> dict[str, Any]:
    if key not in CATALOG or action not in ACTIONS:
        raise ValueError("Empresa ou ação desconhecida.")
    spec = ACTIONS[action]
    comp = ensure(state)
    e = comp[key]
    reason = _scope_ok(state, key)
    if reason:
        raise PermissionError(reason)
    if spec["who"] == "controlled" and not _controlled(e):
        raise PermissionError("A empresa não é controlada pelo governo.")
    if spec["who"] == "petrobras" and key != "petrobras":
        raise PermissionError("Ação exclusiva da Petrobras.")
    if spec["who"] == "stake":
        if CATALOG[key]["level"] != "federal":
            raise PermissionError("Só participações da União.")
        if option not in spec["options"]:
            raise ValueError("Escolha uma das opções.")
        blocked, _ = _stake_check(key, e, action, option)
        if blocked:
            raise PermissionError(blocked)
    today = date.fromisoformat(state["date"])
    last = e["last"].get(action)
    if last and (today - date.fromisoformat(last)).days < spec["cooldown"]:
        raise RuntimeError(f"Disponível em {spec['cooldown'] - (today - date.fromisoformat(last)).days} dia(s).")
    if spec["who"] == "stake":
        return _trade_stake(state, key, action, option, e)
    if spec["options"]:
        if option not in spec["options"]:
            raise ValueError("Escolha uma das opções.")
        eff = dict(EFFECTS[option])
    else:
        option, eff = None, dict(EFFECTS["visit"])
    relation, health = eff.pop("relation", 0.0), eff.pop("health", 0.0)
    e["relation"] = round(max(0.0, min(100.0, e["relation"] + relation)), 2)
    e["health"] = round(max(0.0, min(100.0, e["health"] + health)), 2)
    e["last"][action] = state["date"]
    _apply_metrics(state, eff)
    title = f"{CATALOG[key]['name']}: {spec['label'].lower()}" + (f" — {option}" if option else "")
    forecast = {**eff, "relação": relation, "saúde da empresa": health}
    entry = ledger.record(state, "empresa", title, forecast, forecast, status="feito")
    msg = None
    if action == "visit" and _roll(f"{state.get('campaign_seed', 1)}:{key}:{state['date']}:inv") < 0.35 + 0.004 * e["relation"]:
        _apply_metrics(state, {"gdp_growth": 0.02, "unemployment": -0.02})
        msg = f"{CATALOG[key]['name']} anunciou novo investimento após a visita (simulação)."
        consequences._post(consequences._book(state), state, {"id": f"emp-{key}-{state['date']}", "kind": "mercado", "headline": msg, "body": "O anúncio melhora a expectativa de emprego e atividade, na simulação.", "tone": "positivo", "action_id": f"empresa_{key}"})
    consequences.schedule(state, action_id=f"empresa_{action}", title=title, domain="empresas", effects=eff, ledger_id=entry["id"], local=_office(state)[0] != "presidente")
    return {"entry": entry, "company": next(c for c in overview(state)["companies"] if c["id"] == key), "announcement": msg}


def _trade_stake(state: dict[str, Any], key: str, action: str, option: str, e: dict[str, Any]) -> dict[str, Any]:
    from .fiscal import record_one_off_revenue, record_one_off_spending
    _, pp = _stake_check(key, e, action, option)
    value = _value_bi(key, e)
    sell = action == "sell_stake"
    price = round(value * pp / 100 * (0.97 if sell else 1.03), 2)  # deságio na venda, ágio na compra
    name = CATALOG[key]["name"]
    if sell:
        e["stake"] = round(float(e["stake"]) - pp, 2)
        record_one_off_revenue(state, price)
        eff = {"approval": -0.2 * pp / 5, "congress_support": -0.1 * pp / 5}
        relation, health = -3.0 * pp / 5, 1.0
    else:
        e["stake"] = round(float(e["stake"]) + pp, 2)
        record_one_off_spending(state, price)
        eff = {"approval": 0.1 * pp / 5}
        relation, health = 3.0 * pp / 5, 2.0
    e["relation"] = round(max(0.0, min(100.0, e["relation"] + relation)), 2)
    e["health"] = round(max(0.0, min(100.0, e["health"] + health)), 2)
    e["last"][action] = state["date"]
    _apply_metrics(state, eff)
    title = f"{name}: {'venda' if sell else 'compra'} de {pp:g} p.p. de participação (R$ {price:.1f} bi)"
    forecast = {**eff, "participação da União (p.p.)": -pp if sell else pp, "dívida (R$ bi)": -price if sell else price}
    entry = ledger.record(state, "empresa", title, forecast, forecast, status="feito")
    consequences.schedule(state, action_id=f"empresa_{action}", title=title, domain="empresas", effects=eff, ledger_id=entry["id"], local=False)
    return {"entry": entry, "company": next(c for c in overview(state)["companies"] if c["id"] == key),
            "announcement": f"{name}: União {'vendeu' if sell else 'comprou'} {pp:g} p.p. e ficou com {e['stake']:g}% (R$ {price:.1f} bi {'abatidos da dívida' if sell else 'somados à dívida'})."}


def _apply_metrics(state: dict[str, Any], eff: dict[str, float]) -> None:
    from .powers import METRIC_RANGES, _bump
    from .fiscal import record_policy_balance_delta
    career = state.get("career") or {}
    local = career.get("mode") and career.get("office") != "presidente"
    for k, v in eff.items():
        if local:
            if k == "approval":
                gov = career.setdefault("governance", {})
                gov["trust"] = round(max(0.0, min(100.0, float(gov.get("trust", 50)) + v)), 2)
        elif k == "primary_balance":
            record_policy_balance_delta(state, v)
        elif k in METRIC_RANGES:
            _bump(state, k, v)


def tick(state: dict[str, Any], before: date, after: date) -> list[str]:
    comp = ensure(state)
    msgs: list[str] = []
    growth = float(state.get("metrics", {}).get("gdp_growth", 2.0))
    month = after.isoformat()[:7]
    if state.setdefault("company_month", None) == month:
        return msgs
    state["company_month"] = month
    for key, e in comp.items():
        e["health"] = round(max(0.0, min(100.0, e["health"] + (growth - 2.0) * 0.4 + (60 - e["health"]) * 0.01)), 2)
        e["relation"] = round(e["relation"] + (50 - e["relation"]) * 0.02, 2)
        if e["health"] < 30 and _controlled(e) and (not e.get("last_crisis") or (after - date.fromisoformat(e["last_crisis"])).days > 180) and _scope_ok(state, key) is None:
            e["last_crisis"] = after.isoformat()
            name = CATALOG[key]["name"]
            consequences.open_crisis(state, crisis_id=f"emp-{key}-{month}", action_id=f"empresa_{key}", title=f"{name} em dificuldade financeira",
                                     text="Os resultados caíram e a diretoria pede apoio do controlador.", deadline_days=45, today=after,
                                     options=[{"id": "capitalizar", "label": "Capitalizar a empresa com recursos do Tesouro", "effects": {"primary_balance": -0.05, "approval": 0.2}},
                                              {"id": "reestruturar", "label": "Exigir plano de reestruturação", "effects": {"approval": -0.3, "integrity": 0.5}},
                                              {"id": "aguardar", "label": "Aguardar", "effects": {"approval": -1.0, "gdp_growth": -0.03}}])
            e["health"] = 35.0
            msgs.append(f"{name} entrou em dificuldade financeira. Responda na aba Imprensa.")
    return msgs
