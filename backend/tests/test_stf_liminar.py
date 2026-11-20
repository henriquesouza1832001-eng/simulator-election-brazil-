import unittest
from datetime import date, timedelta

from app.engine import regulators
from app.engine.state import new_game


def caso(seed, action="defesa_bomba", risk_action=True):
    state = new_game()
    state["campaign_seed"] = seed
    case = regulators.schedule_review(state, action_id=action, approval="decreto", title="Ato de teste", ledger_id=None, sets={}, effects={"approval": 2.0})
    return state, case


class LiminarDoSTFTests(unittest.TestCase):
    def test_ato_de_risco_alto_recebe_pedido_de_liminar_entre_7_e_15_dias(self):
        state, case = caso(1)
        self.assertEqual(case["liminar"], "pendente")
        dias = (date.fromisoformat(case["liminar_on"]) - date.fromisoformat(case["filed"])).days
        self.assertTrue(7 <= dias <= 15, dias)

    def test_ato_de_risco_baixo_nao_tem_liminar(self):
        state, case = caso(1, action="eco_salario_minimo")
        self.assertTrue(case is None or "liminar" not in case)

    def test_liminar_pode_ser_concedida_ou_negada_conforme_a_semente(self):
        resultados = set()
        for seed in range(1, 60):
            state, case = caso(seed)
            hoje = date.fromisoformat(state["date"])
            regulators.tick(state, hoje, hoje + timedelta(days=16))
            resultados.add(case["liminar"])
        self.assertEqual(resultados, {"concedida", "negada"})

    def test_liminar_concedida_suspende_e_o_merito_mantido_a_devolve(self):
        for seed in range(1, 200):
            state, case = caso(seed)
            hoje = date.fromisoformat(state["date"])
            msgs = regulators.tick(state, hoje, hoje + timedelta(days=16))
            if case["liminar"] != "concedida":
                continue
            self.assertTrue(any("concedeu liminar" in m for m in msgs))
            confianca = state["metrics"]["institutional_trust"]
            final = regulators.tick(state, hoje + timedelta(days=16), date.fromisoformat(case["decide_on"]) + timedelta(days=1))
            texto = " ".join(final)
            if "revogou a liminar" in texto:
                self.assertGreater(state["metrics"]["institutional_trust"], confianca)   # ato mantido: a confiança volta a subir
                return
        self.fail("nenhuma semente produziu liminar concedida e mérito mantido")

    def test_textos_do_stf_nao_citam_simulacao(self):
        state, case = caso(3)
        hoje = date.fromisoformat(state["date"])
        msgs = regulators.tick(state, hoje, date.fromisoformat(case["decide_on"]) + timedelta(days=1))
        for m in msgs:
            self.assertNotIn("simula", m.lower())


if __name__ == "__main__":
    unittest.main()
