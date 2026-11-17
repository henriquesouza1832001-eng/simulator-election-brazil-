"""Nota de um discurso de campanha a partir de uma *leitura estruturada* do texto.

A leitura vem do Gemini (app/ai/speech_reader.py) ou, se ele falhar, de uma leitura local por palavras-chave. Qualquer
que seja a origem, quem decide a nota é este módulo, com regras fixas: a IA só diz o que está escrito (temas, promessas,
ataques, tom); o motor converte isso em pontos. Julgamentos que dependem do modelo (promessa fora da competência do cargo,
promessa irrealista, risco legal) têm teto de efeito, para um erro do modelo nunca quebrar uma eleição.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any

TONES = ["propositivo", "comparativo", "tecnico", "emocional", "populista", "ataque"]
LEGAL = ["nenhum", "propaganda_antecipada", "desinformacao", "abuso_de_poder", "discurso_de_odio"]
TONE_LABEL = {"propositivo": "propositivo", "comparativo": "compara propostas", "tecnico": "técnico", "emocional": "emocional", "populista": "populista", "ataque": "ataque"}
LEGAL_LABEL = {"nenhum": "nenhum", "propaganda_antecipada": "propaganda antecipada", "desinformacao": "desinformação", "abuso_de_poder": "abuso de poder", "discurso_de_odio": "discurso de ódio"}
LEGAL_PENALTY = {"nenhum": 0, "propaganda_antecipada": 8, "desinformacao": 15, "abuso_de_poder": 18, "discurso_de_odio": 25}
MODEL_JUDGEMENT_CAP = 25   # teto da soma de penalidades que dependem de julgamento do modelo
PROMISE_VERBS = ("vou ", "vamos ", "farei", "faremos", "criar", "criarei", "construir", "construirei", "reduzir", "reduzirei", "ampliar", "ampliarei", "garantir",
                 "garantirei", "entregar", "entregarei", "implantar", "zerar", "acabar com", "dobrar", "contratar", "investir")
DEADLINE = ("prazo", "meses", "mes ", "anos", "dias", "semanas", "ate 20", "ate o fim", "no primeiro ano", "primeiros 100")
FUNDING = ("orcamento", "recurso", "verba", "financiad", "custo", "r$", "emenda", "parceria", "sem aumentar")
ATTACK_WORDS = ("lixo", "vagabundo", "traidor", "inimigo do povo", "bandido", "ladrao", "safado", "canalha")
EXAGGERATION = ("resolver tudo", "nunca mais", "sem custo", "acabar com todo", "em 24 horas", "garanto tudo", "problema nenhum")
COMPARE = ("enquanto", "diferente de", "ao contrario de", "o adversario", "meu oponente", "nossa proposta e")
EMPATHY = ("familia", "morador", "trabalhador", "aluno", "paciente", "bairro", "comunidade", "escutar", "ouvir", "respeito", "cuidado", "medo", "onibus", "mae", "idoso")
LEGAL_HINTS = {"propaganda_antecipada": ("votem em mim", "vote em mim", "meu numero", "me elejam"), "discurso_de_odio": ("raca inferior", "essa gente", "tem que sumir")}


def _plain(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", text.lower()) if unicodedata.category(c) != "Mn")


def _clip(value: Any, limit: int) -> str:
    return " ".join(str(value or "").split())[:limit]


def local_reading(text: str, issue: str, career: dict[str, Any], issues: dict[str, Any]) -> dict[str, Any]:
    """Leitura por palavras-chave: reserva quando o Gemini não responde. Não julga competência nem realismo (assume que cabem)."""
    plain = _plain(text)
    themes = [key for key, data in issues.items() if any(_plain(t) in plain for t in data.get("terms", ()))] or [issue]
    sentences = [s.strip() for s in re.split(r"[.!?\n]+", text) if s.strip()]
    promises = []
    for sentence in sentences:
        low = _plain(sentence)
        if any(v in low for v in PROMISE_VERBS):
            promises.append({"text": _clip(sentence, 140), "measurable": bool(re.search(r"\d", low)), "has_deadline": any(d in low for d in DEADLINE),
                             "funding_stated": any(f in low for f in FUNDING), "within_competence": True, "realistic": not any(e in low for e in EXAGGERATION)})
    attack_hits = [w for w in ATTACK_WORDS if w in plain]
    tone = "ataque" if attack_hits else "populista" if any(e in plain for e in EXAGGERATION) else "comparativo" if any(c in plain for c in COMPARE) else "propositivo"
    legal = next((risk for risk, hints in LEGAL_HINTS.items() if any(h in plain for h in hints)), "nenhum")
    words = len(re.findall(r"\w+", plain))
    clarity = 0.85 if 18 <= words <= 90 else 0.55 if 10 <= words <= 130 else 0.25
    return {"source": "local", "summary": _clip(sentences[0] if sentences else text, 160), "themes": themes[:4], "target_groups": list(issues.get(issue, {}).get("groups", []))[:4],
            "tone": tone, "promises": promises[:4], "attacks": [{"target": "adversario", "personal": True}] if attack_hits else [], "legal_risk": legal,
            "clarity": clarity, "local_connection": min(1.0, sum(1 for e in EMPATHY if e in plain) / 4)}


def normalize(raw: Any, text: str, issue: str, issues: dict[str, Any], rival_ids: list[str], source: str = "gemini") -> dict[str, Any]:
    """Aceita só campos conhecidos e valores dentro de faixas; qualquer coisa fora vira o padrão neutro."""
    raw = raw if isinstance(raw, dict) else {}
    themes = [t for t in (raw.get("themes") or []) if t in issues][:4] or [issue]
    groups = [g for g in (raw.get("target_groups") or []) if isinstance(g, str)][:4]
    promises = []
    for item in (raw.get("promises") or [])[:4]:
        if isinstance(item, dict) and item.get("text"):
            promises.append({"text": _clip(item["text"], 140), "measurable": bool(item.get("measurable")), "has_deadline": bool(item.get("has_deadline")),
                             "funding_stated": bool(item.get("funding_stated")), "within_competence": item.get("within_competence") is not False,
                             "realistic": item.get("realistic") is not False})
    allowed_targets = set(rival_ids) | {"adversario", "governo", "imprensa", "instituicoes", "ninguem"}
    attacks = [{"target": a.get("target") if a.get("target") in allowed_targets else "adversario", "personal": bool(a.get("personal"))}
               for a in (raw.get("attacks") or [])[:3] if isinstance(a, dict)]
    try:
        clarity = max(0.0, min(1.0, float(raw.get("clarity", 0.6))))
        local_connection = max(0.0, min(1.0, float(raw.get("local_connection", 0.3))))
    except (TypeError, ValueError):
        clarity, local_connection = 0.6, 0.3
    return {"source": source, "summary": _clip(raw.get("summary") or text, 160), "themes": themes, "target_groups": groups,
            "tone": raw.get("tone") if raw.get("tone") in TONES else "propositivo", "promises": promises, "attacks": attacks,
            "legal_risk": raw.get("legal_risk") if raw.get("legal_risk") in LEGAL else "nenhum", "clarity": clarity, "local_connection": local_connection}


def score_reading(reading: dict[str, Any], issue: str) -> tuple[int, dict[str, int]]:
    themes = reading.get("themes") or []
    relevance = 18 if issue in themes else 4 if themes else -4
    concrete = 0
    for p in reading.get("promises") or []:
        concrete += 4 * bool(p.get("measurable")) + 3 * bool(p.get("has_deadline")) + 3 * bool(p.get("funding_stated"))
    concrete = min(20, concrete)
    local = round(15 * float(reading.get("local_connection", 0.0)))
    clarity = round(10 * float(reading.get("clarity", 0.0)))
    tone = reading.get("tone", "propositivo")
    tone_points = {"propositivo": 6, "tecnico": 6, "emocional": 3, "comparativo": 3, "populista": -8, "ataque": -8}.get(tone, 0)
    personal = -12 if any(a.get("personal") for a in reading.get("attacks") or []) else 0
    promises = reading.get("promises") or []
    unrealistic = -4 * sum(1 for p in promises if not p.get("realistic", True))
    out_of_scope = -5 * sum(1 for p in promises if not p.get("within_competence", True))
    legal = -LEGAL_PENALTY.get(reading.get("legal_risk", "nenhum"), 0)
    judged = max(-MODEL_JUDGEMENT_CAP, unrealistic + out_of_scope + legal)
    score = max(0, min(100, 40 + relevance + concrete + local + clarity + tone_points + personal + judged))
    rubric = {"pertinência do tema": relevance, "proposta verificável": concrete, "conexão local": local, "clareza": clarity, "tom do discurso": tone_points,
              "ataque pessoal": personal, "promessa fora do alcance": judged}
    return score, rubric


def public(reading: dict[str, Any], issues: dict[str, Any], rival_names: dict[str, str]) -> dict[str, Any]:
    """Versão para a tela: o que o eleitorado entendeu, em português e sem campos internos."""
    flags = []
    for p in reading.get("promises") or []:
        if not p.get("within_competence", True):
            flags.append(f"Fora das competências do cargo: “{p['text']}”")
        if not p.get("realistic", True):
            flags.append(f"Promessa irrealista: “{p['text']}”")
    if reading.get("legal_risk", "nenhum") != "nenhum":
        flags.append(f"Risco legal: {LEGAL_LABEL[reading['legal_risk']]}")
    return {"source": reading.get("source", "local"), "summary": reading.get("summary", ""),
            "themes": [issues[t]["label"] for t in reading.get("themes", []) if t in issues], "tone": TONE_LABEL.get(reading.get("tone"), "propositivo"),
            "promises": [{"text": p["text"], "measurable": p["measurable"], "deadline": p["has_deadline"], "funding": p["funding_stated"]} for p in reading.get("promises", [])],
            "attacks": [{"target": rival_names.get(a["target"], a["target"]), "personal": a["personal"]} for a in reading.get("attacks", [])],
            "legal_risk": LEGAL_LABEL.get(reading.get("legal_risk", "nenhum")), "flags": flags}
