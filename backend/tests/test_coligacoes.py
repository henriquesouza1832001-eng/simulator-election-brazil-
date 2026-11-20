import unittest

from app.engine import coalition, tv_time
from app.engine.career import _projected_public_poll_support, career_overview, start_career
from app.engine.state import new_game, refresh_calendar_fields


def partida(office="governador", party="PSB", ideology="Centro-esquerda", seed=3):
    state = refresh_calendar_fields(new_game())
    state.pop("setup_pending", None)
    start_career(state, office, "MG", "", party, ideology, "Teste", character={"name": "Teste", "political_spectrum": "centro_esquerda", "family_background": "classe_media", "traits": []})
    career = state["career"]
    career["seed"] = seed
    return state, career


def convidar_ate_aceitar(state, career, party, offer="vice"):
    suporte = _projected_public_poll_support(state, career)
    for _ in range(60):   # cada nova proposta é um novo sorteio determinístico
        r = coalition.invite(state, career, party, offer, suporte)
        if r["accepted"]:
            return r
    raise AssertionError("ninguém aceitou em 60 tentativas")


class TempoDeTVTests(unittest.TestCase):
    def test_coligacao_soma_o_tempo_de_tv_dos_partidos(self):
        sozinho = tv_time.share("PSB")
        chapa = tv_time.share("PSB", ["PSD", "MDB"])
        self.assertGreater(chapa["share_pct"], sozinho["share_pct"] * 1.4)
        self.assertEqual(chapa["coalition"], ["PSB", "PSD", "MDB"])
        self.assertLessEqual(chapa["share_pct"], 70.0)

    def test_sem_coligacao_mantem_o_comportamento_antigo(self):
        self.assertEqual(tv_time.share("PSB"), tv_time.share("PSB", []))


class ColigacoesTests(unittest.TestCase):
    def test_so_majoritaria_e_antes_do_fim_da_campanha(self):
        state, career = partida("deputado_estadual", "PSB", "Centro-esquerda")
        self.assertFalse(coalition.eligible(career))
        with self.assertRaises(ValueError):
            coalition.invite(state, career, "PSD", "programa", 30.0)

    def test_aceitar_soma_tv_e_votos_e_tira_o_candidato_proprio_do_aliado(self):
        state, career = partida()
        antes = _projected_public_poll_support(state, career)
        tv0 = tv_time.share(career["party"])["share_pct"]
        r = convidar_ate_aceitar(state, career, "PSD", "vice")
        self.assertTrue(r["accepted"])
        self.assertGreater(_projected_public_poll_support(state, career), antes - 0.01)
        self.assertGreater(tv_time.share(career["party"], coalition.partner_parties(career))["share_pct"], tv0)
        ov = career_overview(state)
        self.assertNotIn("PSD", {x["party"] for x in ov["rivals"]})            # o aliado não disputa mais
        self.assertEqual(ov["coalition"]["partners"][0]["party"], "PSD")
        self.assertEqual(ov["tv"]["coalition"], ["PSB", "PSD"])

    def test_vice_so_para_um_partido_e_limite_de_parceiros(self):
        state, career = partida()
        convidar_ate_aceitar(state, career, "PSD", "vice")
        with self.assertRaises(PermissionError):
            coalition.invite(state, career, "MDB", "vice", 30.0)
        convidar_ate_aceitar(state, career, "MDB", "programa")
        convidar_ate_aceitar(state, career, "PP", "secretarias")
        with self.assertRaises(PermissionError):
            coalition.invite(state, career, "PDT", "programa", 30.0)

    def test_distancia_ideologica_reduz_a_chance_e_custa_reputacao(self):
        state, career = partida()
        perto = coalition.acceptance(career, "PDT", "secretarias", 30.0)
        longe = coalition.acceptance(career, "PL", "secretarias", 30.0)
        self.assertGreater(perto, longe)
        rep = float(career.get("reputation", 50))
        convidar_ate_aceitar(state, career, "PL", "programa")
        self.assertLess(float(career["reputation"]), rep)

    def test_compromissos_ficam_registrados(self):
        state, career = partida()
        convidar_ate_aceitar(state, career, "PSD", "secretarias")
        self.assertEqual(career["coalition"]["obligations"][0]["status"], "pendente")


if __name__ == "__main__":
    unittest.main()
