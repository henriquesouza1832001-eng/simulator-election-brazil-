"""Entrevistas, sabatinas e debates em etapas, com avaliação por critérios e efeito persistente.

As perguntas nascem de fatos do jogo: indicadores atuais, a última decisão do jogador (e o previsto × realizado),
crises pendentes e processos de reguladores. A resposta é texto livre, avaliada por regras determinísticas
(tema, dados, compromisso, tom), com feedback por critério. O resultado vira aprovação/confiança, momentum na
campanha, uma notícia na linha do tempo e um registro no livro-razão. Nenhuma IA decide a nota.
"""
from __future__ import annotations

import hashlib
import re
from datetime import date, timedelta
from typing import Any

from . import consequences, ledger
from .action_mapper import plain, tokens

KINDS = {
    "entrevista": {"label": "Entrevista", "questions": 3, "cooldown": 21, "text": "Conversa mais aberta; perguntas diretas sobre o momento do governo ou da campanha."},
    "sabatina": {"label": "Sabatina", "questions": 5, "cooldown": 45, "text": "Perguntas duras e sobre suas decisões anteriores; vale mais, arrisca mais."},
    "debate": {"label": "Debate", "questions": 5, "cooldown": 30, "text": "Cinco etapas: abertura, dois blocos, direito de resposta e considerações finais. Só na campanha."},
}
INSULTS = {"idiota", "burro", "mentiroso", "canalha", "ladrao", "vagabundo", "corrupto", "imbecil", "safado", "bandido"}
PRAZO = re.compile(r"\b(em|ate|dentro de|nos proximos|ao longo de)\s+\w*\s*\d*\s*(dias|dia|semanas|meses|mes|ano|anos|trimestre)\b|\bprazo\b|\bmeta\b")
RESPONSAVEL = re.compile(r"\b(secretaria|ministerio|prefeitura|governo|comite|orgao|agencia|controladoria|tribunal|congresso|camara|comissao)\b")
NUMBER = re.compile(r"\d+(?:[.,]\d+)?")


def _st(state: dict[str, Any]) -> dict[str, Any]:
    i = state.setdefault("interviews", {})
    i.setdefault("current", None)
    i.setdefault("history", [])
    i.setdefault("last", {})
    return i


def _roll(seed: str) -> float:
    return int(hashlib.sha256(seed.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF


def _context(state: dict[str, Any]) -> dict[str, Any]:
    career = state.get("career") or {}
    local = bool(career.get("mode")) and career.get("office") != "presidente"
    return {"local": local, "office": career.get("office", "presidente"), "territory": career.get("municipality") or career.get("state_name") or "o país",
            "phase": career.get("phase"), "campaign": career.get("phase") == "campaign" or bool(state.get("campaign_active"))}


def _fact_questions(state: dict[str, Any], ctx: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    m = state.get("metrics", {})
    if not ctx["local"]:
        infl, unemp, debt = float(m.get("inflation", 0)), float(m.get("unemployment", 0)), float(m.get("debt_gdp", 0))
        out.append({"topic": "inflação", "terms": ["inflacao", "preco", "juros", "meta"], "fact": infl,
                    "prompt": f"A inflação está em {infl:.1f}% ao ano. Que medidas concretas o senhor ou a senhora adotará e em quanto tempo o cidadão sente a diferença?"})
        out.append({"topic": "emprego", "terms": ["emprego", "desemprego", "renda", "vagas"], "fact": unemp,
                    "prompt": f"O desemprego está em {unemp:.1f}%. Qual é o plano para gerar vagas e de onde sairão os recursos?"})
        out.append({"topic": "dívida", "terms": ["divida", "fiscal", "gasto", "receita"], "fact": debt,
                    "prompt": f"A dívida pública é de {debt:.0f}% do PIB. Como equilibrar as contas sem cortar o que a população mais precisa?"})
    else:
        from . import territory
        mid = (state.get("career") or {}).get("municipality_id")
        try:
            city = territory.city_indicators(state, mid) if mid else None
        except ValueError:
            city = None
        if city:
            ind = {i["id"]: i for i in city["indicators"]}
            for key, topic, terms, label in (("saneamento_basico", "saneamento", ["saneamento", "esgoto", "agua", "obra"], "o índice de saneamento"),
                                             ("mobilidade", "mobilidade", ["transporte", "onibus", "mobilidade", "tarifa"], "a mobilidade urbana"),
                                             ("seguranca", "segurança", ["seguranca", "guarda", "policia", "iluminacao"], "a segurança")):
                if key in ind:
                    v = float(ind[key]["value"])
                    out.append({"topic": topic, "terms": terms, "fact": v,
                                "prompt": f"Em {ctx['territory']}, {label} está em {v:.0f} de 100. O que muda na sua gestão e quando?"})
    return out


def _decision_questions(state: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for e in (state.get("ledger") or [])[:3]:
        if e.get("source") in {"presidencia", "cargo", "território"} and e.get("title"):
            fc = ", ".join(f"{k} {v:+g}" for k, v in (e.get("forecast") or {}).items()) or "sem efeito numérico"
            res = ", ".join(f"{k} {v:+g}" for k, v in (e.get("result") or {}).items()) if e.get("result") else None
            gap = f" O previsto era {fc}; o realizado foi {res}." if res else f" O previsto era {fc}."
            out.append({"topic": "decisão", "terms": tokens(e["title"])[:4] + ["resultado", "decisao"], "fact": None,
                        "prompt": f"Sobre a decisão “{e['title']}”:{gap} Como o senhor ou a senhora avalia o resultado e o que corrige?"})
    return out


def _institution_questions(state: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for c in (state.get("consequences", {}).get("pending") or [])[:2]:
        out.append({"topic": "crise", "terms": tokens(c["title"])[:4] + ["resposta", "crise"], "fact": None,
                    "prompt": f"{c['title']}. {c['text']} Qual é a sua resposta e que prazo o senhor ou a senhora se dá?"})
    for case in (state.get("regulators", {}).get("cases") or [])[:1]:
        out.append({"topic": "legalidade", "terms": ["constituicao", "stf", "legal", "lei", "defesa"], "fact": None,
                    "prompt": f"O ato “{case['title']}” é questionado no STF. Não há risco de desrespeitar a Constituição?"})
    return out


def _opponent(state: dict[str, Any]) -> str:
    career = state.get("career") or {}
    opponents = career.get("opponents") or []
    if opponents:
        return str(opponents[0].get("name") or f"candidato do {opponents[0].get('party')}")
    return "o candidato da oposição"


def build_questions(state: dict[str, Any], kind: str) -> list[dict[str, Any]]:
    ctx = _context(state)
    seed = f"{state.get('campaign_seed', 1)}:{kind}:{state.get('date')}"
    pool = _decision_questions(state) + _institution_questions(state) + _fact_questions(state, ctx)
    if kind == "entrevista":
        pool = _fact_questions(state, ctx) + _decision_questions(state)
    pool = sorted(pool, key=lambda q: _roll(seed + q["prompt"][:20]))
    n = KINDS[kind]["questions"]
    if kind == "debate":
        facts = _fact_questions(state, ctx) or pool
        themes = (facts + pool)[:2] or [{"topic": "projeto de governo", "terms": ["governo", "proposta", "prioridade"], "fact": None, "prompt": "Qual é a sua prioridade central e como será financiada?"}]
        opp = _opponent(state)
        stages = [
            {"stage": "Abertura", "topic": "projeto", "terms": ["governo", "proposta", "prioridade", "compromisso"], "fact": None,
             "prompt": "Apresente em poucas frases quem o senhor ou a senhora é, a sua prioridade e um compromisso que pode ser cobrado."},
            {"stage": "Bloco 1", **themes[0]},
            {"stage": "Direito de resposta", "topic": "réplica", "terms": ["resposta", "dados", "proposta"], "fact": None,
             "prompt": f"{opp[:1].upper() + opp[1:]} afirmou que o seu plano não fecha as contas. Responda com dados e com o que será diferente."},
            {"stage": "Bloco 2", **(themes[1] if len(themes) > 1 else themes[0])},
            {"stage": "Considerações finais", "topic": "compromisso", "terms": ["compromisso", "prazo", "povo", "governo"], "fact": None,
             "prompt": "Em uma última fala, diga o que o eleitor pode cobrar de você e em que prazo."},
        ]
        return stages
    pool = pool or [{"topic": "prioridades", "terms": ["governo", "proposta", "prioridade"], "fact": None, "prompt": "Quais são as suas prioridades agora e como serão financiadas?"}]
    out = []
    for i in range(n):
        out.append(dict(pool[i % len(pool)]))
    return out


def score_answer(text: str, q: dict[str, Any]) -> dict[str, Any]:
    t = plain(text)
    words = set(tokens(text))
    terms = [plain(x) for x in q.get("terms", [])]
    hits = sum(1 for term in terms if term in t or term in words)
    tema = round(25 * min(1.0, (hits / max(len(terms), 1)) * 1.6), 1)
    nums = [float(x.replace(",", ".")) for x in NUMBER.findall(text)]
    fact = q.get("fact")
    if nums and fact:
        near = any(abs(n - fact) <= max(abs(fact) * 0.3, 1.5) for n in nums)
        dados = 25.0 if near else 17.0
    elif nums:
        dados = 20.0
    else:
        dados = 0.0
    has_deadline, has_owner = bool(PRAZO.search(t)), bool(RESPONSAVEL.search(t))
    compromisso = (12.5 if has_deadline else 0.0) + (12.5 if has_owner else 0.0)
    tom = 25.0 - 8.0 * sum(1 for w in INSULTS if w in t)
    if text.isupper() and len(text) > 20:
        tom -= 6
    tom = max(0.0, tom)
    total = round(tema + dados + compromisso + tom, 1)
    feedback = {
        "tema": "Respondeu ao ponto da pergunta." if tema >= 18 else "Faltou tratar do tema da pergunta; use os termos do assunto.",
        "dados": "Usou números coerentes com o fato citado." if dados >= 25 else ("Citou números, mas longe do dado apresentado." if dados >= 17 else ("Citou um número; relacione-o ao dado da pergunta." if dados > 0 else "Sem números: cite dados ou metas.")),
        "compromisso": ("Deu prazo e responsável." if has_deadline and has_owner else "Faltou o responsável." if has_deadline
                        else "Faltou o prazo." if has_owner else "Faltaram prazo e responsável."),
        "tom": "Tom adequado." if tom >= 25 else "O tom atrapalhou: evite ataques pessoais e caixa alta.",
    }
    return {"total": total, "criteria": {"tema": tema, "dados": dados, "compromisso": compromisso, "tom": tom}, "feedback": feedback}


def grade(avg: float) -> str:
    return "forte" if avg >= 75 else "boa" if avg >= 55 else "regular" if avg >= 35 else "fraca"


def overview(state: dict[str, Any]) -> dict[str, Any]:
    i = _st(state)
    ctx = _context(state)
    today = date.fromisoformat(state["date"])
    kinds = []
    for key, info in KINDS.items():
        last = i["last"].get(key)
        wait = max(0, info["cooldown"] - (today - date.fromisoformat(last)).days) if last else 0
        reason = None
        if i["current"]:
            reason = "Há uma sessão em andamento."
        elif key == "debate" and not ctx["campaign"]:
            reason = "Debates acontecem durante a campanha."
        elif wait:
            reason = f"Disponível em {wait} dia(s)."
        kinds.append({"key": key, "label": info["label"], "text": info["text"], "questions": info["questions"], "available": reason is None, "reason": reason})
    cur = i["current"]
    return {"kinds": kinds, "current": cur and {**cur, "question": cur["questions"][cur["index"]] if cur["index"] < len(cur["questions"]) else None},
            "history": i["history"][:10],
            "note": "A nota usa regras públicas (tema, dados, compromisso e tom). Textos de pergunta usam só fatos do jogo."}


def start(state: dict[str, Any], kind: str) -> dict[str, Any]:
    if kind not in KINDS:
        raise ValueError("Tipo desconhecido.")
    info = next(k for k in overview(state)["kinds"] if k["key"] == kind)
    if not info["available"]:
        raise PermissionError(info["reason"])
    i = _st(state)
    i["current"] = {"id": f"{kind}-{state['date']}-{len(i['history']) + 1}", "kind": kind, "index": 0, "questions": build_questions(state, kind), "answers": [], "started": state["date"]}
    return overview(state)


def answer(state: dict[str, Any], text: str) -> dict[str, Any]:
    i = _st(state)
    cur = i["current"]
    if not cur:
        raise PermissionError("Nenhuma sessão em andamento.")
    if len(text.strip()) < 40:
        raise ValueError("Escreva ao menos 40 caracteres para responder.")
    q = cur["questions"][cur["index"]]
    result = score_answer(text, q)
    cur["answers"].append({"stage": q.get("stage"), "topic": q["topic"], "prompt": q["prompt"], "text": text.strip()[:800], **result})
    cur["index"] += 1
    if cur["index"] < len(cur["questions"]):
        return {"done": False, "feedback": result, "overview": overview(state)}
    return {"done": True, "feedback": result, "summary": _finish(state, cur), "overview": overview(state)}


def _finish(state: dict[str, Any], cur: dict[str, Any]) -> dict[str, Any]:
    from .powers import METRIC_RANGES, _bump
    i = _st(state)
    avg = round(sum(a["total"] for a in cur["answers"]) / len(cur["answers"]), 1)
    g = grade(avg)
    kind = cur["kind"]
    weight = {"entrevista": 0.6, "sabatina": 1.0, "debate": 1.2}[kind]
    delta = round(max(-2.5, min(2.5, (avg - 55) * 0.045 * weight)), 2)
    career = state.get("career") or {}
    applied: dict[str, float] = {}
    if career.get("mode") and career.get("office") != "presidente":
        gov = career.setdefault("governance", {})
        if career.get("phase") == "office":
            gov["trust"] = round(max(0.0, min(100.0, float(gov.get("trust", 50)) + delta)), 2)
            applied["trust"] = delta
    elif "approval" in state.get("metrics", {}):
        _bump(state, "approval", delta)
        applied["approval"] = delta
    if career.get("mode") and career.get("phase") == "campaign":
        move = round((avg - 55) * 0.05 * weight, 2)
        career["momentum"] = round(max(-10, min(10, float(career.get("momentum", 0)) + move)), 2)
        career["poll_support"] = round(max(0, min(100, float(career.get("poll_support", 0)) + move * 0.4)), 2)
        applied["momentum"] = move
    title = f"{KINDS[kind]['label']} ({g}, {avg:.0f} pontos)"
    entry = ledger.record(state, "imprensa", title, {}, applied, status="concluído", cost=None,
                          reason="Avaliação por tema, dados, compromisso e tom; veja o feedback por pergunta.")
    consequences._post(consequences._book(state), state, {"id": f"int-{cur['id']}", "kind": "imprensa",
                       "headline": {"forte": "Desempenho forte em " + KINDS[kind]["label"].lower(), "boa": "Boa participação em " + KINDS[kind]["label"].lower(),
                                    "regular": "Participação irregular em " + KINDS[kind]["label"].lower(), "fraca": "Desempenho fraco em " + KINDS[kind]["label"].lower()}[g],
                       "body": f"Na simulação, a avaliação final foi {avg:.0f} pontos. Comentaristas destacam pontos fortes e lacunas nas respostas.",
                       "tone": "positivo" if avg >= 55 else "negativo", "action_id": kind})
    summary = {"id": cur["id"], "kind": kind, "avg": avg, "grade": g, "effects": applied, "date": state["date"], "ledger_id": entry["id"],
               "answers": [{"stage": a.get("stage"), "topic": a["topic"], "total": a["total"]} for a in cur["answers"]]}
    i["history"].insert(0, summary)
    del i["history"][20:]
    i["last"][kind] = state["date"]
    i["current"] = None
    return summary
