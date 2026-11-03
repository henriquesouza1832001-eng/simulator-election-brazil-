"""Merge the official IBGE municipal GDP series into the shipped city catalog.

Run from ``backend`` with::

    python -m app.data.economic_import --zip path/to/base_de_dados_2010_2023_txt.zip

The source archive is an import-time input; game sessions never fetch it.
"""

from __future__ import annotations

import argparse
import json
import zipfile
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


CATALOG_PATH = Path(__file__).resolve().parent / "municipalities.json"
IBGE_SOURCE_URL = "https://ftp.ibge.gov.br/Pib_Municipios/2022_2023/base/base_de_dados_2010_2023_txt.zip"
IBGE_DATASET_URL = "https://www.ibge.gov.br/estatisticas/economicas/contas-nacionais/9088-produto-interno-bruto-dos-municipios.html"
GDP_YEAR = 2023
SECTOR_YEAR = 2021
KNOWN_MISSING_CODES = {"5101837"}  # Boa Esperanca do Norte was not in this source edition.

# One-based positions and lengths from the layout PDF distributed with the
# official fixed-width TXT archive.
FIELDS = {
    "year": (1, 4),
    "ibge_code": (47, 7),
    "agriculture": (821, 18),
    "industry": (840, 18),
    "services": (859, 18),
    "public_services": (878, 18),
    "value_added_total": (897, 18),
    "gdp": (935, 18),
    "gdp_per_capita": (954, 18),
}


def _field(line: str, field: str) -> str:
    position, width = FIELDS[field]
    return line[position - 1:position - 1 + width].strip()


def _decimal(raw: str, field: str, code: str) -> Decimal:
    try:
        return Decimal(raw.replace(",", "."))
    except InvalidOperation as exc:
        raise ValueError(f"Invalid IBGE value in {field} for municipality {code}: {raw!r}.") from exc


def _optional_decimal(raw: str, field: str, code: str) -> Decimal | None:
    return _decimal(raw, field, code) if raw else None


def read_economic_records(zip_path: Path, expected_codes: set[str]) -> dict[str, dict[str, Any] | None]:
    with zipfile.ZipFile(zip_path) as archive:
        text_files = [info for info in archive.infolist() if info.filename.lower().endswith(".txt")]
        if len(text_files) != 1:
            raise ValueError("The IBGE ZIP must contain exactly one TXT data file.")

        records: dict[str, dict[int, dict[str, Decimal | None]]] = {}
        with archive.open(text_files[0]) as stream:
            for raw_line in stream:
                line = raw_line.decode("latin-1").rstrip("\r\n")
                if len(line) < 971:
                    continue
                code = _field(line, "ibge_code")
                if code not in expected_codes:
                    continue
                try:
                    year = int(_field(line, "year"))
                except ValueError:
                    continue
                if year not in {GDP_YEAR, SECTOR_YEAR}:
                    continue
                by_year = records.setdefault(code, {})
                if year in by_year:
                    raise ValueError(f"Duplicate record for {code} in {year}.")
                fields = ("gdp", "gdp_per_capita") if year == GDP_YEAR else (
                    "agriculture", "industry", "services", "public_services", "value_added_total"
                )
                by_year[year] = {field: _optional_decimal(_field(line, field), field, code) for field in fields}

    missing_profiles = sorted(code for code in expected_codes if not records.get(code))
    unexpected_missing = sorted(set(missing_profiles) - KNOWN_MISSING_CODES)
    if unexpected_missing:
        raise ValueError(f"Unexpected municipalities missing from the IBGE series: {', '.join(unexpected_missing[:8])}.")

    result: dict[str, dict[str, Any] | None] = {}
    for code in expected_codes:
        by_year = records.get(code, {})
        current = by_year.get(GDP_YEAR)
        sectors = by_year.get(SECTOR_YEAR)
        shares = None
        leading_sector = None
        sector_status = "not_reported"
        if sectors:
            value_added_total = sectors["value_added_total"]
            sector_values = {key: sectors[key] for key in ("agriculture", "industry", "services", "public_services")}
            if any(value is None for value in (*sector_values.values(), value_added_total)):
                sector_status = "incomplete"
            elif value_added_total <= 0 or any(value < 0 for value in sector_values.values()):
                # Preserve official balances, but don't turn negative or
                # non-positive municipal accounts into misleading shares.
                sector_status = "not_comparable"
            elif abs(sum(sector_values.values()) - value_added_total) > Decimal("2"):
                raise ValueError(f"Setorial value-added check failed for municipality {code}.")
            else:
                shares = {
                    key: float((value / value_added_total).quantize(Decimal("0.0001")))
                    for key, value in sector_values.items()
                }
                leading_sector = max(shares, key=shares.get)
                sector_status = "available"
        if not current and not sectors:
            result[code] = None
            continue
        gdp = current.get("gdp") if current else None
        gdp_per_capita = current.get("gdp_per_capita") if current else None
        result[code] = {
            "gdp_billion_brl": float((gdp / Decimal("1000000")).quantize(Decimal("0.001"))) if gdp is not None else None,
            "gdp_per_capita_brl": float(gdp_per_capita.quantize(Decimal("0.01"))) if gdp_per_capita is not None else None,
            "gdp_reference_year": GDP_YEAR if gdp is not None else None,
            "sector_shares_2021": shares,
            "sector_reference_year": SECTOR_YEAR if sectors else None,
            "leading_sector_2021": leading_sector,
            "sector_profile_status": sector_status,
        }
    return result


def import_economic_profile(zip_path: Path) -> dict[str, Any]:
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    municipalities = catalog.get("municipalities", [])
    expected_codes = {str(item["ibge_code"]) for item in municipalities}
    if len(expected_codes) != len(municipalities) or not expected_codes:
        raise ValueError("O catálogo IBGE está vazio ou contém códigos municipais duplicados.")
    records = read_economic_records(zip_path, expected_codes)
    for item in municipalities:
        item["economic_profile"] = records[str(item["ibge_code"])]

    catalog["schema_version"] = max(3, int(catalog.get("schema_version", 1)))
    catalog.setdefault("metadata", {}).update({
        "economic_source": "IBGE, Produto Interno Bruto dos Munic\u00edpios",
        "economic_source_url": IBGE_SOURCE_URL,
        "economic_dataset_url": IBGE_DATASET_URL,
        "economic_gdp_reference_year": GDP_YEAR,
        "economic_sector_reference_year": SECTOR_YEAR,
        "economic_retrieved_at": date.today().isoformat(),
        "economic_note": "PIB e PIB per capita de 2023 sujeitos a revis\u00e3o; composi\u00e7\u00e3o setorial dispon\u00edvel at\u00e9 2021. O PIB per capita de 2023 usa popula\u00e7\u00e3o do Censo 2022 conforme nota t\u00e9cnica do IBGE.",
        "economic_profile_available_count": sum(profile is not None for profile in records.values()),
        "economic_gdp_available_count": sum(bool(profile and profile.get("gdp_reference_year")) for profile in records.values()),
        "economic_sector_comparable_count": sum(bool(profile and profile.get("sector_profile_status") == "available") for profile in records.values()),
        "economic_sector_not_comparable_count": sum(bool(profile and profile.get("sector_profile_status") == "not_comparable") for profile in records.values()),
        "economic_profile_missing_codes": sorted(code for code, profile in records.items() if profile is None),
        "municipality_count": len(municipalities),
    })
    temporary_path = CATALOG_PATH.with_suffix(".json.tmp")
    temporary_path.write_text(json.dumps(catalog, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    temporary_path.replace(CATALOG_PATH)
    return {
        "output": str(CATALOG_PATH),
        "municipality_count": len(records),
        "gdp_reference_year": GDP_YEAR,
        "sector_reference_year": SECTOR_YEAR,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Importa PIB municipal do IBGE para o catálogo do jogo.")
    parser.add_argument("--zip", required=True, type=Path, help="ZIP da base municipal do IBGE em formato TXT.")
    args = parser.parse_args()
    print(json.dumps(import_economic_profile(args.zip), ensure_ascii=False))


if __name__ == "__main__":
    main()
