"""Modo Eleitor: consulta de candidaturas oficiais do TSE e urna de simulação.

- Pleitos já realizados usam só registros importados do TSE (tabela `tse_candidacies`), com fonte e coleta.
- 2028 e 2030 não têm registro oficial: o elenco é fictício, determinístico e marcado como cenário futuro.
- O voto é **simulado**: fica só neste jogo, não é enviado à Justiça Eleitoral e não altera eleição real.
"""
from __future__ import annotations

import hashlib
import unicodedata
from typing import Any

from ..db import connect, current_player_id
from . import election_rules as er
from .legislature import PARTIES

SIMULATED_VOTE_NOTICE = "Voto simulado: não é enviado à Justiça Eleitoral e não altera uma eleição real."
ELECTED_STATUSES = ("ELEITO", "ELEITO POR QP", "ELEITO POR MÉDIA")


def normalize(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", text or "") if not unicodedata.combining(c)).upper().strip()


def _db():
    """Conexão com a função `norm()` (maiúsculas, sem acento) para buscas insensíveis a acento."""
    db = connect()
    db.create_function("norm", 1, normalize)
    return db


def availability(year: int) -> dict[str, Any]:
    """Estado dos dados oficiais deste ano: quantidade, fonte, licença, coleta e checksum."""
    if year >= 2028:
        return {"year": year, "official_data": False, "future_simulated": True, "candidacies": 0,
                "message": "Cenário futuro simulado: o TSE ainda não publicou candidaturas oficiais."}
    with connect() as db:
        run = db.execute("SELECT * FROM tse_import_runs WHERE election_year = ? ORDER BY collected_at DESC LIMIT 1", (year,)).fetchone()
        count = db.execute("SELECT COUNT(*) FROM tse_candidacies WHERE election_year = ?", (year,)).fetchone()[0]
    if not run or not count:
        return {"year": year, "official_data": False, "future_simulated": False, "candidacies": 0,
                "message": f"Dados oficiais de {year} ainda não importados. Rode: python -m app.data.tse_candidacies --years {year}"}
    return {"year": year, "official_data": True, "future_simulated": False, "candidacies": count, "source_url": run["source_url"],
            "license": run["license_name"], "collected_at": run["collected_at"], "file": run["file_name"], "sha256": run["file_sha256"],
            "rows_read": run["rows_read"], "rows_discarded": run["rows_discarded"],
            "votes_imported": False, "votes_note": "Votos por candidato ainda não importados; o comparativo usa a situação de totalização do cadastro oficial."}


def _scope_filters(office: str, scope: dict[str, Any]) -> tuple[str, list[Any]]:
    names = er.TSE_OFFICE_NAMES[office]
    sql = "office IN (" + ",".join("?" * len(names)) + ")"
    params: list[Any] = list(names)
    if scope.get("uf"):
        sql += " AND uf = ?"
        params.append(scope["uf"])
    return sql, params


def _row(r) -> dict[str, Any]:
    return {"id": r["sq_candidato"], "name": r["name"], "ballot_name": r["ballot_name"] or r["name"], "number": r["number"],
            "party": r["party"], "party_name": r["party_name"], "office": r["office"], "uf": r["uf"], "municipality": r["municipality"],
            "candidacy_status": r["candidacy_status"] or "não informada na fonte", "result": r["result_status"] or "não informado na fonte",
            "fictional": False}


def list_candidates(year: int, office: str, scope: dict[str, Any], query: str = "", page: int = 1, page_size: int = 30) -> dict[str, Any]:
    page_size = max(1, min(100, page_size))
    page = max(1, page)
    if year >= 2028:
        cast = fictional_cast(year, office, scope)
        return {"items": cast, "total": len(cast), "page": 1, "page_size": len(cast), "source": availability(year),
                "scenario": "Cenário futuro simulado — participantes fictícios; não são candidatos registrados."}
    info = availability(year)
    if not info["official_data"]:
        return {"items": [], "total": 0, "page": page, "page_size": page_size, "source": info, "scenario": None}
    sql, params = _scope_filters(office, scope)
    if scope.get("municipality"):
        sql += " AND norm(municipality) = ?"
        params.append(normalize(scope["municipality"]))
    if query.strip():
        sql += " AND (norm(name) LIKE ? OR norm(ballot_name) LIKE ?)"
        like = f"%{normalize(query)}%"
        params += [like, like]
    with _db() as db:
        total = db.execute(f"SELECT COUNT(*) FROM tse_candidacies WHERE election_year = ? AND {sql}", [year, *params]).fetchone()[0]
        rows = db.execute(
            f"SELECT * FROM tse_candidacies WHERE election_year = ? AND {sql} ORDER BY CAST(number AS INTEGER), name LIMIT ? OFFSET ?",
            [year, *params, page_size, (page - 1) * page_size]).fetchall()
    return {"items": [_row(r) for r in rows], "total": total, "page": page, "page_size": page_size, "source": info, "scenario": None}


def fictional_cast(year: int, office: str, scope: dict[str, Any]) -> list[dict[str, Any]]:
    """Elenco simulado para cenários futuros: partidos reais, sem pessoas reais."""
    key = f"{year}|{office}|{scope.get('uf')}|{scope.get('municipality_id')}"
    seed = int.from_bytes(hashlib.sha256(key.encode()).digest()[:8], "big")
    parties = sorted(p["id"] for p in PARTIES)
    size = 5 if er.OFFICES[office]["system"] != "proporcional" else 8
    out = []
    for i in range(size):
        a = (seed >> (i * 3)) & 0xFFFF
        party = parties[(a // 11) % len(parties)]
        name = f"Candidato(a) simulado(a) do {party}"
        out.append({"id": f"fic-{year}-{office}-{i + 1}", "name": name, "ballot_name": name, "number": str(10 + i * 7 + (a % 5)),
                    "party": party, "party_name": party, "office": er.OFFICES[office]["label"],
                    "uf": scope.get("uf"), "municipality": scope.get("municipality"), "candidacy_status": "cenário simulado",
                    "result": "não aplicável", "fictional": True})
    return out


def official_outcome(year: int, office: str, scope: dict[str, Any], limit: int = 30) -> dict[str, Any]:
    """Quem consta como eleito (ou no 2º turno) no cadastro oficial. Não inclui votos."""
    if year >= 2028:
        return {"available": False, "message": "Não há resultado oficial: cenário futuro simulado.", "elected": []}
    if not availability(year)["official_data"]:
        return {"available": False, "message": "Dados oficiais deste ano ainda não importados.", "elected": []}
    sql, params = _scope_filters(office, scope)
    if scope.get("municipality"):
        sql += " AND norm(municipality) = ?"
        params.append(normalize(scope["municipality"]))
    statuses = ELECTED_STATUSES + ("2º TURNO",)
    with _db() as db:
        rows = db.execute(
            f"SELECT * FROM tse_candidacies WHERE election_year = ? AND {sql} AND result_status IN ({','.join('?' * len(statuses))}) "
            "ORDER BY name LIMIT ?", [year, *params, *statuses, limit]).fetchall()
    return {"available": True, "elected": [_row(r) for r in rows], "note": "Situação de totalização do cadastro oficial do TSE. Votos por candidato ainda não importados."}


def scope_key(office: str, scope: dict[str, Any]) -> str:
    return f"{scope.get('uf') or 'BR'}:{scope.get('municipality_id') or '-'}"


def cast_vote(year: int, office: str, scope: dict[str, Any], choice: str) -> dict[str, Any]:
    """Registra o voto simulado do jogador. `choice` é o id do candidato, "branco" ou "nulo"."""
    if choice in {"branco", "nulo"}:
        label, kind = ("Voto em branco" if choice == "branco" else "Voto nulo"), "branco_nulo"
        picked = None
    else:
        listing = list_candidates(year, office, scope, page_size=100)
        picked = next((c for c in listing["items"] if c["id"] == choice), None)
        if picked is None:
            # candidato fora da primeira página: confere direto na base oficial
            if year < 2028:
                sql, params = _scope_filters(office, scope)
                with _db() as db:
                    row = db.execute(f"SELECT * FROM tse_candidacies WHERE election_year = ? AND sq_candidato = ? AND {sql}", [year, choice, *params]).fetchone()
                picked = _row(row) if row else None
            if picked is None:
                raise ValueError("Candidato não encontrado nesta disputa.")
        label = f"{picked['ballot_name']} ({picked['party'] or 's/ partido'}, {picked['number']})"
        kind = "ficticio" if picked["fictional"] else "tse"
    with connect() as db:
        db.execute("INSERT INTO elector_votes (player_id, election_year, office, scope_key, choice, choice_label, source_kind) VALUES (?,?,?,?,?,?,?) "
                   "ON CONFLICT(player_id, election_year, office, scope_key) DO UPDATE SET choice=excluded.choice, "
                   "choice_label=excluded.choice_label, source_kind=excluded.source_kind, created_at=CURRENT_TIMESTAMP",
                   (current_player_id(), year, office, scope_key(office, scope), choice, label, kind))
    outcome = official_outcome(year, office, scope)
    match = None
    if picked and not picked["fictional"]:
        match = "ELEITO" if picked["result"] in ELECTED_STATUSES else ("2º TURNO" if picked["result"] == "2º TURNO" else "NÃO ELEITO")
    return {"notice": SIMULATED_VOTE_NOTICE, "choice": choice, "label": label, "your_candidate_result": match,
            "official": outcome, "scenario_label": "Cenário futuro simulado" if year >= 2028 else None}


def my_votes() -> list[dict[str, Any]]:
    with connect() as db:
        rows = db.execute("SELECT election_year, office, scope_key, choice_label, source_kind, created_at FROM elector_votes "
                          "WHERE player_id = ? ORDER BY created_at DESC LIMIT 100", (current_player_id(),)).fetchall()
    return [dict(r) for r in rows]
