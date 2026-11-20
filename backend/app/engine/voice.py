"""Guia de voz do jogo: o tom da sátira nas notícias que o motor escreve.

Regras (ver docs/GUIA_DE_VOZ.md): os números vêm sempre do motor e aparecem inteiros no texto; o humor fica nas frases, nunca no fato;
sem a palavra "simulação/simulado" dentro da narrativa (o aviso de ficção fica no rodapé e na tela inicial); personagens e veículos são
inventados, nunca pessoas reais; ironia mira o sistema e os hábitos políticos, não pessoas, minorias ou tragédias.
Cada tipo de notícia tem várias variantes e a escolha é determinística pela semente da partida, então a mesma partida sempre conta
a mesma história.
"""
from __future__ import annotations

import hashlib


def pick(options: list[str], seed: str) -> str:
    """Escolha estável: a mesma semente sempre devolve a mesma variante."""
    return options[int(hashlib.sha256(seed.encode()).hexdigest()[:8], 16) % len(options)]


PRESS_UP = [
    "Jornais e portais repercutem a decisão; colunistas já escreveram o texto antes de ler o decreto.",
    "A imprensa registra a decisão e o debate esquenta: cada comentarista descobre que sempre soube que ia dar nisso.",
    "Manchetes do dia tratam da decisão. Especialistas divergem, como manda a tradição.",
]
PRESS_DOWN = [
    "A decisão cai mal nas manchetes; os editoriais acordaram inspirados.",
    "Jornais e portais criticam a decisão e os analistas de plantão pedem 'mais diálogo', sem dizer com quem.",
    "A repercussão é fria: a decisão rendeu mais nota de rodapé que aplauso.",
]
OPPOSITION = [
    "O {party} anuncia oposição à medida e promete dificultar as votações ligadas ao tema, de preferência com microfone ligado.",
    "A bancada do {party} sobe à tribuna contra a medida; o plenário esvazia, mas a ata registra.",
    "O {party} chama a medida de erro histórico. É a terceira vez este mês que algo é histórico.",
]
SUPPORT = [
    "O {party} defende a medida e promete ajudar na tramitação, a depender, claro, de uma conversa sobre cargos.",
    "A bancada do {party} ergue a bandeira da medida e já avisa que é de coração (e de emenda).",
    "O {party} apoia a medida e diz que votará a favor, o que no Congresso significa 'depende do quê'.",
]
MARKET_BY_DECISION = [
    "Investidores reavaliam risco e câmbio; a mesa de operações descobriu que o Brasil existe de novo.",
    "A Faria Lima faz as contas da medida e, por enquanto, muda de ideia só no dólar.",
    "O mercado digere a decisão com a calma de quem tem cinco planilhas abertas.",
]
POLL_LEAD = [
    "A pesquisa saiu e os comitês já a leem como querem: quem lidera chama de tendência, quem perde chama de retrato.",
    "Novo levantamento mexe com a cidade; a margem de erro foi citada em todos os discursos, menos nos de quem está na frente.",
]
POLL_TRAIL = [
    "O levantamento acende o alerta no comitê; ninguém assume, mas a reunião de segunda ficou mais comprida.",
    "A pesquisa não agradou: a campanha promete reagir e a margem de erro vira assunto de primeira hora.",
]
EXPIRED_PAUTA = "O prazo de 15 dias úteis terminou sem decisão; vale a sanção tácita: o silêncio também assina."
EXPIRED_CRISIS = "O prazo passou, ninguém respondeu e a crise tomou a vaga do governo na pauta."
MARKET_DESC = [
    "Os operadores comentam o dia; nenhum previu, todos explicam.",
    "A tela do mercado piscou e os analistas já têm a teoria.",
    "Bolsa e dólar se mexeram; a causa vai depender de quem for perguntado.",
]


def market_day(seed: str, bolsa_pct: float, cambio_pct: float, risco_bps: float, pct, sign) -> str:
    """Manchete do mercado no período; `pct` e `sign` formatam números no padrão brasileiro. Os valores aparecem todos, inalterados."""
    nums = f"dólar {pct(cambio_pct)}, bolsa {pct(bolsa_pct)}, risco-país {sign(risco_bps)}"
    if bolsa_pct <= -3 or cambio_pct >= 3 or risco_bps >= 30:
        opening = pick(["Mesas de operação em pânico educado", "Terça-feira de mercado com cara de segunda", "A tela do mercado ficou vermelha e o café esfriou"], seed + "d")
    elif bolsa_pct >= 3 or cambio_pct <= -3 or risco_bps <= -30:
        opening = pick(["A Faria Lima acordou otimista", "Mercado em dia de festa discreta", "O pregão ensaiou um sorriso"], seed + "u")
    else:
        opening = pick(["Mercado em movimento", "O mercado mexeu, mas sem drama"], seed + "n")
    return f"{opening}: {nums} no período."


def market_reaction(seed: str, label: str, verb_d: str, verb_b: str, cambio_abs: str, bolsa_abs: str, risco: str) -> str:
    opening = pick(["Mercado reage a", "O mercado leu", "A mesa de operações comentou"], seed + "r")
    return f"{opening} {label}: dólar {verb_d} {cambio_abs}, bolsa {verb_b} {bolsa_abs}, risco-país {risco} pontos."
