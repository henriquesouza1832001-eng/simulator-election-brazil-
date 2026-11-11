import unittest
from datetime import date

from app.engine import territory
from app.engine.indicator_registry import REGISTRY, DOMAINS, downstream, explain, for_office, propagate
from app.engine.powers_catalog import ROLES

OFFICES = set(ROLES) | {"prefeito", "governador", "presidente"}


class RegistryTest(unittest.TestCase):
    def test_graph_references_exist(self):
        for item in REGISTRY.values():
            self.assertIn(item["domain"], DOMAINS)
            for d in item["drivers"]:
                self.assertIn(d["from"], REGISTRY, f"{item['id']} depende de {d['from']}")
                self.assertIn(d["sign"], (-1, 1))
                self.assertIn(d["strength"], (1, 2, 3))
            for office in item["levers"]:
                self.assertIn(office, OFFICES)
        self.assertGreaterEqual(len(REGISTRY), 60)

    def test_office_levers_and_propagation(self):
        self.assertTrue(for_office("prefeito"))
        self.assertTrue(for_office("presidente"))
        self.assertIn("pib", {r["id"] for r in downstream("mobilidade")})
        out = propagate({"mobilidade": 1.0})
        self.assertGreater(out["pib"], 0)
        self.assertIn("influences", explain("desemprego"))


class TerritoryTest(unittest.TestCase):
    def setUp(self):
        self.state = {"date": "2027-03-01", "metrics": {"gdp_growth": 2.0}}

    def test_city_uses_real_atlas_data(self):
        bh = territory.city_indicators(self.state, "3106200")
        by_id = {i["id"]: i for i in bh["indicators"]}
        self.assertEqual(by_id["idhm"]["source"], "atlas")
        self.assertGreater(by_id["idhm"]["value"], 0.7)
        self.assertEqual(by_id["mobilidade"]["source"], "estimado")

    def test_overview_covers_states_and_regions(self):
        o = territory.overview(self.state)
        self.assertEqual(len(o["states"]), 27)
        self.assertEqual(len(o["regions"]), 5)

    def test_rodoanel_completes_and_improves_mobility(self):
        before = {i["id"]: i["value"] for i in territory.city_indicators(self.state, "3106200")["indicators"]}
        item = territory.start(self.state, "rodoanel_bh", "governador", "MG", None)
        with self.assertRaises(PermissionError):
            territory.start(self.state, "rodoanel_bh", "governador", "MG", None)
        end = date.fromisoformat(item["end"])
        msgs = territory.advance(self.state, date(2027, 3, 1), end)
        self.assertTrue(msgs)
        after = {i["id"]: i["value"] for i in territory.city_indicators(self.state, "3106200")["indicators"]}
        self.assertGreater(after["mobilidade"], before["mobilidade"])

    def test_office_competence_is_enforced(self):
        with self.assertRaises(PermissionError):
            territory.start(self.state, "rodoanel_bh", "vereador", "MG", None)


if __name__ == "__main__":
    unittest.main()
