import unittest

from app.engine import scale_ruler

GDP, INVEST = 15000.0, 100.0


def check(cost, text, instrument="Projeto de Lei", days=1461):
    return scale_ruler.check(cost, days, instrument, text, gdp_bi=GDP, investment_bi=INVEST)


class ScaleRulerTests(unittest.TestCase):
    def test_lei_de_200_bi_e_programa_de_estado(self):
        r = check(200, "Criar um programa nacional que custa R$ 200 bilhões.")
        self.assertEqual(r["verdict"], "muito_grande")
        self.assertAlmostEqual(r["share_of_gdp_pct"], 1.333, places=2)
        self.assertTrue(any("orçamento anual de investimento" in w for w in r["warnings"]))

    def test_renda_de_15_bi_com_custo_proporcional_passa(self):
        r = check(12, "Programa que custa R$ 12 bilhões e gera R$ 15 bilhões de renda para as famílias.")
        self.assertEqual(r["declared_benefit_bi"], 15.0)
        self.assertEqual(r["verdict"], "medio")
        self.assertEqual(r["benefit_to_cost"], 1.25)
        self.assertEqual(r["warnings"], [])

    def test_beneficio_milagroso_e_recusado(self):
        r = check(2, "Gasto de R$ 2 bilhões que gera R$ 40 bilhões de renda.")
        self.assertTrue(any("0,5 e 2 vezes" in w for w in r["warnings"]))

    def test_valor_enorme_em_ato_executivo_pede_lei(self):
        r = check(300, "Decreto que custa R$ 300 bilhões.", instrument="Decreto", days=200)
        self.assertEqual(r["verdict"], "muito_grande")
        self.assertTrue(any("lei ou emenda" in w for w in r["warnings"]))
        self.assertTrue(any("menos de um ano" in w for w in r["warnings"]))

    def test_fora_de_escala_e_sem_custo(self):
        self.assertEqual(check(900, "x")["verdict"], "fora_de_escala")
        r = check(0, "Reduzir o preço da energia.")
        self.assertEqual(r["verdict"], "sem_custo")
        self.assertEqual(r["message"], "")

    def test_beneficio_sem_custo_nao_conta(self):
        r = check(0, "Isso vai gerar R$ 15 bilhões de renda.")
        self.assertIn("não conta benefício sem custo", r["message"])


if __name__ == "__main__":
    unittest.main()


class CustoNaoSomaBeneficioTests(unittest.TestCase):
    def test_renda_gerada_nao_vira_custo(self):
        from app.engine.measure_validation import extract_explicit_policy_cost_bi
        custo, explicito = extract_explicit_policy_cost_bi("Criar um programa nacional de renda que custa R$ 200 bilhões e gera R$ 15 bilhões de renda para as famílias.")
        self.assertTrue(explicito)
        self.assertEqual(custo, 200.0)

    def test_custo_sem_beneficio_continua_igual(self):
        from app.engine.measure_validation import extract_explicit_policy_cost_bi
        self.assertEqual(extract_explicit_policy_cost_bi("O programa custa R$ 12 bilhões em quatro anos."), (12.0, True))
