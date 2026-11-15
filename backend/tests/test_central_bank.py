import unittest
from datetime import date, timedelta

from app.engine import central_bank, companies, powers
from app.engine.state import new_game, refresh_calendar_fields
from tests.test_office_powers import career_state


def president():
    s = refresh_calendar_fields(new_game())
    s["date"] = "2027-03-01"
    return s


class CopomTest(unittest.TestCase):
    def test_meets_every_45_days_and_records_history(self):
        s = president()
        c = central_bank.ensure(s)
        first = date.fromisoformat(c["next_meeting"])
        msgs = central_bank.tick(s, date(2027, 3, 1), first)
        self.assertEqual(len(msgs), 1)
        self.assertEqual(len(c["history"]), 1)
        self.assertEqual(date.fromisoformat(c["next_meeting"]), first + timedelta(days=45))

    def test_rate_moves_at_most_one_point_and_stays_in_range(self):
        s = president()
        s["metrics"]["inflation"] = 12.0
        c = central_bank.ensure(s)
        start = c["selic"]
        central_bank.meet(s, date(2027, 4, 1))
        self.assertLessEqual(abs(c["selic"] - start), 1.0)
        for i in range(30):
            central_bank.meet(s, date(2027, 4, 1) + timedelta(days=45 * (i + 1)))
        self.assertLessEqual(c["selic"], 20.0)
        self.assertGreaterEqual(c["selic"], 2.0)

    def test_subordinated_bank_cuts_more_and_loses_credibility(self):
        auto, sub = president(), president()
        for s in (auto, sub):
            s["metrics"]["inflation"] = 6.0
        powers.structure(sub)["central_bank"] = "subordinado"
        for s in (auto, sub):
            central_bank.ensure(s)
            for i in range(6):
                central_bank.meet(s, date(2027, 4, 1) + timedelta(days=45 * i))
        self.assertLess(sub["copom"]["selic"], auto["copom"]["selic"])
        self.assertLess(sub["copom"]["credibility"], auto["copom"]["credibility"])

    def test_selic_changes_debt_cost(self):
        from app.engine.fiscal import ensure_fiscal_state, refresh_fiscal_metrics
        s = president()
        ensure_fiscal_state(s)
        central_bank.ensure(s)["selic"] = 10.5
        base = refresh_fiscal_metrics(s)["interest_rate_pct"] if isinstance(refresh_fiscal_metrics(s), dict) and "interest_rate_pct" in refresh_fiscal_metrics(s) else s["fiscal"]["interest_rate_pct"]
        s["copom"]["selic"] = 13.5
        refresh_fiscal_metrics(s)
        self.assertGreater(s["fiscal"]["interest_rate_pct"], base + 0.9)

    def test_local_careers_have_no_copom(self):
        s = career_state("prefeito")
        self.assertEqual(central_bank.tick(s, date(2027, 3, 1), date(2028, 3, 1)), [])
        self.assertFalse(central_bank.overview(s)["applies"])

    def test_overview_shape(self):
        ov = central_bank.overview(president())
        for key in ("selic", "desired", "next_meeting", "credibility", "autonomy_label", "history", "pressure"):
            self.assertIn(key, ov)


class StakeTest(unittest.TestCase):
    def test_sell_stake_cuts_debt_and_changes_stake(self):
        s = president()
        before_debt = float(s["fiscal"]["debt_stock_bi"]) if "fiscal" in s else None
        out = companies.act(s, "caixa", "sell_stake", "5 pontos percentuais")
        self.assertEqual(companies.ensure(s)["caixa"]["stake"], 95.0)
        self.assertIn("vendeu", out["announcement"])
        if before_debt is not None:
            self.assertLess(float(s["fiscal"]["debt_stock_bi"]), before_debt)

    def test_cannot_cross_control_line(self):
        s = president()
        with self.assertRaises(PermissionError):
            companies.act(s, "petrobras", "sell_stake", "5 pontos percentuais")  # 53% -> 48%
        with self.assertRaises(PermissionError):
            companies.act(s, "eletrobras", "buy_stake", "10 pontos percentuais")  # 10% -> 20% ok? valid
            companies.ensure(s)["eletrobras"]["stake"] = 45.0
            companies.act(s, "eletrobras", "buy_stake", "5 pontos percentuais")  # 45 -> 50 cruza

    def test_buy_stake_adds_debt_and_cooldown(self):
        s = president()
        companies.ensure(s)
        companies.act(s, "eletrobras", "buy_stake", "5 pontos percentuais")
        self.assertEqual(companies.ensure(s)["eletrobras"]["stake"], 15.0)
        with self.assertRaises(RuntimeError):
            companies.act(s, "eletrobras", "buy_stake", "5 pontos percentuais")

    def test_stake_not_offered_for_private_without_union_stake(self):
        s = president()
        vale = next(c for c in companies.overview(s)["companies"] if c["id"] == "vale")
        self.assertFalse(any(a["key"] in {"buy_stake", "sell_stake"} for a in vale["actions"]))


if __name__ == "__main__":
    unittest.main()
