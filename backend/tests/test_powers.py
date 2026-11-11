import unittest
from datetime import date, timedelta

from app.engine import powers
from app.engine.powers_catalog import ACTIONS, ROLES
from app.engine.state import new_game, process_legislation, refresh_calendar_fields


def fresh():
    state = refresh_calendar_fields(new_game())
    state["date"] = "2027-03-01"
    return state


class PowersTest(unittest.TestCase):
    def test_catalog_is_consistent(self):
        ids = [a["id"] for a in ACTIONS]
        self.assertEqual(len(ids), len(set(ids)))
        for a in ACTIONS:
            self.assertIn(a["approval"], {"decreto", "mp", "pl", "plp", "pec", "tratado", "blocked"})
            self.assertTrue(a["basis"] and a["summary"])
            if a["approval"] == "blocked":
                self.assertTrue(a["blocked"])
        self.assertGreaterEqual(len(ACTIONS), 45)
        for office in ("militante", "vereador", "prefeito", "governador", "senador", "presidente"):
            self.assertTrue(ROLES[office]["pode"] and ROLES[office]["nao_pode"])

    def test_blocked_and_constitutional_limits(self):
        state = fresh()
        with self.assertRaises(PermissionError):
            powers.execute(state, "reg_abolir_federacao")
        with self.assertRaises(PermissionError):
            powers.execute(state, "reg_monarquia")

    def test_unilateral_decree_applies_immediately_and_has_cooldown(self):
        state = fresh()
        before = state["metrics"]["approval"]
        result = powers.execute(state, "seg_armas_afrouxar")
        self.assertEqual(result["status"], "applied")
        self.assertEqual(powers.structure(state)["guns"], "facilitado")
        self.assertNotEqual(state["metrics"]["approval"], before)
        with self.assertRaises(RuntimeError):
            powers.execute(state, "bc_pressao_juros")

    def test_central_bank_needs_complementary_law_and_independence_default(self):
        state = fresh()
        self.assertEqual(powers.structure(state)["central_bank"], "autonomo_lei")
        result = powers.execute(state, "bc_revogar_autonomia")
        self.assertEqual(result["status"], "pending_legislature")
        self.assertEqual(powers.structure(state)["central_bank"], "autonomo_lei")  # só muda se o Congresso aprovar
        bill = state["legislative_calendar"]["pending_bills"][0]
        self.assertEqual(bill["instrument"], "Projeto de Lei Complementar")
        powers.resolve_bill(state, bill, True)
        self.assertEqual(powers.structure(state)["central_bank"], "subordinado")

    def test_privatization_requires_option_and_changes_ownership(self):
        state = fresh()
        with self.assertRaises(ValueError):
            powers.execute(state, "empresa_privatizar")
        powers.execute(state, "empresa_privatizar", "Correios")
        bill = state["legislative_calendar"]["pending_bills"][0]
        powers.resolve_bill(state, bill, True)
        self.assertEqual(powers.structure(state)["companies"]["Correios"], "privada")

    def test_medida_provisoria_reverts_structure_when_rejected(self):
        state = fresh()
        powers.execute(state, "eco_mp")
        bill = state["legislative_calendar"]["pending_bills"][0]
        self.assertTrue(bill["power_revert"])
        powers.resolve_bill(state, bill, False)

    def test_legislature_hook_resolves_power_bills(self):
        state = fresh()
        powers.execute(state, "reg_reeleicao")
        today = date.fromisoformat(state["date"])
        after = today + timedelta(days=400)
        process_legislation(state, today, after)
        self.assertEqual(state["legislative_calendar"]["pending_bills"], [])
        self.assertIn(powers.structure(state)["reelection"], {"vedada", "permitida"})


if __name__ == "__main__":
    unittest.main()
