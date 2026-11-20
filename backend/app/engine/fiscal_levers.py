"""Alavancas fiscais de peso para a Presidência: contingenciamento, revisão de subsídios e dividendos extraordinários.

Antes o único corte possível era viagens e residência oficial (R$ 3 bi num PIB de R$ 15 tri, efeito de 0,000% do PIB). Estas três
decisões movem o resultado primário de 0,1% a 0,4% do PIB, com custo real: PIB, aprovação, base no Congresso e confiança. Cada uma
passa pelo mesmo caminho das outras decisões do cargo: mercado reage na hora (`macro.react`), a imprensa e as bancadas repercutem
(`consequences.schedule`), o livro-razão guarda previsto e realizado e "Por que mudou?" mostra a decisão como causa.

O motor decide tudo: os números abaixo são parâmetros de jogo, não previsões.
"""
from __future__ import annotations

from datetime import date
from typing import Any

from . import consequences, drivers, ledger, macro
from .fiscal import ensure_fiscal_state, record_one_off_revenue, record_policy_balance_delta, refresh_fiscal_metrics

GDP_REF_BI = 15000.0
COOLDOWN_DAYS = 60            # intervalo entre quaisquer duas alavancas
YEARLY_LIMIT = {"subsidios": 1, "dividendos": 1}
MAX_CONTINGENCIAMENTO_PCT = 15.0

LEVERS: dict[str, dict[str, Any]] = {
    "contingenciamento": {
        "label": "Contingenciar despesas discricionárias",
        "about": "Segura parte das compras e custeio do Executivo (R$ 222 bi por ano). O resultado primário melhora todo ano, e a atividade e a aprovação pagam o preço.",
        "options": {
            "5": {"label": "5% (cerca de R$ 11 bi por ano)", "saving_bi": 11.1, "effects": {"gdp_growth": -0.03, "approval": -0.3, "institutional_trust": 0.2}, "pct": 5.0},
            "10": {"label": "10% (cerca de R$ 22 bi por ano)", "saving_bi": 22.2, "effects": {"gdp_growth": -0.07, "approval": -0.7, "institutional_trust": 0.4}, "pct": 10.0},
            "15": {"label": "15% (cerca de R$ 33 bi por ano)", "saving_bi": 33.3, "effects": {"gdp_growth": -0.12, "approval": -1.2, "institutional_trust": 0.5, "congress_support": -0.4}, "pct": 15.0},
        },
    },
    "subsidios": {
        "label": "Rever subsídios e isenções fiscais",
        "about": "Corta benefícios tributários de setores e empresas. Rende receita todo ano, mas a bancada ligada a esses setores reage e o investimento esfria.",
        "options": {
            "parcial": {"label": "Revisão parcial (cerca de R$ 18 bi por ano)", "saving_bi": 18.0, "effects": {"gdp_growth": -0.03, "approval": -0.4, "congress_support": -1.2}},
            "forte": {"label": "Revisão forte (cerca de R$ 36 bi por ano)", "saving_bi": 36.0, "effects": {"gdp_growth": -0.07, "approval": -0.9, "congress_support": -2.5, "governability": -0.8}},
        },
    },
    "dividendos": {
        "label": "Dividendos extraordinários das estatais",
        "about": "Pede às estatais um dividendo acima do normal. Entra uma vez só e abate a dívida; as empresas ficam com menos caixa para investir.",
        "options": {
            "moderado": {"label": "Moderado (R$ 20 bi, uma vez)", "one_off_bi": 20.0, "effects": {"gdp_growth": -0.02, "institutional_trust": -0.3}},
            "alto": {"label": "Alto (R$ 40 bi, uma vez)", "one_off_bi": 40.0, "effects": {"gdp_growth": -0.05, "institutional_trust": -0.7, "integrity": -0.3}},
        },
    },
}


def _book(state: dict[str, Any]) -> dict[str, Any]:
    return state.setdefault("fiscal_levers", {"last": None, "history": [], "contingenciamento_pct": 0.0})


def _balance_delta_pct(option: dict[str, Any]) -> float:
    """Melhora anual do resultado primário, em % do PIB (apenas fluxo recorrente; o dividendo único abate a dívida)."""
    return float(option.get("saving_bi", 0.0)) / GDP_REF_BI * 100


def _used_this_year(state: dict[str, Any], lever: str) -> int:
    year = str(state["date"])[:4]
    return sum(1 for h in _book(state)["history"] if h["lever"] == lever and str(h["date"])[:4] == year)


def status(state: dict[str, Any], lever: str, option: str) -> dict[str, Any]:
    spec = LEVERS.get(lever)
    if not spec or option not in spec["options"]:
        return {"available": False, "reason": "Alavanca ou opção desconhecida."}
    book = _book(state)
    today = date.fromisoformat(state["date"])
    if book.get("last"):
        wait = COOLDOWN_DAYS - (today - date.fromisoformat(book["last"])).days
        if wait > 0:
            return {"available": False, "reason": f"Uma alavanca fiscal foi usada há pouco. Aguarde {wait} dia(s)."}
    if lever in YEARLY_LIMIT and _used_this_year(state, lever) >= YEARLY_LIMIT[lever]:
        return {"available": False, "reason": "Esta alavanca já foi usada neste ano."}
    if lever == "contingenciamento":
        total = float(book.get("contingenciamento_pct", 0.0)) + float(spec["options"][option]["pct"])
        if total > MAX_CONTINGENCIAMENTO_PCT + 1e-9:
            return {"available": False, "reason": f"O contingenciamento acumulado passaria de {MAX_CONTINGENCIAMENTO_PCT:.0f}% das despesas discricionárias."}
    return {"available": True, "reason": None}


def forecast(lever: str, option: str) -> dict[str, float]:
    opt = LEVERS[lever]["options"][option]
    out = dict(opt["effects"])
    if opt.get("saving_bi"):
        out["primary_balance"] = round(_balance_delta_pct(opt), 3)
    return out


def catalog(state: dict[str, Any]) -> list[dict[str, Any]]:
    """O que a interface mostra: cada alavanca, suas opções, previsão e se está disponível agora."""
    out = []
    for key, spec in LEVERS.items():
        options = []
        for okey, opt in spec["options"].items():
            st = status(state, key, okey)
            options.append({"id": okey, "label": opt["label"], "available": st["available"], "reason": st["reason"], "forecast": forecast(key, okey),
                            "annual_bi": opt.get("saving_bi"), "one_off_bi": opt.get("one_off_bi")})
        out.append({"id": key, "label": spec["label"], "about": spec["about"], "options": options})
    return out


def apply(state: dict[str, Any], lever: str, option: str) -> dict[str, Any]:
    st = status(state, lever, option)
    if not st["available"]:
        raise ValueError(st["reason"])
    from .powers import _bump
    spec, opt = LEVERS[lever], LEVERS[lever]["options"][option]
    title = f"{spec['label']}: {opt['label'].split(' (')[0].lower()}"
    ensure_fiscal_state(state)
    before_balance = float(state["metrics"].get("primary_balance", 0))
    with drivers.because(title):
        applied = {}
        for key, delta in opt["effects"].items():
            applied[key] = round(_bump(state, key, delta), 3)   # `_bump` já anota a causa em "Por que mudou?"
        if opt.get("saving_bi"):
            record_policy_balance_delta(state, _balance_delta_pct(opt))
        if opt.get("one_off_bi"):
            record_one_off_revenue(state, float(opt["one_off_bi"]))
    refresh_fiscal_metrics(state)
    balance_delta = round(float(state["metrics"].get("primary_balance", 0)) - before_balance, 4)
    signal = dict(opt["effects"])
    signal["primary_balance"] = _balance_delta_pct(opt) if opt.get("saving_bi") else 0.0
    cost_bi = -float(opt.get("one_off_bi", 0.0))   # receita única: sinal contrário ao de gasto
    macro.react(state, signal, cost_bi, title, f"lever_{lever}")
    book = _book(state)
    book["last"] = state["date"]
    if lever == "contingenciamento":
        book["contingenciamento_pct"] = round(float(book.get("contingenciamento_pct", 0.0)) + float(opt["pct"]), 2)
    book["history"].insert(0, {"date": state["date"], "lever": lever, "option": option, "title": title})
    del book["history"][20:]
    entry = ledger.record(state, "presidencia", title, forecast(lever, option), {**applied, "primary_balance": balance_delta}, status="em vigor",
                          cost=None)
    consequences.schedule(state, action_id=f"lever_{lever}", title=title, domain="economia", effects=opt["effects"], ledger_id=entry["id"])
    return {"title": title, "effects": applied, "primary_balance_delta_pct_gdp": balance_delta,
            "message": f"{title}: em vigor. O resultado primário muda {balance_delta:+.3f} pontos do PIB."}
