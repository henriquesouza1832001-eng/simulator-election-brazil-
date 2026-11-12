import unittest
from datetime import date, timedelta

from app.engine import congress_process, events, legislature
from app.engine.state import new_game, refresh_calendar_fields


def fresh(seed=1):
    s = refresh_calendar_fields(new_game())
    s["date"] = "2027-03-01"
    s["campaign_seed"] = seed
    return s


class BalanceRulesTest(unittest.TestCase):
    def test_default_base_passes_about_half_of_neutral_bills_and_low_base_rarely(self):
        def rate(support):
            s = fresh()
            s["metrics"]["congress_support"] = support
            wins = 0
            for seed in range(1, 31):
                s["campaign_seed"] = seed
                bill = {"id": f"b{seed}", "instrument": "Projeto de Lei", "interpretation": {"category": "other"}}
                wins += legislature.roll_call(s, bill)["aprovado"]
            return wins / 30
        self.assertGreater(rate(52), 0.3)
        self.assertLess(rate(52), 0.85)
        self.assertLess(rate(35), 0.2)
        self.assertGreater(rate(75), 0.9)

    def test_unanswered_crisis_expires_after_six_months_instead_of_draining_forever(self):
        s = fresh()
        events.ensure_event_state(s)
        s["active_crises"].append({"id": "c1", "kind": "integrity", "title": "Contrato em questionamento", "date": "2027-03-01", "status": "active", "severity": 1.0,
                                   "monthly_effects": {"institutional_trust": -0.5}, "region_keys": [], "days_active": 0})
        s["event_history"].append({"id": "c1", "date": "2027-03-01", "title": "x", "outcome": "em andamento"})
        trust = s["metrics"]["institutional_trust"]
        day = date(2027, 3, 1)
        msgs = []
        for _ in range(9):
            nxt = day + timedelta(days=30)
            msgs += events.process_events(s, day, nxt)
            day = nxt
        self.assertEqual(s["active_crises"][0]["status"], "expired")
        self.assertTrue(any("perdeu força" in m for m in msgs))
        drained = trust - s["metrics"]["institutional_trust"]
        self.assertLess(drained, 4.0)   # seis meses de efeito, não quatro anos
        self.assertEqual(s["event_history"][0]["outcome"], "encerrada sem resposta do governo")

    def test_congress_base_drifts_back_toward_equilibrium(self):
        s = fresh()
        s["metrics"]["congress_support"] = 30
        for _ in range(12):
            congress_process.tick(s, date(2027, 3, 1), date(2027, 3, 31))
        self.assertGreater(s["metrics"]["congress_support"], 36)
        s["metrics"]["congress_support"] = 70
        congress_process.tick(s, date(2027, 3, 1), date(2027, 3, 31))
        self.assertLess(s["metrics"]["congress_support"], 70)

    def test_most_bills_survive_committees_at_default_conditions(self):
        from app.engine import powers
        survived = 0
        for seed in range(1, 41):
            s = fresh(seed)
            powers.execute(s, "empresa_privatizar", "Correios")
            congress_process.tick(s, date(2027, 3, 1), date(2027, 5, 1))
            survived += bool(s["legislative_calendar"]["pending_bills"])
        self.assertGreater(survived / 40, 0.55)


if __name__ == "__main__":
    unittest.main()
