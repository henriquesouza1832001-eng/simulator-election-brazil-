import os
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


class SkipPreparationTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.environment = patch.dict(os.environ, {"DATABASE_PATH": str(Path(self.temp_dir.name) / "game.sqlite3"), "COGNITO_REGION": "", "COGNITO_USER_POOL_ID": "",
                                                    "COGNITO_CLIENT_ID": "", "COGNITO_DOMAIN": "", "GEMINI_API_KEY": ""})
        self.environment.start()
        self.client = TestClient(app)
        self.client.__enter__()

    def tearDown(self):
        self.client.__exit__(None, None, None)
        self.environment.stop()
        self.temp_dir.cleanup()

    def test_refuses_outside_career(self):
        created = self.client.post("/api/game/new", json={"character": {"name": "Teste"}, "difficulty": "normal"})
        self.assertEqual(created.status_code, 200)
        cid = created.json()["campaign_id"]
        r = self.client.post("/api/career/skip-to-election-year", headers={"X-Mandato-Campaign": cid})
        self.assertEqual(r.status_code, 409)

    def test_skips_a_long_preparation_up_to_the_election_year(self):
        from app.engine.career import career_overview, start_career
        from app.engine.state import advance_state, new_game, refresh_calendar_fields
        state = refresh_calendar_fields(new_game())
        state["setup_pending"] = False
        start_career(state, "vereador", "SP", "São Paulo", "Partido da Renovação", "Centro", "Candidata de teste", municipality_id="3550308")
        career = state["career"]
        self.assertEqual(career["phase"], "pre_campaign")
        target = date(date.fromisoformat(career["election_date"]).year, 1, 1)
        self.assertGreater((target - date.fromisoformat(state["date"])).days, 60)
        while date.fromisoformat(state["date"]) < target:
            state, _ = advance_state(state, min(30, (target - date.fromisoformat(state["date"])).days))
        self.assertEqual(state["date"], target.isoformat())
        self.assertIn(state["career"]["phase"], ("pre_campaign", "campaign"))


if __name__ == "__main__":
    unittest.main()
