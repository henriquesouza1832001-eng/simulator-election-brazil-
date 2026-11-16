import importlib.util
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("bots", Path(__file__).resolve().parents[1] / "scripts" / "bots_balanceamento.py")
bots = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bots)


class BotsTests(unittest.TestCase):
    def test_partida_curta_roda_sem_excecao_e_e_reprodutivel(self):
        a = bots.play("ativista", 11, months=4)
        b = bots.play("ativista", 11, months=4)
        self.assertEqual(a["unexpected"], [])
        self.assertEqual(a["final"], b["final"])
        self.assertGreater(a["actions_done"] + a["actions_blocked"], 0)

    def test_passivo_nao_executa_acoes(self):
        r = bots.play("passivo", 3, months=3)
        self.assertEqual((r["actions_done"], r["actions_blocked"]), (0, 0))

    def test_relatorio_aponta_indicador_insensivel(self):
        iguais = [{"strategy": s, "seed": 1, "unexpected": [], "final": {"approval": 40 + i * 5, "inflation": 5.0, "unemployment": 6.7, "gdp_growth": 0.8,
                                                                      "institutional_trust": 50, "integrity": 50, "congress_support": 50, "governability": 50}}
                  for i, s in enumerate(["passivo", "ativista"])]
        texto = " ".join(bots.problems(iguais))
        self.assertIn("inflation quase não responde", texto)
        self.assertIn("unemployment quase não responde", texto)


if __name__ == "__main__":
    unittest.main()
