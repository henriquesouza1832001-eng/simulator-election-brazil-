import json
import math
import random
import unittest
from datetime import date

from app.engine import powers
from app.engine.state import advance_state, new_game

RANGES = {"approval": (0, 100), "institutional_trust": (0, 100), "integrity": (0, 100), "governability": (0, 100), "congress_support": (0, 100),
          "gdp_growth": (-10, 15), "inflation": (-2, 80), "unemployment": (0, 40), "debt_gdp": (0, 400), "country_risk": (0, 1500)}
MACRO = {"bolsa": (20000, 400000), "cambio": (3.0, 12.0), "risco": (60, 1200), "confianca": (5, 95)}


def verificar(testcase, state, rotulo):
    for key, (low, high) in RANGES.items():
        value = state["metrics"].get(key)
        if value is None:
            continue
        testcase.assertTrue(math.isfinite(float(value)), f"{rotulo}: {key} não é número finito ({value})")
        testcase.assertTrue(low <= float(value) <= high, f"{rotulo}: {key}={value} fora de [{low}, {high}]")
    for key, (low, high) in MACRO.items():
        value = float(state["macro"][key])
        testcase.assertTrue(math.isfinite(value) and low <= value <= high, f"{rotulo}: macro {key}={value}")
    for key, value in state["fiscal"].items():
        if isinstance(value, (int, float)):
            testcase.assertTrue(math.isfinite(float(value)), f"{rotulo}: fiscal {key}={value}")


class InvariantesDoMotorTests(unittest.TestCase):
    """Partidas aleatórias em todas as dificuldades: nenhum indicador pode virar NaN, sair da faixa ou quebrar a serialização."""

    def test_vinte_e_quatro_meses_aleatorios_em_cada_dificuldade(self):
        for difficulty in ("tranquilo", "normal", "dificil", "complicado", "realismo_puro"):
            for seed in (3, 4):
                rng = random.Random(seed)
                s = new_game()
                s.pop("setup_pending", None)
                s["difficulty"] = difficulty
                s["campaign_seed"] = 5000 + seed
                anterior = date.fromisoformat(s["date"])
                for month in range(24):
                    options = [a for a in powers.ACTIONS if powers.status(s, a)["available"]]
                    if options and rng.random() < 0.7:
                        action = rng.choice(options)
                        try:
                            powers.execute(s, action["id"], rng.choice(action["options"]) if action["options"] else None)
                        except (PermissionError, RuntimeError, ValueError):
                            pass
                    s, _msg = advance_state(s, rng.choice([7, 15, 30, 30, 45]))
                    atual = date.fromisoformat(s["date"])
                    self.assertGreater(atual, anterior)
                    anterior = atual
                    verificar(self, s, f"{difficulty}/{seed}/mês {month + 1}")
                texto = json.dumps(s)
                self.assertLess(len(texto), 3_000_000, "estado grande demais")

    def test_por_que_mudou_fecha_a_conta_em_toda_partida(self):
        s = new_game()
        s.pop("setup_pending", None)
        for _ in range(18):
            s, _msg = advance_state(s, 30)
            for key, row in s["why"]["metrics"].items():
                if len(row["causes"]) < 3:
                    self.assertAlmostEqual(sum(c["delta"] for c in row["causes"]), row["total"], delta=0.06, msg=key)


if __name__ == "__main__":
    unittest.main()
