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

    def test_debate_is_a_real_format_with_opponents_checks_and_poll(self):
        s = career_state("vereador")
        s["career"].update(phase="campaign", momentum=0.0, poll_support=30.0, opponents=[{"name": "Candidato(a) do PL", "party": "PL"}, {"name": "Candidato(a) do PT", "party": "PT"}])
        interviews.start(s, "debate")
        cur = s["interviews"]["current"]
        self.assertEqual([q["stage"] for q in cur["questions"]], ["Abertura", "Bloco 1", "Réplica", "Bloco 2", "Pergunta ao adversário", "Resposta ao adversário", "Considerações finais"])
        self.assertEqual([o["party"] for o in cur["opponents"]], ["PL", "PT"])
        self.assertEqual(cur["transcript"][0]["who"], "Mediador")
        out = interviews.answer(s, GOOD)
        self.assertTrue(any(t["who"] == "Candidato(a) do PL" for t in cur["transcript"]))   # adversário fala após a abertura
        interviews.answer(s, GOOD)                                                         # bloco 1
        replica = s["interviews"]["current"]["questions"][2]["prompt"]
        self.assertIn("Direito de resposta", replica)                                       # ataque montado após o bloco 1
        for _ in range(5):
            out = interviews.answer(s, GOOD + " Pergunto: como o seu plano será financiado e em que prazo?")
        self.assertTrue(out["done"])
        summary = out["summary"]
        self.assertEqual(set(summary["opponent_scores"]), {"Candidato(a) do PL", "Candidato(a) do PT"})
        self.assertIn("poll_before", summary)
        self.assertGreater(s["career"]["momentum"], 0)
        self.assertTrue(len(summary["transcript"]) > 8)

    def test_fact_check_penalizes_wrong_numbers_and_long_answers_are_accepted(self):
        from app.engine import debate
        self.assertIsNotNone(debate.fact_check("a inflação está em 40% hoje", 4.5))
        self.assertIsNone(debate.fact_check("a inflação está em 4,6% hoje", 4.5))
        s = president()
        interviews.start(s, "sabatina")
        long_text = ("Vamos reduzir a inflação com juros responsáveis, a secretaria publica o plano em 90 dias. " * 40)[:5000]
        out = interviews.answer(s, long_text)
        self.assertFalse(out["done"])
        with self.assertRaises(ValueError):
            interviews.answer(s, "x" * 6001)


if __name__ == "__main__":
    unittest.main()
