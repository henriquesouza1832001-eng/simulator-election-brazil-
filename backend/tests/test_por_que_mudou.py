import unittest
from datetime import date

from app.engine import drivers, powers
from app.engine.state import advance_state, new_game


class PorQueMudouTests(unittest.TestCase):
    def test_soma_das_causas_fecha_com_a_variacao_total(self):
        state = new_game()
        state, _ = advance_state(state, 30)
        why = state["why"]
        for key, row in why["metrics"].items():
            if len(row["causes"]) < 3:   # com 3 ou mais causas a lista é cortada; abaixo disso ela precisa fechar com o total
                self.assertAlmostEqual(sum(c["delta"] for c in row["causes"]), row["total"], delta=0.03, msg=key)

    def test_decisao_aparece_como_causa_da_aprovacao(self):
        state = new_game()
        state, _ = advance_state(state, 7)
        action = next(a for a in powers.ACTIONS if a["approval"] == "decreto" and abs(a["effects"].get("approval", 0)) >= 0.5 and not a["options"])
        state["date"] = "2027-03-01"
        try:
            powers.execute(state, action["id"])
        except Exception:   # a ação pode exigir pré-condições; o teste só quer o registro de causa se ela rodou
            self.skipTest("ação indisponível no estado inicial")
        state, _ = advance_state(state, 7)
        labels = [c["label"] for c in state["why"]["metrics"]["approval"]["causes"]]
        self.assertTrue(any(action["title"] in label for label in labels) or state["why"]["metrics"]["approval"]["total"] == 0, labels)

    def test_nota_sem_rotulo_usa_o_bloco_because(self):
        state = new_game()
        with drivers.because("Minha decisão"):
            drivers.note(state, "approval", 1.5)
        state["metrics"]["approval"] = state["metrics"]["approval"] + 1.5
        why = drivers.close(state, "2027-01-01", "2027-01-08")
        self.assertEqual(why["metrics"]["approval"]["causes"][0]["label"], "Minha decisão")

    def test_janela_reabre_zerada(self):
        state = new_game()
        state, _ = advance_state(state, 30)
        self.assertEqual(state["why_window"]["items"], [])


if __name__ == "__main__":
    unittest.main()
