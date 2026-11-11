import unittest
from datetime import date

from app.engine import office_powers as op
from app.engine import subnational_fiscal as sf
from app.engine import territory
from tests.test_office_powers import career_state


def mayor(budget=400.0, annual=400.0):
    s = career_state("prefeito", budget=budget)
    s["career"]["governance"]["annual_budget_mi"] = annual
    return s


class SubnationalFiscalTest(unittest.TestCase):
    def test_status_reports_limits_and_basis(self):
        s = mayor()
        st = sf.status(s)
        self.assertEqual(st["personnel_limit"], 54.0)
        self.assertEqual(st["rcl_mi"], 3200.0)
        self.assertEqual(st["personnel_level"], "regular")
        self.assertIn("LRF", st["basis"])

    def test_raise_increases_payroll_and_lrf_blocks_above_prudential(self):
        s = mayor()
        op.execute(s, "p_reajuste")
        self.assertEqual(sf.status(s)["personnel_pct"], 47.5)
        s["career"]["governance"]["fiscal"]["personnel_pct"] = 52.0   # acima de 95% de 54%
        s["career"]["governance"]["last_action_date"] = None
        with self.assertRaises(RuntimeError) as ctx:
            op.execute(s, "p_concurso")
        self.assertIn("LRF", str(ctx.exception))
        cat = {a["id"]: a for a in op.catalog(s, "prefeito")}
        self.assertFalse(cat["p_concurso"]["available"])
        self.assertTrue(cat["p_reduzir_folha"]["available"])

    def test_credit_adds_reserve_and_debt_and_respects_limit(self):
        s = mayor(budget=100.0, annual=400.0)
        op.execute(s, "p_credito")
        st = sf.status(s)
        self.assertEqual(st["debt_pct"], 48.0)
        self.assertEqual(st["reserve_available_mi"], 180.0)
        s["career"]["governance"]["fiscal"]["debt_pct"] = 125.0
        s["career"]["governance"]["last_action_date"] = None
        with self.assertRaises(RuntimeError):
            op.execute(s, "p_credito")

    def test_local_project_uses_office_reserve_and_recommits_next_year(self):
        s = mayor(budget=3000.0, annual=3000.0)
        s["date"] = "2029-04-10"
        item = territory.start(s, "brt_capital", "prefeito", "SP", "3550308")
        # R$ 1,2 bi em 30 meses -> parcela anual de R$ 480 mi
        self.assertAlmostEqual(s["career"]["governance"]["budget_mi"], 3000 - 480.0, delta=1.0)
        self.assertTrue(sf.status(s)["commitments"])
        sf.tick(s, date(2029, 12, 30), date(2030, 1, 5))
        self.assertLess(s["career"]["governance"]["budget_mi"], 3000.0 - 400.0)

    def test_project_refused_when_reserve_is_short(self):
        s = mayor(budget=10.0, annual=10.0)
        with self.assertRaises(PermissionError):
            territory.start(s, "brt_capital", "prefeito", "SP", "3550308")

    def test_monthly_summary_and_over_limit_penalty(self):
        s = mayor()
        sf.ensure(s)
        fiscal = s["career"]["governance"]["fiscal"]
        fiscal["personnel_pct"] = 54.5
        trust = s["career"]["governance"]["trust"]
        msgs = sf.tick(s, date(2029, 4, 10), date(2029, 5, 12))
        self.assertTrue(fiscal["summaries"])
        self.assertLess(s["career"]["governance"]["trust"], trust)
        self.assertTrue(any("LRF" in m for m in msgs))


if __name__ == "__main__":
    unittest.main()
