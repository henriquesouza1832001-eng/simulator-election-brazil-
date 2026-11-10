"""Biblioteca de acontecimentos em escala e gerador (Gemini/local) com validação e revisão."""
from __future__ import annotations

import asyncio
import json
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest import mock

from app.ai import event_generator as gen
from app.engine import event_library as lib_mod
from app.engine import event_schema as schema
from app.engine.event_library import build_library, get_library
from app.engine.state import new_game, refresh_calendar_fields


class LibraryScaleTests(unittest.TestCase):
    def test_library_has_thousands_of_valid_events_and_chains(self):
        stats = build_library().stats()
        self.assertGreaterEqual(stats["total"], 2000)
        self.assertEqual(stats["report"]["invalid"], 0, stats["report"]["invalid_examples"])
        self.assertEqual(stats["report"]["dropped_follow"], 0)
        self.assertGreaterEqual(stats["chained_events"], 200)
        self.assertGreaterEqual(stats["families"], 15)

    def test_every_chain_target_exists_and_ids_are_unique(self):
        library = get_library()
        ids = set(library.events)
        for ev in library.events.values():
            for choice in ev["choices"]:
                for target, days in choice.get("follow", []):
                    self.assertIn(target, ids, ev["id"])
                    self.assertGreater(days, 0)

    def test_chain_only_events_never_fire_alone(self):
        from app.engine.story import _eligible
        state = refresh_calendar_fields(new_game())
        eligible = {d for d, _ in _eligible(state, date.fromisoformat(state["date"]))}
        chained_only = {i for i, e in get_library().events.items() if e.get("weight", 1.0) <= 0}
        self.assertTrue(chained_only)
        self.assertFalse(eligible & chained_only)

    def test_family_cooldown_is_respected_over_a_term(self):
        from app.engine import story
        state = refresh_calendar_fields(new_game())
        start = date.fromisoformat(state["date"])
        fired: list[tuple[str, date]] = []
        original = story._fire

        def spy(st, def_id, day):
            fired.append((def_id, day))
            return original(st, def_id, day)

        with mock.patch.object(story, "_fire", spy):
            for step in range(48):
                before = start + timedelta(days=30 * step)
                story.tick(state, before, before + timedelta(days=30))
        self.assertGreater(len(fired), 10)
        last_by_family: dict[str, date] = {}
        for def_id, day in fired:
            definition = get_library().get(def_id)
            if definition.get("weight", 1.0) <= 0 or definition["family"] == "base":
                continue  # continuações encadeadas e catálogo inicial não passam pelo filtro de família
            fam = definition["family"]
            if fam in last_by_family:
                self.assertGreaterEqual((day - last_by_family[fam]).days, story.FAMILY_COOLDOWN_DAYS, fam)
            last_by_family[fam] = day

    def test_a_term_produces_varied_events(self):
        from app.engine import story
        state = refresh_calendar_fields(new_game())
        start = date.fromisoformat(state["date"])
        for step in range(46):
            before = start + timedelta(days=30 * step)
            story.tick(state, before, before + timedelta(days=30))
            for ev in list(state["story"]["pending"]):
                story.respond(state, ev["id"], ev["choices"][0]["id"])
        seen = {h["def"] for h in state["story"]["history"]}
        families = {get_library().get(d)["family"] for d in seen}
        self.assertGreaterEqual(len(families), 8)  # variedade de assuntos, não só repetições


class SchemaTests(unittest.TestCase):
    def _valid(self):
        return {"id": "t:1", "kind": "decisao", "title": "Um título de teste válido", "levels": ["federal"], "tags": ["x"],
                "text": "Um texto de teste com tamanho suficiente para passar na validação do esquema do jogo.",
                "choices": [{"id": "a", "label": "A", "outcome": "ok", "effects": {"approval": 1.0}},
                            {"id": "b", "label": "B", "outcome": "ok", "effects": {"approval": -1.0}}],
                "source": {"type": "modelo"}}

    def test_valid_and_limits(self):
        self.assertEqual(schema.validate_event(self._valid()), [])
        bad = self._valid(); bad["choices"][0]["effects"] = {"approval": 50}
        self.assertTrue(any("limite" in p for p in schema.validate_event(bad)))
        bad = self._valid(); bad["choices"][0]["effects"] = {"dinheiro_infinito": 1}
        self.assertTrue(any("desconhecido" in p for p in schema.validate_event(bad)))
        bad = self._valid(); bad["choices"] = bad["choices"][:1]
        self.assertTrue(schema.validate_event(bad))

    def test_declarative_conditions(self):
        pred = schema.compile_conditions([{"metric": "inflation", "op": ">", "value": 5}])
        self.assertFalse(pred({"metrics": {"inflation": 4}}))
        self.assertTrue(pred({"metrics": {"inflation": 6}}))
        self.assertFalse(schema.compile_conditions([{"metric": "x", "op": "??", "value": 1}])({"metrics": {"x": 1}}))  # inválida nunca dispara


class GeneratorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.patches = [mock.patch.object(gen, "GENERATED_DIR", self.dir / "generated"), mock.patch.object(lib_mod, "EVENTS_DIR", self.dir)]
        for p in self.patches:
            p.start()
        lib_mod._real_names = {"FULANO DE TAL"}
        self.corpus = self.dir / "fatos.jsonl"
        self.corpus.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in [
            {"id": "f1", "date": "2023-05-01", "title": "Greve em refinarias", "summary": "Paralisação afeta o abastecimento.", "area": "trabalho", "source_url": "https://exemplo.gov.br/f1"},
            {"id": "f2", "date": "2022-03-01", "title": "Cheias no litoral", "summary": "Chuvas fortes alagam cidades.", "area": "clima", "source_name": "Defesa Civil"},
            {"id": "f3", "title": "Sem fonte", "summary": "Linha sem fonte é ignorada."}]), encoding="utf-8")

    def tearDown(self):
        for p in self.patches:
            p.stop()
        lib_mod._real_names = None
        lib_mod._cache = None
        self.tmp.cleanup()

    def _mock_caller(self):
        good = {"corpus_id": "f1", "kind": "decisao", "level": "federal", "tags": ["trabalho"], "title": "Paralisação afeta o abastecimento de combustíveis",
                "text": "Uma categoria fictícia de trabalhadores paralisa refinarias fictícias e o abastecimento fica ameaçado em várias cidades do país.",
                "choices": [{"id": "negociar", "label": "Abrir negociação", "tone": "dialogo", "cost_bi": 1.0, "effects": {"approval": 1.0}, "outcome": "A mesa encerra a paralisação."},
                            {"id": "ignorar", "label": "Esperar", "tone": "passiva", "effects": {"approval": -2.0}, "outcome": "A crise se arrasta."}]}
        real = {**good, "corpus_id": "f2", "title": "Fulano de Tal critica o governo em evento", "text": good["text"].replace("Uma categoria", "Fulano de Tal, que lidera uma categoria,")}
        extreme = {**good, "corpus_id": "f1", "title": "Efeito exagerado para testar o limite do esquema", "choices": [
            {"id": "a", "label": "A", "outcome": "x", "effects": {"approval": 99}}, {"id": "b", "label": "B", "outcome": "y", "effects": {}}]}

        async def caller(model, batch):
            return [good, real, extreme]
        return caller

    def test_pipeline_rejects_real_names_and_extreme_effects_and_requires_review(self):
        report = asyncio.run(gen.generate(self.corpus, 10, use_gemini=False, caller=self._mock_caller()))
        self.assertEqual(report["corpus_items"], 2)           # linha sem fonte ignorada
        self.assertEqual(report["accepted_pending_review"], 1)
        self.assertEqual(report["rejected"], 2)
        reasons = " ".join(" ".join(r["problems"]) for r in report["rejected_examples"])
        self.assertIn("pessoa real", reasons)
        self.assertIn("limite", reasons)
        data = json.loads(Path(report["file"]).read_text(encoding="utf-8"))
        self.assertEqual(data["events"][0]["review"], "pendente")
        # pendente não entra no jogo
        self.assertFalse(any(e.startswith(("gemini:", "local:")) for e in build_library().events))
        # revisão humana explícita libera
        self.assertEqual(gen.approve(Path(report["file"]))["approved"], 1)
        self.assertTrue(any(e.startswith(("gemini:", "local:")) for e in build_library().events))

    def test_local_fallback_works_without_api_key(self):
        with mock.patch.dict("os.environ", {"GEMINI_API_KEY": ""}):
            report = asyncio.run(gen.generate(self.corpus, 10, use_gemini=True))
        self.assertEqual(report["mode"], "local")
        self.assertEqual(report["accepted_pending_review"], 2)
        ev = json.loads(Path(report["file"]).read_text(encoding="utf-8"))["events"][0]
        self.assertEqual(ev["source"]["type"], "historico_inspirado")
        self.assertTrue(ev["source"]["ref"])

    def test_guard_blocks_real_names_in_json_files_even_if_approved(self):
        bad = {"id": "manual:x", "kind": "decisao", "tags": ["x"], "levels": ["federal"], "title": "Fulano de Tal faz um discurso polêmico",
               "text": "Fulano de Tal faz um discurso que gera forte reação nas redes e entre aliados do governo fictício.",
               "choices": [{"id": "a", "label": "A", "outcome": "x", "effects": {}}, {"id": "b", "label": "B", "outcome": "y", "effects": {}}],
               "source": {"type": "manual"}, "review": "aprovado"}
        (self.dir / "manual.json").write_text(json.dumps({"events": [bad]}), encoding="utf-8")
        library = build_library()
        self.assertNotIn("manual:x", library.events)
        self.assertEqual(library.report["rejected_real_person"], 1)


if __name__ == "__main__":
    unittest.main()
