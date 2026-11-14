import unittest

from app.engine import mandate_review as mr
from app.engine.state import advance_state, new_game, refresh_calendar_fields


class MandateReviewTest(unittest.TestCase):
    def fresh(self):
        s = refresh_calendar_fields(new_game())
        s["setup_pending"] = False
        return s

    def test_baseline_is_stored_and_review_reports_changes(self):
        s = self.fresh()
        advance_state(s, 30)
        self.assertIn("mandate_baseline", s)
        s["metrics"]["approval"] = s["mandate_baseline"]["metrics"]["approval"] + 10
        r = mr.review(s)
        row = next(x for x in r["metrics"] if x["key"] == "approval")
        self.assertEqual(row["delta"], 10.0)
        self.assertTrue(row["good"])
        self.assertFalse(r["final"])

    def test_grade_follows_results(self):
        good = self.fresh()
        advance_state(good, 30)
        good["metrics"].update({"approval": 80, "integrity": 90, "institutional_trust": 80})
        bad = self.fresh()
        advance_state(bad, 30)
        bad["metrics"].update({"approval": 10, "integrity": 20, "institutional_trust": 20, "unemployment": 14, "inflation": 12})
        self.assertGreater(mr.review(good)["score"], mr.review(bad)["score"])
        self.assertIn(mr.review(good)["letter"], "AB")
        self.assertIn(mr.review(bad)["letter"], "DE")

    def test_final_flag_at_end_of_term(self):
        s = self.fresh()
        advance_state(s, 30)
        s["date"] = "2031-01-02"
        self.assertTrue(mr.review(s)["final"])


if __name__ == "__main__":
    unittest.main()
