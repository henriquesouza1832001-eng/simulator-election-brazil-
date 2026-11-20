import statistics
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import bots_balanceamento as bots  # noqa: E402


def media(strategy, difficulty, seeds=(11, 12, 13)):
    return statistics.mean(bots.play(strategy, seed, difficulty=difficulty)["final"]["approval"] for seed in seeds)


class BalanceamentoPorDificuldadeTests(unittest.TestCase):
    """Trava de balanceamento medida com bots: a dificuldade precisa mudar o resultado e jogar bem precisa valer mais que não jogar."""

    def test_dificuldade_mais_alta_derruba_a_aprovacao_final(self):
        tranquilo, normal, complicado = media("governante", "tranquilo"), media("governante", "normal"), media("governante", "complicado")
        self.assertGreater(tranquilo, normal)
        self.assertGreater(normal, complicado)

    def test_jogar_bem_vale_mais_que_nao_jogar_e_nao_e_facil_demais(self):
        ativo, passivo = media("governante", "normal"), media("passivo", "normal")
        self.assertGreater(ativo - passivo, 15)
        self.assertLess(ativo, 75)      # nenhum jogador competente termina o mandato acima de 75% de aprovação
        self.assertLess(passivo, 50)    # e quem não faz nada não vence


if __name__ == "__main__":
    unittest.main()
