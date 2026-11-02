"""Fixed cabinet catalogue based on the federal SIORG snapshot (2026-11-01).

The budget values below are a game abstraction for discretionary investment allocations,
not a claim about the enacted federal budget.
"""

MINISTRIES = [
    "Agricultura e Pecuária", "Cidades", "Ciência, Tecnologia e Inovação", "Comunicações",
    "Cultura", "Defesa", "Desenvolvimento Agrário e Agricultura Familiar",
    "Empreendedorismo, da Microempresa e da Empresa de Pequeno Porte", "Esporte",
    "Pesca e Aquicultura", "Desenvolvimento e Assistência Social, Família e Combate à Fome",
    "Desenvolvimento, Indústria, Comércio e Serviços", "Direitos Humanos e Cidadania",
    "Educação", "Fazenda", "Gestão e Inovação em Serviços Públicos", "Igualdade Racial",
    "Integração e Desenvolvimento Regional", "Justiça e Segurança Pública",
    "Meio Ambiente e Mudança do Clima", "Minas e Energia", "Mulheres",
    "Planejamento e Orçamento", "Previdência Social", "Portos e Aeroportos",
    "Povos Indígenas", "Relações Exteriores", "Saúde", "Trabalho e Emprego",
    "Transportes", "Turismo",
]

# Narrow investment portfolio used by the simplified budget panel. Values are annual
# game units in R$ bi and total R$ 100 bi; investment transfers must remain budget neutral.
INVESTMENT_AREAS = {
    "education": {"label": "Educação", "ministry": "Educação", "budget": 18.0, "lag_days": 240, "effects": {"education": 1.2, "gdp_growth": 0.08}},
    "health": {"label": "Saúde", "ministry": "Saúde", "budget": 20.0, "lag_days": 180, "effects": {"health": 1.0, "approval": 0.4}},
    "security": {"label": "Segurança pública", "ministry": "Justiça e Segurança Pública", "budget": 12.0, "lag_days": 180, "effects": {"security": 1.2, "approval": 0.2}},
    "sanitation": {"label": "Saneamento", "ministry": "Cidades", "budget": 12.0, "lag_days": 360, "effects": {"health": 0.3, "gdp_growth": 0.06}},
    "logistics": {"label": "Transportes e logística", "ministry": "Transportes", "budget": 20.0, "lag_days": 240, "effects": {"infrastructure": 1.4, "gdp_growth": 0.12}},
    "science": {"label": "Ciência e inovação", "ministry": "Ciência, Tecnologia e Inovação", "budget": 10.0, "lag_days": 360, "effects": {"productivity": 1.0, "gdp_growth": 0.1}},
    "agriculture": {"label": "Agricultura familiar e resiliência rural", "ministry": "Desenvolvimento Agrário e Agricultura Familiar", "budget": 8.0, "lag_days": 180, "effects": {"rural_resilience": 1.2, "gdp_growth": 0.08}},
}


def ministry_catalog() -> list[dict[str, str]]:
    return [{"name": name, "type": "ministry", "source": "SIORG 2026-11-01"} for name in MINISTRIES]
