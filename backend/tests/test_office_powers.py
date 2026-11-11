import unittest

from app.engine import office_powers as op
from app.engine import powers


def career_state(office, capital=60.0, budget=100.0):
    return {"date": "2029-04-10", "campaign_seed": 11, "metrics": {},
            "career": {"mode": True, "office": office, "phase": "office", "municipality_id": "3550308", "state_code": "SP", "reputation": 50.0,
                       "inauguration_date": "2029-01-01", "term_end": "2033-01-01",
                       "governance": {"budget_mi": budget, "trust": 50.0, "political_capital": capital, "actions": []}}}


class OfficePowersTest(unittest.TestCase):
    def test_every_office_has_actions(self):
        for office in ("vereador", "prefeito", "deputado_estadual", "governador", "deputado_federal", "senador"):
            self.assertTrue([a for a in op._A if office in a["offices"]], office)

    def test_competence_is_enforced(self):
        s = career_state("vereador")
        with self.assertRaises(PermissionError):
            op.execute(s, "p_recapear")  # ação de prefeito

    def test_executive_spends_reserve_and_changes_city_indicators(self):
        s = career_state("prefeito")
        r = op.execute(s, "p_recapear")
        self.assertTrue(r["approved"])
        self.assertAlmostEqual(s["career"]["governance"]["budget_mi"], 88.0)
        self.assertGreater(s["territory"]["deltas"]["city:3550308"]["mobilidade"], 0)
        with self.assertRaises(RuntimeError):
            op.execute(s, "p_ubs")  # agenda de 30 dias

    def test_legislative_costs_capital_and_can_fail(self):
        s = career_state("vereador", capital=60)
        r = op.execute(s, "v_cpi")
        self.assertEqual(s["career"]["governance"]["political_capital"], 42.0)
        self.assertIn(r["approved"], (True, False))
        self.assertIsNotNone(r["chance"])
        low = career_state("vereador", capital=5)
        with self.assertRaises(RuntimeError):
            op.execute(low, "v_cpi")

    def test_catalog_via_powers_for_local_office(self):
        s = career_state("prefeito")
        data = powers.catalog_for(s, "prefeito", True)
        self.assertTrue(data["executable"])
        self.assertTrue(all("cost_text" in a for a in data["actions"]))


if __name__ == "__main__":
    unittest.main()
