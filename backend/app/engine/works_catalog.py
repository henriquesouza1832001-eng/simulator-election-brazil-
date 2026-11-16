"""Catálogo ampliado de projetos do governo federal (aba Projetos).

Os nomes de programas são fictícios; os tipos de obra, os prazos e as ordens de grandeza de custo vêm de projetos
públicos reais de porte parecido. Valores em R$ bilhões de 2027, como parâmetros de design e não como orçamento.
`area` diz de qual carteira do orçamento de investimento o projeto é pago (ver ministries.INVESTMENT_AREAS).
`delivery` são efeitos nacionais aplicados na entrega, em pontos; `effects` são efeitos regionais.
"""
from __future__ import annotations

from typing import Any

AREA_LABEL = {"logistics": "Transportes e logística", "sanitation": "Saneamento e cidades", "health": "Saúde", "education": "Educação",
              "security": "Segurança pública", "science": "Ciência, tecnologia e espaço", "agriculture": "Agricultura e resiliência rural"}
CATEGORY_OF_AREA = {"logistics": "Transportes", "sanitation": "Cidades e saneamento", "health": "Saúde", "education": "Educação",
                    "security": "Segurança e defesa", "science": "Espaço e ciência", "agriculture": "Energia e campo"}
SPACE_PHASES = ["Projeto e acordos", "Construção", "Testes em solo", "Lançamento e operação"]


def _w(name: str, kind: str, route: str, regions: list[str], cost: float, days: int, risk: float, area: str, description: str,
       infra: float = 1.0, eco: float = 0.8, delivery: dict[str, float] | None = None, category: str | None = None,
       phases: list[str] | None = None, delivered: str | None = None) -> dict[str, Any]:
    item: dict[str, Any] = {"name": name, "kind": kind, "route": route, "regions": regions, "base_cost_bi": cost, "duration_days": days,
                            "risk": risk, "description": description, "effects": {"infrastructure": infra, "economic_activity": eco},
                            "area": area, "category": category or CATEGORY_OF_AREA[area], "delivery": delivery or {}}
    if phases:
        item["phases"] = phases
    if delivered:
        item["delivered_text"] = delivered
    return item


EXTRA_WORKS: dict[str, dict[str, Any]] = {
    # Transportes
    "ponte_amazonica": _w("Ponte da Integração Amazônica", "Ponte", "Rio Amazonas · Norte", ["norte"], 8.0, 1460, 0.20, "logistics",
                          "Travessia de grande vão sobre o rio, com acessos e balsas de transição. Licença ambiental exigente.", 2.2, 1.0, {"approval": 0.4}),
    "viaduto_metropolitano": _w("Viadutos e alças do anel metropolitano", "Viaduto", "Região metropolitana · Sudeste", ["sudeste"], 2.4, 730, 0.10, "logistics",
                                "Conjunto de viadutos e alças para desfazer gargalos de trânsito.", 1.0, 0.6, {"approval": 0.3}),
    "anel_rodoviario": _w("Anel rodoviário da capital", "Rodovia", "Anel viário · Centro-Oeste", ["centro_oeste"], 9.0, 1095, 0.12, "logistics",
                          "Contorno que tira o tráfego pesado do centro urbano.", 1.6, 1.0),
    "metro_capital": _w("Metrô de capital metropolitana", "Metrô", "Linha estrutural · Nordeste", ["nordeste"], 22.0, 1825, 0.22, "logistics",
                        "Linha de metrô com estações, pátio e sistemas. É o tipo de obra que mais atrasa e mais aumenta o custo.", 2.4, 1.4, {"approval": 0.8}),
    "brt_corredores": _w("Corredores de ônibus de alta capacidade", "BRT", "Corredores urbanos · várias regiões", ["sudeste", "nordeste"], 3.2, 730, 0.09, "logistics",
                         "Faixas exclusivas, estações e terminais. Entrega rápida e efeito imediato na mobilidade.", 1.0, 0.6, {"approval": 0.5}),
    "aeroporto_regional": _w("Aeroporto internacional regional", "Aeroporto", "Hub regional · Nordeste", ["nordeste"], 4.0, 1095, 0.12, "logistics",
                             "Terminal de passageiros e carga, pista ampliada e área de apoio.", 1.4, 1.2),
    "porto_aguas_profundas": _w("Porto de águas profundas", "Porto", "Terminal em mar aberto · Nordeste", ["nordeste"], 14.0, 1460, 0.16, "logistics",
                                "Terminal para navios de grande calado e retroárea industrial.", 2.2, 1.8),
    "ferrovia_do_grao": _w("Ferrovia do Grão", "Ferrovia", "Mato Grosso ao Pará · Centro-Oeste e Norte", ["centro_oeste", "norte"], 30.0, 2190, 0.24, "logistics",
                           "Corredor ferroviário para escoar a safra pelo Norte. Exige licenças, desapropriações e consulta a comunidades.", 3.0, 2.2),
    # Saneamento e cidades
    "drenagem_sul": _w("Drenagem urbana e contenção de enchentes", "Drenagem", "Bacias urbanas · Sul", ["sul"], 16.0, 1460, 0.14, "sanitation",
                       "Canais, reservatórios de amortecimento e proteção de áreas baixas. Reduz o efeito da próxima chuva forte.", 1.8, 0.8, {"approval": 0.6}),
    "adutoras_semiarido": _w("Adutoras e dessalinização do Semiárido", "Água", "Adutoras · Nordeste", ["nordeste"], 11.0, 1460, 0.14, "sanitation",
                             "Adutoras, poços e dessalinizadores para cidades que dependem de carro-pipa.", 1.6, 0.9, {"approval": 0.7}),
    "habitacao_popular": _w("Habitação popular em larga escala", "Habitação", "Conjuntos habitacionais · todo o país", ["sudeste", "nordeste", "sul"], 40.0, 1460, 0.15, "sanitation",
                            "Meio milhão de moradias com infraestrutura básica, em parceria com estados e municípios.", 1.2, 2.0, {"approval": 1.2}, "Cidades e saneamento"),
    "retrofit_predios": _w("Reforma e eficiência dos prédios públicos", "Reforma", "Prédios federais · todo o país", ["centro_oeste", "sudeste"], 5.0, 730, 0.06, "sanitation",
                           "Reforma de fachadas, elétrica e climatização. Gera economia contínua de energia.", 0.6, 0.5, {"integrity": 0.3}, "Reformas"),
    "centros_historicos": _w("Revitalização de centros históricos", "Reforma", "Centros históricos · Nordeste e Sudeste", ["nordeste", "sudeste"], 3.0, 730, 0.07, "sanitation",
                             "Restauro de casarios e espaços públicos, com impulso ao turismo local.", 0.5, 0.9, {"approval": 0.3}, "Reformas"),
    # Saúde
    "hospitais_regionais": _w("Hospitais federais regionais", "Hospital", "Hospitais de referência · interior", ["norte", "nordeste", "centro_oeste"], 9.0, 1095, 0.12, "health",
                              "Hospitais de média e alta complexidade em regiões sem atendimento especializado.", 1.0, 0.8, {"approval": 1.0}),
    "rede_upas": _w("Rede de UPAs e policlínicas", "Hospital", "Unidades de pronto atendimento · todo o país", ["sudeste", "nordeste", "sul"], 6.0, 730, 0.08, "health",
                    "Unidades que desafogam os prontos-socorros e atendem perto de casa.", 0.8, 0.6, {"approval": 0.8}),
    "complexo_vacinas": _w("Complexo industrial de vacinas e insumos", "Indústria", "Polo biotecnológico · Sudeste", ["sudeste"], 7.0, 1460, 0.14, "health",
                           "Fábrica nacional de vacinas e insumos, para depender menos de importação em uma emergência.", 0.8, 1.0, {"approval": 0.5, "institutional_trust": 0.4}),
    # Educação
    "escolas_tempo_integral": _w("Escolas em tempo integral", "Escola", "Escolas · todo o país", ["sudeste", "nordeste", "sul"], 18.0, 1460, 0.10, "education",
                                 "Ampliação e reforma de escolas para oferecer jornada integral.", 0.8, 0.8, {"approval": 0.9}),
    "creches": _w("Creches e pré-escolas", "Escola", "Creches · todo o país", ["sudeste", "nordeste", "norte"], 12.0, 1095, 0.09, "education",
                  "Vagas para a primeira infância, que libera famílias para o trabalho.", 0.7, 1.0, {"approval": 0.8}),
    "universidades_interior": _w("Universidades e institutos no interior", "Universidade", "Campi · interior", ["norte", "centro_oeste", "nordeste"], 10.0, 1460, 0.10, "education",
                                 "Novos campi e institutos técnicos fora das capitais.", 0.9, 1.0, {"approval": 0.4}),
    # Segurança e defesa
    "fronteira_integrada": _w("Monitoramento integrado da fronteira", "Defesa", "Faixa de fronteira · Norte e Centro-Oeste", ["norte", "centro_oeste"], 12.0, 1825, 0.16, "security",
                              "Radares, bases e sensores para vigiar mais de 16 mil km de fronteira terrestre.", 0.8, 0.5, {"institutional_trust": 0.3}),
    "presidios_federais": _w("Sistema penitenciário federal ampliado", "Presídio", "Unidades federais · várias regiões", ["centro_oeste", "norte"], 6.0, 1095, 0.14, "security",
                             "Vagas de segurança máxima e de ressocialização, com monitoramento integrado.", 0.5, 0.3),
    # Energia e campo
    "usina_hidreletrica": _w("Usina hidrelétrica de grande porte", "Energia", "Rio de planalto · Norte", ["norte"], 28.0, 2190, 0.26, "agriculture",
                             "Barragem, casa de força e linhas de escoamento. Exige licença e compensação a comunidades.", 2.6, 2.4, {"approval": 0.4}, "Energia e campo"),
    "eolica_offshore": _w("Parque eólico no mar", "Energia", "Costa · Nordeste e Sul", ["nordeste", "sul"], 25.0, 1825, 0.20, "agriculture",
                          "Turbinas em mar aberto e cabo submarino. Tecnologia nova, custo alto e potencial enorme.", 2.0, 2.0, {}, "Energia e campo"),
    "linhao_transmissao": _w("Linhão de transmissão Norte-Sul", "Energia", "Linha de alta tensão · Norte ao Sudeste", ["norte", "sudeste"], 15.0, 1460, 0.15, "agriculture",
                             "Mais de 2.000 km de linha para reduzir apagões e escoar energia renovável.", 1.8, 1.6, {"institutional_trust": 0.3}, "Energia e campo"),
    "irrigacao_sao_francisco": _w("Irrigação e perímetros do Rio São Francisco", "Irrigação", "Perímetros irrigados · Nordeste", ["nordeste"], 10.0, 1460, 0.13, "agriculture",
                                  "Canais e perímetros para a agricultura familiar e a fruticultura.", 1.2, 1.6, {"approval": 0.5}, "Energia e campo"),
    # Espaço e ciência
    "alcantara_comercial": _w("Centro de Lançamentos de Alcântara: base comercial", "Espaço", "Alcântara (MA) · Nordeste", ["nordeste"], 12.0, 2190, 0.22, "science",
                              "Plataformas, torre de integração e estrada de acesso para lançamentos comerciais do Brasil e de parceiros. Exige consulta às comunidades quilombolas do entorno e acordos de salvaguarda tecnológica.",
                              1.8, 1.6, {"approval": 0.6, "institutional_trust": 0.3}, "Espaço e ciência", SPACE_PHASES,
                              "O Centro de Alcântara fez o primeiro lançamento comercial da base ampliada."),
    "satelites_nacionais": _w("Constelação nacional de satélites", "Espaço", "Órbita baixa · todo o país", ["sudeste", "nordeste"], 9.0, 1460, 0.20, "science",
                              "Satélites de observação da Amazônia, comunicações e clima, fabricados em parceria com a indústria nacional.", 1.2, 1.4, {"institutional_trust": 0.4}, "Espaço e ciência", SPACE_PHASES,
                              "A constelação nacional entrou em operação e passou a monitorar o território."),
    "astronauta_orbita": _w("Programa Astronauta Brasileiro: missão em órbita", "Espaço", "Estação em órbita · parceria internacional", ["sudeste", "nordeste"], 35.0, 2555, 0.28, "science",
                            "Treino de astronautas, acordo com agência parceira e voo tripulado de um brasileiro à órbita. Depende do Centro de Lançamentos e de acordos internacionais.",
                            1.0, 1.8, {"approval": 3.0, "institutional_trust": 1.0}, "Espaço e ciência", SPACE_PHASES,
                            "Um brasileiro foi ao espaço e voltou. A missão virou orgulho nacional."),
    "missao_lunar": _w("Missão Lunar Brasileira", "Espaço", "Lua · cooperação internacional", ["sudeste", "nordeste"], 150.0, 4380, 0.40, "science",
                       "Foguete, módulo de pouso e treino de tripulação para levar um brasileiro à Lua com parceiros. Projeto de duas décadas na vida real; aqui, de 12 anos. Custa mais que a carteira anual de ciência e exige remanejar orçamento.",
                       1.5, 2.5, {"approval": 6.0, "institutional_trust": 2.0}, "Espaço e ciência", SPACE_PHASES,
                       "Um brasileiro pisou na Lua. O país parou para assistir."),
    "reator_pesquisa": _w("Reator multipropósito de pesquisa", "Ciência", "Centro nuclear · Sudeste", ["sudeste"], 5.0, 1460, 0.18, "science",
                          "Reator para radiofármacos e pesquisa, com licença nuclear e controle internacional.", 0.8, 1.0, {"institutional_trust": 0.3}, "Espaço e ciência"),
    "supercomputador": _w("Supercomputador nacional", "Ciência", "Centro de dados · Sudeste", ["sudeste"], 2.5, 730, 0.08, "science",
                          "Capacidade de simulação para clima, saúde e indústria.", 0.5, 0.8, {"institutional_trust": 0.2}, "Espaço e ciência"),
}
