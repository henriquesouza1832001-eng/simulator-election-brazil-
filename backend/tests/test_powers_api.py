import os
import tempfile
import unittest

from fastapi.testclient import TestClient


class PowersApiTests(unittest.TestCase):
    def test_interpret_execute_regulators_and_news_endpoints(self):
        os.environ.pop("GEMINI_API_KEY", None)
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["DATABASE_PATH"] = os.path.join(tmp, "g.sqlite3")
            from app.main import app
            with TestClient(app) as client:
                catalog = client.get("/api/powers").json()
                self.assertEqual(catalog["office"], "presidente")
                self.assertTrue(all("legal" in a for a in catalog["actions"]))

                out = client.post("/api/powers/interpret", json={"text": "quero liberar o porte de arma"}).json()
                self.assertEqual(out["matches"][0]["id"], "seg_armas_afrouxar")
                self.assertEqual(out["source"], "local")

                vague = client.post("/api/powers/interpret", json={"text": "asfaltar uma rodovia"}).json()
                self.assertTrue(any("Em qual destes" in q for q in vague["questions"]))

                self.assertEqual(client.post("/api/powers/confirm?action=seg_armas_afrouxar", json={"text": "liberar o porte de arma"}).json(), {"saved": True})
                again = client.post("/api/powers/interpret", json={"text": "liberar o porte de arma agora"}).json()
                self.assertTrue(again["learned"])

                blocked = client.post("/api/powers/execute", json={"action": "seg_armas_afrouxar"})
                self.assertEqual(blocked.status_code, 409)  # pronunciamento de posse ainda não registrado
                from tests.test_api_smoke import INAUGURAL_ADDRESS
                self.assertEqual(client.post("/api/game/inaugural-address", json={"text": INAUGURAL_ADDRESS}).status_code, 200)
                done = client.post("/api/powers/execute", json={"action": "seg_armas_afrouxar"})
                self.assertEqual(done.status_code, 200, done.text)
                self.assertEqual(client.post("/api/powers/execute", json={"action": "reg_monarquia"}).status_code, 409)

                regs = client.get("/api/regulators").json()
                self.assertEqual(len(regs["regulators"]), 5)
                news = client.get("/api/consequences").json()
                self.assertTrue(news["pending"])  # processo no STF aguardando resposta
                crisis = news["pending"][0]
                reply = client.post(f"/api/consequences/{crisis['id']}/respond?option={crisis['options'][0]['id']}")
                self.assertEqual(reply.status_code, 200, reply.text)
                self.assertEqual(client.post("/api/consequences/xx/respond?option=a").status_code, 422)
                self.assertTrue(client.get("/api/ledger").json()["entries"])


if __name__ == "__main__":
    unittest.main()
