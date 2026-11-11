"""Indicadores por município, estado e região, e projetos de transporte e urbanismo.

Dados de base (população, PIB, setores) vêm do IBGE via `data/municipalities.json`.
IDH, Gini, mobilidade e demais índices são ESTIMATIVAS do jogo derivadas do PIB per capita
e dos setores; não são séries oficiais. Projetos mudam os índices do território atingido.
"""
from __future__ import annotations

import json
import math
from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Any

from .fiscal import record_one_off_spending
from .indicator_registry import REGISTRY, propagate

DATA = Path(__file__).resolve().parents[1] / "data" / "municipalities.json"
REGIONS = {"N": "Norte", "NE": "Nordeste", "SE": "Sudeste", "S": "Sul", "CO": "Centro-Oeste"}
ATLAS = Path(__file__).resolve().parents[2] / "data" / "atlas_municipal.json"

# id, nome, tipo, escopo (cidade/uf), UF, custo bi (R$ de 2027), meses, efeitos nos índices, descrição, base legal/competência
PROJECTS: list[dict[str, Any]] = [
    {"id": "rodoanel_bh", "name": "Rodoanel Metropolitano de Belo Horizonte", "kind": "Rodovia", "uf": "MG", "city": "3106200", "cost_bi": 6.5, "months": 60,
     "effects": {"mobilidade": 9, "desemprego": -0.8, "idhm": 0.004, "seguranca": 0.5}, "gdp_pct": 0.35,
     "text": "Anel viário que tira o tráfego pesado da BR-381 e da Av. do Contorno. Obra de longa duração, com desapropriações.", "who": ["governador", "presidente"]},
    {"id": "metro_bh_l2", "name": "Metrô de BH, Linha 2", "kind": "Metrô", "uf": "MG", "city": "3106200", "cost_bi": 4.2, "months": 72,
     "effects": {"mobilidade": 10, "desemprego": -0.5, "gini": -0.002}, "gdp_pct": 0.2,
     "text": "Ligação Barreiro–Nova Lima. Reduz tempo de viagem de quem mora longe.", "who": ["governador", "presidente", "prefeito"]},
    {"id": "rodoanel_sp_norte", "name": "Rodoanel Norte de São Paulo", "kind": "Rodovia", "uf": "SP", "city": "3550308", "cost_bi": 9.0, "months": 48,
     "effects": {"mobilidade": 8, "desemprego": -1.0}, "gdp_pct": 0.4, "text": "Fecha o anel viário metropolitano.", "who": ["governador", "presidente"]},
    {"id": "brt_capital", "name": "Corredores de BRT", "kind": "Ônibus", "uf": None, "city": None, "cost_bi": 1.2, "months": 30,
     "effects": {"mobilidade": 6, "gini": -0.0015, "desemprego": -0.25}, "gdp_pct": 0.08, "text": "Faixas exclusivas e estações: barato e rápido de fazer.", "who": ["prefeito", "governador"]},
    {"id": "vlt", "name": "VLT (veículo leve sobre trilhos)", "kind": "Trilhos", "uf": None, "city": None, "cost_bi": 2.4, "months": 48,
     "effects": {"mobilidade": 7, "desemprego": -0.3}, "gdp_pct": 0.12, "text": "Bonde moderno em eixo de grande demanda.", "who": ["prefeito", "governador"]},
    {"id": "trem_intercidades", "name": "Trem intercidades regional", "kind": "Trilhos", "uf": None, "city": None, "cost_bi": 14.0, "months": 84,
     "effects": {"mobilidade": 8, "desemprego": -0.8, "gini": -0.003}, "gdp_pct": 0.45, "text": "Liga a capital às cidades do entorno.", "who": ["governador", "presidente"]},
    {"id": "tarifa_zero", "name": "Tarifa zero no transporte coletivo", "kind": "Subsídio", "uf": None, "city": None, "cost_bi": 1.8, "months": 6,
     "effects": {"mobilidade": 4, "gini": -0.003, "desemprego": -0.2}, "gdp_pct": 0.02, "recurring": True,
     "text": "Gratuidade para todos. Exige recurso todo ano; aumenta a demanda e o custo.", "who": ["prefeito"]},
    {"id": "saneamento_metropolitano", "name": "Universalizar esgoto e água", "kind": "Saneamento", "uf": None, "city": None, "cost_bi": 5.0, "months": 60,
     "effects": {"agua_encanada": 8, "esgoto_inadequado": -10, "saneamento_basico": 14, "idhm": 0.008, "desemprego": -0.2}, "gdp_pct": 0.1, "text": "Marco Legal do Saneamento (Lei 14.026/2020): metas de 99% de água e 90% de esgoto.", "who": ["prefeito", "governador", "presidente"]},
    {"id": "policiamento_integrado", "name": "Centro integrado de segurança", "kind": "Segurança", "uf": None, "city": None, "cost_bi": 0.9, "months": 18,
     "effects": {"seguranca": 6}, "gdp_pct": 0.02, "text": "Câmeras, despacho unificado e inteligência (competência estadual).", "who": ["governador"]},
    {"id": "polo_industrial", "name": "Polo industrial e logístico", "kind": "Economia", "uf": None, "city": None, "cost_bi": 3.0, "months": 36,
     "effects": {"desemprego": -1.5, "gini": 0.0005, "idhm": 0.003}, "gdp_pct": 0.3, "text": "Incentivos e infraestrutura para atrair fábricas.", "who": ["prefeito", "governador", "presidente"]},
    {"id": "habitacao_popular", "name": "Programa de habitação popular", "kind": "Habitação", "uf": None, "city": None, "cost_bi": 2.2, "months": 30,
     "effects": {"gini": -0.004, "idhm": 0.005, "saneamento_basico": 3}, "gdp_pct": 0.06, "text": "Moradias para famílias de baixa renda.", "who": ["prefeito", "governador", "presidente"]},
]
BY_ID = {p["id"]: p for p in PROJECTS}


@lru_cache(maxsize=1)
def _cities() -> dict[str, dict[str, Any]]:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    return {c["ibge_code"]: c for c in data["municipalities"]} if "municipalities" in data else {c["ibge_code"]: c for c in data.get("items", [])}


@lru_cache(maxsize=1)
def _atlas() -> dict[str, dict[str, float]]:
    if not ATLAS.exists():
        return {}
    return json.loads(ATLAS.read_text(encoding="utf-8"))["municipalities"]


def _atlas_values(code: str) -> dict[str, float]:
    """Valores reais do Atlas (Censo 2010) para o município, indexados pelo id do registro de indicadores."""
    row = _atlas().get(code, {})
    return {ind["id"]: row[ind["atlas"]] for ind in REGISTRY.values() if ind.get("atlas") and ind["atlas"] in row}


def _base(city: dict[str, Any]) -> dict[str, float]:
    """Índices-base do município: dado real do Atlas quando existe; o restante é estimado."""
    profile = city.get("economic_profile") or {}
    pc = float(profile.get("gdp_per_capita_brl") or 25000)
    wealth = max(0.0, min(1.0, (math.log(max(pc, 5000)) - math.log(8000)) / (math.log(120000) - math.log(8000))))
    pop = float(city.get("population_estimate") or 10000)
    size = max(0.0, min(1.0, (math.log10(max(pop, 1000)) - 3) / 4))
    out = dict(_atlas_values(city["ibge_code"]))
    out.setdefault("idhm", round(0.55 + 0.30 * wealth, 3))
    out.setdefault("gini", round(0.58 - 0.08 * wealth, 3))
    out["mobilidade"] = round(35 + 25 * size + 15 * wealth, 1)
    out["seguranca"] = round(55 + 15 * wealth - 8 * size, 1)
    out["saude_atencao"] = round(60 + 25 * wealth - 5 * size, 1)
    out["conectividade"] = round(30 + 55 * wealth + 8 * size, 1)
    water, sewer, trash = out.get("agua_encanada"), out.get("esgoto_inadequado"), out.get("coleta_lixo")
    if water is not None and sewer is not None:
        out["saneamento_basico"] = round(0.4 * water + 0.4 * (100 - sewer) + 0.2 * (trash if trash is not None else water), 1)
    else:
        out["saneamento_basico"] = round(35 + 55 * wealth, 1)
    out["populacao"] = pop
    return out


def ensure(state: dict[str, Any]) -> dict[str, Any]:
    t = state.setdefault("territory", {})
    t.setdefault("projects", [])
    t.setdefault("deltas", {})  # "uf:MG" ou "city:3106200" -> indicador -> variação acumulada
    return t


def _deltas_for(state: dict[str, Any], city: dict[str, Any]) -> dict[str, float]:
    t = ensure(state)
    out: dict[str, float] = {}
    for scope in (f"city:{city['ibge_code']}", f"uf:{city['state_code']}"):
        weight = 1.0 if scope.startswith("city") else 0.35
        for k, v in t["deltas"].get(scope, {}).items():
            out[k] = out.get(k, 0.0) + v * weight
    return out


def _clamp(key: str, value: float) -> float:
    if key in {"idhm", "idhm_educacao", "idhm_longevidade", "idhm_renda", "gini", "theil"}:
        return max(0.0, min(1.0, value))
    if REGISTRY.get(key, {}).get("unit", "") in {"%", "0 a 100"}:
        return max(0.0, min(100.0, value))
    return max(0.0, value)


def city_indicators(state: dict[str, Any], ibge: str) -> dict[str, Any]:
    city = _cities().get(ibge)
    if not city:
        raise ValueError("Município não encontrado.")
    base, delta = _base(city), _deltas_for(state, city)
    real = _atlas_values(ibge)
    profile = city.get("economic_profile") or {}
    rows = []
    for key, b in base.items():
        meta = REGISTRY.get(key)
        if not meta:
            continue
        value = round(_clamp(key, b + delta.get(key, 0)), 4)
        rows.append({"id": key, "label": meta["label"], "unit": meta["unit"], "domain": meta["domain"], "better": meta["better"], "value": value,
                     "base": b, "delta": round(value - b, 4), "source": "atlas" if key in real else ("ibge" if key == "populacao" else "estimado")})
    return {"ibge_code": ibge, "name": city["name"], "uf": city["state_code"], "region": REGIONS.get(city["region_code"], city["region_code"]),
            "population": city.get("population_estimate"), "gdp_bi": profile.get("gdp_billion_brl"), "gdp_per_capita": profile.get("gdp_per_capita_brl"),
            "indicators": rows,
            "note": "PIB e população: IBGE. Indicadores sociais: Atlas do Desenvolvimento Humano (Censo 2010), a base municipal mais recente. Mobilidade, segurança, saúde e conectividade: estimativas do jogo."}


AGG_KEYS = ("idhm", "gini", "pobreza", "extrema_pobreza", "esperanca_vida", "mortalidade_infantil", "desemprego", "agua_encanada",
            "saneamento_basico", "mobilidade", "seguranca", "educacao_analfabetismo", "renda_per_capita")


def _aggregate(state: dict[str, Any], cities: list[dict[str, Any]]) -> dict[str, Any]:
    pop = sum(float(c.get("population_estimate") or 0) for c in cities) or 1.0
    gdp = sum(float((c.get("economic_profile") or {}).get("gdp_billion_brl") or 0) for c in cities)
    sums: dict[str, float] = {}
    weights: dict[str, float] = {}
    for c in cities:
        w = float(c.get("population_estimate") or 0)
        b, d = _base(c), _deltas_for(state, c)
        for k in AGG_KEYS:
            if k in b:
                sums[k] = sums.get(k, 0.0) + (b[k] + d.get(k, 0.0)) * w
                weights[k] = weights.get(k, 0.0) + w
    return {"population": int(pop), "gdp_bi": round(gdp, 1), "gdp_per_capita": round(gdp * 1e9 / pop),
            "indicators": {k: round(sums[k] / weights[k], 3) for k in sums if weights[k]}}


def overview(state: dict[str, Any]) -> dict[str, Any]:
    cities = list(_cities().values())
    by_uf: dict[str, list] = {}
    by_region: dict[str, list] = {}
    for c in cities:
        by_uf.setdefault(c["state_code"], []).append(c)
        by_region.setdefault(c["region_code"], []).append(c)
    return {"country": _aggregate(state, cities),
            "regions": [{"code": k, "name": REGIONS.get(k, k), **_aggregate(state, v)} for k, v in by_region.items()],
            "states": [{"uf": k, "name": v[0]["state_name"], **_aggregate(state, v)} for k, v in sorted(by_uf.items())],
            "projects": ensure(state)["projects"],
            "note": "Médias ponderadas pela população. Base social: Atlas do Desenvolvimento Humano (Censo 2010); mobilidade e segurança são estimativas do jogo."}


def search(query: str, uf: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
    from unicodedata import normalize
    norm = lambda s: "".join(ch for ch in normalize("NFKD", s.lower()) if not ch.islower() or ch.isascii() or True).encode("ascii", "ignore").decode()
    q = norm(query)
    rows = [c for c in _cities().values() if (not uf or c["state_code"] == uf) and q in norm(c["name"])]
    rows.sort(key=lambda c: -float(c.get("population_estimate") or 0))
    return [{"ibge_code": c["ibge_code"], "name": c["name"], "uf": c["state_code"], "population": c.get("population_estimate")} for c in rows[:limit]]


def catalog(state: dict[str, Any], office: str) -> list[dict[str, Any]]:
    done = {p["project_id"] for p in ensure(state)["projects"]}
    return [{**p, "available": office in p["who"] and p["id"] not in done, "reason": None if office in p["who"] else "Fora das competências do cargo.",
             "done": p["id"] in done} for p in PROJECTS]


def start(state: dict[str, Any], project_id: str, office: str, uf: str, city: str | None) -> dict[str, Any]:
    p = BY_ID.get(project_id)
    if not p:
        raise ValueError("Projeto desconhecido.")
    if office not in p["who"]:
        raise PermissionError("Este cargo não tem competência para este projeto.")
    t = ensure(state)
    if any(x["project_id"] == project_id and x["uf"] == (p["uf"] or uf) for x in t["projects"]):
        raise PermissionError("O projeto já está em andamento ou concluído neste território.")
    uf = p["uf"] or uf
    city = p["city"] or city
    if city and city not in _cities():
        raise ValueError("Município inválido.")
    price = float(state.get("budget", {}).get("works", {}).get("price_index", 1.0))
    cost = round(p["cost_bi"] * price, 2)
    today = date.fromisoformat(state["date"])
    record_one_off_spending(state, cost)
    item = {"id": f"terr-{project_id}-{len(t['projects']) + 1}", "project_id": project_id, "name": p["name"], "uf": uf, "city": city,
            "cost_bi": cost, "start": today.isoformat(), "end": (today + timedelta(days=30 * p["months"])).isoformat(), "status": "em obra"}
    t["projects"].append(item)
    return item


def advance(state: dict[str, Any], before: date, after: date) -> list[str]:
    t = ensure(state)
    msgs = []
    for item in t["projects"]:
        if item["status"] == "em obra" and before < date.fromisoformat(item["end"]) <= after:
            p = BY_ID[item["project_id"]]
            scope = f"city:{item['city']}" if item["city"] else f"uf:{item['uf']}"
            d = t["deltas"].setdefault(scope, {})
            for k, v in p["effects"].items():
                d[k] = round(d.get(k, 0.0) + v, 5)
            # segundo nível: efeitos indiretos pequenos em indicadores percentuais que dependem dos atingidos
            for k, v in propagate({k: (1 if v > 0 else -1) for k, v in p["effects"].items()}, depth=1, decay=0.2).items():
                if k not in p["effects"] and k in REGISTRY and REGISTRY[k]["unit"] in {"%", "0 a 100"}:
                    d[k] = round(d.get(k, 0.0) + v * 0.5, 5)
            metrics = state.setdefault("metrics", {})
            metrics["gdp_growth"] = round(float(metrics.get("gdp_growth", 0)) + p["gdp_pct"] * 0.1, 2)
            item["status"] = "concluída"
            msgs.append(f"Obra concluída: {item['name']}.")
    return msgs
