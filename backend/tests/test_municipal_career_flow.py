"""Fluxo completo da carreira municipal: militante → pré-candidatura → campanha → eleição de 2028 → posse ou derrota → continuação."""
from __future__ import annotations

import os
import random
import tempfile
import unittest
from datetime import date
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

START = {"name": "Marina Teste", "state_code": "SP", "municipality_id": "3550308", "spectrum": "centro_esquerda", "cause": "educacao"}
SPEECH = ("Assumo o mandato com responsabilidade, diálogo com a câmara e metas públicas verificáveis em educação, saúde e emprego, "
          "prestando contas todo mês à cidade.")
MESSAGE = "Vou ampliar vagas em creches com metas públicas, prazo definido e prestação de contas à comunidade."
PREFS = {"eleitor": ["reuniao_bairro", "ato_publico"], "militante": ["panfletagem", "abaixo_assinado", "cabo_eleitoral"],
         "filiado": ["tarefa_partido", "reuniao_partido", "buscar_padrinho"], "quadro": ["tarefa_partido", "reuniao_partido", "buscar_padrinho"]}


class MunicipalCareerFlowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old = os.environ.get("DATABASE_PATH")
        os.environ["DATABASE_PATH"] = os.path.join(self.tmp.name, "g.sqlite3")
        from app.main import app
        self.ctx = TestClient(app)
        self.c = self.ctx.__enter__()
        state = self.c.post("/api/party-path/start", json=START).json()
        self.c.headers["X-Mandato-Campaign"] = state["campaign_id"]

    def tearDown(self):
        self.ctx.__exit__(None, None, None)
        if self.old is None:
            os.environ.pop("DATABASE_PATH", None)
        else:
            os.environ["DATABASE_PATH"] = self.old
        self.tmp.cleanup()

    # ---- ajudantes -------------------------------------------------------------------------------------------
    def game(self):
        return self.c.get("/api/game").json()

    def party_day(self):
        """Um dia de vida partidária: pede filiação/cargo quando pode, faz uma ação e avança um dia."""
        ov = self.c.get("/api/party-path").json()
        stage = ov["stage"]
        if stage == "militante" and ov["next"]["ready"] and not ov["party"] and ov["affiliation"].get("status") != "analise":
            self.c.post("/api/party-path/affiliate", json={"party": "Partido Teste Renovador", "ideology": "Centro-esquerda"})
        if stage == "filiado" and ov["next"]["ready"]:
            self.c.post("/api/party-path/run-post")
        for key in PREFS.get(stage, []) + ["voluntariado", "estudar", "descansar"]:
            if self.c.post("/api/party-path/act", json={"action": key}).status_code == 200:
                break
        self.c.post("/api/game/advance", json={"days": 1})
        return ov

    def reach_launch(self, office="vereador", limit=700):
        for _ in range(limit):
            ov = self.c.get("/api/party-path").json()
            if ov["stage"] == "quadro":
                option = next(o for o in ov["next"]["offices"] if o["key"] == office)
                if option["ready"]:
                    out = self.c.post("/api/party-path/launch", json={"office": office})
                    self.assertEqual(out.status_code, 200, out.text)
                    return out.json()
            self.party_day()
        self.fail(f"não chegou à pré-candidatura a {office}")

    def run_until_result(self, campaign: bool):
        """Avança até a eleição. Com `campaign`, faz organização e atos; sem, só deixa o tempo passar."""
        phases = []
        for _ in range(140):
            g = self.game()
            co = g["career_overview"]
            if co["phase"] not in phases:
                phases.append(co["phase"])
            if co["phase"] not in {"pre_campaign", "campaign"}:
                return g, phases
            if campaign and co["phase"] == "pre_campaign" and co["can_prepare"]:
                self.c.post("/api/career/preparation", json={"action": "mobilizar_voluntariado"})
            if campaign and co["phase"] == "campaign" and co["can_act"]:
                self.c.post("/api/career/action", json={"activity_type": "comicio", "issue": "educacao", "message": MESSAGE, "municipality_id": START["municipality_id"]})
            out = self.c.post("/api/game/advance", json={"days": 7 if campaign else 30})
            self.assertEqual(out.status_code, 200, out.text)
        self.fail("a eleição não chegou")

    # ---- testes ------------------------------------------------------------------------------------------------
    def test_defeat_keeps_character_returns_to_party_and_allows_new_candidacy(self):
        self.reach_launch("vereador")
        g, phases = self.run_until_result(campaign=False)
        co = g["career_overview"]
        self.assertEqual(phases[:2], ["pre_campaign", "campaign"])          # nenhuma fase obrigatória é pulada
        self.assertEqual(g["date"], "2028-10-01")                            # o avanço para no dia da eleição
        self.assertEqual(co["result"], "lost")                               # sem campanha, não se elege
        er = co["electoral_result"]
        self.assertEqual(er["system"], "proporcional_simulado")
        self.assertFalse(er["elected"])
        self.assertGreater(er["candidate_list_rank"], er["party_seats"])     # o resultado se explica: posição na lista × cadeiras
        self.assertTrue(er["list"] and all(item["simulated"] for item in er["list"]))
        self.assertEqual(g["player_character"]["name"], "Marina Teste")      # personagem preservado
        # a vida partidária volta
        pp = g["party_path"]
        self.assertTrue(pp["active"])
        self.assertEqual(pp["stage"], "quadro")
        self.assertEqual(pp["returns"], 1)
        ov = self.c.get("/api/party-path").json()
        self.assertTrue(ov["actions"])
        # o save continua: recarregar devolve o mesmo ponto
        again = self.game()
        self.assertEqual((again["date"], again["career_overview"]["result"], again["party_path"]["stage"]), (g["date"], "lost", "quadro"))
        # nova disputa: reconstrói e lança de novo, com a derrota no histórico
        self.reach_launch("vereador")
        g2 = self.game()
        co2 = g2["career_overview"]
        self.assertEqual(co2["phase"], "pre_campaign")
        self.assertEqual(co2["election_date"], "2032-10-03")
        self.assertEqual(len(co2["history"]), 1)
        self.assertEqual(co2["history"][0]["result"], "lost")

    def test_campaign_leads_to_result_and_office_or_opposition(self):
        self.reach_launch("vereador")
        g, phases = self.run_until_result(campaign=True)
        co = g["career_overview"]
        self.assertIn(co["result"], {"won", "lost"})
        er = co["electoral_result"]
        self.assertEqual(er["elected"], co["result"] == "won")
        self.assertEqual(er["elected"], er["candidate_list_rank"] <= er["party_seats"])
        if co["result"] == "lost":
            self.assertTrue(g["party_path"]["active"])
            return
        self.assertEqual(co["phase"], "transition")
        # posse: o tempo não passa da posse sem o pronunciamento
        for _ in range(8):
            out = self.c.post("/api/game/advance", json={"days": 30})
            if out.status_code == 409:
                self.assertEqual(out.json()["action"], "inaugural_address")
                self.assertEqual(self.c.post("/api/game/inaugural-address", json={"text": SPEECH}).status_code, 200)
                break
        g = self.game()
        self.assertEqual(g["career_overview"]["phase"], "office")
        self.assertTrue(g["career_overview"]["governing"])
        # no mandato de vereador surgem acontecimentos do nível legislativo, com efeitos sobre o mandato
        from app.engine.event_library import get_library
        seen = False
        for _ in range(14):
            pending = self.c.get("/api/story").json()["pending"]
            if pending:
                ev = pending[0]
                self.assertIn("legislativo", get_library().get(ev["def"])["levels"])
                entry = self.c.post(f"/api/story/{ev['id']}/respond", json={"choice": ev["choices"][0]["id"]}).json()["entry"]
                keys = {d["key"] for d in entry["deltas"]}
                self.assertTrue(keys <= {"trust", "political_capital", "reputation", "cost_mi"}, keys)
                seen = True
                break
            self.assertEqual(self.c.post("/api/game/advance", json={"days": 30}).status_code, 200)
        self.assertTrue(seen, "nenhum acontecimento no mandato em mais de um ano")


class ProportionalModelTests(unittest.TestCase):
    def test_open_list_is_consistent_and_campaign_strength_matters(self):
        from app.engine.career import _proportional_result
        career = {"office": "vereador", "candidate_name": "X", "municipality_id": "3550308"}
        weak = strong = 0
        for i in range(300):
            a = _proportional_result(career, random.Random(f"w{i}"), 30)
            b = _proportional_result(career, random.Random(f"s{i}"), 48)
            for r in (a, b):
                self.assertEqual(r["elected"], r["candidate_list_rank"] <= r["party_seats"])
                self.assertEqual(sum(1 for item in r["list"] if item["is_player"]), 1)
                self.assertGreaterEqual(r["margin_share"], 0)
            weak += a["elected"]
            strong += b["elected"]
        self.assertLess(weak / 300, 0.08)       # sem campanha: derrota provável
        self.assertGreater(strong / 300, 0.85)  # campanha forte: vitória provável
        self.assertIsNotNone(a["candidate_votes"])   # com eleitorado do TSE, mostra votos estimados


class CareerEventCostTests(unittest.TestCase):
    def test_remixed_career_event_cost_is_applied_once(self):
        from app.engine.state import new_game
        from app.engine import story

        definition = {
            "id": "historical_cost_test", "kind": "decisao", "title": "Evento de teste", "text": "Teste.",
            "tags": [], "family": "test", "fallback": "agir",
            "choices": [{"id": "agir", "label": "Agir", "hint": "", "tone": "neutra",
                         "cost_bi": 0.02, "effects": {}, "outcome": "Feito."}],
        }
        state = new_game()
        state["career"] = {"mode": True, "phase": "office", "office": "prefeito", "reputation": 50,
                            "governance": {"budget_mi": 100, "annual_budget_mi": 1000, "trust": 50, "political_capital": 50}}
        remix_data = {"title": "Evento simulado", "text": "Teste simulado.", "places": {},
                      "intensity": 1.5, "intensity_label": "grave"}
        library = SimpleNamespace(get=lambda _event_id: definition)

        with patch("app.engine.story.get_library", return_value=library), \
             patch("app.engine.story.is_historical", return_value=True), \
             patch("app.engine.story.remix", return_value=remix_data):
            ev = story._fire(state, definition["id"], date.fromisoformat(state["date"]))
            entry = story.respond(state, ev["id"], "agir")

        self.assertEqual(ev["career_costs"]["agir"], 30.0)
        cost = next(delta for delta in entry["deltas"] if delta["key"] == "cost_mi")
        self.assertEqual(cost["delta"], -30.0)
        self.assertEqual(state["career"]["governance"]["budget_mi"], 70.0)


if __name__ == "__main__":
    unittest.main()
