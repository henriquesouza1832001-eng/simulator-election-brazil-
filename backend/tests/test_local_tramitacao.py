import unittest
from datetime import date, timedelta

from app.engine import congress_process as cp
from app.engine import office_powers as op
from app.engine import powers
from app.engine.state import new_game, refresh_calendar_fields
from tests.test_office_powers import career_state


class LocalTramitacaoTest(unittest.TestCase):
    def test_councillor_bill_goes_through_committee_and_plenary_with_ledger(self):
        s = career_state("vereador", capital=80)
        out = op.execute(s, "v_creches")
        bill = s["local_bills"][0]
        self.assertEqual([x["name"] for x in bill["stages"]], ["Protocolo", "Comissão", "Plenário (Câmara Municipal)"])
        self.assertEqual(s["ledger"][0]["status"], "em tramitação")
        self.assertEqual(out["decision_date"], bill["decision_date"])
        approved = rejected = 0
        for seed in range(1, 60):
            t = career_state("vereador", capital=80)
            t["campaign_seed"] = seed
            op.execute(t, "v_creches")
            op.local_tick(t, date(2029, 4, 10), date(2029, 7, 30))
            status = t["local_bills"][0]["status"]
            approved += status == "aprovado"
            rejected += status.startswith("rejeitado")
            self.assertNotEqual(status, "em tramitação")
        self.assertGreater(approved, 0)
        self.assertGreater(rejected, 0)

    def test_effects_only_apply_after_approval(self):
        for seed in range(1, 80):
            s = career_state("vereador", capital=90)
            s["campaign_seed"] = seed
            op.execute(s, "v_ubs")
            self.assertNotIn("territory", s)   # nada muda no protocolo
            op.local_tick(s, date(2029, 4, 10), date(2029, 7, 30))
            if s["local_bills"][0]["status"] == "aprovado":
                self.assertGreater(s["territory"]["deltas"]["city:3550308"]["saude_atencao"], 0)
                self.assertEqual(s["ledger"][0]["status"], "aprovado")
                return
        self.fail("nenhum projeto aprovado")

    def test_federal_deputy_bill_has_a_real_deputy_as_relator(self):
        s = career_state("deputado_federal", capital=80)
        op.execute(s, "df_emenda")
        rel = s["local_bills"][0]["relator"]
        self.assertTrue(rel["real"] and rel["party"])


class ObstructionTest(unittest.TestCase):
    def president_bill(self, seed):
        s = refresh_calendar_fields(new_game())
        s["date"] = "2027-03-01"
        s["campaign_seed"] = seed
        powers.execute(s, "empresa_privatizar", "Correios")
        return s, s["legislative_calendar"]["pending_bills"][0]

    def test_polarizing_bills_can_be_obstructed_and_lose_text_to_destaque(self):
        obstructed = destaque = 0
        for seed in range(1, 80):
            s, bill = self.president_bill(seed)
            end = bill["decision_date"]
            cp.tick(s, date(2027, 3, 1), date(2027, 5, 15))
            if not s["legislative_calendar"]["pending_bills"]:
                continue
            proc = bill["process"]
            if proc.get("obstructed"):
                obstructed += 1
                self.assertGreater(bill["decision_date"], end)
            if proc.get("destaque"):
                destaque += 1
                self.assertLess(proc["dilution"], 1.0)
        self.assertGreater(obstructed, 0)
        self.assertGreater(destaque, 0)

    def test_neutral_bills_are_not_obstructed_and_negotiation_reduces_obstruction(self):
        s, bill = self.president_bill(1)
        self.assertGreater(cp.opposition_share(bill), 0.1)
        neutral = {"power_id": "bc_meta_inflacao"}
        self.assertEqual(cp.opposition_share(neutral), 0.0)
        cp_before = sum(1 for seed in range(1, 60) if self._obstructs(seed, 0))
        cp_after = sum(1 for seed in range(1, 60) if self._obstructs(seed, 3))
        self.assertGreaterEqual(cp_before, cp_after)

    def _obstructs(self, seed, offers):
        s, bill = self.president_bill(seed)
        for party in ["PT", "PSOL", "PSB"][:offers]:
            cp.negotiate(s, bill["id"], party, "emendas")
        cp.tick(s, date(2027, 3, 1), date(2027, 5, 15))
        return bool(bill["process"].get("obstructed"))


if __name__ == "__main__":
    unittest.main()
