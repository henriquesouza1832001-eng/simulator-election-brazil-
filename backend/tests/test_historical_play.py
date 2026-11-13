import os
import tempfile
import unittest

from fastapi.testclient import TestClient

CAND = lambda sq, name, num, party, res: (2024, sq, 1, "Eleições Municipais 2024", "PREFEITO", "SP", "71072", "SÃO PAULO", num, name, name, party, party, "DEFERIDO", res, "u", "l", "f", "sha", "", "2026-01-01")


class HistoricalPlayTest(unittest.TestCase):
    def test_play_a_real_past_election_and_compare_with_the_official_result(self):
        os.environ.pop("GEMINI_API_KEY", None)
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["DATABASE_PATH"] = os.path.join(tmp, "g.sqlite3")
            from app.main import app
            from app.db import connect
            from app.data import tse_candidacies, tse_votes
            with TestClient(app) as client:
                tse_candidacies.ensure_schema()
                tse_votes.ensure_schema()
                with connect() as db:
                    db.executemany("INSERT INTO tse_candidacies VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", [
                        CAND("1", "ANA", "15", "MDB", "ELEITO"), CAND("2", "BRUNO", "50", "PSOL", "NÃO ELEITO"), CAND("3", "CARLA", "28", "PRTB", "NÃO ELEITO"), CAND("4", "DAVI", "40", "PSB", "NÃO ELEITO")])
                    db.executemany("INSERT INTO tse_votes VALUES (?,?,?,?,?,?,?)", [(2024, 1, "11", "SP", "71072", "1", 3000), (2024, 1, "11", "SP", "71072", "2", 2800),
                                                                                       (2024, 1, "11", "SP", "71072", "3", 2500), (2024, 1, "11", "SP", "71072", "4", 700)])
                opts = client.get("/api/historical/options").json()
                self.assertIn(2024, opts["years"]["prefeito"])
                self.assertEqual(opts["years"]["presidente"], [])  # anos gerais não importados neste teste
                body = {"office": "prefeito", "state_code": "SP", "municipality": "São Paulo", "municipality_id": "3550308", "party": "PSB", "ideology": "Centro-esquerda",
                        "candidate_name": "Marina Histórica", "year": 2024, "character": {"name": "Marina Histórica"}}
                bad = client.post("/api/historical/start", json={**body, "year": 2016})
                self.assertEqual(bad.status_code, 422)
                out = client.post("/api/historical/start", json=body)
                self.assertEqual(out.status_code, 200, out.text)
                cid = out.json()["state"]["campaign_id"]
                hdr = {"X-Mandato-Campaign": cid}
                career = out.json()["state"]["career_overview"]
                self.assertEqual(career["election_date"], "2024-10-06")
                self.assertEqual({o["party"] for o in career["opponents"]}, {"MDB", "PSOL", "PRTB"})
                self.assertTrue(all(o["name"].startswith("Candidato(a) do") for o in career["opponents"]))
                for _ in range(30):
                    g = client.get("/api/game", headers=hdr).json()
                    co = g["career_overview"]
                    if co["result"] is not None:
                        break
                    if co["phase"] == "campaign" and co["can_act"]:
                        client.post("/api/career/action", headers=hdr, json={"activity_type": "comicio", "issue": "educacao", "message": "Vou ampliar creches com metas públicas, prazo definido e prestação de contas à comunidade.", "municipality_id": "3550308"})
                    client.post("/api/game/advance", headers=hdr, json={"days": 14})
                co = client.get("/api/game", headers=hdr).json()["career_overview"]
                self.assertIsNotNone(co["result"])
                cmp = co["historical_compare"]
                self.assertEqual(cmp["kind"], "majoritaria")
                self.assertEqual(cmp["real_winner"]["name"], "ANA")
                self.assertIn("Na eleição de verdade", cmp["text"])


if __name__ == "__main__":
    unittest.main()
