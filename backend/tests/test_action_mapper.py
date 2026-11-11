import asyncio
import unittest

from app.ai import mapper_ai
from app.engine import action_mapper, powers
from app.engine.state import new_game, refresh_calendar_fields


def catalog():
    s = refresh_calendar_fields(new_game())
    s["date"] = "2027-03-01"
    return powers.catalog_for(s, "presidente", True)["actions"]


class ActionMapperTest(unittest.TestCase):
    def top(self, text):
        rows = action_mapper.rank(text, catalog())
        return rows[0]["id"] if rows else None

    def test_examples_from_the_brief_map_to_expected_actions(self):
        cases = {
            "quero asfaltar a BR-163": "infra_asfaltar",
            "duplicar a rodovia BR-101": "infra_duplicar",
            "vender a concessão da rodovia": "infra_vender_concessao",
            "abrir Alcântara para foguetes comerciais": "defesa_alcantara",
            "construir uma bomba nuclear": "defesa_bomba",
            "mudar para o parlamentarismo": "reg_forma_governo",
            "liberar o porte de arma": "seg_armas_afrouxar",
            "desmilitarizar a polícia": "seg_desmilitarizar",
            "criar uma moeda da américa do sul": "bc_moeda_comum",
            "sair do BRICS": "ext_brics_sair",
            "entrar na OTAN": "ext_otan",
            "aderir à OPEP": "ext_opep",
            "privatizar os Correios": "empresa_privatizar",
            "acabar com a autonomia do banco central": "bc_revogar_autonomia",
        }
        for text, expected in cases.items():
            self.assertEqual(self.top(text), expected, text)

    def test_option_is_guessed_from_text(self):
        row = action_mapper.rank("asfaltar a BR-163 no Pará", catalog())[0]
        self.assertEqual(row["option_guess"], "BR-163 (MT-PA)")

    def test_missing_option_generates_question(self):
        rows = action_mapper.rank("quero asfaltar uma rodovia", catalog())
        qs = action_mapper.questions_for("quero asfaltar uma rodovia", rows)
        self.assertTrue(any("Em qual destes" in q for q in qs))

    def test_nonsense_asks_for_area(self):
        rows = action_mapper.rank("bom dia, tudo bem", catalog())
        self.assertEqual(rows, [])
        self.assertTrue(action_mapper.questions_for("bom dia", rows))
        self.assertTrue(action_mapper.needs_ai(rows))

    def test_learned_choice_boosts_candidate(self):
        base = action_mapper.rank("mexer nos preços", catalog())
        boosted = action_mapper.rank("mexer nos preços", catalog(), [{"action_id": "eco_confisco"}])
        self.assertTrue(boosted and boosted[0]["id"] == "eco_confisco")
        self.assertNotEqual([r["id"] for r in base][:1], ["zzz"])

    def test_ai_output_is_validated_against_candidate_ids(self):
        ids = ["a", "b"]
        self.assertIsNone(mapper_ai.validate({"choice": "inventado", "questions": []}, ids)["choice"])
        self.assertEqual(mapper_ai.validate({"choice": "a", "questions": ["Qual rodovia você quer?", "x", 5]}, ids)["questions"], ["Qual rodovia você quer?"])
        self.assertEqual(asyncio.run(mapper_ai.refine("x", [{"id": "a", "title": "A"}], [])), {"choice": None, "questions": [], "source": "local"})


if __name__ == "__main__":
    unittest.main()
