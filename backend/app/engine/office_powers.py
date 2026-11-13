"""Ações executáveis dos cargos locais e legislativos (vereador a senador), com custo, previsão e resultado.

Executivos (prefeito, governador) gastam reserva do cargo; legislativos gastam capital político e dependem de
votação simulada determinística. Efeitos atingem confiança, reputação e indicadores do território (cidade ou estado).
Usa a mesma agenda de 30 dias de `perform_governance_action`.
"""
from __future__ import annotations

import hashlib
from datetime import date, timedelta
from typing import Any

from .career import is_career_governing, _clamp  # noqa: F401
from . import consequences, ledger, subnational_fiscal
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


DAYS = {"vereador": 45, "deputado_estadual": 60, "deputado_federal": 75, "senador": 90}
CHAMBER = {"vereador": "Câmara Municipal", "deputado_estadual": "Assembleia Legislativa", "deputado_federal": "Câmara dos Deputados", "senador": "Senado"}


def _roll(seed: str) -> float:
    return int(hashlib.sha256(seed.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF


def _relator(state: dict[str, Any], office: str, seed: str) -> dict[str, Any]:
    if office in {"deputado_federal", "senador"}:
        from . import legislature
        house = legislature.composition(state)["camara" if office == "deputado_federal" else "senado"]
        pick = house[int(_roll(seed + "relator") * len(house)) % len(house)]
        return {"name": pick["name"], "party": pick["party"], "state": pick["state"], "real": True}
    return {"name": "Relator(a) da comissão (simulado)", "party": None, "state": None, "real": False}


def _submit_local_bill(state: dict[str, Any], action: dict[str, Any], chance: float, forecast: dict[str, float]) -> dict[str, Any]:
    career = state["career"]
    office = career["office"]
    today = date.fromisoformat(state["date"])
    span = DAYS[office]
    seed = f"{state.get('campaign_seed', 1)}:{action['id']}:{state['date']}"
    p_comm = min(0.97, 0.5 + 0.5 * chance)
    p_plen = min(0.99, chance / p_comm)
    bills = state.setdefault("local_bills", [])
    led = ledger.record(state, "cargo", action["title"], forecast, None, status="em tramitação", cost=f"{action['cost']:.0f} pontos de capital político")
    bill = {"id": f"lb-{len(bills) + 1}-{state['date']}", "action_id": action["id"], "title": action["title"], "office": office, "chamber": CHAMBER[office],
            "submitted": state["date"], "decision_date": (today + timedelta(days=span)).isoformat(), "status": "em tramitação", "chance": chance,
            "p_committee": round(p_comm, 3), "p_plenary": round(p_plen, 3), "relator": _relator(state, office, seed), "ledger_id": led["id"], "seed": seed, "forecast": forecast,
            "stages": [{"name": "Protocolo", "date": state["date"], "committee": False, "status": "concluída"},
                       {"name": "Comissão", "date": (today + timedelta(days=round(span * 0.4))).isoformat(), "committee": True, "status": "pendente"},
                       {"name": f"Plenário ({CHAMBER[office]})", "date": (today + timedelta(days=span)).isoformat(), "committee": False, "status": "pendente"}]}
    bills.append(bill)
    return bill


def _finalize(state: dict[str, Any], action: dict[str, Any], approved: bool, forecast: dict[str, float]) -> dict[str, float]:
    """Aplica (ou nega) os efeitos de uma ação do cargo; usado na execução direta e na votação depois da tramitação."""
    career = state["career"]
    gov = _governance(state)
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
        if action["fiscal"]:
            for key, value in subnational_fiscal.apply(state, **action["fiscal"]).items():
                if value:
                    applied[f"lrf_{key}"] = value
        consequences.schedule(state, action_id=action["id"], title=action["title"], domain=action["domain"], effects=action["effects"], source="cargo", local=True)
    else:
        gov["trust"] = round(_clamp(float(gov.get("trust", 50)) - 0.8), 2)
        applied["trust"] = -0.8
    return applied


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
    if action["kind"] == "leg":
        if gov.get("political_capital", 0) < action["cost"]:
            raise RuntimeError("Capital político insuficiente.")
        gov["political_capital"] = round(float(gov["political_capital"]) - action["cost"], 1)
        chance = _chance(state, gov, action)
        bill = _submit_local_bill(state, action, chance, forecast)
        gov["last_action_date"] = state["date"]
        return {"ledger_id": bill["ledger_id"], "approved": None, "pending": True, "decision_date": bill["decision_date"], "chance": chance, "forecast": forecast, "result": None,
                "message": f"{action['title']} foi protocolado na {bill['chamber']}; votação prevista para {bill['decision_date']}."}
    reserve = float(gov.get("budget_mi", 0))
    if action["cost"] > 0 and reserve <= 0:
        raise RuntimeError("Reserva do cargo insuficiente.")
    gov["budget_mi"] = round(reserve - reserve * action["cost"], 2)
    applied = _finalize(state, action, True, forecast)
    gov["last_action_date"] = state["date"]
    entry = {"id": f"office-{state['date']}-{len(gov.get('actions', [])) + 1}", "date": state["date"], "action": action_id, "title": action["title"], "summary": "Executado.",
             "forecast": forecast, "result": applied, "approved": True, "chance": None, "status": "active", "simulated": True}
    gov.setdefault("actions", []).append(entry)
    gov["actions"] = gov["actions"][-50:]
    led = ledger.record(state, "cargo", action["title"], forecast, applied, status="aprovado", cost=f"{action['cost'] * 100:.0f}% da reserva", reason=ledger.explain_gap(forecast, applied, None))
    return {"ledger_id": led["id"], "approved": True, "chance": None, "forecast": forecast, "result": applied, "entry": entry, "message": f"{action['title']}: executado."}


def local_tick(state: dict[str, Any], before: date, after: date) -> list[str]:
    """Tramitação dos projetos de vereador, deputados e senador: comissão e plenário, com relator."""
    career = state.get("career") or {}
    msgs: list[str] = []
    if not career.get("mode") or career.get("office") not in DAYS:
        return msgs
    for bill in state.get("local_bills", []):
        if bill["status"] != "em tramitação" or bill["office"] != career.get("office"):
            continue
        action = BY_ID[bill["action_id"]]
        for stage in bill["stages"]:
            when = date.fromisoformat(stage["date"])
            if stage["status"] != "pendente" or not (before < when <= after):
                continue
            ok = _roll(f"{bill['seed']}:{stage['name']}") < (bill["p_committee"] if stage["committee"] else bill["p_plenary"])
            rel = bill["relator"]
            who = f" (relator {rel['name']}{', ' + rel['party'] if rel['party'] else ''})" if stage["committee"] else ""
            if stage["committee"]:
                stage["status"] = "aprovada" if ok else "rejeitada"
                _post_news(state, bill, f"{bill['title']}: {'aprovado' if ok else 'rejeitado'} na comissão{who}." + ("" if ok else " O projeto foi arquivado."))
                if not ok:
                    bill["status"] = "rejeitado na comissão"
                    applied = _finalize(state, action, False, bill["forecast"])
                    ledger.settle(state, bill["ledger_id"], applied, "rejeitado na comissão", "Arquivado na comissão; capital político gasto.")
                    msgs.append(f"{bill['title']} foi arquivado na comissão.")
                    break
            else:
                stage["status"] = "aprovada" if ok else "rejeitada"
                applied = _finalize(state, action, ok, bill["forecast"])
                bill["status"] = "aprovado" if ok else "rejeitado no plenário"
                ledger.settle(state, bill["ledger_id"], applied, bill["status"], ledger.explain_gap(bill["forecast"], applied, ok))
                _post_news(state, bill, f"{bill['title']}: {'aprovado' if ok else 'rejeitado'} no plenário da {bill['chamber']}.")
                msgs.append(f"{bill['title']} foi {'aprovado' if ok else 'rejeitado'} no plenário.")
    return msgs


def _post_news(state: dict[str, Any], bill: dict[str, Any], text: str) -> None:
    book = consequences._book(state)
    consequences._post(book, state, {"id": f"lt-{bill['id']}-{len(book['feed'])}", "kind": "congresso", "headline": text, "body": "Tramitação simulada.", "tone": "neutro", "action_id": bill["action_id"]})
