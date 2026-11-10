"""Equilíbrio dos acontecimentos: decidir bem tem que compensar, e ignorar tem que custar."""
from __future__ import annotations

import os
import tempfile
import unittest

from fastapi.testclient import TestClient

SPEECH = ("Assumo com responsabilidade fiscal, diálogo com o Congresso e metas públicas verificáveis em educação, "
          "saúde e emprego, prestando contas todo mês ao país.")


def _play(policy: str, months: int = 24) -> float:
    from app.engine.story_catalog import EVENTS
    tmp = tempfile.mkdtemp()
    old = os.environ.get("DATABASE_PATH")
    os.environ["DATABASE_PATH"] = os.path.join(tmp, "g.sqlite3")
    try:
        from app.main import app

        def score(ch):
            e = ch.get("effects", {})
            return e.get("approval", 0) + 0.5 * e.get("integrity", 0) + 0.3 * e.get("congress_support", 0) - 0.5 * ch.get("cost_bi", 0)

        with TestClient(app) as client:
            client.post("/api/game/new", json={"difficulty": "normal", "character": {"name": "Teste"}, "campaign_name": "t"})
            client.post("/api/game/inaugural-address", json={"text": SPEECH})
            approval = 0.0
            for _ in range(months):
                if policy != "ignorar":
                    for ev in client.get("/api/story").json()["pending"][:2]:
                        choices = EVENTS[ev["def"]]["choices"]
                        pick = max(choices, key=score) if policy == "melhor" else min(choices, key=score)
                        client.post(f"/api/story/{ev['id']}/respond", json={"choice": pick["id"]})
                state = client.post("/api/game/advance", json={"days": 30}).json()["state"]
                approval = state["metrics"]["approval"]
            return approval
    finally:
        if old is None:
            os.environ.pop("DATABASE_PATH", None)
        else:
            os.environ["DATABASE_PATH"] = old


class StoryBalanceTests(unittest.TestCase):
    def test_deciding_well_beats_ignoring_and_deciding_badly(self):
        best, worst, ignored = _play("melhor"), _play("pior"), _play("ignorar")
        self.assertGreater(best, worst + 4)      # decidir bem compensa
        self.assertGreater(best, ignored)        # ignorar custa
        self.assertGreater(best, 45)             # jogar bem não derruba a aprovação ao longo de 2 anos


if __name__ == "__main__":
    unittest.main()
