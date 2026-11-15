"""Redes sociais fictícias: o motor decide o que aconteceu e o alcance; a voz das publicações é satírica e inventada.

Cada publicação nasce de um fato do jogo (decisão, crise, pesquisa, resultado) e traz o alcance estimado pelo motor.
Perfis, nomes e frases são fictícios e não representam pessoas ou páginas reais. Até a 0.6 as frases vêm de modelos
guiados pelo motor; na 0.7 o Gemini só reescreve o tom, sem decidir nada.
"""
from __future__ import annotations

import hashlib
from typing import Any

PROFILES = {
    "apoio": [("@militante_de_plantao", "Militante de Plantão"), ("@tia_do_zap_oficial", "Tia do Zap"), ("@coluna_da_base", "Coluna da Base")],
    "oposicao": [("@analista_de_sofa", "Analista de Sofá"), ("@economista_de_bar", "Economista de Bar"), ("@fiscal_de_tudo", "Fiscal de Tudo")],
    "humor": [("@meme_do_planalto", "Meme do Planalto"), ("@tio_do_pave", "Tio do Pavê"), ("@satira_diaria", "Sátira Diária")],
    "imprensa": [("@jornal_da_manha_ficticio", "Jornal da Manhã (fictício)"), ("@radio_noticia_ficticia", "Rádio Notícia (fictícia)")],
}
TEMPLATES = {
    "decisao_boa": {"apoio": ["Decisão certeira: “{t}”. Quem disse que não dava? 👏", "“{t}” saiu do papel. Enquanto uns falam, outros fazem."],
                    "oposicao": ["“{t}”… vamos ver quem paga essa conta.", "Anunciou “{t}”. Falta explicar o prazo e o custo."],
                    "humor": ["“{t}”: o plano que até o grupo da família aprovou (por enquanto).", "Quando o governo faz “{t}” e a oposição fica sem pauta."],
                    "imprensa": ["Governo anuncia “{t}”. Efeitos só aparecem nos próximos meses, dizem analistas fictícios."]},
    "decisao_ruim": {"apoio": ["Calma, gente: “{t}” precisa de tempo para dar resultado.", "Quem critica “{t}” não leu o documento inteiro."],
                     "oposicao": ["“{t}” foi barrada ou deu errado. Precisava mesmo?", "Mais uma: “{t}”. Alguém avisa o governo que a conta chega."],
                     "humor": ["“{t}” teve a estreia de um filme de desastre.", "Se “{t}” fosse prova, o gabarito era chute."],
                     "imprensa": ["Revés para o governo: “{t}” não avançou como o esperado."]},
    "crise": {"apoio": ["Crise: “{t}”. É hora de união, não de politicagem.", "Já tem equipe em campo para “{t}”."],
              "oposicao": ["“{t}” e o governo ainda estuda a resposta?", "Cobrar não é torcer contra: “{t}” exige ação agora."],
              "humor": ["“{t}” e o grupo do prédio já tem três especialistas.", "O Brasil descobriu hoje que sabe de tudo sobre “{t}”."],
              "imprensa": ["“{t}” domina o noticiário; governo avalia opções de resposta."]},
    "pesquisa_alta": {"apoio": ["Pesquisa fictícia mostra {v}% de apoio. O povo sabe!", "{v}% e subindo. A conta fecha."],
                      "oposicao": ["Pesquisa é retrato, não filme. {v}% hoje, amanhã quem sabe.", "Margem de erro existe, sim: {v}%."],
                      "humor": ["Apoio em {v}%: até o cachorro do vizinho está de bandeirinha.", "{v}% e a tia já mandou o áudio de 4 minutos."],
                      "imprensa": ["Pesquisa simulada: apoio em {v}%, tendência de alta."]},
    "pesquisa_baixa": {"apoio": ["{v}% hoje, mas campanha é maratona.", "Pesquisa não ganha eleição. {v}% é só ponto de partida."],
                       "oposicao": ["{v}%. A conta do desgaste chegou.", "Com {v}%, o recado das ruas é claro."],
                       "humor": ["{v}% de apoio: o time precisa de um VAR.", "Pesquisa em {v}%: o grupo da família abriu enquete paralela."],
                       "imprensa": ["Pesquisa simulada mostra apoio em {v}% e cenário de disputa aberta."]},
    "eleicao_ganhou": {"apoio": ["Ganhou! Obrigado a todo mundo que acreditou. 🇧🇷", "Resultado nas urnas: vitória. Agora é trabalhar."],
                       "oposicao": ["Resultado reconhecido. Vamos fiscalizar cada passo.", "Perdemos, mas a oposição começa hoje."],
                       "humor": ["Apuração terminou e o grupo da família segue discutindo.", "A noite acabou, o café não."],
                       "imprensa": ["Fim da apuração simulada: vitória do candidato do jogador."]},
    "eleicao_perdeu": {"apoio": ["Não foi dessa vez, mas a história continua.", "Derrota nas urnas. Reorganizar e voltar."],
                       "oposicao": ["Vitória nas urnas. Obrigado ao povo.", "O voto falou. Respeito ao resultado."],
                       "humor": ["Apuração: o suspense foi maior que o resultado.", "Perdeu a eleição, mas ganhou o direito de dizer “eu avisei”."],
                       "imprensa": ["Fim da apuração simulada: derrota do candidato do jogador."]},
}
GOOD = ("aprov", "conclu", "sancion", "execut", "decidid", "respond")
BAD = ("rejeit", "veto", "barr", "agrav", "negad", "sem resposta")


def _pick(seq: list[Any], seed: str) -> Any:
    return seq[int(hashlib.sha256(seed.encode()).hexdigest()[:8], 16) % len(seq)]


def _reach(state: dict[str, Any], kind: str, seed: str) -> int:
    """Alcance estimado (pessoas): cresce com o caixa de campanha e o momentum; humor viraliza mais que imprensa."""
    campaign = state.get("campaign") or {}
    funds = float(campaign.get("funds_bi") or 0.0)
    momentum = float(campaign.get("momentum") or 0.0)
    base = 8000 + funds * 90000 + max(0.0, momentum) * 4000
    factor = {"humor": 2.4, "apoio": 1.0, "oposicao": 1.3, "imprensa": 3.0}[kind]
    jitter = 0.7 + 0.6 * (int(hashlib.sha256(seed.encode()).hexdigest()[8:12], 16) / 0xFFFF)
    return int(base * factor * jitter)


def _post(state: dict[str, Any], fact: dict[str, Any], kind: str, tmpl: str, **fmt: Any) -> dict[str, Any]:
    seed = f"{state.get('campaign_seed', 1)}:{fact['id']}:{kind}"
    handle, name = _pick(PROFILES[kind], seed + "h")
    text = _pick(TEMPLATES[tmpl][kind], seed + "t").format(**fmt)
    reach = _reach(state, kind, seed)
    return {"id": f"{fact['id']}-{kind}", "date": fact["date"], "kind": kind, "handle": handle, "name": name, "text": text,
            "reach": reach, "likes": int(reach * (0.04 + 0.05 * (int(hashlib.sha256(seed.encode()).hexdigest()[12:16], 16) / 0xFFFF))),
            "origin": fact["origin"], "tab": fact.get("tab")}


def build(state: dict[str, Any], limit: int = 24) -> dict[str, Any]:
    facts: list[dict[str, Any]] = []
    for e in (state.get("ledger") or [])[:10]:
        status = str(e.get("status") or "").lower()
        tone = "decisao_ruim" if any(b in status for b in BAD) else "decisao_boa"
        facts.append({"id": f"l{e.get('id')}", "date": e.get("date") or state["date"], "tmpl": tone, "fmt": {"t": str(e.get("title", "decisão"))[:70]},
                      "origin": f"Decisão: {e.get('title', '')[:50]}", "tab": "Histórico"})
    for c in state.get("active_crises") or []:
        facts.append({"id": f"c{c.get('id')}", "date": state["date"], "tmpl": "crise", "fmt": {"t": str(c.get("title", "crise"))[:70]},
                      "origin": f"Crise: {c.get('title', '')[:50]}", "tab": "Crises"})
    campaign = state.get("campaign") or {}
    if campaign.get("national_support") is not None and campaign.get("activities"):
        support = round(float(campaign["national_support"]), 1)
        facts.append({"id": f"p{state['date']}", "date": state["date"], "tmpl": "pesquisa_alta" if support >= 50 else "pesquisa_baixa",
                      "fmt": {"v": f"{support:.1f}".replace(".", ",")}, "origin": "Pesquisa de apoio", "tab": "Eleição"})
    election = state.get("election") or {}
    career = state.get("career") or {}
    result = election.get("result") or career.get("result")
    if result in ("won", "lost"):
        facts.append({"id": f"e{election.get('date') or state['date']}", "date": str(election.get("date") or state["date"]),
                      "tmpl": "eleicao_ganhou" if result == "won" else "eleicao_perdeu", "fmt": {}, "origin": "Resultado da eleição", "tab": "Apuração"})
    posts: list[dict[str, Any]] = []
    for fact in facts:
        kinds = ["apoio", "oposicao", "humor"] + (["imprensa"] if fact["tmpl"] in ("crise", "eleicao_ganhou", "eleicao_perdeu", "decisao_ruim") else [])
        order = sorted(kinds, key=lambda k: hashlib.sha256(f"{state.get('campaign_seed', 1)}:{fact['id']}:{k}".encode()).hexdigest())
        for kind in order[:3]:
            posts.append(_post(state, fact, kind, fact["tmpl"], **fact["fmt"]))
    posts.sort(key=lambda p: (p["date"], p["reach"]), reverse=True)
    return {"posts": posts[:limit], "total": len(posts),
            "note": "Perfis e frases são fictícios e satíricos. O alcance é estimado pelo motor a partir do caixa de campanha, do momentum e do tipo de perfil."}
