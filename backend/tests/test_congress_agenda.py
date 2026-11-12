import unittest
from datetime import date, timedelta

from app.engine import congress_agenda as ag
from app.engine import consequences
from app.engine.state import new_game, refresh_calendar_fields
from tests.test_office_powers import career_state


def fresh(seed=1):
    s = refresh_calendar_fields(new_game())
    s["date"] = "2027-03-01"
    s["campaign_seed"] = seed
    return s


def with_bill(max_seed=200):
    for seed in range(1, max_seed):
        s = fresh(seed)
        ag.tick(s, date(2027, 3, 1), date(2027, 4, 1))
        pend = [c for c in s.get("consequences", {}).get("pending", []) if c["action_id"].startswith("pauta_")]
        if pend:
            return s, pend[0]
    raise AssertionError("nenhuma semente gerou projeto")


class CongressAgendaTest(unittest.TestCase):
    def test_congress_sends_bills_to_sanction_with_four_options(self):
        s, crisis = with_bill()
        self.assertEqual([o["id"] for o in crisis["options"]], ["sancionar", "vetar_parcial", "vetar", "tacita"])
        self.assertIn("15 dias úteis", crisis["text"])
        self.assertIn("autoria", crisis["text"])

    def test_sanction_applies_effects_and_veto_schedules_override_vote(self):
        s, crisis = with_bill()
        consequences.respond(s, crisis["id"], "vetar")
        self.assertEqual(len(s["congress_agenda"]["overrides"]), 1)
        self.assertEqual(s["congress_agenda"]["overrides"][0]["scope"], "total")
        s2, crisis2 = with_bill()
        before = dict(s2["metrics"])
        consequences.respond(s2, crisis2["id"], "sancionar")
        self.assertEqual(s2["congress_agenda"]["overrides"], [])
        self.assertNotEqual(before, s2["metrics"])

    def test_override_vote_depends_on_the_base(self):
        results = {}
        for support in (20, 80):
            overridden = 0
            for seed in range(1, 25):
                s = fresh(seed)
                s["metrics"]["congress_support"] = support
                ag.schedule_override(s, "piso_saude", "total", "PT")
                ag.tick(s, date(2027, 3, 1), date(2027, 5, 1))
                overridden += bool(s["congress_agenda"]["history"] and s["congress_agenda"]["history"][0]["overridden"])
            results[support] = overridden
        self.assertGreater(results[20], results[80])   # base forte sustenta o veto; base fraca o vê derrubado

    def test_unanswered_bill_becomes_law_by_tacit_sanction(self):
        s, crisis = with_bill()
        before = s["metrics"]["institutional_trust"]
        consequences.tick(s, date(2027, 4, 1), date(2027, 6, 1))
        self.assertEqual([c for c in s["consequences"]["pending"] if c["action_id"].startswith("pauta_")], [])
        self.assertTrue(any("sem resposta" in f["headline"] for f in s["consequences"]["feed"]))

    def test_only_the_presidency_receives_bills_to_sanction(self):
        s = career_state("prefeito")
        s["date"] = "2029-04-10"
        for seed in range(1, 40):
            s["campaign_seed"] = seed
            self.assertEqual(ag.tick(s, date(2029, 4, 10), date(2029, 5, 12)), [])


if __name__ == "__main__":
    unittest.main()
