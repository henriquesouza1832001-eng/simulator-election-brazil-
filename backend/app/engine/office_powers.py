"""Ações executáveis dos cargos locais e legislativos (vereador a senador), com custo, previsão e resultado.

Executivos (prefeito, governador) gastam reserva do cargo; legislativos gastam capital político e dependem de
votação simulada determinística. Efeitos atingem confiança, reputação e indicadores do território (cidade ou estado).
Usa a mesma agenda de 30 dias de `perform_governance_action`.
"""
from __future__ import annotations

import hashlib
from datetime import date
from typing import Any

from .career import is_career_governing, _clamp  # noqa: F401
from . import ledger, subnational_fiscal
from .indicator_registry import REGISTRY

# kind: exec (reserva) | leg (capital político); cost: fração da reserva (exec) ou pontos de capital (leg)
_A: list[dict[str, Any]] = []


def _a(id: str, offices: list[str], title: str, kind: str, basis: str, text: str, cost: float, effects: dict[str, float], territory: dict[str, float],
       scope: str = "city", domain: str = "geral", p: float = 0.6, fiscal: dict[str, float] | None = None, spend: str = "programa") -> None:
    _A.append({"id": id, "offices": offices, "title": title, "kind": kind, "basis": basis, "text": text, "cost": cost, "effects": effects,
               "territory": territory, "scope": scope, "domain": domain, "p": p, "fiscal": fiscal or {}, "spend": spend})


V, P, DE, G, DF, S = "vereador", "prefeito", "deputado_estadual", "governador", "deputado_federal", "senador"
# ---------------- Vereador
_a("v_creches", [V], "Emenda para ampliar vagas em creches", "leg", "CF art. 30, I e VI; art. 208, IV", "Emenda ao orçamento municipal destinada à educação infantil.", 12, {"trust": 1.2}, {"educacao_fundamental": 0.4, "idhm_educacao": 0.001}, domain="educacao", p=0.62)
_a("v_ubs", [V], "Emenda para unidades de saúde", "leg", "CF art. 30, VII", "Reforça a atenção básica da cidade.", 12, {"trust": 1.2}, {"saude_atencao": 1.5}, domain="saude", p=0.6)
_a("v_onibus_noturno", [V], "Lei do transporte coletivo noturno", "leg", "CF art. 30, V", "Obriga linhas noturnas em corredores de grande demanda.", 14, {"trust": 1.0}, {"mobilidade": 1.2}, domain="mobilidade", p=0.5)
_a("v_iluminacao", [V], "Emenda de iluminação pública", "leg", "CF art. 149-A (COSIP); art. 30, V", "Amplia a iluminação em vias com maior risco.", 10, {"trust": 0.8}, {"seguranca": 1.2}, domain="seguranca", p=0.65)
_a("v_cpi", [V], "Instalar CPI do transporte", "leg", "CF art. 58, §3º (por simetria); Lei Orgânica", "Investiga contratos e tarifa do transporte coletivo.", 18, {"trust": 0.8, "reputation": 2.5}, {}, domain="fiscalizacao", p=0.45)
_a("v_convocar", [V], "Convocar secretário municipal", "leg", "Lei Orgânica; CF art. 31", "Cobra metas e prazos de uma secretaria.", 6, {"trust": 0.8, "reputation": 1.0}, {}, domain="fiscalizacao", p=0.8)
# ---------------- Prefeito
_a("p_recapear", [P], "Recapear e abrir vias", "exec", "CF art. 30, V", "Pavimentação e corredores locais.", 0.12, {"trust": 1.4}, {"mobilidade": 2.0}, domain="mobilidade")
_a("p_ubs", [P], "Ampliar unidades de saúde", "exec", "CF art. 30, VII", "Mais equipes de saúde da família e farmácia.", 0.14, {"trust": 1.6}, {"saude_atencao": 3.0, "mortalidade_infantil": -0.4}, domain="saude")
_a("p_creches", [P], "Construir creches", "exec", "CF art. 208, IV", "Vagas na educação infantil.", 0.12, {"trust": 1.5}, {"educacao_fundamental": 0.8, "desemprego": -0.15}, domain="educacao")
_a("p_esgoto", [P], "Ampliar coleta e esgoto", "exec", "Lei 14.026/2020; CF art. 30, V", "Redes de água e esgoto por concessão ou obra própria.", 0.2, {"trust": 1.2}, {"saneamento_basico": 2.5, "agua_encanada": 1.0, "esgoto_inadequado": -2.0}, domain="saneamento")
_a("p_guarda", [P], "Fortalecer guarda municipal e iluminação", "exec", "CF art. 144, §8º", "Protege bens e serviços; não faz policiamento ostensivo.", 0.08, {"trust": 1.0}, {"seguranca": 2.0}, domain="seguranca")
_a("p_onibus", [P], "Renovar concessão do ônibus", "exec", "CF art. 175; Lei 8.987/1995", "Nova licitação com metas de frota e tarifa.", 0.05, {"trust": 0.6}, {"mobilidade": 2.5}, domain="mobilidade")
_a("p_habitacao", [P], "Programa de habitação popular", "exec", "CF art. 182 e 23, IX", "Moradias e regularização fundiária.", 0.18, {"trust": 1.6}, {"adensamento": -1.5, "gini": -0.002}, domain="saneamento")
_a("p_iptu", [P], "Reajustar o IPTU", "exec", "CF art. 156, I; art. 150, III", "Aumenta a receita; custa popularidade.", -0.15, {"trust": -3.0}, {}, domain="fiscal")
_a("p_reajuste", [P], "Reajustar o salário dos servidores", "exec", "CF art. 37, X; LRF art. 20 e 22", "Aumenta a folha (LRF: acima do limite prudencial, não pode).", 0.0,
   {"trust": 2.2}, {}, domain="fiscal", fiscal={"personnel": 2.5}, spend="pessoal")
_a("p_concurso", [P], "Abrir concurso para saúde e educação", "exec", "CF art. 37, II; LRF art. 20", "Contrata equipes; amplia a folha de forma permanente.", 0.05,
   {"trust": 1.4}, {"saude_atencao": 1.5, "educacao_fundamental": 0.4}, domain="saude", fiscal={"personnel": 1.6}, spend="pessoal")
_a("p_reduzir_folha", [P], "Reduzir despesa com pessoal", "exec", "LRF art. 23 (recondução ao limite)", "Corta cargos em comissão e gratificações; custa popularidade.", 0.0,
   {"trust": -2.0}, {}, domain="fiscal", fiscal={"personnel": -2.5})
_a("p_credito", [P], "Contratar operação de crédito", "exec", "LRF art. 32; Res. Senado 43/2001", "Antecipa recursos para obras; aumenta a dívida.", 0.0,
   {"trust": 0.4}, {}, domain="fiscal", fiscal={"debt": 8.0, "reserve_pct": 0.2}, spend="credito")
_a("g_reajuste", [G], "Reajustar o salário dos servidores", "exec", "CF art. 37, X; LRF art. 20 e 22", "Aumenta a folha estadual.", 0.0,
   {"trust": 2.2}, {}, "uf", "fiscal", fiscal={"personnel": 2.0}, spend="pessoal")
_a("g_reduzir_folha", [G], "Reduzir despesa com pessoal", "exec", "LRF art. 23", "Recondução da folha ao limite.", 0.0,
   {"trust": -2.0}, {}, "uf", "fiscal", fiscal={"personnel": -2.0})
_a("g_credito", [G], "Contratar operação de crédito", "exec", "LRF art. 32; Res. Senado 43/2001", "Financia obras; aumenta a dívida estadual.", 0.0,
   {"trust": 0.4}, {}, "uf", "fiscal", fiscal={"debt": 12.0, "reserve_pct": 0.2}, spend="credito")
# ---------------- Deputado estadual
_a("de_lei_estadual", [DE], "Lei estadual de ensino integral", "leg", "CF art. 24, IX e 25", "Amplia escolas de tempo integral no estado.", 14, {"trust": 1.2}, {"educacao_medio": 0.5}, "uf", "educacao", 0.55)
_a("de_saude", [DE], "Emenda para hospital regional", "leg", "CF art. 25 e 196", "Direciona recursos a um hospital do interior.", 14, {"trust": 1.4}, {"saude_atencao": 0.8}, "uf", "saude", 0.55)
_a("de_cpi", [DE], "CPI de contratos estaduais", "leg", "CF art. 58, §3º (por simetria)", "Investiga contratos do governo estadual.", 18, {"trust": 0.8, "reputation": 2.5}, {}, "uf", "fiscalizacao", 0.45)
_a("de_sustar", [DE], "Sustar decreto do governador", "leg", "CF art. 49, V (por simetria)", "Quando o ato excede o poder regulamentar.", 20, {"reputation": 2.0}, {}, "uf", "fiscalizacao", 0.35)
# ---------------- Governador
_a("g_rodovia", [G], "Duplicar rodovia estadual", "exec", "CF art. 25; Lei 14.133/2021", "Obra estadual com licitação.", 0.2, {"trust": 1.5}, {"mobilidade": 1.2, "logistica": -0.5}, "uf", "mobilidade")
_a("g_policia", [G], "Reforçar as polícias estaduais", "exec", "CF art. 144, §6º", "Efetivo, viaturas e inteligência.", 0.16, {"trust": 1.4}, {"seguranca": 1.8, "homicidios": -0.6}, "uf", "seguranca")
_a("g_hospital", [G], "Hospitais regionais", "exec", "CF art. 25 e 198", "Rede de média e alta complexidade.", 0.18, {"trust": 1.6}, {"saude_atencao": 2.0}, "uf", "saude")
_a("g_escola", [G], "Ensino médio integral", "exec", "CF art. 211, §3º", "Rede estadual de ensino médio.", 0.16, {"trust": 1.4}, {"educacao_medio": 1.0}, "uf", "educacao")
_a("g_concessao", [G], "Conceder rodovia estadual", "exec", "CF art. 175", "Leilão de pedágio com metas de duplicação.", 0.04, {"trust": 0.4}, {"mobilidade": 1.5}, "uf", "mobilidade")
_a("g_icms", [G], "Rever alíquotas do ICMS", "exec", "CF art. 155, II e §2º", "Mais receita; custo político alto.", -0.12, {"trust": -2.5}, {}, "uf", "fiscal")
# ---------------- Deputado federal / Senador
_a("df_emenda", [DF], "Emenda individual ao orçamento", "leg", "CF art. 166, §9º (EC 86/2015)", "Direciona verba a obras e serviços na sua base.", 10, {"trust": 1.4}, {"saude_atencao": 0.6, "mobilidade": 0.4}, "uf", "orcamento", 0.7)
_a("df_projeto", [DF], "Projeto de lei federal", "leg", "CF art. 61", "Projeto de lei em sua área de atuação.", 14, {"trust": 1.0, "reputation": 1.0}, {}, "nation", "legislacao", 0.4)
_a("df_cpi", [DF], "Instalar CPI", "leg", "CF art. 58, §3º", "Um terço dos deputados para investigar fato determinado.", 20, {"reputation": 3.0}, {}, "nation", "fiscalizacao", 0.4)
_a("df_convocar", [DF], "Convocar ministro", "leg", "CF art. 50", "Cobra explicações; ausência é crime de responsabilidade.", 8, {"reputation": 1.5}, {}, "nation", "fiscalizacao", 0.8)
_a("s_sabatina", [S], "Sabatinar autoridade indicada", "leg", "CF art. 52, III e IV", "Questiona indicado ao BC, STF ou embaixada.", 10, {"reputation": 2.0}, {}, "nation", "fiscalizacao", 0.85)
_a("s_resolucao", [S], "Resolução do Senado sobre dívida estadual", "leg", "CF art. 52, V a IX", "Fixa limites de endividamento.", 16, {"trust": 1.0}, {"divida_pib": -0.1}, "uf", "fiscal", 0.5)
_a("s_projeto", [S], "Projeto de lei federal", "leg", "CF art. 61", "Matéria de interesse nacional ou do estado.", 14, {"trust": 1.0, "reputation": 1.0}, {}, "nation", "legislacao", 0.4)
_a("s_emenda", [S], "Emenda de bancada estadual", "leg", "CF art. 166, §12", "Obras de interesse do estado.", 14, {"trust": 1.4}, {"mobilidade": 0.5, "saneamento_basico": 0.5}, "uf", "orcamento", 0.65)

BY_ID = {a["id"]: a for a in _A}
OFFICES = {o for a in _A for o in a["offices"]}


def _governance(state: dict[str, Any]) -> dict[str, Any]:
    career = state.get("career") or {}
    return career.setdefault("governance", {"budget_mi": 0.0, "trust": 50.0, "delivery": 0.0, "political_capital": 50.0, "actions": [], "pipeline": [], "outcomes": {}})


def _wait(state: dict[str, Any], gov: dict[str, Any]) -> int:
    last = gov.get("last_action_date")
    if not last:
        return 0
    return max(0, 30 - (date.fromisoformat(state["date"]) - date.fromisoformat(last)).days)


def _chance(state: dict[str, Any], gov: dict[str, Any], action: dict[str, Any]) -> float:
    capital, trust = float(gov.get("political_capital", 50)), float(gov.get("trust", 50))
    return max(0.1, min(0.95, action["p"] + (capital - 50) / 250 + (trust - 50) / 400))


def catalog(state: dict[str, Any], office: str) -> list[dict[str, Any]]:
    career = state.get("career") or {}
    governing = career.get("mode") and is_career_governing(career, date.fromisoformat(state["date"]))
    gov = _governance(state) if governing else {}
    out = []
    for a in _A:
        if office not in a["offices"]:
            continue
        reason = None
        if not governing:
            reason = "Disponível quando você estiver empossado no cargo."
        elif _wait(state, gov):
            reason = f"A agenda do cargo abre em {_wait(state, gov)} dia(s)."
        elif a["kind"] == "leg" and gov.get("political_capital", 0) < a["cost"]:
            reason = "Capital político insuficiente."
        elif a["kind"] == "exec" and a["cost"] > 0 and float(gov.get("budget_mi", 0)) <= 0:
            reason = "Reserva do cargo insuficiente."
        elif a["kind"] == "exec" and a["spend"] != "programa" and subnational_fiscal.check_can_spend(state, a["spend"]):
            reason = subnational_fiscal.check_can_spend(state, a["spend"])
        row = {"id": a["id"], "title": a["title"], "domain": a["domain"], "instrument": "Votação no plenário" if a["kind"] == "leg" else "Ato do Executivo",
               "approval": "pl" if a["kind"] == "leg" else "decreto", "basis": a["basis"], "summary": a["text"], "options": [], "precedent": None, "cost_bi": 0,
               "effects": {**{k: v for k, v in a["effects"].items()}, **{k: v for k, v in a["territory"].items()}},
               "available": reason is None, "reason": reason, "kind": a["kind"],
               "cost_text": (f"{a['cost']:.0f} pontos de capital político" if a["kind"] == "leg" else (f"{a['cost'] * 100:.0f}% da reserva anual" if a["cost"] > 0 else f"gera receita de {-a['cost'] * 100:.0f}% da reserva"))}
        if governing and a["kind"] == "leg":
            row["chance"] = round(_chance(state, gov, a), 2)
        out.append(row)
    return out


def execute(state: dict[str, Any], action_id: str) -> dict[str, Any]:
    action = BY_ID.get(action_id)
    career = state.get("career") or {}
    if not action or career.get("office") not in action["offices"]:
        raise PermissionError("Esta ação não pertence às atribuições do seu cargo.")
    if not career.get("mode") or not is_career_governing(career, date.fromisoformat(state["date"])):
        raise PermissionError("Você precisa estar empossado para agir neste cargo.")
    gov = _governance(state)
    if _wait(state, gov):
        raise RuntimeError(f"A agenda do cargo abre em {_wait(state, gov)} dia(s).")
    blocked = subnational_fiscal.check_can_spend(state, action["spend"]) if action["spend"] != "programa" else None
    if blocked:
        raise RuntimeError(blocked)
    forecast = {**action["effects"], **action["territory"], **{f"lrf_{k}": v for k, v in action["fiscal"].items()}}
    approved = True
    chance = None
    if action["kind"] == "leg":
        if gov.get("political_capital", 0) < action["cost"]:
            raise RuntimeError("Capital político insuficiente.")
        gov["political_capital"] = round(float(gov["political_capital"]) - action["cost"], 1)
        chance = _chance(state, gov, action)
        roll = int(hashlib.sha256(f"{state.get('campaign_seed', 1)}:{action_id}:{state['date']}".encode()).hexdigest()[:8], 16) / 0xFFFFFFFF
        approved = roll < chance
    else:
        reserve = float(gov.get("budget_mi", 0))
        spend = reserve * action["cost"]
        if action["cost"] > 0 and reserve <= 0:
            raise RuntimeError("Reserva do cargo insuficiente.")
        gov["budget_mi"] = round(reserve - spend, 2)
    applied: dict[str, float] = {}
    if approved:
        for key, value in action["effects"].items():
            if key == "trust":
                gov["trust"] = round(_clamp(float(gov.get("trust", 50)) + value), 2)
            elif key == "reputation":
                career["reputation"] = round(_clamp(float(career.get("reputation", 50)) + value), 2)
            applied[key] = value
        if action["territory"]:
            scope = {"city": f"city:{career.get('municipality_id')}", "uf": f"uf:{career.get('state_code')}", "nation": "nation"}[action["scope"]]
            deltas = state.setdefault("territory", {}).setdefault("deltas", {}).setdefault(scope, {})
            for key, value in action["territory"].items():
                if key in REGISTRY:
                    deltas[key] = round(deltas.get(key, 0.0) + value, 5)
                    applied[key] = value
    else:
        gov["trust"] = round(_clamp(float(gov.get("trust", 50)) - 0.8), 2)
        applied["trust"] = -0.8
    if approved and action["fiscal"]:
        for key, value in subnational_fiscal.apply(state, **action["fiscal"]).items():
            if value:
                applied[f"lrf_{key}"] = value
    gov["last_action_date"] = state["date"]
    entry = {"id": f"office-{state['date']}-{len(gov.get('actions', [])) + 1}", "date": state["date"], "action": action_id, "title": action["title"],
             "summary": ("Aprovado no plenário." if approved else "Rejeitado no plenário; capital político gasto.") if action["kind"] == "leg" else "Executado.",
             "forecast": forecast, "result": applied, "approved": approved, "chance": chance, "status": "active", "simulated": True}
    gov.setdefault("actions", []).append(entry)
    gov["actions"] = gov["actions"][-50:]
    led = ledger.record(state, "cargo", action["title"], forecast, applied, status="aprovado" if approved else "rejeitado",
                        cost=(f"{action['cost']:.0f} pontos de capital político" if action["kind"] == "leg" else f"{action['cost'] * 100:.0f}% da reserva"),
                        reason=ledger.explain_gap(forecast, applied, approved if action["kind"] == "leg" else None))
    return {"ledger_id": led["id"], "approved": approved, "chance": chance, "forecast": forecast, "result": applied, "entry": entry,
            "message": f"{action['title']}: {'aprovado' if approved else 'rejeitado'}." if action["kind"] == "leg" else f"{action['title']}: executado."}
