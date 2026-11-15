import os
import tempfile
import unittest


class StampsByGameTests(unittest.TestCase):
    def test_carimbos_antigos_migram_para_a_partida_onde_foram_ganhos(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["DATABASE_PATH"] = os.path.join(tmp, "g.sqlite3")
            from app import db
            db.initialize()
            with db.connect() as con:
                con.execute("INSERT INTO stamps_unlocked (player_id, stamp_id, campaign_id) VALUES ('p1', 'x1', 'campA')")
            db.initialize()  # a migração roda a cada inicialização e não duplica
            db.initialize()
            with db.connect() as con:
                rows = con.execute("SELECT player_id, campaign_id, stamp_id FROM stamps_by_game").fetchall()
            self.assertEqual([(r["player_id"], r["campaign_id"], r["stamp_id"]) for r in rows], [("p1", "campA", "x1")])

    def test_o_mesmo_carimbo_pode_existir_em_duas_partidas(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["DATABASE_PATH"] = os.path.join(tmp, "g.sqlite3")
            from app import db
            db.initialize()
            with db.connect() as con:
                con.execute("INSERT INTO stamps_by_game (player_id, campaign_id, stamp_id) VALUES ('p1', 'campA', 'x1')")
                con.execute("INSERT INTO stamps_by_game (player_id, campaign_id, stamp_id) VALUES ('p1', 'campB', 'x1')")
                n = con.execute("SELECT COUNT(*) AS n FROM stamps_by_game WHERE stamp_id = 'x1'").fetchone()["n"]
            self.assertEqual(n, 2)


if __name__ == "__main__":
    unittest.main()
