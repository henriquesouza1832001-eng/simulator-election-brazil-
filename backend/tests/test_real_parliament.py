import unittest

from app.engine import legislature


class RealParliamentTest(unittest.TestCase):
    def test_roster_sizes_and_parties_are_real(self):
        house = legislature.composition({"campaign_seed": 7})
        self.assertEqual(len(house["camara"]), 513)
        self.assertEqual(len(house["senado"]), 81)
        parties = {m["party"] for m in house["camara"]}
        self.assertTrue({"PL", "PT", "PSOL", "PSD", "MDB"} <= parties)
        self.assertFalse(parties & {"PTR", "PLB", "MDC", "UDB", "PSU"})

    def test_ideology_ordering_makes_sense(self):
        pos = {p["id"]: p["ideology"] for p in legislature.PARTIES}
        self.assertLess(pos["PSOL"], pos["PT"])
        self.assertLess(pos["PT"], pos["MDB"])
        self.assertLess(pos["MDB"], pos["PL"])
        self.assertLess(pos["PSOL"], -0.9)
        self.assertGreater(pos["PL"], 0.7)

    def test_seat_counts_match_roster(self):
        total = sum(p["seats"] for p in legislature.PARTIES)
        self.assertEqual(total, 513)
        self.assertEqual(sum(p["senate"] for p in legislature.PARTIES), 81)

    def test_every_party_in_roster_has_profile(self):
        missing = {p["id"] for p in legislature.PARTIES} - set(legislature.PARTY_PROFILE)
        self.assertEqual(missing, set())


if __name__ == "__main__":
    unittest.main()
