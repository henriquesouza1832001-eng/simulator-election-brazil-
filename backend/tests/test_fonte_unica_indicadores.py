import unittest

from app.engine.state import advance_state, new_game


class FonteUnicaDeIndicadoresTests(unittest.TestCase):
    """Todo número que aparece em mais de uma tela precisa ter o mesmo valor no mesmo instante."""

    def avancado(self, meses=6):
        state = new_game()
        for _ in range(meses):
            state, _ = advance_state(state, 30)
        return state

    def test_indicadores_copiam_os_numeros_ja_atualizados_pela_economia(self):
        state = self.avancado()
        values, metrics = state["nation"]["values"], state["metrics"]
        self.assertAlmostEqual(values["inflacao"], metrics["inflation"], places=2)
        self.assertAlmostEqual(values["crescimento_pib"], metrics["gdp_growth"], places=2)
        self.assertAlmostEqual(values["desemprego"], metrics["unemployment"], places=2)
        self.assertAlmostEqual(values["aprovacao"], metrics["approval"], places=2)

    def test_risco_pais_e_o_mesmo_no_mercado_nas_metricas_e_no_orcamento(self):
        state = self.avancado()
        mercado = state["macro"]["risco"]
        self.assertAlmostEqual(state["nation"]["values"]["risco_pais"], mercado, delta=0.5)
        self.assertAlmostEqual(state["metrics"]["country_risk"], mercado, delta=1.0)
        self.assertAlmostEqual(state["fiscal"]["country_risk"], mercado, delta=1.0)


if __name__ == "__main__":
    unittest.main()
