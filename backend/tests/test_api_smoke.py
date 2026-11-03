"""Small API-level smoke tests for the first playable release."""
from __future__ import annotations

import json
import os
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from fastapi import HTTPException

from app.db import (
    archive_state, connect, list_archives, load_state, recent_actions, record_action,
    reset_campaign_id, reset_player_id, restore_archive, save_state,
    set_campaign_id, set_player_id, useful_corrections,
)
from app.engine.difficulty import adjust_coalition_probability, election_margin, event_severity_weights, get_difficulty
from app.engine.appointments import appoint_minister, appointments_overview
from app.engine.career import advance_career, career_overview, governance_actions_for, is_career_governing, perform_career_action, perform_career_preparation, perform_governance_action, resolve_career_election, start_career
from app.engine.fiscal import fiscal_overview
from app.engine.issues import canonical_issue_ids
from app.engine.rules import apply_effects, forecast
from app.main import app, require_presidential_authority
from app.engine.state import advance_state, new_game


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

        cities = self.client.get("/api/geography/municipalities", params={"state_code": "SP", "q": "sao paulo"})
        self.assertEqual(cities.status_code, 200, cities.text)
        self.assertEqual(cities.json()["catalog"]["count"], 5571)
        self.assertEqual(cities.json()["catalog"]["reference_date"], "2026-07-01")
        self.assertEqual(cities.json()["items"][0]["ibge_code"], "3550308")
        self.assertEqual(canonical_issue_ids("servicos"), ("saude", "educacao"))

        campaign_topics = self.client.get("/api/game").json()["campaign_overview"]["issue_options"]
        campaign_topic_ids = {item["key"] for item in campaign_topics}
        self.assertTrue({"saude", "educacao"}.issubset(campaign_topic_ids))
        self.assertNotIn("servicos", campaign_topic_ids)

    def test_municipality_code_must_match_candidate_state(self) -> None:
        response = self.client.post("/api/career/start", json={
            "office": "prefeito", "state_code": "MG", "municipality": "",
            "municipality_id": "3550308", "party": "Partido da RenovaÃ§Ã£o",
            "ideology": "Centro", "candidate_name": "Candidatura de teste",
        })
        self.assertEqual(response.status_code, 422)

    def test_measure_preview_failure_is_a_controlled_gateway_error(self) -> None:
        with patch("app.main.interpret", new=AsyncMock(side_effect=RuntimeError("model unavailable"))):
            response = self.client.post("/api/measures/preview", json={"text": "Revisar compras públicas para reduzir desperdício."})
        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json()["detail"], "A interpretação não pôde ser gerada. Tente novamente.")

    def test_measure_forecast_matches_applied_delta_and_marks_legislative_uncertainty(self) -> None:
        state = new_game()
        interpretation = {
            "category": "security", "instrument": "Ato do Executivo", "fiscal_cost_bi": 20,
        }
        preview = forecast(state, interpretation)
        apply_effects(state, interpretation)
        self.assertEqual(preview["impact_if_applied"][0]["after"], state["metrics"]["primary_balance"])
        self.assertEqual(preview["impact_if_applied"][1]["after"], state["metrics"]["gdp_growth"])
        self.assertEqual(preview["impact_if_applied"][2]["after"], state["metrics"]["approval"])
        self.assertEqual(preview["timeline"][0]["metrics"][0]["after"], state["metrics"]["primary_balance"])

        bill = forecast(new_game(), {
            "category": "public_investment", "instrument": "Projeto de Lei", "fiscal_cost_bi": 0,
        })
        self.assertEqual(bill["timeline"][0]["metrics"][1]["delta"], 0)
        self.assertTrue(bill["timeline"][1]["conditional_on_approval"])
        self.assertIn("Se aprovada", bill["timeline"][1]["status"])
        self.assertEqual(bill["timeline"][2]["metrics"][1]["delta"], 0.02)
    def test_structured_interpretation_correction_is_saved_for_offline_training(self) -> None:
        proposal = "Ampliar a rede de saneamento com investimento público planejado."
        preview = self.client.post("/api/measures/preview", json={"text": proposal})
        self.assertEqual(preview.status_code, 200, preview.text)
        response = self.client.post("/api/learning/corrections", json={
            "original_text": proposal,
            "corrected_interpretation": "Categoria e instrumento revisados pelo jogador.",
            "labels": {"category": "public_investment", "instrument": "Projeto de Lei"},
        })
        self.assertEqual(response.status_code, 200, response.text)
        self.assertTrue(response.json()["training_labels_saved"])
        with connect() as db:
            row = db.execute(
                "SELECT labels_json, interpretation_log_id FROM interpretation_corrections ORDER BY id DESC LIMIT 1"
            ).fetchone()
        self.assertEqual(json.loads(row["labels_json"]), {
            "category": "public_investment", "instrument": "Projeto de Lei",
        })
        self.assertEqual(row["interpretation_log_id"], preview.json()["interpretation_id"])

        second_correction = self.client.post("/api/learning/corrections", json={
            "original_text": proposal,
            "corrected_interpretation": "Instrumento também revisado pelo jogador.",
            "labels": {"instrument": "Ato do Executivo"},
        })
        self.assertEqual(second_correction.status_code, 200, second_correction.text)
        from app.ai.trainer import load_reviewed_examples
        examples = load_reviewed_examples()["local"]
        self.assertEqual(examples[0]["labels"], {
            "category": "public_investment", "instrument": "Ato do Executivo",
        })
        with connect() as db:
            db.execute(
                "INSERT INTO interpretation_corrections (original_text, corrected_interpretation, labels_json, player_id) "
                "VALUES (?, ?, ?, ?)",
                ("Outro jogador revisou esta proposta de imposto", "Correção privada",
                 json.dumps({"category": "tax_change"}), "aaa-other-player"),
            )
        self.assertEqual(set(load_reviewed_examples()), {"local", "aaa-other-player"})
        self.assertEqual(set(load_reviewed_examples("local")), {"local"})
        retrieved = useful_corrections(proposal)
        self.assertEqual(len(retrieved), 1)
        self.assertEqual(retrieved[0]["corrected_labels"], examples[0]["labels"])

        evaluation = self.client.post("/api/learning/train", json={})
        self.assertEqual(evaluation.status_code, 200, evaluation.text)
        self.assertFalse(evaluation.json()["live_interpreter_changed"])
        self.assertFalse(evaluation.json()["fields"]["category"]["ready"])
        self.assertEqual(evaluation.json()["reviewed_proposals"], 1)
        self.assertEqual(evaluation.json()["fields"]["category"]["classes"], {"public_investment": 1})

        invalid = self.client.post("/api/learning/corrections", json={
            "original_text": proposal,
            "corrected_interpretation": "Rótulo inválido.",
            "labels": {"category": "valor_inventado"},
        })
        self.assertEqual(invalid.status_code, 422)

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
        self.assertEqual(overview["municipality_id"], "3550308")
        self.assertEqual(overview["municipality_profile"]["population_reference_year"], 2026)
        self.assertEqual(overview["election_date"], "2028-10-01")
        self.assertEqual(overview["campaign_start_date"], "2028-07-03")
        self.assertFalse(overview["inaugural_address"]["required"])

    def test_named_campaigns_keep_saves_actions_and_archives_separate(self) -> None:
        first_id = "a" * 32
        first_token = set_campaign_id(first_id)
        try:
            first_state = {"date": "2027-01-01", "owner": "first"}
            save_state(first_state)
            record_action("2027-01-01", "test", "Ação da primeira", "", {}, [])
            first_archive = archive_state(first_state.copy(), "Snapshot da primeira")
            self.assertEqual(recent_actions()[0]["title"], "Ação da primeira")
            self.assertEqual(len(list_archives()), 1)
        finally:
            reset_campaign_id(first_token)

        second_id = "b" * 32
        second_token = set_campaign_id(second_id)
        try:
            save_state({"date": "2027-02-01", "owner": "second"})
            record_action("2027-02-01", "test", "Ação da segunda", "", {}, [])
            self.assertEqual(load_state(), {"date": "2027-02-01", "owner": "second"})
            self.assertEqual([item["title"] for item in recent_actions()], ["Ação da segunda"])
            self.assertEqual(list_archives(), [])
            self.assertIsNone(restore_archive(first_archive))
        finally:
            reset_campaign_id(second_token)

        first_token = set_campaign_id(first_id)
        try:
            self.assertEqual(load_state(), {"date": "2027-01-01", "owner": "first"})
            self.assertEqual([item["title"] for item in recent_actions()], ["Ação da primeira"])
            self.assertEqual(restore_archive(first_archive), {"date": "2027-01-01", "owner": "first", "action_log_end_id": 1})
        finally:
            reset_campaign_id(first_token)

    def test_new_named_campaign_can_be_switched_without_overwriting_default(self) -> None:
        default = self.client.get("/api/game", headers={"X-Mandato-Campaign": "default"})
        self.assertEqual(default.status_code, 200, default.text)

        started = self.client.post("/api/career/start", headers={"X-Mandato-Campaign": "default"}, json={
            "office": "prefeito", "state_code": "SP", "municipality": "São Paulo",
            "party": "MDB — Movimento Democrático Brasileiro", "ideology": "Centro",
            "candidate_name": "Ana Exemplo", "character": {"name": "Ana Exemplo"},
            "difficulty": "normal", "new_game": True, "campaign_name": "Prefeitura de teste",
        })
        self.assertEqual(started.status_code, 200, started.text)
        campaign_id = started.json()["state"]["campaign_id"]
        self.assertRegex(campaign_id, r"^[a-f0-9]{32}$")
        self.assertEqual(started.json()["state"]["campaign_name"], "Prefeitura de teste")

        reopened = self.client.get("/api/game", headers={"X-Mandato-Campaign": campaign_id})
        self.assertEqual(reopened.status_code, 200, reopened.text)
        self.assertEqual(reopened.json()["career_overview"]["office"], "prefeito")
        unchanged_default = self.client.get("/api/game", headers={"X-Mandato-Campaign": "default"})
        self.assertEqual(unchanged_default.status_code, 200, unchanged_default.text)
        self.assertEqual(unchanged_default.json()["campaign_id"], "default")
        self.assertIsNone(unchanged_default.json()["career_overview"])

        campaigns = self.client.get("/api/campaigns", headers={"X-Mandato-Campaign": "default"})
        self.assertEqual(campaigns.status_code, 200, campaigns.text)
        self.assertIn(campaign_id, {item["campaign_id"] for item in campaigns.json()["items"]})
        activated = self.client.post(f"/api/campaigns/{campaign_id}/activate", headers={"X-Mandato-Campaign": "default"}, json={})
        self.assertEqual(activated.status_code, 200, activated.text)
        self.assertEqual(activated.json()["state"]["campaign_id"], campaign_id)

    def test_career_campaign_action_and_election_complete(self) -> None:
        started = self.client.post("/api/career/start", json={
            "office": "prefeito", "state_code": "MG", "municipality": "Belo Horizonte",
            "party": "Partido da RenovaÃ§Ã£o", "ideology": "Centro", "candidate_name": "Candidatura de teste",
        })
        self.assertEqual(started.status_code, 200, started.text)

        overview = started.json()["state"]["career_overview"]
        self.assertEqual(overview["municipality_id"], "3106200")
        self.assertEqual(overview["municipality_profile"]["city_size"], "metropole")
        while not overview["campaign_active"]:
            days = min(90, max(1, overview["days_until_campaign"]))
            advanced = self.client.post("/api/game/advance", json={"days": days})
            self.assertEqual(advanced.status_code, 200, advanced.text)
            overview = advanced.json()["state"]["career_overview"]

        action_date = date.fromisoformat(self.client.get("/api/game").json()["date"])
        action = self.client.post("/api/career/action", json={
            "activity_type": "comicio", "issue": "educacao",
            "municipality_id": "3106200",
            "message": "Vamos publicar metas para melhorar escolas e postos de saúde, com prazo, equipe e prestação de contas.",
        })
        self.assertEqual(action.status_code, 200, action.text)
        self.assertGreater(action.json()["result"]["score"], 0)
        self.assertEqual(action.json()["result"]["days_cost"], 2)
        self.assertEqual(date.fromisoformat(action.json()["state"]["date"]), action_date + timedelta(days=2))
        activity = action.json()["state"]["career_overview"]["activities"][0]
        self.assertEqual(activity["type"], "comicio")
        self.assertEqual(activity["municipality_id"], "3106200")
        self.assertEqual(activity["municipality_name"], "Belo Horizonte")
        self.assertGreater(activity["municipality_support"], 0)
        self.assertEqual(activity["city_reach_multiplier"], 0.7)

        cooldown = self.client.post("/api/game/advance", json={"days": 5})
        self.assertEqual(cooldown.status_code, 200, cooldown.text)
        debate = self.client.post("/api/career/action", json={
            "activity_type": "debate", "issue": "mobilidade",
            "message": "Vamos publicar metas de transporte, prazo de 100 dias, custo previsto e fiscalização mensal dos moradores.",
        })
        self.assertEqual(debate.status_code, 200, debate.text)
        debate_result = debate.json()["result"]["debate"]
        self.assertIn(debate_result["outcome"], {"won", "tied", "lost"})
        self.assertEqual(debate_result["scope"], "municipal")
        self.assertTrue(debate_result["opponent_reply"])
        self.assertEqual(debate_result["question"], debate.json()["state"]["career_overview"]["debate_prompts"]["mobilidade"]["question"])
        self.assertIn(debate_result["support_delta"], {-0.5, 0.1, 0.6})
        self.assertEqual(debate.json()["state"]["career_overview"]["activities"][0]["debate"], debate_result)

        election = self.client.post("/api/game/advance", json={"days": 90})
        self.assertEqual(election.status_code, 200, election.text)
        result = election.json()["state"]["career_overview"]
        self.assertIn(result["result"], {"won", "lost"})
        self.assertIn(result["phase"], {"transition", "outgoing", "opposition"})

    def test_pre_campaign_preparation_uses_candidate_fund_without_changing_poll(self) -> None:
        started = self.client.post("/api/career/start", json={
            "office": "presidente", "state_code": "DF", "party": "Partido da RenovaÃ§Ã£o",
            "ideology": "Centro", "candidate_name": "Candidatura de teste",
        })
        self.assertEqual(started.status_code, 200, started.text)
        before = started.json()["state"]["career_overview"]
        response = self.client.post("/api/career/preparation", json={"action": "mapear_prioridades"})
        self.assertEqual(response.status_code, 200, response.text)
        result = response.json()["result"]
        after = response.json()["state"]["career_overview"]
        self.assertEqual(result["preparation"]["organization_gain"], 0.75)
        self.assertEqual(result["days_cost"], 1)
        self.assertAlmostEqual(after["campaign_fund_mi"], before["campaign_fund_mi"] - 0.04)
        self.assertEqual(after["poll_support"], before["poll_support"])
        self.assertEqual(after["pre_campaign_organization"], 0.75)
        self.assertFalse(after["can_prepare"])
        self.assertEqual(after["preparation_wait_days"], 29)

        too_soon = self.client.post("/api/career/preparation", json={"action": "reunir_partido"})
        self.assertEqual(too_soon.status_code, 409)
        self.assertIn("29 dia(s)", too_soon.json()["detail"])

        advanced = self.client.post("/api/game/advance", json={"days": 29})
        self.assertEqual(advanced.status_code, 200, advanced.text)
        self.assertTrue(advanced.json()["state"]["career_overview"]["can_prepare"])

    def test_pre_campaign_organization_contributes_to_election_result(self) -> None:
        ordinary = new_game()
        organized = new_game()
        for state in (ordinary, organized):
            state["date"] = "2030-07-08"
            start_career(state, "presidente", "DF", "", "Partido da RenovaÃ§Ã£o", "Centro", "Candidata de teste")
        organized["career"]["pre_campaign_organization"] = 1.5
        resolve_career_election(ordinary, date(2030, 10, 6))
        resolve_career_election(organized, date(2030, 10, 6))
        self.assertAlmostEqual(organized["career"]["vote_share"] - ordinary["career"]["vote_share"], 1.5)

    def test_pre_campaign_preparation_is_closed_during_official_campaign(self) -> None:
        state = new_game()
        state["date"] = "2030-07-08"
        start_career(state, "presidente", "DF", "", "Partido da RenovaÃ§Ã£o", "Centro", "Candidata de teste")
        with self.assertRaisesRegex(ValueError, "antes da abertura oficial"):
            perform_career_preparation(state, "mapear_prioridades")

    def test_public_campaign_polls_have_reproducible_dates_and_report_uncertainty(self) -> None:
        state = new_game()
        state["date"] = "2030-07-08"
        start_career(state, "presidente", "DF", "", "Partido da RenovaÃ§Ã£o", "Centro", "Candidatura de teste")
        first = career_overview(state)
        poll = first["latest_public_poll"]
        self.assertEqual(poll["date"], first["campaign_start_date"])
        self.assertEqual(poll["sample_size"], 1800)
        self.assertEqual(poll["margin_of_error"], 2.3)
        self.assertAlmostEqual(poll["candidate_support"] + poll["other_candidates_support"], 100.0)
        self.assertTrue(poll["simulated"])

        replay = new_game()
        replay["date"] = "2030-07-08"
        start_career(replay, "presidente", "DF", "", "Partido da RenovaÃ§Ã£o", "Centro", "Candidatura de teste")
        self.assertEqual(replay["career"]["public_polls"], state["career"]["public_polls"])

        state, _ = advance_state(state, 30)
        later = career_overview(state)
        self.assertEqual(later["latest_public_poll"]["date"], "2030-08-07")
        self.assertEqual(len(later["public_polls"]), 2)

    def test_campaign_actions_target_valid_cities_within_the_office_scope(self) -> None:
        message = "Vamos publicar prazos para melhorar o transporte e fiscalizar cada obra com transparência."
        governor_state = new_game()
        governor_state["date"] = "2030-07-08"
        start_career(governor_state, "governador", "MG", "", "Partido da Renovação", "Centro", "Candidata estadual")

        with self.assertRaisesRegex(ValueError, "estado da candidatura"):
            perform_career_action(governor_state, "comicio", "mobilidade", message, municipality_id="3550308")

        activity = perform_career_action(
            governor_state, "comicio", "mobilidade", message, municipality_id="3106200",
        )["activity"]
        self.assertEqual(activity["municipality_id"], "3106200")
        self.assertEqual(activity["municipality_name"], "Belo Horizonte")
        self.assertEqual(activity["municipality_state_code"], "MG")
        self.assertEqual(activity["travel_days"], 0)
        self.assertEqual(activity["days_cost"], 2)
        self.assertEqual(career_overview(governor_state)["campaign_city_support"][0]["municipality_id"], "3106200")

        governor_state["date"] = "2030-07-15"
        traveled = perform_career_action(
            governor_state, "comicio", "mobilidade", message, municipality_id="3170206",
        )
        self.assertEqual(traveled["days_cost"], 3)
        self.assertEqual(traveled["activity"]["travel_days"], 1)
        self.assertEqual(traveled["activity"]["travel_from_municipality_id"], "3106200")
        self.assertEqual(career_overview(governor_state)["campaign_team_location"]["municipality_id"], "3170206")

        governor_state["date"] = "2030-07-22"
        remote = perform_career_action(
            governor_state, "rede_vitrine", "mobilidade", message, municipality_id="3170206",
        )
        self.assertEqual(remote["activity"]["travel_days"], 0)
        self.assertEqual(remote["days_cost"], 1)

        president_state = new_game()
        president_state["date"] = "2030-07-08"
        start_career(president_state, "presidente", "DF", "", "Partido da Renovação", "Centro", "Candidato nacional")
        national_activity = perform_career_action(
            president_state, "comicio", "mobilidade", message, municipality_id="3550308",
        )["activity"]
        self.assertEqual(national_activity["municipality_name"], "São Paulo")
        self.assertEqual(national_activity["municipality_state_code"], "SP")
        self.assertEqual(national_activity["travel_days"], 2)
        self.assertEqual(national_activity["days_cost"], 4)

    def test_municipal_campaign_cannot_leave_its_electoral_city(self) -> None:
        state = new_game()
        state["date"] = "2028-07-03"
        start_career(state, "prefeito", "MG", "Belo Horizonte", "Partido da Renovação", "Centro", "Candidata municipal", municipality_id="3106200")
        with self.assertRaisesRegex(ValueError, "município da candidatura"):
            perform_career_action(
                state, "comicio", "educacao",
                "Vamos publicar metas de educação, prazos, equipes e resultados para cada escola.",
                municipality_id="3170206",
            )

    def test_incumbent_keeps_governing_through_term_end_after_election(self) -> None:
        state = new_game()
        state["date"] = "2030-09-01"
        start_career(state, "presidente", "DF", "", "Partido da Renovação", "Centro", "Presidência de teste")
        career = state["career"]
        career["phase"] = "campaign"
        career["office_start"] = "2027-01-05"
        career["term_end"] = "2031-01-04"
        career["election_date"] = "2030-10-06"
        career["poll_support"] = 0.0
        career["governance"] = {
            "budget_mi": 100000.0, "annual_budget_mi": 100000.0,
            "investment_commitment_mi": 0.0, "budget_year": 2030,
            "budget_price_index": 1.0, "trust": 50.0, "delivery": 0.0,
            "political_capital": 50.0, "actions": [], "pipeline": [], "outcomes": {},
        }
        overview = career_overview(state)
        self.assertTrue(overview["campaign_active"])
        self.assertTrue(overview["governing"])
        require_presidential_authority(state, "Ação federal de teste")
        perform_governance_action(state, "public_report")

        state["date"] = "2030-10-06"
        election_message = resolve_career_election(state, date(2030, 10, 6))
        self.assertEqual(career["result"], "lost")
        self.assertEqual(career["phase"], "outgoing")
        self.assertEqual(career["transition_date"], "2031-01-05")
        self.assertIn("04/01/2031", election_message)

        overview = career_overview(state)
        self.assertTrue(overview["governing"])
        self.assertTrue(overview["governance_actions"])
        perform_governance_action(state, "public_report")

        state["date"] = "2031-01-04"
        self.assertTrue(career_overview(state)["governing"])
        perform_governance_action(state, "public_report")
        state["date"] = "2031-01-05"
        self.assertFalse(career_overview(state)["governing"])
        self.assertFalse(is_career_governing(career, date(2031, 1, 5)))
        legacy_caretaker = {"phase": "outgoing", "office": "presidente", "office_start": "2027-01-05", "term_years": 4}
        self.assertTrue(is_career_governing(legacy_caretaker, date(2031, 1, 4)))
        self.assertFalse(is_career_governing(legacy_caretaker, date(2031, 1, 5)))
        with self.assertRaises(HTTPException) as error:
            require_presidential_authority(state, "Ação federal de teste")
        self.assertEqual(error.exception.status_code, 403)
        with self.assertRaises(ValueError):
            perform_governance_action(state, "public_report")

        advance_career(state, date(2031, 1, 4), date(2031, 1, 5))
        self.assertEqual(career["phase"], "opposition")

    def test_reelected_incumbent_remains_in_office_until_next_inauguration(self) -> None:
        state = new_game()
        state["date"] = "2030-10-06"
        start_career(state, "presidente", "DF", "", "Partido da Renovação", "Centro", "Presidência de teste")
        career = state["career"]
        career.update({
            "phase": "campaign", "office_start": "2027-01-05", "term_end": "2031-01-04",
            "election_date": "2030-10-06", "poll_support": 100.0,
        })
        resolve_career_election(state, date(2030, 10, 6))
        self.assertEqual(career["result"], "won")
        self.assertEqual(career["phase"], "transition")
        self.assertEqual(career["transition_date"], "2031-01-05")
        self.assertTrue(career_overview(state)["governing"])

    def test_executive_mandate_actions_follow_scope_and_inflation(self) -> None:
        career = {
            "mode": True, "phase": "office", "office": "prefeito", "scope": "municipal",
            "municipality": "Belo Horizonte", "municipality_id": "3106200", "state_name": "Minas Gerais", "state_code": "MG",
            "group_support": {}, "governance": {
                "budget_mi": 350.0, "annual_budget_mi": 350.0, "budget_year": 2027,
                "budget_price_index": 1.0, "trust": 50.0, "delivery": 0.0,
                "political_capital": 50.0, "actions": [], "pipeline": [], "outcomes": {},
            },
        }
        actions = governance_actions_for(career, career["governance"])
        action_keys = {item["key"] for item in actions}
        self.assertIn("service_sanitation", action_keys)
        self.assertNotIn("service_security", action_keys)

        state = {"date": "2027-06-01", "career": career}
        with self.assertRaises(ValueError):
            perform_governance_action(state, "service_security")
        result = perform_governance_action(state, "service_education")
        self.assertEqual(result["days_cost"], 1)
        self.assertEqual(result["action"]["cost_mi"], 18.0)
        self.assertEqual(career["governance"]["budget_mi"], 332.0)
        self.assertEqual(career["governance"]["pipeline"][0]["kind"], "service")
        self.assertEqual(career["governance"]["pipeline"][0]["territory"], "Belo Horizonte · MG")
        career["election_date"] = "2028-10-01"
        career["term_end"] = "2031-12-31"
        due = date.fromisoformat(career["governance"]["pipeline"][0]["due_date"])
        messages = advance_career(state, due - timedelta(days=1), due)
        self.assertEqual(career["governance"]["outcomes"]["education"], 55.0)
        self.assertTrue(any("Belo Horizonte · MG" in message for message in messages))

        annual_state = {
            "metrics": {"inflation": 5.0},
            "career": {
                "mode": True, "phase": "office", "office": "prefeito",
                "election_date": "2028-10-01", "term_end": "2031-12-31",
                "governance": {"budget_mi": 100.0, "annual_budget_mi": 350.0,
                               "budget_year": 2027, "trust": 50.0, "delivery": 0.0,
                               "political_capital": 50.0, "pipeline": [], "actions": []},
            },
        }
        advance_career(annual_state, date(2027, 12, 31), date(2028, 1, 1))
        annual_governance = annual_state["career"]["governance"]
        self.assertEqual(annual_governance["budget_mi"], 350.0)
        self.assertAlmostEqual(annual_governance["budget_price_index"], 1.05)
        adjusted_cost = next(item["cost_mi"] for item in governance_actions_for(annual_state["career"], annual_governance)
                             if item["key"] == "service_education")
        self.assertEqual(adjusted_cost, 18.9)

    def test_presidential_programs_share_the_federal_investment_appropriation(self) -> None:
        state = new_game()
        state["date"] = "2027-06-01"
        state["office_status"] = "elected_official"
        state["budget"]["annual_investment_bi"] = 72.5
        state["career"] = {
            "mode": True, "phase": "office", "office": "presidente", "scope": "federal",
            "state_code": "DF", "state_name": "Distrito Federal",
            "governance": {"budget_mi": 100000.0, "annual_budget_mi": 100000.0,
                           "budget_year": 2027, "budget_price_index": 1.0, "trust": 50.0,
                           "delivery": 0.0, "political_capital": 50.0, "actions": [],
                           "pipeline": [], "outcomes": {"education": 50.0}},
        }

        action = perform_governance_action(state, "service_education")
        governance = state["career"]["governance"]
        self.assertEqual(action["action"]["cost_mi"], 4500.0)
        self.assertEqual(governance["annual_budget_mi"], 72500.0)
        self.assertEqual(governance["budget_mi"], 68000.0)
        self.assertEqual(governance["investment_commitment_mi"], 4500.0)

        state["date"] = "2027-07-02"
        state["budget"]["annual_investment_bi"] = 60.0
        health_action = perform_governance_action(state, "service_health")
        self.assertEqual(health_action["action"]["cost_mi"], 6500.0)
        self.assertEqual(governance["annual_budget_mi"], 60000.0)
        self.assertEqual(governance["budget_mi"], 49000.0)
        self.assertEqual(governance["investment_commitment_mi"], 11000.0)

        fiscal = fiscal_overview(state)
        investment = next(item for item in fiscal["primary_spending"] if item["key"] == "investment")
        self.assertEqual(investment["annual_bi"], 60.0)
        self.assertAlmostEqual(fiscal["executive_investment"]["committed_bi"], 11.0)
        self.assertAlmostEqual(fiscal["executive_investment"]["available_bi"], 49.0)
        self.assertAlmostEqual(sum(item["annual_bi"] for item in fiscal["primary_spending"]), fiscal["annual_primary_spending_bi"])

        annual_state = new_game()
        annual_state["career"] = {
            "mode": True, "phase": "office", "office": "presidente", "scope": "federal",
            "election_date": "2028-10-01", "term_end": "2031-01-04",
            "governance": {"budget_mi": 20000.0, "annual_budget_mi": 72500.0,
                           "budget_year": 2027, "budget_price_index": 1.0,
                           "investment_commitment_mi": 52500.0, "pipeline": [], "actions": []},
        }
        advance_career(annual_state, date(2027, 12, 31), date(2028, 1, 1))
        renewed = annual_state["career"]["governance"]
        self.assertEqual(renewed["budget_mi"], 100000.0)
        self.assertEqual(renewed["investment_commitment_mi"], 0.0)

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

    def test_minister_profiles_shift_presidential_campaign_group_support(self) -> None:
        state = new_game()
        baseline = dict(state["campaign"]["group_support"])
        overview = appointments_overview(state)
        ministry = overview["cabinet"][0]
        self.assertTrue(all(item["political_profile"]["simulated"] for item in ministry["candidates"]))
        self.assertIn("rural", {item["key"] for item in overview["campaign_groups"]})
        recreated = appointments_overview(new_game())["cabinet"][0]
        self.assertEqual(ministry["candidates"][0]["political_profile"], recreated["candidates"][0]["political_profile"])

        first = ministry["candidates"][0]
        result = appoint_minister(state, ministry["id"], first["id"])
        for group, change in first["political_profile"]["group_effects"].items():
            self.assertAlmostEqual(state["campaign"]["group_support"][group], baseline[group] + change)
        self.assertTrue(result["campaign_group_changes"])

        state["date"] = "2027-01-08"
        second = ministry["candidates"][1]
        appoint_minister(state, ministry["id"], second["id"])
        for group in baseline:
            expected = baseline[group] + second["political_profile"]["group_effects"].get(group, 0)
            self.assertAlmostEqual(state["campaign"]["group_support"][group], expected)

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

            started = self.client.post("/api/career/start", headers={"Authorization": "Bearer token-player-a"}, json={
                "office": "prefeito", "state_code": "SP", "municipality": "São Paulo",
                "party": "MDB — Movimento Democrático Brasileiro", "ideology": "Centro",
                "candidate_name": "Ana Exemplo", "character": {"name": "Ana Exemplo"},
                "new_game": True, "campaign_name": "Partida privada",
            })
            self.assertEqual(started.status_code, 200, started.text)
            private_campaign = started.json()["state"]["campaign_id"]
            another_player = self.client.get("/api/game", headers={
                "Authorization": "Bearer token-player-b", "X-Mandato-Campaign": private_campaign,
            })
            self.assertEqual(another_player.status_code, 200, another_player.text)
            self.assertEqual(another_player.json()["campaign_id"], "default")
            denied_activation = self.client.post(f"/api/campaigns/{private_campaign}/activate",
                headers={"Authorization": "Bearer token-player-b"}, json={})
            self.assertEqual(denied_activation.status_code, 404)

if __name__ == "__main__":
    unittest.main()
