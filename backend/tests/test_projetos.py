import unittest
from datetime import date, timedelta

from app.engine import works
from app.engine.state import new_game


class ProjetosTests(unittest.TestCase):
    def setUp(self):
        self.state = new_game()

    def test_catalogo_cobre_areas_e_traz_o_programa_espacial(self):
        catalog = works.WORK_CATALOG
        self.assertGreaterEqual(len(catalog), 35)
        for key in ("alcantara_comercial", "satelites_nacionais", "astronauta_orbita", "missao_lunar", "ponte_amazonica", "metro_capital"):
            self.assertIn(key, catalog)
        self.assertGreaterEqual(len({item["area"] for item in catalog.values()}), 6)
        for key, item in catalog.items():
            self.assertTrue(item["name"] and item["regions"] and item["base_cost_bi"] > 0 and item["duration_days"] > 0, key)
            self.assertIn(item["area"], works.AREA_LABEL, key)

    def test_projeto_e_pago_pela_carteira_da_propria_area(self):
        result = works.start_work(self.state, "alcantara_comercial", "consorcio_horizonte")
        project = result["project"]
        self.assertEqual(project["area"], "science")
        committed = works.refresh_work_finance(self.state)["annual_commitment_by_area"]
        self.assertGreater(committed["science"], 0)
        self.assertNotIn("logistics", committed)

    def test_missao_lunar_exige_remanejar_orcamento(self):
        with self.assertRaises(ValueError) as ctx:
            works.start_work(self.state, "missao_lunar", "consorcio_horizonte")
        self.assertIn("Ciência", str(ctx.exception))
        self.state["budget"]["allocations"]["science"] = 40.0
        works.start_work(self.state, "missao_lunar", "consorcio_horizonte")

    def test_visao_tem_fases_e_areas(self):
        works.start_work(self.state, "satelites_nacionais", "consorcio_horizonte")
        view = works.works_overview(self.state)
        self.assertEqual(len(view["areas"]), len(works.AREA_LABEL))
        project = view["projects"][0]
        self.assertEqual(project["phase"], "Projeto e acordos")
        self.assertEqual(project["phases"][-1], "Lançamento e operação")
        option = next(item for item in view["options"] if item["id"] == "missao_lunar")
        self.assertEqual(option["area_label"], "Ciência, tecnologia e espaço")
        self.assertFalse(option["affordable"])

    def test_entrega_aplica_efeito_nacional_e_noticia_propria(self):
        before = float(self.state["metrics"]["approval"])
        works.start_work(self.state, "astronauta_orbita", "consorcio_horizonte")
        project = self.state["budget"]["works"]["projects"][0]
        project["risk"] = 0.0
        project["financial_risk"] = 0.0
        project["integrity_risk"] = 0.0
        start = date.fromisoformat(self.state["date"])
        end = start + timedelta(days=int(project["duration_days"]) + 5)
        messages = works.advance_works(self.state, start, end)
        self.assertEqual(project["status"], "delivered")
        self.assertTrue(any("brasileiro foi ao espaço" in text for text in messages))
        self.assertGreater(float(self.state["metrics"]["approval"]), before)

    def test_obra_antiga_continua_na_carteira_de_transportes(self):
        result = works.start_work(self.state, "br116_sul", "consorcio_horizonte")
        self.assertEqual(result["project"]["area"], "logistics")
        view = works.works_overview(self.state)
        self.assertGreater(view["annual_committed_bi"], 0)


if __name__ == "__main__":
    unittest.main()
