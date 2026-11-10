"""Importação versionada de candidaturas do TSE para a tabela `tse_candidacies`.

Substitui, para o fluxo novo, o importador antigo (`tse_import.py`), que misturava recursos
(bens e redes sociais de candidatos) e sobrescrevia linhas completas por linhas vazias.

- Só usa o recurso do catálogo chamado exatamente "Candidatos" (arquivo `consulta_cand_AAAA.zip`).
- Guarda proveniência: URL da fonte, licença, data da coleta e SHA-256 do arquivo baixado.
- Não copia dados pessoais desnecessários (CPF, e-mail, endereço, nascimento).
- Rejeita registros sem identificador, nome ou cargo e conta o que foi descartado.
- O download é feito no servidor, em arquivo temporário, nunca no navegador.

Exemplo: python -m app.data.tse_candidacies --years 2026 2022
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
from typing import Iterator

import httpx

from ..db import connect

CKAN = "https://dadosabertos.tse.jus.br/api/3/action/package_show"

# Nomes de coluna mudam entre épocas do TSE; cada campo aceita alternativas.
ALIASES: dict[str, tuple[str, ...]] = {
    "sq": ("SQ_CANDIDATO", "SEQUENCIAL_CANDIDATO"),
    "year": ("ANO_ELEICAO",),
    "round": ("NR_TURNO", "NUM_TURNO"),
    "election": ("DS_ELEICAO", "DESCRICAO_ELEICAO"),
    "election_type": ("NM_TIPO_ELEICAO",),
    "uf": ("SG_UF", "SIGLA_UF"),
    "ue_code": ("SG_UE", "SIGLA_UE"),
    "ue_name": ("NM_UE", "DESCRICAO_UE"),
    "office_code": ("CD_CARGO", "CODIGO_CARGO"),
    "office": ("DS_CARGO", "DESCRICAO_CARGO"),
    "number": ("NR_CANDIDATO", "NUMERO_CANDIDATO"),
    "name": ("NM_CANDIDATO", "NOME_CANDIDATO"),
    "ballot_name": ("NM_URNA_CANDIDATO", "NOME_URNA_CANDIDATO"),
    "status": ("DS_SITUACAO_CANDIDATURA", "DESCRICAO_SITUACAO_CANDIDATURA", "DES_SITUACAO_CANDIDATURA"),
    "party_number": ("NR_PARTIDO", "NUMERO_PARTIDO"),
    "party": ("SG_PARTIDO", "SIGLA_PARTIDO"),
    "party_name": ("NM_PARTIDO", "NOME_PARTIDO"),
    "coalition": ("DS_COMPOSICAO_COLIGACAO", "COMPOSICAO_LEGENDA"),
    "result": ("DS_SIT_TOT_TURNO", "DESC_SIT_TOT_TURNO"),
    "generation_date": ("DT_GERACAO",),
}

DDL = """
CREATE TABLE IF NOT EXISTS tse_candidacies (
    election_year INTEGER NOT NULL,
    sq_candidato TEXT NOT NULL,
    round INTEGER,
    election_description TEXT,
    office TEXT NOT NULL,
    uf TEXT,
    ue_code TEXT,
    municipality TEXT,
    number TEXT,
    name TEXT NOT NULL,
    ballot_name TEXT,
    party TEXT,
    party_name TEXT,
    candidacy_status TEXT,
    result_status TEXT,
    source_url TEXT NOT NULL,
    license_name TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_sha256 TEXT NOT NULL,
    source_generated_at TEXT,
    collected_at TEXT NOT NULL,
    PRIMARY KEY (election_year, sq_candidato)
);
CREATE INDEX IF NOT EXISTS idx_candidacies_lookup ON tse_candidacies (election_year, office, uf, municipality);
CREATE TABLE IF NOT EXISTS tse_import_runs (
    election_year INTEGER NOT NULL,
    file_name TEXT NOT NULL,
    file_sha256 TEXT NOT NULL,
    source_url TEXT NOT NULL,
    license_name TEXT NOT NULL,
    rows_read INTEGER NOT NULL,
    rows_kept INTEGER NOT NULL,
    rows_discarded INTEGER NOT NULL,
    collected_at TEXT NOT NULL,
    PRIMARY KEY (election_year, file_sha256)
);
"""


def ensure_schema() -> None:
    with connect() as db:
        db.executescript(DDL)


# Alguns anos usam outro identificador no catálogo do TSE.
SLUG_OVERRIDES = {2020: "candidatos-2020-subtemas"}


def dataset_slug(year: int) -> str:
    return SLUG_OVERRIDES.get(year, f"candidatos-{year}")


def find_main_resource(year: int) -> dict:
    """Localiza o recurso "Candidatos" (somente ele) no catálogo CKAN do TSE."""
    response = httpx.get(CKAN, params={"id": dataset_slug(year)}, timeout=40)
    response.raise_for_status()
    payload = response.json()
    if not payload.get("success"):
        raise RuntimeError(f"O catálogo do TSE não encontrou candidatos-{year}.")
    package = payload["result"]
    main = [r for r in package.get("resources", []) if str(r.get("name", "")).strip().lower() == "candidatos"
            and str(r.get("url", "")).lower().endswith(".zip")]
    if len(main) != 1:
        raise RuntimeError(f"candidatos-{year}: esperava exatamente um recurso 'Candidatos' em ZIP, achei {len(main)}.")
    resource = dict(main[0])
    resource["_license"] = package.get("license_title") or package.get("license_id") or "Consulte a licença no catálogo do TSE"
    return resource


def download(url: str, target: Path) -> str:
    """Baixa em disco e devolve o SHA-256 (sem carregar o ZIP inteiro na memória)."""
    digest = hashlib.sha256()
    with httpx.stream("GET", url, timeout=300, follow_redirects=True) as response:
        response.raise_for_status()
        with target.open("wb") as handle:
            for chunk in response.iter_bytes(1 << 20):
                handle.write(chunk)
                digest.update(chunk)
    return digest.hexdigest()


def pick_member(archive: zipfile.ZipFile) -> str:
    """Prefere o arquivo nacional (BRASIL); sem ele, usa todos os arquivos de consulta_cand."""
    names = [n for n in archive.namelist() if n.lower().endswith((".csv", ".txt")) and "consulta_cand" in Path(n).name.lower()
             and "complement" not in Path(n).name.lower()]
    brasil = [n for n in names if "brasil" in Path(n).name.lower()]
    if brasil:
        return brasil[0]
    if len(names) == 1:
        return names[0]
    raise RuntimeError(f"Não foi possível escolher o arquivo principal: {names[:6]}")


def read_rows(archive: zipfile.ZipFile, member: str) -> Iterator[dict[str, str]]:
    with archive.open(member) as raw:
        text = io.TextIOWrapper(raw, encoding="latin-1", newline="")
        reader = csv.DictReader(text, delimiter=";", quotechar='"')
        for row in reader:
            yield {str(k).strip().upper(): (v or "").strip() for k, v in row.items() if k}


def field(row: dict[str, str], key: str) -> str:
    for alias in ALIASES[key]:
        value = row.get(alias)
        # O TSE usa marcadores como #NE, #NULO, #NULO# e códigos negativos para "não informado".
        if value and not value.startswith("#") and value not in {"-1", "-3", "-4"}:
            return value
    return ""


def import_year(year: int) -> dict:
    ensure_schema()
    resource = find_main_resource(year)
    url = resource["url"]
    collected = datetime.now(timezone.utc).isoformat()
    kept = discarded = read = 0
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / f"consulta_cand_{year}.zip"
        sha = download(url, target)
        with zipfile.ZipFile(target) as archive:
            member = pick_member(archive)
            batch: list[tuple] = []
            with connect() as db:
                for row in read_rows(archive, member):
                    read += 1
                    sq, name, office = field(row, "sq"), field(row, "name"), field(row, "office")
                    if not (sq and name and office):
                        discarded += 1
                        continue
                    batch.append((
                        year, sq, int(field(row, "round") or 1), field(row, "election"), office, field(row, "uf"),
                        field(row, "ue_code"), field(row, "ue_name"), field(row, "number"), name, field(row, "ballot_name"),
                        field(row, "party"), field(row, "party_name"), field(row, "status"), field(row, "result"),
                        f"https://dadosabertos.tse.jus.br/dataset/{dataset_slug(year)}", resource["_license"], Path(member).name, sha,
                        field(row, "generation_date"), collected))
                    kept += 1
                    if len(batch) >= 2000:
                        _flush(db, batch)
                if batch:
                    _flush(db, batch)
                db.execute("INSERT OR REPLACE INTO tse_import_runs VALUES (?,?,?,?,?,?,?,?,?)",
                           (year, Path(member).name, sha, url, resource["_license"], read, kept, discarded, collected))
    return {"year": year, "file": member, "sha256": sha, "license": resource["_license"], "rows_read": read,
            "rows_kept": kept, "rows_discarded": discarded}


def _flush(db, batch: list[tuple]) -> None:
    db.executemany("""
        INSERT INTO tse_candidacies (election_year, sq_candidato, round, election_description, office, uf, ue_code, municipality,
            number, name, ballot_name, party, party_name, candidacy_status, result_status, source_url, license_name, file_name,
            file_sha256, source_generated_at, collected_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(election_year, sq_candidato) DO UPDATE SET
            round=excluded.round, election_description=excluded.election_description, office=excluded.office, uf=excluded.uf,
            ue_code=excluded.ue_code, municipality=excluded.municipality, number=excluded.number, name=excluded.name,
            ballot_name=excluded.ballot_name, party=excluded.party, party_name=excluded.party_name,
            candidacy_status=excluded.candidacy_status, result_status=excluded.result_status, file_sha256=excluded.file_sha256,
            source_generated_at=excluded.source_generated_at, collected_at=excluded.collected_at
    """, batch)
    batch.clear()


def main() -> None:
    parser = argparse.ArgumentParser(description="Importa candidaturas do TSE com proveniência e checksum.")
    parser.add_argument("--years", nargs="+", type=int, required=True)
    args = parser.parse_args()
    for year in args.years:
        print(json.dumps(import_year(year), ensure_ascii=False))


if __name__ == "__main__":
    main()
