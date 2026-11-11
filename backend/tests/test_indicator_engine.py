import unittest
from datetime import date

from app.engine import indicator_engine as ie
from app.engine.state import new_game, refresh_calendar_fields, advance_state


class IndicatorEngineTest(unittest.TestCase):
    def fresh(self):
        s = refresh_calendar_fields(new_game())
        return s

    def test_initial_nation_has_real_and_default_values(self):
        s = self.fresh()
        n = ie.ensure(s)
        self.assertIn("idhm", n["values"])
        self.assertIn("juros", n["values"])
        self.assertAlmostEqual(n["values"]["inflacao"], s["metrics"]["inflation"])

    def test_unemployment_rise_propagates_to_poverty_and_gini(self):
        s = self.fresh()
        n = ie.ensure(s)
        poverty, gini = n["values"]["pobreza"], n["values"]["gini"]
        s["metrics"]["unemployment"] += 3.0
        ie.tick(s, date(2027, 1, 1), date(2027, 2, 1))
        self.assertGreater(n["values"]["pobreza"], poverty)
        self.assertGreater(n["values"]["gini"], gini)
        self.assertTrue(n["history"])

    def test_national_shock_reaches_municipalities(self):
        from app.engine import territory
        s = self.fresh()
        ie.ensure(s)
        before = {i["id"]: i["value"] for i in territory.city_indicators(s, "3106200")["indicators"]}
        s["metrics"]["unemployment"] += 4.0
        ie.tick(s, date(2027, 1, 1), date(2027, 2, 1))
        after = {i["id"]: i["value"] for i in territory.city_indicators(s, "3106200")["indicators"]}
        self.assertGreater(after["pobreza"], before["pobreza"])

    def test_advance_state_ticks_engine(self):
        s = self.fresh()
        advance_state(s, 30)
        self.assertTrue(s["nation"]["history"])


if __name__ == "__main__":
    unittest.main()
