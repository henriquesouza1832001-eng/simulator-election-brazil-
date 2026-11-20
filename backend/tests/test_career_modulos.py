import pathlib
import unittest

ENGINE = pathlib.Path(__file__).resolve().parents[1] / "app" / "engine"


class CarreiraDivididaTests(unittest.TestCase):
    def test_fachada_reexporta_a_api_publica_e_os_nomes_internos_usados(self):
        from app.engine import career
        for name in ("start_career", "career_overview", "perform_career_action", "perform_career_preparation", "perform_governance_action", "advance_career",
                     "resolve_career_election", "governance_actions_for", "is_career_governing", "career_options", "validate_party_name",
                     "_opponent_supports", "_ensure_opponents", "_campaign", "_clamp", "_proportional_result", "_is_explicit_promise",
                     "ISSUES", "OFFICES", "GROUPS", "STATES", "FAMILY_GROUP_EFFECTS", "SPECTRUM_GROUP_EFFECTS", "IDEOLOGY_SPECTRUM", "SPECTRUM_ORDER"):
            self.assertTrue(hasattr(career, name), name)

    def test_nenhum_modulo_da_carreira_passa_de_450_linhas(self):
        for path in sorted(ENGINE.glob("career*.py")):
            lines = len(path.read_text(encoding="utf-8").splitlines())
            self.assertLessEqual(lines, 450, f"{path.name} tem {lines} linhas; divida por responsabilidade")


if __name__ == "__main__":
    unittest.main()


class FrontDivididoTests(unittest.TestCase):
    """O problema dos arquivos grandes do front é tamanho em KB (linhas muito longas), então o limite é em KB."""

    def test_app_e_painel_da_carreira_ficam_abaixo_de_50_kb(self):
        src = pathlib.Path(__file__).resolve().parents[2] / "src"
        for name in ("App.jsx", "CareerPanel.jsx"):
            kb = (src / name).stat().st_size / 1024
            self.assertLessEqual(kb, 50, f"{name} tem {kb:.0f} KB; extraia blocos para componentes")

    def test_componentes_extraidos_existem(self):
        src = pathlib.Path(__file__).resolve().parents[2] / "src"
        for name in ("BudgetSection", "CrisesSection", "InstitutionsSection", "MeasuresSection", "TopBar", "TabNav", "appData",
                     "CareerMandate", "CareerCampaignForm", "CareerSummaryColumns", "CareerHistory"):
            self.assertTrue((src / f"{name}.jsx").exists(), name)
