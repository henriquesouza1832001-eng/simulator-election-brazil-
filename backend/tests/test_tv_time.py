import unittest

from app.engine import tv_time


class TvTimeTests(unittest.TestCase):
    def test_bancada_maior_tem_mais_tempo(self):
        big = tv_time.share("PL")
        small = tv_time.share("REDE")
        self.assertGreater(big["share_pct"], small["share_pct"])
        self.assertGreater(big["seats"], small["seats"])

    def test_partido_sem_bancada_fica_so_com_a_parte_igual(self):
        s = tv_time.share("Partido Inventado")
        self.assertEqual(s["seats"], 0)
        self.assertEqual(s["proportional_pct"], 0)
        self.assertGreater(s["share_pct"], 0)
        self.assertLess(s["share_pct"], 2.0)

    def test_soma_do_horario_chega_a_cem(self):
        parties = tv_time.legislature.PARTIES
        total = sum(tv_time.share(p["id"])["share_pct"] for p in parties if p["seats"] > 0)
        self.assertAlmostEqual(total, 100.0, delta=0.5)

    def test_efeito_e_limitado_e_so_amplia_ganhos(self):
        self.assertLessEqual(tv_time.share("PL")["factor"], 1.12)
        self.assertGreaterEqual(tv_time.share("Partido Inventado")["factor"], 0.92)
        self.assertEqual(tv_time.apply(-0.5, "PL"), -0.5)
        self.assertGreater(tv_time.apply(1.0, "PL"), 1.0)
        self.assertLess(tv_time.apply(1.0, "Partido Inventado"), 1.0)


if __name__ == "__main__":
    unittest.main()
