"""Teste de ponta a ponta das carreiras: de vereador a presidente, vencendo e perdendo a eleição.

Cada partida começa o cargo, atravessa a pré-campanha e a campanha, passa pela eleição (resultado forçado para cobrir os dois caminhos),
e, se vence, toma posse e joga meses de mandato. Em todas as fases confere as telas principais e as regras básicas (data nunca volta,
indicadores válidos, nenhuma chamada quebra com erro 500).

Variáveis de ambiente:
  E2E_OFFICES=vereador,prefeito   limita os cargos testados (padrão: todos)
  E2E_MONTHS=12                   meses de mandato jogados depois da posse (padrão 6; 48 joga o mandato inteiro)
"""
from __future__ import annotations

import os
import time
import unittest

from e2e.harness import MESSAGE, Failure, Player

OFFICES = [("vereador", "SP", "3550308"), ("prefeito", "SP", "3550308"), ("deputado_estadual", "SP", None), ("governador", "SP", None),
           ("deputado_federal", "SP", None), ("senador", "SP", None), ("presidente", "DF", None)]
SELECTED = {o.strip() for o in os.getenv("E2E_OFFICES", "").split(",") if o.strip()}
MONTHS = int(os.getenv("E2E_MONTHS", "6"))


RESULTS: list[dict] = []


def tearDownModule() -> None:
    """Se E2E_REPORT apontar para um arquivo, grava o relatório da rodada em Markdown (o GitHub o mostra no resumo da execução)."""
    path = os.getenv("E2E_REPORT")
    if not path or not RESULTS:
        return
    ordem = [o[0] for o in OFFICES]
    rows = sorted(RESULTS, key=lambda r: (ordem.index(r["office"]), not r["win"]))
    ok = sum(1 for r in rows if r["ok"])
    lines = [f"## Carreiras de ponta a ponta: {ok} de {len(rows)} cenários passaram", "",
             f"Meses de mandato jogados: {MONTHS}. Resultado da eleição forçado para cobrir vitória e derrota.", "",
             "| Cargo | Eleição | Situação | Fases | Ações do cargo | Meses | Chamadas | Tempo |", "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['office']} | {'vence' if r['win'] else 'perde'} | {'passou' if r['ok'] else 'FALHOU'} | {', '.join(r.get('phases', []))} | {r.get('powers', '')} | {r.get('months', '')} | {r.get('calls', '')} | {r['seconds']:.0f}s |")
    falhas = [r for r in rows if not r["ok"]]
    if falhas:
        lines += ["", "### Falhas"] + [f"- **{r['office']} ({'vence' if r['win'] else 'perde'})**: {r['error']}" for r in falhas]
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(chr(10).join(lines) + chr(10))


def force(support: float, momentum: float):
    def change(state):
        career = state["career"]
        career["poll_support"] = support
        career["local_support"] = support
        career["state_support"] = support
        career["momentum"] = momentum
    return change


def run_career(test: unittest.TestCase, office: str, state_code: str, municipality: str | None, win: bool) -> dict:
    summary = {"office": office, "win": win, "phases": [], "powers": 0, "months": 0, "calls": 0}
    with Player(office, state_code, municipality) as g:
        state = g.start()
        test.assertEqual(g.overview()["phase"], "pre_campaign", "a carreira deve começar na pré-campanha")
        g.smoke("pré-campanha")

        # pré-campanha: uma preparação e, se a espera é longa, o pulo para o ano da eleição
        code, _ = g.status("POST", "/api/career/preparation", {"action": "mobilizar_voluntariado"})
        ov = g.overview()
        if ov["phase"] == "pre_campaign" and ov["days_until_campaign"] > 120:
            g.call("POST", "/api/career/skip-to-election-year")
        guard = 0
        while g.overview()["phase"] == "pre_campaign":
            g.advance(30)
            guard += 1
            test.assertLess(guard, 40, "a pré-campanha não terminou")

        # campanha: atividades até perto da eleição, onde o resultado é forçado
        g.smoke("campanha")
        forced = False
        guard = 0
        while g.overview()["phase"] in ("campaign", "runoff_campaign"):
            ov = g.overview()
            if not forced and ov["days_until_election"] <= 8:
                g.tweak(force(97.0, 10.0) if win else force(2.0, -10.0))
                forced = True
            if ov.get("can_act"):
                g.status("POST", "/api/career/action", {"activity_type": "comicio", "issue": "educacao", "message": MESSAGE, "municipality_id": municipality})
            else:
                g.advance(7)
            guard += 1
            test.assertLess(guard, 120, "a campanha não terminou")
        if not forced:
            test.fail("a eleição passou sem que o resultado fosse forçado")

        # segundo turno (cargos majoritários): força de novo e deixa passar
        guard = 0
        while g.overview()["phase"] in ("runoff_observer",) and guard < 10:
            g.advance(7)
            guard += 1

        ov = g.overview()
        summary["phases"].append(ov["phase"])
        test.assertIn(ov["phase"], ("transition", "opposition", "office", "term_complete"), f"fase inesperada depois da eleição: {ov['phase']}")
        if win:
            test.assertIn(ov["phase"], ("transition", "office"), "o resultado forçado era vitória, mas o jogador não venceu")
        else:
            test.assertIn(ov["phase"], ("opposition", "term_complete"), "o resultado forçado era derrota, mas o jogador não perdeu")
        g.smoke("resultado")

        if win and ov["phase"] == "transition":
            guard = 0
            while g.overview()["phase"] == "transition":
                g.advance(30)
                guard += 1
                test.assertLess(guard, 12, "a posse não chegou")
            test.assertEqual(g.overview()["phase"], "office", "depois da posse o jogador deve estar no cargo")
            g.smoke("posse")
            start = g.game()["date"]
            played = 0
            for month in range(MONTHS):
                g.advance(30)
                if month % 2 == 0:
                    played += g.play_powers(2)
                if month % 3 == 2:
                    g.smoke(f"mandato mês {month + 1}")
            test.assertGreater(g.months_between(start, g.game()["date"]), MONTHS - 2, "o mandato deveria ter avançado")
            test.assertGreaterEqual(played, 1, "nenhuma ação do cargo pôde ser executada durante o mandato")
            summary["phases"].append("office")
            summary["powers"], summary["months"] = played, MONTHS
        elif not win:
            test.assertIn(ov["phase"], ("opposition", "term_complete"), "a derrota deve levar à oposição")
            for _ in range(3):
                g.advance(30)
            g.smoke("pós-derrota")
        summary["calls"] = g.calls
    return summary


class CareerEndToEnd(unittest.TestCase):
    pass


def _make(office: str, state_code: str, municipality: str | None, win: bool):
    def test(self):
        started = time.time()
        entry = {"office": office, "win": win, "ok": False, "seconds": 0.0, "error": ""}
        RESULTS.append(entry)
        try:
            summary = run_career(self, office, state_code, municipality, win)
            entry.update(summary, ok=True, seconds=time.time() - started)
            print(f"   {summary['office']:18s} {'vence' if win else 'perde':5s} fases={summary['phases']} ações_do_cargo={summary['powers']} meses={summary['months']} chamadas={summary['calls']}")
        except BaseException as exc:
            entry.update(seconds=time.time() - started, error=str(exc)[:300])
            if isinstance(exc, Failure):
                self.fail(str(exc))
            raise
    test.__name__ = f"test_{office}_{'vence' if win else 'perde'}"
    return test


for _office, _uf, _mun in OFFICES:
    if SELECTED and _office not in SELECTED:
        continue
    for _win in (True, False):
        _t = _make(_office, _uf, _mun, _win)
        setattr(CareerEndToEnd, _t.__name__, _t)


if __name__ == "__main__":
    unittest.main()
