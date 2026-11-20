import unittest

from app.engine import speech_score
from app.engine.campaign import campaign_overview, perform_campaign_action, speech_issues
from app.engine.state import advance_state, new_game

TEXTO = "Vou criar 2 milhões de empregos em 24 meses, com recurso do orçamento e parceria com os estados."


def estado_em_campanha():
    state = new_game()
    for _ in range(80):
        if campaign_overview(state)["active"]:
            return state
        state, _ = advance_state(state, 60)
    raise AssertionError("a campanha presidencial não abriu")


class CampanhaPresidencialLeituraTests(unittest.TestCase):
    def test_temas_da_campanha_tem_palavras_para_a_leitura_local(self):
        issues = speech_issues()
        self.assertNotIn("servicos", issues)
        self.assertTrue(all(item["terms"] for key, item in issues.items() if key != "integridade") or issues["economia"]["terms"])

    def test_leitura_estruturada_define_a_nota_e_aparece_no_resultado(self):
        state = estado_em_campanha()
        leitura = speech_score.local_reading(TEXTO, "economia", {}, speech_issues())
        esperado, _ = speech_score.score_reading(leitura, "economia")
        result = perform_campaign_action(state, "comicio", "sudeste", "economia", TEXTO, reading=leitura)
        self.assertEqual(result["score"], esperado)
        self.assertEqual(result["reading"]["source"], "local")
        self.assertTrue(result["reading"]["promises"][0]["funding"])
        self.assertEqual(result["activity"]["reading"], result["reading"])

    def test_sem_leitura_mantem_o_calculo_antigo(self):
        state = estado_em_campanha()
        result = perform_campaign_action(state, "comicio", "sudeste", "economia", TEXTO)
        self.assertIsNone(result["reading"])


if __name__ == "__main__":
    unittest.main()
