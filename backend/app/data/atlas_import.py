"""Importa IDHM, Gini e saneamento municipais (Censo 2010, Atlas do Desenvolvimento Humano) via Ipeadata.

Fonte: Ipeadata (séries ADH_IDHM, ADH_GINI, ADH_T_BANAGUA) com dados do Atlas Brasil/PNUD-IPEA-FJP.
Saída: backend/data/atlas_municipal.json. Uso: python -m app.data.atlas_import
"""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

BASE = "http://www.ipeadata.gov.br/api/odata4/ValoresSerie(SERCODIGO='{code}')"
SERIES = {
    "idhm": "ADH_IDHM", "idhm_educacao": "ADH_IDHM_E", "idhm_longevidade": "ADH_IDHM_L", "idhm_renda": "ADH_IDHM_R",
    "esperanca_vida": "ADH_ESPVIDA", "mortalidade_infantil": "ADH_MORT1", "fecundidade": "ADH_FECTOT",
    "razao_dependencia": "ADH_RAZDEP", "envelhecimento": "ADH_T_ENV", "pop_urbana": "ADH_PESOURB", "pop_rural": "ADH_PESORUR",
    "analfabetismo_15m": "ADH_T_ANALF15M", "freq_fundamental": "ADH_T_FLFUND", "freq_medio": "ADH_T_FLMED", "superior_25m": "ADH_T_SUPER25M",
    "agua_encanada": "ADH_T_AGUA", "agua_esgoto_inadequado": "ADH_T_AGUA_ESGOTO", "coleta_lixo": "ADH_T_LIXO", "energia_eletrica": "ADH_T_LUZ", "densidade_domiciliar": "ADH_T_DENS",
    "formalizacao": "ADH_P_FORMAL", "ocup_agro": "ADH_P_AGRO", "ocup_industria": "ADH_P_TRANSF", "ocup_servicos": "ADH_P_SERV", "ocup_comercio": "ADH_P_COM", "ocup_construcao": "ADH_P_CONSTR",
    "renda_media_ocupados": "ADH_RENOCUP", "renda_per_capita": "ADH_RDPC", "gini": "ADH_GINI", "theil": "ADH_THEIL",
    "extrema_pobreza": "ADH_PIND", "pobreza": "ADH_PMPOB", "desocupacao_18m": "ADH_T_DES18M", "atividade_18m": "ADH_T_ATIV18M",
}
OUT = Path(__file__).resolve().parents[2] / "data" / "atlas_municipal.json"


def _fetch(url: str) -> dict:
    with urllib.request.urlopen(urllib.request.Request(url, headers={"Accept": "application/json"}), timeout=120) as r:
        return json.load(r)


def collect(year: int = 2010) -> dict:
    out: dict[str, dict[str, float]] = {}
    for key, code in SERIES.items():
        query = urllib.parse.quote(f"VALDATA ge {year}-01-01T00:00:00-03:00 and VALDATA le {year}-12-31T00:00:00-01:00 and NIVNOME eq 'Municípios'", safe="'= ")
        url = BASE.format(code=code) + "?$filter=" + query.replace(" ", "%20")
        while url:
            page = _fetch(url)
            for row in page.get("value", []):
                if row["VALVALOR"] is not None and row["VALDATA"].startswith(str(year)):
                    out.setdefault(row["TERCODIGO"], {})[key] = float(row["VALVALOR"])
            url = page.get("@odata.nextLink")
    return {"collected_on": date.today().isoformat(), "reference_year": year,
            "source": "Ipeadata / Atlas do Desenvolvimento Humano no Brasil (PNUD, Ipea, FJP), Censo 2010",
            "series": SERIES, "municipalities": out}


if __name__ == "__main__":
    data = collect()
    OUT.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    print(len(data["municipalities"]), "municípios ->", OUT)
