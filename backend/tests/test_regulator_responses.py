import unittest
from datetime import date, timedelta

from app.engine import consequences, powers, regulators
from app.engine.state import new_game, refresh_calendar_fields


def president(seed=1):
    s = refresh_calendar_fields(new_game())
    s["date"] = "2027-03-01"
    s["campaign_seed"] = seed
    return s


class RegulatorResponsesTest(unittest.TestCase):
    def test_risky_act_opens_stf_defense_decision_and_agu_lowers_risk(self):
        s = president()
        powers.execute(s, "seg_armas_afrouxar")
        pending = s["consequences"]["pending"]
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0]["regulator"], "stf")
        case = s["regulators"]["cases"][0]
        before = case["risk"]
        consequences.respond(s, pending[0]["id"], "agu")
        self.assertLess(case["risk"], before)

    def test_inquiry_is_a_decision_with_consequences(self):
        for seed in range(1, 200):
            s = president(seed)
            s["metrics"]["integrity"] = 5
            msgs = regulators.tick(s, date(2027, 3, 1), date(2027, 4, 1))
            if any("inquérito" in m for m in msgs):
                break
        else:
            self.fail("sem inquérito")
        crisis = next(c for c in s["consequences"]["pending"] if c["regulator"] == "pf_mp")
        before = s["metrics"]["integrity"]
        consequences.respond(s, crisis["id"], "afastar")
        self.assertGreater(s["metrics"]["integrity"], before)

    def test_unanswered_inquiry_expires_with_worst_option(self):
        for seed in range(1, 200):
            s = president(seed)
            s["metrics"]["integrity"] = 5
            msgs = regulators.tick(s, date(2027, 3, 1), date(2027, 4, 1))
            if any("inquérito" in m for m in msgs):
                break
        before = s["metrics"]["approval"]
        consequences.tick(s, date(2027, 4, 1), date(2027, 6, 1))
        self.assertEqual([c for c in s["consequences"]["pending"] if c["regulator"] == "pf_mp"], [])
        self.assertLess(s["metrics"]["approval"], before)


if __name__ == "__main__":
    unittest.main()
