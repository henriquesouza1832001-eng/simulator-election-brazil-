import asyncio
import unittest

from app.ai import narrator
from app.engine import office_powers, powers
from app.engine.state import new_game, refresh_calendar_fields
from tests.test_office_powers import career_state


def president():
    s = refresh_calendar_fields(new_game())
    s["date"] = "2027-03-01"
    return s


class LedgerTest(unittest.TestCase):
    def test_decree_and_bill_are_recorded_and_settled(self):
        s = president()
        powers.execute(s, "seg_armas_afrouxar")
        self.assertEqual(s["ledger"][0]["status"], "em vigor")
        powers.execute(s, "reg_reeleicao")
        bill = s["legislative_calendar"]["pending_bills"][0]
        powers.resolve_bill(s, bill, True)
        entry = next(e for e in s["ledger"] if e["id"] == bill["ledger_id"])
        self.assertEqual(entry["status"], "aprovado")
        self.assertIsNotNone(entry["result"])

    def test_rejected_bill_explains_gap(self):
        s = president()
        powers.execute(s, "reg_reeleicao")
        bill = s["legislative_calendar"]["pending_bills"][0]
        powers.resolve_bill(s, bill, False)
        e = next(e for e in s["ledger"] if e["id"] == bill["ledger_id"])
        self.assertEqual(e["status"], "rejeitado")
        self.assertIn("rejeitada", e["reason"])

    def test_office_action_logged_with_forecast_and_result(self):
        s = career_state("prefeito")
        office_powers.execute(s, "p_recapear")
        e = s["ledger"][0]
        self.assertIn("mobilidade", e["forecast"])
        self.assertIn("mobilidade", e["result"])

    def test_local_narration_uses_only_facts(self):
        facts = {"title": "Recapear vias", "status": "aprovado", "forecast": {"mobilidade": 2.0}, "result": {"mobilidade": 2.0}, "cost": "12% da reserva", "reason": None}
        out = asyncio.run(narrator.narrate(facts))
        self.assertEqual(out["source"], "local")
        self.assertIn("2", out["text"])

    def test_gemini_text_with_invented_numbers_is_rejected(self):
        facts = {"title": "Recapear vias", "forecast": {"mobilidade": 2.0}, "result": {"mobilidade": 2.0}}
        self.assertFalse(narrator._acceptable("A obra reduziu o tempo de viagem em 37 minutos na cidade.", facts))
        self.assertTrue(narrator._acceptable("Na simulação, a obra elevou a mobilidade em 2 pontos, como previsto pelo motor.", facts))


if __name__ == "__main__":
    unittest.main()
