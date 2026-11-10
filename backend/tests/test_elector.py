"""Modo Eleitor: cenários, candidatos oficiais (dados de teste), cenário futuro e urna simulada."""
from __future__ import annotations

import os
import tempfile
import unittest

from fastapi.testclient import TestClient

from app.db import connect, initialize


def _row(year, sq, office, uf, city, name, number, party, status="Deferido", result="NÃO ELEITO"):
    return (year, sq, 1, "Eleições", office, uf, "1", city, number, name, name, party, party, status, result,
            "https://dadosabertos.tse.jus.br/dataset/candidatos-teste", "Creative Commons Attribution", "arquivo-teste.csv",
            "sha-teste", "09/11/2026", "2026-11-09T00:00:00+00:00")


class ElectorApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old = os.environ.get("DATABASE_PATH")
        os.environ["DATABASE_PATH"] = os.path.join(self.tmp.name, "g.sqlite3")
        initialize()
        rows = [
            _row(2022, "1", "PRESIDENTE", "BR", "BRASIL", "ANA TESTE", "13", "PTX", result="ELEITO"),
            _row(2022, "2", "PRESIDENTE", "BR", "BRASIL", "JOSÉ DA SILVA", "22", "PLX"),
            _row(2024, "3", "PREFEITO", "SP", "SÃO PAULO", "MARIA EXEMPLO", "15", "MDX", result="ELEITO"),
            _row(2024, "4", "PREFEITO", "SP", "SÃO PAULO", "PEDRO TESTE", "50", "PSX"),
            _row(2024, "5", "PREFEITO", "RJ", "RIO DE JANEIRO", "OUTRO RJ", "10", "PRX"),
        ]
        with connect() as db:
            db.executemany("INSERT INTO tse_candidacies VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", rows)
            db.execute("INSERT INTO tse_import_runs VALUES (2022,'arquivo-teste.csv','sha-teste','https://x','Creative Commons Attribution',2,2,0,'2026-11-09')")
            db.execute("INSERT INTO tse_import_runs VALUES (2024,'arquivo-teste.csv','sha-teste','https://x','Creative Commons Attribution',3,3,0,'2026-11-09')")

    def tearDown(self):
        if self.old is None:
            os.environ.pop("DATABASE_PATH", None)
        else:
            os.environ["DATABASE_PATH"] = self.old
        self.tmp.cleanup()

    def client(self):
        from app.main import app
        return TestClient(app)

    def test_scenarios_list_and_data_status(self):
        with self.client() as c:
            data = c.get("/api/scenarios").json()
            years = [s["year"] for s in data["scenarios"]]
            self.assertEqual(years, [2014, 2016, 2018, 2020, 2022, 2024, 2026, 2028, 2030])
            by_year = {s["year"]: s for s in data["scenarios"]}
            self.assertTrue(by_year[2022]["data"]["official_data"])
            self.assertFalse(by_year[2014]["data"]["official_data"])  # não importado no teste: mensagem honesta
            self.assertTrue(by_year[2030]["future_simulated"])
            self.assertEqual([m["key"] for m in data["modes"]], ["eleitor", "carreira", "posse"])

    def test_future_years_have_only_fictional_candidates(self):
        with self.client() as c:
            out = c.get("/api/elector/candidates", params={"year": 2030, "office": "presidente"}).json()
            self.assertTrue(out["items"])
            self.assertTrue(all(i["fictional"] for i in out["items"]))
            self.assertIn("simulado", out["scenario"].lower())
            self.assertEqual(out["items"], c.get("/api/elector/candidates", params={"year": 2030, "office": "presidente"}).json()["items"])

    def test_official_candidates_and_provenance(self):
        with self.client() as c:
            out = c.get("/api/elector/candidates", params={"year": 2022, "office": "presidente"}).json()
            self.assertEqual(out["total"], 2)
            self.assertEqual(out["source"]["sha256"], "sha-teste")
            self.assertEqual(out["source"]["license"], "Creative Commons Attribution")
            self.assertFalse(out["items"][0]["fictional"])
            self.assertIn("Voto simulado", out["notice"])
            # busca sem acento encontra nome acentuado
            found = c.get("/api/elector/candidates", params={"year": 2022, "office": "presidente", "q": "jose"}).json()
            self.assertEqual([i["name"] for i in found["items"]], ["JOSÉ DA SILVA"])

    def test_municipality_scope_uses_ibge_and_filters(self):
        with self.client() as c:
            out = c.get("/api/elector/candidates", params={"year": 2024, "office": "prefeito", "municipality_id": "3550308"}).json()
            self.assertEqual({i["name"] for i in out["items"]}, {"MARIA EXEMPLO", "PEDRO TESTE"})
            bad = c.get("/api/elector/candidates", params={"year": 2024, "office": "prefeito", "municipality_id": "0000000"})
            self.assertEqual(bad.status_code, 422)

    def test_incoherent_selection_is_rejected(self):
        with self.client() as c:
            self.assertEqual(c.post("/api/scenarios/validate", json={"year": 2024, "office": "presidente"}).status_code, 422)
            self.assertEqual(c.post("/api/scenarios/validate", json={"year": 2022, "office": "governador", "uf": "ZZ"}).status_code, 422)
            ok = c.post("/api/scenarios/validate", json={"year": 2022, "office": "governador", "uf": "MG"})
            self.assertEqual(ok.status_code, 200)

    def test_simulated_vote_and_comparison(self):
        with self.client() as c:
            body = {"year": 2022, "office": "presidente", "choice": "1"}
            out = c.post("/api/elector/vote", json=body).json()
            self.assertIn("não é enviado à Justiça Eleitoral", out["notice"])
            self.assertEqual(out["your_candidate_result"], "ELEITO")
            self.assertEqual(out["official"]["elected"][0]["name"], "ANA TESTE")
            c.post("/api/elector/vote", json={**body, "choice": "2"})  # troca o voto (um por disputa)
            votes = c.get("/api/elector/votes").json()["votes"]
            self.assertEqual(len(votes), 1)
            self.assertIn("JOSÉ DA SILVA", votes[0]["choice_label"])
            self.assertEqual(c.post("/api/elector/vote", json={**body, "choice": "nulo"}).json()["label"], "Voto nulo")
            self.assertEqual(c.post("/api/elector/vote", json={**body, "choice": "999"}).status_code, 404)

    def test_future_vote_is_labelled_scenario(self):
        with self.client() as c:
            cand = c.get("/api/elector/candidates", params={"year": 2030, "office": "presidente"}).json()["items"][0]
            out = c.post("/api/elector/vote", json={"year": 2030, "office": "presidente", "choice": cand["id"]}).json()
            self.assertEqual(out["scenario_label"], "Cenário futuro simulado")
            self.assertFalse(out["official"]["available"])


if __name__ == "__main__":
    unittest.main()
