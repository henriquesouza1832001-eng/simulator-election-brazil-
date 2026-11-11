"""Testes do Congresso nominal, do placar e da coleção."""
from __future__ import annotations

import os
import tempfile
import unittest
from datetime import date, timedelta

from fastapi.testclient import TestClient

from app.engine import legislature, meta
from app.engine.state import advance_state, new_game, refresh_calendar_fields


class LegislatureTests(unittest.TestCase):
    def test_chambers_have_official_sizes_and_are_deterministic(self):
        state = new_game()
        first = legislature.composition(state)
        self.assertEqual(len(first["camara"]), 513)
        self.assertEqual(len(first["senado"]), 81)
        self.assertEqual(first, legislature.composition(state))

    def test_roll_call_counts_add_up(self):
        state = new_game()
        bill = {"id": "t1", "instrument": "PEC", "title": "x"}
        result = legislature.roll_call(state, bill)
        camara = result["camara"]
        self.assertEqual(camara["sim"] + camara["nao"] + camara["abstencao"], 513)
        self.assertEqual(camara["necessarios"], 308)
        self.assertEqual(result, legislature.roll_call(state, bill))

    def test_members_have_axes_and_ideology_moves_votes(self):
        state = refresh_calendar_fields(new_game())
        chamber = legislature.composition(state)["camara"]
        self.assertEqual(set(chamber[0]["eixos"]), set(legislature.AXES))
        bill = {"id": "soc", "instrument": "Projeto de Lei", "interpretation": {"category": "social_policy"}}
        result = legislature.roll_call(state, bill)["camara"]["votos"]
        by_id = {m["id"]: m for m in chamber}
        left = [v for v in result if by_id[v["id"]]["eixos"]["economico"] < -0.4]
        right = [v for v in result if by_id[v["id"]]["eixos"]["economico"] > 0.4]
        rate = lambda group: sum(v["voto"] == "sim" for v in group) / max(1, len(group))
        self.assertGreater(rate(left), rate(right))

    def test_pending_bill_is_voted_nominally_when_due(self):
        state = refresh_calendar_fields(new_game())
        today = date.fromisoformat(state["date"])
        state["legislative_calendar"]["pending_bills"].append({
            "id": "b1", "title": "Projeto", "instrument": "Projeto de Lei", "status": "em tramitação",
            "decision_date": (today + timedelta(days=3)).isoformat(),
            "interpretation": {"category": "other", "instrument": "Projeto de Lei", "title": "Projeto"}})
        state, _ = advance_state(state, 5)
        history = state["legislative_calendar"]["vote_history"]
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["resultado"]["camara"]["necessarios"], 257)


class CampaignWeekTests(unittest.TestCase):
    def test_week_rules(self):
        from app.engine import campaign_week as cw
        state = refresh_calendar_fields(new_game())
        view = cw.overview(state)
        self.assertEqual(view["free_actions"], 1)
        self.assertEqual(len(view["catalog"]), 17)
        voto = next(a for a in view["catalog"] if a["key"] == "voto_util")
        self.assertFalse(voto["available"])  # só a partir da semana 8
        first = cw.perform(state, "comicio", "sudeste")["result"]
        self.assertGreater(first["gain"], 0)
        with self.assertRaises(ValueError):
            cw.perform(state, "caminhada", "sul")  # sem ações livres
        cw.close_week(state)
        before = state["campaign_week"]["energy"]
        trip = cw.perform(state, "caminhada", "sul")["result"]  # outra região: custa viagem
        self.assertEqual(trip["travel_energy"], cw.TRAVEL_OTHER_REGION)
        self.assertEqual(state["campaign_week"]["energy"], before - cw.TRAVEL_OTHER_REGION - cw.ACTIONS["caminhada"]["energy"])
        cw.close_week(state)
        state["campaign_week"]["week"] = 3
        again = cw.perform(state, "comicio", "sudeste")["result"]
        self.assertLess(again["gain"], first["gain"])  # rendimento decrescente
        state["campaign_week"]["energy"] = 10
        with self.assertRaises(ValueError):
            cw.perform(state, "comicio", "sul")  # energia insuficiente


class StoryTests(unittest.TestCase):
    def _run(self, days=400):
        from app.engine import story
        state = refresh_calendar_fields(new_game())
        start = date.fromisoformat(state["date"])
        msgs: list[str] = []
        for offset in range(0, days, 30):  # como na partida: o jogador avança em passos de até 90 dias
            msgs += story.tick(state, start + timedelta(days=offset), start + timedelta(days=min(days, offset + 30)))
        return state, msgs

    def test_events_fire_with_rhythm_and_are_deterministic(self):
        state, msgs = self._run()
        again, _ = self._run()
        self.assertEqual(state["story"]["history"], again["story"]["history"])
        total = len(state["story"]["history"]) + len(state["story"]["pending"])
        self.assertGreater(total, 5)
        days = sorted(date.fromisoformat(v["last"]) for v in state["story"]["seen"].values())
        self.assertLessEqual(len(state["story"]["pending"]), 2)

    def test_event_born_during_advance_does_not_expire_in_same_advance(self):
        """Regressão: avançar 30 dias não pode resolver sozinhos acontecimentos que o jogador nunca viu."""
        from app.engine import story
        state = refresh_calendar_fields(new_game())
        start = date.fromisoformat(state["date"])
        for step in range(40):
            before = start + timedelta(days=30 * step)
            story.tick(state, before, before + timedelta(days=30))
            after = before + timedelta(days=30)
            for ev in state["story"]["pending"]:
                if ev["on"] > before.isoformat() and ev["expires"]:
                    self.assertGreaterEqual(ev["expires"], after.isoformat())
        # sem resposta do jogador, só decisões que já estavam pendentes antes de um avanço vencem; nunca informativos
        autos = [h for h in state["story"]["history"] if h["auto"]]
        self.assertTrue(autos)
        self.assertTrue(all(h["kind"] != "info" for h in autos))

    def test_unanswered_decision_uses_fallback(self):
        state, _ = self._run()
        self.assertGreaterEqual(state["story"]["counters"].get("sem_resposta", 0), 1)

    def test_respond_applies_effects_and_chains(self):
        from app.engine import story
        state = refresh_calendar_fields(new_game())
        day = date.fromisoformat(state["date"])
        ev = story._fire(state, "denuncia_assessor", day)
        approval = state["metrics"]["approval"]
        entry = story.respond(state, ev["id"], "defender")
        self.assertLess(state["metrics"]["approval"], approval)
        self.assertTrue(any(q["def"] == "cpi_pedido" for q in state["story"]["queue"]))
        with self.assertRaises(ValueError):
            story.respond(state, ev["id"], "defender")  # já resolvido
        self.assertTrue(entry["deltas"])


class DebateTests(unittest.TestCase):
    def _state_at(self, week):
        from app.engine import campaign_week as cw
        state = refresh_calendar_fields(new_game())
        cw.ensure_week_state(state)["week"] = week
        return state

    def test_refuse_costs_momentum_and_gives_extra_action(self):
        from app.engine import campaign_debate as cd, campaign_week as cw
        state = self._state_at(5)
        free_before = cw.overview(state)["free_actions"]
        out = cd.attend(state, "recusar")
        self.assertEqual(out["momentum_delta"], -1.0)
        self.assertEqual(cw.overview(state)["free_actions"], free_before + 1)
        with self.assertRaises(ValueError):
            cd.attend(state, "casa")  # já resolvido nesta semana

    def test_home_is_fixed_score_and_participation_needs_text(self):
        from app.engine import campaign_debate as cd
        state = self._state_at(7)
        with self.assertRaises(ValueError):
            cd.attend(state, "participar", "economia", "curto")
        self.assertEqual(cd.attend(state, "casa")["score"], 45)

    def test_no_debate_in_other_weeks(self):
        from app.engine import campaign_debate as cd
        with self.assertRaises(ValueError):
            cd.attend(self._state_at(2), "casa")


class GovernorTests(unittest.TestCase):
    def test_governor_refuses_then_warms_up(self):
        from app.engine import campaign_week as cw
        state = refresh_calendar_fields(new_game())
        week = cw.ensure_week_state(state)
        week["week"] = 7  # várias ações livres
        first = cw.perform(state, "palanque_governador", "sul")["result"]
        self.assertTrue(first["refused"])
        self.assertGreater(first["shortfall"], 0)
        self.assertEqual(week["promises"], 3)  # promessa não é gasta na recusa
        second = cw.perform(state, "palanque_governador", "sul")["result"]
        self.assertFalse(second["refused"])
        self.assertEqual(week["promises"], 2)
        # o apoio gera um compromisso; descumprir derruba a relação da bancada e reduz o voto a favor
        item = second["commitment"]
        bill = {"id": "cm", "instrument": "Projeto de Lei", "interpretation": {"category": "other"}}
        before = legislature.roll_call(state, bill)["camara"]
        before_yes = sum(v["voto"] == "sim" for v in before["votos"] if v["party"] == item["party"])
        legislature.resolve_commitment(state, item["id"], False)
        self.assertAlmostEqual(state["relation_delta"][item["party"]], -legislature.RELATION_BREAK_PENALTY)
        after = legislature.roll_call(state, bill)["camara"]
        after_yes = sum(v["voto"] == "sim" for v in after["votos"] if v["party"] == item["party"])
        self.assertLessEqual(after_yes, before_yes)
        with self.assertRaises(ValueError):
            legislature.resolve_commitment(state, item["id"], True)  # já resolvido


class MetaTests(unittest.TestCase):
    def test_score_has_grade_and_easy_is_unranked(self):
        state = refresh_calendar_fields(new_game())
        self.assertIn(meta.score_mandate(state)["grade"], "SABCDF")
        state["difficulty"] = "tranquilo"
        self.assertFalse(meta.score_mandate(state)["ranked"])

    def test_stamps_are_unique(self):
        ids = [s[0] for s in meta.STAMPS]
        self.assertEqual(len(ids), len(set(ids)))


class MetaApiTests(unittest.TestCase):
    def test_endpoints(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["DATABASE_PATH"] = os.path.join(tmp, "g.sqlite3")
            from app.main import app
            with TestClient(app) as client:
                self.assertEqual(client.get("/api/legislature").json()["camara_total"], 513)
                self.assertEqual(client.get("/api/ranking?quadro=geral").json()["linhas"], [])  # sem entradas de exemplo
                self.assertEqual(client.get("/api/ranking?quadro=xx").status_code, 422)
                coll = client.get("/api/collection").json()
                self.assertEqual(coll["total"], len(meta.STAMPS))
                self.assertEqual(client.post("/api/ranking/submit").status_code, 409)
                self.assertTrue(client.get("/api/diary").json()["edicoes"])
                self.assertIn("grade", client.get("/api/score").json())
                week = client.get("/api/campaign-week").json()
                self.assertEqual(week["week"], 1)
                client.post("/api/game/inaugural-address", json={"text": "Assumo com responsabilidade fiscal, diálogo com o Congresso e metas públicas verificáveis em educação, saúde e emprego, prestando contas todo mês ao país."})
                done = client.post("/api/campaign-week/act", json={"action": "comicio", "region": "sudeste"})
                self.assertEqual(done.status_code, 200)
                self.assertEqual(client.post("/api/campaign-week/act", json={"action": "radio"}).status_code, 409)
                self.assertEqual(client.post("/api/campaign-week/close").json()["overview"]["week"], 2)


if __name__ == "__main__":
    unittest.main()
