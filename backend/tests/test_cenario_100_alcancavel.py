import random
import statistics
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import bots_balanceamento as bots  # noqa: E402

from app.engine import powers, scenario_100  # noqa: E402
from app.engine.state import advance_state, new_game  # noqa: E402


def jogar(strategy, seed):
    rng = random.Random(seed)
    s = new_game()
    s.pop("setup_pending", None)
    s["campaign_seed"] = 1000 + seed
    scenario_100.apply(s)
    for _ in range(4):
        if str(s["date"]) >= s["scenario"]["end"]:
            break
        bots.respond(strategy, s, rng)
        a = bots.choose(strategy, s, rng)
        if a:
            try:
                powers.execute(s, a["id"], rng.choice(a["options"]) if a["options"] else None)
            except Exception:  # noqa: BLE001 - ações bloqueadas fazem parte do jogo
                pass
        s, _ = advance_state(s, 30)
    while s["scenario"]["status"] == "em_andamento":
        s, _ = advance_state(s, 10)
    return s["scenario"]["result"]["done"]


class CenarioCemDiasAlcancavelTests(unittest.TestCase):
    """O tutorial só é justo se quem joga bem consegue cumprir quase tudo e quem não joga não passa de uma ou duas metas."""

    def test_quem_governa_cumpre_mais_metas_que_quem_nao_faz_nada(self):
        ativo = statistics.mean(jogar("governante", seed) for seed in (1, 2, 3, 4))
        passivo = statistics.mean(jogar("passivo", seed) for seed in (1, 2, 3, 4))
        self.assertGreaterEqual(ativo, 3.0)
        self.assertLessEqual(passivo, 2.0)
        self.assertGreater(ativo - passivo, 1.5)

    def test_toda_meta_tem_um_caminho_de_acao_na_interface(self):
        s = new_game()
        s.pop("setup_pending", None)
        scenario_100.apply(s)
        abas = {g["tab"] for g in scenario_100.goals(s)}
        self.assertTrue(abas <= {"Indicadores", "Orçamento", "Medidas", "Tramitação", "Imprensa"}, abas)


if __name__ == "__main__":
    unittest.main()
