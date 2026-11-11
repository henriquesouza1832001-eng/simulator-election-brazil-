"""Registro central de indicadores do país: fonte, escopo, o que os influencia e quem age sobre eles.

Cada indicador declara:
  source    "atlas" (Atlas do Desenvolvimento Humano, Censo 2010, importado), "ibge", "motor" (calculado pelo jogo) ou "estimado"
  atlas     nome da série em backend/data/atlas_municipal.json, quando existe dado real por município
  scopes    níveis em que o indicador existe: pais, regiao, uf, municipio
  better    "up" (mais é melhor), "down" (menos é melhor) ou "neutral"
  drivers   [(id do indicador que o influencia, sinal +1/-1, força 1-3)] — o grafo de influências
  levers    {cargo: instrumento} — quem pode agir diretamente e como (ver powers_catalog.py)

O grafo é a base para propagar efeitos de decisões (ex.: construir um rodoanel melhora a mobilidade, que
reduz o desemprego e eleva o PIB). Os pesos são escolhas de design, revisáveis; não são elasticidades estimadas.
"""
from __future__ import annotations

from typing import Any

DOMAINS = {
    "economia": "Economia", "fiscal": "Contas públicas", "trabalho": "Trabalho e renda", "desigualdade": "Pobreza e desigualdade",
    "educacao": "Educação", "saude": "Saúde", "saneamento": "Saneamento e moradia", "infraestrutura": "Transporte e infraestrutura",
    "seguranca": "Segurança", "ambiente": "Meio ambiente", "instituicoes": "Instituições e política", "demografia": "População",
    "externo": "Setor externo",
}
_R: list[dict[str, Any]] = []


def _i(id: str, label: str, unit: str, domain: str, scopes: str, source: str, better: str = "up", *, atlas: str | None = None,
       drivers: list[tuple[str, int, int]] | None = None, levers: dict[str, str] | None = None, note: str = "") -> None:
    _R.append({"id": id, "label": label, "unit": unit, "domain": domain, "scopes": scopes.split(","), "source": source, "better": better,
               "atlas": atlas, "drivers": [{"from": f, "sign": s, "strength": k} for f, s, k in (drivers or [])], "levers": levers or {}, "note": note})


ALL_SCOPES = "pais,regiao,uf,municipio"
# ------------------------------------------------------------------ Demografia
_i("populacao", "População", "hab.", "demografia", ALL_SCOPES, "ibge")
_i("pop_urbana", "População urbana", "%", "demografia", ALL_SCOPES, "atlas", "neutral", atlas="pop_urbana")
_i("envelhecimento", "Taxa de envelhecimento", "%", "demografia", ALL_SCOPES, "atlas", "neutral", atlas="envelhecimento", drivers=[("esperanca_vida", 1, 2), ("fecundidade", -1, 2)])
_i("fecundidade", "Taxa de fecundidade", "filhos/mulher", "demografia", ALL_SCOPES, "atlas", "neutral", atlas="fecundidade", drivers=[("educacao_superior", -1, 1), ("renda_per_capita", -1, 1)])
_i("razao_dependencia", "Razão de dependência", "%", "demografia", ALL_SCOPES, "atlas", "down", atlas="razao_dependencia", drivers=[("fecundidade", 1, 2), ("envelhecimento", 1, 2)])
# ------------------------------------------------------------------ Economia
_i("pib", "PIB", "R$ bi", "economia", ALL_SCOPES, "ibge", drivers=[("mobilidade", 1, 2), ("energia", 1, 1), ("educacao_medio", 1, 2), ("seguranca", 1, 1), ("juros", -1, 2), ("investimento_publico", 1, 2), ("confianca_institucional", 1, 1)],
   levers={"prefeito": "Obras, ISS e licenciamento", "governador": "Obras estaduais, ICMS e incentivos", "presidente": "Política econômica, crédito e investimento federal"})
_i("pib_per_capita", "PIB per capita", "R$", "economia", ALL_SCOPES, "ibge", drivers=[("pib", 1, 3), ("populacao", -1, 2)])
_i("crescimento_pib", "Crescimento do PIB", "% a.a.", "economia", "pais,regiao,uf", "motor", drivers=[("investimento_publico", 1, 2), ("juros", -1, 3), ("confianca_institucional", 1, 2), ("inflacao", -1, 1), ("mobilidade", 1, 1)],
   levers={"presidente": "Medidas econômicas, concessões e privatizações", "governador": "Incentivos e obras"})
_i("inflacao", "Inflação (IPCA)", "% a.a.", "economia", "pais", "motor", "down", drivers=[("juros", -1, 3), ("resultado_primario", 1, 1), ("cambio", 1, 2), ("salario_minimo", 1, 1)],
   levers={"presidente": "Meta no CMN, política fiscal (o BC é autônomo)"})
_i("juros", "Taxa básica de juros (Selic)", "% a.a.", "economia", "pais", "motor", "down", drivers=[("inflacao", 1, 3), ("expectativas", 1, 2), ("autonomia_bc", 1, 1)],
   levers={"presidente": "Só indiretamente: nomeia diretores do BC e fixa a meta; o BC decide a Selic"})
_i("cambio", "Câmbio (R$/US$)", "R$", "externo", "pais", "motor", "down", drivers=[("risco_pais", 1, 2), ("juros", -1, 1), ("balanca_comercial", -1, 1)])
_i("balanca_comercial", "Balança comercial", "US$ bi", "externo", "pais", "motor", drivers=[("cambio", 1, 2), ("acordos_comerciais", 1, 2)], levers={"presidente": "Acordos e tarifas"})
_i("acordos_comerciais", "Acordos comerciais em vigor", "nº", "externo", "pais", "motor", levers={"presidente": "Tratados (Congresso aprova)"})
_i("risco_pais", "Risco-país", "pontos", "externo", "pais", "motor", "down", drivers=[("divida_pib", 1, 2), ("resultado_primario", -1, 2), ("confianca_institucional", -1, 2)])
_i("estrutura_agro", "Peso da agropecuária no emprego", "%", "economia", ALL_SCOPES, "atlas", "neutral", atlas="ocup_agro")
_i("estrutura_industria", "Peso da indústria no emprego", "%", "economia", ALL_SCOPES, "atlas", "neutral", atlas="ocup_industria", levers={"prefeito": "Polos e incentivos", "governador": "Incentivos fiscais", "presidente": "Política industrial"})
_i("estrutura_servicos", "Peso dos serviços no emprego", "%", "economia", ALL_SCOPES, "atlas", "neutral", atlas="ocup_servicos")
_i("estrutura_construcao", "Peso da construção no emprego", "%", "economia", ALL_SCOPES, "atlas", "neutral", atlas="ocup_construcao", drivers=[("investimento_publico", 1, 2)])
# ------------------------------------------------------------------ Contas públicas
_i("resultado_primario", "Resultado primário", "% do PIB", "fiscal", "pais,uf,municipio", "motor", drivers=[("pib", 1, 2), ("gasto_pessoal", -1, 1), ("investimento_publico", -1, 2), ("desoneracoes", -1, 2)],
   levers={"prefeito": "Orçamento municipal", "governador": "Orçamento estadual", "presidente": "Orçamento federal e regra fiscal"})
_i("divida_pib", "Dívida pública", "% do PIB", "fiscal", "pais,uf,municipio", "motor", "down", drivers=[("resultado_primario", -1, 3), ("juros", 1, 3), ("crescimento_pib", -1, 2)], levers={"presidente": "Contas federais", "governador": "Dívida estadual (Senado autoriza)"})
_i("investimento_publico", "Investimento público", "% do PIB", "fiscal", "pais,uf,municipio", "motor", levers={"prefeito": "Obras municipais", "governador": "Obras estaduais", "presidente": "Obras e PAC"})
_i("gasto_pessoal", "Gasto com pessoal", "% da receita", "fiscal", "pais,uf,municipio", "motor", "down", levers={"prefeito": "Folha municipal (limite da LRF)", "governador": "Folha estadual", "presidente": "Folha federal"})
_i("desoneracoes", "Renúncia de receita", "% do PIB", "fiscal", "pais,uf", "motor", "down", levers={"presidente": "Desonerações (LRF exige compensação)", "governador": "Benefícios de ICMS"})
_i("carga_tributaria", "Carga tributária", "% do PIB", "fiscal", "pais,uf", "motor", "neutral", drivers=[("pib", 1, 1)], levers={"presidente": "Reforma tributária (PEC)", "governador": "ICMS", "prefeito": "IPTU e ISS"})
# ------------------------------------------------------------------ Trabalho e renda
_i("desemprego", "Desemprego", "%", "trabalho", ALL_SCOPES, "atlas", "down", atlas="desocupacao_18m", drivers=[("pib", -1, 3), ("educacao_medio", -1, 1), ("mobilidade", -1, 1), ("formalizacao", -1, 1)],
   levers={"prefeito": "Polos e qualificação", "governador": "Incentivos", "presidente": "Crédito e política econômica"})
_i("atividade", "Taxa de atividade", "%", "trabalho", ALL_SCOPES, "atlas", atlas="atividade_18m", drivers=[("educacao_medio", 1, 1), ("mobilidade", 1, 1)])
_i("formalizacao", "Formalização do trabalho", "%", "trabalho", ALL_SCOPES, "atlas", atlas="formalizacao", drivers=[("pib", 1, 1), ("educacao_medio", 1, 2)], levers={"presidente": "Legislação trabalhista", "prefeito": "Simplificação de abertura de empresas"})
_i("renda_per_capita", "Renda domiciliar per capita", "R$", "trabalho", ALL_SCOPES, "atlas", atlas="renda_per_capita", drivers=[("pib_per_capita", 1, 3), ("desemprego", -1, 2), ("salario_minimo", 1, 1), ("transferencias", 1, 2)])
_i("renda_ocupados", "Rendimento médio dos ocupados", "R$", "trabalho", ALL_SCOPES, "atlas", atlas="renda_media_ocupados", drivers=[("educacao_medio", 1, 2), ("formalizacao", 1, 1)])
_i("salario_minimo", "Salário mínimo", "R$", "trabalho", "pais", "motor", levers={"presidente": "Reajuste por decreto/lei"})
# ------------------------------------------------------------------ Pobreza e desigualdade
_i("gini", "Índice de Gini", "0 a 1", "desigualdade", ALL_SCOPES, "atlas", "down", atlas="gini", drivers=[("transferencias", -1, 3), ("educacao_medio", -1, 2), ("desemprego", 1, 2), ("saneamento_basico", -1, 1)],
   levers={"prefeito": "Habitação, tarifa social", "governador": "Políticas sociais estaduais", "presidente": "Transferências, salário mínimo, tributação"})
_i("theil", "Índice de Theil-L", "0 a 1", "desigualdade", ALL_SCOPES, "atlas", "down", atlas="theil", drivers=[("gini", 1, 3)])
_i("pobreza", "Pobreza", "%", "desigualdade", ALL_SCOPES, "atlas", "down", atlas="pobreza", drivers=[("renda_per_capita", -1, 3), ("transferencias", -1, 3), ("desemprego", 1, 2)])
_i("extrema_pobreza", "Extrema pobreza", "%", "desigualdade", ALL_SCOPES, "atlas", "down", atlas="extrema_pobreza", drivers=[("pobreza", 1, 3), ("transferencias", -1, 3)])
_i("transferencias", "Transferências de renda", "% do PIB", "desigualdade", "pais,uf,municipio", "motor", levers={"presidente": "Bolsa Família e benefícios (lei)", "prefeito": "Programas locais", "governador": "Programas estaduais"})
# ------------------------------------------------------------------ Educação
_i("educacao_analfabetismo", "Analfabetismo (15+)", "%", "educacao", ALL_SCOPES, "atlas", "down", atlas="analfabetismo_15m", drivers=[("educacao_fundamental", -1, 3)])
_i("educacao_fundamental", "Frequência líquida no fundamental", "%", "educacao", ALL_SCOPES, "atlas", atlas="freq_fundamental", levers={"prefeito": "Ensino fundamental e creches", "governador": "Ensino médio e fundamental", "presidente": "Financiamento (Fundeb) e MEC"})
_i("educacao_medio", "Frequência líquida no ensino médio", "%", "educacao", ALL_SCOPES, "atlas", atlas="freq_medio", drivers=[("educacao_fundamental", 1, 3), ("renda_per_capita", 1, 1)], levers={"governador": "Rede estadual de ensino médio", "presidente": "Novo Ensino Médio, financiamento"})
_i("educacao_superior", "Superior completo (25+)", "%", "educacao", ALL_SCOPES, "atlas", atlas="superior_25m", drivers=[("educacao_medio", 1, 3)], levers={"presidente": "Universidades federais, Fies e Prouni", "governador": "Universidades estaduais"})
_i("idhm_educacao", "IDHM — educação", "0 a 1", "educacao", ALL_SCOPES, "atlas", atlas="idhm_educacao", drivers=[("educacao_fundamental", 1, 2), ("educacao_medio", 1, 2), ("educacao_analfabetismo", -1, 2)])
_i("idhm_renda", "IDHM — renda", "0 a 1", "trabalho", ALL_SCOPES, "atlas", atlas="idhm_renda", drivers=[("renda_per_capita", 1, 3)])
_i("idhm", "IDHM (índice de desenvolvimento humano municipal)", "0 a 1", "desigualdade", ALL_SCOPES, "atlas", atlas="idhm",
   drivers=[("idhm_educacao", 1, 3), ("idhm_longevidade", 1, 3), ("idhm_renda", 1, 3)],
   levers={"prefeito": "Educação, saúde e renda locais", "governador": "Políticas estaduais", "presidente": "Políticas nacionais"})
# ------------------------------------------------------------------ Saúde
_i("esperanca_vida", "Esperança de vida", "anos", "saude", ALL_SCOPES, "atlas", atlas="esperanca_vida", drivers=[("mortalidade_infantil", -1, 3), ("saneamento_basico", 1, 2), ("saude_atencao", 1, 2), ("renda_per_capita", 1, 1)])
_i("mortalidade_infantil", "Mortalidade infantil", "por mil", "saude", ALL_SCOPES, "atlas", "down", atlas="mortalidade_infantil", drivers=[("saneamento_basico", -1, 3), ("saude_atencao", -1, 3), ("pobreza", 1, 2)])
_i("saude_atencao", "Cobertura de atenção básica", "%", "saude", "pais,uf,municipio", "estimado", levers={"prefeito": "Unidades básicas (SUS municipal)", "governador": "Hospitais estaduais", "presidente": "Financiamento do SUS e Mais Médicos"})
_i("idhm_longevidade", "IDHM — longevidade", "0 a 1", "saude", ALL_SCOPES, "atlas", atlas="idhm_longevidade", drivers=[("esperanca_vida", 1, 3)])
# ------------------------------------------------------------------ Saneamento e moradia
_i("agua_encanada", "Água encanada", "%", "saneamento", ALL_SCOPES, "atlas", atlas="agua_encanada", levers={"prefeito": "Concessão de saneamento", "governador": "Companhias estaduais", "presidente": "Marco legal (Lei 14.026/2020)"})
_i("esgoto_inadequado", "Água e esgoto inadequados", "%", "saneamento", ALL_SCOPES, "atlas", "down", atlas="agua_esgoto_inadequado", levers={"prefeito": "Redes de esgoto", "governador": "Companhias estaduais", "presidente": "Recursos federais"})
_i("saneamento_basico", "Saneamento básico (índice)", "0 a 100", "saneamento", ALL_SCOPES, "estimado", drivers=[("agua_encanada", 1, 2), ("esgoto_inadequado", -1, 3), ("coleta_lixo", 1, 1)])
_i("coleta_lixo", "Coleta de lixo urbano", "%", "saneamento", ALL_SCOPES, "atlas", atlas="coleta_lixo", levers={"prefeito": "Serviço municipal"})
_i("energia", "Energia elétrica nos domicílios", "%", "saneamento", ALL_SCOPES, "atlas", atlas="energia_eletrica", levers={"presidente": "Luz para Todos e transmissão"})
_i("adensamento", "Domicílios adensados", "%", "saneamento", ALL_SCOPES, "atlas", "down", atlas="densidade_domiciliar", levers={"prefeito": "Habitação popular", "governador": "Habitação", "presidente": "Minha Casa Minha Vida"})
# ------------------------------------------------------------------ Transporte e infraestrutura
_i("mobilidade", "Mobilidade urbana (índice)", "0 a 100", "infraestrutura", "pais,regiao,uf,municipio", "estimado", drivers=[("investimento_publico", 1, 2)],
   levers={"prefeito": "Ônibus, BRT, VLT, tarifa zero", "governador": "Metrô, trem e rodoanel", "presidente": "Rodovias e ferrovias federais"})
_i("logistica", "Custo logístico", "índice", "infraestrutura", "pais,regiao,uf", "estimado", "down", drivers=[("mobilidade", -1, 1), ("investimento_publico", -1, 2)], levers={"presidente": "Rodovias, ferrovias, portos e concessões"})
_i("conectividade", "Conectividade digital", "%", "infraestrutura", ALL_SCOPES, "estimado", levers={"presidente": "Leilões de telecom", "prefeito": "Internet pública"})
# ------------------------------------------------------------------ Segurança
_i("seguranca", "Segurança (índice)", "0 a 100", "seguranca", "pais,regiao,uf,municipio", "estimado", drivers=[("desemprego", -1, 1), ("gini", -1, 1), ("investimento_seguranca", 1, 2)],
   levers={"governador": "Polícias civil e militar", "prefeito": "Guarda municipal e iluminação", "presidente": "Polícia Federal, fundos e GLO"})
_i("homicidios", "Homicídios", "por 100 mil", "seguranca", "pais,regiao,uf,municipio", "motor", "down", drivers=[("seguranca", -1, 3), ("desemprego", 1, 1), ("gini", 1, 1)])
_i("investimento_seguranca", "Investimento em segurança", "% do orçamento", "seguranca", "pais,uf", "motor", levers={"governador": "Orçamento estadual", "presidente": "Fundo nacional"})
# ------------------------------------------------------------------ Meio ambiente
_i("desmatamento", "Desmatamento", "km²/ano", "ambiente", "pais,regiao,uf", "motor", "down", drivers=[("fiscalizacao_ambiental", -1, 3), ("estrutura_agro", 1, 1)], levers={"presidente": "Ibama, ICMBio e política florestal", "governador": "Órgãos estaduais"})
_i("fiscalizacao_ambiental", "Fiscalização ambiental", "índice", "ambiente", "pais,uf", "motor", levers={"presidente": "Orçamento e comando dos órgãos", "governador": "Órgãos estaduais"})
_i("emissoes", "Emissões de gases de efeito estufa", "Mt CO2e", "ambiente", "pais", "motor", "down", drivers=[("desmatamento", 1, 3), ("energia_limpa", -1, 2)])
_i("energia_limpa", "Participação de renováveis", "%", "ambiente", "pais", "motor", drivers=[("investimento_publico", 1, 1)], levers={"presidente": "Leilões de energia"})
# ------------------------------------------------------------------ Instituições e política
_i("aprovacao", "Aprovação do governante", "%", "instituicoes", "pais,uf,municipio", "motor", drivers=[("pib", 1, 1), ("inflacao", -1, 2), ("desemprego", -1, 2), ("seguranca", 1, 1), ("mobilidade", 1, 1), ("saude_atencao", 1, 1)])
_i("confianca_institucional", "Confiança institucional", "0 a 100", "instituicoes", "pais", "motor", drivers=[("integridade", 1, 2), ("autonomia_bc", 1, 1)])
_i("integridade", "Integridade pública", "0 a 100", "instituicoes", "pais,uf,municipio", "motor", levers={"presidente": "CGU, PF e nomeações", "governador": "Controladoria estadual", "prefeito": "Transparência municipal"})
_i("governabilidade", "Governabilidade", "0 a 100", "instituicoes", "pais,uf,municipio", "motor", drivers=[("base_legislativa", 1, 3), ("aprovacao", 1, 1)])
_i("base_legislativa", "Base no Legislativo", "%", "instituicoes", "pais,uf,municipio", "motor", drivers=[("aprovacao", 1, 1)], levers={"presidente": "Ministérios e emendas", "governador": "Secretarias", "prefeito": "Secretarias"})
_i("autonomia_bc", "Autonomia do Banco Central", "estado", "instituicoes", "pais", "motor", "up", levers={"presidente": "PLP/PEC (Congresso decide)"})
_i("expectativas", "Expectativas de inflação", "% a.a.", "economia", "pais", "motor", "down", drivers=[("confianca_institucional", -1, 2), ("resultado_primario", 1, 1)])

REGISTRY: dict[str, dict[str, Any]] = {r["id"]: r for r in _R}


def downstream(indicator_id: str) -> list[dict[str, Any]]:
    """Quem é influenciado por este indicador."""
    return [{"id": r["id"], "label": r["label"], "sign": d["sign"], "strength": d["strength"]}
            for r in _R for d in r["drivers"] if d["from"] == indicator_id]


def explain(indicator_id: str) -> dict[str, Any]:
    item = REGISTRY[indicator_id]
    return {**item, "drivers": [{**d, "label": REGISTRY[d["from"]]["label"]} for d in item["drivers"]], "influences": downstream(indicator_id),
            "domain_label": DOMAINS[item["domain"]]}


def for_office(office: str) -> list[dict[str, Any]]:
    """Indicadores sobre os quais o cargo age diretamente, com o instrumento."""
    return [{"id": r["id"], "label": r["label"], "domain": r["domain"], "instrument": r["levers"][office]} for r in _R if office in r["levers"]]


def propagate(changes: dict[str, float], depth: int = 2, decay: float = 0.35) -> dict[str, float]:
    """Efeitos de segunda ordem: cada mudança em um indicador se espalha pelos que dependem dele.

    A variação é em unidades relativas (fração do desvio): sinal x força/3 x decaimento por nível.
    Usado para estimativas e visualização; os valores absolutos vêm do motor de cada indicador.
    """
    total = dict(changes)
    frontier = dict(changes)
    for level in range(depth):
        nxt: dict[str, float] = {}
        for src, delta in frontier.items():
            for dep in downstream(src):
                amount = delta * dep["sign"] * dep["strength"] / 3 * decay
                nxt[dep["id"]] = nxt.get(dep["id"], 0.0) + amount
        for k, v in nxt.items():
            total[k] = total.get(k, 0.0) + v
        frontier = nxt
    return {k: round(v, 4) for k, v in total.items()}
