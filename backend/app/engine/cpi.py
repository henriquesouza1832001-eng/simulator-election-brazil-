"""CPI em etapas: requerimento, instalação, oitivas, relatório final e encaminhamento.

Dois caminhos: (1) a CPI que o jogador instala como parlamentar (ações v_cpi, de_cpi, df_cpi), cujo resultado afeta a reputação
dele; (2) a CPI que a oposição abre contra o governo quando a integridade está baixa, que o jogador enfrenta com decisões.
Base: CF art. 58, §3º (um terço dos membros, fato determinado, prazo certo; conclusões vão ao Ministério Público).
Tudo é simulação: os convocados são cargos (ministro, ex-assessor, empresário), nunca pessoas reais.
"""
from __future__ import annotations

import hashlib
from datetime import date, timedelta
from typing import Any

from . import consequences, ledger

# dias desde o requerimento até cada etapa
OFFSETS = {"Requerimento": 0, "Instalação": 21, "Oitiva 1": 45, "Oitiva 2": 70, "Oitiva 3": 95, "Relatório final": 125, "Encaminhamento": 150}
WITNESSES = ["um ex-assessor do gabinete", "o secretário-executivo responsável", "o presidente de uma empresa contratada", "um auditor do tribunal de contas", "o ministro da área"]
SCOPE_NAME = {"vereador": "Câmara Municipal", "deputado_estadual": "Assembleia Legislativa", "deputado_federal": "Câmara dos Deputados", "senador": "Senado Federal",
              "presidente": "Congresso Nacional", "governador": "Assembleia Legislativa", "prefeito": "Câmara Municipal"}
MONTHLY_CHANCE = 0.10


def _roll(seed: str) -> float:
    return int(hashlib.sha256(seed.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF


def _st(state: dict[str, Any]) -> list[dict[str, Any]]:
    return state.setdefault("cpis", [])


def _stages(start: date) -> list[dict[str, Any]]:
    return [{"name": n, "date": (start + timedelta(days=d)).isoformat(), "status": "concluída" if d == 0 else "pendente"} for n, d in OFFSETS.items()]


def _integrity(state: dict[str, Any]) -> float:
    career = state.get("career") or {}
    if career.get("mode") and career.get("office") != "presidente":
        return float(career.get("reputation", 60))
    return float(state.get("metrics", {}).get("integrity", 70))


def _gov(state: dict[str, Any]) -> dict[str, Any] | None:
    career = state.get("career") or {}
    return career.get("governance") if career.get("mode") else None


def open_cpi(state: dict[str, Any], *, subject: str, author: str, severity: float = 0.5, office: str | None = None) -> dict[str, Any]:
    """author: 'jogador' (ele instalou) ou 'oposicao' (mira o governo dele)."""
    today = date.fromisoformat(state["date"])
    cpis = _st(state)
    office = office or (state.get("career") or {}).get("office") or "presidente"
    cpi = {"id": f"cpi-{len(cpis) + 1}-{state['date']}", "subject": subject, "author": author, "severity": round(severity, 2), "house": SCOPE_NAME.get(office, "Congresso Nacional"),
           "status": "em andamento", "opened": state["date"], "seed": f"{state.get('campaign_seed', 1)}:{len(cpis)}:{subject}", "stages": _stages(today), "findings": 0, "log": []}
    cpis.append(cpi)
    cpi["log"].append({"date": state["date"], "text": f"Requerimento de CPI sobre {subject} protocolado na {cpi['house']} com as assinaturas de um terço dos membros."})
    consequences._post(consequences._book(state), state, {"id": f"{cpi['id']}-req", "kind": "congresso", "headline": f"CPI sobre {subject}: requerimento protocolado",
                                                           "body": "Simulação.", "tone": "negativo" if author == "oposicao" else "neutro", "action_id": "cpi"})
    return cpi


def _news(state: dict[str, Any], cpi: dict[str, Any], suffix: str, text: str, tone: str = "negativo") -> None:
    cpi["log"].append({"date": state["date"], "text": text})
    consequences._post(consequences._book(state), state, {"id": f"{cpi['id']}-{suffix}", "kind": "congresso", "headline": text, "body": "Simulação.", "tone": tone, "action_id": "cpi"})


def _bump(state: dict[str, Any], effects: dict[str, float]) -> None:
    m = state.setdefault("metrics", {})
    gov = _gov(state)
    for key, value in effects.items():
        if key in ("trust",) and gov is not None:
            gov["trust"] = round(max(0.0, min(100.0, float(gov.get("trust", 50)) + value)), 2)
        elif key == "reputation" and (state.get("career") or {}).get("mode"):
            c = state["career"]
            c["reputation"] = round(max(0.0, min(100.0, float(c.get("reputation", 50)) + value)), 2)
        elif key in m:
            m[key] = round(max(0.0, min(100.0, float(m[key]) + value)), 2)


def _step(state: dict[str, Any], cpi: dict[str, Any], stage: dict[str, Any], after: date) -> list[str]:
    name = stage["name"]
    opp = cpi["author"] == "oposicao"
    seed = f"{cpi['seed']}:{name}"
    msgs: list[str] = []
    if name == "Instalação":
        p_install = 0.85 if not opp else max(0.35, 0.95 - float((state.get("metrics") or {}).get("governability", 50)) / 100 * 0.6)
        if _roll(seed) < p_install:
            stage["status"] = "concluída"
            _news(state, cpi, "inst", f"CPI sobre {cpi['subject']} instalada na {cpi['house']}; o relator foi escolhido.")
            msgs.append(f"CPI sobre {cpi['subject']} foi instalada.")
        else:
            stage["status"] = "barrada"
            cpi["status"] = "barrada"
            _news(state, cpi, "bar", f"CPI sobre {cpi['subject']} barrada antes da instalação.", "neutro")
            for later in cpi["stages"]:
                if later["status"] == "pendente":
                    later["status"] = "cancelada"
            msgs.append(f"CPI sobre {cpi['subject']} foi barrada antes da instalação.")
    elif name.startswith("Oitiva"):
        who = WITNESSES[int(_roll(seed + "w") * len(WITNESSES)) % len(WITNESSES)]
        hit = _roll(seed) < max(0.15, min(0.85, (100 - _integrity(state)) / 100 + cpi["severity"] * 0.3))
        stage["status"] = "concluída"
        if hit:
            cpi["findings"] += 1
            _news(state, cpi, name, f"Oitiva de {who} na CPI sobre {cpi['subject']} traz indícios que a oposição explora.")
            if opp:
                _bump(state, {"approval": -0.8})
        else:
            _news(state, cpi, name, f"Oitiva de {who} na CPI sobre {cpi['subject']} termina sem fatos novos.", "neutro")
        if opp and name == "Oitiva 2":
            consequences.open_crisis(
                state, crisis_id=f"{cpi['id']}-resp", action_id="cpi", today=after, deadline_days=30, title=f"CPI sobre {cpi['subject']}: como o governo reage?",
                text="As oitivas esquentaram o debate. A base pede uma linha de defesa antes do relatório final.",
                options=[{"id": "colaborar", "label": "Colaborar: entregar documentos e enviar os convocados", "effects": {"integrity": 1.5, "congress_support": -1.0}, "hook": {"cpi": cpi["id"], "option": "colaborar"}},
                         {"id": "base", "label": "Mobilizar a base para limitar o relatório", "effects": {"congress_support": -2.0, "governability": -1.0}, "hook": {"cpi": cpi["id"], "option": "base"}},
                         {"id": "silencio", "label": "Não comentar", "effects": {"approval": -1.0, "integrity": -1.0}}])
    elif name == "Relatório final":
        stage["status"] = "concluída"
        strength = cpi["findings"] / 3
        guilty = _roll(seed) < min(0.9, 0.15 + strength * 0.5 + (100 - _integrity(state)) / 250 + cpi.get("pressure", 0.0))
        cpi["verdict"] = "pede indiciamentos" if guilty else "sem indiciamentos"
        if opp:
            _bump(state, {"approval": -2.5, "integrity": -2.0} if guilty else {"approval": 0.5})
            _news(state, cpi, "rel", f"Relatório final da CPI sobre {cpi['subject']} {'pede indiciamentos' if guilty else 'não pede indiciamentos'}.", "negativo" if guilty else "neutro")
        else:
            _bump(state, {"reputation": 3.0, "trust": 0.8} if guilty else {"reputation": -1.5})
            _news(state, cpi, "rel", f"Relatório final da CPI que você instalou sobre {cpi['subject']} {'pede indiciamentos' if guilty else 'fica sem conclusões fortes'}.", "positivo" if guilty else "neutro")
    elif name == "Encaminhamento":
        stage["status"] = "concluída"
        cpi["status"] = "concluída"
        if cpi.get("verdict") == "pede indiciamentos":
            _news(state, cpi, "enc", f"Conclusões da CPI sobre {cpi['subject']} seguem ao Ministério Público e à Polícia Federal.")
            if opp:
                from . import regulators
                r = regulators._st(state)
                r["decisions"].insert(0, {"id": f"{cpi['id']}-mp", "regulator": "pf_mp", "title": f"Inquérito a partir da CPI: {cpi['subject']}", "status": "aberto", "decided": after.isoformat()})
                msgs.append("O relatório da CPI foi encaminhado ao MP e à PF.")
        else:
            _news(state, cpi, "enc", f"CPI sobre {cpi['subject']} encerrada e arquivada.", "neutro")
    return msgs


def _opposition_trigger(state: dict[str, Any], after: date) -> list[str]:
    career = state.get("career") or {}
    if career.get("mode") and career.get("office") not in ("presidente", "governador", "prefeito"):
        return []
    if career.get("mode") and not career.get("phase") == "office":
        return []
    if any(c["author"] == "oposicao" and c["status"] == "em andamento" for c in _st(state)):
        return []
    month = after.isoformat()[:7]
    integrity = _integrity(state)
    if integrity >= 60 or _roll(f"{state.get('campaign_seed', 1)}:cpi:{month}") >= MONTHLY_CHANCE * (60 - integrity) / 30:
        return []
    subjects = ["contratos do governo", "gastos de publicidade", "obras paralisadas", "emendas e repasses"]
    subject = subjects[int(_roll(f"{month}:subj") * len(subjects)) % len(subjects)]
    cpi = open_cpi(state, subject=subject, author="oposicao", severity=min(1.0, (60 - integrity) / 40), office=career.get("office") if career.get("mode") else "presidente")
    return [f"A oposição pediu uma CPI sobre {subject}."]


def tick(state: dict[str, Any], before: date, after: date) -> list[str]:
    msgs: list[str] = []
    if state.get("setup_pending"):
        return msgs
    for cpi in _st(state):
        if cpi["status"] != "em andamento":
            continue
        for stage in cpi["stages"]:
            when = date.fromisoformat(stage["date"])
            if stage["status"] == "pendente" and before < when <= after:
                msgs.extend(_step(state, cpi, stage, after))
                if cpi["status"] != "em andamento":
                    break
    msgs.extend(_opposition_trigger(state, after))
    return msgs


def apply_response(state: dict[str, Any], cpi_id: str, option_id: str) -> None:
    """Resposta do jogador: 'colaborar' reduz a pressão do relatório; 'base' também, mas com custo político."""
    for cpi in _st(state):
        if cpi["id"] == cpi_id:
            cpi["pressure"] = {"colaborar": -0.25, "base": -0.15}.get(option_id, 0.05)
            cpi["log"].append({"date": state["date"], "text": f"Resposta do governo: {option_id}."})


def overview(state: dict[str, Any]) -> dict[str, Any]:
    return {"cpis": list(reversed(_st(state))),
            "note": "CF art. 58, §3º: a CPI tem poderes de investigação, prazo certo e fato determinado; só pode concluir e encaminhar ao Ministério Público. As oitivas e os resultados aqui são simulados."}
