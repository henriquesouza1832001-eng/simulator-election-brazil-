"""Pauta própria do Congresso: projetos que chegam à sanção e o ciclo veto, derrubada ou manutenção do veto.

Todo mês há chance de o Congresso aprovar um projeto de iniciativa parlamentar. O Presidente tem 15 dias úteis
(aqui, 21 dias corridos) para sancionar, vetar parcialmente ou vetar totalmente (CF art. 66). Se não responder, vale
a sanção tácita. Um veto volta ao plenário: derrubá-lo exige maioria absoluta das duas casas (257 deputados e 41
senadores), resolvida na votação nominal simulada. Os textos são genéricos (sem nomes de leis reais); efeitos são
parâmetros de design.
"""
from __future__ import annotations

import hashlib
from datetime import date, timedelta
from typing import Any

from . import consequences, legislature
from .consequences import LEAN

PAUTAS: dict[str, dict[str, Any]] = {
    "piso_saude": {"title": "Piso salarial para profissionais de saúde", "lean": -0.6, "author": "esquerda",
                   "sancao": {"approval": 0.8, "primary_balance": -0.08}, "veto": {"approval": -0.8, "congress_support": -1.0}},
    "reajuste_beneficios": {"title": "Reajuste de benefícios acima da inflação", "lean": -0.3, "author": "esquerda",
                            "sancao": {"approval": 0.4, "primary_balance": -0.15}, "veto": {"approval": -0.3, "congress_support": -0.6}},
    "desoneracao_folha": {"title": "Desoneração da folha de setores que mais empregam", "lean": 0.5, "author": "direita",
                          "sancao": {"approval": 0.2, "unemployment": -0.04, "primary_balance": -0.1}, "veto": {"approval": -0.2, "congress_support": -0.8}},
    "armas_colecionadores": {"title": "Ampliação do acesso a armas para colecionadores e atiradores", "lean": 0.8, "author": "direita",
                             "sancao": {"approval": 0.1, "institutional_trust": -0.4}, "veto": {"approval": -0.1, "congress_support": -0.8}},
    "licenciamento": {"title": "Simplificação do licenciamento ambiental", "lean": 0.6, "author": "direita",
                      "sancao": {"gdp_growth": 0.05, "approval": -0.4, "institutional_trust": -0.4}, "veto": {"approval": 0.2, "congress_support": -0.8}},
    "transparencia_emendas": {"title": "Transparência total das emendas parlamentares", "lean": -0.2, "author": "centro",
                              "sancao": {"integrity": 1.0, "congress_support": -0.4}, "veto": {"integrity": -1.0, "approval": -0.3}},
    "penas_patrimoniais": {"title": "Endurecimento de penas para crimes patrimoniais", "lean": 0.6, "author": "direita",
                           "sancao": {"approval": 0.5, "institutional_trust": -0.2}, "veto": {"approval": -0.4, "congress_support": -0.6}},
    "creches": {"title": "Vinculação de recursos para creches", "lean": -0.5, "author": "esquerda",
                "sancao": {"approval": 0.5, "primary_balance": -0.06}, "veto": {"approval": -0.4, "congress_support": -0.6}},
}
SANCTION_DAYS = 21
OVERRIDE_DAYS = 30
MONTHLY_CHANCE = 0.22


def _roll(seed: str) -> float:
    return int(hashlib.sha256(seed.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF


def _st(state: dict[str, Any]) -> dict[str, Any]:
    a = state.setdefault("congress_agenda", {})
    a.setdefault("overrides", [])
    a.setdefault("month", None)
    a.setdefault("history", [])
    return a


def _author(spec: dict[str, Any], seed: str) -> str:
    pools = {"esquerda": ["PT", "PSB", "PDT", "PSOL"], "direita": ["PL", "PP", "REPUBLICANOS", "UNIÃO"], "centro": ["MDB", "PSD", "PSDB", "PODE"]}
    pool = pools[spec["author"]]
    return pool[int(_roll(seed + "a") * len(pool)) % len(pool)]


def _scale(effects: dict[str, float], k: float) -> dict[str, float]:
    return {key: round(v * k, 4) for key, v in effects.items()}


def _is_presidency(state: dict[str, Any]) -> bool:
    career = state.get("career") or {}
    return not career.get("mode") or career.get("office") == "presidente"


def schedule_override(state: dict[str, Any], key: str, scope: str, author: str) -> None:
    today = date.fromisoformat(state["date"])
    _st(state)["overrides"].append({"key": key, "scope": scope, "author": author, "due": (today + timedelta(days=OVERRIDE_DAYS)).isoformat()})


def tick(state: dict[str, Any], before: date, after: date) -> list[str]:
    if not _is_presidency(state) or state.get("office_status", "incumbent") != "incumbent":
        return []
    ag = _st(state)
    msgs: list[str] = []
    # 1) vetos que voltam ao plenário
    keep = []
    for item in ag["overrides"]:
        if date.fromisoformat(item["due"]) > after:
            keep.append(item)
            continue
        spec = PAUTAS[item["key"]]
        bill = {"id": f"veto-{item['key']}-{item['due']}", "instrument": "Projeto de Lei Complementar", "interpretation": {"category": "other"}, "power_id": "", "title": spec["title"]}
        # derrubar o veto é votar CONTRA o governo: quanto mais forte a base do Presidente, menos votos pela derrubada
        mood = {**state, "metrics": {**state.get("metrics", {}), "congress_support": 100 - float(state.get("metrics", {}).get("congress_support", 50))}}
        result = legislature.roll_call(mood, bill)
        # o resultado depende da base: maioria absoluta nas duas casas; veto parcial é derrubado com mais dificuldade
        overridden = bool(result["aprovado"]) and (item["scope"] == "total" or _roll(f"{state.get('campaign_seed', 1)}:{item['key']}:parcial") < 0.6)
        book = consequences._book(state)
        m = state.setdefault("metrics", {})
        if overridden:
            consequences._apply(state, _scale(spec["sancao"], 1.0))
            m["congress_support"] = round(max(0.0, float(m.get("congress_support", 50)) - 0.6), 2)
            text = f"O Congresso derrubou o veto: {spec['title']} (votos na Câmara: {result['camara']['sim']} de {result['camara']['necessarios']} necessários). A lei entrou em vigor."
        else:
            text = f"O veto foi mantido: {spec['title']} (votos na Câmara: {result['camara']['sim']} de {result['camara']['necessarios']} necessários)."
        consequences._post(book, state, {"id": f"veto-{item['key']}-{item['due']}", "kind": "congresso", "headline": text, "body": f"Projeto de autoria do {item['author']}.", "tone": "negativo" if overridden else "neutro", "action_id": f"pauta_{item['key']}"})
        ag["history"].insert(0, {"key": item["key"], "title": spec["title"], "veto": item["scope"], "overridden": overridden, "date": after.isoformat()})
        msgs.append(text)
    ag["overrides"] = keep
    # 2) novos projetos chegam à sanção
    month = after.isoformat()[:7]
    if ag["month"] != month:
        ag["month"] = month
        pending = [c for c in state.get("consequences", {}).get("pending", []) if c["action_id"].startswith("pauta_")]
        seed = f"{state.get('campaign_seed', 1)}:pauta:{month}"
        if not pending and _roll(seed) < MONTHLY_CHANCE:
            used = {h["key"] for h in ag["history"][:4]}
            keys = [k for k in PAUTAS if k not in used]
            key = keys[int(_roll(seed + "k") * len(keys)) % len(keys)]
            spec = PAUTAS[key]
            author = _author(spec, seed)
            s, v = spec["sancao"], spec["veto"]
            consequences.open_crisis(
                state, crisis_id=f"pauta-{key}-{month}", action_id=f"pauta_{key}", today=after, deadline_days=SANCTION_DAYS,
                title=f"Projeto aprovado pelo Congresso aguarda sanção: {spec['title']}",
                text=f"De autoria do {author}. O senhor ou a senhora tem 15 dias úteis para sancionar ou vetar; sem resposta, vale a sanção tácita.",
                options=[{"id": "sancionar", "label": "Sancionar integralmente", "effects": s},
                         {"id": "vetar_parcial", "label": "Vetar parcialmente (metade dos efeitos; o Congresso pode derrubar)", "effects": _scale(s, 0.5),
                          "hook": {"veto": key, "scope": "parcial", "author": author}},
                         {"id": "vetar", "label": "Vetar totalmente (o Congresso pode derrubar o veto)", "effects": v, "hook": {"veto": key, "scope": "total", "author": author}},
                         {"id": "tacita", "label": "Deixar virar lei por sanção tácita", "effects": {**_scale(s, 1.0), "institutional_trust": -0.3}}])
            msgs.append(f"O Congresso aprovou um projeto que aguarda a sua sanção: {spec['title']}.")
    return msgs


def overview(state: dict[str, Any]) -> dict[str, Any]:
    ag = _st(state)
    return {"overrides": [{**o, "title": PAUTAS[o["key"]]["title"]} for o in ag["overrides"]], "history": ag["history"][:10]}
