import os
import tempfile
import unittest
from datetime import date

from fastapi.testclient import TestClient

from app.engine import campaign_events, electoral_field


def carreira(office="governador", party="PT", ideology="Esquerda"):
    return {"office": office, "state_code": "MG", "party": party, "ideology": ideology, "seed": 11, "phase": "campaign", "momentum": 0.0}


class InstitutosTests(unittest.TestCase):
    def test_institutos_se_revezam_sempre_na_mesma_ordem(self):
        nomes = [campaign_events.institute_for(i)["name"] for i in range(6)]
        self.assertEqual(nomes[:3], nomes[3:])
        self.assertEqual(len(set(nomes[:3])), 3)

    def test_vies_favorece_quem_esta_do_lado_do_instituto(self):
        vox = next(i for i in campaign_events.INSTITUTES if i["id"] == "vox")           # tende à esquerda
        esquerda = campaign_events.house_effect(vox, -1.0)
        direita = campaign_events.house_effect(vox, 1.0)
        self.assertGreater(esquerda, 0)
        self.assertLess(direita, 0)
        self.assertEqual(campaign_events.house_effect(campaign_events.INSTITUTES[0], 1.0), 0.0)   # instituto neutro não enviesa
        self.assertLessEqual(abs(esquerda), campaign_events.HOUSE_EFFECT_PP)


class MovimentosDosRivaisTests(unittest.TestCase):
    def avancar(self, career, dias=120):
        state = {"date": "2026-08-01"}
        inicio = date(2026, 8, 1)
        mensagens = []
        for d in range(dias):
            antes = date.fromordinal(inicio.toordinal() + d)
            depois = date.fromordinal(antes.toordinal() + 1)
            mensagens += campaign_events.tick_rivals(state, career, antes, depois)
        return mensagens

    def test_rivais_se_movem_ao_longo_da_campanha_e_tudo_fica_registrado(self):
        career = carreira()
        electoral_field.ensure_field(career)
        mensagens = self.avancar(career)
        self.assertGreaterEqual(len(mensagens), 5)
        eventos = career["rival_events"]
        self.assertLessEqual(len(eventos), campaign_events.MAX_EVENTS_KEPT)
        self.assertTrue({e["party"] for e in eventos} <= {r["party"] for r in career["opponents"]})

    def test_avancar_dia_a_dia_ou_de_uma_vez_da_o_mesmo_resultado(self):
        a, b = carreira(), carreira()
        electoral_field.ensure_field(a)
        electoral_field.ensure_field(b)
        self.avancar(a, 60)
        state = {"date": "2026-08-01"}
        campaign_events.tick_rivals(state, b, date(2026, 8, 1), date(2026, 9, 30))
        self.assertEqual([e["text"] for e in a["rival_events"]], [e["text"] for e in b["rival_events"]])

    def test_efeitos_tem_teto(self):
        career = carreira()
        rivais = electoral_field.ensure_field(career)
        base = {r["id"]: r["support_weight"] for r in rivais}
        self.avancar(career, 400)
        for r in career["opponents"]:
            self.assertLessEqual(r["support_weight"], base[r["id"]] * 1.4 + 0.01)
        self.assertGreaterEqual(career["momentum"], -10.0)

    def test_nao_age_fora_de_eleicao_majoritaria_nem_fora_da_campanha(self):
        proporcional = carreira("vereador", "MDB", "Centro")
        self.assertEqual(self.avancar(proporcional, 60), [])
        pre = carreira()
        pre["phase"] = "pre_campaign"
        self.assertEqual(self.avancar(pre, 60), [])


class PesquisaComInstitutoTests(unittest.TestCase):
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

    def test_pesquisas_da_campanha_trazem_instituto_e_movimentos_aparecem_no_painel(self):
        body = {"office": "governador", "state_code": "MG", "party": "PSB", "ideology": "Centro-esquerda", "candidate_name": "Teste",
                "character": {"name": "Teste"}, "difficulty": "normal"}
        started = self.c.post("/api/career/start", json=body).json()
        self.c.headers["X-Mandato-Campaign"] = (started.get("state") or started)["campaign_id"]
        state = started.get("state") or started
        for _ in range(110):
            state = self.c.post("/api/game/advance", json={"days": 30}).json()["state"]
            ov = state["career_overview"]
            if ov["phase"] == "campaign" and len(ov["public_polls"]) >= 2:
                break
        ov = state["career_overview"]
        self.assertEqual(ov["phase"], "campaign")
        institutos = {p["institute"] for p in ov["public_polls"]}
        self.assertGreaterEqual(len(institutos), 2)
        self.assertTrue(all("margin_of_error" in p for p in ov["public_polls"]))
        self.assertIn("rival_events", ov)


if __name__ == "__main__":
    unittest.main()
