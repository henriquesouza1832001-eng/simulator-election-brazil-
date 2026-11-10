"""Remix de eventos históricos: fora de época, único por partida, reproduzível."""
from __future__ import annotations

import unittest
from datetime import date

from app.engine import story
from app.engine.event_library import get_library
from app.engine.event_remix import is_historical, remix, remap_places, scale_effects
from app.engine.state import new_game, refresh_calendar_fields


def _historical(substr: str):
    return next(e for e in get_library().events.values() if is_historical(e) and substr in e["title"])


class RemixTests(unittest.TestCase):
    def test_historical_events_exist_with_source_and_review_label(self):
        hist = [e for e in get_library().events.values() if is_historical(e)]
        self.assertGreaterEqual(len(hist), 100)
        self.assertTrue(all(e["source"].get("ref") for e in hist))
        self.assertTrue(all(e["source"].get("source_verified") is False for e in hist))  # fonte primária a anexar: nunca finge verificação

    def test_same_game_same_day_is_reproducible_but_games_differ(self):
        e = _historical("Rio Grande do Sul")
        a = remix(e, {"campaign_seed": 1}, "2028-03-10")
        self.assertEqual(a, remix(e, {"campaign_seed": 1}, "2028-03-10"))
        outcomes = {(remix(e, {"campaign_seed": s}, "2028-03-10")["title"]) for s in range(1, 12)}
        self.assertGreaterEqual(len(outcomes), 6)  # lugares diferentes entre partidas

    def test_real_place_never_stays_and_prepositions_agree(self):
        e = _historical("Rio Grande do Sul")
        for seed in range(1, 15):
            r = remix(e, {"campaign_seed": seed}, "2030-01-01")
            self.assertNotIn("Rio Grande do Sul", r["title"] + r["text"])
        text = remap_places("Chuvas em Minas Gerais afetam o Pará e o trabalho do governo de Goiás.", {"campaign_seed": 3}, "k", {})
        self.assertNotIn("Minas Gerais", text)
        self.assertNotIn("Goiás", text)

    def test_cities_and_years_are_removed(self):
        text = remap_places("Em 2021 faltou oxigênio em hospitais de Manaus e em Brumadinho.", {"campaign_seed": 1}, "k", {})
        self.assertNotIn("Manaus", text)
        self.assertNotIn("Brumadinho", text)
        self.assertNotIn("2021", text)

    def test_intensity_scales_effects_within_limits(self):
        scaled = scale_effects({"approval": 4.0, "gdp_growth": 0.5, "pp:reputation": 10.0}, 1.5)
        self.assertEqual(scaled["approval"], 6.0)           # limite do esquema
        self.assertLessEqual(scaled["gdp_growth"], 0.6)
        self.assertLessEqual(scaled["pp:reputation"], 12.0)

    def test_fired_event_carries_remix_and_resolution_uses_it(self):
        state = refresh_calendar_fields(new_game())
        day = date.fromisoformat(state["date"])
        def_id = _historical("Rio Grande do Sul")["id"]
        ev = story._fire(state, def_id, day)
        self.assertTrue(ev["inspired_by_real_event"])
        self.assertNotIn("Rio Grande do Sul", ev["title"])
        self.assertIn("places", ev["remix"])
        entry = story.respond(state, ev["id"], "agir")
        self.assertTrue(entry["inspired_by_real_event"])
        self.assertIn(entry["intensity"], {"leve", "média", "grave"})
        self.assertNotIn("Rio Grande do Sul", entry["outcome"])

    def test_not_tied_to_the_real_era(self):
        """Nenhum evento histórico depende de data: só de condições do estado, de ritmo e de sorteio."""
        for e in get_library().events.values():
            if is_historical(e):
                self.assertFalse(e.get("conditions"))
                self.assertNotIn("date", e)


if __name__ == "__main__":
    unittest.main()
