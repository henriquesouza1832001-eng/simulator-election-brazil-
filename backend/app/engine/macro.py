"""Motor macro-financeiro: o mercado e a economia reagem ao que o governo faz.

Antes, inflação e desemprego só voltavam devagar a uma média fixa e o resto era enfeite. Agora tudo está ligado:

  déficit e dívida, confiança nas instituições e integridade  ->  risco-país
  risco-país e juros reais                                      ->  câmbio
  câmbio, expectativas, juros e atividade                       ->  inflação (repasse cambial, demanda, política monetária)
  juros reais, confiança, risco e investimento                  ->  crescimento do PIB  ->  desemprego (lei de Okun)
  confiança, juros, risco e crescimento                         ->  bolsa

Além da dinâmica mês a mês, toda decisão tem uma reação imediata do mercado (`react`): o dólar, a bolsa e o risco-país
saltam na hora conforme o que a decisão sinaliza (contas públicas, confiança nas instituições, estatais, intervenção no
Banco Central). Coeficientes são parâmetros de design calibrados para um país emergente com juros altos; não são
previsões nem estimativas econômicas.
"""
from __future__ import annotations

import hashlib
import math
from datetime import date
from typing import Any

from . import voice

NEUTRAL_REAL = 4.5       # juro real neutro (% a.a.)
POTENTIAL = 2.2          # crescimento potencial (% a.a.)
NAIRU = 6.0              # desemprego de equilíbrio (%)
TARGET = 3.0             # meta de inflação
GDP_REF_BI = 15000.0
HISTORY_LIMIT = 72
NEWS_LIMIT = 40

# Sinal de mercado extra de decisões específicas: (bolsa %, câmbio %, risco-país em pontos-base).
MARKET_SIGNALS: dict[str, tuple[float, float, float]] = {
    "bc_revogar_autonomia": (-3.0, 3.5, 45), "bc_restaurar_autonomia": (3.0, -2.5, -35), "bc_autonomia_constitucional": (2.5, -1.5, -20),
    "bc_pressao_juros": (-1.2, 1.0, 12), "bc_meta_inflacao": (-0.5, 0.4, 5), "bc_moeda_comum": (-4.0, 3.0, 50),
    "empresa_privatizar": (2.5, -0.6, -8), "empresa_estatizar": (-3.5, 1.2, 18), "empresa_criar": (-1.0, 0.4, 6), "empresa_monopolio_petroleo": (-3.0, 1.0, 14),
    "eco_reforma_tributaria": (3.0, -1.0, -12), "eco_previdencia": (3.5, -1.2, -18), "eco_teto": (2.0, -0.8, -12), "eco_confisco": (-12.0, 7.0, 150),
    "eco_desoneracao": (1.0, 0.4, 6), "eco_bolsa": (-0.5, 0.5, 8), "eco_mp": (-0.6, 0.5, 6),
    "defesa_guerra": (-12.0, 9.0, 140), "defesa_bomba": (-6.0, 4.0, 60), "defesa_intervencao": (-4.0, 3.0, 40),
    "reg_monarquia": (-15.0, 10.0, 200), "reg_abolir_federacao": (-14.0, 9.0, 180), "reg_forma_governo": (-6.0, 4.0, 60), "reg_reeleicao": (-1.0, 0.6, 12),
    "ext_brics_entrar": (-1.5, 1.2, 12), "ext_brics_sair": (1.0, -0.6, -6), "ext_otan": (-0.5, 0.3, 4), "ext_mercosul": (0.5, -0.2, -2), "ext_acordo_comercial": (1.8, -0.8, -8),
    "jus_indulto_8jan": (-1.5, 1.0, 15), "jus_8jan_manter": (0.8, -0.5, -8), "jus_anistia_8jan": (-1.0, 0.8, 10),
    "jus_stf_numero": (-5.0, 3.0, 60), "jus_pec_stf_mandato": (-1.5, 1.0, 15), "leg_emendas": (-0.8, 0.6, 8),
    "amb_licenciamento": (1.0, -0.3, -4), "saude_emergencia": (-1.5, 1.2, 12), "amb_calamidade": (-1.0, 0.8, 10),
}


def _u(state: dict[str, Any], key: str) -> float:
    return int(hashlib.sha256(f"{state.get('campaign_seed', 1)}|macro|{key}".encode()).hexdigest()[:8], 16) / 0xFFFFFFFF


def _normal(state: dict[str, Any], key: str) -> float:
    return (sum(_u(state, f"{key}|{k}") for k in range(4)) - 2.0) / math.sqrt(4 / 12)


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def ensure(state: dict[str, Any]) -> dict[str, Any]:
    from . import central_bank
    macro = state.setdefault("macro", {})
    if "bolsa" not in macro:
        nation = (state.get("nation") or {}).get("values") or {}
        m = state.get("metrics", {})
        selic = float(central_bank.ensure(state)["selic"])
        macro.update({"bolsa": 130000.0, "cambio": float(nation.get("cambio", 5.3)), "risco": float(nation.get("risco_pais", 220.0)),
                      "expect": float(m.get("inflation", 4.5)), "confianca": 55.0, "gap": 0.0, "selic_prev": selic, "history": [], "news": []})
        macro["start"] = {k: macro[k] for k in ("bolsa", "cambio", "risco", "expect")} | {"selic": selic}
    return macro


def _news(state: dict[str, Any], text: str, bolsa_pct: float, cambio_pct: float, risco_bps: float, label: str = "") -> None:
    macro = ensure(state)
    entry = {"date": state.get("date"), "text": text, "bolsa_pct": round(bolsa_pct, 2), "cambio_pct": round(cambio_pct, 2), "risco_bps": round(risco_bps), "label": label}
    macro["news"].insert(0, entry)
    del macro["news"][NEWS_LIMIT:]
    if abs(bolsa_pct) >= 2.0 or abs(cambio_pct) >= 1.5:
        board = state.setdefault("simulated_news", [])
        board.insert(0, {"id": f"mkt-{state.get('date')}-{len(macro['news'])}", "date": state.get("date"), "title": text, "region": "Nacional",
                         "description": voice.pick(voice.MARKET_DESC, str(state.get("date")) + text), "simulated": True})
        del board[20:]


def _pct(v: float, signed: bool = True) -> str:
    return f"{'+' if (signed and v > 0) else ''}{v:.1f}".replace(".", ",") + "%"


def react(state: dict[str, Any], effects: dict[str, float], cost_bi: float = 0.0, label: str = "uma decisão", action_id: str | None = None, scale: float = 1.0) -> dict[str, float] | None:
    """Reação imediata do mercado a uma decisão: dólar, bolsa e risco-país saltam conforme o que ela sinaliza."""
    macro = ensure(state)
    inst, integ = float(effects.get("institutional_trust", 0)), float(effects.get("integrity", 0))
    pb, g, inf = float(effects.get("primary_balance", 0)), float(effects.get("gdp_growth", 0)), float(effects.get("inflation", 0))
    gov = float(effects.get("governability", 0)) + float(effects.get("congress_support", 0)) * 0.5
    pbe = pb - (float(cost_bi or 0) * 0.3) / GDP_REF_BI * 100       # gasto pontual pesa menos que mudança permanente
    risco = _clamp(-10 * inst - 6 * integ - 110 * pbe + 2 * inf, -250, 250)
    bolsa = 2.2 * inst + 14 * pbe + 10 * g + 0.8 * integ + 0.6 * gov - 3 * inf
    cambio = 0.012 * risco - 0.5 * g
    extra = MARKET_SIGNALS.get(action_id or "")
    if extra:
        bolsa, cambio, risco = bolsa + extra[0], cambio + extra[1], risco + extra[2]
    bolsa, cambio, risco = bolsa * scale, cambio * scale, risco * scale   # anúncio (parte do efeito) ou reversão na rejeição (negativo)
    policy = macro.setdefault("policy", {"g": 0.0, "i": 0.0})
    policy["g"] = _clamp(policy["g"] + 4.0 * g * scale, -1.5, 1.5)   # efeito de política que persiste e decai devagar
    policy["i"] = _clamp(policy["i"] + 2.0 * inf * scale, -1.0, 1.0)
    if abs(bolsa) < 0.15 and abs(cambio) < 0.1 and abs(risco) < 2:
        return None
    macro["bolsa"] = _clamp(macro["bolsa"] * (1 + bolsa / 100), 20000, 400000)
    macro["cambio"] = _clamp(macro["cambio"] * (1 + cambio / 100), 3.0, 12.0)
    macro["risco"] = _clamp(macro["risco"] + risco, 60, 1200)
    macro["confianca"] = _clamp(macro["confianca"] + (0.9 * inst + 0.5 * integ + 8 * pbe) * scale, 5, 95)
    _sync_nation(state)
    if abs(bolsa) >= 1.0 or abs(cambio) >= 0.6 or abs(risco) >= 10:
        verb_d = "sobe" if cambio > 0 else "cai"
        verb_b = "sobe" if bolsa > 0 else "cai"
        quoted = label if "“" in label else f"“{label}”"
        _news(state, voice.market_reaction(f"{state.get('campaign_seed', 1)}:{state.get('date')}:{label}", quoted, verb_d, verb_b, _pct(abs(cambio), False), _pct(abs(bolsa), False),
                                           f"{'+' if risco >= 0 else '−'}{abs(round(risco))}"),
              bolsa, cambio, risco, label)
    return {"bolsa_pct": round(bolsa, 2), "cambio_pct": round(cambio, 2), "risco_bps": round(risco, 1)}


def _sync_nation(state: dict[str, Any]) -> None:
    macro = state["macro"]
    values = (state.get("nation") or {}).get("values")
    if values is not None:
        values["cambio"], values["risco_pais"], values["expectativas"] = round(macro["cambio"], 3), round(macro["risco"], 1), round(macro["expect"], 2)
        values["bolsa"] = round(macro["bolsa"], 0)


def step(state: dict[str, Any], before: date, after: date, volatility: float = 1.0) -> list[str]:
    """Um passo de tempo da economia: encadeia contas públicas, mercado, inflação, atividade e emprego."""
    from . import central_bank
    elapsed = (after - before).days
    if elapsed <= 0:
        return []
    macro = ensure(state)
    copom = central_bank.ensure(state)
    m = state["metrics"]
    dt = elapsed / 30.44
    vol = max(0.3, float(volatility))
    infl, unemp, growth = float(m["inflation"]), float(m["unemployment"]), float(m["gdp_growth"])
    pb, debt = float(m.get("primary_balance", -1.5)), float(m.get("debt_gdp", 78.0))
    inst, integ = float(m.get("institutional_trust", 58)), float(m.get("integrity", 70))
    selic, cred = float(copom["selic"]), float(copom.get("credibility", 70))
    outcomes = (state.get("budget") or {}).get("outcomes") or {}
    infra = float(outcomes.get("infrastructure", 50.0))
    human = 0.02 * (float(outcomes.get("productivity", 50.0)) - 50) + 0.008 * (float(outcomes.get("education", 50.0)) - 50) + 0.005 * (float(outcomes.get("health", 50.0)) - 50)  # investimento acumulado
    key = f"{after.isoformat()}"
    policy = macro.setdefault("policy", {"g": 0.0, "i": 0.0})
    for k in ("g", "i"):
        policy[k] *= 0.94 ** dt
    old = {k: macro[k] for k in ("bolsa", "cambio", "risco", "confianca")}

    # 1) risco-país: contas públicas, dívida e instituições
    risco_target = 105 + 7 * max(0.0, debt - 70) + 55 * max(0.0, -pb - 0.5) + 3.5 * max(0.0, 60 - inst) + 2.0 * max(0.0, 55 - integ)
    macro["risco"] = _clamp(macro["risco"] + (risco_target - macro["risco"]) * (1 - math.exp(-0.35 * dt)), 60, 1200)
    # 2) expectativas de inflação (ancoradas pela credibilidade do Banco Central)
    exp_target = 0.55 * infl + 0.45 * TARGET + (70 - cred) * 0.02 + policy["i"]
    macro["expect"] = _clamp(macro["expect"] + (exp_target - macro["expect"]) * (1 - math.exp(-0.3 * dt)), 1.0, 40.0)
    real = selic - macro["expect"]
    # 3) câmbio: risco-país e diferencial de juros
    cambio_target = 5.1 + 0.0035 * (macro["risco"] - 150) - 0.05 * (real - NEUTRAL_REAL)
    cambio = macro["cambio"] + (cambio_target - macro["cambio"]) * (1 - math.exp(-0.45 * dt))
    cambio *= 1 + _normal(state, "cambio|" + key) * 0.012 * math.sqrt(dt) * vol
    cambio = _clamp(cambio, 3.0, 12.0)
    cambio_pct = (cambio / macro["cambio"] - 1) * 100
    macro["cambio"] = cambio
    # 4) inflação: expectativas, política monetária, demanda e repasse cambial
    d_infl = (macro["expect"] - infl) * (1 - math.exp(-0.25 * dt)) - 0.03 * (real - NEUTRAL_REAL) * dt + 0.06 * macro["gap"] * dt + 0.15 * cambio_pct
    from . import drivers
    k_i = 1 - math.exp(-0.25 * dt)
    for why, part in (
            ("Expectativas de inflação", (macro["expect"] - infl) * k_i), ("Juros (Selic) frente à inflação esperada", -0.03 * (real - NEUTRAL_REAL) * dt),
            ("Demanda da economia", 0.06 * macro["gap"] * dt), ("Câmbio (dólar)", 0.15 * cambio_pct)):
        drivers.note(state, "inflation", part, why)   # "Por que mudou?": cada termo da inflação vira uma causa
    infl = _clamp(infl + d_infl, 0.3, 40.0)
    # 5) crescimento: juros reais, confiança, risco, impulso fiscal e investimento público
    growth_target = POTENTIAL + 0.07 * (macro["confianca"] - 55) - 0.25 * (real - NEUTRAL_REAL) - 0.12 * (pb + 1.0) - 0.004 * (macro["risco"] - 200) + 0.02 * (infra - 50) + human + policy["g"]
    k_g = 1 - math.exp(-0.3 * dt)
    for why, part in (
            ("Retorno ao ritmo normal da economia", POTENTIAL - growth), ("Confiança de empresas e consumidores", 0.07 * (macro["confianca"] - 55)),
            ("Juros reais", -0.25 * (real - NEUTRAL_REAL)), ("Contas públicas (resultado primário)", -0.12 * (pb + 1.0)), ("Risco-país", -0.004 * (macro["risco"] - 200)),
            ("Investimento em infraestrutura", 0.02 * (infra - 50)), ("Educação, saúde e produtividade", human), ("Estímulo ou aperto das suas decisões", policy["g"])):
        drivers.note(state, "gdp_growth", part * k_g, why)
    growth = _clamp(growth + (growth_target - growth) * k_g, -6.0, 8.0)
    macro["gap"] = _clamp(macro["gap"] * 0.93 ** dt + (growth - POTENTIAL) * dt / 6, -6.0, 6.0)
    # 6) desemprego: lei de Okun e retorno ao desemprego de equilíbrio
    drivers.note(state, "unemployment", -0.5 * (growth - POTENTIAL) * dt / 12, "Atividade econômica (PIB)")
    drivers.note(state, "unemployment", 0.04 * (NAIRU - unemp) * dt, "Retorno ao desemprego de equilíbrio")
    unemp = _clamp(unemp - 0.5 * (growth - POTENTIAL) * dt / 12 + 0.04 * (NAIRU - unemp) * dt, 2.0, 25.0)
    # 7) confiança de empresas e consumidores
    conf_target = 55 + 0.5 * (inst - 58) + 0.15 * (integ - 70) - 0.05 * (macro["risco"] - 220) - 2.0 * max(0.0, infl - 5.0) - 1.5 * max(0.0, -pb - 1.5)
    macro["confianca"] = _clamp(macro["confianca"] + (_clamp(conf_target, 5, 95) - macro["confianca"]) * (1 - math.exp(-0.35 * dt)), 5, 95)
    # 8) bolsa: lucros esperados, juros, risco e humor
    ret = 0.007 * dt + 0.0028 * (macro["confianca"] - old["confianca"]) - 0.012 * (selic - macro["selic_prev"]) - 0.0010 * (macro["risco"] - old["risco"]) \
        + 0.0035 * (growth - 2.0) * dt + _normal(state, "bolsa|" + key) * 0.04 * math.sqrt(dt) * vol
    macro["bolsa"] = _clamp(macro["bolsa"] * math.exp(ret), 20000, 400000)
    macro["selic_prev"] = selic

    m["inflation"], m["unemployment"], m["gdp_growth"] = round(infl, 2), round(unemp, 2), round(growth, 2)
    # 9) a economia do dia a dia pesa na popularidade: crescimento ajuda; desemprego e inflação alta cobram a conta
    econ = 0.8 * (growth - 2.0) - 0.9 * (unemp - 6.5) - 0.5 * (infl - 4.5)
    approval_before = float(m["approval"])
    m["approval"] = round(_clamp(float(m["approval"]) + dt * (0.12 * econ - 0.05 * (float(m["approval"]) - 50.0)), 0.0, 100.0), 2)  # a popularidade volta à média sem mérito novo
    from . import drivers
    drivers.note(state, "approval", float(m["approval"]) - approval_before, "Economia: crescimento, inflação e desemprego")
    _sync_nation(state)
    messages: list[str] = []
    bolsa_pct = (macro["bolsa"] / old["bolsa"] - 1) * 100
    risco_bps = macro["risco"] - old["risco"]
    if abs(bolsa_pct) >= 6 or abs(cambio_pct) >= 4 or abs(risco_bps) >= 40:
        text = voice.market_day(f"{state.get('campaign_seed', 1)}:{after.isoformat()}", bolsa_pct, cambio_pct, risco_bps, _pct, lambda r: f"{'+' if r >= 0 else '−'}{abs(round(r))} pontos")
        _news(state, text, bolsa_pct, cambio_pct, risco_bps, "movimento do período")
        messages.append(text)
    month = after.isoformat()[:7]
    if not macro["history"] or macro["history"][-1]["month"] != month:
        macro["history"].append({"month": month, "bolsa": round(macro["bolsa"]), "cambio": round(macro["cambio"], 3), "risco": round(macro["risco"]), "selic": round(selic, 2),
                                 "expect": round(macro["expect"], 2), "confianca": round(macro["confianca"], 1), "inflacao": round(infl, 2), "desemprego": round(unemp, 2), "pib": round(growth, 2)})
        del macro["history"][:-HISTORY_LIMIT]
    return messages


def _n(v: float) -> str:
    return f"{v:.1f}".replace(".", ",")


def overview(state: dict[str, Any]) -> dict[str, Any]:
    from . import central_bank
    macro = ensure(state)
    copom = central_bank.ensure(state)
    m = state["metrics"]
    start = macro["start"]
    pb, debt = float(m.get("primary_balance", -1.5)), float(m.get("debt_gdp", 78.0))
    inst, integ = float(m.get("institutional_trust", 58)), float(m.get("integrity", 70))
    real = float(copom["selic"]) - macro["expect"]
    drivers = []
    if pb < -0.5:
        drivers.append(f"Déficit primário de {_n(abs(pb))}% do PIB pressiona o risco-país e o dólar.")
    if debt > 70:
        drivers.append(f"Dívida em {debt:.0f}% do PIB, acima de 70%, encarece o risco-país.")
    if inst < 60:
        drivers.append(f"Confiança nas instituições em {inst:.0f} pontos afasta investidores.")
    if integ < 55:
        drivers.append(f"Integridade do governo em {integ:.0f} pontos pesa no risco-país.")
    if real > NEUTRAL_REAL + 1:
        drivers.append(f"Juro real de {_n(real)}% a.a., acima do neutro, segura inflação e atividade e valoriza o real.")
    elif real < NEUTRAL_REAL - 1:
        drivers.append(f"Juro real de {_n(real)}% a.a., abaixo do neutro, estimula atividade e pressiona inflação e câmbio.")
    if copom.get("credibility", 70) < 55:
        drivers.append("A credibilidade do Banco Central está baixa: expectativas de inflação sobem.")
    if not drivers:
        drivers.append("Contas, juros e instituições estão perto do equilíbrio: o mercado anda de lado.")
    def row(key, label, unit, value, start_value, better):
        return {"id": key, "label": label, "unit": unit, "value": round(value, 3), "start": round(start_value, 3), "change": round(value - start_value, 3),
                "change_pct": round((value / start_value - 1) * 100, 2) if start_value else 0.0, "better": better}
    return {"indicators": [row("cambio", "Dólar", "R$", macro["cambio"], start["cambio"], "down"), row("bolsa", "Bolsa (índice)", "pontos", macro["bolsa"], start["bolsa"], "up"),
                           row("selic", "Selic", "% a.a.", copom["selic"], start["selic"], "down"), row("risco", "Risco-país", "pontos", macro["risco"], start["risco"], "down"),
                           row("expect", "Expectativa de inflação", "% a.a.", macro["expect"], start["expect"], "down")],
            "confianca": round(macro["confianca"], 1), "real_rate": round(real, 2), "drivers": drivers, "history": macro["history"], "news": macro["news"][:15],
            "note": "Mercado simulado: coeficientes de design, não previsões. O dólar, a bolsa e o risco-país reagem na hora às suas decisões e seguem as contas públicas, os juros e a confiança."}
