import unittest

from app.engine import social_feed, tally


def _state(result="lost", margin=-20.0):
    return {"date": "2030-10-07", "campaign_seed": 777, "election": {"date": "2030-10-06", "result": result, "margin": margin},
            "campaign": {"regional_support": {"norte": 50, "nordeste": 60, "centro_oeste": 45, "sudeste": 50, "sul": 40}, "funds_bi": 1.2, "momentum": 2.0,
                         "national_support": 49.0, "activities": [{"id": 1}]},
            "ledger": [{"id": 1, "date": "2030-09-01", "title": "Reforma do transporte", "status": "aprovada"}], "active_crises": [{"id": "x", "title": "Seca no Nordeste"}]}


class TallyTests(unittest.TestCase):
    def test_sem_resultado_nao_ha_apuracao(self):
        self.assertFalse(tally.build({"date": "2030-01-01", "campaign_seed": 1})["available"])

    def test_boletins_terminam_no_resultado_nacional(self):
        data = tally.build(_state())
        self.assertTrue(data["available"])
        last = data["steps"][-1]
        self.assertEqual(last["counted"], 100.0)
        self.assertAlmostEqual(last["national_player"], data["player_final"], delta=0.2)
        self.assertEqual(len(last["closed"]), 27)

    def test_contagem_so_cresce(self):
        steps = tally.build(_state())["steps"]
        counted = [s["counted"] for s in steps]
        self.assertEqual(counted, sorted(counted))
        self.assertIsNone(steps[0]["national_player"])

    def test_determinista_pela_semente(self):
        self.assertEqual(tally.build(_state()), tally.build(_state()))

    def test_vitoria_e_derrota_seguem_a_margem(self):
        self.assertGreater(tally.build(_state("won", 12.0))["player_final"], 50)
        self.assertLess(tally.build(_state("lost", -12.0))["player_final"], 50)


class SocialTests(unittest.TestCase):
    def test_publicacoes_nascem_de_fatos(self):
        feed = social_feed.build(_state())
        origins = " ".join(p["origin"] for p in feed["posts"])
        self.assertIn("Seca no Nordeste", origins)
        self.assertIn("Reforma do transporte", origins)
        self.assertIn("Resultado da eleição", origins)

    def test_perfis_sao_ficticios_e_alcance_positivo(self):
        for p in social_feed.build(_state())["posts"]:
            self.assertGreater(p["reach"], 0)
            self.assertTrue(p["handle"].startswith("@"))

    def test_determinista(self):
        self.assertEqual(social_feed.build(_state()), social_feed.build(_state()))


if __name__ == "__main__":
    unittest.main()
