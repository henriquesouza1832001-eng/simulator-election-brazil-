import unittest
from datetime import date, timedelta

from app.engine import congress_process as cp
from app.engine import powers
from app.engine.state import new_game, process_legislation, refresh_calendar_fields


def president(seed=1):
    s = refresh_calendar_fields(new_game())
    s["date"] = "2027-03-01"
    s["campaign_seed"] = seed
    return s


def bill_for(action="empresa_privatizar", option="Correios", seed=1):
    s = president(seed)
    powers.execute(s, action, option if action == "empresa_privatizar" else None)
    return s, s["legislative_calendar"]["pending_bills"][0]


class CongressProcessTest(unittest.TestCase):
    def test_bill_gets_stages_and_a_real_deputy_as_relator(self):
        s, bill = bill_for()
        proc = bill["process"]
        self.assertEqual([x["name"] for x in proc["stages"]], ["Protocolo", "Comissão de mérito", "CCJ", "Plenário da Câmara", "Senado"])
        self.assertTrue(proc["relator"]["name"] and proc["relator"]["party"] in {p["id"] for p in cp.legislature.PARTIES})
        pec = president()
        powers.execute(pec, "reg_reeleicao")
        self.assertEqual(pec["legislative_calendar"]["pending_bills"][0]["process"]["stages"][1]["name"], "CCJ — admissibilidade")

    def test_outlook_by_party_is_ideological(self):
        s, bill = bill_for()   # privatização: ação de direita
        rows = {r["party"]: r for r in cp.party_outlook(s, bill)}
        self.assertGreater(rows["PL"]["support_pct"], rows["PSOL"]["support_pct"])

    def test_negotiation_raises_relation_once_and_concession_dilutes_text(self):
        s, bill = bill_for()
        before = s.get("relation_delta", {}).get("PSD", 0.0)
        cp.negotiate(s, bill["id"], "PSD", "emendas")
        self.assertGreater(s["relation_delta"]["PSD"], before)
        with self.assertRaises(PermissionError):
            cp.negotiate(s, bill["id"], "PSD", "emendas")
        out = cp.negotiate(s, bill["id"], "MDB", "concessao")
        self.assertEqual(out["dilution"], 0.9)
        with self.assertRaises(ValueError):
            cp.negotiate(s, bill["id"], "XXX", "emendas")

    def test_urgency_shortens_deadline_skips_committees_and_costs_relations(self):
        s, bill = bill_for()
        end = bill["decision_date"]
        cp.request_urgency(s, bill["id"])
        self.assertLess(bill["decision_date"], end)
        self.assertTrue(all(st["status"] != "pendente" for st in bill["process"]["stages"][1:3]))
        with self.assertRaises(PermissionError):
            cp.request_urgency(s, bill["id"])
        pec = president()
        powers.execute(pec, "reg_reeleicao")
        with self.assertRaises(PermissionError):
            cp.request_urgency(pec, pec["legislative_calendar"]["pending_bills"][0]["id"])

    def test_committee_can_shelve_a_bill_and_news_is_posted(self):
        killed = passed = 0
        for seed in range(1, 80):
            s, bill = bill_for(seed=seed)
            s["metrics"]["congress_support"] = 25
            cp.tick(s, date(2027, 3, 1), date(2027, 8, 1))
            if not s["legislative_calendar"]["pending_bills"]:
                killed += 1
                self.assertEqual(s["legislative_calendar"]["laws_failed"], 1)
                self.assertTrue(any("arquivado" in f["headline"] for f in s["consequences"]["feed"]))
            else:
                passed += 1
        self.assertGreater(killed, 0)
        self.assertGreater(passed, 0)

    def test_better_base_and_negotiation_improve_committee_odds(self):
        s, bill = bill_for()
        s["metrics"]["congress_support"] = 30
        low = cp.committee_chance(s, bill)
        s["metrics"]["congress_support"] = 70
        high = cp.committee_chance(s, bill)
        cp.negotiate(s, bill["id"], "PSD", "emendas")
        self.assertGreater(high, low)
        self.assertGreater(cp.committee_chance(s, bill), high)

    def test_dilution_reduces_effects_when_law_passes(self):
        s, bill = bill_for(action="seg_armas_afrouxar" if False else "empresa_privatizar")
        cp.negotiate(s, bill["id"], "MDB", "concessao")
        before = s["metrics"]["approval"]
        powers.resolve_bill(s, bill, True)
        entry = next(e for e in s["ledger"] if e["id"] == bill["ledger_id"])
        full = powers.BY_ID["empresa_privatizar"]["effects"]["approval"]
        self.assertAlmostEqual(entry["result"]["approval"], round(full * 0.9, 4), places=2)


if __name__ == "__main__":
    unittest.main()
