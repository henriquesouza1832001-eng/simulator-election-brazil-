import unittest

from app.ai import event_generator, gateway, interpreter, mapper_ai, narrator

FACTS = {"title": "Reduzir o preço da energia elétrica", "status": "feito", "forecast": {"approval": 1.2, "inflation": -0.1},
         "result": {"approval": 0.9, "inflation": -0.08}, "cost": "R$ 1,2 bi"}


class NarratorGuardTests(unittest.TestCase):
    def test_decimal_com_virgula_vale_o_mesmo_que_com_ponto(self):
        text = "Na simulação, a redução do preço da energia custou R$ 1,2 bi. O motor previu aprovação 1,2 e o realizado foi 0,9."
        self.assertTrue(narrator._acceptable(text, FACTS))

    def test_numero_inventado_e_recusado(self):
        text = "Na simulação, a redução do preço da energia aumentou a aprovação em 7 pontos, acima do previsto pelo motor."
        self.assertFalse(narrator._acceptable(text, FACTS))

    def test_zero_a_esquerda_nao_cria_numero_novo(self):
        self.assertEqual(narrator._numbers("0,90 e 0.9"), {"0.9"})


class ModeloPadraoTests(unittest.TestCase):
    def test_todos_os_recursos_usam_o_mesmo_modelo(self):
        models = {interpreter.DEFAULT_MODEL, narrator.DEFAULT_MODEL, mapper_ai.DEFAULT_MODEL, gateway.DEFAULT_MODEL}
        self.assertEqual(len(models), 1)
        self.assertEqual(event_generator.DEFAULT_MODEL, gateway.DEFAULT_MODEL if not __import__("os").getenv("GEMINI_MODEL") else event_generator.DEFAULT_MODEL)


if __name__ == "__main__":
    unittest.main()
