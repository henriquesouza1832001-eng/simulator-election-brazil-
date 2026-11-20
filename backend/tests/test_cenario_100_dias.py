import unittest

from app.engine import scenario_100
from app.engine.state import advance_state, new_game


def partida():
    state = new_game()
    state.pop("setup_pending", None)
    scenario_100.apply(state)
    return state


class CenarioCemDiasTests(unittest.TestCase):
    def test_parte_de_numeros_piores_e_cinco_metas_abertas(self):
        s = partida()
        self.assertEqual(s["metrics"]["approval"], 44.0)
        view = scenario_100.public(s)
        self.assertEqual(len(view["goals"]), 5)
        self.assertEqual(view["status"], "em_andamento")
        self.assertEqual(view["day"], 1)   # primeiro dia = dia 1, como no cabeçalho "DIA 1 DE 1461"
        self.assertFalse(view["goals"][0]["done"])   # aprovação 44 < 50

    def test_meta_fiscal_usa_virgula_e_so_se_cumpre_com_alavanca(self):
        from app.engine import fiscal_levers
        s = partida()
        meta = next(g for g in scenario_100.goals(s) if g["id"] == "fiscal")
        self.assertFalse(meta["done"])
        self.assertIn(",", meta["progress"])
        fiscal_levers.apply(s, "contingenciamento", "10")
        self.assertTrue(next(g for g in scenario_100.goals(s) if g["id"] == "fiscal")["done"])

    def test_meta_de_lei_conta_projeto_enviado(self):
        from app.engine import powers
        s = partida()
        self.assertFalse(next(g for g in scenario_100.goals(s) if g["id"] == "lei")["done"])
        powers.execute(s, "empresa_privatizar", "Correios")
        self.assertTrue(next(g for g in scenario_100.goals(s) if g["id"] == "lei")["done"])

    def test_balanco_fecha_uma_vez_no_centesimo_dia_com_nota_pelo_numero_de_metas(self):
        s = partida()
        for _ in range(4):
            s, _msg = advance_state(s, 30)
        view = scenario_100.public(s)
        self.assertEqual(view["status"], "concluido")
        feitas = sum(1 for g in view["goals"] if g["done"])
        self.assertEqual(view["result"]["done"], feitas)
        resultado = dict(view["result"])
        s, _msg = advance_state(s, 30)
        self.assertEqual(scenario_100.public(s)["result"], resultado)   # não recalcula depois de fechado

    def test_partida_normal_nao_tem_cenario(self):
        self.assertIsNone(scenario_100.public(new_game()))


if __name__ == "__main__":
    unittest.main()
