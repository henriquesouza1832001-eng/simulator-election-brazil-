import unittest

from app.engine import macro, rules
from app.engine.measure_validation import extract_explicit_policy_cost_bi, extract_explicit_policy_savings_bi
from app.engine.state import new_game


def resultado(state, **interpretation):
    return rules._measure_result(state, {"category": "social_policy", "duration_days": 365, **interpretation})


class MedidaFiscalTests(unittest.TestCase):
    def test_custo_anual_pesa_de_verdade_no_resultado_primario(self):
        state = new_game()
        base = state["metrics"]["primary_balance"]
        out = resultado(state, fiscal_cost_bi=60.0)
        self.assertAlmostEqual(out["primary_balance"] - base, -0.40, delta=0.02)   # 60 / 15.000 = 0,4% do PIB
        self.assertGreater(out["gdp_growth"], state["metrics"]["gdp_growth"])       # gasto estimula no curto prazo

    def test_custo_em_varios_anos_e_diluido(self):
        state = new_game()
        base = state["metrics"]["primary_balance"]
        um_ano = resultado(state, fiscal_cost_bi=60.0, duration_days=365)["primary_balance"] - base
        dois_anos = resultado(state, fiscal_cost_bi=60.0, duration_days=730)["primary_balance"] - base
        self.assertAlmostEqual(dois_anos, um_ano / 2, delta=0.02)

    def test_corte_declarado_melhora_as_contas_e_esfria_a_economia(self):
        state = new_game()
        base = state["metrics"]
        out = rules._measure_result(state, {"category": "fiscal_efficiency", "duration_days": 365, "fiscal_cost_bi": 0.0, "fiscal_saving_bi": 30.0})
        self.assertGreater(out["primary_balance"], base["primary_balance"] + 0.15)
        self.assertLess(out["gdp_growth"], base["gdp_growth"])
        self.assertLess(out["approval"], base["approval"] + 0.5)

    def test_extrator_separa_corte_de_custo(self):
        texto = "Cortar R$ 20 bilhões de despesas de custeio e criar um programa que custa R$ 8 bilhões."
        self.assertEqual(extract_explicit_policy_savings_bi(texto), 20.0)
        self.assertEqual(extract_explicit_policy_cost_bi(texto), (8.0, True))
        self.assertEqual(extract_explicit_policy_savings_bi("Programa que custa R$ 12 bilhões e gera R$ 15 bilhões de renda."), 0.0)

    def test_aplicar_medida_grande_mexe_no_mercado(self):
        state = new_game()
        macro.ensure(state)
        antes = state["macro"]["risco"], state["macro"]["bolsa"]
        interpretation = {"title": "Transferência de renda", "category": "social_policy", "instrument": "Indefinido", "duration_days": 365, "fiscal_cost_bi": 60.0}
        rules.apply_effects(state, interpretation)
        self.assertGreater(state["macro"]["risco"], antes[0] + 20)
        self.assertLess(state["macro"]["bolsa"], antes[1] * 0.97)
        self.assertIn("Mercado reage", state["macro"]["news"][0]["text"])


if __name__ == "__main__":
    unittest.main()
