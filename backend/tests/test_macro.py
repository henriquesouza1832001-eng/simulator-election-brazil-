import unittest
from datetime import date, timedelta

from app.engine import central_bank, macro, powers
from app.engine.state import advance_state, new_game


def meses(state, n, **overrides):
    """Avança n meses chamando só o motor macro (isola o modelo do resto do jogo)."""
    for _ in range(n):
        before = date.fromisoformat(state["date"])
        after = before + timedelta(days=30)
        state["date"] = after.isoformat()
        for key, value in overrides.items():
            if key == "selic":
                central_bank.ensure(state)["selic"] = value
            else:
                state["metrics"][key] = value
        macro.step(state, before, after)
    return state


def novo(seed=11):
    state = new_game()
    state["campaign_seed"] = seed
    macro.ensure(state)
    return state


class DecisoesMexemNoMercado(unittest.TestCase):
    def test_decisao_ruim_para_o_mercado_sobe_dolar_e_risco_e_derruba_bolsa(self):
        state = novo()
        antes = dict(state["macro"])
        out = macro.react(state, {"institutional_trust": -4.0}, 0.0, "revogar autonomia", "bc_revogar_autonomia")
        self.assertGreater(out["risco_bps"], 30)
        self.assertGreater(state["macro"]["risco"], antes["risco"] + 30)
        self.assertGreater(state["macro"]["cambio"], antes["cambio"])
        self.assertLess(state["macro"]["bolsa"], antes["bolsa"] * 0.93)

    def test_decisao_boa_para_o_mercado_faz_o_contrario(self):
        state = novo()
        antes = dict(state["macro"])
        macro.react(state, {"primary_balance": 0.15, "institutional_trust": 0.5}, 0.0, "reforma", "eco_previdencia")
        self.assertLess(state["macro"]["risco"], antes["risco"])
        self.assertLess(state["macro"]["cambio"], antes["cambio"])
        self.assertGreater(state["macro"]["bolsa"], antes["bolsa"] * 1.03)

    def test_privatizar_sobe_a_bolsa_e_estatizar_derruba(self):
        a, b = novo(), novo()
        macro.react(a, {}, 0.0, "privatizar", "empresa_privatizar")
        macro.react(b, {}, 0.0, "estatizar", "empresa_estatizar")
        self.assertGreater(a["macro"]["bolsa"], b["macro"]["bolsa"] * 1.05)

    def test_poderes_executados_geram_noticia_de_mercado(self):
        state = new_game()
        powers.execute(state, "jus_8jan_manter")
        self.assertTrue(state["macro"]["news"])
        self.assertIn("Mercado reage", state["macro"]["news"][0]["text"])
        self.assertNotIn("cai +", state["macro"]["news"][0]["text"])

    def test_envio_de_pec_mexe_um_pouco_e_a_rejeicao_desfaz(self):
        state = new_game()
        macro.ensure(state)
        base = dict(state["macro"])
        powers.execute(state, "jus_stf_numero")  # PEC: o mercado antecipa
        depois_do_envio = state["macro"]["bolsa"]
        self.assertLess(depois_do_envio, base["bolsa"])
        bill = state["legislative_calendar"]["pending_bills"][0]
        powers.resolve_bill(state, bill, False)
        self.assertGreater(state["macro"]["bolsa"], depois_do_envio)
        self.assertAlmostEqual(state["macro"]["risco"], base["risco"], delta=8)


class EconomiaEncadeada(unittest.TestCase):
    def test_deficit_e_divida_altos_pioram_risco_e_dolar(self):
        ruim, bom = novo(), novo()
        meses(ruim, 18, primary_balance=-4.5, debt_gdp=100.0)
        meses(bom, 18, primary_balance=0.5, debt_gdp=65.0)
        self.assertGreater(ruim["macro"]["risco"], bom["macro"]["risco"] + 150)
        self.assertGreater(ruim["macro"]["cambio"], bom["macro"]["cambio"] * 1.10)
        self.assertLess(ruim["macro"]["bolsa"], bom["macro"]["bolsa"])

    def test_dolar_mais_caro_empurra_a_inflacao(self):
        ruim, bom = novo(), novo()
        meses(ruim, 18, primary_balance=-4.5, debt_gdp=100.0)
        meses(bom, 18, primary_balance=0.5, debt_gdp=65.0)
        self.assertGreater(ruim["metrics"]["inflation"], bom["metrics"]["inflation"] + 0.5)

    def test_juros_altos_seguram_inflacao_e_pib(self):
        alto, baixo = novo(), novo()
        meses(alto, 24, selic=15.0)
        meses(baixo, 24, selic=5.0)
        self.assertLess(alto["metrics"]["inflation"], baixo["metrics"]["inflation"] - 0.8)
        self.assertLess(alto["metrics"]["gdp_growth"], baixo["metrics"]["gdp_growth"] - 1.0)
        self.assertGreater(alto["metrics"]["unemployment"], baixo["metrics"]["unemployment"])

    def test_crescimento_derruba_o_desemprego(self):
        forte, fraco = novo(), novo()
        forte["macro"]["policy"] = {"g": 1.5, "i": 0.0}
        fraco["macro"]["policy"] = {"g": -1.5, "i": 0.0}
        meses(forte, 24)
        meses(fraco, 24)
        self.assertLess(forte["metrics"]["unemployment"], fraco["metrics"]["unemployment"] - 0.6)

    def test_economia_ruim_derruba_a_aprovacao(self):
        boa, ruim = novo(), novo()
        meses(boa, 12, gdp_growth=4.0, unemployment=5.0, inflation=3.0)
        meses(ruim, 12, gdp_growth=-2.0, unemployment=11.0, inflation=9.0)
        self.assertGreater(boa["metrics"]["approval"], ruim["metrics"]["approval"] + 5)

    def test_efeito_direto_de_politica_nao_some_em_poucos_meses(self):
        com, sem = novo(), novo()
        macro.react(com, {"gdp_growth": 0.3}, 0.0, "pacote", None)
        meses(com, 6)
        meses(sem, 6)
        self.assertGreater(com["metrics"]["gdp_growth"], sem["metrics"]["gdp_growth"] + 0.05)


class Estabilidade(unittest.TestCase):
    def test_mandato_inteiro_fica_em_faixas_plausiveis_e_e_deterministico(self):
        def jogar():
            state = new_game()
            state["campaign_seed"] = 5
            for _ in range(48):
                state, _msg = advance_state(state, 30)
            return state
        a, b = jogar(), jogar()
        self.assertEqual(a["macro"]["bolsa"], b["macro"]["bolsa"])
        m, k = a["metrics"], a["macro"]
        self.assertTrue(-1 <= m["inflation"] <= 30 and 2 <= m["unemployment"] <= 25 and -6 <= m["gdp_growth"] <= 8)
        self.assertTrue(3.0 <= k["cambio"] <= 12.0 and 60 <= k["risco"] <= 1200 and 20000 <= k["bolsa"] <= 400000)
        self.assertGreaterEqual(len(k["history"]), 45)

    def test_visao_do_mercado_explica_o_que_move_os_precos(self):
        state = novo()
        state["metrics"]["primary_balance"] = -3.0
        view = macro.overview(state)
        self.assertEqual({r["id"] for r in view["indicators"]}, {"cambio", "bolsa", "selic", "risco", "expect"})
        self.assertTrue(any("Déficit primário" in d for d in view["drivers"]))
        self.assertFalse(any(",," in d or "a,a" in d for d in view["drivers"]))


if __name__ == "__main__":
    unittest.main()
