import time
import unittest

from app.engine.state import advance_state, new_game


class DesempenhoDoMandatoTests(unittest.TestCase):
    def test_quarenta_e_oito_meses_rodam_em_poucos_segundos(self):
        """Trava de regressão: o motor leva cerca de 1 a 3 s por mandato (a biblioteca de eventos carrega uma vez, ~2 s). Limite folgado para CI lento."""
        state = new_game()
        state.pop("setup_pending", None)
        started = time.perf_counter()
        for _ in range(48):
            state, _message = advance_state(state, 30)
        elapsed = time.perf_counter() - started
        self.assertEqual(state["day_of_mandate"] >= 1, True)
        self.assertLess(elapsed, 12.0, f"48 meses levaram {elapsed:.1f} s")


if __name__ == "__main__":
    unittest.main()
