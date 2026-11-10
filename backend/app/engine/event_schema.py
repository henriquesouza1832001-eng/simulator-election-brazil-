"""Esquema, condições declarativas e validação de eventos do jogo.

Um evento é dado puro (JSON), não código. Isso permite milhares de eventos, geração por IA e revisão humana.
Condições são listas de comparações sobre o estado; todas precisam valer (E lógico).

Exemplo de condição: {"metric": "inflation", "op": ">", "value": 3.5}
Métricas aceitas: qualquer chave de `state["metrics"]` ou `inst:<nome>` (instituições).
"""
from __future__ import annotations

import operator
from typing import Any, Callable

KINDS = {"decisao", "oportunidade", "info"}
TONES = {"dialogo", "dura", "etica", "passiva", "neutra", "fisiologica", "tecnica", "populista"}
LEVELS = {"federal", "estadual", "municipal", "legislativo", "partido", "militante"}
SOURCE_TYPES = {"modelo", "historico_inspirado", "gemini", "manual"}
REVIEW = {"aprovado", "pendente", "rejeitado"}

# Limites por efeito (valor bruto, antes da escala global do motor). Impede evento gerado de "quebrar" o jogo.
EFFECT_LIMITS: dict[str, float] = {
    "approval": 6.0, "congress_support": 8.0, "integrity": 8.0, "governability": 6.0, "institutional_trust": 6.0,
    "gdp_growth": 0.6, "inflation": 1.0, "unemployment": 0.8, "primary_balance": 0.5,
}
INST_LIMIT = 5.0
PP_LIMIT = 12.0
PP_ENERGY_LIMIT = 30.0
#                     # efeitos "pp:" (trajetória partidária): reputation, network, standing, militancy, energy
PP_KEYS = {"reputation", "network", "standing", "militancy", "energy"}
REL_LIMIT = 8.0
COST_LIMIT_BI = 12.0

OPS: dict[str, Callable[[Any, Any], bool]] = {">": operator.gt, ">=": operator.ge, "<": operator.lt, "<=": operator.le, "==": operator.eq}


def compile_conditions(conditions: list[dict[str, Any]] | None) -> Callable[[dict[str, Any]], bool]:
    """Transforma a lista declarativa em um predicado sobre o estado. Condição inválida nunca dispara o evento."""
    items = list(conditions or [])

    def predicate(state: dict[str, Any]) -> bool:
        for cond in items:
            try:
                metric, op, value = cond["metric"], cond["op"], cond["value"]
                if metric.startswith("inst:"):
                    current = float(state.get("institutions", {}).get(metric[5:], 50))
                elif metric == "month":
                    current = float(state.get("month", 1))
                else:
                    current = float(state.get("metrics", {}).get(metric, 50))
                if not OPS[op](current, float(value)):
                    return False
            except (KeyError, TypeError, ValueError):
                return False
        return True

    return predicate


def _check_effects(effects: dict[str, Any], where: str, errors: list[str]) -> None:
    for key, value in effects.items():
        if not isinstance(value, (int, float)):
            errors.append(f"{where}: efeito '{key}' não é número")
            continue
        if key.startswith("inst:"):
            limit = INST_LIMIT
        elif key.startswith("pp:"):
            if key[3:] not in PP_KEYS:
                errors.append(f"{where}: efeito desconhecido '{key}'")
                continue
            limit = PP_ENERGY_LIMIT if key == "pp:energy" else PP_LIMIT
        elif key.startswith("rel:"):
            limit = REL_LIMIT
        elif key in EFFECT_LIMITS:
            limit = EFFECT_LIMITS[key]
        else:
            errors.append(f"{where}: efeito desconhecido '{key}'")
            continue
        if abs(value) > limit:
            errors.append(f"{where}: efeito '{key}'={value} passa do limite {limit}")


def validate_event(ev: dict[str, Any]) -> list[str]:
    """Devolve a lista de problemas; vazia significa válido."""
    errors: list[str] = []
    for field in ("id", "kind", "title", "text", "choices", "levels", "tags"):
        if field not in ev:
            errors.append(f"campo obrigatório ausente: {field}")
    if errors:
        return errors
    if ev["kind"] not in KINDS:
        errors.append(f"tipo inválido: {ev['kind']}")
    if not isinstance(ev["levels"], list) or not ev["levels"] or not set(ev["levels"]) <= LEVELS:
        errors.append(f"níveis inválidos: {ev['levels']}")
    if not (10 <= len(ev["title"]) <= 120):
        errors.append("título deve ter de 10 a 120 caracteres")
    if not (40 <= len(ev["text"]) <= 700):
        errors.append("texto deve ter de 40 a 700 caracteres")
    choices = ev["choices"]
    if not isinstance(choices, list) or not (1 <= len(choices) <= 4) or (ev["kind"] != "info" and len(choices) < 2):
        errors.append("quantidade de opções inválida (decisão e oportunidade: 2 a 4; informativo: 1)")
        return errors
    seen: set[str] = set()
    for choice in choices:
        cid = choice.get("id")
        if not cid or cid in seen:
            errors.append(f"id de opção ausente ou repetido: {cid}")
        seen.add(cid)
        if not choice.get("label") or not choice.get("outcome"):
            errors.append(f"opção {cid}: rótulo e desfecho são obrigatórios")
        if choice.get("tone", "neutra") not in TONES:
            errors.append(f"opção {cid}: tom inválido")
        cost = float(choice.get("cost_bi", 0) or 0)
        if not (0 <= cost <= COST_LIMIT_BI):
            errors.append(f"opção {cid}: custo fora do limite")
        _check_effects(choice.get("effects", {}), f"opção {cid}", errors)
    fb = ev.get("fallback")
    if fb is not None and fb not in seen:
        errors.append("opção padrão (fallback) não existe")
    source = ev.get("source", {})
    if source.get("type") not in SOURCE_TYPES:
        errors.append("origem (source.type) inválida")
    if ev.get("review", "aprovado") not in REVIEW:
        errors.append("status de revisão inválido")
    return errors


def normalize_event(ev: dict[str, Any]) -> dict[str, Any]:
    """Preenche padrões e compila a condição. Não valida; use `validate_event` antes."""
    out = dict(ev)
    out.setdefault("weight", 1.0)
    out.setdefault("cooldown", 120)
    out.setdefault("family", out["id"].split(":")[0])
    out.setdefault("review", "aprovado")
    out.setdefault("source", {"type": "modelo"})
    out["when"] = compile_conditions(out.get("conditions"))
    if out["kind"] != "info":
        out.setdefault("fallback", out["choices"][-1]["id"])
    return out
