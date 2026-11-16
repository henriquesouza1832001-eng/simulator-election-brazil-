import unittest
from datetime import date

from app.engine import crises_local, story
from app.engine.event_library import get_library
from app.engine.event_remix import remix
from app.engine.state import new_game


def governing(office: str, uf: str, municipality: str | None = None) -> dict:
    state = new_game()
    state["career"] = {"mode": True, "phase": "office", "office": office, "state_code": uf, "municipality": municipality}
    return state


def definition(event_id: str) -> dict:
    return get_library().get(event_id)


class CrisesLocaisTests(unittest.TestCase):
    def test_barragem_so_acontece_onde_ha_mineracao(self):
        barragem = definition("crise:barragem_alerta")
        today = date(2028, 5, 10)
        self.assertTrue(crises_local.allowed(barragem, governing("governador", "MG"), today))
        self.assertFalse(crises_local.allowed(barragem, governing("governador", "AC"), today))
        self.assertTrue(crises_local.allowed(barragem, new_game(), today))  # Presidência: em algum estado exposto

    def test_deslizamento_e_coisa_de_verao_nas_encostas(self):
        d = definition("crise:deslizamento")
        self.assertTrue(crises_local.allowed(d, governing("governador", "RJ"), date(2028, 1, 15)))
        self.assertFalse(crises_local.allowed(d, governing("governador", "RJ"), date(2028, 7, 15)))
        self.assertFalse(crises_local.allowed(d, governing("governador", "RS"), date(2028, 1, 15)))

    def test_enchente_do_corpus_respeita_o_sul_e_a_estacao(self):
        item = next(e for e in get_library().events.values() if "Enchentes históricas" in e["title"])
        self.assertTrue(crises_local.allowed(item, governing("prefeito", "RS", "Porto Alegre"), date(2028, 10, 5)))
        self.assertFalse(crises_local.allowed(item, governing("prefeito", "RS", "Porto Alegre"), date(2028, 7, 5)))
        self.assertFalse(crises_local.allowed(item, governing("prefeito", "AM", "Manaus"), date(2028, 10, 5)))

    def test_na_presidencia_o_lugar_fica_entre_os_estados_expostos(self):
        d = definition("crise:seca_semiarido")
        expostos = set(d["where"]["states"])
        state = new_game()
        for dia in range(1, 28):
            self.assertIn(crises_local.place_for(d, state, date(2028, 9, dia))["uf"], expostos)

    def test_texto_usa_o_municipio_de_quem_governa(self):
        d = definition("crise:deslizamento")
        prefeito = crises_local.fill(d["text"], d, governing("prefeito", "RJ", "Petrópolis"), date(2028, 2, 1))
        self.assertIn("em Petrópolis", prefeito)
        governador = crises_local.fill(d["title"], d, governing("governador", "RJ"), date(2028, 2, 1))
        self.assertIn("no Rio de Janeiro", governador)
        self.assertNotIn("{", prefeito + governador)

    def test_remix_de_fato_historico_prefere_os_estados_expostos(self):
        item = next(e for e in get_library().events.values() if "Rompimento de barragem de rejeitos em Minas Gerais" in e["title"])
        state = governing("governador", "PA")
        prefer = crises_local.preferred_places(item, state)
        self.assertEqual(prefer, ["Pará"])
        result = remix(item, state, "2028-05-10", prefer)
        self.assertEqual(set(result["places"].values()), {"Pará"})

    def test_elegibilidade_do_motor_filtra_por_lugar(self):
        day = date(2028, 1, 20)
        rj = {d for d, _ in story._eligible(governing("governador", "RJ"), day)}
        am = {d for d, _ in story._eligible(governing("governador", "AM"), day)}
        self.assertIn("crise:deslizamento", rj)
        self.assertNotIn("crise:deslizamento", am)
        # consequências encadeadas (peso 0) nunca entram sozinhas
        self.assertNotIn("crise:deslizamento_resgate_apos", rj)

    def test_encadeamento_da_barragem_ignorada_pune(self):
        d = definition("crise:barragem_agrava")
        esperar = next(c for c in d["choices"] if c["id"] == "esperar_mais")
        evacuar = next(c for c in d["choices"] if c["id"] == "evacuar_agora")
        self.assertLess(esperar["effects"]["approval"], evacuar["effects"]["approval"])
        self.assertLess(esperar["effects"]["integrity"], 0)
        minimizar = next(c for c in definition("crise:barragem_alerta")["choices"] if c["id"] == "minimizar")
        self.assertIn("crise:barragem_agrava", [f[0] for f in minimizar["follow"]])


if __name__ == "__main__":
    unittest.main()
