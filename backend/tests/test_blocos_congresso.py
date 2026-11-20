import unittest

from app.engine import congress_process as cp
from tests.test_congress_process import bill_for


class BlocosDoCongressoTests(unittest.TestCase):
    def test_partidos_se_agrupam_em_blocos_com_lider_na_maior_bancada(self):
        s, bill = bill_for()   # privatização: ação de direita
        grupos = {b["id"]: b for b in cp.blocs(s, bill)}
        self.assertGreaterEqual(len(grupos), 2)
        rows = {r["party"]: r for r in cp.party_outlook(s, bill)}
        for grupo in grupos.values():
            lider = max(grupo["parties"], key=lambda p: rows[p]["seats"])
            self.assertEqual(grupo["leader"], lider)
            self.assertEqual(grupo["seats"], sum(rows[p]["seats"] for p in grupo["parties"]))
        todos = [p for g in grupos.values() for p in g["parties"]]
        self.assertEqual(len(todos), len(set(todos)))   # cada partido está em um só bloco
        self.assertEqual(set(todos), set(rows))

    def test_pacote_ao_bloco_sobe_a_relacao_de_todos_os_partidos_e_mais_ao_lider(self):
        s, bill = bill_for()
        grupo = max(cp.blocs(s, bill), key=lambda b: len(b["parties"]))
        antes = {p: s.get("relation_delta", {}).get(p, 0.0) for p in grupo["parties"]}
        r = cp.negotiate_bloc(s, bill["id"], grupo["id"], "emendas")
        self.assertEqual(r["leader"], grupo["leader"])
        for p in grupo["parties"]:
            self.assertGreater(s["relation_delta"][p], antes[p])
        lider = s["relation_delta"][grupo["leader"]] - antes[grupo["leader"]]
        outro = next((p for p in grupo["parties"] if p != grupo["leader"]), None)
        if outro:
            self.assertGreater(lider, s["relation_delta"][outro] - antes[outro])

    def test_pacote_custa_mais_quanto_maior_o_bloco(self):
        s, bill = bill_for()
        grupo = max(cp.blocs(s, bill), key=lambda b: len(b["parties"]))
        antes = s["metrics"].get("integrity", 70)
        r = cp.negotiate_bloc(s, bill["id"], grupo["id"], "cargo")
        esperado = 1 + cp.BLOC_PACKAGE_COST_PER_EXTRA_PARTY * (len(grupo["parties"]) - 1)
        self.assertAlmostEqual(r["cost_factor"], esperado, places=2)
        self.assertLess(s["metrics"]["integrity"], antes)

    def test_mesma_oferta_ao_mesmo_bloco_nao_se_repete(self):
        s, bill = bill_for()
        grupo = cp.blocs(s, bill)[0]
        cp.negotiate_bloc(s, bill["id"], grupo["id"], "emendas")
        with self.assertRaises(PermissionError):
            cp.negotiate_bloc(s, bill["id"], grupo["id"], "emendas")

    def test_visao_geral_traz_os_blocos(self):
        s, bill = bill_for()
        ov = cp.overview(s)
        self.assertTrue(ov["bills"][0]["blocs"])


if __name__ == "__main__":
    unittest.main()
