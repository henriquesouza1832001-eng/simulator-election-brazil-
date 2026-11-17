import asyncio
import os
import tempfile
import unittest
from unittest import mock

from fastapi.testclient import TestClient

from app.engine import electoral_field as field
from app.engine import elector, speech_score

ISSUES = {"economia": {"label": "Economia", "terms": {"emprego", "renda", "preço", "preco"}, "groups": ["trabalhadores", "pequenos_negocios"]},
          "saude": {"label": "Saúde", "terms": {"saúde", "saude", "hospital", "posto"}, "groups": ["familias", "servidores"]},
          "educacao": {"label": "Educação", "terms": {"escola", "creche", "professor"}, "groups": ["familias", "juventude"]}}


def prefeito(party="MDB", seed=7):
    return {"office": "prefeito", "state_code": "SP", "municipality": "São Paulo", "municipality_id": "3550308", "party": party, "ideology": "Centro", "seed": seed}


class CampoDeCandidatosTests(unittest.TestCase):
    def test_nunca_ha_rival_do_mesmo_partido_do_jogador(self):
        for party in ("MDB", "PSOL", "PT", "PL"):
            rivals = field.ensure_field(prefeito(party))
            self.assertGreaterEqual(len(rivals), 3)
            self.assertNotIn(party, {r["party"] for r in rivals})

    def test_soma_das_intencoes_fecha_em_100_para_qualquer_apoio_do_jogador(self):
        career = prefeito()
        for p in (3, 12, 28.4, 47, 80):
            total = p + sum(r["support"] for r in field.shares(career, p))
            self.assertAlmostEqual(total, 100.0, delta=0.15)

    def test_quando_o_jogador_sobe_perde_mais_o_rival_mais_proximo(self):
        career = {"office": "governador", "state_code": "MG", "party": "PT", "ideology": "Esquerda", "seed": 3}
        rivals = field.ensure_field(career)
        before = {r["id"]: r["support"] for r in field.shares(career, career["field_baseline"])}
        after = {r["id"]: r["support"] for r in field.shares(career, career["field_baseline"] + 20)}
        perdas = {i: (before[i] - after[i]) / before[i] for i in before}
        proximo = max(rivals, key=lambda r: r["proximity"])["id"]
        distante = min(rivals, key=lambda r: r["proximity"])["id"]
        self.assertGreater(perdas[proximo], perdas[distante])

    def test_ataque_que_pega_enfraquece_o_rival_e_reacao_contraria_fortalece(self):
        career = prefeito()
        rid = field.ensure_field(career)[0]["id"]
        antes = next(r["support"] for r in field.shares(career, 30) if r["id"] == rid)
        field.apply_pressure(career, rid, 2.0)
        depois = next(r["support"] for r in field.shares(career, 30) if r["id"] == rid)
        self.assertLess(depois, antes)
        field.apply_pressure(career, rid, -4.0)
        reacao = next(r["support"] for r in field.shares(career, 30) if r["id"] == rid)
        self.assertGreater(reacao, antes)

    def test_cargo_proporcional_nao_usa_o_campo_majoritario(self):
        self.assertIsNone(field.real_party_shares({"office": "vereador", "party": "MDB"}))

    @unittest.skipUnless(elector.votes_available(2024), "votos do TSE de 2024 não importados neste banco")
    def test_com_dados_do_tse_os_rivais_sao_os_partidos_que_disputaram(self):
        career = prefeito("MDB")
        rivals = field.ensure_field(career)
        self.assertEqual(career["field_reference_year"], 2024)
        self.assertIn("PSOL", {r["party"] for r in rivals})   # segundo colocado em São Paulo em 2024
        self.assertNotIn("MDB", {r["party"] for r in rivals})
        self.assertAlmostEqual(career["field_baseline"], 29.49, delta=0.1)   # força real do MDB na cidade


class NotaDoDiscursoTests(unittest.TestCase):
    def leitura(self, **kw):
        base = {"source": "gemini", "themes": ["educacao"], "tone": "propositivo", "promises": [], "attacks": [], "legal_risk": "nenhum", "clarity": 0.8, "local_connection": 0.5}
        return {**base, **kw}

    def promessa(self, **kw):
        return {"text": "Vou ampliar creches", "measurable": True, "has_deadline": True, "funding_stated": True, "within_competence": True, "realistic": True, **kw}

    def test_proposta_concreta_vale_mais_que_promessa_vaga(self):
        concreta, _ = speech_score.score_reading(self.leitura(promises=[self.promessa()]), "educacao")
        vaga, _ = speech_score.score_reading(self.leitura(promises=[self.promessa(measurable=False, has_deadline=False, funding_stated=False)]), "educacao")
        self.assertGreater(concreta, vaga + 8)

    def test_fora_do_tema_escolhido_perde_pontos_de_pertinencia(self):
        dentro, _ = speech_score.score_reading(self.leitura(themes=["educacao"]), "educacao")
        fora, rubrica = speech_score.score_reading(self.leitura(themes=["saude"]), "educacao")
        self.assertGreater(dentro, fora)
        self.assertEqual(rubrica["pertinência do tema"], 4)

    def test_ataque_pessoal_e_tom_agressivo_derrubam_a_nota(self):
        limpo, _ = speech_score.score_reading(self.leitura(), "educacao")
        agressivo, rubrica = speech_score.score_reading(self.leitura(tone="ataque", attacks=[{"target": "adversario", "personal": True}]), "educacao")
        self.assertLess(agressivo, limpo - 15)
        self.assertEqual(rubrica["ataque pessoal"], -12)

    def test_promessa_fora_da_competencia_e_irrealista_pesa_mas_tem_teto(self):
        ruins = [self.promessa(within_competence=False, realistic=False) for _ in range(4)]
        _, rubrica = speech_score.score_reading(self.leitura(promises=ruins, legal_risk="discurso_de_odio"), "educacao")
        self.assertEqual(rubrica["promessa fora do alcance"], -speech_score.MODEL_JUDGEMENT_CAP)

    def test_normalizacao_descarta_valores_fora_das_faixas(self):
        lixo = {"themes": ["inexistente", "saude"], "tone": "gritaria", "legal_risk": "crime_hediondo", "clarity": 9, "promises": [{"text": "x" * 500}, "nao-objeto"],
                "attacks": [{"target": "alvo_invalido", "personal": 1}]}
        lido = speech_score.normalize(lixo, "texto", "economia", ISSUES, ["opponent-1"])
        self.assertEqual(lido["themes"], ["saude"])
        self.assertEqual((lido["tone"], lido["legal_risk"], lido["clarity"]), ("propositivo", "nenhum", 1.0))
        self.assertEqual(len(lido["promises"][0]["text"]), 140)
        self.assertEqual(lido["attacks"], [{"target": "adversario", "personal": True}])

    def test_leitura_local_acha_promessa_numero_prazo_e_ataque(self):
        texto = "Vou construir 20 creches em 12 meses com recurso do orçamento. O adversário é um vagabundo."
        lido = speech_score.local_reading(texto, "educacao", {}, ISSUES)
        self.assertEqual(lido["source"], "local")
        p = lido["promises"][0]
        self.assertTrue(p["measurable"] and p["has_deadline"] and p["funding_stated"])
        self.assertEqual(lido["tone"], "ataque")
        self.assertTrue(lido["attacks"][0]["personal"])


class LeituraPeloGeminiTests(unittest.TestCase):
    def setUp(self):
        from app.ai import speech_reader
        self.reader = speech_reader
        self.rivals = [{"id": "opponent-1", "party": "PT", "issue_focus": "economia"}]

    def run_read(self):
        return asyncio.run(self.reader.read("Vou ampliar creches com prazo de 12 meses e orçamento previsto.", "educacao", {"office": "prefeito"}, ISSUES, self.rivals))

    def test_sem_chave_usa_a_leitura_local(self):
        with mock.patch.dict(os.environ, {"GEMINI_API_KEY": ""}):
            self.assertEqual(self.run_read()["source"], "local")

    def test_recurso_desligado_usa_a_leitura_local_mesmo_com_chave(self):
        with mock.patch.dict(os.environ, {"GEMINI_API_KEY": "chave-de-teste", "GEMINI_RECURSOS": "narrar"}):
            self.assertEqual(self.run_read()["source"], "local")

    def test_resposta_valida_do_gemini_vira_leitura_normalizada(self):
        corpo = ('{"summary":"Creches com prazo","themes":["educacao"],"tone":"tecnico","promises":[{"text":"ampliar creches","measurable":true,'
                 '"has_deadline":true,"funding_stated":true,"within_competence":true,"realistic":true}],"attacks":[],"legal_risk":"nenhum","clarity":0.9,"local_connection":0.6}')
        resposta = mock.Mock(is_error=False)
        resposta.json.return_value = {"candidates": [{"content": {"parts": [{"text": corpo}]}}]}
        cliente = mock.AsyncMock()
        cliente.__aenter__.return_value.post = mock.AsyncMock(return_value=resposta)
        with mock.patch.dict(os.environ, {"GEMINI_API_KEY": "chave-de-teste", "GEMINI_RECURSOS": "interpretar"}), mock.patch("httpx.AsyncClient", return_value=cliente):
            lido = self.run_read()
        self.assertEqual((lido["source"], lido["tone"]), ("gemini", "tecnico"))
        self.assertTrue(lido["promises"][0]["measurable"])

    def test_erro_do_gemini_cai_na_leitura_local(self):
        resposta = mock.Mock(is_error=True, status_code=429)
        cliente = mock.AsyncMock()
        cliente.__aenter__.return_value.post = mock.AsyncMock(return_value=resposta)
        with mock.patch.dict(os.environ, {"GEMINI_API_KEY": "chave-de-teste", "GEMINI_RECURSOS": "interpretar"}), mock.patch("httpx.AsyncClient", return_value=cliente):
            self.assertEqual(self.run_read()["source"], "local")


class AcaoDeCampanhaComLeituraTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.old = os.environ.get("DATABASE_PATH")
        os.environ["DATABASE_PATH"] = os.path.join(self.tmp.name, "g.sqlite3")
        from app.main import app
        self.ctx = TestClient(app)
        self.c = self.ctx.__enter__()

    def tearDown(self):
        self.ctx.__exit__(None, None, None)
        if self.old is None:
            os.environ.pop("DATABASE_PATH", None)
        else:
            os.environ["DATABASE_PATH"] = self.old
        self.tmp.cleanup()

    def test_acao_registra_leitura_e_usa_a_nota_do_motor(self):
        body = {"office": "prefeito", "state_code": "SP", "municipality": "São Paulo", "municipality_id": "3550308", "party": "MDB", "ideology": "Centro",
                "candidate_name": "Teste", "character": {"name": "Teste"}, "difficulty": "normal"}
        started = self.c.post("/api/career/start", json=body).json()
        self.c.headers["X-Mandato-Campaign"] = (started.get("state") or started)["campaign_id"]
        for _ in range(40):
            state = self.c.post("/api/game/advance", json={"days": 30}).json()["state"]
            if state["career_overview"]["phase"] == "campaign":
                break
        self.assertEqual(state["career_overview"]["phase"], "campaign")
        rival = state["career_overview"]["opponents"][0]
        self.assertNotEqual(rival["party"], "MDB")
        leitura = {"source": "gemini", "summary": "Creches", "themes": ["educacao"], "target_groups": ["familias"], "tone": "tecnico",
                   "promises": [{"text": "ampliar creches", "measurable": True, "has_deadline": True, "funding_stated": True, "within_competence": True, "realistic": True}],
                   "attacks": [{"target": rival["id"], "personal": False}], "legal_risk": "nenhum", "clarity": 0.9, "local_connection": 0.7}
        with mock.patch("app.ai.speech_reader.read", new=mock.AsyncMock(return_value=leitura)):
            r = self.c.post("/api/career/action", json={"activity_type": "comicio", "issue": "educacao", "message": "Vou ampliar creches com prazo e orçamento definidos para as famílias."})
        self.assertEqual(r.status_code, 200, r.text)
        result = r.json()["result"]
        self.assertEqual(result["reading"]["source"], "gemini")
        self.assertEqual(result["reading"]["tone"], "técnico")
        esperado, _ = speech_score.score_reading(leitura, "educacao")
        self.assertEqual(result["score"], esperado)


if __name__ == "__main__":
    unittest.main()
