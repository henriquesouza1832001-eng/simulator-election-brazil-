import re
import unittest

from app.engine import voice
from app.engine.macro import _pct


def sinal(r):
    return f"{'+' if r >= 0 else '−'}{abs(round(r))} pontos"


class VozDoJogoTests(unittest.TestCase):
    def test_escolha_e_estavel_para_a_mesma_semente(self):
        self.assertEqual(voice.pick(voice.PRESS_UP, "x"), voice.pick(voice.PRESS_UP, "x"))
        self.assertGreater(len({voice.pick(voice.PRESS_UP, str(i)) for i in range(40)}), 1)   # e varia entre sementes

    def test_manchete_do_mercado_mantem_todos_os_numeros_do_motor(self):
        for bolsa, cambio, risco in ((-6.2, 4.1, 55), (6.2, -3.4, -40), (1.0, 0.5, 3)):
            texto = voice.market_day("s", bolsa, cambio, risco, _pct, sinal)
            self.assertIn(_pct(bolsa), texto)
            self.assertIn(_pct(cambio), texto)
            self.assertIn(sinal(risco), texto)

    def test_nada_diegetico_cita_simulacao(self):
        todos = voice.PRESS_UP + voice.PRESS_DOWN + voice.OPPOSITION + voice.SUPPORT + voice.MARKET_BY_DECISION + voice.MARKET_DESC + voice.POLL_LEAD + voice.POLL_TRAIL + [voice.EXPIRED_PAUTA, voice.EXPIRED_CRISIS]
        for texto in todos:
            self.assertIsNone(re.search(r"simula", texto, re.I), texto)

    def test_variantes_de_partido_aceitam_a_sigla(self):
        self.assertIn("PSB", voice.pick(voice.OPPOSITION, "k").format(party="PSB"))


if __name__ == "__main__":
    unittest.main()


class VozNasEntrevistasTests(unittest.TestCase):
    def test_perguntas_de_entrevista_e_sabatina_ganham_deixa_sem_perder_o_fato(self):
        from app.engine import interviews
        from app.engine.state import new_game
        s = new_game()
        s["date"] = "2027-05-01"
        for kind in ("entrevista", "sabatina"):
            perguntas = interviews.build_questions(s, kind)
            com_deixa = [q for q in perguntas if any(q["prompt"].startswith(lead) for lead in voice.REPORTER_LEADS[kind])]
            self.assertTrue(com_deixa, kind)
            self.assertLess(len(com_deixa), len(perguntas))   # só parte delas ganha deixa
        base = interviews._fact_questions(s, interviews._context(s))
        self.assertTrue(base)   # o fato (número do motor) continua na pergunta de origem

    def test_deixas_nao_citam_simulacao(self):
        for leads in voice.REPORTER_LEADS.values():
            for lead in leads:
                self.assertNotIn("simula", lead.lower())

    def test_crises_genericas_sem_a_palavra_simulado(self):
        from app.engine.events import EVENTS
        for event in EVENTS.values():
            self.assertNotIn("simula", event["description"].lower())
