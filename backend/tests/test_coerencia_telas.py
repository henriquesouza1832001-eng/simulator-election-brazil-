import os
import tempfile
import unittest

from fastapi.testclient import TestClient


class CoerenciaDasTelasTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.old = os.environ.get("DATABASE_PATH")
        os.environ["DATABASE_PATH"] = os.path.join(self.tmp.name, "g.sqlite3")
        from app.main import app
        self.ctx = TestClient(app)
        self.c = self.ctx.__enter__()

    def tearDown(self):
        self.ctx.__exit__(None, None, None)
        if self.old is None:
            os.environ.pop("DATABASE_PATH", None)
        else:
            os.environ["DATABASE_PATH"] = self.old
        self.tmp.cleanup()

    def campanha(self):
        body = {"office": "prefeito", "state_code": "SP", "municipality": "São Paulo", "municipality_id": "3550308", "party": "MDB", "ideology": "Centro",
                "candidate_name": "Teste", "character": {"name": "Teste"}, "difficulty": "normal"}
        started = self.c.post("/api/career/start", json=body).json()
        self.c.headers["X-Mandato-Campaign"] = (started.get("state") or started)["campaign_id"]
        state = started.get("state") or started
        for _ in range(40):
            if state["career_overview"]["phase"] == "campaign":
                break
            state = self.c.post("/api/game/advance", json={"days": 30}).json()["state"]
        return state

    def test_um_numero_de_intencao_de_voto_e_grupos_em_torno_dele(self):
        ov = self.campanha()["career_overview"]
        self.assertEqual(ov["phase"], "campaign")
        grupos = [g["support"] for g in ov["groups"]]
        self.assertAlmostEqual(sum(grupos) / len(grupos), ov["vote_intent"], delta=1.5)
        self.assertGreater(max(grupos) - min(grupos), 3)   # grupos deixam de ser todos iguais

    def test_rivais_com_apoio_somam_o_que_o_jogador_nao_tem(self):
        ov = self.campanha()["career_overview"]
        self.assertGreaterEqual(len(ov["rivals"]), 3)
        self.assertNotIn("MDB", {r["party"] for r in ov["rivals"]})
        self.assertAlmostEqual(ov["vote_intent"] + sum(r["support"] for r in ov["rivals"]), 100.0, delta=0.3)

    def test_metas_da_campanha_listam_o_que_fazer_com_numero_em_pt_br(self):
        goals = self.campanha()["career_overview"]["goals"]
        self.assertTrue({"lider", "visitas", "debate"} <= {g["id"] for g in goals})
        lider = next(g for g in goals if g["id"] == "lider")
        self.assertNotIn(".", lider["progress"])   # vírgula decimal, como no resto da tela

    def test_campanha_local_nao_recebe_crise_nacional_generica(self):
        state = self.campanha()
        for _ in range(8):
            state = self.c.post("/api/game/advance", json={"days": 30}).json()["state"]
            if state["career_overview"]["phase"] != "campaign":
                break
        self.assertEqual([c for c in state.get("active_crises", []) if c.get("status") == "active"], [])


if __name__ == "__main__":
    unittest.main()
