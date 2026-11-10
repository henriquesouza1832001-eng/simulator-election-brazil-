"""Gerador de acontecimentos a partir de um corpus de fatos históricos.

Fluxo: corpus (JSONL com fonte) → Gemini (opcional) ou adaptação local → validação → arquivo **pendente de revisão**.
Nada gerado entra no jogo sem aprovação explícita (`review = "aprovado"`).

Regras de conteúdo (aplicadas na validação, não só no prompt):
- O evento é uma **ficção inspirada** no fato; cita papéis e instituições genéricos, nunca pessoas reais.
- Qualquer nome de candidato de maior visibilidade (TSE) no texto reprova o evento.
- Efeitos têm limites (ver `event_schema.EFFECT_LIMITS`); o motor decide os números, a IA propõe.
- A chave do Gemini fica só no backend (`GEMINI_API_KEY`). Sem chave, usa-se a adaptação local.

Uso:
  python -m app.ai.event_generator generate --corpus data/events/corpus/fatos.jsonl --limit 20
  python -m app.ai.event_generator generate --corpus ... --local          # sem Gemini
  python -m app.ai.event_generator approve data/events/generated/arquivo.json   # revisão humana feita
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Awaitable, Callable

import httpx

from ..engine import event_schema as schema
from ..engine.event_library import EVENTS_DIR, mentions_real_person, real_person_names

logger = logging.getLogger(__name__)
GENERATED_DIR = EVENTS_DIR / "generated"
DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
MODEL_PATTERN = re.compile(r"[A-Za-z0-9._-]{3,80}")

INSTRUCTIONS = """Você cria acontecimentos para um simulador político brasileiro FICTÍCIO e satírico.
Receberá fatos históricos resumidos (com fonte). Para cada fato, crie UM acontecimento de jogo para CADA nível listado em "niveis", em português do Brasil, com "level" igual ao nível.
Regras obrigatórias:
- É uma ficção inspirada no tema do fato. NÃO cite pessoas reais, nem nomes de candidatos, nem atribua falas, crimes, doenças ou atos a pessoas reais.
  Use papéis genéricos (um ministro fictício, entidades fictícias, uma agência fictícia).
- Responda SOMENTE com JSON no esquema pedido.
- kind: decisao (prazo curto), oportunidade (prazo maior) ou info.
- Decisão/oportunidade: 2 a 4 opções com tons diferentes; info: 1 opção.
- effects usa só estas chaves: approval, congress_support, integrity, governability, institutional_trust, gdp_growth, inflation,
  unemployment, primary_balance, inst:<nome>, rel:<SIGLA>. Valores pequenos (aprovação entre -4 e +4; economia entre -0.5 e +0.5).
- cost_bi em bilhões de reais, de 0 a 8.
- Opções boas devem ter custo ou contrapartida; opções omissas devem ter custo de opinião.
- Título de 10 a 120 caracteres; texto de 40 a 600 caracteres; desfecho de cada opção em uma frase."""

OUTPUT_SCHEMA = {
    "type": "ARRAY",
    "items": {
        "type": "OBJECT",
        "properties": {
            "corpus_id": {"type": "STRING"}, "kind": {"type": "STRING"}, "level": {"type": "STRING"},
            "tags": {"type": "ARRAY", "items": {"type": "STRING"}}, "title": {"type": "STRING"}, "text": {"type": "STRING"},
            "choices": {"type": "ARRAY", "items": {"type": "OBJECT", "properties": {
                "id": {"type": "STRING"}, "label": {"type": "STRING"}, "hint": {"type": "STRING"}, "tone": {"type": "STRING"},
                "cost_bi": {"type": "NUMBER"}, "outcome": {"type": "STRING"},
                "effects": {"type": "OBJECT"}}, "required": ["id", "label", "outcome"]}},
        },
        "required": ["corpus_id", "kind", "title", "text", "choices"],
    },
}

Caller = Callable[[str, list[dict[str, Any]]], Awaitable[list[dict[str, Any]]]]


def load_corpus(path: Path, limit: int | None = None) -> list[dict[str, Any]]:
    """Lê JSONL: {id, date, title, summary, area, level?, source_name, source_url}. Linhas sem fonte são ignoradas."""
    items: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if item.get("id") and item.get("summary") and (item.get("source_url") or item.get("source_name")):
            items.append(item)
        if limit and len(items) >= limit:
            break
    return items


async def gemini_call(model: str, key: str, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Chama o Gemini com um lote do corpus e devolve a lista de eventos propostos (ainda não validados)."""
    if not MODEL_PATTERN.fullmatch(model):
        raise ValueError("Nome de modelo inválido.")
    payload = {
        "systemInstruction": {"parts": [{"text": INSTRUCTIONS}]},
        "contents": [{"role": "user", "parts": [{"text": "Fatos históricos (corpus):\n" + json.dumps(
            [{"corpus_id": i["id"], "data": i.get("date"), "area": i.get("area"), "niveis": i.get("levels") or [i.get("level", "federal")], "titulo": i.get("title"), "resumo": i["summary"]} for i in items],
            ensure_ascii=False)}]}],
        "generationConfig": {"responseFormat": {"text": {"mimeType": "APPLICATION_JSON", "schema": OUTPUT_SCHEMA}},
                             "thinkingConfig": {"thinkingLevel": "low"}, "maxOutputTokens": 6000},
    }
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    async with httpx.AsyncClient(timeout=httpx.Timeout(connect=5, read=90, write=10, pool=5)) as client:
        response = await client.post(endpoint, headers={"x-goog-api-key": key}, json=payload)
    response.raise_for_status()
    data = response.json()
    parts = data["candidates"][0]["content"]["parts"]
    text = next(p["text"] for p in parts if isinstance(p, dict) and isinstance(p.get("text"), str))
    result = json.loads(text)
    return result if isinstance(result, list) else []


# Perfil por área: rótulos das três respostas e efeitos de cada uma (valores brutos, antes da escala do motor).
AREA_PROFILE: dict[str, dict[str, Any]] = {
    "economia": {"agir": "Anunciar um pacote de resposta e dar previsibilidade", "firme": "Cortar gastos e endurecer a regra fiscal", "omitir": "Aguardar o mercado se acalmar",
                 "agir_fx": {"approval": 0.8, "gdp_growth": 0.04}, "firme_fx": {"primary_balance": 0.08, "approval": -1.0}, "omitir_fx": {"approval": -1.2, "inflation": 0.2}},
    "saude": {"agir": "Reforçar a rede de saúde e enviar equipes", "firme": "Impor restrições e campanhas obrigatórias", "omitir": "Manter a rotina e esperar os casos caírem",
              "agir_fx": {"approval": 1.6, "governability": 0.5}, "firme_fx": {"approval": -0.8, "governability": 0.8}, "omitir_fx": {"approval": -2.0, "integrity": -0.3}},
    "seguranca": {"agir": "Integrar as forças e lançar um plano com metas", "firme": "Endurecer operações e ampliar a presença policial", "omitir": "Deixar com as autoridades locais",
                  "agir_fx": {"approval": 1.0, "governability": 0.8}, "firme_fx": {"approval": 0.6, "inst:constitutional_order": -1.2}, "omitir_fx": {"approval": -1.6}},
    "clima": {"agir": "Declarar emergência e liberar recursos para a reconstrução", "firme": "Cobrar responsáveis e endurecer a fiscalização", "omitir": "Aguardar a normalização",
              "agir_fx": {"approval": 1.8, "governability": 0.6}, "firme_fx": {"approval": 0.5, "integrity": 0.6}, "omitir_fx": {"approval": -2.2}},
    "trabalho": {"agir": "Abrir mesa de negociação com a categoria", "firme": "Responder com firmeza para garantir os serviços", "omitir": "Esperar a mobilização perder força",
                 "agir_fx": {"approval": 1.0, "governability": 0.8}, "firme_fx": {"approval": -1.2, "governability": -1.0}, "omitir_fx": {"approval": -1.8, "gdp_growth": -0.05}},
    "integridade": {"agir": "Abrir apuração independente e colaborar", "firme": "Contestar publicamente as acusações", "omitir": "Responder só com nota",
                    "agir_fx": {"integrity": 2.0, "approval": 0.4}, "firme_fx": {"integrity": -1.5, "approval": -0.8}, "omitir_fx": {"integrity": -1.0, "approval": -0.6}},
    "congresso": {"agir": "Construir acordo com as lideranças", "firme": "Pressionar a base e forçar a votação", "omitir": "Deixar a pauta correr sem interferir",
                  "agir_fx": {"congress_support": 3.0, "governability": 1.0}, "firme_fx": {"congress_support": -2.0, "governability": 0.6}, "omitir_fx": {"congress_support": -1.5, "governability": -0.8}},
    "diplomacia": {"agir": "Negociar e enviar uma missão ao exterior", "firme": "Responder com medidas recíprocas", "omitir": "Aguardar sinais da outra parte",
                   "agir_fx": {"approval": 0.4, "gdp_growth": 0.03}, "firme_fx": {"approval": 0.3, "gdp_growth": -0.06}, "omitir_fx": {"approval": -0.6, "gdp_growth": -0.05}},
    "educacao": {"agir": "Abrir diálogo e garantir recursos para a educação", "firme": "Manter o corte e defender a prioridade fiscal", "omitir": "Deixar o tema com os gestores locais",
                 "agir_fx": {"approval": 1.3, "governability": 0.6}, "firme_fx": {"approval": -1.4, "governability": -0.5}, "omitir_fx": {"approval": -1.2}},
    "infraestrutura": {"agir": "Acionar contingência e cobrar a concessionária", "firme": "Aplicar multas e intervir no serviço", "omitir": "Esperar a normalização",
                       "agir_fx": {"approval": 1.0, "gdp_growth": 0.02}, "firme_fx": {"approval": 0.5, "inst:institutional_resistance": 0.5}, "omitir_fx": {"approval": -1.4, "gdp_growth": -0.05}},
    "transporte": {"agir": "Negociar e garantir uma rede mínima de transporte", "firme": "Aplicar multas e acionar a Justiça", "omitir": "Aguardar a greve terminar",
                   "agir_fx": {"approval": 1.0, "governability": 0.6}, "firme_fx": {"approval": -0.6, "governability": -0.8}, "omitir_fx": {"approval": -1.6}},
    "cultura": {"agir": "Aproveitar o momento com programação e apoio", "firme": "Limitar gastos e focar no essencial", "omitir": "Deixar a organização com terceiros",
                "agir_fx": {"approval": 0.8, "gdp_growth": 0.02}, "firme_fx": {"approval": -0.3, "primary_balance": 0.04}, "omitir_fx": {"approval": -0.5}},
    "opiniao": {"agir": "Responder com transparência e uma agenda positiva", "firme": "Rebater o que for falso", "omitir": "Deixar o assunto esfriar",
                "agir_fx": {"approval": 1.0}, "firme_fx": {"approval": 0.2, "integrity": -0.3}, "omitir_fx": {"approval": -0.8}},
    "partido": {"agir": "Mediar entre as alas e buscar consenso", "firme": "Tomar partido e marcar posição", "omitir": "Ficar de fora da disputa",
                "agir_fx": {"pp:standing": 2.5, "pp:network": 1.5, "pp:energy": -10}, "firme_fx": {"pp:standing": 1.5, "pp:network": -1.5}, "omitir_fx": {"pp:standing": -1.0}},
}
LEVEL_COST_BI = {"federal": 2.0, "estadual": 0.8, "municipal": 0.15, "legislativo": 0.0, "partido": 0.0, "militante": 0.0}
LEVEL_WHO = {"federal": "o governo federal", "estadual": "o governo do estado", "municipal": "a prefeitura", "legislativo": "o plenário",
             "partido": "a direção do partido", "militante": "a militância local"}


def _party_fx(fx: dict[str, float]) -> dict[str, float]:
    """Nos níveis de partido/militante, converte efeitos de opinião em efeitos de trajetória."""
    out: dict[str, float] = {}
    for key, value in fx.items():
        if key.startswith("pp:"):
            out[key] = value
        elif key in ("approval", "integrity"):
            out["pp:reputation"] = round(out.get("pp:reputation", 0) + value, 2)
        elif key in ("congress_support", "governability"):
            out["pp:standing"] = round(out.get("pp:standing", 0) + value * 0.6, 2)
    return out


def local_adapt(item: dict[str, Any], level: str | None = None) -> dict[str, Any] | None:
    """Adaptação sem IA: versão fictícia do fato, com respostas específicas da área e do nível de governo."""
    area = (item.get("area") or "opiniao").lower()
    profile = AREA_PROFILE.get(area) or AREA_PROFILE["opiniao"]
    level = level or (item.get("levels") or [item.get("level", "federal")])[0]
    cost = LEVEL_COST_BI.get(level, 0.0)
    who = LEVEL_WHO.get(level, "o governo")
    low = level in ("partido", "militante")
    fx = (lambda d: _party_fx(d)) if low else (lambda d: dict(d))
    title = (item.get("title") or "Fato relevante").strip().rstrip(".")
    summary = (item.get("summary") or "").strip()
    text = f"Versão fictícia inspirada em um episódio real: {summary} Agora {who} precisa decidir como responder."
    return {
        "corpus_id": item["id"], "kind": "decisao", "level": level, "tags": [area, "historico", level],
        "title": f"{title}: {who} precisa responder"[:120], "text": text[:640],
        "choices": [
            {"id": "agir", "label": profile["agir"], "hint": f"Custa cerca de R$ {cost} bi." if cost else "Custa atenção e energia.", "tone": "dialogo",
             "cost_bi": cost, "effects": fx(profile["agir_fx"]), "outcome": "A resposta organizada melhora a percepção de gestão."},
            {"id": "firme", "label": profile["firme"], "hint": "Resolve mais rápido, com custo político.", "tone": "dura",
             "effects": fx(profile["firme_fx"]), "outcome": "A postura firme gera resultado imediato e críticas."},
            {"id": "omitir", "label": profile["omitir"], "hint": "Sem custo agora; o desgaste vem depois.", "tone": "passiva",
             "effects": fx(profile["omitir_fx"]), "outcome": "A omissão pesa na avaliação e o assunto volta a aparecer."}],
        "fallback": "omitir",
    }


def to_event(raw: dict[str, Any], corpus: dict[str, dict[str, Any]], model: str | None) -> dict[str, Any]:
    src = corpus.get(raw.get("corpus_id", ""), {})
    digest = hashlib.sha1(f"{raw.get('corpus_id')}|{raw.get('level')}|{raw.get('title')}".encode()).hexdigest()[:10]
    level = raw.get("level") if raw.get("level") in schema.LEVELS else (src.get("levels") or [src.get("level", "federal")])[0]
    choices = []
    for ch in raw.get("choices", []):
        choices.append({"id": str(ch.get("id", "")).strip(), "label": str(ch.get("label", "")).strip(), "hint": str(ch.get("hint", "")).strip(),
                        "tone": ch.get("tone", "neutra") if ch.get("tone") in schema.TONES else "neutra",
                        "cost_bi": float(ch.get("cost_bi", 0) or 0), "effects": {k: float(v) for k, v in (ch.get("effects") or {}).items() if isinstance(v, (int, float))},
                        "outcome": str(ch.get("outcome", "")).strip(), "follow": []})
    return {
        "id": f"{'gemini' if model else 'local'}:{digest}", "kind": raw.get("kind", "decisao"), "tags": [str(t) for t in raw.get("tags", [])][:5] or ["historico"],
        "levels": [level], "weight": 0.8, "cooldown": 180, "family": f"hist:{src.get('area', 'geral')}:{level}", "title": str(raw.get("title", "")).strip(),
        "text": str(raw.get("text", "")).strip(), "choices": choices,
        "source": {"type": "gemini" if model else "historico_inspirado", "ref": src.get("source_url") or src.get("source_name"),
                   "corpus_id": raw.get("corpus_id"), "fact_date": src.get("date"), "model": model, "source_verified": bool(src.get("source_verified", False))},
        "review": "pendente", "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def validate_generated(ev: dict[str, Any]) -> list[str]:
    problems = schema.validate_event(ev)
    blob = " ".join([ev.get("title", ""), ev.get("text", "")] + [c.get("label", "") + " " + c.get("outcome", "") + " " + c.get("hint", "") for c in ev.get("choices", [])])
    found = mentions_real_person(blob)
    if found:
        problems.append(f"menciona pessoa real: {found}")
    return problems


async def generate(corpus_path: Path, limit: int, use_gemini: bool, batch_size: int = 5, caller: Caller | None = None,
                   require_guard: bool = True) -> dict[str, Any]:
    if require_guard and not real_person_names():
        # Sem os candidatos do TSE no banco, a trava contra nomes reais fica vazia: não gera nada.
        return {"mode": "recusado", "error": "A trava contra nomes de pessoas reais está indisponível. Importe candidaturas do TSE antes: "
                "python -m app.data.tse_candidacies --years 2014 2018 2022 2026 (ou use --no-guard por sua conta e risco).",
                "accepted_pending_review": 0, "file": None}
    items = load_corpus(corpus_path, limit)
    by_id = {i["id"]: i for i in items}
    key = os.getenv("GEMINI_API_KEY", "").strip()
    model = DEFAULT_MODEL if (use_gemini and key) else None
    proposals: list[dict[str, Any]] = []
    errors: list[str] = []
    for start in range(0, len(items), batch_size):
        batch = items[start:start + batch_size]
        try:
            if caller is not None:
                proposals += await caller(model or "teste", batch)
            elif model:
                proposals += await gemini_call(model, key, batch)
            else:
                for item in batch:
                    for lv in (item.get("levels") or [item.get("level", "federal")]):
                        adapted = local_adapt(item, lv)
                        if adapted:
                            proposals.append(adapted)
        except (httpx.HTTPError, KeyError, StopIteration, ValueError, json.JSONDecodeError) as problem:
            errors.append(f"lote {start // batch_size + 1}: {type(problem).__name__}")
            logger.warning("Falha ao gerar lote: %s", problem)
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for raw in proposals:
        ev = to_event(raw, by_id, model if (model or caller) else None)
        problems = validate_generated(ev)
        if ev["id"] in seen_ids:
            problems.append("id repetido no lote")
        if problems:
            rejected.append({"id": ev["id"], "title": ev["title"][:60], "problems": problems})
        else:
            seen_ids.add(ev["id"])
            accepted.append(ev)
    out_path = None
    if accepted:
        GENERATED_DIR.mkdir(parents=True, exist_ok=True)
        out_path = GENERATED_DIR / f"{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{'gemini' if model else 'local'}.json"
        out_path.write_text(json.dumps({"events": accepted}, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"mode": "gemini" if model else "local", "corpus_items": len(items), "proposed": len(proposals), "accepted_pending_review": len(accepted),
            "rejected": len(rejected), "rejected_examples": rejected[:5], "errors": errors, "file": str(out_path) if out_path else None}


def approve(path: Path, reviewer: str = "revisão humana") -> dict[str, Any]:
    """Marca como aprovados os eventos válidos de um arquivo. É um ato de revisão humana, nunca automático."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    items = payload["events"] if isinstance(payload, dict) else payload
    ok = bad = 0
    for ev in items:
        if validate_generated(ev):
            bad += 1
            continue
        ev["review"] = "aprovado"
        ev["reviewed_at"] = datetime.now(timezone.utc).isoformat()
        ev["reviewed_by"] = reviewer
        ok += 1
    path.write_text(json.dumps({"events": items}, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"approved": ok, "still_invalid": bad}


def main() -> None:
    parser = argparse.ArgumentParser(description="Gera acontecimentos a partir de um corpus histórico (saída pendente de revisão).")
    sub = parser.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("generate")
    g.add_argument("--corpus", type=Path, required=True)
    g.add_argument("--limit", type=int, default=20)
    g.add_argument("--local", action="store_true", help="não usar o Gemini")
    g.add_argument("--no-guard", action="store_true", help="gera mesmo sem a trava de nomes reais (não recomendado)")
    a = sub.add_parser("approve")
    a.add_argument("file", type=Path)
    a.add_argument("--reviewer", default="revisão humana", help="identificação de quem revisou (fica gravada no evento)")
    args = parser.parse_args()
    if args.cmd == "generate":
        print(json.dumps(asyncio.run(generate(args.corpus, args.limit, not args.local, require_guard=not args.no_guard)), ensure_ascii=False, indent=1))
    else:
        print(json.dumps(approve(args.file, args.reviewer), ensure_ascii=False))


if __name__ == "__main__":
    main()
