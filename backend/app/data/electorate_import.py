"""Merge TSE's 2026 first-round registered electorate into the IBGE catalog.

The game ships the small, aggregated municipality catalog. The much larger TSE
archive is an import-time input and is never downloaded while playing.

Run from ``backend`` with::

    python -m app.data.electorate_import --zip path/to/eleitorado_local_votacao_2026.zip
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
import unicodedata
import zipfile
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any


CATALOG_PATH = Path(__file__).resolve().parent / "municipalities.json"
TSE_SOURCE = "TSE/AGEL, Eleitorado por local de votação 2026 (1º turno)"
TSE_SOURCE_URL = "https://cdn.tse.jus.br/estatistica/sead/odsele/eleitorado_locais_votacao/eleitorado_local_votacao_2026.zip"
TSE_DATASET_URL = "https://dadosabertos.tse.jus.br/dataset/eleitorado-2026"
UF_CODES = {
    "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG", "MS", "MT",
    "PA", "PB", "PE", "PI", "PR", "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO",
}
TSE_NAME_ALIASES = {
    # TSE names occasionally retain local/historical spellings; map only known,
    # one-to-one cases and keep the UF in the key to avoid cross-state matches.
    ("SE", "amparo de sao francisco"): "amparo do sao francisco",
    ("RN", "boa saude"): "januario cicco",  # IBGE municipality name; Boa Saúde is the former toponym.
    ("PR", "munhoz de mello"): "munhoz de melo",
    ("RO", "espigao do oeste"): "espigao d oeste",
    ("SP", "sao luis do paraitinga"): "sao luiz do paraitinga",
    ("MG", "sao thome das letras"): "sao tome das letras",
    ("PA", "eldorado dos carajas"): "eldorado do carajas",
    ("MT", "santo antonio do leverger"): "santo antonio de leverger",
    ("RO", "alvorada do oeste"): "alvorada d oeste",
    ("MG", "dona eusebia"): "dona euzebia",
    ("MG", "barao de monte alto"): "barao do monte alto",
    ("GO", "bom jesus"): "bom jesus de goias",
    ("RR", "sao luiz"): "sao luiz do anaua",
}


def _normalize(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", value.casefold())
    ascii_name = "".join(char for char in decomposed if unicodedata.category(char) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", ascii_name).strip()


def _read_catalog() -> dict[str, Any]:
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def aggregate_electorate(zip_path: Path, catalog: dict[str, Any]) -> dict[str, int]:
    municipality_by_name = {
        (item["state_code"], _normalize(item["name"])): str(item["ibge_code"])
        for item in catalog["municipalities"]
    }
    municipality_names_by_state: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for (state_code, normalized_name), ibge_code in municipality_by_name.items():
        municipality_names_by_state[state_code].append((normalized_name, ibge_code))
    total_by_code: dict[str, int] = defaultdict(int)
    seen_states: set[str] = set()
    unmapped: set[tuple[str, str]] = set()

    with zipfile.ZipFile(zip_path) as archive:
        state_files = []
        for info in archive.infolist():
            match = re.fullmatch(r"eleitorado_local_votacao_2026_([A-Z]{2})\.csv", Path(info.filename).name)
            if match and match.group(1) in UF_CODES:
                state_files.append((match.group(1), info))
        for state_code, info in state_files:
            seen_states.add(state_code)
            with archive.open(info) as binary_stream:
                text_stream = io.TextIOWrapper(binary_stream, encoding="latin-1", newline="")
                reader = csv.DictReader(text_stream, delimiter=";")
                required = {"NR_TURNO", "SG_UF", "NM_MUNICIPIO", "DS_SITU_SECAO", "QT_ELEITOR_SECAO"}
                if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
                    raise ValueError(f"Cabeçalho inesperado no arquivo TSE {info.filename}.")
                for row in reader:
                    if row["NR_TURNO"].strip() != "1" or _normalize(row["DS_SITU_SECAO"]) != "ativo":
                        continue
                    row_state = row["SG_UF"].strip().upper()
                    name = row["NM_MUNICIPIO"].strip()
                    normalized_name = _normalize(name)
                    normalized_name = TSE_NAME_ALIASES.get((row_state, normalized_name), normalized_name)
                    key = (row_state, normalized_name)
                    ibge_code = municipality_by_name.get(key)
                    if not ibge_code:
                        prefix_matches = {
                            code for municipality_name, code in municipality_names_by_state[row_state]
                            if municipality_name.startswith(normalized_name + " ")
                            or normalized_name.startswith(municipality_name + " ")
                        }
                        if len(prefix_matches) == 1:
                            ibge_code = prefix_matches.pop()
                    if not ibge_code:
                        unmapped.add((row_state, name))
                        continue
                    try:
                        count = int(row["QT_ELEITOR_SECAO"].strip())
                    except (TypeError, ValueError) as exc:
                        raise ValueError(f"Quantidade de eleitores inválida para {name}/{row_state}.") from exc
                    if count < 0:
                        raise ValueError(f"Quantidade negativa de eleitores para {name}/{row_state}.")
                    total_by_code[ibge_code] += count
                text_stream.detach()

    expected_states = {item["state_code"] for item in catalog["municipalities"]}
    if seen_states != expected_states:
        missing = sorted(expected_states - seen_states)
        raise ValueError(f"Arquivos estaduais do TSE ausentes: {', '.join(missing)}.")
    if unmapped:
        examples = ", ".join(f"{name}/{uf}" for uf, name in sorted(unmapped)[:8])
        raise ValueError(f"Municípios do TSE sem correspondência IBGE ({len(unmapped)}): {examples}.")
    expected_codes = {str(item["ibge_code"]) for item in catalog["municipalities"]}
    if set(total_by_code) != expected_codes:
        missing = sorted(expected_codes - set(total_by_code))
        raise ValueError(f"Eleitorado ausente em {len(missing)} municípios: {', '.join(missing[:8])}.")
    nationwide_total = sum(total_by_code.values())
    if not 80_000_000 <= nationwide_total <= 180_000_000:
        raise ValueError(f"Total nacional fora da faixa esperada: {nationwide_total:,}.")
    return dict(total_by_code)


def import_electorate(zip_path: Path) -> dict[str, Any]:
    catalog = _read_catalog()
    totals = aggregate_electorate(zip_path, catalog)
    for item in catalog["municipalities"]:
        item["electorate_count"] = totals[str(item["ibge_code"])]
        item["electorate_reference_year"] = 2026

    catalog["schema_version"] = 2
    catalog["metadata"].update({
        "electorate_source": TSE_SOURCE,
        "electorate_source_url": TSE_SOURCE_URL,
        "electorate_dataset_url": TSE_DATASET_URL,
        "electorate_reference_year": 2026,
        "electorate_reference_date": "2026-10-04",
        "electorate_license": "Creative Commons Attribution (CC BY); atribuir ao TSE/AGEL.",
        "electorate_retrieved_at": date.today().isoformat(),
        "municipality_count": len(catalog["municipalities"]),
    })
    temporary_path = CATALOG_PATH.with_suffix(".json.tmp")
    temporary_path.write_text(json.dumps(catalog, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    temporary_path.replace(CATALOG_PATH)
    return {
        "output": str(CATALOG_PATH),
        "municipality_count": len(totals),
        "electorate_reference_date": "2026-10-04",
        "nationwide_electorate": sum(totals.values()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Importa eleitores aptos por município a partir do arquivo público do TSE.")
    parser.add_argument("--zip", required=True, type=Path, help="Arquivo ZIP do TSE: Eleitorado por local de votação 2026.")
    args = parser.parse_args()
    print(json.dumps(import_electorate(args.zip), ensure_ascii=False))


if __name__ == "__main__":
    main()
