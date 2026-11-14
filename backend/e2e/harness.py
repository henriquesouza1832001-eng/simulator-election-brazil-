"""Ferramentas do teste de ponta a ponta: um jogador automático que conduz uma carreira pela API, como o navegador faria.

Não faz parte dos testes unitários (pasta tests/): é mais lento e joga partidas inteiras. Rodar com `python -m unittest e2e.test_careers`.
"""
from __future__ import annotations

import math
import os
import tempfile
from datetime import date
from pathlib import Path
from typing import Any, Callable
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.db import reset_campaign_id, set_campaign_id
from app.main import app, game_state, save_state

SPEECH = "Assumo o mandato com responsabilidade, diálogo e metas públicas verificáveis em educação, saúde e emprego, prestando contas todo mês."
MESSAGE = "Vou ampliar vagas em creches com metas públicas, prazo definido e prestação de contas à comunidade."
BOUNDED = ("approval", "governability", "congress_support", "institutional_trust", "integrity", "fiscal_credibility")

# telas que precisam responder 200 em qualquer fase da carreira
CORE_GET = ["/api/game", "/api/powers", "/api/regulators", "/api/consequences", "/api/ledger", "/api/mandate/review", "/api/budget/history", "/api/cpi",
            "/api/territory", "/api/territory/home", "/api/indicators/nation/history?keys=aprovacao,inflacao", "/api/indicators/registry", "/api/congress/process",
            "/api/congress/agenda", "/api/career/options", "/api/data/tse/status"]
# podem recusar por regra do cargo (4xx), mas nunca quebrar (5xx)
SOFT_GET = ["/api/companies", "/api/interviews", "/api/fiscal/local", "/api/elector/results"]


class Failure(AssertionError):
    pass


class Player:
    """Uma partida de carreira conduzida por código."""

    def __init__(self, office: str, state_code: str = "SP", municipality_id: str | None = None) -> None:
        self.office, self.state_code, self.municipality_id = office, state_code, municipality_id
        self.cid = ""
        self.calls = 0
        self.log: list[str] = []
        self.last_date: str | None = None

    def __enter__(self) -> "Player":
        self.tmp = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, {"DATABASE_PATH": str(Path(self.tmp.name) / "game.sqlite3"), "COGNITO_REGION": "", "COGNITO_USER_POOL_ID": "",
                                           "COGNITO_CLIENT_ID": "", "COGNITO_DOMAIN": "", "GEMINI_API_KEY": "", "GEMINI_GATEWAY_URL": ""})
        self.env.start()
        self.client = TestClient(app, raise_server_exceptions=False)
        self.client.__enter__()
        return self

    def __exit__(self, *exc: Any) -> None:
        self.client.__exit__(*exc)
        self.env.stop()
        self.tmp.cleanup()

    # ---------- chamadas ----------
    def call(self, method: str, path: str, body: dict[str, Any] | None = None, ok: tuple[int, ...] = (200,)) -> Any:
        self.calls += 1
        headers = {"X-Mandato-Campaign": self.cid} if self.cid else {}
        r = self.client.request(method, path, json=body, headers=headers)
        self.log.append(f"{method} {path} -> {r.status_code}")
        if r.status_code >= 500:
            raise Failure(f"{method} {path} quebrou com {r.status_code}: {r.text[:300]}")
        if r.status_code not in ok:
            raise Failure(f"{method} {path} devolveu {r.status_code} (esperado {ok}): {r.text[:300]}")
        return r.json() if r.content else {}

    def status(self, method: str, path: str, body: dict[str, Any] | None = None) -> tuple[int, Any]:
        self.calls += 1
        headers = {"X-Mandato-Campaign": self.cid} if self.cid else {}
        r = self.client.request(method, path, json=body, headers=headers)
        self.log.append(f"{method} {path} -> {r.status_code}")
        if r.status_code >= 500:
            raise Failure(f"{method} {path} quebrou com {r.status_code}: {r.text[:300]}")
        return r.status_code, (r.json() if r.content else {})

    # ---------- partida ----------
    def start(self) -> dict[str, Any]:
        body = {"office": self.office, "state_code": self.state_code, "municipality": "São Paulo" if self.municipality_id else "", "municipality_id": self.municipality_id,
                "party": "Partido Teste Renovador", "ideology": "Centro-esquerda", "candidate_name": "Candidata Teste", "difficulty": "normal", "new_game": True,
                "campaign_name": f"E2E {self.office}", "character": {"name": "Candidata Teste"}}
        data = self.call("POST", "/api/career/start", body)
        state = data.get("state", data)
        self.cid = state["campaign_id"]
        self.check(state)
        return state

    def game(self) -> dict[str, Any]:
        state = self.call("GET", "/api/game")
        self.check(state)
        return state

    def overview(self) -> dict[str, Any]:
        return self.game()["career_overview"]

    def advance(self, days: int) -> dict[str, Any]:
        code, data = self.status("POST", "/api/game/advance", {"days": days})
        if code == 409:
            action = data.get("action") or (data.get("detail") or {}).get("action") if isinstance(data, dict) else None
            if action != "inaugural_address":
                raise Failure(f"avançar {days} dias recusado (409) sem ser o discurso de posse: {data}")
            self.call("POST", "/api/game/inaugural-address", {"text": SPEECH})
            return self.advance(days)
        if code != 200:
            raise Failure(f"avançar {days} dias devolveu {code}: {data}")
        state = data["state"]
        self.check(state)
        return state

    def tweak(self, change: Callable[[dict[str, Any]], None]) -> None:
        """Altera o estado salvo por dentro (só o teste faz isso): serve para forçar vitória ou derrota na eleição."""
        token = set_campaign_id(self.cid)
        try:
            state = game_state()
            change(state)
            save_state(state)
        finally:
            reset_campaign_id(token)

    # ---------- verificações ----------
    def check(self, state: dict[str, Any]) -> None:
        today = state.get("date")
        if today and self.last_date and today < self.last_date:
            raise Failure(f"a data voltou no tempo: {self.last_date} -> {today}")
        if today:
            self.last_date = today
        metrics = state.get("metrics") or {}
        for key, value in metrics.items():
            if isinstance(value, (int, float)) and not math.isfinite(float(value)):
                raise Failure(f"métrica {key} ficou inválida: {value}")
        for key in BOUNDED:
            value = metrics.get(key)
            if isinstance(value, (int, float)) and not (-0.001 <= float(value) <= 100.001):
                raise Failure(f"métrica {key} saiu de 0..100: {value} em {today}")

    def smoke(self, label: str) -> None:
        for path in CORE_GET:
            code, _ = self.status("GET", path)
            if code != 200:
                raise Failure(f"[{label}] {path} devolveu {code}")
        for path in SOFT_GET:
            self.status("GET", path)

    def play_powers(self, limit: int = 3) -> int:
        """Executa algumas ações do cargo e responde às decisões pendentes; devolve quantas ações passaram."""
        done = 0
        data = self.call("GET", "/api/powers")
        for action in data.get("actions", []):
            if done >= limit:
                break
            if not action.get("available") or action.get("options"):
                continue
            code, _ = self.status("POST", "/api/powers/execute", {"action": action["id"], "option": None})
            if code in (200,):
                done += 1
        feed = self.call("GET", "/api/consequences")
        for crisis in feed.get("pending", [])[:2]:
            option = crisis["options"][0]["id"]
            self.status("POST", f"/api/consequences/{crisis['id']}/respond?option={option}", {})
        return done

    def months_between(self, a: str, b: str) -> int:
        da, db = date.fromisoformat(a), date.fromisoformat(b)
        return (db.year - da.year) * 12 + db.month - da.month
