"""Download and version IBGE municipality identifiers and population estimates.

Run from ``backend`` with ``python -m app.data.municipality_import --year 2026``.
The game never fetches these data during a turn; imports are explicit and versioned.
"""

from __future__ import annotations

import argparse
import gzip
import json
from datetime import date
from pathlib import Path
from urllib.request import Request, urlopen


LOCALITIES_URL = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios?orderBy=nome"
POPULATION_URL = "https://servicodados.ibge.gov.br/api/v3/agregados/6579/periodos/{year}/variaveis/9324?localidades=N6%5Ball%5D"
OUTPUT_PATH = Path(__file__).resolve().parent / "municipalities.json"


def _get_json(url: str) -> object:
    request = Request(url, headers={
        "User-Agent": "MandatoSimulator/0.1 (IBGE open-data import)",
        "Accept-Encoding": "identity",
    })
    with urlopen(request, timeout=60) as response:
        body = response.read()
    if body.startswith(b"\x1f\x8b"):
        body = gzip.decompress(body)
    return json.loads(body.decode("utf-8"))


def build_catalog(year: int, retrieved_at: str | None = None) -> dict:
    locality_rows = _get_json(LOCALITIES_URL)
    population_response = _get_json(POPULATION_URL.format(year=year))
    if not isinstance(locality_rows, list) or not isinstance(population_response, list) or not population_response:
        raise ValueError("A resposta da API do IBGE veio em formato inesperado.")

    populations: dict[str, int] = {}
    for result in population_response[0].get("resultados", []):
        for row in result.get("series", []):
            population = row.get("serie", {}).get(str(year))
            if population is not None:
                populations[str(row["localidade"]["id"]).zfill(7)] = int(population)

    previous_catalog = json.loads(OUTPUT_PATH.read_text(encoding="utf-8")) if OUTPUT_PATH.exists() else {}
    previous_by_code = {
        str(item["ibge_code"]): item for item in previous_catalog.get("municipalities", [])
    }
    municipalities = []
    for row in locality_rows:
        state = row["regiao-imediata"]["regiao-intermediaria"]["UF"]
        code = str(row["id"]).zfill(7)
        if code not in populations:
            raise ValueError(f"A estimativa populacional de {code} ({row['nome']}) não foi encontrada.")
        municipality = {
            "ibge_code": code,
            "name": row["nome"],
            "state_code": state["sigla"],
            "state_name": state["nome"],
            "region_code": state["regiao"]["sigla"],
            "population_estimate": populations[code],
            "population_reference_year": year,
            "population_source": "IBGE SIDRA, tabela 6579, variável 9324",
        }
        previous = previous_by_code.get(code, {})
        if previous.get("electorate_count"):
            municipality["electorate_count"] = int(previous["electorate_count"])
            municipality["electorate_reference_year"] = int(previous["electorate_reference_year"])
        if previous.get("economic_profile"):
            municipality["economic_profile"] = previous["economic_profile"]
        municipalities.append(municipality)

    municipalities.sort(key=lambda item: (item["state_code"], item["name"].casefold(), item["ibge_code"]))
    if len(municipalities) != len(populations):
        raise ValueError(f"As APIs divergem: {len(municipalities)} municípios e {len(populations)} estimativas.")
    if len({item["ibge_code"] for item in municipalities}) != len(municipalities):
        raise ValueError("A lista do IBGE contém códigos municipais duplicados.")

    metadata = {
        "retrieved_at": retrieved_at or date.today().isoformat(),
        "population_reference_date": f"{year}-07-01",
        "population_reference_year": year,
        "population_source": "IBGE SIDRA, tabela 6579, variável 9324",
        "population_source_url": POPULATION_URL.format(year=year),
        "locality_source": "IBGE API de Localidades",
        "locality_source_url": LOCALITIES_URL,
        "license_note": "A API não declara licença por registro; preservar atribuição e URL da fonte.",
        "municipality_count": len(municipalities),
    }
    for key, value in previous_catalog.get("metadata", {}).items():
        if (key.startswith("electorate_") and key != "electorate_retrieved_at") or key.startswith("economic_"):
            metadata[key] = value
    if any(item.get("electorate_count") for item in municipalities):
        metadata["electorate_retrieved_at"] = previous_catalog.get("metadata", {}).get("electorate_retrieved_at")
    return {
        "schema_version": 3 if metadata.get("economic_source") else 2 if metadata.get("electorate_source") else 1,
        "metadata": metadata,
        "municipalities": municipalities,
    }


def import_catalog(year: int) -> dict[str, object]:
    catalog = build_catalog(year)
    OUTPUT_PATH.write_text(json.dumps(catalog, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    return {"output": str(OUTPUT_PATH), "municipality_count": len(catalog["municipalities"]),
            "population_reference_date": catalog["metadata"]["population_reference_date"]}


def main() -> None:
    parser = argparse.ArgumentParser(description="Importa localidades e população municipal do IBGE.")
    parser.add_argument("--year", type=int, default=2026)
    args = parser.parse_args()
    print(json.dumps(import_catalog(args.year), ensure_ascii=False))


if __name__ == "__main__":
    main()
