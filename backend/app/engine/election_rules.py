"""Calendário eleitoral e regras por ano e cargo (`ElectionRuleset`).

Princípios:
- Nada de aplicar a regra atual retroativamente: cada ano tem seu conjunto de regras.
- Só entra como regra o que tem base normativa citada. O que não foi confirmado fica em
  `pending` e **não** pode ser usado para apresentar um resultado como factual.
- Datas de 2028 e 2030 são calculadas pela regra constitucional (art. 28, art. 29 II e art. 77 da
  CF: primeiro domingo de outubro e, havendo segundo turno, último domingo de outubro).
- Este módulo descreve regras; não registra candidatos reais de pleitos futuros.

Fontes: Constituição Federal (planalto.gov.br/ccivil_03/constituicao/constituicao.htm), Lei nº 9.504/1997
(planalto.gov.br/ccivil_03/leis/l9504.htm), Emendas Constitucionais citadas em cada regra e calendário do TSE
(tse.jus.br/eleicoes/calendario-eleitoral).
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any

SOURCES = {
    "cf": "https://www.planalto.gov.br/ccivil_03/constituicao/constituicao.htm",
    "lei9504": "https://www.planalto.gov.br/ccivil_03/leis/l9504.htm",
    "tse_cal": "https://www.tse.jus.br/eleicoes/calendario-eleitoral/calendario-eleitoral",
    "tse_res": "https://www.tse.jus.br/eleicoes/resultados-eleicoes",
}

UFS = ["AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR",
       "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO"]

GENERAL_YEARS = (2014, 2018, 2022, 2026, 2030)
MUNICIPAL_YEARS = (2016, 2020, 2024, 2028)
SCENARIO_YEARS = tuple(sorted(GENERAL_YEARS + MUNICIPAL_YEARS))

# Datas conhecidas (1º e 2º turno). 2020 foi adiada pela EC 107/2020.
KNOWN_DATES: dict[int, tuple[date, date, str]] = {
    2014: (date(2014, 10, 5), date(2014, 10, 26), "Calendário do TSE; CF art. 77."),
    2016: (date(2016, 10, 2), date(2016, 10, 30), "Calendário do TSE; CF art. 29, II."),
    2018: (date(2018, 10, 7), date(2018, 10, 28), "Calendário do TSE; CF art. 77."),
    2020: (date(2020, 11, 15), date(2020, 11, 29), "Adiamento pela Emenda Constitucional nº 107/2020 (pandemia); a data ordinária seria 4 e 25 de outubro."),
    2022: (date(2022, 10, 2), date(2022, 10, 30), "Calendário do TSE; CF art. 77."),
    2024: (date(2024, 10, 6), date(2024, 10, 27), "Calendário do TSE; CF art. 29, II."),
    2026: (date(2026, 10, 4), date(2026, 10, 25), "Calendário do TSE; CF art. 77."),
}


def _nth_sunday(year: int, month: int, n: int) -> date:
    first = date(year, month, 1)
    return first + timedelta(days=(6 - first.weekday()) % 7 + 7 * (n - 1))


def _last_sunday(year: int, month: int) -> date:
    last = date(year + (month == 12), month % 12 + 1, 1) - timedelta(days=1)
    return last - timedelta(days=(last.weekday() + 1) % 7)


def election_dates(year: int) -> dict[str, Any]:
    if year in KNOWN_DATES:
        first, second, source = KNOWN_DATES[year]
        derived = False
    elif year in SCENARIO_YEARS:
        first, second = _nth_sunday(year, 10, 1), _last_sunday(year, 10)
        source = ("Calculada pela regra constitucional: primeiro domingo de outubro e, se houver 2º turno, "
                  "último domingo de outubro (CF arts. 28, 29, II e 77). Confirmar no calendário do TSE quando publicado.")
        derived = True
    else:
        raise ValueError("Ano fora do calendário do jogo.")
    return {"first_round": first.isoformat(), "second_round": second.isoformat(), "source": source, "derived_from_rule": derived}


# Cargo → (rótulo, circunscrição, mandato em anos, idade mínima, sistema). Idade: CF art. 14, §3º, VI.
OFFICES: dict[str, dict[str, Any]] = {
    "presidente": {"label": "Presidente da República", "scope": "nacional", "term": 4, "min_age": 35, "system": "majoritario_2_turnos",
                   "level": "federal", "type": "geral", "source": "CF arts. 14, §3º, VI, a; 77 e 82"},
    "governador": {"label": "Governador", "scope": "uf", "term": 4, "min_age": 30, "system": "majoritario_2_turnos",
                   "level": "estadual", "type": "geral", "source": "CF arts. 14, §3º, VI, b; 28"},
    "senador": {"label": "Senador", "scope": "uf", "term": 8, "min_age": 35, "system": "majoritario_1_turno",
                "level": "federal", "type": "geral", "source": "CF arts. 14, §3º, VI, a; 46 (mandato de 8 anos; renovação de 1/3 e 2/3)"},
    "deputado_federal": {"label": "Deputado Federal", "scope": "uf", "term": 4, "min_age": 21, "system": "proporcional",
                         "level": "federal", "type": "geral", "source": "CF arts. 14, §3º, VI, c; 45"},
    "deputado_estadual": {"label": "Deputado Estadual / Distrital", "scope": "uf", "term": 4, "min_age": 21, "system": "proporcional",
                          "level": "estadual", "type": "geral", "source": "CF arts. 14, §3º, VI, c; 27"},
    "prefeito": {"label": "Prefeito", "scope": "municipio", "term": 4, "min_age": 21, "system": "majoritario_2_turnos_acima_de_200_mil",
                 "level": "municipal", "type": "municipal", "source": "CF arts. 14, §3º, VI, c; 29, I e II"},
    "vereador": {"label": "Vereador", "scope": "municipio", "term": 4, "min_age": 18, "system": "proporcional",
                 "level": "municipal", "type": "municipal", "source": "CF arts. 14, §3º, VI, d; 29, I"},
}

# Nomes de cargo como aparecem nos arquivos do TSE.
TSE_OFFICE_NAMES = {
    "presidente": ["PRESIDENTE"], "governador": ["GOVERNADOR"], "senador": ["SENADOR"],
    "deputado_federal": ["DEPUTADO FEDERAL"], "deputado_estadual": ["DEPUTADO ESTADUAL", "DEPUTADO DISTRITAL"],
    "prefeito": ["PREFEITO"], "vereador": ["VEREADOR"],
}


def election_type(year: int) -> str:
    if year in GENERAL_YEARS:
        return "geral"
    if year in MUNICIPAL_YEARS:
        return "municipal"
    raise ValueError("Ano fora do calendário do jogo.")


def senate_renewal(year: int) -> str | None:
    """Fração do Senado renovada (CF art. 46, §2º): 1/3 e 2/3 alternadas a cada quatro anos."""
    if year not in GENERAL_YEARS:
        return None
    return "2/3 (duas vagas por estado)" if year in (2018, 2026) else "1/3 (uma vaga por estado)"


def ruleset_for(year: int) -> dict[str, Any]:
    """Conjunto de regras da eleição de `year`. Itens em `pending` ainda não foram confirmados."""
    kind = election_type(year)
    offices = {key: {k: v for k, v in info.items() if k != "type"} for key, info in OFFICES.items() if info["type"] == kind}
    rules: dict[str, Any] = {
        "year": year, "type": kind, "dates": election_dates(year), "offices": offices,
        "reelection": {"executive": "uma reeleição consecutiva (Emenda Constitucional nº 16/1997)", "source": "CF art. 14, §5º"},
        "runoff": {"majoritarian": "maioria absoluta dos votos válidos no 1º turno; senão 2º turno entre os dois mais votados"
                                   " (presidente e governador; prefeito apenas em município com mais de 200 mil eleitores)",
                   "source": "CF arts. 28, 29, II e 77"},
        "notes": [], "pending": [],
    }
    if year >= 2020:
        rules["coalitions_proportional"] = {"allowed": False, "source": "Emenda Constitucional nº 97/2017 (vedação a partir das eleições de 2020)"}
    else:
        rules["coalitions_proportional"] = {"allowed": True, "source": "Lei nº 9.504/1997 antes da Emenda Constitucional nº 97/2017"}
    rules["federations"] = {"allowed": year >= 2022, "source": "Lei nº 14.208/2021 (federações partidárias, a partir de 2022)"}
    rules["corporate_donations"] = {"allowed": year <= 2014,
                                     "source": "STF, ADI 4650 (2015): doações de empresas vedadas a partir das eleições de 2016"}
    rules["public_campaign_fund"] = {"exists": year >= 2018,
                                      "source": "Fundo Especial de Financiamento de Campanha (Lei nº 13.487/2017), usado a partir de 2018"}
    if kind == "geral":
        rules["senate_renewal"] = senate_renewal(year)
        if year >= 2026:
            rules["inauguration"] = {"president": "5 de janeiro de 2027", "governors": "6 de janeiro de 2027",
                                     "source": "Emenda Constitucional nº 111/2021 (nova data de posse a partir de 2027)"}
        else:
            rules["inauguration"] = {"president": "1º de janeiro", "governors": "1º de janeiro", "source": "CF art. 82 (redação anterior à EC 111/2021)"}
    else:
        rules["inauguration"] = {"mayors_and_councillors": "1º de janeiro do ano seguinte", "source": "CF art. 29, III"}
    if year == 2020:
        rules["notes"].append("Calendário excepcional: eleição adiada pela EC 107/2020; prazos de convenção, registro e propaganda foram deslocados.")
    if year in (2028, 2030):
        rules["notes"].append("Cenário futuro simulado: ainda não há registro oficial de candidaturas no TSE.")
    # Itens cuja redação mudou entre ciclos e que ainda não foram conferidos norma a norma.
    rules["pending"] = [
        "Prazo mínimo de filiação partidária e de domicílio eleitoral neste ciclo (alterado por leis de 2015 e 2017; conferir Lei nº 9.504/1997 art. 9 e Lei nº 9.096/1995 art. 18 na redação vigente em cada data).",
        "Limites de gastos de campanha e regras de prestação de contas deste ciclo (resoluções do TSE).",
        "Datas de convenção, registro e propaganda deste ciclo (calendário do TSE do ano).",
        "Cálculo de vagas e sobras do sistema proporcional neste ciclo (Código Eleitoral e Lei nº 9.504/1997).",
    ]
    return rules


def scenarios() -> list[dict[str, Any]]:
    out = []
    for year in SCENARIO_YEARS:
        kind = election_type(year)
        dates = election_dates(year)
        out.append({"year": year, "type": kind, "type_label": "Eleição geral" if kind == "geral" else "Eleição municipal",
                    "first_round": dates["first_round"], "second_round": dates["second_round"],
                    "future_simulated": year >= 2028, "offices": [k for k, v in OFFICES.items() if v["type"] == kind]})
    return out


def validate_selection(year: int, office: str, uf: str | None, municipality_id: str | None) -> dict[str, Any]:
    """Valida a combinação ano + cargo + território. Levanta ValueError com mensagem clara."""
    if year not in SCENARIO_YEARS:
        raise ValueError("Escolha um ano do calendário do jogo.")
    info = OFFICES.get(office)
    if not info:
        raise ValueError("Cargo desconhecido.")
    if info["type"] != election_type(year):
        raise ValueError(f"{info['label']} não é disputado em eleição {'geral' if election_type(year) == 'geral' else 'municipal'} ({year}).")
    scope = info["scope"]
    if scope == "nacional":
        return {"scope": "nacional", "uf": None, "municipality_id": None}
    if scope == "uf":
        if uf not in UFS:
            raise ValueError("Informe uma UF válida.")
        return {"scope": "uf", "uf": uf, "municipality_id": None}
    from .geography import get_municipality  # catálogo IBGE do projeto

    if not municipality_id or not str(municipality_id).isdigit() or len(str(municipality_id)) != 7:
        raise ValueError("Informe um município pelo código IBGE de 7 dígitos.")
    found = get_municipality(str(municipality_id))
    if not found:
        raise ValueError("Município não encontrado no catálogo oficial do IBGE.")
    if uf and found["state_code"] != uf:
        raise ValueError("O município não pertence à UF informada.")
    return {"scope": "municipio", "uf": found["state_code"], "municipality_id": str(municipality_id), "municipality": found["name"]}
