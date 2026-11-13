import os
import tempfile
import unittest


class TseVotesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["DATABASE_PATH"] = os.path.join(self.tmp.name, "g.sqlite3")
        from app import db
        from app.data import tse_candidacies, tse_votes
        db.init_db() if hasattr(db, "init_db") else None
        tse_candidacies.ensure_schema()
        tse_votes.ensure_schema()
        with db.connect() as conn:
            cand = lambda sq, name, office, num, party, res: (2024, sq, 1, "Eleições Municipais 2024", office, "SP", "99999", "TESTELANDIA", num, name, name, party, party, "DEFERIDO", res, "u", "l", "f", "sha", "", "2026-01-01")
            conn.executemany("INSERT INTO tse_candidacies VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", [
                cand("1", "ANA PREFEITA", "PREFEITO", "11", "PSB", "ELEITO"), cand("2", "BRUNO", "PREFEITO", "22", "PL", "NÃO ELEITO"),
                cand("11", "VER UM", "VEREADOR", "11111", "PT", "ELEITO POR QP"), cand("12", "VER DOIS", "VEREADOR", "22222", "PL", "ELEITO POR MÉDIA"),
                cand("13", "VER TRES", "VEREADOR", "33333", "MDB", "NÃO ELEITO")])
            conn.executemany("INSERT INTO tse_votes VALUES (?,?,?,?,?,?,?)", [
                (2024, 1, "11", "SP", "99999", "1", 6000), (2024, 1, "11", "SP", "99999", "2", 4000),
                (2024, 1, "13", "SP", "99999", "11", 900), (2024, 1, "13", "SP", "99999", "12", 500), (2024, 1, "13", "SP", "99999", "13", 450)])

    def tearDown(self):
        self.tmp.cleanup()

    def test_results_show_votes_share_and_rounds(self):
        from app.engine import elector
        scope = {"scope": "municipio", "uf": "SP", "municipality_id": "0000000", "municipality": "Testelândia"}
        res = elector.official_results(2024, "prefeito", scope, 5)
        self.assertTrue(res["available"])
        r = res["rounds"][0]
        self.assertEqual(r["nominal_votes"], 10000)
        self.assertEqual(r["candidates"][0]["name"], "ANA PREFEITA")
        self.assertEqual(r["candidates"][0]["share_pct"], 60.0)

    def test_missing_year_explains_how_to_import(self):
        from app.engine import elector
        res = elector.official_results(2022, "presidente", {"scope": "nacional", "uf": None}, 5)
        self.assertFalse(res["available"])
        self.assertIn("tse_votes", res["message"])

    def test_reference_election_for_councillor_uses_last_elected(self):
        from app.engine import historical
        historical._benchmark.cache_clear()
        ref = historical.reference_election({"office": "vereador", "municipality_id": "0000000", "municipality": "Testelândia", "state_code": "SP"})
        self.assertEqual(ref["seats"], 2)
        self.assertEqual(ref["last_elected"]["votes"], 500)
        self.assertIn("500", ref["text"])
        self.assertIsNone(historical.reference_election({"office": "senador", "municipality_id": "1", "municipality": "x", "state_code": "SP"}))


if __name__ == "__main__":
    unittest.main()
