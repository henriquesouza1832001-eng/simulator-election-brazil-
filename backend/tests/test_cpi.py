import unittest
from datetime import date

from app.engine import cpi
from app.engine import consequences
from app.engine import office_powers as op
from tests.test_office_powers import career_state


def run(state, until):
    cur = date.fromisoformat(state["date"])
    step = 20
    while cur < until:
        nxt = min(until, date.fromordinal(cur.toordinal() + step))
        state["date"] = nxt.isoformat()
        cpi.tick(state, cur, nxt)
        cur = nxt


class CpiTest(unittest.TestCase):
    def test_player_cpi_runs_through_stages_and_ends(self):
        outcomes = set()
        for seed in range(1, 40):
            s = career_state("deputado_federal", capital=90)
            s["campaign_seed"] = seed
            c = cpi.open_cpi(s, subject="contratos", author="jogador", office="deputado_federal")
            self.assertEqual([x["name"] for x in c["stages"]][:3], ["Requerimento", "Instalação", "Oitiva 1"])
            run(s, date(2030, 1, 1))
            outcomes.add(c["status"])
            self.assertNotEqual(c["status"], "em andamento")
        self.assertIn("concluída", outcomes)

    def test_approved_cpi_action_opens_cpi_for_player(self):
        for seed in range(1, 80):
            s = career_state("vereador", capital=90)
            s["campaign_seed"] = seed
            op.execute(s, "v_cpi")
            op.local_tick(s, date(2029, 4, 10), date(2029, 7, 30))
            if s["local_bills"][0]["status"] == "aprovado":
                self.assertEqual(s["cpis"][0]["author"], "jogador")
                return
        self.fail("nenhuma aprovada")

    def test_opposition_cpi_hits_low_integrity_government_and_asks_for_response(self):
        opened = asked = 0
        for seed in range(1, 60):
            s = {"date": "2028-01-01", "campaign_seed": seed, "metrics": {"integrity": 25.0, "approval": 50.0, "governability": 50.0}}
            run(s, date(2029, 6, 1))
            if s.get("cpis"):
                opened += 1
                if any(c["id"].endswith("-resp") for c in consequences._book(s)["pending"]) or any("-resp" in n.get("id", "") for n in consequences._book(s)["feed"]):
                    asked += 1
        self.assertGreater(opened, 10)
        self.assertGreater(asked, 0)

    def test_clean_government_gets_no_cpi(self):
        s = {"date": "2028-01-01", "campaign_seed": 3, "metrics": {"integrity": 85.0, "approval": 50.0}}
        run(s, date(2030, 1, 1))
        self.assertFalse(s.get("cpis"))

    def test_cooperating_reduces_pressure(self):
        s = {"date": "2028-01-01", "campaign_seed": 3, "metrics": {"integrity": 40.0}}
        c = cpi.open_cpi(s, subject="obras", author="oposicao")
        cpi.apply_response(s, c["id"], "colaborar")
        self.assertLess(c["pressure"], 0)


if __name__ == "__main__":
    unittest.main()
