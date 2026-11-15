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
    "imprensa": [("@jornal_da_manha_ficticio", "Jornal da Manhã (fictício)"), ("@radio_noticia_ficticia", "Rádio Notícia (fictícia)"), ("@portal_do_dia_ficticio", "Portal do Dia (fictício)")],
}
PROFILES["apoio"] += [("@vizinha_que_apoia", "Vizinha que Apoia"), ("@sindicalista_de_bairro", "Sindicalista de Bairro")]
PROFILES["oposicao"] += [("@contador_de_promessas", "Contador de Promessas"), ("@professor_de_cursinho", "Professor de Cursinho")]
PROFILES["humor"] += [("@primo_do_churrasco", "Primo do Churrasco"), ("@gatinho_politico", "Gatinho Político")]
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
TEMPLATES.update({
    "acao_forte": {"apoio": ["{t}: “{m}”. Foi esse o recado que o Brasil queria ouvir.", "“{m}” — {t}. Quem estava lá saiu convencido."],
                   "oposicao": ["{t} e o discurso “{m}”. Bonito no palanque; falta mostrar como fecha a conta.", "“{m}”… e na prática, quando?"],
                   "humor": ["“{m}”: o trecho de {t} que já virou áudio de grupo da família.", "{t} rendeu uma frase que vai ser cobrada na ceia."],
                   "imprensa": ["Em {t}, candidato afirma: “{m}”. Fala repercute entre eleitores."]},
    "acao_media": {"apoio": ["{t}: “{m}”. Campanha é construção, e hoje foi um bom dia.", "Mais um dia de rua: {t}."],
                   "oposicao": ["{t} e “{m}”. Nada de novo sob o sol.", "Comício, discurso, promessa… e as respostas?"],
                   "humor": ["{t}: “{m}”. O grupo de zap ficou dividido entre aplaudir e conferir.", "Frase de {t} ganhou 3 interpretações no jantar."],
                   "imprensa": ["{t}: candidato repete pontos centrais da campanha."]},
    "acao_fraca": {"apoio": ["{t} não foi o melhor dia, mas a campanha segue. “{m}” foi tirado de contexto.", "Todo mundo tem um dia ruim. {t} ficou para trás."],
                   "oposicao": ["“{m}”? Isso foi sério? {t} deixou mais dúvidas que respostas.", "{t}: faltou preparo, faltou conteúdo."],
                   "humor": ["“{m}”: o corte de {t} que ninguém pediu e todo mundo compartilhou.", "{t} virou meme antes de acabar."],
                   "imprensa": ["Fala em {t} gera críticas; equipe diz que foi mal interpretada."]},
    "viral": {"apoio": ["Estourou! {t} bateu recorde de alcance. 🚀", "A campanha viralizou: {t}."],
              "oposicao": ["Viralizou, mas voto não vem de curtida. {t}.", "Muito barulho em {t}; e as propostas?"],
              "humor": ["{t} viralizou até na tia que não usa internet.", "O algoritmo escolheu um lado: {t}."],
              "imprensa": ["Publicação de {t} alcança grande audiência nas redes."]},
})

TEMPLATES.update({
    "inflacao_alta": {"apoio": ["Inflação em {v}%: o governo está de olho e as medidas já estão a caminho.", "Preço sobe no mundo todo; aqui a resposta já começou. Inflação em {v}%."],
                      "oposicao": ["Inflação em {v}%. A feira que o governo nunca visita já sentiu.", "{v}% de inflação e nenhuma explicação convincente."],
                      "humor": ["Inflação em {v}%: o tomate virou joia e o cafezinho, investimento.", "Com {v}% de inflação, a lista do mercado agora vem com orçamento."],
                      "imprensa": ["Inflação anual chega a {v}%; economistas fictícios divergem sobre o ritmo de queda."]},
    "desemprego_alto": {"apoio": ["Desemprego em {v}%: cada vaga criada é uma família que respira.", "Estamos trabalhando para reduzir os {v}% de desemprego."],
                        "oposicao": ["{v}% de desemprego. Quem disse que a economia ia bem?", "O trabalhador sentiu: desemprego em {v}%."],
                        "humor": ["Desemprego em {v}%: o LinkedIn virou novela das oito.", "Com {v}% de desemprego, até o currículo pede currículo."],
                        "imprensa": ["Desemprego em {v}%; mercado de trabalho segue no centro do debate."]},
    "aprovacao_baixa": {"apoio": ["Aprovação em {v}%? Governar é decidir o que é difícil. Seguimos.", "A pesquisa é retrato; o trabalho é filme. {v}% hoje."],
                        "oposicao": ["Aprovação de {v}%. O recado das ruas é claro.", "{v}% de aprovação: hora de ouvir mais e anunciar menos."],
                        "humor": ["Aprovação em {v}%: até o pombo da praça pediu transferência.", "{v}%: o governo pediu revisão da pesquisa; a pesquisa pediu revisão do governo."],
                        "imprensa": ["Aprovação do governo fica em {v}% na pesquisa simulada."]},
    "aprovacao_alta": {"apoio": ["Aprovação em {v}%! Obrigado a quem acredita no trabalho.", "{v}% de aprovação e muito trabalho pela frente."],
                       "oposicao": ["Aprovação em {v}% não paga a conta de luz. Falta resultado.", "{v}% hoje; amanhã é outro dia."],
                       "humor": ["Aprovação em {v}%: o governo anunciou que vai comemorar... depois da reunião.", "{v}%: a tia do zap mudou o bom-dia para o governo."],
                       "imprensa": ["Governo tem aprovação de {v}% na pesquisa simulada."]},
})
for _k, _extra in {
    "crise": {"apoio": ["Defesa Civil, prefeituras e governo juntos em “{t}”.", "Sem politizar: “{t}” exige trabalho, e o trabalho começou."],
              "oposicao": ["“{t}” não é surpresa para quem acompanha. Cadê o plano?", "Quando vem “{t}”, o improviso aparece."],
              "humor": ["“{t}” e o prédio inteiro virou comitê de crise no grupo.", "A crise é “{t}”; o meme chegou antes do relatório."],
              "imprensa": ["Governo acompanha “{t}”; reunião de emergência prevista, segundo fontes fictícias."]},
    "decisao_boa": {"apoio": ["“{t}” saiu e já tem gente sentindo no bolso.", "Promessa feita, “{t}” entregue."],
                    "oposicao": ["“{t}” é um começo. A pergunta é de onde vem o dinheiro.", "Aplaudo “{t}”, mas quero ver a execução."],
                    "humor": ["“{t}”: a única notícia boa que o grupo da família não discutiu.", "Anunciaram “{t}” e a oposição pediu um minuto para pensar."],
                    "imprensa": ["“{t}” é publicado; especialistas fictícios veem efeito gradual."]},
    "decisao_ruim": {"apoio": ["“{t}” não saiu como queríamos, mas aprendemos e seguimos.", "Revés em “{t}” não muda o rumo."],
                     "oposicao": ["“{t}” deu errado e o governo vai culpar quem desta vez?", "Alguém avisa que “{t}” precisava de votos."],
                     "humor": ["“{t}” virou aula de como não fazer.", "Se “{t}” fosse prova, o governo pediria segunda chamada."],
                     "imprensa": ["“{t}” não avança; governo promete nova tentativa."]},
}.items():
    for _kind, _texts in _extra.items():
        TEMPLATES[_k][_kind] += _texts

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
    metrics = state.get("metrics") or {}
    month = str(state["date"])[:7]
    if float(metrics.get("inflation", 0) or 0) >= 6.0:
        facts.append({"id": f"i{month}", "date": state["date"], "tmpl": "inflacao_alta", "fmt": {"v": f"{float(metrics['inflation']):.1f}".replace(".", ",")}, "origin": "Inflação", "tab": "Indicadores"})
    if float(metrics.get("unemployment", 0) or 0) >= 8.5:
        facts.append({"id": f"u{month}", "date": state["date"], "tmpl": "desemprego_alto", "fmt": {"v": f"{float(metrics['unemployment']):.1f}".replace(".", ",")}, "origin": "Desemprego", "tab": "Indicadores"})
    approval = metrics.get("approval")
    if approval is not None and (float(approval) < 35 or float(approval) >= 60):
        facts.append({"id": f"p{month}", "date": state["date"], "tmpl": "aprovacao_baixa" if float(approval) < 35 else "aprovacao_alta",
                      "fmt": {"v": f"{float(approval):.1f}".replace(".", ",")}, "origin": "Aprovação do governo", "tab": "Indicadores"})
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
    activities = list(campaign.get("activities") or []) + list(career.get("activities") or [])
    for a in sorted(activities, key=lambda x: str(x.get("date", "")))[-6:]:
        score = a.get("score")
        place = a.get("municipality_name") or a.get("region_label") or a.get("region") or "campanha"
        label = str(a.get("label") or a.get("type") or "Atividade")
        msg = " ".join(str(a.get("message") or "").split())
        snippet = (msg[:70].rstrip() + ("…" if len(msg) > 70 else "")) if msg else "o recado do dia"
        virality = int(((a.get("social_result") or {}).get("virality_pct")) or 0)
        tmpl = "viral" if virality >= 70 else "acao_forte" if (score or 0) >= 75 else "acao_fraca" if (score or 100) < 55 else "acao_media"
        facts.append({"id": f"a{a.get('id') or a.get('date')}", "date": str(a.get("date") or state["date"]), "tmpl": tmpl,
                      "fmt": {"t": f"{label} em {place}", "m": snippet}, "origin": f"{label} em {place}", "tab": "Eleição"})
    posts: list[dict[str, Any]] = []
    for fact in facts:
        kinds = ["apoio", "oposicao", "humor"] + (["imprensa"] if fact["tmpl"] in ("crise", "eleicao_ganhou", "eleicao_perdeu", "decisao_ruim", "viral", "acao_fraca") else [])
        order = sorted(kinds, key=lambda k: hashlib.sha256(f"{state.get('campaign_seed', 1)}:{fact['id']}:{k}".encode()).hexdigest())
        for kind in order[:3]:
            posts.append(_post(state, fact, kind, fact["tmpl"], **fact["fmt"]))
    posts.sort(key=lambda p: (p["date"], p["reach"]), reverse=True)
    return {"posts": posts[:limit], "total": len(posts),
            "note": "Perfis e frases são fictícios e satíricos. O alcance é estimado pelo motor a partir do caixa de campanha, do momentum e do tipo de perfil."}
