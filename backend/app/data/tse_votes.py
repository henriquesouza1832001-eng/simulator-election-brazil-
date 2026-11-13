"""Importa votos nominais por candidato do TSE (arquivo "Votação nominal por município e zona").

- Fonte: catálogo CKAN do TSE, recurso "Votação nominal por município e zona" de cada ano (arquivo
  `votacao_candidato_munzona_AAAA.zip`). O download é feito no servidor, em disco temporário, com SHA-256.
- Agrega as zonas: guarda votos por candidato e município (prefeito, vereador, presidente, governador e senador) ou por
  candidato e UF (deputados). Os votos são NOMINAIS: brancos e nulos não entram, então a participação é sobre votos nominais.
- Não copia dados pessoais; junte com `tse_candidacies` por (ano, sq_candidato) para nome, partido e situação.

Exemplo: python -m app.data.tse_votes --years 2016 2020 2024
Anos gerais (2014, 2018, 2022) têm arquivos de 400 a 600 MB; rode no servidor, não no navegador.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import httpx

from ..db import connect

CKAN = "https://dadosabertos.tse.jus.br/api/3/action/package_show"
RESOURCE_NAME = "votação nominal por município e zona"
MUNICIPAL_LEVEL = {"1", "3", "5", "11", "13"}   # presidente, governador, senador, prefeito, vereador (código de cargo do TSE)
# vereador (13) existe como código de cargo municipal; deputados gerais (6, 7, 8) ficam por UF

DDL = """
CREATE TABLE IF NOT EXISTS tse_votes (
    election_year INTEGER NOT NULL,
    round INTEGER NOT NULL,
    office_code TEXT NOT NULL,
    uf TEXT NOT NULL,
    cd_municipio TEXT NOT NULL,
    sq_candidato TEXT NOT NULL,
    votes INTEGER NOT NULL,
    PRIMARY KEY (election_year, round, office_code, uf, cd_municipio, sq_candidato)
);
CREATE INDEX IF NOT EXISTS idx_votes_territory ON tse_votes (election_year, office_code, uf, cd_municipio, round);
"""
IMPORT_RUNS_DDL = """
CREATE TABLE IF NOT EXISTS tse_import_runs (
    election_year INTEGER NOT NULL, file_name TEXT NOT NULL, file_sha256 TEXT NOT NULL, source_url TEXT NOT NULL,
    license_name TEXT NOT NULL, rows_read INTEGER NOT NULL, rows_kept INTEGER NOT NULL, rows_discarded INTEGER NOT NULL,
    collected_at TEXT NOT NULL, PRIMARY KEY (election_year, file_sha256)
);
"""


def ensure_schema() -> None:
    with connect() as db:
        db.executescript(DDL + IMPORT_RUNS_DDL)


def find_resource(year: int) -> dict:
    response = httpx.get(CKAN, params={"id": f"resultados-{year}"}, timeout=40)
    response.raise_for_status()
    payload = response.json()
    if not payload.get("success"):
        raise RuntimeError(f"O catálogo do TSE não encontrou resultados-{year}.")
    package = payload["result"]
    found = [r for r in package.get("resources", []) if str(r.get("name", "")).strip().lower().startswith(RESOURCE_NAME)
             and str(r.get("url", "")).lower().endswith(".zip")]
    if len(found) != 1:
        raise RuntimeError(f"resultados-{year}: esperava um recurso '{RESOURCE_NAME}' em ZIP, achei {len(found)}.")
    resource = dict(found[0])
    resource["_license"] = package.get("license_title") or package.get("license_id") or "Consulte a licença no catálogo do TSE"
    return resource


def download(url: str, target: Path) -> str:
    digest = hashlib.sha256()
    with httpx.stream("GET", url, timeout=600, follow_redirects=True) as response:
        response.raise_for_status()
        with target.open("wb") as handle:
            for chunk in response.iter_bytes(1 << 20):
                handle.write(chunk)
                digest.update(chunk)
    return digest.hexdigest()


def pick_members(archive: zipfile.ZipFile) -> list[str]:
    names = [n for n in archive.namelist() if n.lower().endswith((".csv", ".txt")) and "votacao_candidato_munzona" in Path(n).name.lower()]
    brasil = [n for n in names if "brasil" in Path(n).name.lower()]
    return brasil or names


def _col(row: dict[str, str], *aliases: str) -> str:
    for a in aliases:
        v = row.get(a)
        if v not in (None, ""):
            return v.strip()
    return ""


def aggregate(archive: zipfile.ZipFile, members: list[str], year: int) -> tuple[dict[tuple, int], int, int]:
    totals: dict[tuple, int] = {}
    read = discarded = 0
    for member in members:
        with archive.open(member) as raw:
            reader = csv.DictReader(io.TextIOWrapper(raw, encoding="latin-1", newline=""), delimiter=";", quotechar='"')
            for row in reader:
                read += 1
                r = {str(k).strip().upper(): v for k, v in row.items() if k}
                sq, office = _col(r, "SQ_CANDIDATO"), _col(r, "CD_CARGO")
                votes_raw = _col(r, "QT_VOTOS_NOMINAIS_VALIDOS", "QT_VOTOS_NOMINAIS")
                if not (sq and office and votes_raw.lstrip("-").isdigit()) or sq.startswith("-"):
                    discarded += 1
                    continue
                rnd = int(_col(r, "NR_TURNO") or 1)
                uf = _col(r, "SG_UF") or "BR"
                muni = _col(r, "CD_MUNICIPIO") if office in MUNICIPAL_LEVEL else "0"
                key = (year, rnd, office, uf, muni, sq)
                totals[key] = totals.get(key, 0) + int(votes_raw)
    return totals, read, discarded


def import_year(year: int) -> dict:
    ensure_schema()
    resource = find_resource(year)
    url = resource["url"]
    collected = datetime.now(timezone.utc).isoformat()
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / f"votacao_candidato_munzona_{year}.zip"
        sha = download(url, target)
        with zipfile.ZipFile(target) as archive:
            members = pick_members(archive)
            totals, read, discarded = aggregate(archive, members, year)
    rows = [(*k, v) for k, v in totals.items()]
    with connect() as db:
        db.execute("DELETE FROM tse_votes WHERE election_year = ?", (year,))
        for i in range(0, len(rows), 5000):
            db.executemany("INSERT INTO tse_votes (election_year, round, office_code, uf, cd_municipio, sq_candidato, votes) VALUES (?,?,?,?,?,?,?)", rows[i:i + 5000])
            db.commit()
        db.execute("INSERT OR REPLACE INTO tse_import_runs VALUES (?,?,?,?,?,?,?,?,?)",
                   (year, "votacao_candidato_munzona", sha, url, resource["_license"], read, len(rows), discarded, collected))
    return {"year": year, "members": members, "sha256": sha, "license": resource["_license"], "rows_read": read, "rows_kept": len(rows), "rows_discarded": discarded}


def main() -> None:
    parser = argparse.ArgumentParser(description="Importa votos nominais por candidato do TSE com proveniência e checksum.")
    parser.add_argument("--years", nargs="+", type=int, required=True)
    args = parser.parse_args()
    for year in args.years:
        print(json.dumps(import_year(year), ensure_ascii=False))


if __name__ == "__main__":
    main()
