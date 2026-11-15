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


def _career(office, **extra):
    return {"date": "2028-10-08", "campaign_seed": 55, "career": {"mode": True, "office": office, "result": "won", "vote_share": 54.0, "opponent_share": 40.0, **extra}}


class FormatosTests(unittest.TestCase):
    def test_lista_soma_as_cadeiras_da_casa(self):
        state = _career("vereador", electoral_result={"district_magnitude": 13, "party_vote_share": 18.0, "party_seats": 3, "valid_votes": 1_300_000,
                                                      "elected": True, "candidate_list_rank": 2, "list": []})
        data = tally.build(state)
        self.assertEqual(data["kind"], "lista")
        final = data["steps"][-1]["parties"]
        self.assertEqual(sum(p["seats"] for p in final), 13)
        self.assertEqual(next(p for p in final if p["mine"])["seats"], 3)
        self.assertEqual(data["quotient"], 100_000)

    def test_zonas_terminam_no_resultado(self):
        data = tally.build(_career("prefeito"))
        self.assertEqual(data["kind"], "zonas")
        self.assertEqual(data["steps"][-1]["counted"], 100.0)
        self.assertAlmostEqual(data["steps"][-1]["national_player"], data["player_final"], delta=0.3)

    def test_sem_resultado_na_carreira(self):
        state = _career("vereador")
        state["career"]["result"] = None
        self.assertFalse(tally.build(state)["available"])


class CampanhaNasRedesTests(unittest.TestCase):
    def test_acao_de_campanha_vira_publicacao_com_a_fala(self):
        state = _state()
        state["campaign"]["activities"] = [{"id": "a1", "date": "2030-09-20", "label": "Comício", "region_label": "Nordeste", "score": 82,
                                            "message": "Vou cortar juros do povo e investir em escola de tempo integral"}]
        feed = social_feed.build(state)
        posts = [p for p in feed["posts"] if p["origin"].startswith("Comício")]
        self.assertTrue(posts)
        self.assertTrue(any("tempo integral" in p["text"] or "Comício" in p["text"] for p in posts))

    def test_acao_viral_gera_post_de_alcance(self):
        state = _state()
        state["career"] = {"activities": [{"id": "b1", "date": "2030-09-21", "label": "Live", "score": 70, "message": "ola", "social_result": {"virality_pct": 90}}]}
        feed = social_feed.build(state)
        self.assertTrue(any(p["origin"].startswith("Live") for p in feed["posts"]))


class TurnosTests(unittest.TestCase):
    def test_apuracao_mostra_os_dois_turnos(self):
        state = _career("presidente", first_round_results=[{"name": "A", "party": "X", "support": 41.0, "is_player": True}, {"name": "B", "party": "Y", "support": 38.0}],
                        runoff_results=[{"name": "A", "party": "X", "support": 52.0, "is_player": True}, {"name": "B", "party": "Y", "support": 48.0}])
        data = tally.build(state)
        self.assertEqual(data["kind"], "mapa")
        self.assertEqual(len(data["rounds"]["first"]), 2)
        self.assertEqual(data["rounds"]["runoff"][0]["support"], 52.0)

    def test_sem_segundo_turno(self):
        state = _career("presidente", first_round_results=[{"name": "A", "party": "X", "support": 55.0, "is_player": True}])
        self.assertIsNone(tally.build(state)["rounds"]["runoff"])


class IndicadoresNasRedesTests(unittest.TestCase):
    def test_inflacao_e_desemprego_altos_geram_posts_com_o_numero(self):
        state = _state()
        state["metrics"] = {"inflation": 7.2, "unemployment": 9.4, "approval": 28.0}
        feed = social_feed.build(state, limit=200)
        origins = {p["origin"] for p in feed["posts"]}
        self.assertTrue({"Inflação", "Desemprego", "Aprovação do governo"} <= origins)
        self.assertTrue(any("7,2" in p["text"] for p in feed["posts"]))

    def test_numeros_normais_nao_geram_ruido(self):
        state = _state()
        state["metrics"] = {"inflation": 4.0, "unemployment": 6.0, "approval": 48.0}
        origins = {p["origin"] for p in social_feed.build(state, limit=200)["posts"]}
        self.assertFalse({"Inflação", "Desemprego", "Aprovação do governo"} & origins)


if __name__ == "__main__":
    unittest.main()
