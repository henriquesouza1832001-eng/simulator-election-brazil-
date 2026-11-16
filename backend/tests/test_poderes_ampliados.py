import unittest

from app.engine import powers, powers_catalog
from app.engine.state import new_game

NOVOS = {
    "saude": ["saude_sus", "saude_provimento", "saude_vacinacao", "saude_emergencia"],
    "educacao": ["edu_fundeb", "edu_piso", "edu_ensino_medio"],
    "social": ["soc_bpc"],
    "ambiente": ["amb_fiscalizacao", "amb_terras_indigenas", "amb_licenciamento", "amb_calamidade"],
    "justica": ["jus_indulto_natalino", "jus_indulto_8jan", "jus_anistia_8jan", "jus_pec_stf_mandato", "jus_stf_numero"],
    "legislativo": ["leg_emendas", "leg_sessao_extra", "leg_reforma_politica"],
    "memoria": ["mem_comissao", "mem_arquivos"],
    "espaco": ["espaco_agencia", "espaco_cooperacao"],
}


class PoderesAmpliadosTests(unittest.TestCase):
    def test_catalogo_cobre_os_tres_poderes(self):
        ids = [a["id"] for a in powers_catalog.ACTIONS]
        self.assertEqual(len(ids), len(set(ids)))
        domains = {a["domain"] for a in powers_catalog.ACTIONS}
        for domain, expected in NOVOS.items():
            self.assertIn(domain, domains)
            for action_id in expected:
                self.assertIn(action_id, ids)

    def test_toda_acao_nova_tem_base_legal_e_aprovacao_valida(self):
        for action_id in sum(NOVOS.values(), []):
            action = powers.BY_ID[action_id]
            self.assertTrue(action["basis"].strip(), action_id)
            self.assertIn(action["approval"], {"decreto", "mp", "pl", "plp", "pec", "tratado"}, action_id)
            self.assertTrue(action["summary"].strip(), action_id)

    def test_toda_acao_nova_executa_sem_erro(self):
        for action_id in sum(NOVOS.values(), []):
            state = new_game()
            before = dict(state["metrics"])
            result = powers.execute(state, action_id)
            self.assertIn(result["status"], {"applied", "pending_legislature"}, action_id)
            action = powers.BY_ID[action_id]
            if action["approval"] in {"decreto", "mp"}:
                changed = [k for k in action["effects"] if k in before and state["metrics"][k] != before[k]]
                self.assertTrue(changed or not action["effects"], action_id)

    def test_indulto_de_8_de_janeiro_custa_confianca_e_ganha_lealdade_militar(self):
        state = new_game()
        trust, loyalty = state["metrics"]["institutional_trust"], state["institutions"]["military_loyalty"]
        powers.execute(state, "jus_indulto_8jan")
        self.assertLess(state["metrics"]["institutional_trust"], trust)
        self.assertGreater(state["institutions"]["military_loyalty"], loyalty)

    def test_pec_vai_ao_congresso_e_nao_vale_na_hora(self):
        state = new_game()
        approval = state["metrics"]["approval"]
        powers.execute(state, "jus_stf_numero")
        self.assertEqual(len(state["legislative_calendar"]["pending_bills"]), 1)
        self.assertEqual(state["legislative_calendar"]["pending_bills"][0]["instrument"], "PEC")
        self.assertEqual(state["metrics"]["approval"], approval)


if __name__ == "__main__":
    unittest.main()
