"""Catálogo de competências: o que cada cargo pode (e não pode) fazer, com base legal.

Os dados são um resumo editorial da Constituição de 1988 e de leis citadas, feito para
um jogo; não é parecer jurídico. Números de efeito são parâmetros de design, não
estimativas econômicas. Cada ação diz quem a inicia, por qual instrumento, o que
precisa de aprovação e o que a constituição veda.

approval:
  decreto    ato do Executivo, vale na hora
  mp         medida provisória: vale na hora, mas o Congresso precisa converter em lei
  pl         projeto de lei (maioria simples nas duas casas)
  plp        projeto de lei complementar (maioria absoluta)
  pec        emenda constitucional (3/5 em dois turnos nas duas casas)
  tratado    tratado: Congresso aprova (decreto legislativo) e o Presidente ratifica
  blocked    vedado por cláusula pétrea ou competência de outro poder
"""
from __future__ import annotations

from typing import Any

ROLES: dict[str, dict[str, Any]] = {
    "eleitor": {
        "label": "Eleitor(a)", "pode": ["Votar", "Acompanhar candidatos e o debate público", "Participar de consultas e audiências abertas"],
        "nao_pode": ["Propor ou votar leis", "Disputar cargo sem filiação partidária"],
        "base": "CF art. 14 (soberania popular, voto direto e secreto).",
    },
    "militante": {
        "label": "Militante", "pode": ["Panfletar, organizar atos e coletar assinaturas", "Participar de reuniões e do trabalho de campanha", "Ganhar reputação e contatos"],
        "nao_pode": ["Votar em convenção sem estar filiado", "Receber mandato ou verba pública", "Falar pelo partido"],
        "base": "CF art. 5º, XVII e XX (liberdade de associação) e art. 17 (autonomia partidária).",
    },
    "filiado": {
        "label": "Filiado(a)", "pode": ["Votar em convenções e eleições internas", "Disputar cargo no diretório", "Ser escolhido candidato"],
        "nao_pode": ["Ser candidato sem filiação deferida e domicílio na circunscrição", "Mudar de partido sem justa causa mantendo o mandato (quando eleito)"],
        "base": "CF art. 14, §3º, V (filiação partidária) e art. 17; Lei 9.096/1995.",
    },
    "quadro": {
        "label": "Dirigente partidário", "pode": ["Compor a executiva do diretório", "Articular alianças e a lista de candidatos", "Pedir apoio de padrinhos políticos"],
        "nao_pode": ["Decidir sozinho a candidatura (cabe à convenção)", "Usar o fundo partidário fora das regras"],
        "base": "Lei 9.096/1995 (Lei dos Partidos Políticos); Lei 9.504/1997 art. 8º (convenções).",
    },
    "vereador": {
        "label": "Vereador(a)", "pode": ["Legislar sobre assuntos de interesse local", "Votar o orçamento e o plano diretor do município", "Fiscalizar a prefeitura (pedidos de informação, CPI)", "Convocar secretários municipais"],
        "nao_pode": ["Executar obras ou contratar (cabe ao prefeito)", "Criar despesa sem iniciativa do Executivo nas matérias reservadas", "Legislar sobre direito civil, penal, trânsito ou segurança estadual"],
        "base": "CF art. 29 (Lei Orgânica) e art. 30, I e V; art. 31 (fiscalização).",
    },
    "prefeito": {
        "label": "Prefeito(a)", "pode": ["Executar o orçamento municipal e contratar obras e serviços", "Organizar transporte coletivo, limpeza e iluminação", "Conceder serviços públicos por licitação", "Sancionar ou vetar leis; nomear secretários"],
        "nao_pode": ["Legislar sozinho em matéria que exige lei", "Cuidar de segurança pública (só guarda municipal patrimonial)", "Criar tributos fora das competências municipais"],
        "base": "CF art. 29, 30 (IPTU, ISS), 144 §8º (guarda municipal) e 182 (política urbana).",
    },
    "deputado_estadual": {
        "label": "Deputado(a) estadual", "pode": ["Legislar sobre matérias estaduais e propor emendas à constituição estadual", "Votar o orçamento do estado", "Fiscalizar o governo estadual, convocar secretários e instalar CPI"],
        "nao_pode": ["Legislar sobre matérias privativas da União (direito penal, civil, comercial)", "Administrar o estado (cabe ao governador)"],
        "base": "CF art. 25 e 27 (Assembleias), art. 24 (competência concorrente) e art. 22 (privativa da União).",
    },
    "governador": {
        "label": "Governador(a)", "pode": ["Dirigir as polícias civil e militar do estado", "Executar o orçamento e as obras estaduais", "Conceder rodovias e serviços estaduais", "Fixar o ICMS dentro das regras do Confaz e do Senado", "Sancionar ou vetar leis; nomear secretários"],
        "nao_pode": ["Legislar sobre direito penal ou armas (privativa da União)", "Alterar a estrutura das polícias militares (exige PEC federal)", "Emitir moeda ou tratados"],
        "base": "CF art. 25, 125, 144 §6º, 155 e 175.",
    },
    "deputado_federal": {
        "label": "Deputado(a) federal", "pode": ["Propor leis, PECs e fiscalizar ministérios", "Votar o orçamento e propor emendas individuais", "Instalar CPI (1/3 dos membros)", "Convocar ministros e apresentar denúncia por crime de responsabilidade"],
        "nao_pode": ["Executar políticas (cabe ao Executivo)", "Criar despesa em projeto de iniciativa exclusiva do Presidente", "Julgar o Presidente (cabe ao Senado)"],
        "base": "CF art. 44 a 58, 61 (iniciativa), 166 (orçamento) e 50 (convocação de ministros).",
    },
    "senador": {
        "label": "Senador(a)", "pode": ["Aprovar autoridades (BC, STF, embaixadores, AGU)", "Julgar o Presidente em crime de responsabilidade", "Fixar alíquotas e limites de endividamento por resolução", "Representar o estado e propor leis"],
        "nao_pode": ["Iniciar projetos de iniciativa exclusiva do Presidente", "Executar políticas públicas"],
        "base": "CF art. 52 (competências privativas do Senado), 155 §2º IV e 49.",
    },
    "presidente": {
        "label": "Presidente(a)", "pode": ["Dirigir a administração federal e nomear ministros", "Editar decretos e medidas provisórias", "Propor leis, PECs e o orçamento; sancionar e vetar", "Conduzir a política externa e assinar tratados", "Comandar as Forças Armadas; nomear STF, BC e AGU com aprovação do Senado"],
        "nao_pode": ["Legislar sem o Congresso fora das medidas provisórias", "Mexer em cláusulas pétreas (federalismo, voto, separação de poderes, direitos individuais)", "Alterar sozinho o Banco Central, que tem autonomia por lei complementar", "Governar polícias estaduais (cabem aos governadores)", "Declarar guerra sem autorização do Congresso"],
        "base": "CF art. 84 (competência do Presidente), art. 62 (MP), art. 60 §4º (cláusulas pétreas) e art. 21.",
    },
}

# Atalho de construção: define uma ação em uma chamada.
_A: list[dict[str, Any]] = []


def _act(id: str, title: str, domain: str, who: list[str], instrument: str, approval: str, basis: str, summary: str,
         effects: dict[str, float] | None = None, *, sets: dict[str, Any] | None = None, cost_bi: float = 0.0,
         options: list[str] | None = None, requires: list[tuple[str, str, Any]] | None = None, blocked: str | None = None,
         precedent: str | None = None, axis: str = "other", popular_vote: bool = False) -> None:
    _A.append({"id": id, "title": title, "domain": domain, "who": who, "instrument": instrument, "approval": approval, "basis": basis,
               "summary": summary, "effects": effects or {}, "sets": sets or {}, "cost_bi": cost_bi, "options": options or [],
               "requires": requires or [], "blocked": blocked, "precedent": precedent, "axis": axis, "popular_vote": popular_vote})


P = ["presidente"]

# ---------------------------------------------------------------- Banco Central e moeda
_act("bc_autonomia_constitucional", "Constitucionalizar a autonomia do Banco Central", "banco", P, "PEC", "pec", "CF art. 164 e 60; LC 179/2021",
     "Hoje a autonomia vem de lei complementar. Uma PEC a tornaria mais difícil de desfazer.", {"institutional_trust": 2, "approval": -0.3},
     sets={"central_bank": "autonomo_constitucional"}, requires=[("structure.central_bank", "==", "autonomo_lei")], axis="economico",
     precedent="LC 179/2021 deu mandato fixo à diretoria do BC.")
_act("bc_revogar_autonomia", "Revogar a autonomia do Banco Central", "banco", P, "Projeto de Lei Complementar", "plp", "CF art. 164; LC 179/2021",
     "A diretoria deixa de ter mandato fixo e passa a responder ao governo. Mercados reagem mal; o governo ganha influência sobre juros.",
     {"institutional_trust": -4, "approval": -0.5, "gdp_growth": 0.05}, sets={"central_bank": "subordinado"},
     requires=[("structure.central_bank", "==", "autonomo_lei")], axis="economico", precedent="Antes de 2021 o Presidente podia demitir a diretoria do BC.")
_act("bc_restaurar_autonomia", "Restaurar a autonomia do Banco Central", "banco", P, "Projeto de Lei Complementar", "plp", "LC 179/2021",
     "Devolve mandatos fixos à diretoria e tira o BC do controle direto do governo.", {"institutional_trust": 3},
     sets={"central_bank": "autonomo_lei"}, requires=[("structure.central_bank", "==", "subordinado")], axis="economico")
_act("bc_meta_inflacao", "Mudar a meta de inflação", "banco", P, "Resolução do CMN", "decreto", "Decreto 3.088/1999; CF art. 164",
     "A meta é fixada pelo Conselho Monetário Nacional (Fazenda, Planejamento e presidente do BC), não pelo Presidente sozinho.",
     {"inflation": -0.1, "institutional_trust": 0.5}, options=["Meta de 3,0%", "Meta de 3,5%", "Meta de 4,0%"], axis="economico")
_act("bc_pressao_juros", "Criticar publicamente os juros", "banco", P, "Declaração pública", "decreto", "CF art. 164 (autonomia)",
     "O governo não manda no BC, mas pode pressionar. Em geral cobra credibilidade.", {"approval": 0.6, "institutional_trust": -1.2})
_act("bc_moeda_comum", "Criar moeda comum sul-americana", "banco", P, "Tratado + lei", "tratado", "CF art. 4º, parágrafo único; art. 21, VII; art. 22, VI; art. 49, I",
     "Exige negociação com outros países, aprovação do Congresso e mudança no sistema monetário. Efeitos de longo prazo.",
     {"institutional_trust": -1, "gdp_growth": -0.05, "approval": -0.8}, sets={"currency": "sul_americana"},
     requires=[("structure.currency", "==", "real")], precedent="Proposta de moeda comum (\"Sur\") discutida na região; nada aprovado.", axis="economico")
_act("bc_diretor", "Indicar presidente ou diretor do Banco Central", "banco", P, "Indicação com sabatina", "pl", "CF art. 84, XIV; art. 52, III, d",
     "O Presidente indica; o Senado aprova em voto secreto. Mandatos são fixos e não coincidem com o do Presidente.", {"institutional_trust": 0.5})

# ---------------------------------------------------------------- Empresas e patrimônio
_ESTATAIS = ["Petrobras", "Banco do Brasil", "Caixa Econômica Federal", "Correios", "BNDES", "Eletronuclear"]
_act("empresa_privatizar", "Privatizar empresa estatal", "empresas", P, "Projeto de Lei + PND", "pl", "CF art. 37, XIX e XX; art. 173; Lei 9.491/1997",
     "Vende o controle e gera caixa. A venda de empresa-mãe exige lei; setores de monopólio (art. 177) exigem mudança constitucional.",
     {"primary_balance": 0.12, "gdp_growth": 0.04, "approval": -1.2, "integrity": -0.5}, cost_bi=-40.0, options=_ESTATAIS, axis="fiscal_efficiency",
     precedent="Vale (1997) e Telebrás (1998) no governo FHC; Eletrobras (2022).")
_act("empresa_estatizar", "Estatizar ou comprar participação em empresa", "empresas", P, "Projeto de Lei", "pl", "CF art. 173; art. 37, XIX; art. 5º, XXIV",
     "A exploração direta pelo Estado só é permitida por segurança nacional ou relevante interesse coletivo, e exige lei. Custa caixa.",
     {"primary_balance": -0.15, "approval": 0.5, "institutional_trust": -0.8}, cost_bi=40.0,
     options=["Distribuidora de energia", "Banco regional", "Empresa de logística", "Eletrobras (retomar controle)"], axis="public_investment")
_act("empresa_criar", "Criar empresa pública", "empresas", P, "Projeto de Lei", "pl", "CF art. 37, XIX",
     "Só por lei específica. Cria estrutura nova e despesa de capital.", {"gdp_growth": 0.03, "primary_balance": -0.04}, cost_bi=8.0, axis="public_investment")
_act("empresa_monopolio_petroleo", "Mudar o monopólio do petróleo", "empresas", P, "PEC", "pec", "CF art. 177",
     "O monopólio da União sobre petróleo e gás só muda por emenda constitucional.", {"gdp_growth": 0.1, "approval": -0.8}, axis="economico",
     precedent="EC 9/1995 permitiu contratar empresas privadas para pesquisa e lavra.")
_act("empresa_itaipu", "Rever o acordo de Itaipu", "empresas", P, "Tratado com o Paraguai", "tratado", "CF art. 84, VIII; art. 49, I; Tratado de Itaipu (1973)",
     "A usina é binacional; mudanças de tarifa e partilha exigem acordo diplomático e aprovação do Congresso.", {"approval": 0.4, "institutional_trust": -0.4})

# ---------------------------------------------------------------- Infraestrutura
_act("infra_asfaltar", "Asfaltar rodovia federal", "infraestrutura", P, "Contratação de obra", "decreto", "CF art. 21, XII e XXI; Lei 14.133/2021",
     "Obras exigem licitação e prazo; o benefício aparece quando termina. Não se repete no mesmo trecho.",
     {"gdp_growth": 0.04, "approval": 0.7, "primary_balance": -0.03}, cost_bi=6.0, options=["BR-319 (AM-RO)", "BR-163 (MT-PA)", "BR-135 (MA)", "BR-040 (MG)"], axis="public_investment",
     precedent="Pavimentação da BR-163 no Pará avançou nos anos 2010.")
_act("infra_duplicar", "Duplicar rodovia federal", "infraestrutura", P, "Contratação de obra", "decreto", "CF art. 21, XXI; Lei 14.133/2021",
     "Custa mais que asfaltar, mas reduz acidentes e tempo de viagem.", {"gdp_growth": 0.06, "approval": 0.5, "primary_balance": -0.05}, cost_bi=12.0,
     options=["BR-101 (Nordeste)", "BR-116 (RS)", "BR-381 (MG)", "BR-153 (GO-TO)"], axis="public_investment", precedent="Duplicação da BR-101 Nordeste (PAC).")
_act("infra_conceder", "Conceder rodovia à iniciativa privada", "infraestrutura", P, "Leilão de concessão", "decreto", "CF art. 175; Lei 8.987/1995; ANTT",
     "A empresa vencedora duplica e cobra pedágio. Entra caixa no leilão; o usuário paga a tarifa.",
     {"gdp_growth": 0.05, "primary_balance": 0.03, "approval": -0.5}, cost_bi=-8.0, options=["BR-116/SP (Dutra)", "BR-364 (MT)", "BR-381 (MG)", "BR-040 (MG-GO)"], axis="business_formalization",
     precedent="Primeiras concessões federais em 1995 (Rio–Juiz de Fora e Ponte Rio–Niterói).")
_act("infra_vender_concessao", "Transferir ou vender concessão", "infraestrutura", P, "Relicitação", "decreto", "Lei 13.448/2017; CF art. 175",
     "Transferir a concessão a outra empresa depende da agência reguladora e do cumprimento do contrato.", {"primary_balance": 0.02, "approval": -0.2}, cost_bi=-3.0, axis="business_formalization")
_act("infra_ferrovia", "Construir ferrovia", "infraestrutura", P, "Concessão ou obra pública", "decreto", "CF art. 21, XII, d; Lei 14.133/2021",
     "Reduz custo de frete no longo prazo, com licenciamento ambiental e prazo longo.", {"gdp_growth": 0.07, "approval": 0.3, "primary_balance": -0.05}, cost_bi=20.0,
     options=["Ferrogrão (MT-PA)", "Transnordestina", "Ferrovia Norte-Sul (extensão)"], axis="public_investment")
_act("infra_porto", "Modernizar porto ou aeroporto", "infraestrutura", P, "Concessão ou arrendamento", "decreto", "CF art. 21, XII, e e f; Lei 12.815/2013",
     "Arrendar terminais atrai investimento privado e reduz custo logístico.", {"gdp_growth": 0.05, "approval": 0.2}, cost_bi=-2.0, options=["Porto de Santos", "Porto de Paranaguá", "Aeroporto de Viracopos"], axis="business_formalization")

# ---------------------------------------------------------------- Defesa, nuclear, forças armadas
_act("defesa_alcantara", "Abrir Alcântara a lançamentos comerciais", "defesa", P, "Acordo + decreto legislativo", "tratado", "CF art. 21, XXIII e art. 49, I",
     "O Centro de Lançamento de Alcântara (MA) pode receber empresas estrangeiras por acordo de salvaguardas tecnológicas.", {"gdp_growth": 0.03, "approval": -0.3, "institutional_trust": 0.3},
     sets={"alcantara": "comercial"}, requires=[("structure.alcantara", "==", "restrito")], precedent="Acordo de Salvaguardas Tecnológicas Brasil–EUA, aprovado em 2019.")
_act("defesa_nuclear_civil", "Ampliar o programa nuclear civil", "defesa", P, "Iniciativa do Executivo + aprovação", "pl", "CF art. 21, XXIII, a e c; art. 49, XIV",
     "Toda atividade nuclear é só para fins pacíficos e as iniciativas do Executivo precisam de aprovação do Congresso (Angra 3 etc.).",
     {"gdp_growth": 0.03, "primary_balance": -0.05, "approval": 0.1}, cost_bi=15.0, axis="public_investment")
_act("defesa_bomba", "Desenvolver armas nucleares", "defesa", P, "PEC + denúncia de tratados", "pec", "CF art. 21, XXIII, a (somente fins pacíficos); TNP; Tratado de Tlatelolco",
     "Exigiria emenda constitucional e sair de tratados internacionais. O custo diplomático e econômico seria enorme.",
     {"institutional_trust": -12, "gdp_growth": -0.15, "approval": -2, "military_loyalty": 3}, sets={"nuclear": "armas"},
     requires=[("structure.nuclear", "==", "civil")], precedent="O Brasil abandonou programa paralelo nos anos 1990 e aderiu ao TNP em 1998.", axis="security")
_act("defesa_guerra", "Declarar guerra", "defesa", P, "Autorização do Congresso", "pl", "CF art. 84, XIX; art. 49, II",
     "Só em caso de agressão estrangeira, autorizada ou referendada pelo Congresso.", {"approval": -3, "gdp_growth": -0.1, "institutional_trust": -2}, axis="security")
_act("defesa_glo", "Decretar GLO", "defesa", P, "Decreto", "decreto", "CF art. 142; LC 97/1999",
     "Garantia da Lei e da Ordem: as Forças Armadas atuam em segurança por tempo limitado, a pedido de governador ou por decisão do Presidente.",
     {"approval": 0.3, "military_loyalty": 1, "institutional_trust": -0.8}, axis="security")
_act("defesa_intervencao", "Decretar intervenção federal em um estado", "defesa", P, "Decreto + aprovação do Congresso", "decreto", "CF art. 34 e 36",
     "Só nos casos previstos; o Congresso precisa aprovar em 24 horas. Suspende parte da autonomia do estado.", {"approval": 0.2, "institutional_trust": -1.5, "governability": -1},
     precedent="Intervenção federal na segurança do Rio de Janeiro, 2018.", axis="security")
_act("defesa_estado_defesa", "Decretar estado de defesa ou de sítio", "defesa", P, "Decreto + aprovação do Congresso", "decreto", "CF art. 136 e 137",
     "Medida excepcional para calamidade ou grave instabilidade. O sítio exige autorização prévia do Congresso.", {"institutional_trust": -4, "approval": -1, "military_loyalty": 1})
_act("defesa_submarino", "Concluir submarino de propulsão nuclear", "defesa", P, "Programa de Defesa", "decreto", "CF art. 21, XXIII; Estratégia Nacional de Defesa",
     "Propulsão nuclear naval é permitida; arma nuclear, não.", {"military_loyalty": 2, "primary_balance": -0.04}, cost_bi=10.0)

# ---------------------------------------------------------------- Segurança, armas e polícia
_act("seg_armas_afrouxar", "Facilitar o porte e a posse de armas", "seguranca", P, "Decreto", "decreto", "CF art. 21, VI; Lei 10.826/2003 (Estatuto do Desarmamento)",
     "Pode regulamentar a lei por decreto, mas não revogá-la; o Congresso pode sustar.", {"approval": 0.2, "institutional_trust": -0.6, "integrity": -0.3}, sets={"guns": "facilitado"},
     requires=[("structure.guns", "!=", "facilitado")], precedent="Decretos 9.685 e 9.847, de 2019.", axis="security")
_act("seg_armas_restringir", "Restringir armas e munições", "seguranca", P, "Decreto", "decreto", "Lei 10.826/2003",
     "Endurece o controle de registro e compra.", {"approval": -0.1, "institutional_trust": 0.4}, sets={"guns": "restrito"},
     requires=[("structure.guns", "!=", "restrito")], precedent="Decretos de 2023 reforçaram o controle.", axis="security")
_act("seg_estatuto_alterar", "Mudar a lei do desarmamento", "seguranca", P, "Projeto de Lei", "pl", "CF art. 22, I e XXI",
     "Mudar a regra de fundo exige lei federal aprovada pelo Congresso.", {"approval": 0.1}, sets={"guns": "liberado_por_lei"}, axis="security")
_act("seg_desmilitarizar", "Desmilitarizar a polícia", "seguranca", P, "PEC", "pec", "CF art. 144, §§ 5º e 6º",
     "As polícias militares são forças auxiliares do Exército e subordinadas aos governadores. Unificar ou desmilitarizar exige emenda.",
     {"approval": -0.3, "institutional_trust": -0.5, "military_loyalty": -2}, sets={"police_model": "civil_unificada"},
     requires=[("structure.police_model", "==", "dual")], precedent="Propostas como a PEC 51/2013 não foram votadas.", axis="security")
_act("seg_fundo_seguranca", "Criar fundo federal de segurança pública", "seguranca", P, "Projeto de Lei", "pl", "CF art. 144; Lei 13.756/2018",
     "A segurança é dos estados; a União pode financiar e coordenar.", {"approval": 0.4, "primary_balance": -0.05}, cost_bi=6.0, axis="security")

# ---------------------------------------------------------------- Política externa e blocos
_act("ext_brics_entrar", "Aprofundar a participação no BRICS", "exterior", P, "Acordo", "decreto", "CF art. 4º, I, IX e parágrafo único; art. 84, VII",
     "O Brasil é membro fundador. Aprofundar cooperação financeira e comercial é ato de política externa.", {"gdp_growth": 0.03, "institutional_trust": -0.2},
     sets={"blocs.brics": True}, requires=[("structure.blocs.brics", "==", False)], axis="economico")
_act("ext_brics_sair", "Deixar o BRICS", "exterior", P, "Denúncia de acordo", "tratado", "CF art. 84, VII e VIII; art. 49, I",
     "Sair de acordo internacional é ato controverso; o Congresso costuma ser ouvido.", {"gdp_growth": -0.05, "institutional_trust": 0.2, "approval": -0.3},
     sets={"blocs.brics": False}, requires=[("structure.blocs.brics", "==", True)])
_act("ext_otan", "Pedir adesão à OTAN", "exterior", P, "Tratado", "tratado", "CF art. 4º (independência nacional, não intervenção); art. 84, VIII; art. 49, I",
     "A OTAN só aceita membros do Atlântico Norte pelo tratado original; seria preciso convite e aprovação do Congresso. O pedido tem pouca chance e custo político.",
     {"approval": -1, "institutional_trust": -0.8, "military_loyalty": 0.5}, sets={"blocs.otan": "parceiro_global"}, requires=[("structure.blocs.otan", "==", False)])
_act("ext_opep", "Aderir à cooperação OPEP+", "exterior", P, "Acordo", "tratado", "CF art. 84, VII; art. 49, I",
     "Participar de cartel de produtores afeta política de petróleo e imagem climática.", {"gdp_growth": 0.04, "approval": -0.3, "institutional_trust": -0.5},
     sets={"blocs.opep": True}, requires=[("structure.blocs.opep", "==", False)], axis="economico")
_act("ext_opep_sair", "Deixar a cooperação OPEP+", "exterior", P, "Denúncia de acordo", "decreto", "CF art. 84, VII",
     "Volta à posição de produtor independente.", {"approval": 0.1}, sets={"blocs.opep": False}, requires=[("structure.blocs.opep", "==", True)])
_act("ext_mercosul", "Rever o Mercosul", "exterior", P, "Negociação + tratado", "tratado", "CF art. 4º, parágrafo único; art. 84, VIII",
     "O bloco tem normas próprias; flexibilizar a tarifa externa comum exige consenso dos parceiros.", {"gdp_growth": 0.05, "approval": -0.2}, axis="economico")
_act("ext_acordo_comercial", "Fechar acordo comercial", "exterior", P, "Tratado", "tratado", "CF art. 84, VIII; art. 49, I",
     "Abre mercados e importa concorrência.", {"gdp_growth": 0.08, "approval": 0.1, "unemployment": 0.04}, options=["União Europeia–Mercosul", "China", "EUA", "Índia"], axis="economico")

# ---------------------------------------------------------------- Regime e instituições
_act("reg_forma_governo", "Mudar o sistema de governo (parlamentarismo)", "regime", P, "PEC + plebiscito", "pec", "CF art. 2º do ADCT (plebiscito de 1993); art. 60",
     "O povo escolheu o presidencialismo em 1993. Mudar exigiria emenda e nova consulta popular.", {"institutional_trust": -3, "governability": -5, "approval": -2},
     sets={"government_system": "parlamentarismo"}, requires=[("structure.government_system", "==", "presidencialismo")], popular_vote=True,
     precedent="Plebiscito de 21/04/1993: presidencialismo e república venceram.")
_act("reg_monarquia", "Restaurar a monarquia", "regime", P, "—", "blocked", "CF art. 1º (República); art. 2º do ADCT; art. 34, VII, a",
     "A forma republicana foi decidida em plebiscito. Não há caminho legal simples; qualquer tentativa vira crise institucional.",
     blocked="Não é possível por via ordinária. Só uma ruptura institucional tentaria isso.")
_act("reg_abolir_federacao", "Abolir a federação ou o voto direto", "regime", P, "—", "blocked", "CF art. 60, §4º, I e II (cláusulas pétreas)",
     "Propostas tendentes a abolir a forma federativa de Estado ou o voto direto, secreto, universal e periódico não podem sequer ser votadas.",
     blocked="Cláusula pétrea: nem a PEC pode tratar disso.")
_act("reg_reeleicao", "Rever a reeleição", "regime", P, "PEC", "pec", "CF art. 14, §5º (EC 16/1997)",
     "Pode acabar com a reeleição ou ampliar o mandato. Alterações valem a partir da próxima eleição.", {"institutional_trust": 0.8, "approval": 0.2}, sets={"reelection": "vedada"},
     requires=[("structure.reelection", "==", "permitida")], precedent="EC 16/1997 permitiu a reeleição no governo FHC.")
_act("reg_ministerios", "Reorganizar ministérios", "regime", P, "Decreto/Medida provisória", "decreto", "CF art. 84, VI; art. 88",
     "O Presidente pode reorganizar a administração federal, mas a criação de ministérios segue a lei.", {"governability": 1, "approval": -0.1})

# ---------------------------------------------------------------- Economia e tributos
_act("eco_reforma_tributaria", "Enviar reforma tributária", "economia", P, "PEC", "pec", "CF art. 153, 155 e 156; art. 60",
     "Muda impostos sobre consumo e renda. Costuma levar anos e dividir governadores e prefeitos.", {"gdp_growth": 0.12, "primary_balance": 0.05, "approval": -0.3}, axis="tax_change",
     precedent="EC 132/2023 reformou a tributação do consumo.")
_act("eco_teto", "Criar regra fiscal (teto de gastos)", "economia", P, "PEC", "pec", "CF art. 60; ADCT",
     "Limita o crescimento da despesa federal. Dá credibilidade e reduz margem de investimento.", {"primary_balance": 0.2, "institutional_trust": 1.5, "approval": -0.7},
     precedent="EC 95/2016 (teto de gastos).", axis="fiscal_efficiency")
_act("eco_previdencia", "Reformar a Previdência", "economia", P, "PEC", "pec", "CF art. 40 e 201",
     "Muda regras de aposentadoria; economiza no longo prazo e custa popularidade.", {"primary_balance": 0.18, "approval": -2.5, "institutional_trust": 0.8},
     precedent="EC 103/2019.", axis="fiscal_efficiency")
_act("eco_bolsa", "Ampliar programa de transferência de renda", "economia", P, "Projeto de Lei", "pl", "CF art. 6º, 203 e 204",
     "Reduz pobreza e aumenta o consumo; precisa de fonte de recursos.", {"approval": 1.0, "primary_balance": -0.12, "gdp_growth": 0.05}, cost_bi=20.0,
     precedent="Bolsa Família (2003) e Auxílio Brasil.", axis="social_policy")
_act("eco_salario_minimo", "Reajustar o salário mínimo acima da inflação", "economia", P, "Decreto/lei", "decreto", "CF art. 7º, IV; Lei 14.663/2023",
     "Aumenta a renda e as despesas previdenciárias.", {"approval": 0.8, "primary_balance": -0.06, "inflation": 0.05}, axis="social_policy")
_act("eco_desoneracao", "Desonerar setores", "economia", P, "Projeto de Lei", "pl", "CF art. 150, §6º; LRF art. 14",
     "Reduz impostos para estimular emprego; a LRF exige compensação.", {"gdp_growth": 0.06, "primary_balance": -0.1, "unemployment": -0.05}, axis="tax_change",
     precedent="Desonerações da folha (2011–2014 e depois).")
_act("eco_confisco", "Congelar preços", "economia", P, "Medida provisória", "mp", "CF art. 62, §1º, II (veda MP sobre bloqueio de poupança e ativos)",
     "Congelar preços pode ser tentado por MP; já o bloqueio de poupança e ativos financeiros não pode ser feito por MP. Costuma gerar escassez e perda de credibilidade.", {"inflation": -0.3, "gdp_growth": -0.12, "institutional_trust": -3, "approval": -1.5},
     precedent="Plano Collor (1990) e Plano Cruzado (1986).", axis="economico")
_act("eco_mp", "Editar medida provisória", "economia", P, "Medida provisória", "mp", "CF art. 62",
     "Vale por 60 dias, prorrogável por mais 60. Se o Congresso não converter, perde a eficácia.", {"approval": 0.4, "congress_support": -1.0}, axis="other")

ACTIONS: list[dict[str, Any]] = _A

# Cargos que não executam o mesmo catálogo: lista curta das principais iniciativas, só descritiva nesta versão.
OTHER_OFFICE_ACTIONS: dict[str, list[dict[str, str]]] = {
    "vereador": [
        {"title": "Propor lei municipal", "basis": "CF art. 30, I", "text": "Sobre assunto de interesse local. Iniciativa exclusiva do prefeito em orçamento e servidores."},
        {"title": "Emendar a lei orçamentária", "basis": "CF art. 165 e 166 (por simetria)", "text": "Pode remanejar despesas; não pode aumentar o total sem fonte."},
        {"title": "Instalar CPI municipal", "basis": "CF art. 58, §3º (por simetria)", "text": "Investiga fato determinado com apoio de um terço da Câmara."},
        {"title": "Convocar secretário municipal", "basis": "Lei Orgânica", "text": "Cobra informações sobre serviços da cidade."},
        {"title": "Julgar as contas do prefeito", "basis": "CF art. 31, §2º", "text": "O parecer do Tribunal de Contas só deixa de prevalecer por 2/3 da Câmara."},
        {"title": "Aprovar o plano diretor", "basis": "CF art. 182", "text": "Instrumento básico da política urbana em cidades com mais de 20 mil habitantes."},
    ],
    "prefeito": [
        {"title": "Asfaltar rua e tapar buracos", "basis": "CF art. 30, V", "text": "Serviço local executado com o orçamento municipal."},
        {"title": "Conceder transporte coletivo", "basis": "CF art. 30, V e art. 175", "text": "Licitação de linhas de ônibus; tarifa e contrato precisam constar."},
        {"title": "Reajustar o IPTU", "basis": "CF art. 156, I; art. 150", "text": "Por lei municipal; respeita anterioridade e limites."},
        {"title": "Criar guarda municipal", "basis": "CF art. 144, §8º", "text": "Protege bens, serviços e instalações; não faz policiamento ostensivo."},
        {"title": "Fazer parceria público-privada", "basis": "Lei 11.079/2004", "text": "Contrata a iniciativa privada para obra ou serviço de longo prazo."},
        {"title": "Vetar projeto da Câmara", "basis": "Lei Orgânica", "text": "Veto total ou parcial; a Câmara pode derrubar."},
    ],
    "deputado_estadual": [
        {"title": "Propor lei estadual", "basis": "CF art. 25 e 24", "text": "Competência concorrente com a União; respeita normas gerais federais."},
        {"title": "Instalar CPI na Assembleia", "basis": "CF art. 58, §3º (por simetria)", "text": "Investiga fato determinado no âmbito estadual."},
        {"title": "Convocar secretário de estado", "basis": "Constituição estadual", "text": "Cobra explicações sobre políticas estaduais."},
        {"title": "Sustar ato do governador", "basis": "CF art. 49, V (por simetria)", "text": "Quando exorbita do poder regulamentar."},
        {"title": "Propor emenda à constituição estadual", "basis": "CF art. 25", "text": "Exige um terço da Assembleia e três quintos para aprovar."},
    ],
    "governador": [
        {"title": "Comandar a polícia militar e a civil", "basis": "CF art. 144, §6º", "text": "As polícias estaduais respondem ao governador."},
        {"title": "Asfaltar e duplicar rodovia estadual", "basis": "CF art. 25 e 175", "text": "Obra estadual, com licitação."},
        {"title": "Conceder rodovia estadual", "basis": "CF art. 175", "text": "Pedágio e investimentos privados."},
        {"title": "Mudar alíquota do ICMS", "basis": "CF art. 155, II e §2º", "text": "Dentro do Confaz e dos limites do Senado."},
        {"title": "Privatizar estatal estadual", "basis": "CF art. 37, XIX; Constituição estadual", "text": "Exige lei da Assembleia."},
        {"title": "Pedir intervenção ou GLO", "basis": "CF art. 34 e 142", "text": "A União pode intervir ou enviar as Forças Armadas, mas a decisão é do Presidente."},
    ],
    "deputado_federal": [
        {"title": "Propor projeto de lei ou PEC", "basis": "CF art. 61 e 60", "text": "PEC precisa de um terço da Câmara para iniciar."},
        {"title": "Instalar CPI", "basis": "CF art. 58, §3º", "text": "Um terço dos deputados para investigar fato determinado."},
        {"title": "Convocar ministro", "basis": "CF art. 50", "text": "Ministro que não comparece comete crime de responsabilidade."},
        {"title": "Emenda individual ao orçamento", "basis": "CF art. 166, §9º (EC 86/2015)", "text": "Direciona parte do orçamento a obras e serviços de sua base."},
        {"title": "Apresentar denúncia por crime de responsabilidade", "basis": "CF art. 85; Lei 1.079/1950", "text": "Qualquer cidadão pode; a Câmara autoriza o processo por 2/3."},
    ],
    "senador": [
        {"title": "Sabatinar e aprovar autoridades", "basis": "CF art. 52, III e IV", "text": "Banco Central, STF, embaixadores, AGU."},
        {"title": "Julgar o Presidente", "basis": "CF art. 52, I", "text": "Em crime de responsabilidade, sob presidência do presidente do STF."},
        {"title": "Fixar alíquotas e dívida por resolução", "basis": "CF art. 52, V a IX; art. 155, §2º, IV", "text": "Limites de endividamento e alíquotas interestaduais do ICMS."},
        {"title": "Suspender lei declarada inconstitucional", "basis": "CF art. 52, X", "text": "Resolução que amplia a decisão do STF."},
        {"title": "Representar o estado", "basis": "CF art. 46", "text": "Três senadores por estado, com mandato de oito anos."},
    ],
}
