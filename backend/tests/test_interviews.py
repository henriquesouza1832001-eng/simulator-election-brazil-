import unittest
from datetime import date

from app.engine import interviews, powers
from app.engine.state import new_game, refresh_calendar_fields
from tests.test_office_powers import career_state

GOOD = ("Vamos reduzir a inflação de 4,5% para a meta com juros responsáveis e controle de preços; a secretaria da fazenda divulga "
        "o plano em 90 dias e presta contas todo mês ao congresso e à população.")
INSULT = "Isso é uma mentira de um mentiroso e canalha, não vou responder essa pergunta de jeito nenhum hoje."


def president():
    s = refresh_calendar_fields(new_game())
    s["date"] = "2027-03-01"
    return s


class InterviewsTest(unittest.TestCase):
    def test_questions_use_real_game_facts_and_last_decision(self):
        s = president()
        powers.execute(s, "seg_armas_afrouxar")
        qs = interviews.build_questions(s, "sabatina")
        self.assertEqual(len(qs), 5)
        joined = " ".join(q["prompt"] for q in qs)
        self.assertIn(f"{s['metrics']['inflation']:.1f}%", " ".join(q["prompt"] for q in interviews._fact_questions(s, interviews._context(s))))
        self.assertTrue("decisão" in {q["topic"] for q in qs} or "crise" in {q["topic"] for q in qs}, joined)

    def test_scoring_rewards_theme_data_commitment_and_tone(self):
        q = {"topic": "inflação", "terms": ["inflacao", "preco", "juros", "meta"], "fact": 4.5}
        good = interviews.score_answer(GOOD, q)
        bad = interviews.score_answer(INSULT, q)
        self.assertGreater(good["total"], 75)
        self.assertLess(bad["total"], 20)
        self.assertEqual(good["criteria"]["compromisso"], 25.0)
        self.assertIn("ataques", bad["feedback"]["tom"])

    def test_full_interview_applies_persistent_effects_and_cooldown(self):
        s = president()
        interviews.start(s, "entrevista")
        approval = s["metrics"]["approval"]
        for _ in range(3):
            out = interviews.answer(s, GOOD)
        self.assertTrue(out["done"])
        self.assertGreater(s["metrics"]["approval"], approval)
        self.assertEqual(s["interviews"]["history"][0]["grade"], "forte")
        self.assertTrue(any(f["action_id"] == "entrevista" for f in s["consequences"]["feed"]))
        self.assertEqual(s["ledger"][0]["source"], "imprensa")
        with self.assertRaises(PermissionError):
            interviews.start(s, "entrevista")  # intervalo de 21 dias

    def test_short_answer_is_rejected_and_debate_needs_campaign(self):
        s = president()
        with self.assertRaises(PermissionError):
            interviews.start(s, "debate")
        interviews.start(s, "sabatina")
        with self.assertRaises(ValueError):
            interviews.answer(s, "curto")

    def test_debate_has_five_stages_in_campaign_and_moves_momentum(self):
        s = career_state("vereador")
        s["career"].update(phase="campaign", momentum=0.0, poll_support=30.0, opponents=[{"name": "Candidato(a) do PL", "party": "PL"}])
        interviews.start(s, "debate")
        stages = [q["stage"] for q in s["interviews"]["current"]["questions"]]
        self.assertEqual(stages, ["Abertura", "Bloco 1", "Direito de resposta", "Bloco 2", "Considerações finais"])
        self.assertIn("Candidato(a) do PL", s["interviews"]["current"]["questions"][2]["prompt"])
        for _ in range(5):
            out = interviews.answer(s, GOOD)
        self.assertGreater(s["career"]["momentum"], 0)
        self.assertGreater(s["career"]["poll_support"], 30.0)


if __name__ == "__main__":
    unittest.main()
