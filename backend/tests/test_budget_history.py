import unittest
from datetime import date

from app.engine import budget_history as bh
from app.engine import powers
from app.engine.state import advance_state, new_game, refresh_calendar_fields


def fresh():
    s = refresh_calendar_fields(new_game())
    s["date"] = "2027-03-01"
    s["setup_pending"] = False
    return s


class BudgetHistoryTest(unittest.TestCase):
    def test_monthly_snapshot_has_planned_and_executed_by_function(self):
        s = fresh()
        bh.tick(s, date(2027, 3, 1), date(2027, 3, 15))
        self.assertEqual(s["budget_history"]["months"], [])
        bh.tick(s, date(2027, 3, 15), date(2027, 4, 2))
        m = s["budget_history"]["months"][0]
        self.assertEqual(m["month"], "2027-03")
        self.assertAlmostEqual(m["functions"]["education"]["planned"], 18.0 / 12, places=3)
        self.assertEqual(m["functions"]["education"]["planned"], m["functions"]["education"]["executed"])

    def test_one_off_action_cost_shows_up_as_overrun_in_its_function(self):
        s = fresh()
        powers.execute(s, "infra_asfaltar", "BR-135 (MA)")
        bh.tick(s, date(2027, 3, 1), date(2027, 4, 2))
        m = s["budget_history"]["months"][-1]["functions"]["logistics"]
        self.assertGreater(m["executed"], m["planned"])
        ov = bh.overview(s)
        row = next(r for r in ov["ytd"] if r["function"] == "logistics")
        self.assertGreater(row["difference_bi"], 0)

    def test_advance_state_records_history(self):
        s = fresh()
        for _ in range(3):
            advance_state(s, 30)
        self.assertGreaterEqual(len(s["budget_history"]["months"]), 2)
        self.assertIn("note", bh.overview(s))


if __name__ == "__main__":
    unittest.main()
