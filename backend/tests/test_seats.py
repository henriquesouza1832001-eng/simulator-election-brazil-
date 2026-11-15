import unittest

from app.engine import seats


class SeatsTests(unittest.TestCase):
    def test_bancadas_federais_somam_513(self):
        self.assertEqual(sum(seats.FEDERAL_SEATS.values()), 513)
        self.assertEqual(len(seats.FEDERAL_SEATS), 27)

    def test_deputados_estaduais_seguem_a_constituicao(self):
        self.assertEqual(seats.estadual("SP"), 94)   # 70 federais + 24
        self.assertEqual(seats.estadual("AC"), 24)   # mínimo
        self.assertEqual(seats.estadual("PB"), 36)   # 3 x 12
        self.assertEqual(seats.estadual("MG"), 77)

    def test_vereadores_pela_populacao(self):
        self.assertEqual(seats.vereadores(10_000), 9)
        self.assertEqual(seats.vereadores(50_000), 13)
        self.assertEqual(seats.vereadores(500_000), 25)
        self.assertEqual(seats.vereadores(11_900_000), 55)
        self.assertEqual(seats.vereadores(None), 13)

    def test_por_cargo(self):
        self.assertEqual(seats.for_office("deputado_federal", "SP"), 70)
        self.assertEqual(seats.for_office("vereador", None, 3_000_000), 43)


if __name__ == "__main__":
    unittest.main()
