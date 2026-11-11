"""Aplicação das competências: quem pode o quê, com qual aprovação e quais efeitos."""
from __future__ import annotations

import random
from datetime import date, timedelta
from typing import Any

from .fiscal import ensure_fiscal_state, record_one_off_spending, record_policy_balance_delta
from .powers_catalog import ACTIONS, OTHER_OFFICE_ACTIONS, ROLES

BY_ID = {a["id"]: a for a in ACTIONS}

DEFAULT_STRUCTURE: dict[str, Any] = {
    "central_bank": "autonomo_lei",
    "currency": "real",
    "guns": "restrito",
    "police_model": "dual",
    "government_system": "presidencialismo",
    "reelection": "permitida",
    "nuclear": "civil",
    "alcantara": "restrito",
    "blocs": {"brics": True, "opep": False, "otan": False, "mercosul": True},
    "companies": {"Petrobras": "controle_estatal", "Banco do Brasil": "controle_estatal", "Caixa Econômica Federal": "estatal",
                  "Correios": "estatal", "BNDES": "estatal", "Eletronuclear": "estatal", "Eletrobras": "privada"},
    "done": [],
    "history": [],
}

STRUCTURE_LABELS = {
    "central_bank": {"autonomo_lei": "Autônomo por lei complementar", "autonomo_constitucional": "Autonomia na Constituição", "subordinado": "Subordinado ao governo"},
    "guns": {"restrito": "Controle restrito", "facilitado": "Acesso facilitado", "liberado_por_lei": "Liberado por lei"},
    "police_model": {"dual": "Polícia civil e militar (CF art. 144)", "civil_unificada": "Polícia civil unificada"},
    "government_system": {"presidencialismo": "Presidencialismo", "parlamentarismo": "Parlamentarismo"},
    "currency": {"real": "Real", "sul_americana": "Moeda sul-americana"},
}

METRIC_RANGES = {"approval": (0, 100), "institutional_trust": (0, 100), "integrity": (0, 100), "governability": (0, 100),
                 "congress_support": (0, 100), "gdp_growth": (-10, 15), "inflation": (-2, 80), "unemployment": (0, 40)}


def structure(state: dict[str, Any]) -> dict[str, Any]:
    st = state.setdefault("structure", {})
    for key, value in DEFAULT_STRUCTURE.items():
        if key not in st:
            st[key] = {k: v for k, v in value.items()} if isinstance(value, dict) else (list(value) if isinstance(value, list) else value)
    return st


def _get(state: dict[str, Any], path: str) -> Any:
    node: Any = state if not path.startswith("structure.") else structure(state)
    parts = path.split(".")[1:] if path.startswith("structure.") else path.split(".")
    for part in parts:
        node = node.get(part) if isinstance(node, dict) else None
    return node


def _set(state: dict[str, Any], path: str, value: Any) -> None:
    st = structure(state)
    parts = path.split(".")
    for part in parts[:-1]:
        st = st.setdefault(part, {})
    st[parts[-1]] = value


def _requirements_met(state: dict[str, Any], action: dict[str, Any]) -> str | None:
    for path, op, expected in action["requires"]:
        actual = _get(state, path)
        ok = actual == expected if op == "==" else actual != expected
        if not ok:
            return "Não se aplica à situação atual do país."
    return None


def status(state: dict[str, Any], action: dict[str, Any], option: str | None = None) -> dict[str, Any]:
    """Diz se a ação pode ser tentada agora e por quê."""
    if action["approval"] == "blocked":
        return {"available": False, "reason": action["blocked"]}
    reason = _requirements_met(state, action)
    if reason:
        return {"available": False, "reason": reason}
    st = structure(state)
    key = f"{action['id']}:{option}" if option else action["id"]
    if option and key in st["done"]:
        return {"available": False, "reason": "Já foi feito para este item."}
    if not option and not action["options"] and action["id"] in st["done"] and action["sets"]:
        return {"available": False, "reason": "Já está em vigor."}
    return {"available": True, "reason": None}


def catalog_for(state: dict[str, Any], office: str, governing: bool) -> dict[str, Any]:
    role = ROLES.get(office, ROLES["eleitor"])
    out: dict[str, Any] = {"office": office, "role": role, "executable": office == "presidente" and governing}
    if office == "presidente":
        out["actions"] = [{**{k: a[k] for k in ("id", "title", "domain", "instrument", "approval", "basis", "summary", "options", "precedent", "cost_bi")},
                           **status(state, a), "effects": a["effects"]} for a in ACTIONS]
        st = structure(state)
        out["structure"] = {k: {"value": st[k], "label": STRUCTURE_LABELS[k].get(st[k], str(st[k]))} for k in STRUCTURE_LABELS}
        out["blocs"] = st["blocs"]
        out["companies"] = st["companies"]
        out["history"] = st["history"][:15]
    else:
        from . import office_powers
        out["actions"] = office_powers.catalog(state, office) if office in office_powers.OFFICES else []
        out["executable"] = governing and bool(out["actions"])
        out["reference"] = [] if out["actions"] else OTHER_OFFICE_ACTIONS.get(office, [])
    return out


def _bump(state: dict[str, Any], key: str, delta: float) -> float:
    metrics = state["metrics"]
    low, high = METRIC_RANGES[key]
    before = float(metrics.get(key, 0))
    metrics[key] = round(max(low, min(high, before + delta)), 2)
    return metrics[key] - before


def apply(state: dict[str, Any], action: dict[str, Any], option: str | None, *, revertible: bool = False) -> list[dict[str, Any]]:
    """Aplica efeitos, custo e mudanças estruturais. Retorna a lista de variações registradas."""
    ensure_fiscal_state(state)
    rows: list[dict[str, Any]] = []
    for key, delta in action["effects"].items():
        if key == "primary_balance":
            record_policy_balance_delta(state, delta)
            rows.append({"key": key, "delta": delta})
        elif key == "military_loyalty":
            inst = state.setdefault("institutions", {})
            inst[key] = round(max(0, min(100, float(inst.get(key, 60)) + delta)), 2)
            rows.append({"key": key, "delta": delta})
        elif key in METRIC_RANGES:
            rows.append({"key": key, "delta": round(_bump(state, key, delta), 2)})
    if action["cost_bi"]:
        record_one_off_spending(state, float(action["cost_bi"]))
        rows.append({"key": "cost_bi", "delta": float(action["cost_bi"])})
    st = structure(state)
    for path, value in action["sets"].items():
        _set(state, path, value)
    if option:
        st["done"].append(f"{action['id']}:{option}")
        if action["id"] in {"empresa_privatizar"}:
            st["companies"][option] = "privada"
        if action["id"] in {"empresa_estatizar"}:
            st["companies"][option] = "estatal"
    elif action["sets"]:
        st["done"].append(action["id"])
    st["history"].insert(0, {"date": state.get("date"), "id": action["id"], "title": action["title"] + (f" — {option}" if option else "")})
    del st["history"][40:]
    return rows


def _bill(state: dict[str, Any], action: dict[str, Any], option: str | None, today: date) -> dict[str, Any]:
    calendar = state["legislative_calendar"]
    instrument = action["instrument"]
    days = 150 if action["approval"] in {"pec", "plp"} else 90
    number = int(calendar.get("laws_enacted", 0)) + int(calendar.get("laws_failed", 0)) + len(calendar.get("pending_bills", [])) + 1
    kind = "pec" if action["approval"] == "pec" else ("projeto de lei complementar" if action["approval"] == "plp" else "projeto de lei")
    title = action["title"] + (f" — {option}" if option else "")
    bill = {"id": f"bill-{today.isoformat()}-{number}", "title": title, "instrument": {"pec": "PEC", "projeto de lei complementar": "Projeto de Lei Complementar"}.get(kind, "Projeto de Lei"),
            "submitted_date": today.isoformat(), "decision_date": (today + timedelta(days=days)).isoformat(), "status": "em tramitação",
            "interpretation": {"title": title, "category": action["axis"], "instrument": instrument, "fiscal_cost_bi": max(0.0, float(action["cost_bi"]))},
            "power_id": action["id"], "power_option": option, "simulated": True}
    calendar["last_submission"] = today.isoformat()
    calendar["cooldown_days"] = 180 if action["approval"] == "pec" else 60
    calendar.setdefault("pending_bills", []).append(bill)
    return bill


def execute(state: dict[str, Any], action_id: str, option: str | None = None) -> dict[str, Any]:
    action = BY_ID.get(action_id)
    if action is None:
        raise ValueError("Ação desconhecida.")
    if action["options"] and option not in action["options"]:
        raise ValueError("Escolha uma das opções da ação.")
    if not action["options"]:
        option = None
    info = status(state, action, option)
    if not info["available"]:
        raise PermissionError(info["reason"])
    today = date.fromisoformat(state["date"])
    approval = action["approval"]
    if approval in {"decreto", "mp"}:
        calendar = state.setdefault("executive_calendar", {"last_action": None})
        cooldown = 30 if approval == "mp" else 7
        last = calendar.get("last_action")
        if last and (today - date.fromisoformat(last)).days < cooldown:
            raise RuntimeError(f"A agenda administrativa já foi usada. Aguarde {cooldown - (today - date.fromisoformat(last)).days} dia(s).")
        calendar["last_action"] = today.isoformat()
        calendar["cooldown_days"] = cooldown
        effects = apply(state, action, option)
        message = f"{action['title']}: em vigor desde hoje."
        if approval == "mp":
            bill = _bill(state, action, option, today)
            bill["status"] = "medida provisória — conversão em lei"
            bill["decision_date"] = (today + timedelta(days=120)).isoformat()
            bill["power_revert"] = True
            message += " A medida provisória precisa ser convertida em lei em até 120 dias."
        return {"status": "applied", "effects": effects, "message": message}
    # pl, plp, pec, tratado: precisam do Congresso
    calendar = state["legislative_calendar"]
    last = calendar.get("last_submission")
    interval = 180 if approval == "pec" else 60
    if last and (today - date.fromisoformat(last)).days < interval:
        raise RuntimeError(f"A pauta legislativa já tem proposta recente. Aguarde {interval - (today - date.fromisoformat(last)).days} dia(s).")
    bill = _bill(state, action, option, today)
    return {"status": "pending_legislature", "effects": [], "decision_date": bill["decision_date"],
            "message": f"{action['title']} foi enviado ao Congresso; a votação simulada será em {bill['decision_date']}."}


def resolve_bill(state: dict[str, Any], bill: dict[str, Any], approved: bool) -> list[dict[str, Any]] | None:
    """Chamado pela tramitação quando um projeto de competência é votado."""
    action = BY_ID.get(bill.get("power_id", ""))
    if action is None:
        return None
    option = bill.get("power_option")
    if bill.get("power_revert"):
        if not approved:
            for path in action["sets"]:
                default = _default_for(path)
                _set(state, path, default)
            st = structure(state)
            st["done"] = [d for d in st["done"] if not d.startswith(action["id"])]
        return []
    if not approved:
        return []
    if action["popular_vote"]:
        rng = random.Random(f"{state.get('campaign_seed', 1)}:popular:{action['id']}")
        support = float(state["metrics"].get("approval", 50)) / 100 * 0.6 + rng.uniform(-0.1, 0.1)
        if rng.random() > support:
            state.setdefault("simulated_news", []).insert(0, {"id": f"plebiscito-{action['id']}", "date": state["date"], "title": "Plebiscito rejeita a mudança", "region": "Nacional",
                                                              "description": f"A população rejeitou, na simulação: {action['title']}."})
            return []
    return apply(state, action, option)


def _default_for(path: str) -> Any:
    node: Any = DEFAULT_STRUCTURE
    for part in path.split("."):
        node = node[part]
    return node
