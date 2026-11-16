import unittest

from app.engine import tally_municipal
from app.engine.state import new_game


def presidente(result=True, share=52.0):
    state = new_game()
    state["career"] = {"mode": True, "office": "presidente", "result": "won" if result else None, "vote_share": share, "phase": "office"}
    state["campaign_seed"] = 4321
    return state


class TallyMunicipalTests(unittest.TestCase):
    def test_sem_resultado_nao_ha_mapa(self):
        out = tally_municipal.build(presidente(result=False), "SP")
        self.assertFalse(out["available"])

    def test_soma_dos_municipios_bate_com_o_estado(self):
        state = presidente()
        for uf in ("SP", "MG", "AC"):
            out = tally_municipal.build(state, uf)
            self.assertTrue(out["available"], uf)
            total = sum(t["electorate"] for t in out["tiles"])
            media = sum(t["share"] * t["electorate"] for t in out["tiles"]) / total
            self.assertAlmostEqual(media, out["state_share"], delta=0.3, msg=uf)

    def test_numero_de_municipios_e_ordem_por_eleitorado(self):
        out = tally_municipal.build(presidente(), "SP")
        self.assertEqual(out["municipalities"], 645)
        eleitorados = [t["electorate"] for t in out["tiles"]]
        self.assertEqual(eleitorados, sorted(eleitorados, reverse=True))
        self.assertEqual(out["tiles"][0]["name"], "São Paulo")

    def test_determinismo_por_semente(self):
        a = tally_municipal.build(presidente(), "BA")
        b = tally_municipal.build(presidente(), "BA")
        self.assertEqual(a["tiles"], b["tiles"])
        outra = presidente()
        outra["campaign_seed"] = 99
        self.assertNotEqual(a["tiles"], tally_municipal.build(outra, "BA")["tiles"])

    def test_governador_so_ve_o_proprio_estado(self):
        state = new_game()
        state["career"] = {"mode": True, "office": "governador", "state_code": "PR", "result": "won", "vote_share": 55.0, "opponent_share": 45.0}
        self.assertEqual(tally_municipal.available_ufs(state), ["PR"])
        self.assertTrue(tally_municipal.build(state, "PR")["available"])
        self.assertFalse(tally_municipal.build(state, "SP")["available"])

    def test_vitoria_aparece_em_mais_municipios_que_derrota(self):
        ganha = tally_municipal.build(presidente(share=65.0), "MG")
        perde = tally_municipal.build(presidente(share=35.0), "MG")
        self.assertGreater(ganha["won"], perde["won"])


if __name__ == "__main__":
    unittest.main()
