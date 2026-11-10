"""Calendário eleitoral e validação de cargo/território."""
from __future__ import annotations

import unittest
from datetime import date

from app.engine import election_rules as er


class CalendarTests(unittest.TestCase):
    def test_years_and_types(self):
        years = {s["year"]: s["type"] for s in er.scenarios()}
        self.assertEqual(years, {2014: "geral", 2016: "municipal", 2018: "geral", 2020: "municipal", 2022: "geral",
                                 2024: "municipal", 2026: "geral", 2028: "municipal", 2030: "geral"})

    def test_all_election_days_are_sundays(self):
        for year in er.SCENARIO_YEARS:
            dates = er.election_dates(year)
            for key in ("first_round", "second_round"):
                self.assertEqual(date.fromisoformat(dates[key]).weekday(), 6, (year, key))

    def test_derived_and_exceptional_dates(self):
        self.assertEqual(er.election_dates(2028)["first_round"], "2028-10-01")
        self.assertEqual(er.election_dates(2028)["second_round"], "2028-10-29")
        self.assertEqual(er.election_dates(2030)["first_round"], "2030-10-06")
        self.assertEqual(er.election_dates(2030)["second_round"], "2030-10-27")
        self.assertTrue(er.election_dates(2030)["derived_from_rule"])
        self.assertEqual(er.election_dates(2020)["first_round"], "2020-11-15")  # EC 107/2020
        self.assertFalse(er.election_dates(2026)["derived_from_rule"])

    def test_senate_renewal_alternates(self):
        self.assertTrue(er.senate_renewal(2026).startswith("2/3"))
        self.assertTrue(er.senate_renewal(2030).startswith("1/3"))
        self.assertIsNone(er.senate_renewal(2024))

    def test_rules_are_versioned_by_year(self):
        self.assertTrue(er.ruleset_for(2016)["corporate_donations"]["allowed"] is False)
        self.assertTrue(er.ruleset_for(2014)["corporate_donations"]["allowed"])
        self.assertFalse(er.ruleset_for(2018)["federations"]["allowed"])
        self.assertTrue(er.ruleset_for(2022)["federations"]["allowed"])
        self.assertTrue(er.ruleset_for(2018)["coalitions_proportional"]["allowed"])
        self.assertFalse(er.ruleset_for(2020)["coalitions_proportional"]["allowed"])
        self.assertTrue(er.ruleset_for(2026)["pending"])  # o que não foi confirmado não é omitido
        self.assertIn("2027", er.ruleset_for(2026)["inauguration"]["president"])

    def test_offices_depend_on_election_type(self):
        self.assertIn("presidente", er.ruleset_for(2022)["offices"])
        self.assertNotIn("prefeito", er.ruleset_for(2022)["offices"])
        self.assertIn("prefeito", er.ruleset_for(2024)["offices"])
        self.assertNotIn("presidente", er.ruleset_for(2024)["offices"])
        self.assertEqual(er.OFFICES["senador"]["term"], 8)


class ValidationTests(unittest.TestCase):
    def test_incoherent_combinations_are_rejected(self):
        with self.assertRaises(ValueError):
            er.validate_selection(2024, "presidente", None, None)
        with self.assertRaises(ValueError):
            er.validate_selection(2022, "prefeito", "SP", "3550308")
        with self.assertRaises(ValueError):
            er.validate_selection(2022, "governador", "XX", None)
        with self.assertRaises(ValueError):
            er.validate_selection(2019, "presidente", None, None)

    def test_valid_combinations(self):
        self.assertEqual(er.validate_selection(2026, "presidente", None, None)["scope"], "nacional")
        self.assertEqual(er.validate_selection(2026, "senador", "MG", None)["uf"], "MG")

    def test_municipality_is_validated_against_ibge(self):
        ok = er.validate_selection(2028, "prefeito", None, "3550308")
        self.assertEqual(ok["uf"], "SP")
        with self.assertRaises(ValueError):
            er.validate_selection(2028, "prefeito", None, "0000000")
        with self.assertRaises(ValueError):
            er.validate_selection(2028, "vereador", "RJ", "3550308")  # município de SP, UF RJ
        with self.assertRaises(ValueError):
            er.validate_selection(2028, "vereador", None, "abc")


if __name__ == "__main__":
    unittest.main()
