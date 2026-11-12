import unittest
from datetime import date, timedelta

from app.engine import companies, powers
from app.engine.state import new_game, refresh_calendar_fields
from tests.test_office_powers import career_state


def president():
    s = refresh_calendar_fields(new_game())
    s["date"] = "2027-03-01"
    return s


class CompaniesTest(unittest.TestCase):
    def test_catalog_and_scope_by_office(self):
        s = president()
        ov = companies.overview(s)
        ids = {c["id"] for c in ov["companies"]}
        self.assertTrue({"petrobras", "bb", "caixa", "bndes", "correios", "eletrobras", "embraer", "vale"} <= ids)
        pet = next(c for c in ov["companies"] if c["id"] == "petrobras")
        self.assertTrue(pet["controlled"])
        self.assertTrue(any(a["key"] == "prices" for a in pet["actions"]))
        gov = career_state("governador")
        gov["career"]["state_code"] = "MG"
        cemig = next(c for c in companies.overview(gov)["companies"] if c["id"] == "cemig")
        self.assertTrue(all(a["available"] or "Disponível" in (a["reason"] or "") for a in cemig["actions"]))
        with self.assertRaises(PermissionError):
            companies.act(gov, "petrobras", "visit")
        with self.assertRaises(PermissionError):
            companies.act(career_state("prefeito"), "petrobras", "visit")

    def test_visit_improves_relation_and_has_cooldown(self):
        s = president()
        before = companies.ensure(s)["bb"]["relation"]
        out = companies.act(s, "bb", "visit")
        self.assertGreater(companies.ensure(s)["bb"]["relation"], before)
        self.assertEqual(s["ledger"][0]["source"], "empresa")
        with self.assertRaises(RuntimeError):
            companies.act(s, "bb", "visit")

    def test_price_policy_trades_inflation_for_company_health(self):
        s = president()
        infl, health = s["metrics"]["inflation"], companies.ensure(s)["petrobras"]["health"]
        companies.act(s, "petrobras", "prices", "Segurar preços")
        self.assertLess(s["metrics"]["inflation"], infl)
        self.assertLess(companies.ensure(s)["petrobras"]["health"], health)
        with self.assertRaises(ValueError):
            companies.act(s, "petrobras", "dividends", "inexistente")

    def test_privatization_updates_company_control_and_blocks_management_actions(self):
        s = president()
        powers.execute(s, "empresa_privatizar", "Correios")
        powers.resolve_bill(s, s["legislative_calendar"]["pending_bills"][0], True)
        ov = companies.overview(s)
        correios = next(c for c in ov["companies"] if c["id"] == "correios")
        self.assertFalse(correios["controlled"])
        with self.assertRaises(PermissionError):
            companies.act(s, "correios", "dividends", "Pedir mais dividendos")

    def test_low_health_triggers_crisis_decision(self):
        s = president()
        companies.ensure(s)["bndes"]["health"] = 10.0
        msgs = companies.tick(s, date(2027, 3, 1), date(2027, 4, 5))
        self.assertTrue(any("dificuldade" in m for m in msgs))
        self.assertTrue(any(c["action_id"] == "empresa_bndes" for c in s["consequences"]["pending"]))


if __name__ == "__main__":
    unittest.main()
