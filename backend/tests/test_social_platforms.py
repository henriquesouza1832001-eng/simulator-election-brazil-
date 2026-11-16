import collections
import unittest

from app.engine import social_feed
from app.engine.state import new_game


def state_with_facts(seed: int):
    state = new_game()
    state["campaign_seed"] = seed
    state["ledger"] = [{"id": i, "title": f"Decisão {i}", "date": "2027-03-01", "status": "rejeitada" if i % 2 else "aprovada"} for i in range(1, 9)]
    state["active_crises"] = [{"id": "c1", "title": "Crise hídrica"}, {"id": "c2", "title": "Greve geral"}]
    state["metrics"]["approval"] = 30.0
    return state


class PlataformasTests(unittest.TestCase):
    def posts(self, seeds=range(1, 16)):
        return [p for s in seeds for p in social_feed.build(state_with_facts(s), limit=200)["posts"]]

    def test_todo_post_tem_plataforma_valida(self):
        posts = self.posts(range(1, 4))
        self.assertTrue(posts)
        for p in posts:
            self.assertIn(p["platform"], social_feed.PLATFORMS)
            self.assertEqual(p["platform_label"], social_feed.PLATFORMS[p["platform"]]["label"])

    def test_imprensa_nao_publica_no_zapzap_e_humor_prefere_o_instante(self):
        posts = self.posts()
        self.assertFalse([p for p in posts if p["kind"] == "imprensa" and p["platform"] == "zapzap"])
        humor = collections.Counter(p["platform"] for p in posts if p["kind"] == "humor")
        self.assertEqual(humor.most_common(1)[0][0], "instante")

    def test_boato_so_nasce_no_zapzap_com_apoio_ou_oposicao(self):
        posts = self.posts()
        boatos = [p for p in posts if p["rumor"]]
        self.assertTrue(boatos, "com 15 partidas deveria haver ao menos um boato")
        for p in boatos:
            self.assertEqual(p["platform"], "zapzap")
            self.assertIn(p["kind"], {"apoio", "oposicao"})
            self.assertIn("epassa", p["text"])
        self.assertFalse([p for p in posts if p["platform"] != "zapzap" and p["rumor"]])

    def test_boato_alcanca_mais_que_o_mesmo_perfil_sem_boato(self):
        posts = self.posts()
        media = lambda xs: sum(xs) / len(xs)
        boato = media([p["reach"] for p in posts if p["rumor"]])
        normal = media([p["reach"] for p in posts if p["platform"] == "zapzap" and not p["rumor"]])
        self.assertGreater(boato, normal)

    def test_determinismo(self):
        self.assertEqual(social_feed.build(state_with_facts(7), limit=50), social_feed.build(state_with_facts(7), limit=50))

    def test_feed_informa_as_plataformas(self):
        feed = social_feed.build(state_with_facts(1))
        self.assertEqual([p["key"] for p in feed["platforms"]], list(social_feed.PLATFORMS))


if __name__ == "__main__":
    unittest.main()
