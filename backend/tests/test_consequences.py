import unittest
from datetime import date, timedelta

from app.engine import consequences, office_powers, powers
from app.engine.state import new_game, refresh_calendar_fields
from tests.test_office_powers import career_state


def president(seed=1):
    s = refresh_calendar_fields(new_game())
    s["date"] = "2027-03-01"
    s["campaign_seed"] = seed
    return s


class ConsequencesTest(unittest.TestCase):
    def test_decision_schedules_press_and_party_reactions_that_persist(self):
        s = president()
        powers.execute(s, "seg_armas_afrouxar")
        kinds = {i["kind"] for i in s["consequences"]["scheduled"]}
        self.assertIn("imprensa", kinds)
        self.assertIn("congresso", kinds)
        consequences.tick(s, date(2027, 3, 1), date(2027, 4, 15))
        feed = s["consequences"]["feed"]
        self.assertTrue(feed)
        self.assertTrue(any("PSOL" in f["headline"] or "PT" in f["headline"] or "PL" in f["headline"] for f in feed))

    def test_opposition_is_ideologically_opposite(self):
        right = consequences._opposing_parties(0.8)
        left = consequences._opposing_parties(-0.8)
        self.assertTrue({"PSOL", "PT", "PCdoB"} & set(right))
        self.assertTrue({"PL", "NOVO", "REPUBLICANOS"} & set(left))

    def test_backlash_crisis_requires_answer_or_gets_worse(self):
        for seed in range(1, 60):
            s = president(seed)
            powers.execute(s, "eco_confisco")
            if any(i["kind"] == "crise" for i in s["consequences"]["scheduled"]):
                break
        else:
            self.fail("nenhuma semente gerou crise")
        consequences.tick(s, date(2027, 3, 1), date(2027, 5, 15))
        pending = s["consequences"]["pending"]
        self.assertEqual(len(pending), 1)
        approval = s["metrics"]["approval"]
        out = consequences.respond(s, pending[0]["id"], "liberar")
        self.assertEqual(s["consequences"]["pending"], [])
        self.assertIn("approval", out["effects"])
        # sem resposta: expira com a pior opção
        for seed in range(1, 60):
            t = president(seed)
            powers.execute(t, "eco_confisco")
            if any(i["kind"] == "crise" for i in t["consequences"]["scheduled"]):
                break
        consequences.tick(t, date(2027, 3, 1), date(2027, 5, 15))
        before = t["metrics"]["approval"]
        consequences.tick(t, date(2027, 5, 15), date(2027, 8, 1))
        self.assertEqual(t["consequences"]["pending"], [])
        self.assertLess(t["metrics"]["approval"], before)

    def test_local_action_gets_press_only_and_affects_trust(self):
        s = career_state("prefeito")
        office_powers.execute(s, "p_recapear")
        kinds = {i["kind"] for i in s["consequences"]["scheduled"]}
        self.assertEqual(kinds, {"imprensa"})
        trust = s["career"]["governance"]["trust"]
        consequences.tick(s, date(2029, 4, 10), date(2029, 5, 30))
        self.assertGreaterEqual(s["career"]["governance"]["trust"], trust)

    def test_invalid_crisis_response_is_rejected(self):
        s = president()
        with self.assertRaises(ValueError):
            consequences.respond(s, "inexistente", "x")


if __name__ == "__main__":
    unittest.main()
