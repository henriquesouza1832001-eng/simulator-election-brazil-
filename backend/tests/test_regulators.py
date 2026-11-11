import unittest
from datetime import date, timedelta

from app.engine import powers, regulators
from app.engine.state import new_game, refresh_calendar_fields, process_legislation


def president():
    s = refresh_calendar_fields(new_game())
    s["date"] = "2027-03-01"
    return s


class RegulatorsTest(unittest.TestCase):
    def test_agu_opinion_levels(self):
        s = president()
        self.assertEqual(regulators.opinion("eco_confisco", "mp", s)["level"], "alto")
        self.assertEqual(regulators.opinion("infra_asfaltar", "decreto", s)["level"], "baixo")
        self.assertIn("art. 62", regulators.opinion("eco_confisco", "mp", s)["note"])

    def test_aligned_court_lowers_effective_risk(self):
        s = president()
        base = regulators.opinion("seg_armas_afrouxar", "decreto", s)["risk_pct"]
        s["government_appointments"] = {"judiciary": {"confirmed": [1, 2, 3, 4, 5, 6, 7]}}
        self.assertLess(regulators.opinion("seg_armas_afrouxar", "decreto", s)["risk_pct"], base)

    def test_low_risk_acts_are_not_reviewed_but_risky_ones_are(self):
        s = president()
        powers.execute(s, "infra_asfaltar", "BR-135 (MA)")
        self.assertEqual(s.get("regulators", {}).get("cases", []), [])
        s["executive_calendar"]["last_action"] = None
        powers.execute(s, "seg_armas_afrouxar")
        self.assertEqual(len(s["regulators"]["cases"]), 1)

    def test_stf_can_suspend_and_revert_a_decree(self):
        # procura uma semente em que o STF suspende (determinística por partida)
        for seed in range(1, 200):
            s = president()
            s["campaign_seed"] = seed
            powers.execute(s, "seg_armas_afrouxar")
            self.assertEqual(powers.structure(s)["guns"], "facilitado")
            case = s["regulators"]["cases"][0]
            case["risk"] = 0.95
            trust = s["metrics"]["institutional_trust"]
            msgs = regulators.tick(s, date(2027, 3, 1), date(2027, 3, 1) + timedelta(days=200))
            if s["regulators"]["decisions"] and s["regulators"]["decisions"][0]["status"] == "suspenso":
                self.assertTrue(any("suspendeu" in m for m in msgs))
                self.assertEqual(powers.structure(s)["guns"], "restrito")  # decreto suspenso volta ao regime anterior
                entry = next(e for e in s["ledger"] if e["id"] == case["ledger_id"])
                self.assertIn("STF", entry["reason"])
                return
        self.fail("nenhuma semente produziu suspensão")

    def test_overview_lists_all_regulators(self):
        ids = {r["id"] for r in regulators.overview(president())["regulators"]}
        self.assertEqual(ids, {"stf", "agu", "tcu", "pf_mp", "tse"})

    def test_low_integrity_can_trigger_investigation(self):
        hits = 0
        for seed in range(1, 120):
            s = president()
            s["campaign_seed"] = seed
            s["metrics"]["integrity"] = 10
            msgs = regulators.tick(s, date(2027, 3, 1), date(2027, 4, 1))
            hits += any("inquérito" in m for m in msgs)
        self.assertGreater(hits, 0)

    def test_approved_law_is_also_reviewed(self):
        s = president()
        powers.execute(s, "reg_reeleicao")
        bill = s["legislative_calendar"]["pending_bills"][0]
        powers.resolve_bill(s, bill, True)
        self.assertTrue(any(c["action_id"] == "reg_reeleicao" for c in s["regulators"]["cases"]))


if __name__ == "__main__":
    unittest.main()
