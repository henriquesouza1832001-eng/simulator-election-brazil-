import unittest
from datetime import date, timedelta

from app.engine import congress_process, powers
from app.engine.state import new_game


class MedidaProvisoriaTests(unittest.TestCase):
    def setUp(self):
        self.state = new_game()
        powers.execute(self.state, "eco_mp")
        self.mp = self.state["legislative_calendar"]["pending_bills"][0]
        self.start = date.fromisoformat(self.state["date"])

    def test_dia_a_dia_da_mp(self):
        antes = congress_process.mp_status(self.mp, self.start + timedelta(days=30))
        self.assertEqual((antes["locks_agenda"], antes["prorrogated"]), (False, False))
        meio = congress_process.mp_status(self.mp, self.start + timedelta(days=50))
        self.assertEqual((meio["locks_agenda"], meio["prorrogated"]), (True, False))
        fim = congress_process.mp_status(self.mp, self.start + timedelta(days=100))
        self.assertEqual((fim["locks_agenda"], fim["prorrogated"], fim["days_left"]), (True, True, 20))
        self.assertEqual(fim["expires"], (self.start + timedelta(days=120)).isoformat())

    def test_so_tranca_a_pauta_depois_de_45_dias(self):
        self.assertIsNone(congress_process.locking_mp(self.state, self.start + timedelta(days=44)))
        self.assertIsNotNone(congress_process.locking_mp(self.state, self.start + timedelta(days=45)))

    def test_mp_trancada_bloqueia_projeto_de_lei_mas_nao_pec(self):
        self.state["date"] = (self.start + timedelta(days=70)).isoformat()
        self.state["legislative_calendar"]["last_submission"] = None
        self.state["executive_calendar"]["last_action"] = None
        with self.assertRaises(RuntimeError) as ctx:
            powers.execute(self.state, "saude_sus")  # projeto de lei ordinário
        self.assertIn("trancada", str(ctx.exception))
        self.assertIn("art. 62", str(ctx.exception))
        result = powers.execute(self.state, "jus_pec_stf_mandato")  # PEC não é trancada pela MP
        self.assertEqual(result["status"], "pending_legislature")

    def test_sem_mp_nada_tranca(self):
        limpo = new_game()
        self.assertIsNone(congress_process.locking_mp(limpo, date.fromisoformat(limpo["date"]) + timedelta(days=200)))
        powers.execute(limpo, "saude_sus")


if __name__ == "__main__":
    unittest.main()
