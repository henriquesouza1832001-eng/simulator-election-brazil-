"""Geradores por famílias de acontecimentos (camada base da biblioteca).

Cada família é um arquétipo com encaixes (setor, região, gravidade...). A geração é determinística e
produz eventos em dados puros (ver `event_schema`). Todos são marcados `source.type = "modelo"`.
Entidades, grupos e lugares são fictícios ou genéricos; nenhuma pessoa real aparece. Os números são
abstrações de jogo, ajustáveis aqui.
"""
from __future__ import annotations

from typing import Any, Iterator


# (nome, sigla, preposição+artigo): usado nos textos de eventos por estado.
STATES = [("Acre","AC","no"),("Alagoas","AL","em"),("Amapá","AP","no"),("Amazonas","AM","no"),("Bahia","BA","na"),("Ceará","CE","no"),
          ("Distrito Federal","DF","no"),("Espírito Santo","ES","no"),("Goiás","GO","em"),("Maranhão","MA","no"),("Mato Grosso","MT","em"),
          ("Mato Grosso do Sul","MS","em"),("Minas Gerais","MG","em"),("Pará","PA","no"),("Paraíba","PB","na"),("Paraná","PR","no"),
          ("Pernambuco","PE","em"),("Piauí","PI","no"),("Rio de Janeiro","RJ","no"),("Rio Grande do Norte","RN","no"),("Rio Grande do Sul","RS","no"),
          ("Rondônia","RO","em"),("Roraima","RR","em"),("Santa Catarina","SC","em"),("São Paulo","SP","em"),("Sergipe","SE","em"),("Tocantins","TO","no")]
STATE_SLOTS = [(n, uf.lower()) for n, uf, _ in STATES]
IN = {n: (f"{prep} {n}") for n, _, prep in STATES}                                   # "no Pará", "em Goiás", "na Bahia"
OF = {n: ({"no": "do", "na": "da", "em": "de"}[prep] + f" {n}") for n, _, prep in STATES}   # "do Pará", "de Goiás", "da Bahia"

SEVERITIES = [("leve", 0.6), ("média", 1.0), ("grave", 1.6)]
REGIONS = [("Norte", "norte"), ("Nordeste", "nordeste"), ("Centro-Oeste", "centro_oeste"), ("Sudeste", "sudeste"), ("Sul", "sul")]


def _ev(fid: str, slots: tuple, **kw: Any) -> dict[str, Any]:
    eid = ":".join([fid, *[str(s) for s in slots]])
    kw.setdefault("source", {"type": "modelo", "ref": f"família {fid}"})
    kw.setdefault("review", "aprovado")
    kw.setdefault("family", fid)
    return {"id": eid, **kw}


def _scale(effects: dict[str, float], k: float) -> dict[str, float]:
    return {key: round(v * k, 3) for key, v in effects.items() if round(v * k, 3)}


def _trio(sev: float, sector: str, cost: float, impact: dict[str, float], *, follow: str | None = None,
          dialog: str, firm: str, passive: str) -> list[dict[str, Any]]:
    """Três respostas típicas: diálogo (custa dinheiro), linha dura (custa instituições) e omissão (custa opinião)."""
    ignore_effects = {"approval": -2.0, **{k: v for k, v in impact.items()}}
    ch_pass = {"id": "omitir", "label": "Esperar a situação se resolver", "hint": "Sem custo agora; o desgaste vem depois.", "tone": "passiva",
               "effects": _scale(ignore_effects, sev), "outcome": passive}
    if follow:
        ch_pass["follow"] = [[follow, 20]]
    return [
        {"id": "dialogar", "label": "Abrir negociação e ofertar apoio", "hint": f"Custa cerca de R$ {round(cost * sev, 1)} bi.", "tone": "dialogo",
         "cost_bi": round(cost * sev, 1), "effects": _scale({"approval": 1.0, "governability": 1.0}, sev ** 0.5), "outcome": dialog},
        {"id": "firme", "label": "Responder com firmeza", "hint": "Resolve rápido, com custo político.", "tone": "dura",
         "effects": _scale({"approval": -1.2, "governability": -1.5, "inst:civilian_legitimacy": -1.5}, sev ** 0.5), "outcome": firm},
        ch_pass,
    ]


# ---------------------------------------------------------------------------------------------- paralisações
STRIKE_SECTORS = [
    ("cargas", "transportadores de carga", {"inflation": 0.3, "gdp_growth": -0.1}, 2.0),
    ("aplicativos", "motoristas de aplicativo", {"approval": -0.4}, 0.8),
    ("professores", "professores da rede pública", {"approval": -0.6}, 2.5),
    ("saude", "profissionais de saúde", {"approval": -0.8}, 3.0),
    ("policiais", "policiais civis", {"inst:constitutional_order": -0.5}, 2.2),
    ("servidores", "servidores federais", {"governability": -0.8}, 3.5),
    ("portuarios", "trabalhadores portuários", {"gdp_growth": -0.15, "inflation": 0.15}, 1.8),
    ("aeroviarios", "trabalhadores da aviação civil", {"gdp_growth": -0.1}, 1.5),
    ("petroleiros", "petroleiros de estatais fictícias", {"inflation": 0.25, "gdp_growth": -0.12}, 2.4),
    ("rurais", "produtores rurais", {"inflation": 0.2, "approval": -0.3}, 2.0),
    ("ferroviarios", "ferroviários", {"gdp_growth": -0.08}, 1.2),
    ("bancarios", "bancários de bancos públicos fictícios", {"gdp_growth": -0.05}, 1.0),
]


def strikes() -> Iterator[dict[str, Any]]:
    for sid, who, impact, cost in STRIKE_SECTORS:
        for sname, sev in SEVERITIES:
            esc = f"strike_escalada:{sid}:{sname}"
            yield _ev("strike", (sid, sname), kind="decisao", tags=["trabalho", sid], levels=["federal"], weight=1.0, cooldown=150,
                      title=f"Paralisação de {who} ({sname})",
                      text=f"Entidades de {who} fictícias anunciam paralisação de intensidade {sname}, com pauta de reajuste e condições de trabalho. "
                           f"A imprensa acompanha os efeitos no dia a dia e aliados pedem uma posição do Planalto.",
                      conditions=[{"metric": "approval", "op": "<", "value": 80}], fallback="omitir",
                      choices=_trio(sev, sid, cost, impact, follow=esc,
                                    dialog=f"A negociação com {who} encerra a paralisação em poucos dias, com custo para o caixa.",
                                    firm=f"A resposta dura reduz a paralisação de {who}, mas o governo é acusado de truculência.",
                                    passive=f"A paralisação de {who} se prolonga e o desgaste aparece na avaliação do governo."))
            yield _ev("strike_escalada", (sid, sname), kind="decisao", tags=["trabalho", sid], levels=["federal"], weight=0.0, cooldown=200,
                      title=f"Paralisação de {who} se agrava", text=f"Sem acordo, a paralisação dos {who} ganha adesão e passa a afetar serviços e preços. Governadores e prefeitos pedem socorro federal.",
                      choices=_trio(sev * 1.3, sid, cost, impact, dialog=f"Uma mediação de última hora encerra a crise com {who}, a um custo maior.",
                                    firm="A medida enérgica encerra o impasse, mas deixa cicatrizes institucionais.",
                                    passive="A crise se arrasta e vira assunto nacional."))


# ---------------------------------------------------------------------------------------------- desastres e clima
DISASTERS = [
    ("enchente", "Enchentes", {"approval": -0.5}, "Chuvas intensas alagam áreas urbanas", 1.5),
    ("seca", "Seca prolongada", {"gdp_growth": -0.1, "inflation": 0.15}, "A estiagem castiga lavouras e reservatórios", 2.5),
    ("queimada", "Queimadas", {"approval": -0.4, "inst:institutional_resistance": 0.5}, "Focos de incêndio cobrem a região de fumaça", 1.2),
    ("deslizamento", "Deslizamentos de terra", {"approval": -0.6}, "Encostas cedem após dias de chuva", 1.0),
    ("calor", "Onda de calor extremo", {"approval": -0.3, "gdp_growth": -0.05}, "Temperaturas recordes pressionam saúde e energia", 0.8),
    ("tempestade", "Tempestades e ventos fortes", {"approval": -0.3}, "Ventos derrubam redes elétricas e telhados", 0.9),
    ("geada", "Geadas fora de época", {"inflation": 0.2, "gdp_growth": -0.08}, "Geadas atingem lavouras e elevam preços de alimentos", 1.4),
    ("ressaca", "Ressaca e erosão costeira", {"approval": -0.3}, "O mar avança sobre áreas habitadas do litoral", 0.9),
]


def disasters() -> Iterator[dict[str, Any]]:
    for did, name, impact, lead, cost in DISASTERS:
        for rlabel, rid in STATE_SLOTS:
            for sname, sev in SEVERITIES:
                yield _ev("desastre", (did, rid, sname), kind="decisao", tags=["clima", "emergencia", did], levels=["federal"], weight=0.7, cooldown=270,
                          title=f"{name} {IN[rlabel]} ({sname})",
                          text=f"{lead} em cidades fictícias {OF[rlabel]}. Governadores e prefeitos pedem ajuda federal e a imprensa mostra famílias desalojadas. "
                               f"A gravidade é {sname}.",
                          fallback="enviar_ministro",
                          choices=[
                              {"id": "visitar", "label": "Visitar a área e liberar verba emergencial", "hint": f"R$ {round(cost * sev, 1)} bi e agenda cheia.", "tone": "dialogo",
                               "cost_bi": round(cost * sev, 1), "effects": _scale({"approval": 2.0, "governability": 1.0}, sev ** 0.5),
                               "outcome": f"A presença do presidente e a verba rápida melhoram a imagem do governo {IN[rlabel]}."},
                              {"id": "enviar_ministro", "label": "Enviar o ministro responsável", "hint": "Resposta protocolar, custo menor.", "tone": "neutra",
                               "cost_bi": round(cost * sev * 0.5, 1), "effects": {"approval": round(0.5 * sev, 2)},
                               "outcome": "A resposta é considerada correta, porém distante."},
                              {"id": "omitir", "label": "Deixar com estados e municípios", "hint": "Sem custo federal agora.", "tone": "passiva",
                               "effects": _scale({"approval": -2.0, **impact}, sev), "outcome": f"A demora federal {IN[rlabel]} vira crítica nacional."}])


# ---------------------------------------------------------------------------------------------- denúncias e integridade
MINISTRIES = ["Casa Civil", "Fazenda", "Saúde", "Educação", "Infraestrutura", "Justiça", "Defesa", "Agricultura", "Desenvolvimento Social",
              "Relações Exteriores", "Minas e Energia", "Cidades"]
SCANDALS = [("contrato", "um contrato de comunicação", "favorecimento"), ("licitacao", "uma licitação de obras", "direcionamento"),
            ("viagem", "gastos com viagens oficiais", "uso indevido de recursos"), ("nomeacao", "nomeações para cargos técnicos", "indicação política")]


def scandals() -> Iterator[dict[str, Any]]:
    for m in MINISTRIES:
        slug = m.lower().replace(" ", "_").replace("ú", "u").replace("é", "e").replace("ã", "a").replace("ç", "c")
        for cid, what, tipo in SCANDALS:
            for sname, sev in SEVERITIES[1:]:
                follow_cpi = f"cpi_pedido_familia:{slug}:{cid}:{sname}"
                yield _ev("escandalo", (slug, cid, sname), kind="decisao", tags=["integridade", "imprensa"], levels=["federal"], weight=0.8, cooldown=160,
                          title=f"Reportagem aponta suspeita sobre {what} no ministério de {m}",
                          text=f"Uma reportagem fictícia levanta suspeita de {tipo} em {what} ligada a um dirigente do ministério de {m}. A oposição cobra explicações "
                               f"e aliados pedem uma resposta rápida do Planalto.",
                          conditions=[{"metric": "integrity", "op": "<", "value": 92}], fallback="nota",
                          choices=[
                              {"id": "afastar", "label": "Afastar o dirigente e abrir apuração", "hint": "Protege a imagem; abre vaga.", "tone": "etica",
                               "effects": _scale({"integrity": 2.0, "approval": 0.6, "congress_support": -1.0}, sev), "outcome": "O dirigente sai, a apuração começa e o caso perde força."},
                              {"id": "defender", "label": "Defender publicamente a equipe", "hint": "Mantém a unidade e arrisca a imagem.", "tone": "passiva",
                               "effects": _scale({"integrity": -3.0, "approval": -1.5}, sev), "follow": [[follow_cpi, 18]],
                               "outcome": "A oposição ganha munição e promete pedir uma comissão de inquérito."},
                              {"id": "nota", "label": "Responder apenas com nota oficial", "hint": "Meio-termo.", "tone": "neutra",
                               "effects": _scale({"integrity": -1.0, "approval": -0.5}, sev), "outcome": "A nota não convence todos, mas tira o tema do centro da pauta."}])
                yield _ev("cpi_pedido_familia", (slug, cid, sname), kind="decisao", tags=["congresso", "integridade"], levels=["federal"], weight=0.0, cooldown=260,
                          title=f"Oposição junta assinaturas para CPI sobre {what}",
                          text=f"Parlamentares de oposição fictícios reúnem assinaturas para instalar uma comissão de inquérito sobre {what} no ministério de {m}.",
                          fallback="resistir",
                          choices=[
                              {"id": "colaborar", "label": "Colaborar e entregar documentos", "hint": "Reduz o desgaste futuro.", "tone": "etica",
                               "effects": _scale({"integrity": 1.5, "congress_support": -1.0}, sev), "outcome": "A comissão se instala sem surpresas e perde fôlego."},
                              {"id": "resistir", "label": "Mobilizar a base para barrar", "hint": "Gasta capital político.", "tone": "dura",
                               "effects": _scale({"congress_support": -3.0, "governability": -2.0}, sev),
                               "follow": [[f"cpi_instalada_familia:{slug}:{cid}:{sname}", 22]], "outcome": "A base adia a instalação, mas o desgaste cresce."}])
                yield _ev("cpi_instalada_familia", (slug, cid, sname), kind="info", tags=["congresso"], levels=["federal"], weight=0.0, cooldown=300,
                          title=f"CPI sobre {what} é instalada", text=f"A comissão foi instalada e convoca depoimentos sobre {what} no ministério de {m}. O noticiário acompanha cada audiência.",
                          choices=[{"id": "ok", "label": "Acompanhar", "effects": _scale({"approval": -1.5, "integrity": -1.0}, sev), "outcome": "As audiências desgastam o governo."}])


# ---------------------------------------------------------------------------------------------- mercado e economia
MARKET_SHOCKS = [
    ("cambio", "Câmbio dispara", {"inflation": 0.3}, "O dólar sobe com sinais de incerteza e operadores esperam sinalização do governo"),
    ("juros_ext", "Juros externos sobem", {"gdp_growth": -0.1, "inflation": 0.15}, "Bancos centrais do exterior elevam juros e capital deixa países emergentes"),
    ("commodities", "Queda nas commodities", {"gdp_growth": -0.12}, "Preços de exportações agrícolas e minerais caem no mercado internacional"),
    ("rating", "Agência revisa nota de crédito", {"inflation": 0.1, "gdp_growth": -0.06}, "Uma agência fictícia de classificação revê a perspectiva do país"),
    ("bolsa", "Bolsa cai em dia de nervosismo", {"gdp_growth": -0.05}, "A bolsa recua forte e investidores pedem previsibilidade"),
    ("fuga_capital", "Saída de capital estrangeiro", {"inflation": 0.2, "gdp_growth": -0.08}, "Investidores estrangeiros reduzem posições no país"),
    ("petroleo", "Petróleo dispara", {"inflation": 0.35}, "O preço do petróleo sobe e pressiona combustíveis"),
    ("credito", "Aperto de crédito", {"gdp_growth": -0.1, "unemployment": 0.1}, "Bancos endurecem a oferta de crédito para empresas e famílias"),
]


def markets() -> Iterator[dict[str, Any]]:
    for mid, name, impact, lead in MARKET_SHOCKS:
        for sname, sev in SEVERITIES:
            yield _ev("mercado", (mid, sname), kind="decisao", tags=["economia", "mercado", mid], levels=["federal"], weight=0.8, cooldown=150,
                      title=f"{name} ({sname})", text=f"{lead}. A equipe econômica pede uma decisão sobre o tom da resposta. A intensidade do choque é {sname}.",
                      fallback="minimizar",
                      choices=[
                          {"id": "sinalizar", "label": "Anunciar medidas de ajuste e previsibilidade", "hint": "Acalma o mercado; pede disciplina.", "tone": "tecnica",
                           "effects": _scale({"primary_balance": 0.08, "congress_support": -1.0, "approval": -0.3}, sev ** 0.5), "outcome": "O mercado respira, mas a base reclama de cortes."},
                          {"id": "estimular", "label": "Lançar estímulo para amortecer o choque", "hint": "Protege emprego; custa caixa.", "tone": "populista", "cost_bi": round(2.0 * sev, 1),
                           "effects": _scale({"approval": 0.8, "gdp_growth": 0.05, "inflation": 0.1}, sev ** 0.5), "outcome": "O estímulo ameniza o choque, com custo fiscal."},
                          {"id": "minimizar", "label": "Minimizar o movimento", "hint": "Aposta que passa.", "tone": "passiva",
                           "effects": _scale({"approval": -0.5, **impact}, sev), "outcome": "O choque se prolonga e o custo aparece nos preços e no crescimento."}])


# ---------------------------------------------------------------------------------------------- preços e abastecimento
FOODS = ["arroz", "feijão", "carne", "café", "leite", "ovos", "trigo", "açúcar", "óleo de soja", "frango", "hortaliças", "frutas"]


def prices() -> Iterator[dict[str, Any]]:
    for food in FOODS:
        for sname, sev in SEVERITIES:
            yield _ev("preco_alimento", (food.replace(" ", "_"), sname), kind="decisao", tags=["precos", "abastecimento"], levels=["federal", "estadual", "municipal"],
                      weight=0.8, cooldown=170, title=f"Preço de {food} sobe ({sname}) e pesa no bolso",
                      text=f"O preço de {food} sobe em feiras e supermercados fictícios e vira assunto nas redes e no rádio. Entidades de consumidores cobram providências do governo.",
                      fallback="aguardar",
                      choices=[
                          {"id": "importar", "label": "Facilitar importação e reduzir tarifas por tempo limitado", "hint": "Alivia o preço; irrita o produtor local.", "tone": "tecnica",
                           "cost_bi": round(1.0 * sev, 1), "effects": _scale({"approval": 1.0, "inflation": -0.2, "inst:institutional_resistance": 0.3}, sev ** 0.5),
                           "outcome": f"A medida segura o preço de {food}, com reclamação do setor produtivo."},
                          {"id": "estoque", "label": "Liberar estoques públicos e reforçar a fiscalização", "hint": "Resposta rápida e dirigida.", "tone": "dialogo", "cost_bi": round(0.6 * sev, 1),
                           "effects": _scale({"approval": 0.6, "inflation": -0.1}, sev ** 0.5), "outcome": f"Os estoques reduzem a pressão no preço de {food} por algumas semanas."},
                          {"id": "aguardar", "label": "Aguardar a safra e o mercado se ajustarem", "hint": "Sem custo agora.", "tone": "passiva",
                           "effects": _scale({"approval": -1.5, "inflation": 0.25}, sev), "outcome": f"O preço de {food} segue alto e pesa na avaliação do governo."}])


# ---------------------------------------------------------------------------------------------- saúde
HEALTH = [("dengue", "Surto de dengue", 1.5), ("gripe", "Alta de casos de gripe", 0.9), ("sarampo", "Casos de sarampo por baixa vacinação", 0.8),
          ("remedios", "Falta de medicamentos em postos de saúde", 1.2), ("superlotacao", "Superlotação de hospitais", 1.8), ("filas", "Filas por cirurgias eletivas", 1.6)]


def health() -> Iterator[dict[str, Any]]:
    for hid, name, cost in HEALTH:
        for rlabel, rid in STATE_SLOTS:
            for sname, sev in SEVERITIES[1:]:
                yield _ev("saude_crise", (hid, rid, sname), kind="decisao", tags=["saude"], levels=["federal"], weight=0.7, cooldown=210,
                          title=f"{name} {IN[rlabel]} ({sname})", text=f"{name} pressiona a rede de saúde de cidades fictícias {OF[rlabel]}. Secretarias estaduais pedem apoio federal e a imprensa mostra filas.",
                          fallback="omitir",
                          choices=[
                              {"id": "forca_tarefa", "label": "Enviar força-tarefa e reforçar a rede", "hint": f"R$ {round(cost * sev, 1)} bi.", "tone": "dialogo", "cost_bi": round(cost * sev, 1),
                               "effects": _scale({"approval": 1.5, "governability": 0.5}, sev ** 0.5), "outcome": f"A força-tarefa reduz a pressão sobre a rede {IN[rlabel]}."},
                              {"id": "campanha", "label": "Lançar campanha de prevenção e orientar estados", "hint": "Custo menor, efeito mais lento.", "tone": "tecnica", "cost_bi": round(cost * sev * 0.3, 1),
                               "effects": _scale({"approval": 0.5}, sev), "outcome": "A campanha ajuda, mas a pressão imediata permanece."},
                              {"id": "omitir", "label": "Manter a responsabilidade com estados e municípios", "hint": "Sem custo federal.", "tone": "passiva",
                               "effects": _scale({"approval": -2.0, "integrity": -0.3}, sev), "outcome": "A ausência federal vira crítica no noticiário."}])


# ---------------------------------------------------------------------------------------------- segurança
SECURITY = [("faccao", "Ataques coordenados atribuídos a uma facção fictícia", 2.0), ("chacina", "Chacina em bairro periférico", 1.0), ("rebeliao", "Rebelião em presídio", 1.3),
            ("fronteira", "Aumento de crimes na fronteira", 1.5), ("cibercrime", "Onda de golpes digitais e ataques a sistemas", 0.9), ("roubo_carga", "Alta de roubos de carga em rodovias", 1.1)]


def security() -> Iterator[dict[str, Any]]:
    for sid, name, cost in SECURITY:
        for rlabel, rid in STATE_SLOTS:
            for sname, sev in SEVERITIES[1:]:
                yield _ev("seguranca", (sid, rid, sname), kind="decisao", tags=["seguranca"], levels=["federal"], weight=0.7, cooldown=200,
                          title=f"{name} {IN[rlabel]} ({sname})", text=f"{name} em cidades fictícias {OF[rlabel]} preocupa moradores. Governadores cobram integração das forças e a oposição pede uma resposta dura.",
                          fallback="omitir",
                          choices=[
                              {"id": "integrar", "label": "Integrar forças federais e estaduais com plano de metas", "hint": f"R$ {round(cost * sev, 1)} bi.", "tone": "tecnica", "cost_bi": round(cost * sev, 1),
                               "effects": _scale({"approval": 1.0, "governability": 1.0}, sev ** 0.5), "outcome": "O plano integra as forças e reduz a sensação de insegurança."},
                              {"id": "forca", "label": "Enviar a Força Nacional e endurecer operações", "hint": "Impacto imediato, risco institucional.", "tone": "dura",
                               "effects": _scale({"approval": 0.8, "inst:constitutional_order": -1.2, "inst:civilian_legitimacy": -1.0}, sev ** 0.5), "outcome": "A presença reduz os crimes, mas gera críticas de direitos humanos."},
                              {"id": "omitir", "label": "Deixar com os governos estaduais", "hint": "Sem custo federal.", "tone": "passiva",
                               "effects": _scale({"approval": -1.8}, sev), "outcome": "A inação federal alimenta a pressão sobre o governo."}])


# ---------------------------------------------------------------------------------------------- Congresso e pautas
BLOCS = [("ruralista", "bancada ruralista fictícia"), ("evangelica", "bancada evangélica fictícia"), ("seguranca", "bancada da segurança fictícia"),
         ("sindical", "bancada sindical fictícia"), ("ambiental", "bancada ambiental fictícia"), ("empresarial", "frente empresarial fictícia"),
         ("municipalista", "frente municipalista fictícia"), ("saude", "frente da saúde fictícia")]
DEMANDS = [("emendas", "liberação de emendas parlamentares", 2.5), ("cargos", "mais espaço em cargos de segundo escalão", 0.0), ("pauta", "prioridade para um projeto da bancada", 0.5),
           ("obra", "uma obra prioritária na base eleitoral", 3.0)]


def congress() -> Iterator[dict[str, Any]]:
    for bid, bname in BLOCS:
        for did, dname, cost in DEMANDS:
            for sname, sev in SEVERITIES[:2]:
                yield _ev("congresso_demanda", (bid, did, sname), kind="oportunidade", tags=["congresso", bid], levels=["federal"], weight=0.9, cooldown=130,
                          title=f"A {bname} cobra {dname}",
                          text=f"Lideranças da {bname} procuram o governo e cobram {dname} em troca de apoio em votações importantes das próximas semanas.",
                          conditions=[{"metric": "congress_support", "op": "<", "value": 75}], fallback="recusar",
                          choices=[
                              {"id": "atender", "label": "Atender o pedido", "hint": f"Ganha base; custa R$ {round(cost * sev, 1)} bi e imagem." if cost else "Ganha base; custa imagem.", "tone": "fisiologica",
                               "cost_bi": round(cost * sev, 1), "effects": _scale({"congress_support": 5.0, "governability": 2.0, "integrity": -2.5}, sev ** 0.5),
                               "outcome": f"A {bname} passa a votar com o governo, e a imprensa registra o acordo."},
                              {"id": "negociar", "label": "Negociar contrapartidas técnicas", "hint": "Apoio parcial.", "tone": "tecnica",
                               "effects": _scale({"congress_support": 2.0, "governability": 1.0, "integrity": 0.3}, sev ** 0.5), "outcome": "O acordo é possível, com apoio mais limitado."},
                              {"id": "recusar", "label": "Recusar e manter critérios", "hint": "Preserva a imagem.", "tone": "etica",
                               "effects": _scale({"congress_support": -2.0, "integrity": 1.5}, sev ** 0.5), "outcome": "A base reclama, mas a gestão ganha credibilidade."}])


# ---------------------------------------------------------------------------------------------- opinião pública por grupo
GROUPS = [("jovens", "jovens de 16 a 29 anos"), ("mulheres", "eleitoras mulheres"), ("evangelicos", "eleitores evangélicos"), ("servidores", "servidores públicos"),
          ("agro", "o agronegócio"), ("sindicalizados", "trabalhadores sindicalizados"), ("classe_media", "a classe média urbana"), ("periferia", "moradores das periferias"),
          ("empresarios", "pequenos empresários"), ("idosos", "eleitores idosos"), ("rurais", "a população rural"), ("professores", "professores")]


def opinion() -> Iterator[dict[str, Any]]:
    for gid, gname in GROUPS:
        yield _ev("opiniao_queda", (gid,), kind="oportunidade", tags=["opiniao", gid], levels=["federal"], weight=0.8, cooldown=150,
                  title=f"Pesquisa mostra queda de aprovação entre {gname}",
                  text=f"Um instituto fictício aponta queda na avaliação do governo entre {gname}. A equipe de comunicação propõe uma resposta direcionada.",
                  conditions=[{"metric": "approval", "op": "<", "value": 60}], fallback="ignorar",
                  choices=[
                      {"id": "agenda", "label": "Montar uma agenda de entregas para o grupo", "hint": "R$ 0,5 bi e articulação.", "tone": "dialogo", "cost_bi": 0.5,
                       "effects": {"approval": 1.2}, "outcome": f"A agenda recupera parte do terreno entre {gname}."},
                      {"id": "campanha", "label": "Lançar campanha de comunicação", "hint": "R$ 0,2 bi.", "tone": "populista", "cost_bi": 0.2,
                       "effects": {"approval": 0.6}, "outcome": "A campanha ajuda um pouco, sem mudar a percepção de fundo."},
                      {"id": "ignorar", "label": "Deixar passar", "hint": "Sem custo.", "tone": "passiva",
                       "effects": {"approval": -0.5}, "outcome": "A tendência continua por algum tempo."}])
        yield _ev("opiniao_alta", (gid,), kind="info", tags=["opiniao", gid], levels=["federal"], weight=0.5, cooldown=200,
                  title=f"Boa avaliação do governo entre {gname}", text=f"Uma pesquisa fictícia registra melhora na avaliação do governo entre {gname}. Aliados pedem aproveitar o momento.",
                  conditions=[{"metric": "approval", "op": ">", "value": 55}],
                  choices=[{"id": "ok", "label": "Acompanhar", "effects": {"congress_support": 0.8}, "outcome": "A base se anima e pede pautas mais ambiciosas."}])


# ---------------------------------------------------------------------------------------------- infraestrutura e energia
INFRA = [("apagao", "Apagão", {"gdp_growth": -0.08, "approval": -0.5}, 1.6), ("rodovia", "Rodovia federal interditada", {"gdp_growth": -0.05}, 1.0),
         ("aeroporto", "Caos em aeroportos", {"approval": -0.4}, 0.8), ("barragem", "Alerta em barragem", {"approval": -0.6, "inst:institutional_resistance": 0.4}, 1.8),
         ("porto", "Congestionamento em porto", {"gdp_growth": -0.07, "inflation": 0.1}, 1.1), ("internet", "Queda de conectividade em larga escala", {"approval": -0.3}, 0.9)]


def infrastructure() -> Iterator[dict[str, Any]]:
    for iid, name, impact, cost in INFRA:
        for rlabel, rid in STATE_SLOTS:
            for sname, sev in SEVERITIES[:2]:
                yield _ev("infraestrutura", (iid, rid, sname), kind="decisao", tags=["infraestrutura", iid], levels=["federal"], weight=0.7, cooldown=220,
                          title=f"{name} {IN[rlabel]} ({sname})", text=f"{name} afeta cidades fictícias {OF[rlabel]}. Empresas e prefeitos cobram ação do governo federal e da agência responsável.",
                          fallback="omitir",
                          choices=[
                              {"id": "intervir", "label": "Acionar plano de contingência e reforçar a fiscalização", "hint": f"R$ {round(cost * sev, 1)} bi.", "tone": "tecnica", "cost_bi": round(cost * sev, 1),
                               "effects": _scale({"approval": 1.0, "governability": 0.8}, sev ** 0.5), "outcome": "A contingência normaliza o serviço e melhora a percepção de gestão."},
                              {"id": "cobrar", "label": "Cobrar a concessionária e aplicar multas", "hint": "Pressão sem custo; efeito limitado.", "tone": "dura",
                               "effects": _scale({"approval": 0.4, "gdp_growth": 0.02}, sev ** 0.5), "outcome": "A cobrança dá resposta política, com efeito prático lento."},
                              {"id": "omitir", "label": "Esperar a normalização", "hint": "Sem custo.", "tone": "passiva",
                               "effects": _scale({"approval": -1.2, **impact}, sev), "outcome": "O problema se arrasta e o desgaste aparece."}])


# ---------------------------------------------------------------------------------------------- justiça e instituições
LEGAL = [("tributaria", "uma medida tributária"), ("ambiental", "uma norma ambiental"), ("trabalhista", "uma regra trabalhista"), ("previdenciaria", "um ajuste previdenciário"),
         ("seguranca", "um decreto de segurança"), ("educacao", "uma política de educação"), ("saude", "uma regra de saúde"), ("energia", "uma regra do setor elétrico")]


def legal() -> Iterator[dict[str, Any]]:
    for lid, what in LEGAL:
        for sname, sev in SEVERITIES[:2]:
            yield _ev("liminar", (lid, sname), kind="decisao", tags=["justica", "instituicoes"], levels=["federal"], weight=0.7, cooldown=210,
                      title=f"Liminar suspende {what} do governo",
                      text=f"Um ministro fictício de um tribunal superior suspende {what} do Executivo por falta de base legal. A advocacia pública pede orientação sobre como proceder.",
                      fallback="acatar",
                      choices=[
                          {"id": "recorrer", "label": "Recorrer ao plenário", "hint": "Pode desgastar a relação com a Corte.", "tone": "dura",
                           "effects": _scale({"inst:institutional_resistance": 2.0, "governability": 1.0, "approval": 0.3}, sev), "outcome": "O recurso mantém a medida em disputa por semanas."},
                          {"id": "acatar", "label": "Acatar e reescrever a medida", "hint": "Evita atrito.", "tone": "etica",
                           "effects": _scale({"inst:constitutional_order": 2.0, "governability": -1.0}, sev), "outcome": "A medida volta ao Congresso em nova forma."}])


# ---------------------------------------------------------------------------------------------- ambiente e diplomacia
ENVIRONMENT = [("desmatamento", "Alerta de desmatamento acima do esperado"), ("oleo", "Vazamento de óleo no litoral"), ("mineracao", "Conflito por mineração ilegal"),
               ("licenciamento", "Disputa sobre licenciamento ambiental de grande obra")]
DIPLOMACY = [("tarifa", "Bloco comercial anuncia tarifas sobre produtos do país"), ("cupula", "Convite para uma cúpula regional"), ("acordo", "Proposta de acordo comercial com bloco asiático"),
             ("fronteira", "Incidente diplomático na fronteira"), ("clima", "Conferência internacional cobra metas climáticas"), ("refugiados", "Chegada de refugiados à fronteira")]


def environment_and_diplomacy() -> Iterator[dict[str, Any]]:
    for eid, name in ENVIRONMENT:
        for sname, sev in SEVERITIES[:2]:
            yield _ev("ambiente", (eid, sname), kind="decisao", tags=["ambiente", eid], levels=["federal"], weight=0.6, cooldown=240, title=f"{name} ({sname})",
                      text=f"{name}. Organizações, governadores e o noticiário pedem uma posição do governo. O assunto tem repercussão externa e interna.", fallback="omitir",
                      choices=[
                          {"id": "agir", "label": "Lançar plano de fiscalização e recuperação", "hint": f"R$ {round(1.2 * sev, 1)} bi.", "tone": "tecnica", "cost_bi": round(1.2 * sev, 1),
                           "effects": _scale({"approval": 0.8, "inst:institutional_resistance": -0.4, "gdp_growth": -0.02}, sev ** 0.5), "outcome": "A resposta firme melhora a imagem do governo, com custo ao setor."},
                          {"id": "omitir", "label": "Evitar medidas que desagradem setores produtivos", "hint": "Sem custo agora.", "tone": "passiva",
                           "effects": _scale({"approval": -1.0, "inst:institutional_resistance": 0.6}, sev), "outcome": "A inação gera críticas dentro e fora do país."}])
    for did, name in DIPLOMACY:
        for sname, sev in SEVERITIES[:2]:
            yield _ev("diplomacia", (did, sname), kind="oportunidade", tags=["diplomacia", did], levels=["federal"], weight=0.5, cooldown=240, title=f"{name} ({sname})",
                      text=f"{name}. O Itamaraty fictício apresenta opções ao presidente, com impacto no comércio e na imagem externa do país.", fallback="neutro",
                      choices=[
                          {"id": "avancar", "label": "Avançar com negociação e agenda pessoal", "hint": "Custa dias de agenda.", "tone": "dialogo", "cost_bi": 0.05,
                           "effects": _scale({"approval": 0.4, "gdp_growth": 0.03}, sev), "outcome": "A negociação avança e a imagem externa melhora."},
                          {"id": "neutro", "label": "Delegar ao ministério", "hint": "Sem custo.", "tone": "neutra", "effects": {"approval": 0.1}, "outcome": "A resposta é correta e discreta."}])


# ---------------------------------------------------------------------------------------------- militância e partido
CAUSES_PT = [("moradia", "moradia"), ("saude", "saúde"), ("educacao", "educação"), ("transporte", "transporte"), ("seguranca", "segurança"),
             ("ambiente", "meio ambiente"), ("cultura", "cultura"), ("esporte", "esporte"), ("trabalho", "trabalho e renda"), ("mulheres", "direitos das mulheres"),
             ("juventude", "juventude"), ("idosos", "pessoas idosas")]


def _mil(slug: str, cid: str, **kw: Any) -> dict[str, Any]:
    return _ev(f"mil_{slug}", (cid,), **kw)


def militancy() -> Iterator[dict[str, Any]]:
    """Acontecimentos da trajetória partidária (níveis `militante` e `partido`). Efeitos `pp:*` na escala da tela."""
    for cid, c in CAUSES_PT:
        base = dict(tags=["militancia", cid], cooldown=60, weight=1.0)
        yield _mil("mutirao", cid, kind="oportunidade", levels=["militante"], title=f"Mutirão comunitário por {c} no seu bairro",
                   text=f"Moradores fictícios organizam um mutirão por {c} e convidam você. É uma chance de ser visto e de conhecer lideranças locais.", fallback="ignorar", **base,
                   choices=[{"id": "participar", "label": "Participar do mutirão", "hint": "Gasta energia e rende contatos.", "tone": "dialogo", "effects": {"pp:reputation": 1.5, "pp:network": 2.5, "pp:energy": -10}, "outcome": "Você ajuda, conversa com muita gente e sai conhecido no bairro."},
                            {"id": "liderar", "label": "Propor-se a coordenar", "hint": "Mais retorno, mais cansaço.", "tone": "tecnica", "effects": {"pp:reputation": 3.0, "pp:network": 3.0, "pp:militancy": 2.0, "pp:energy": -20}, "outcome": "A coordenação dá visibilidade, e o cansaço cobra seu preço."},
                            {"id": "ignorar", "label": "Não participar desta vez", "hint": "Sem custo de energia.", "tone": "passiva", "effects": {"pp:reputation": -0.5}, "outcome": "O mutirão acontece sem você e alguém ocupa o espaço."}])
        yield _mil("assembleia_conflito", cid, kind="decisao", levels=["militante"], title=f"Conflito em reunião sobre {c}",
                   text=f"Uma reunião sobre {c} esquenta: dois grupos fictícios discutem e a mesa pede que alguém ajude a destravar. Todos olham para você.", fallback="calar", **base,
                   choices=[{"id": "mediar", "label": "Propor uma mediação", "hint": "Pode render respeito.", "tone": "dialogo", "effects": {"pp:reputation": 2.0, "pp:network": 1.5, "pp:energy": -8}, "outcome": "Sua mediação acalma os ânimos e rende respeito dos dois lados."},
                            {"id": "tomar_lado", "label": "Defender com firmeza um dos lados", "hint": "Ganha militância; perde pontes.", "tone": "dura", "effects": {"pp:militancy": 2.5, "pp:network": -1.5, "pp:reputation": 0.5}, "outcome": "Você marca posição e conquista aliados, mas fecha portas."},
                            {"id": "calar", "label": "Ficar em silêncio", "hint": "Sem risco.", "tone": "passiva", "effects": {"pp:reputation": -0.8}, "outcome": "Você passa despercebido, e a oportunidade de se destacar se perde."}])
        yield _mil("convite_fala", cid, kind="oportunidade", levels=["militante"], title=f"Convite para falar sobre {c} em um evento local",
                   text=f"Uma associação fictícia de moradores convida você para falar sobre {c} em um evento local. Haverá imprensa de bairro e lideranças.", fallback="recusar", **base,
                   choices=[{"id": "aceitar", "label": "Aceitar e preparar a fala", "hint": "Pode render muito ou dar errado.", "tone": "tecnica", "effects": {"pp:reputation": 3.0, "pp:network": 2.0, "pp:militancy": 1.0, "pp:energy": -12}, "outcome": "Sua fala é bem recebida e gera convites."},
                            {"id": "recusar", "label": "Recusar por ora", "hint": "Preserva energia.", "tone": "passiva", "effects": {"pp:reputation": -0.3}, "outcome": "Outra pessoa ocupa o espaço no evento."}])
        yield _mil("ataque_redes", cid, kind="decisao", levels=["militante", "partido"], title=f"Ataques nas redes à sua defesa de {c}",
                   text=f"Perfis fictícios atacam nas redes a sua defesa de {c}, misturando críticas legítimas e ofensas. O assunto começa a circular no bairro.", fallback="ignorar", **base,
                   choices=[{"id": "dados", "label": "Responder com dados e calma", "hint": "Constrói reputação.", "tone": "tecnica", "effects": {"pp:reputation": 2.0, "pp:energy": -6}, "outcome": "A resposta serena ganha respeito até de quem discorda."},
                            {"id": "duro", "label": "Rebater no mesmo tom", "hint": "Mobiliza a base; arrisca a imagem.", "tone": "dura", "effects": {"pp:militancy": 2.0, "pp:reputation": -1.5}, "outcome": "Sua base vibra, mas a briga mancha a imagem."},
                            {"id": "ignorar", "label": "Não responder", "hint": "Sem custo.", "tone": "passiva", "effects": {"pp:reputation": -0.5}, "outcome": "O assunto esfria devagar."}])
        yield _mil("vizinho_pede", cid, kind="decisao", levels=["militante"], title=f"Morador pede ajuda com um problema de {c}",
                   text=f"Um morador fictício procura você com um problema concreto de {c} e acredita que você pode ajudar a encaminhar.", fallback="encaminhar", **base,
                   choices=[{"id": "ajudar", "label": "Acompanhar o caso pessoalmente", "hint": "Gasta energia; rende reputação.", "tone": "dialogo", "effects": {"pp:reputation": 2.5, "pp:network": 1.0, "pp:energy": -10}, "outcome": "O caso se resolve e a notícia corre pelo bairro."},
                            {"id": "encaminhar", "label": "Encaminhar a um órgão competente", "hint": "Custo baixo.", "tone": "neutra", "effects": {"pp:reputation": 0.8}, "outcome": "Você ajuda de forma discreta."},
                            {"id": "recusar", "label": "Dizer que não pode ajudar", "hint": "Sem custo.", "tone": "passiva", "effects": {"pp:reputation": -1.0}, "outcome": "A recusa decepciona quem confiava em você."}])
        yield _mil("assembleia_diretorio", cid, kind="decisao", levels=["partido"], title=f"Assembleia do diretório discute uma proposta sobre {c}",
                   text=f"O diretório local do partido debate uma proposta sobre {c}. Há alas divididas e quem se posiciona ganha ou perde prestígio.", fallback="maioria", **base,
                   choices=[{"id": "defender", "label": "Defender uma proposta própria", "hint": "Risco e retorno altos.", "tone": "tecnica", "effects": {"pp:standing": 3.5, "pp:reputation": 1.0, "pp:energy": -10}, "outcome": "Sua proposta chama atenção e consolida seu nome no diretório."},
                            {"id": "maioria", "label": "Apoiar a posição da maioria", "hint": "Segurança.", "tone": "neutra", "effects": {"pp:standing": 1.2}, "outcome": "Você é visto como alguém confiável, sem brilho."},
                            {"id": "abster", "label": "Abster-se", "hint": "Sem risco.", "tone": "passiva", "effects": {"pp:standing": -0.8}, "outcome": "A abstenção é lida como falta de iniciativa."}])
        yield _mil("denuncia_interna", cid, kind="decisao", levels=["partido"], title=f"Suspeita de irregularidade no diretório sobre recursos de {c}",
                   text=f"Você percebe uma possível irregularidade na aplicação de recursos de uma ação sobre {c} no diretório fictício. Há quem peça discrição.", fallback="omitir", **base,
                   choices=[{"id": "denunciar", "label": "Levar o caso à comissão de ética", "hint": "Honra a reputação; custa prestígio.", "tone": "etica", "effects": {"pp:reputation": 3.0, "pp:standing": -3.0}, "outcome": "Sua atitude impressiona o público, mas cria desafetos no partido."},
                            {"id": "conversar", "label": "Conversar reservadamente com a direção", "hint": "Meio-termo.", "tone": "dialogo", "effects": {"pp:standing": 1.0, "pp:reputation": 0.5}, "outcome": "A direção corrige o rumo e agradece a discrição."},
                            {"id": "omitir", "label": "Fingir que não viu", "hint": "Preserva relações; corrói a imagem.", "tone": "passiva", "effects": {"pp:standing": 1.5, "pp:reputation": -2.0}, "outcome": "Você preserva laços, mas se sente cúmplice."}])
    for aid, a in [("a", "ala mais antiga do partido"), ("b", "ala renovadora do partido"), ("c", "ala sindical do partido"), ("d", "ala liberal do partido")]:
        yield _ev("mil_padrinho", (aid,), kind="decisao", tags=["partido", "alas"], levels=["partido"], weight=0.9, cooldown=90,
                  title=f"Dirigente da {a} oferece ser seu padrinho político",
                  text=f"Um dirigente fictício da {a} oferece apoio à sua trajetória em troca de lealdade nas próximas votações internas.", fallback="recusar",
                  choices=[{"id": "aceitar", "label": "Aceitar o apadrinhamento", "hint": "Ganha prestígio; compromete sua independência.", "tone": "fisiologica", "effects": {"pp:standing": 5.0, "pp:network": 2.0, "pp:reputation": -1.0}, "outcome": "Portas se abrem, mas você agora tem dono."},
                           {"id": "negociar", "label": "Aceitar sem se comprometer com votos", "hint": "Meio-termo.", "tone": "dialogo", "effects": {"pp:standing": 2.5, "pp:network": 1.0}, "outcome": "O apoio é mais frio, porém sem amarras."},
                           {"id": "recusar", "label": "Recusar e seguir por conta própria", "hint": "Preserva a independência.", "tone": "etica", "effects": {"pp:reputation": 1.5, "pp:standing": -1.5}, "outcome": "A independência rende respeito, e menos portas."}])
        yield _ev("mil_ajuda_campanha", (aid,), kind="oportunidade", tags=["partido", "campanha"], levels=["partido"], weight=0.9, cooldown=90,
                  title=f"Candidato da {a} pede ajuda na campanha",
                  text=f"Um candidato fictício da {a} pede que você coordene a mobilização em um bairro durante a campanha.", fallback="recusar",
                  choices=[{"id": "ajudar", "label": "Coordenar a mobilização no bairro", "hint": "Exige muita energia.", "tone": "dialogo", "effects": {"pp:standing": 3.5, "pp:network": 3.0, "pp:energy": -18}, "outcome": "Seu trabalho é notado e a gratidão do candidato vira capital político."},
                           {"id": "recusar", "label": "Recusar por falta de tempo", "hint": "Preserva energia.", "tone": "passiva", "effects": {"pp:standing": -1.0}, "outcome": "O convite passa para outra pessoa."}])
        yield _ev("mil_assessor", (aid,), kind="oportunidade", tags=["partido"], levels=["partido"], weight=0.7, cooldown=150,
                  title=f"Convite para assessorar um parlamentar da {a}",
                  text=f"Um parlamentar fictício da {a} convida você para ajudar na organização de seu mandato por algumas semanas.", fallback="recusar",
                  choices=[{"id": "aceitar", "label": "Aceitar o convite", "hint": "Aprende por dentro; custa energia.", "tone": "tecnica", "effects": {"pp:network": 3.5, "pp:standing": 2.0, "pp:reputation": 1.0, "pp:energy": -15}, "outcome": "Você aprende como o mandato funciona e amplia contatos."},
                           {"id": "recusar", "label": "Recusar", "hint": "Sem custo.", "tone": "passiva", "effects": {}, "outcome": "Nada muda por ora."}])


FAMILIES = [strikes, disasters, scandals, markets, prices, health, security, congress, opinion, infrastructure, legal, environment_and_diplomacy, militancy]


def generate_all() -> list[dict[str, Any]]:
    """Todos os eventos do catálogo base de modelos (em dados puros)."""
    out: list[dict[str, Any]] = []
    for family in FAMILIES:
        out.extend(family())
    return out
