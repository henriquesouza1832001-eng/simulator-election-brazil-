import re
import unittest

from app.engine import voice
from app.engine.macro import _pct


def sinal(r):
    return f"{'+' if r >= 0 else '−'}{abs(round(r))} pontos"


class VozDoJogoTests(unittest.TestCase):
    def test_escolha_e_estavel_para_a_mesma_semente(self):
        self.assertEqual(voice.pick(voice.PRESS_UP, "x"), voice.pick(voice.PRESS_UP, "x"))
        self.assertGreater(len({voice.pick(voice.PRESS_UP, str(i)) for i in range(40)}), 1)   # e varia entre sementes

    def test_manchete_do_mercado_mantem_todos_os_numeros_do_motor(self):
        for bolsa, cambio, risco in ((-6.2, 4.1, 55), (6.2, -3.4, -40), (1.0, 0.5, 3)):
            texto = voice.market_day("s", bolsa, cambio, risco, _pct, sinal)
            self.assertIn(_pct(bolsa), texto)
            self.assertIn(_pct(cambio), texto)
            self.assertIn(sinal(risco), texto)

    def test_nada_diegetico_cita_simulacao(self):
        todos = voice.PRESS_UP + voice.PRESS_DOWN + voice.OPPOSITION + voice.SUPPORT + voice.MARKET_BY_DECISION + voice.MARKET_DESC + voice.POLL_LEAD + voice.POLL_TRAIL + [voice.EXPIRED_PAUTA, voice.EXPIRED_CRISIS]
        for texto in todos:
            self.assertIsNone(re.search(r"simula", texto, re.I), texto)

    def test_variantes_de_partido_aceitam_a_sigla(self):
        self.assertIn("PSB", voice.pick(voice.OPPOSITION, "k").format(party="PSB"))


if __name__ == "__main__":
    unittest.main()
