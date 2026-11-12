"""Avaliação de respostas por contexto, não por palavras-chave.

A resposta é lida contra o funcionamento do país modelado no jogo:
  - Relevância causal: as ações e indicadores citados realmente influenciam o indicador da pergunta (grafo do registro)?
  - Viabilidade e competência: o cargo pode fazer o que prometeu? Há vedação, aprovação do Congresso ou risco jurídico?
  - Dados: números coerentes com o fato apresentado.
  - Compromisso e tom: prazo, responsável e respeito.
O texto é mapeado para ações do catálogo e para indicadores do registro (regras locais; o Gemini, quando ativo, só ajuda
o mapeamento de ações e nunca dá nota). Sem leitura possível, a nota diz o que faltou em vez de inventar.
"""
from __future__ import annotations

import re
from typing import Any

from .action_mapper import plain, rank, tokens
from .indicator_registry import REGISTRY

ALIASES: dict[str, list[str]] = {
    "inflacao": ["inflacao", "ipca", "custo de vida", "precos"], "juros": ["juros", "selic", "copom"], "desemprego": ["desemprego", "emprego", "vagas", "ocupacao"],
    "pobreza": ["pobreza", "pobres"], "extrema_pobreza": ["fome", "miseria", "extrema pobreza"], "gini": ["desigualdade", "concentracao de renda", "gini"],
    "divida_pib": ["divida"], "resultado_primario": ["deficit", "superavit", "contas publicas", "gasto publico", "arcabouco", "equilibrio fiscal", "resultado primario"],
    "investimento_publico": ["investimento", "obras"], "pib": ["crescimento", "economia", "atividade economica", "pib"], "crescimento_pib": ["crescimento", "pib"],
    "mobilidade": ["transporte", "onibus", "metro", "transito", "mobilidade"], "seguranca": ["seguranca", "policia", "violencia", "crime", "guarda"],
    "homicidios": ["homicidios", "assassinatos"], "saude_atencao": ["saude", "posto de saude", "hospital", "sus", "ubs"],
    "educacao_fundamental": ["escola", "creche", "ensino fundamental", "educacao"], "educacao_medio": ["ensino medio"], "saneamento_basico": ["esgoto", "saneamento", "agua"],
    "agua_encanada": ["agua encanada", "abastecimento"], "esperanca_vida": ["expectativa de vida", "esperanca de vida"], "mortalidade_infantil": ["mortalidade infantil"],
    "transferencias": ["bolsa familia", "transferencia de renda", "auxilio", "renda minima"], "salario_minimo": ["salario minimo"], "carga_tributaria": ["imposto", "tributo", "reforma tributaria", "tributaria"],
    "integridade": ["transparencia", "corrupcao", "integridade", "controle interno", "controladoria"], "base_legislativa": ["congresso", "base aliada", "aliados", "partidos", "negociacao", "bancada"],
    "aprovacao": ["aprovacao", "popularidade"], "confianca_institucional": ["instituicoes", "confianca institucional"], "desmatamento": ["desmatamento", "floresta", "amazonia"],
    "cambio": ["dolar", "cambio"], "energia": ["energia", "luz"], "idhm": ["desenvolvimento humano", "idh"], "formalizacao": ["informalidade", "carteira assinada", "formalizacao"],
    "logistica": ["logistica", "frete", "rodovia", "ferrovia", "porto"], "balanca_comercial": ["exportacao", "importacao", "balanca comercial"],
}
METRIC_TO_REGISTRY = {"gdp_growth": ["crescimento_pib", "pib"], "inflation": ["inflacao"], "unemployment": ["desemprego"], "approval": ["aprovacao"],
                      "institutional_trust": ["confianca_institucional"], "integrity": ["integridade"], "governability": ["governabilidade"],
                      "congress_support": ["base_legislativa"], "primary_balance": ["resultado_primario"], "trust": ["aprovacao"]}
DOMAIN_TO_REGISTRY = {"banco": ["juros", "inflacao"], "infraestrutura": ["mobilidade", "logistica", "pib"], "seguranca": ["seguranca", "homicidios"], "empresas": ["investimento_publico", "pib"],
                      "exterior": ["balanca_comercial", "pib"], "defesa": ["seguranca"], "economia": ["pib", "inflacao", "desemprego"], "regime": ["confianca_institucional"],
                      "educacao": ["educacao_fundamental"], "saude": ["saude_atencao"], "mobilidade": ["mobilidade"], "saneamento": ["saneamento_basico"], "fiscal": ["resultado_primario"]}
LIMIT_WORDS = ("nao e competencia", "nao compete", "nao cabe a mim", "cabe ao", "cabe a uniao", "cabe ao estado", "cabe ao municipio", "compete ao", "competencia do", "nao posso decidir",
               "fora da minha competencia", "e atribuicao", "atribuicao do", "o banco central decide", "e do congresso", "depende do congresso", "depende da assembleia", "depende da camara")
LAW_WORDS = ("constituicao", "lei", "congresso", "stf", "legal", "licitacao", "camara", "assembleia", "aprovacao", "tribunal")
PRAZO = re.compile(r"\b(em|ate|dentro de|nos proximos|ao longo de)\s+\w*\s*\d*\s*(dias|dia|semanas|meses|mes|ano|anos|trimestre|semestre)\b|\bprazo\b|\bcronograma\b")
RESPONSAVEL = re.compile(r"\b(secretaria|ministerio|prefeitura|governo|comite|orgao|agencia|controladoria|tribunal|congresso|camara|comissao|banco central|conselho|fundo|empresa)\b")
INSULTS = {"idiota", "burro", "mentiroso", "canalha", "ladrao", "vagabundo", "corrupto", "imbecil", "safado", "bandido"}
NUMBER = re.compile(r"\d+(?:[.,]\d+)?")


def indicators_in(text: str) -> set[str]:
    t = plain(text)
    return {key for key, words in ALIASES.items() if key in REGISTRY and any(w in t for w in words)}


def upstream(target: str, depth: int = 2) -> dict[str, tuple[int, int]]:
    """Indicadores que influenciam o alvo: (distância no grafo, força mínima do caminho). Distância 1 = influência direta."""
    found: dict[str, tuple[int, int]] = {}
    frontier = {target: 3}
    for level in range(1, depth + 1):
        nxt: dict[str, int] = {}
        for key, strength in frontier.items():
            for d in REGISTRY.get(key, {}).get("drivers", []):
                if d["from"] not in found and d["from"] != target:
                    path = min(strength, d["strength"])
                    found[d["from"]] = (level, path)
                    nxt[d["from"]] = path
        frontier = nxt
    return found


def action_indicators(action: dict[str, Any]) -> set[str]:
    out: set[str] = set()
    for key in list(action.get("effects", {})):
        out.update(METRIC_TO_REGISTRY.get(key, [key] if key in REGISTRY else []))
    out.update(DOMAIN_TO_REGISTRY.get(action.get("domain", ""), []))
    return {k for k in out if k in REGISTRY}


def _all_actions() -> list[dict[str, Any]]:
    from . import office_powers, powers
    rows = [{"id": a["id"], "title": a["title"], "summary": a["summary"], "options": a["options"], "domain": a["domain"], "effects": a["effects"],
             "offices": {"presidente"}, "approval": a["approval"], "basis": a["basis"]} for a in powers.ACTIONS]
    rows += [{"id": a["id"], "title": a["title"], "summary": a["text"], "options": [], "domain": a["domain"], "effects": {**a["effects"], **a["territory"]},
              "offices": set(a["offices"]), "approval": "pl" if a["kind"] == "leg" else "decreto", "basis": a["basis"]} for a in office_powers._A]
    return rows


def _levers_ok(office: str, key: str) -> bool:
    return office in REGISTRY.get(key, {}).get("levers", {})


def analyze(text: str, office: str, target: str | None, trap: bool = False) -> dict[str, Any]:
    actions = _all_actions()
    matches = rank(text, actions)
    mentioned = {m["id"]: next(a for a in actions if a["id"] == m["id"]) for m in matches}
    inds = indicators_in(text)
    own = [a for a in mentioned.values() if office in a["offices"]]
    foreign = [a for a in mentioned.values() if office not in a["offices"]]
    implied = set(inds)
    for a in mentioned.values():
        implied |= action_indicators(a)
    return {"actions_own": own, "actions_foreign": foreign, "indicators": inds, "implied": implied}


def score(text: str, q: dict[str, Any], office: str) -> dict[str, Any]:
    t = plain(text)
    ctx = analyze(text, office, q.get("target"), bool(q.get("trap")))
    target, trap = q.get("target"), bool(q.get("trap"))
    notes: dict[str, str] = {}

    # --- relevância causal
    if target and target in REGISTRY:
        up = upstream(target)
        label = REGISTRY[target]["label"]
        direct = target in ctx["implied"]
        explicit = target in ctx["indicators"]
        near = sorted((k for k in ctx["implied"] if up.get(k, (9, 0))[0] == 1 and up[k][1] >= 2), key=str)
        far = sorted((k for k in ctx["implied"] if k in up and k not in near), key=str)
        if trap:
            rel = 25.0 if (ctx["actions_own"] or any(_levers_ok(office, k) for k in ctx["implied"])) else 12.0 if ctx["implied"] else 4.0
            notes["relevancia"] = "Ligou a pergunta ao que o seu cargo realmente controla." if rel >= 25 else "Faltou dizer o que o seu cargo pode fazer sobre o assunto."
        elif near or (explicit and ctx["actions_own"]):
            rel = 25.0
            names = ", ".join(REGISTRY[k]["label"].lower() for k in (near or [target])[:3])
            notes["relevancia"] = f"Boa ligação causal: {names} influencia {label.lower()}."
        elif far or direct:
            rel = 17.0
            notes["relevancia"] = f"Ligação indireta com {label.lower()}; explique o caminho (o que muda primeiro)."
        elif ctx["implied"]:
            rel = 7.0
            drivers = ", ".join(REGISTRY[k]["label"].lower() for k in list(up)[:3])
            notes["relevancia"] = f"O que você citou pouco afeta {label.lower()}. O que pesa mais: {drivers}."
        else:
            rel = 0.0
            drivers = ", ".join(REGISTRY[k]["label"].lower() for k in list(up)[:3])
            notes["relevancia"] = f"Não consegui ligar a resposta a {label.lower()}. O que pesa: {drivers or 'veja os indicadores relacionados'}."
    else:
        rel = 20.0 if (ctx["actions_own"] or ctx["implied"]) else 8.0
        notes["relevancia"] = "Resposta ligada a uma ação ou indicador do jogo." if rel >= 20 else "Faltou citar uma ação ou resultado concreto."

    # --- viabilidade e competência
    limit = any(w in t for w in LIMIT_WORDS)
    law = any(w in t for w in LAW_WORDS)
    if trap:
        if limit and (ctx["actions_own"] or ctx["implied"]):
            via = 25.0
            notes["viabilidade"] = "Reconheceu o limite de competência e apontou o que pode fazer."
        elif limit:
            via = 14.0
            notes["viabilidade"] = "Reconheceu o limite, mas faltou dizer o que o seu cargo faz sobre isso."
        elif ctx["actions_foreign"]:
            via = 2.0
            notes["viabilidade"] = "Prometeu algo que não é do seu cargo. Em um debate real, isso vira desmentido."
        else:
            via = 8.0
            notes["viabilidade"] = "Essa pergunta fala de algo fora do seu cargo; explique quem decide e o que você faz."
    else:
        via = 25.0
        if ctx["actions_foreign"] and not limit:
            via -= 12.0 * min(len(ctx["actions_foreign"]), 2)
            notes["viabilidade"] = "Citou ação que não cabe ao seu cargo (" + ", ".join(a["title"].lower() for a in ctx["actions_foreign"][:2]) + ")."
        elif not ctx["actions_own"]:
            via = 12.0
            notes["viabilidade"] = "Faltou dizer o instrumento: o que o seu cargo assina, propõe ou executa."
        else:
            risky = [a for a in ctx["actions_own"] if a.get("approval") in {"pec", "plp", "tratado"}]
            if risky and not law:
                via -= 6.0
                notes["viabilidade"] = "A medida exige " + {"pec": "emenda constitucional", "plp": "lei complementar", "tratado": "aprovação de tratado"}[risky[0]["approval"]] + "; cite como vai aprovar."
            else:
                notes["viabilidade"] = "Instrumento coerente com as competências do cargo."
    # afirmações que o desenho institucional do país não permite, ditas como promessa
    impossible = []
    if ("juros" in ctx["indicators"] or "selic" in t) and re.search(r"\b(por decreto|determino|ordeno|mando|vou fixar|vou cortar a selic|a selic cai)\b", t) and not limit:
        impossible.append("A Selic é decidida pelo Copom; o Banco Central é autônomo (LC 179/2021). Cabe influenciar pela meta e pelas contas, não decretar.")
    if "constituicao" in t and re.search(r"\b(por decreto|ignorar|passar por cima|mudar sozinho)\b", t):
        impossible.append("A Constituição só muda por emenda aprovada pelo Congresso; decreto não altera a Constituição.")
    if impossible and not trap:
        via = max(0.0, via - 15.0)
        notes["viabilidade"] = impossible[0]
    via = max(0.0, via)

    # --- dados
    nums = [float(x.replace(",", ".")) for x in NUMBER.findall(text)]
    fact = q.get("fact")
    if nums and fact:
        near_fact = any(abs(n - fact) <= max(abs(fact) * 0.3, 1.5) for n in nums)
        dados = 25.0 if near_fact else 14.0
        notes["dados"] = "Números coerentes com o dado da pergunta." if near_fact else "Citou números, mas longe do dado apresentado."
    elif nums:
        dados, notes["dados"] = 20.0, "Citou meta ou valor concreto."
    else:
        dados, notes["dados"] = 0.0, "Sem números: cite meta, valor ou prazo mensurável."

    # --- compromisso e tom
    has_deadline, has_owner = bool(PRAZO.search(t)), bool(RESPONSAVEL.search(t))
    comp = (8.0 if has_deadline else 0.0) + (7.0 if has_owner else 0.0)
    tom = max(0.0, 10.0 - 8.0 * sum(1 for w in INSULTS if w in t) - (5.0 if text.isupper() and len(text) > 20 else 0.0))
    comp_total = round(comp + tom, 1)
    pieces = []
    if not has_deadline:
        pieces.append("prazo")
    if not has_owner:
        pieces.append("responsável")
    notes["compromisso"] = ("Deu prazo e responsável. " if not pieces else f"Faltou {' e '.join(pieces)}. ") + ("Tom adequado." if tom >= 10 else "O tom atrapalhou: evite ataques pessoais e caixa alta.")

    total = round(rel + via + dados + comp_total, 1)
    return {"total": total, "criteria": {"relevancia": round(rel, 1), "viabilidade": round(via, 1), "dados": dados, "compromisso": comp_total}, "feedback": notes,
            "read": {"acoes": [a["title"] for a in ctx["actions_own"]][:3], "fora_do_cargo": [a["title"] for a in ctx["actions_foreign"]][:2],
                     "indicadores": [REGISTRY[k]["label"] for k in sorted(ctx["implied"])][:5]}}
