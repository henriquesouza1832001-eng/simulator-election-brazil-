import asyncio
import os
import unittest
from unittest import mock

from app.ai import gateway, mapper_ai, narrator, question_ai
from app.engine import interviews
from app.engine.state import new_game, refresh_calendar_fields

FACTS = [{"topic": "inflação", "text": "A inflação está em 4.5% ao ano. Que medidas o governo adotará?"}]


def run(coro):
    return asyncio.run(coro)


class GatewayTest(unittest.TestCase):
    def setUp(self):
        self.env = mock.patch.dict(os.environ, {"GEMINI_GATEWAY_URL": "https://gw.example.workers.dev", "GEMINI_GATEWAY_TOKEN": "t" * 24})
        self.env.start()
        os.environ.pop("GEMINI_API_KEY", None)

    def tearDown(self):
        self.env.stop()

    def test_configured_requires_both_variables_and_https(self):
        self.assertTrue(gateway.configured())
        with mock.patch.dict(os.environ, {"GEMINI_GATEWAY_URL": "http://inseguro.example"}):
            self.assertIsNone(run(gateway.post("/v1/questions", {})))

    def test_questions_are_validated_even_when_gateway_answers(self):
        good = {"source": "gemini", "questions": [{"topic": "inflação", "prompt": "A inflação está em 4.5% ao ano. O que o governo fará nos próximos meses?"}]}
        bad = {"source": "gemini", "questions": [{"topic": "inflação", "prompt": "A inflação subiu para 9.9% neste mês. Qual é a sua explicação para isso?"}]}
        with mock.patch.object(gateway, "post", mock.AsyncMock(return_value=good)):
            out = run(question_ai.generate(FACTS, ["inflação"], "entrevista", "presidente", 2))
        self.assertEqual(out["source"], "gemini")
        with mock.patch.object(gateway, "post", mock.AsyncMock(return_value=bad)):
            out = run(question_ai.generate(FACTS, [], "entrevista", "presidente", 2))
        self.assertEqual(out, {"questions": [], "source": "local"})

    def test_action_choice_through_gateway_must_be_a_candidate(self):
        cands = [{"id": "a", "title": "A"}, {"id": "b", "title": "B"}]
        with mock.patch.object(gateway, "post", mock.AsyncMock(return_value={"source": "gemini", "choice": "zzz", "questions": []})):
            self.assertEqual(run(mapper_ai.refine("x", cands, []))["source"], "local")
        with mock.patch.object(gateway, "post", mock.AsyncMock(return_value={"source": "gemini", "choice": "b", "questions": ["Qual das duas você quer?"]})):
            out = run(mapper_ai.refine("x", cands, []))
        self.assertEqual((out["choice"], out["source"]), ("b", "gemini"))

    def test_narration_through_gateway_is_filtered(self):
        facts = {"title": "Recapear vias", "forecast": {"mobilidade": 2.0}, "result": {"mobilidade": 2.0}}
        with mock.patch.object(gateway, "post", mock.AsyncMock(return_value={"source": "gemini", "text": "A obra cortou 37 minutos do trajeto na cidade inteira."})):
            self.assertEqual(run(narrator.narrate(facts))["source"], "local")


class InterviewAiTest(unittest.TestCase):
    def test_generated_questions_replace_last_ones_and_weak_topics_use_history(self):
        s = refresh_calendar_fields(new_game())
        s["date"] = "2027-03-01"
        s["interviews"] = {"current": None, "last": {}, "history": [{"answers": [{"topic": "dívida", "total": 30}, {"topic": "emprego", "total": 80}]}]}
        self.assertEqual(interviews.weak_topics(s), ["dívida"])
        self.assertTrue(interviews.facts_for_ai(s))
        extra = [{"topic": "dívida", "prompt": "A dívida pública é de 78% do PIB. Qual é o plano para reduzi-la sem cortar saúde?"}]
        out = interviews.start(s, "entrevista", extra)
        qs = s["interviews"]["current"]["questions"]
        self.assertTrue(qs[-1].get("ai"))
        self.assertEqual(len(qs), 3)


if __name__ == "__main__":
    unittest.main()
