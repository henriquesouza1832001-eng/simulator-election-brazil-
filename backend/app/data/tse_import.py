"""Import TSE candidate records from the CKAN Open Data API, with provenance.

Example: python -m app.data.tse_import --years 2022 2024 2026
Only candidate CSV resources are imported. Photos, criminal certificates,
addresses and other unnecessary personal details are not copied into the game DB.
"""
import argparse
import csv
import io
import json
import zipfile
from io import BytesIO
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

import httpx

from ..db import connect

CKAN = "https://dadosabertos.tse.jus.br/api/3/action/package_show"
KEEP_FIELDS = {
    "ANO_ELEICAO", "SG_UF", "NM_UE", "DS_CARGO", "SQ_CANDIDATO", "NR_CANDIDATO",
    "NM_CANDIDATO", "NM_URNA_CANDIDATO", "SG_PARTIDO", "NM_PARTIDO", "DS_SIT_TOT_TURNO",
    "ST_REELEICAO", "DS_GENERO", "DS_GRAU_INSTRUCAO", "DS_COR_RACA", "DS_OCUPACAO",
    "DT_GERACAO", "DS_COMPOSICAO_COLIGACAO", "TP_AGREMIACAO",
}


def find_candidate_resources(year: int) -> list[dict]:
    slug = f"candidatos-{year}"
    response = httpx.get(CKAN, params={"id": slug}, timeout=30)
    response.raise_for_status()
    payload = response.json()
    if not payload.get("success"):
        raise RuntimeError(f"O catálogo do TSE não encontrou {slug}.")
    package = payload["result"]
    resources = package.get("resources", [])
    found = [r for r in resources if "csv" in str(r.get("format", "")).lower()
             and "candidato" in str(r.get("name", "")).lower()
             and "complement" not in str(r.get("name", "")).lower()]
    if not found:
        raise RuntimeError(f"O conjunto {slug} não retornou recurso CSV de candidaturas.")
    for resource in found:
        resource["_license_title"] = package.get("license_title") or package.get("license_id") or "Consulte licença no catálogo do TSE"
    return found


def candidate_rows(content: bytes) -> Iterator[dict[str, str]]:
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = content.decode("latin-1")
    reader = csv.DictReader(io.StringIO(text), delimiter=";")
    for row in reader:
        normalized = {str(k).strip().upper(): (v or "").strip() for k, v in row.items() if k}
        if normalized.get("SQ_CANDIDATO"):
            yield {key: normalized.get(key, "") for key in KEEP_FIELDS}


def import_year(year: int) -> tuple[int, list[str]]:
    rows_processed = 0
    licenses: set[str] = set()
    for resource in find_candidate_resources(year):
        url = resource.get("url")
        if not url:
            continue
        response = httpx.get(url, timeout=120, follow_redirects=True)
        response.raise_for_status()
        files = [(resource.get("name", "Candidatos") + ".csv", response.content)]
        if response.content[:2] == b"PK":
            with zipfile.ZipFile(BytesIO(response.content)) as archive:
                csv_names = [name for name in archive.namelist() if name.lower().endswith(".csv")]
                names = [name for name in csv_names if any(token in Path(name).name.lower() for token in ("consulta_cand", "candidato"))
                         and "complement" not in Path(name).name.lower()]
                if not names:
                    names = [name for name in csv_names if "brasil" in Path(name).name.lower()]
                if not names:
                    raise RuntimeError(f"O ZIP do recurso {resource.get('name')} não contém tabela principal de candidaturas.")
                files = [(name, archive.read(name)) for name in names]
        source_ref = f"https://dadosabertos.tse.jus.br/dataset/candidatos-{year}"
        license_name = resource.get("_license_title", "Consulte licença no catálogo do TSE")
        licenses.add(license_name)
        imported_at = datetime.now(timezone.utc).isoformat()
        with connect() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS tse_candidates (
                    election_year INTEGER NOT NULL,
                    candidate_id TEXT NOT NULL,
                    display_name TEXT,
                    party TEXT,
                    office TEXT,
                    state TEXT,
                    municipality TEXT,
                    result_status TEXT,
                    profile_json TEXT NOT NULL,
                    source_url TEXT NOT NULL,
                    license_name TEXT NOT NULL,
                    imported_at TEXT NOT NULL,
                    PRIMARY KEY (election_year, candidate_id)
                )
            """)
            batch = []
            statement = """
                INSERT INTO tse_candidates (election_year, candidate_id, display_name, party, office, state, municipality, result_status, profile_json, source_url, license_name, imported_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(election_year,candidate_id) DO UPDATE SET
                  display_name=excluded.display_name, party=excluded.party, office=excluded.office,
                  state=excluded.state, municipality=excluded.municipality, result_status=excluded.result_status,
                  profile_json=excluded.profile_json, source_url=excluded.source_url, license_name=excluded.license_name, imported_at=excluded.imported_at
            """
            for _filename, content in files:
                for record in candidate_rows(content):
                    batch.append((year, record.get("SQ_CANDIDATO", ""), record.get("NM_URNA_CANDIDATO") or record.get("NM_CANDIDATO"),
                                  record.get("SG_PARTIDO"), record.get("DS_CARGO"), record.get("SG_UF"), record.get("NM_UE"),
                                  record.get("DS_SIT_TOT_TURNO"), json.dumps(record, ensure_ascii=False), source_ref, license_name, imported_at))
                    if len(batch) >= 1000:
                        db.executemany(statement, batch)
                        rows_processed += len(batch)
                        batch.clear()
            if batch:
                db.executemany(statement, batch)
                rows_processed += len(batch)
    with connect() as db:
        unique_candidates = db.execute("SELECT COUNT(*) FROM tse_candidates WHERE election_year = ?", (year,)).fetchone()[0]
    return int(unique_candidates), sorted(licenses)


def main() -> None:
    parser = argparse.ArgumentParser(description="Importa dados públicos de candidaturas do TSE.")
    parser.add_argument("--years", nargs="+", type=int, required=True)
    args = parser.parse_args()
    results = {str(year): import_year(year) for year in args.years}
    counts = {year: result[0] for year, result in results.items()}
    licenses = {year: result[1] for year, result in results.items()}
    print(json.dumps({"imported_by_year": counts, "license_by_year": licenses, "source": "TSE/AGEL Open Data"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
