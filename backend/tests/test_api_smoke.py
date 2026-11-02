"""Small API-level smoke tests for the first playable release."""
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.db import load_state, reset_player_id, save_state, set_player_id
from app.engine.difficulty import adjust_coalition_probability, election_margin, event_severity_weights, get_difficulty
from app.main import app


INAUGURAL_ADDRESS = (
    "Brasileiros e brasileiras, vamos trabalhar com responsabilidade e transparência, "
    "respeitando a Constituição, a lei e o Congresso. Vamos cuidar da saúde, da educação, "
    "da renda e da segurança com metas públicas e prestação de contas ao povo."
)


class ApiSmokeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.environment = patch.dict(os.environ, {
            "DATABASE_PATH": str(Path(self.temp_dir.name) / "game.sqlite3"),
            "COGNITO_REGION": "",
            "COGNITO_USER_POOL_ID": "",
            "COGNITO_CLIENT_ID": "",
            "COGNITO_DOMAIN": "",
            "GEMINI_API_KEY": "",
        })
        self.environment.start()
        self.client = TestClient(app)
        self.client.__enter__()

    def tearDown(self) -> None:
        self.client.__exit__(None, None, None)
        self.environment.stop()
        self.temp_dir.cleanup()

    def deliver_inaugural_address(self) -> None:
        response = self.client.post("/api/game/inaugural-address", json={"text": INAUGURAL_ADDRESS})
        self.assertEqual(response.status_code, 200, response.text)

    def test_new_game_requires_inaugural_address_before_time_advances(self) -> None:
        state = self.client.get("/api/game")
        self.assertEqual(state.status_code, 200)
        self.assertEqual(state.json()["date"], "2027-01-01")
        self.assertTrue(state.json()["communications"]["inauguration"]["required"])

        difficulty = self.client.patch("/api/game/difficulty", json={"difficulty": "tranquilo"})
        self.assertEqual(difficulty.status_code, 200, difficulty.text)
        self.assertEqual(difficulty.json()["difficulty"], "tranquilo")

        blocked = self.client.post("/api/game/advance", json={"days": 1})
        self.assertEqual(blocked.status_code, 409)
        self.assertEqual(blocked.json()["action"], "inaugural_address")

        self.deliver_inaugural_address()
        advanced = self.client.post("/api/game/advance", json={"days": 1})
        self.assertEqual(advanced.status_code, 200, advanced.text)
        self.assertEqual(advanced.json()["state"]["date"], "2027-01-02")

    def test_core_screens_load_and_offer_all_five_difficulties(self) -> None:
        for path in (
            "/api/health",
            "/api/game/options",
            "/api/career/options",
            "/api/budget",
            "/api/diplomacy",
            "/api/government/ministries",
            "/api/government/appointments",
        ):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200, response.text)

        options = self.client.get("/api/game/options").json()
        self.assertEqual(set(options["difficulties"]), {"tranquilo", "normal", "dificil", "complicado", "realismo_puro"})
        career = self.client.get("/api/career/options").json()
        self.assertEqual(len(career["offices"]), 7)
        self.assertIn("works", self.client.get("/api/budget").json())

    def test_measure_preview_failure_is_a_controlled_gateway_error(self) -> None:
        with patch("app.main.interpret", new=AsyncMock(side_effect=RuntimeError("model unavailable"))):
            response = self.client.post("/api/measures/preview", json={"text": "Revisar compras públicas para reduzir desperdício."})
        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json()["detail"], "A interpretação não pôde ser gerada. Tente novamente.")

    def test_campaign_can_start_and_reports_its_calendar(self) -> None:
        response = self.client.post("/api/career/start", json={
            "office": "vereador",
            "state_code": "SP",
            "municipality": "São Paulo",
            "party": "Partido da Renovação",
            "ideology": "Centro",
            "candidate_name": "Candidatura de teste",
        })
        self.assertEqual(response.status_code, 200, response.text)
        overview = response.json()["state"]["career_overview"]
        self.assertEqual(overview["phase"], "pre_campaign")
        self.assertEqual(overview["election_date"], "2028-10-01")
        self.assertEqual(overview["campaign_start_date"], "2028-07-03")
        self.assertFalse(overview["inaugural_address"]["required"])

    def test_career_campaign_action_and_election_complete(self) -> None:
        started = self.client.post("/api/career/start", json={
            "office": "prefeito", "state_code": "MG", "municipality": "Belo Horizonte",
            "party": "Partido da RenovaÃ§Ã£o", "ideology": "Centro", "candidate_name": "Candidatura de teste",
        })
        self.assertEqual(started.status_code, 200, started.text)

        overview = started.json()["state"]["career_overview"]
        while not overview["campaign_active"]:
            days = min(90, max(1, overview["days_until_campaign"]))
            advanced = self.client.post("/api/game/advance", json={"days": days})
            self.assertEqual(advanced.status_code, 200, advanced.text)
            overview = advanced.json()["state"]["career_overview"]

        action = self.client.post("/api/career/action", json={
            "activity_type": "comicio", "issue": "educacao",
            "message": "Vamos publicar metas para melhorar escolas e postos de saúde, com prazo, equipe e prestação de contas.",
        })
        self.assertEqual(action.status_code, 200, action.text)
        self.assertGreater(action.json()["result"]["score"], 0)
        self.assertEqual(action.json()["state"]["career_overview"]["activities"][0]["type"], "comicio")

        election = self.client.post("/api/game/advance", json={"days": 90})
        self.assertEqual(election.status_code, 200, election.text)
        result = election.json()["state"]["career_overview"]
        self.assertIn(result["result"], {"won", "lost"})
        self.assertIn(result["phase"], {"transition", "outgoing", "opposition"})

    def test_difficulty_profiles_change_game_parameters(self) -> None:
        easy = get_difficulty("tranquilo")
        normal = get_difficulty("normal")
        hard = get_difficulty("complicado")
        realism = get_difficulty("realismo_puro")
        self.assertLess(easy["event_pressure"], normal["event_pressure"])
        self.assertGreater(hard["opposition_pressure"], normal["opposition_pressure"])
        self.assertLess(hard["coalition_flexibility"], normal["coalition_flexibility"])
        self.assertGreater(realism["economic_volatility"], hard["economic_volatility"])
        self.assertLess(realism["opposition_pressure"], hard["opposition_pressure"])
        self.assertGreater(event_severity_weights(hard["event_pressure"])[2], event_severity_weights(normal["event_pressure"])[2])
        self.assertGreater(adjust_coalition_probability(.55, easy["coalition_flexibility"]), .55)
        self.assertLess(adjust_coalition_probability(.55, hard["coalition_flexibility"]), .55)
        self.assertLess(election_margin(0, 0, hard["opposition_pressure"]), election_margin(0, 0, normal["opposition_pressure"]))

    def test_public_work_and_diplomatic_trip_use_the_shared_budget_and_calendar(self) -> None:
        self.deliver_inaugural_address()
        budget = self.client.get("/api/budget").json()
        affordable_work = next(item for item in budget["works"]["options"] if item["affordable"])
        contractor = budget["works"]["contractors"][0]
        started_work = self.client.post("/api/budget/works/start", json={
            "work_id": affordable_work["id"], "contractor_id": contractor["id"],
        })
        self.assertEqual(started_work.status_code, 200, started_work.text)
        self.assertGreater(started_work.json()["budget"]["works"]["annual_committed_bi"], 0)

        before_visit = self.client.get("/api/game").json()["date"]
        before_relation = next(item["relation"] for item in self.client.get("/api/diplomacy").json()["countries"] if item["code"] == "ARG")
        visit = self.client.post("/api/diplomacy/visit", json={"country_code": "ARG", "agenda": "trade"})
        self.assertEqual(visit.status_code, 200, visit.text)
        self.assertEqual(visit.json()["state"]["date"], before_visit)

        days = visit.json()["result"]["duration_days"]
        returned = self.client.post("/api/game/advance", json={"days": days})
        self.assertEqual(returned.status_code, 200, returned.text)
        diplomacy = self.client.get("/api/diplomacy").json()
        after_relation = next(item["relation"] for item in diplomacy["countries"] if item["code"] == "ARG")
        self.assertIsNone(diplomacy["active_trip"])
        self.assertGreater(after_relation, before_relation)

    def test_saves_are_isolated_by_player_id(self) -> None:
        token = set_player_id("player-a")
        try:
            save_state({"date": "2027-01-01", "owner": "player-a"})
        finally:
            reset_player_id(token)

        token = set_player_id("player-b")
        try:
            self.assertIsNone(load_state())
        finally:
            reset_player_id(token)

        token = set_player_id("player-a")
        try:
            self.assertEqual(load_state(), {"date": "2027-01-01", "owner": "player-a"})
        finally:
            reset_player_id(token)

    def test_cognito_subject_scopes_api_saves_to_each_player(self) -> None:
        config = {
            "COGNITO_REGION": "us-east-2",
            "COGNITO_USER_POOL_ID": "us-east-2_example",
            "COGNITO_CLIENT_ID": "browser-client",
        }

        def claims_for_token(token: str, *_args, **_kwargs) -> dict[str, str]:
            return {
                "iss": "https://cognito-idp.us-east-2.amazonaws.com/us-east-2_example",
                "sub": token.removeprefix("token-"),
                "token_use": "access",
                "client_id": "browser-client",
            }

        with patch.dict(os.environ, config), patch("jwt.PyJWKClient") as jwks, patch("jwt.decode", side_effect=claims_for_token):
            jwks.return_value.get_signing_key_from_jwt.return_value.key = "test-public-key"
            health = self.client.get("/api/health")
            self.assertEqual(health.status_code, 200)
            unauthenticated = self.client.get("/api/game")
            self.assertEqual(unauthenticated.status_code, 401)

            player_a = self.client.patch("/api/game/dashboard", headers={"Authorization": "Bearer token-player-a"}, json={"cards": ["inflation"]})
            self.assertEqual(player_a.status_code, 200, player_a.text)
            player_a_state = self.client.get("/api/game", headers={"Authorization": "Bearer token-player-a"})
            player_b_state = self.client.get("/api/game", headers={"Authorization": "Bearer token-player-b"})
            self.assertEqual(player_a_state.status_code, 200, player_a_state.text)
            self.assertEqual(player_b_state.status_code, 200, player_b_state.text)
            self.assertEqual(player_a_state.json()["dashboard_cards"], ["inflation"])
            self.assertNotEqual(player_b_state.json()["dashboard_cards"], ["inflation"])

if __name__ == "__main__":
    unittest.main()
