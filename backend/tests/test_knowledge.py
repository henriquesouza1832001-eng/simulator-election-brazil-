import unittest

from app import knowledge_routes
from app.engine import powers


class KnowledgeTests(unittest.TestCase):
    def test_normas_tem_campos_e_busca_valida(self):
        normas = knowledge_routes._load("normas.json")["normas"]
        self.assertGreaterEqual(len(normas), 45)
        ids = [n["id"] for n in normas]
        self.assertEqual(len(ids), len(set(ids)))
        for n in normas:
            for campo in ("citacao", "nome", "tipo", "ano", "assunto", "resumo", "busca"):
                self.assertTrue(n.get(campo), (n.get("id"), campo))
            self.assertTrue(n["busca"].startswith("https://www.lexml.gov.br/busca/"), n["id"])
            self.assertTrue(1900 <= int(n["ano"]) <= 2026, n["id"])

    def test_criterio_de_ligacao_nunca_e_um_numero_curto_solto(self):
        for n in knowledge_routes._load("normas.json")["normas"]:
            for chave in n["match"]:
                self.assertFalse(chave.isdigit(), (n["id"], chave))  # "64" casaria com qualquer art. 64

    def test_normas_se_ligam_as_acoes_que_as_citam(self):
        por_citacao = {n["citacao"]: n for n in knowledge_routes._load("normas.json")["normas"]}
        acoes = knowledge_routes.actions_citing(por_citacao["Lei 14.133/2021"])
        self.assertTrue(acoes)
        licitacao = knowledge_routes.actions_citing(por_citacao["Lei 12.528/2011"])
        self.assertIn("mem_comissao", [a["id"] for a in licitacao])

    def test_memoria_nao_cita_pessoas_reais_e_liga_a_acoes_existentes(self):
        fatos = knowledge_routes._load("memoria.json")["fatos"]
        texto = " ".join(f["titulo"] + f["resumo"] for f in fatos)
        for nome in ("Goulart", "Collor", "Sarney", "Tancredo", "Dilma", "Lula", "Bolsonaro"):
            self.assertNotIn(nome, texto)
        for f in fatos:
            for acao in f["no_jogo"]:
                if ":" in acao or acao in ("drenagem_sul",):
                    continue  # evento ou projeto
                self.assertIn(acao, powers.BY_ID, acao)
        self.assertEqual(sorted(f["ano"] for f in fatos), [f["ano"] for f in fatos])

    def test_8_de_janeiro_tem_os_tres_caminhos_ligados(self):
        fato = next(f for f in knowledge_routes._load("memoria.json")["fatos"] if f["ano"] == 2023)
        self.assertEqual(set(fato["no_jogo"]), {"jus_indulto_8jan", "jus_8jan_manter", "jus_anistia_8jan"})


if __name__ == "__main__":
    unittest.main()
