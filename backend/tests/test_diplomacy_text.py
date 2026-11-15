import unittest

from app.engine import diplomacy
from app.engine.state import new_game, refresh_calendar_fields


class DiplomacyTextTests(unittest.TestCase):
    def test_partida_antiga_sem_acento_volta_com_o_texto_do_catalogo(self):
        state = refresh_calendar_fields(new_game())
        dip = diplomacy.ensure_diplomacy_state(state)
        dip["countries"]["ARG"]["region"] = "America do Sul"
        dip["countries"]["TUR"]["region"] = "Mediterraneo"
        dip["events"][-1]["name"] = "Cupula Global do Clima"
        dip["events"][-1]["description"] = "Cupula ficticia do calendario do jogo; nao representa uma conferencia oficial."
        fresh = diplomacy.ensure_diplomacy_state(state)
        self.assertEqual(fresh["countries"]["ARG"]["region"], "América do Sul")
        self.assertEqual(fresh["countries"]["TUR"]["region"], "Mediterrâneo")
        self.assertEqual(fresh["events"][-1]["name"], "Cúpula Global do Clima")
        self.assertIn("calendário", fresh["events"][-1]["description"])


if __name__ == "__main__":
    unittest.main()
