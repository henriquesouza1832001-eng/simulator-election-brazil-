"""Reguladores: STF, AGU, tribunais de contas, PF/MP e TSE como atores que revisam, limitam e investigam.

Eles não escolhem políticas: avaliam o risco jurídico de cada ato, podem suspendê-lo, auditar obras e contas,
abrir investigações quando a integridade cai e fiscalizar campanhas. Probabilidades e pesos são parâmetros de
design; as bases legais são resumo editorial da Constituição (não é parecer jurídico).
"""
from __future__ import annotations

import hashlib
from datetime import date, timedelta
from typing import Any

from . import ledger

REGULATORS: dict[str, dict[str, Any]] = {
    "stf": {"name": "Supremo Tribunal Federal", "basis": "CF art. 101 a 103-B",
            "role": "Guarda da Constituição: julga ações de inconstitucionalidade (ADI, ADPF) e pode suspender leis, decretos e medidas provisórias.",
            "can": ["Suspender ou anular atos do Executivo e leis", "Julgar o Presidente em crimes comuns (art. 102, I, b)", "Decidir conflitos entre poderes e entes"],
            "cannot": ["Agir sem provocação (ADI exige legitimado)", "Criar despesa ou legislar"]},
    "agu": {"name": "Advocacia-Geral da União", "basis": "CF art. 131",
            "role": "Consultoria jurídica do Executivo: emite parecer sobre o risco jurídico de um ato antes de você assinar e defende o governo no STF.",
            "can": ["Avisar o risco jurídico de cada medida", "Defender atos do governo em juízo"], "cannot": ["Impedir o Presidente de assinar", "Julgar o ato"]},
    "tcu": {"name": "Tribunais de Contas (TCU, TCE, TCM)", "basis": "CF art. 70 a 75; art. 31",
            "role": "Fiscalizam contas, obras e a LRF; podem apontar irregularidades, multar gestores e paralisar contratos.",
            "can": ["Auditar obras e contratos", "Julgar contas de gestores", "Sugerir suspensão de despesas"], "cannot": ["Criar políticas", "Anular lei"]},
    "pf_mp": {"name": "Polícia Federal, CGU e Ministério Público", "basis": "CF art. 127 a 130-A; art. 144, §1º; Lei 12.846/2013",
              "role": "Investigam desvios e acusam. Quando a integridade do governo cai, aumentam as chances de inquérito e denúncia.",
              "can": ["Abrir inquérito e denunciar", "Propor ação civil pública", "Recomendar correções"], "cannot": ["Condenar", "Prender sem decisão judicial"]},
    "tse": {"name": "Tribunal Superior Eleitoral", "basis": "CF art. 118 a 121; LC 64/1990 e LC 135/2010 (Ficha Limpa); Lei 9.504/1997",
            "role": "Regula as eleições: registra candidaturas, fiscaliza propaganda e gastos de campanha, e pode cassar registro ou diploma por abuso.",
            "can": ["Indeferir registro de candidatura", "Multar e punir propaganda irregular", "Cassar diploma por abuso de poder"], "cannot": ["Escolher candidatos", "Alterar resultado sem provas"]},
}

# risco jurídico (0 a 1) por ação presidencial; o padrão depende do instrumento
RISK = {"bc_revogar_autonomia": 0.35, "bc_pressao_juros": 0.02, "bc_moeda_comum": 0.30, "bc_autonomia_constitucional": 0.15, "bc_meta_inflacao": 0.04,
        "defesa_bomba": 0.90, "defesa_glo": 0.15, "defesa_intervencao": 0.30, "defesa_estado_defesa": 0.40, "defesa_guerra": 0.30, "defesa_alcantara": 0.12,
        "seg_armas_afrouxar": 0.35, "seg_armas_restringir": 0.10, "seg_estatuto_alterar": 0.15, "seg_desmilitarizar": 0.25,
        "ext_brics_sair": 0.20, "ext_otan": 0.10, "ext_opep": 0.08, "eco_confisco": 0.70, "eco_mp": 0.15, "eco_desoneracao": 0.18, "eco_salario_minimo": 0.04,
        "empresa_privatizar": 0.25, "empresa_estatizar": 0.20, "empresa_criar": 0.10, "infra_conceder": 0.10, "infra_asfaltar": 0.04, "infra_duplicar": 0.04,
        "reg_forma_governo": 0.50, "reg_reeleicao": 0.20, "reg_ministerios": 0.06}
DEFAULT_RISK = {"decreto": 0.10, "mp": 0.20, "pl": 0.08, "plp": 0.08, "pec": 0.10, "tratado": 0.06}
REASON = {"defesa_bomba": "CF art. 21, XXIII, a: atividade nuclear só para fins pacíficos.",
          "eco_confisco": "CF art. 62, §1º, II: a MP não pode bloquear poupança e ativos; o congelamento pode violar a livre iniciativa (art. 170).",
          "seg_armas_afrouxar": "Decreto que extrapola o Estatuto do Desarmamento pode ser sustado (CF art. 49, V) e questionado no STF.",
          "bc_revogar_autonomia": "Mudar a autonomia do BC por lei complementar é possível, mas contestada por afetar política monetária.",
          "reg_forma_governo": "Mudança de sistema de governo exige plebiscito (ADCT art. 2º); risco de violar cláusula pétrea.",
          "defesa_estado_defesa": "Estado de defesa tem hipóteses estritas (CF art. 136) e controle posterior do Congresso.",
          "defesa_intervencao": "Intervenção federal só nas hipóteses do art. 34 e com aprovação do Congresso (art. 36)."}


def _st(state: dict[str, Any]) -> dict[str, Any]:
    r = state.setdefault("regulators", {})
    r.setdefault("cases", [])
    r.setdefault("decisions", [])
    r.setdefault("last_audit_month", None)
    return r


def court_alignment(state: dict[str, Any]) -> float:
    """Quanto o STF tende a acompanhar o governo (0 a 0,5): cresce com ministros indicados e confirmados pelo jogador."""
    confirmed = len((state.get("government_appointments", {}).get("judiciary", {}) or {}).get("confirmed", []))
    return round(min(0.5, 0.07 * confirmed), 2)


def risk_for(action_id: str, approval: str = "decreto") -> float:
    return RISK.get(action_id, DEFAULT_RISK.get(approval, 0.08))


def opinion(action_id: str, approval: str, state: dict[str, Any] | None = None) -> dict[str, Any]:
    """Parecer da AGU: risco de o ato ser suspenso pelo STF."""
    risk = risk_for(action_id, approval)
    align = court_alignment(state) if state else 0.0
    effective = round(risk * (1 - 0.6 * align), 3)
    level = "alto" if effective >= 0.3 else "médio" if effective >= 0.12 else "baixo"
    return {"level": level, "risk_pct": round(effective * 100), "note": REASON.get(action_id, "Medida sujeita a controle de constitucionalidade (CF art. 102, I, a)."),
            "reviewer": "STF" if effective >= 0.08 else None}


def _roll(seed: str) -> float:
    return int(hashlib.sha256(seed.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF


def schedule_review(state: dict[str, Any], *, action_id: str, approval: str, title: str, ledger_id: str | None,
                    sets: dict[str, Any], effects: dict[str, float]) -> dict[str, Any] | None:
    """Agenda a revisão do ato pelo STF quando o risco justifica; atos de baixo risco não geram processo."""
    risk = risk_for(action_id, approval)
    if risk < 0.08:
        return None
    r = _st(state)
    today = date.fromisoformat(state["date"])
    case = {"id": f"adi-{len(r['cases']) + len(r['decisions']) + 1}-{state['date']}", "regulator": "stf", "action_id": action_id, "title": title,
            "risk": risk, "ledger_id": ledger_id, "sets": dict(sets), "effects": dict(effects), "filed": today.isoformat(),
            "decide_on": (today + timedelta(days=45 + int(_roll(f"{action_id}:{state['date']}:when") * 75))).isoformat(), "status": "em julgamento"}
    r["cases"].append(case)
    return case


def _revert(state: dict[str, Any], case: dict[str, Any]) -> None:
    from . import powers
    from .fiscal import record_policy_balance_delta
    for path in case["sets"]:
        powers._set(state, path, powers._default_for(path))
    st = powers.structure(state)
    st["done"] = [d for d in st["done"] if not d.startswith(case["action_id"])]
    for key, value in case["effects"].items():
        if key == "primary_balance":
            record_policy_balance_delta(state, -value * 0.6)
        elif key in powers.METRIC_RANGES:
            powers._bump(state, key, -value * 0.6)


def tick(state: dict[str, Any], before: date, after: date) -> list[str]:
    r = _st(state)
    messages: list[str] = []
    still = []
    for case in r["cases"]:
        if before < date.fromisoformat(case["decide_on"]) <= after:
            chance = case["risk"] * (1 - 0.6 * court_alignment(state))
            struck = _roll(f"{state.get('campaign_seed', 1)}:{case['id']}") < chance
            m = state.setdefault("metrics", {})
            if struck:
                _revert(state, case)
                m["institutional_trust"] = round(max(0, float(m.get("institutional_trust", 50)) - 1.5), 2)
                m["approval"] = round(max(0, float(m.get("approval", 50)) - 1.0), 2)
                outcome, text = "suspenso", f"O STF suspendeu, na simulação: {case['title']}."
            else:
                m["institutional_trust"] = round(min(100, float(m.get("institutional_trust", 50)) + 0.5), 2)
                outcome, text = "mantido", f"O STF manteve, na simulação: {case['title']}."
            case.update(status=outcome, decided=after.isoformat(), chance_pct=round(chance * 100))
            r["decisions"].insert(0, case)
            del r["decisions"][40:]
            if case.get("ledger_id"):
                ledger.settle(state, case["ledger_id"], {}, outcome if struck else "mantido pelo STF",
                              "Suspenso pelo STF; efeitos revertidos em parte." if struck else "O STF manteve a medida; sem novos efeitos.")
            messages.append(text)
        else:
            still.append(case)
    r["cases"] = still
    messages.extend(_audits(state, after))
    return messages


def _audits(state: dict[str, Any], after: date) -> list[str]:
    """Tribunais de contas e PF/MP: auditorias e inquéritos, uma checagem por mês."""
    r = _st(state)
    month = after.isoformat()[:7]
    if r["last_audit_month"] == month:
        return []
    r["last_audit_month"] = month
    out: list[str] = []
    m = state.get("metrics", {})
    career = state.get("career") or {}
    integrity = float(m.get("integrity", 70)) if not career.get("mode") or career.get("office") == "presidente" else float(career.get("reputation", 60))
    # PF/MP: abre inquérito com mais chance quanto menor a integridade
    chance = max(0.0, (60 - integrity) / 60) * 0.12
    if chance and _roll(f"{state.get('campaign_seed', 1)}:inq:{month}") < chance:
        if "integrity" in m:
            m["integrity"] = round(max(0, float(m["integrity"]) - 2), 2)
        m["approval"] = round(max(0, float(m.get("approval", 50)) - 1.5), 2)
        out.append("PF e Ministério Público abriram inquérito sobre o governo, na simulação; a aprovação caiu.")
        r["decisions"].insert(0, {"id": f"inq-{month}", "regulator": "pf_mp", "title": "Inquérito aberto", "status": "aberto", "decided": after.isoformat()})
    # Tribunais de contas: obras em andamento com custo alto
    projects = [p for p in (state.get("territory", {}).get("projects", [])) if p.get("status") == "em obra"]
    if projects and _roll(f"{state.get('campaign_seed', 1)}:tc:{month}") < 0.10:
        p = projects[int(_roll(f"{month}:pick") * len(projects)) % len(projects)]
        gov = career.get("governance") if career.get("mode") else None
        if gov is not None:
            gov["trust"] = round(max(0.0, float(gov.get("trust", 50)) - 1.0), 2)
        out.append(f"O Tribunal de Contas auditou a obra {p['name']}, na simulação, e apontou ressalvas.")
        r["decisions"].insert(0, {"id": f"tc-{month}", "regulator": "tcu", "title": f"Auditoria: {p['name']}", "status": "com ressalvas", "decided": after.isoformat()})
    del r["decisions"][40:]
    return out


def overview(state: dict[str, Any]) -> dict[str, Any]:
    r = _st(state)
    career = state.get("career") or {}
    tse = None
    if career.get("mode"):
        cr = career.get("conduct_review") or {}
        tse = {"attempts": cr.get("attempts", 0), "detected": cr.get("detected", 0), "vote_penalty": cr.get("vote_penalty", 0.0), "reviewed": cr.get("reviewed", False)}
    items = []
    for key, info in REGULATORS.items():
        row = {"id": key, **info}
        if key == "stf":
            row["alignment"] = court_alignment(state)
            row["open_cases"] = [c for c in r["cases"] if c["regulator"] == "stf"]
        if key == "tse":
            row["conduct"] = tse
        items.append(row)
    return {"regulators": items, "decisions": r["decisions"][:20],
            "note": "Reguladores são atores do jogo com probabilidades de design; as bases legais são um resumo editorial, não parecer jurídico."}
