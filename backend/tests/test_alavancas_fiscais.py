import unittest
from datetime import date, timedelta

from app.engine import fiscal_levers
from app.engine.state import advance_state, new_game


def partida():
    state = new_game()
    state.pop("setup_pending", None)
    return state


class AlavancasFiscaisTests(unittest.TestCase):
    def test_alavanca_de_peso_move_o_resultado_primario_de_verdade(self):
        s = partida()
        antes = s["metrics"]["primary_balance"]
        resultado = fiscal_levers.apply(s, "contingenciamento", "10")
        depois = s["metrics"]["primary_balance"]
        self.assertGreaterEqual(depois - antes, 0.13)          # 10% de contingenciamento: ~R$ 22 bi, ~0,15% do PIB
        self.assertAlmostEqual(resultado["primary_balance_delta_pct_gdp"], depois - antes, places=3)

    def test_tem_custo_real_em_atividade_e_aprovacao(self):
        s = partida()
        g0, a0 = s["metrics"]["gdp_growth"], s["metrics"]["approval"]
        fiscal_levers.apply(s, "subsidios", "forte")
        self.assertLess(s["metrics"]["gdp_growth"], g0)
        self.assertLess(s["metrics"]["approval"], a0)
        self.assertLess(s["metrics"]["congress_support"], 52)   # bancada dos setores reage

    def test_mercado_o_livro_razao_e_a_imprensa_registram_a_decisao(self):
        s = partida()
        fiscal_levers.apply(s, "contingenciamento", "15")
        self.assertTrue(s["macro"]["news"])
        self.assertTrue(any("ontingenciar" in e["title"] for e in s["ledger"]))
        self.assertTrue(s["consequences"]["scheduled"])

    def test_intervalo_entre_alavancas_e_limite_anual(self):
        s = partida()
        fiscal_levers.apply(s, "subsidios", "parcial")
        with self.assertRaises(ValueError):
            fiscal_levers.apply(s, "dividendos", "moderado")     # 60 dias entre alavancas
        s["date"] = (date.fromisoformat(s["date"]) + timedelta(days=61)).isoformat()
        with self.assertRaises(ValueError):
            fiscal_levers.apply(s, "subsidios", "forte")         # subsídios: uma vez por ano
        fiscal_levers.apply(s, "dividendos", "moderado")

    def test_contingenciamento_acumulado_tem_teto_de_15_por_cento(self):
        s = partida()
        fiscal_levers.apply(s, "contingenciamento", "10")
        s["date"] = (date.fromisoformat(s["date"]) + timedelta(days=61)).isoformat()
        with self.assertRaises(ValueError):
            fiscal_levers.apply(s, "contingenciamento", "10")
        fiscal_levers.apply(s, "contingenciamento", "5")

    def test_dividendo_unico_abate_a_divida_sem_mexer_no_primario_recorrente(self):
        s = partida()
        antes = s["fiscal"]["debt_stock_bi"] if "fiscal" in s else None
        from app.engine.fiscal import ensure_fiscal_state
        ensure_fiscal_state(s)
        antes = s["fiscal"]["debt_stock_bi"]
        fiscal_levers.apply(s, "dividendos", "alto")
        self.assertAlmostEqual(antes - s["fiscal"]["debt_stock_bi"], 40.0, delta=0.5)

    def test_catalogo_lista_previsao_e_disponibilidade(self):
        cat = fiscal_levers.catalog(partida())
        self.assertEqual({c["id"] for c in cat}, {"contingenciamento", "subsidios", "dividendos"})
        opt = cat[0]["options"][1]
        self.assertIn("primary_balance", opt["forecast"])
        self.assertTrue(opt["available"])

    def test_efeito_aparece_como_causa_em_por_que_mudou(self):
        s = partida()
        s, _ = advance_state(s, 5)
        fiscal_levers.apply(s, "subsidios", "forte")
        s, _ = advance_state(s, 20)
        causas = [c["label"] for c in s["why"]["metrics"]["approval"]["causes"]]
        self.assertTrue(any("subsídios" in c.lower() for c in causas), causas)


if __name__ == "__main__":
    unittest.main()
