"""Trajetória partidária: eleitor → militante → filiado → quadro → pré-candidato → carreira de vereador."""
from __future__ import annotations

import os
import tempfile
import unittest

from fastapi.testclient import TestClient

START = {"name": "Marina Teste", "state_code": "SP", "municipality_id": "3550308", "spectrum": "centro_esquerda", "cause": "educacao"}


class PartyPathApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old = os.environ.get("DATABASE_PATH")
        os.environ["DATABASE_PATH"] = os.path.join(self.tmp.name, "g.sqlite3")

    def tearDown(self):
        if self.old is None:
            os.environ.pop("DATABASE_PATH", None)
        else:
            os.environ["DATABASE_PATH"] = self.old
        self.tmp.cleanup()

    def client(self):
        from app.main import app
        return TestClient(app)

    def test_start_validates_municipality_and_cause(self):
        with self.client() as c:
            self.assertEqual(c.post("/api/party-path/start", json={**START, "municipality_id": "0000000"}).status_code, 422)
            self.assertEqual(c.post("/api/party-path/start", json={**START, "state_code": "RJ"}).status_code, 422)  # município de SP
            self.assertEqual(c.post("/api/party-path/start", json={**START, "cause": "inexistente"}).status_code, 422)
            state = c.post("/api/party-path/start", json=START).json()
            c.headers["X-Mandato-Campaign"] = state["campaign_id"]
            self.assertEqual(state["mode"], "party_path")
            self.assertEqual(state["party_path"]["stage"], "eleitor")
            self.assertFalse(state["communications"]["inauguration"]["required"])  # sem pronunciamento de presidente

    def test_actions_are_gated_by_stage_energy_and_party(self):
        with self.client() as c:
            c.headers["X-Mandato-Campaign"] = c.post("/api/party-path/start", json=START).json()["campaign_id"]
            self.assertEqual(c.post("/api/party-path/act", json={"action": "tarefa_partido"}).status_code, 409)   # exige partido
            self.assertEqual(c.post("/api/party-path/act", json={"action": "panfletagem"}).status_code, 409)       # exige ser militante
            r = c.post("/api/party-path/act", json={"action": "reuniao_bairro"}).json()
            self.assertGreater(r["result"]["applied"]["network"], 0)
            self.assertEqual(c.post("/api/party-path/affiliate", json={"party": "Partido Teste", "ideology": "Centro"}).status_code, 409)  # ainda não é militante

    def test_full_path_to_vereador_candidacy(self):
        with self.client() as c:
            c.headers["X-Mandato-Campaign"] = c.post("/api/party-path/start", json=START).json()["campaign_id"]
            launched = False
            for day in range(1, 420):
                ov = c.get("/api/party-path").json()
                stage = ov["stage"]
                if stage == "militante" and ov["next"]["ready"] and not ov["affiliation"].get("status") == "analise" and not ov["party"]:
                    c.post("/api/party-path/affiliate", json={"party": "Partido Teste Renovador", "ideology": "Centro-esquerda"})
                if stage == "filiado" and ov["next"]["ready"]:
                    c.post("/api/party-path/run-post")
                if stage == "quadro" and ov["next"]["ready"]:
                    out = c.post("/api/party-path/launch")
                    self.assertEqual(out.status_code, 200, out.text)
                    launched = True
                    break
                prefs = {"eleitor": ["reuniao_bairro", "ato_publico", "acompanhar"], "militante": ["panfletagem", "abaixo_assinado", "cabo_eleitoral", "debate_local"],
                         "filiado": ["tarefa_partido", "reuniao_partido", "buscar_padrinho", "reuniao_bairro"], "quadro": ["reuniao_partido", "tarefa_partido", "voluntariado", "estudar"]}.get(stage, [])
                done = False
                for key in prefs + ["voluntariado", "estudar"]:
                    r = c.post("/api/party-path/act", json={"action": key})
                    if r.status_code == 200:
                        done = True
                        break
                if not done:
                    c.post("/api/party-path/act", json={"action": "descansar"})
                c.post("/api/game/advance", json={"days": 1})
            self.assertTrue(launched, "a trajetória deveria chegar à pré-candidatura em até ~14 meses de jogo")
            state = c.get("/api/game").json()
            self.assertEqual(state["party_path"]["stage"], "candidato")
            self.assertFalse(state["party_path"]["active"])
            self.assertTrue(state["career"].get("mode"))
            self.assertEqual(state["career"]["office"], "vereador")
            self.assertEqual(state["career"]["municipality"], "São Paulo")

    def test_affiliation_can_be_refused_and_has_cooldown(self):
        from app.engine import party_path
        from app.engine.state import new_game, refresh_calendar_fields
        from datetime import date
        refused_seen = False
        for seed in range(200000, 200040):
            state = refresh_calendar_fields(new_game())
            state["campaign_seed"] = seed
            pp = party_path.init_state(state, name="X", state_code="SP", municipality_id="3550308", municipality="São Paulo", spectrum="esquerda", cause="saude")
            pp.update(stage="militante", militancy=30.0, network=10.0, reputation=20.0)
            party_path.request_affiliation(state, "Partido Teste", "Direita")  # linha oposta: chance baixa
            party_path.tick(state, date.fromisoformat(state["date"]), date.fromisoformat(state["date"]) + __import__("datetime").timedelta(days=15))
            if pp["affiliation"]["status"] == "recusado":
                refused_seen = True
                with self.assertRaises(ValueError):
                    party_path.request_affiliation(state, "Partido Teste", "Direita")  # em carência
                break
        self.assertTrue(refused_seen)

    def test_inactivity_erodes_reputation_and_events_apply_pp_effects(self):
        from app.engine import party_path, story
        from app.engine.state import new_game, refresh_calendar_fields
        from datetime import date, timedelta
        state = refresh_calendar_fields(new_game())
        pp = party_path.init_state(state, name="X", state_code="SP", municipality_id="3550308", municipality="São Paulo", spectrum="centro", cause="saude")
        pp["last_action"] = state["date"]
        start = date.fromisoformat(state["date"])
        before = pp["reputation"]
        party_path.tick(state, start, start + timedelta(days=90))
        self.assertLess(pp["reputation"], before)
        # evento de militante aplica efeitos pp:*
        ev = story._fire(state, "mil_mutirao:saude", start)
        entry = story.respond(state, ev["id"], "liderar")
        self.assertTrue(any(d["key"] == "pp:network" for d in entry["deltas"]))
        self.assertGreater(pp["network"], 8.0)


class StoryLevelTests(unittest.TestCase):
    def test_militant_level_only_fires_militant_events(self):
        from datetime import date, timedelta
        from app.engine import party_path, story
        from app.engine.event_library import get_library
        from app.engine.state import new_game, refresh_calendar_fields
        state = refresh_calendar_fields(new_game())
        party_path.init_state(state, name="X", state_code="SP", municipality_id="3550308", municipality="São Paulo", spectrum="centro", cause="saude")
        start = date.fromisoformat(state["date"])
        for step in range(24):
            before = start + timedelta(days=30 * step)
            story.tick(state, before, before + timedelta(days=30))
            for ev in list(state["story"]["pending"]):
                story.respond(state, ev["id"], ev["choices"][0]["id"])
        defs = {h["def"] for h in state["story"]["history"]}
        self.assertTrue(defs)
        self.assertTrue(all("militante" in get_library().get(d)["levels"] for d in defs), defs)


if __name__ == "__main__":
    unittest.main()
