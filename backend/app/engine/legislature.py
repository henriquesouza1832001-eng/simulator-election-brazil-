"""Câmara (513) e Senado (81) fictícios, com votação nominal determinística.

Todos os parlamentares são inventados: nomes são sorteados de listas genéricas e
as siglas são partidos fictícios do cenário. Nenhum parlamentar real é representado.
As regras ficam em constantes ajustáveis; a semente da partida torna o resultado
reprodutível.
"""
from __future__ import annotations

import random
from typing import Any

CHAMBER_SIZE = 513
SENATE_SIZE = 81

# sigla, nome, posição (-1 esquerda … +1 direita), cadeiras na Câmara, cadeiras no Senado, ponto de partida de adesão ao governo (0-1)
PARTIES: list[dict[str, Any]] = [
    {"id": "PTR", "name": "Partido Trabalhista Renovador", "ideology": -0.8, "seats": 68, "senate": 9, "base": 0.45},
    {"id": "PSU", "name": "Partido Social Unido", "ideology": -0.6, "seats": 41, "senate": 6, "base": 0.45},
    {"id": "PVE", "name": "Partido Verde Ecológico", "ideology": -0.4, "seats": 22, "senate": 3, "base": 0.5},
    {"id": "MDC", "name": "Movimento Democrático do Centro", "ideology": 0.0, "seats": 62, "senate": 10, "base": 0.55},
    {"id": "PSN", "name": "Partido Social Nacional", "ideology": 0.1, "seats": 54, "senate": 8, "base": 0.55},
    {"id": "PRP", "name": "Partido Republicano Progressista", "ideology": 0.3, "seats": 58, "senate": 9, "base": 0.5},
    {"id": "UDB", "name": "União Democrática Brasileira", "ideology": 0.4, "seats": 59, "senate": 9, "base": 0.5},
    {"id": "PLB", "name": "Partido Liberal Brasileiro", "ideology": 0.6, "seats": 81, "senate": 12, "base": 0.4},
    {"id": "PAG", "name": "Partido do Agro e Trabalho", "ideology": 0.5, "seats": 38, "senate": 6, "base": 0.5},
    {"id": "NVO", "name": "Novo Caminho", "ideology": 0.7, "seats": 15, "senate": 2, "base": 0.4},
    {"id": "PDE", "name": "Partido Democrata Evangélico", "ideology": 0.4, "seats": 15, "senate": 7, "base": 0.5},
]

_FIRST = ["Ana", "Carlos", "Marta", "João", "Luiza", "Paulo", "Helena", "Rui", "Sônia", "Tiago", "Bianca", "Otávio",
          "Cláudia", "Henrique", "Lídia", "Murilo", "Nádia", "Fábio", "Regina", "Vicente", "Alice", "Dante", "Elisa", "Jorge"]
_LAST = ["Albuquerque", "Barreto", "Cardoso", "Duarte", "Esteves", "Falcão", "Guedes", "Heredia", "Ivo", "Jardim",
         "Klein", "Lacerda", "Moura", "Nogueira", "Ornelas", "Paiva", "Queiroz", "Rangel", "Sampaio", "Tavares",
         "Uchoa", "Vasconcelos", "Werneck", "Ximenes", "Yamada", "Zanetti"]
STATES = ["AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR",
          "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO"]

# Quórum de aprovação por instrumento (Câmara).
THRESHOLDS = {"pec": 308, "projeto de lei complementar": 257, "projeto de lei": 257 // 1}
# Efeito do tipo de proposta sobre a disposição de votar a favor.
INSTRUMENT_PENALTY = {"pec": -0.12, "projeto de lei complementar": -0.04, "projeto de lei": 0.0}


AXES = ("economico", "social", "autoridade", "federalismo", "ambiental")
# Posição de cada categoria de medida nos eixos (-1 … +1). Ajustável; é escolha de design desta reconstrução.
CATEGORY_AXES: dict[str, dict[str, float]] = {
    "fiscal_efficiency": {"economico": 0.6},
    "business_formalization": {"economico": 0.6, "federalismo": 0.1},
    "public_investment": {"economico": -0.4, "social": -0.2},
    "tax_change": {"economico": 0.3},
    "social_policy": {"economico": -0.5, "social": -0.6},
    "security": {"autoridade": 0.7},
    "communication": {},
    "other": {},
}


def _axes(ideology: float, party: dict[str, Any], rng: random.Random) -> dict[str, float]:
    """Eixos do parlamentar: o econômico segue a posição do partido; os demais variam em torno dela."""
    jitter = lambda scale: rng.uniform(-scale, scale)
    clamp = lambda v: round(max(-1.0, min(1.0, v)), 2)
    return {"economico": clamp(ideology), "social": clamp(ideology * 0.8 + jitter(0.35)),
            "autoridade": clamp(ideology * 0.7 + jitter(0.4)), "federalismo": clamp(jitter(0.6)),
            "ambiental": clamp(-ideology * 0.6 + jitter(0.4))}


def _caucuses(axes: dict[str, float], rng: random.Random) -> list[str]:
    """Frentes parlamentares a que o parlamentar pertence, conforme seus eixos."""
    out = []
    if axes["economico"] > 0.35 and rng.random() < 0.6: out.append("agro")
    if axes["social"] > 0.3 and rng.random() < 0.5: out.append("evangelica")
    if axes["autoridade"] > 0.4 and rng.random() < 0.6: out.append("seguranca")
    if axes["economico"] < -0.35 and rng.random() < 0.6: out.append("sindical")
    if axes["ambiental"] > 0.3 and rng.random() < 0.6: out.append("ambiental")
    return out


RELATION_BREAK_PENALTY = 0.20  # observado: descumprir compromisso = −20 de relação (em escala 0-100); aqui em -1…+1
RELATION_KEEP_BONUS = 0.05      # design próprio: cumprir melhora a relação um pouco


def add_commitment(state: dict[str, Any], kind: str, party: str, region: str, week: int) -> dict[str, Any]:
    """Registra um compromisso de campanha (ex.: um ministério para o partido do governador)."""
    ledger = state.setdefault("commitments", [])
    item = {"id": f"c{len(ledger) + 1}", "kind": kind, "party": party, "region": region, "week": week, "status": "pendente"}
    ledger.append(item)
    return item


def resolve_commitment(state: dict[str, Any], commitment_id: str, fulfilled: bool) -> dict[str, Any]:
    """Cumpre ou descumpre um compromisso; descumprir derruba a relação da bancada do partido."""
    for item in state.get("commitments", []):
        if item["id"] == commitment_id:
            if item["status"] != "pendente":
                raise ValueError("Este compromisso já foi resolvido.")
            item["status"] = "cumprido" if fulfilled else "descumprido"
            delta = state.setdefault("relation_delta", {})
            delta[item["party"]] = round(delta.get(item["party"], 0.0) + (RELATION_KEEP_BONUS if fulfilled else -RELATION_BREAK_PENALTY), 3)
            return item
    raise ValueError("Compromisso não encontrado.")


def party_for_region(region: str) -> str:
    """Partido do governador de uma região (escolha determinística, fictícia)."""
    order = sorted(p["id"] for p in PARTIES)
    return order[sum(ord(c) for c in region) % len(order)]


def _bill_axes(bill: dict[str, Any]) -> dict[str, float]:
    category = str((bill.get("interpretation") or {}).get("category", "other"))
    return CATEGORY_AXES.get(category, {})


def _seed(state: dict[str, Any]) -> int:
    return int(state.get("campaign_seed", 203001))


def _build(chamber: str, seed: int) -> list[dict[str, Any]]:
    rng = random.Random(f"{seed}:{chamber}")
    key = "seats" if chamber == "camara" else "senate"
    members: list[dict[str, Any]] = []
    for party in PARTIES:
        for _ in range(party[key]):
            ideology = round(max(-1, min(1, party["ideology"] + rng.uniform(-0.25, 0.25))), 2)
            axes = _axes(ideology, party, rng)
            members.append({
                "name": f"{rng.choice(_FIRST)} {rng.choice(_LAST)}",
                "party": party["id"],
                "state": rng.choice(STATES),
                "ideology": ideology,
                "loyalty": round(max(0.0, min(1.0, party["base"] + rng.uniform(-0.18, 0.18))), 2),
                "ministry_seats": 0,
                # Modelo inspirado no esquema observado (eixos, disciplina, fisiologismo…); fórmulas próprias.
                "eixos": axes,
                "disciplina": round(rng.uniform(0.35, 0.95), 2),
                "fisiologismo": round(rng.uniform(0.0, 1.0), 2),
                "imprevisibilidade": round(rng.uniform(0.0, 0.5), 2),
                "relacao": round(max(-1.0, min(1.0, (party["base"] - 0.5) * 2 + rng.uniform(-0.3, 0.3))), 2),
                "sensibilidadeEleitoral": round(rng.uniform(0.1, 0.9), 2),
                "bancadas": _caucuses(axes, rng),
            })
    rng.shuffle(members)
    for i, member in enumerate(members, start=1):
        member["id"] = f"{'dep' if chamber == 'camara' else 'sen'}-{i:03d}"
    return members


def composition(state: dict[str, Any]) -> dict[str, Any]:
    chamber = _build("camara", _seed(state))
    senate = _build("senado", _seed(state))
    return {"camara": chamber, "senado": senate}


def _disposition(member: dict[str, Any], state: dict[str, Any], instrument: str, bill_axes: dict[str, float] | None = None) -> float:
    metrics = state.get("metrics", {})
    support = float(metrics.get("congress_support", 50)) / 100
    approval = float(metrics.get("approval", 50)) / 100
    flexibility = 1.0
    try:
        from .difficulty import get_difficulty
        flexibility = float(get_difficulty(state.get("difficulty", "normal"))["coalition_flexibility"])
    except Exception:
        pass
    ministry_bonus = 0.04 * min(3, _party_ministries(state).get(member["party"], 0))
    p = 0.12 + 0.55 * support + 0.18 * (member["loyalty"] - 0.5) + 0.08 * (approval - 0.5)
    p += ministry_bonus + INSTRUMENT_PENALTY.get(instrument, 0.0)
    # Afinidade ideológica com o conteúdo da medida (produto escalar nos eixos que a medida toca).
    weights = bill_axes or {}
    if weights:
        total = sum(abs(w) for w in weights.values())
        fit = sum(member["eixos"][axis] * w for axis, w in weights.items()) / total  # -1 … +1
        p += 0.22 * fit * (0.5 + 0.5 * (1 - member["disciplina"]))  # quem tem disciplina segue mais o partido
    # Quem tem disciplina e boa relação com o Planalto vota com o governo; fisiologismo vende voto a quem tem caixa.
    relation = max(-1.0, min(1.0, member["relacao"] + state.get("relation_delta", {}).get(member["party"], 0.0)))
    p += 0.12 * relation * member["disciplina"]
    p += 0.05 * member["fisiologismo"] * (support - 0.5)
    p = 0.5 + (p - 0.5) * flexibility
    return max(0.02, min(0.98, p))


def _party_ministries(state: dict[str, Any]) -> dict[str, int]:
    """Ministros nomeados por partido, quando o motor de nomeações os informa."""
    counts: dict[str, int] = {}
    for item in (state.get("appointments", {}) or {}).get("ministers", []) or []:
        if isinstance(item, dict) and item.get("party"):
            counts[item["party"]] = counts.get(item["party"], 0) + 1
    return counts


def roll_call(state: dict[str, Any], bill: dict[str, Any]) -> dict[str, Any]:
    """Votação nominal na Câmara e, se aprovada, no Senado. Determinística por projeto."""
    instrument = str(bill.get("instrument", "Projeto de Lei")).strip().lower()
    need_camara = THRESHOLDS.get(instrument, 257)
    need_senado = 49 if instrument == "pec" else 41
    rng = random.Random(f"{_seed(state)}:rollcall:{bill.get('id')}")
    houses = composition(state)

    def vote(members: list[dict[str, Any]], need: int) -> dict[str, Any]:
        votes = []
        for member in members:
            p = _disposition(member, state, instrument, _bill_axes(bill))
            p = max(0.02, min(0.98, p + rng.uniform(-1, 1) * member["imprevisibilidade"] * 0.2))
            r = rng.random()
            choice = "sim" if r < p else ("nao" if r < p + (1 - p) * 0.9 else "abstencao")
            votes.append({"id": member["id"], "name": member["name"], "party": member["party"], "state": member["state"], "voto": choice})
        yes = sum(v["voto"] == "sim" for v in votes)
        no = sum(v["voto"] == "nao" for v in votes)
        abst = len(votes) - yes - no
        by_party: dict[str, dict[str, int]] = {}
        for v in votes:
            row = by_party.setdefault(v["party"], {"sim": 0, "nao": 0, "abstencao": 0})
            row[v["voto"]] += 1
        return {"sim": yes, "nao": no, "abstencao": abst, "necessarios": need, "aprovado": yes >= need,
                "por_partido": by_party, "votos": votes}

    camara = vote(houses["camara"], need_camara)
    result: dict[str, Any] = {"instrument": instrument, "camara": camara}
    if instrument == "pec":
        # PEC: dois turnos na Câmara; o segundo é sorteado de novo com a mesma regra.
        camara2 = vote(houses["camara"], need_camara)
        result["camara_segundo_turno"] = {k: v for k, v in camara2.items() if k != "votos"}
        camara["aprovado"] = camara["aprovado"] and camara2["aprovado"]
    if camara["aprovado"]:
        senado = vote(houses["senado"], need_senado)
        result["senado"] = senado
        result["aprovado"] = senado["aprovado"]
    else:
        result["aprovado"] = False
    # Mantém a resposta pública enxuta: guarda os votos nominais só da Câmara.
    if "senado" in result:
        result["senado"] = {k: v for k, v in result["senado"].items() if k != "votos"}
    return result


def overview(state: dict[str, Any]) -> dict[str, Any]:
    houses = composition(state)
    support = float(state.get("metrics", {}).get("congress_support", 50))
    parties = []
    for party in PARTIES:
        members = [m for m in houses["camara"] if m["party"] == party["id"]]
        avg_loyalty = sum(m["loyalty"] for m in members) / len(members) if members else 0
        parties.append({"id": party["id"], "name": party["name"], "ideology": party["ideology"],
                        "camara": party["seats"], "senado": party["senate"], "adesao_media": round(avg_loyalty * 100)})
    calendar = state.get("legislative_calendar", {})
    return {
        "simulated": True,
        "aviso": "Parlamentares, partidos e votos são fictícios e gerados pela semente da partida.",
        "camara_total": len(houses["camara"]), "senado_total": len(houses["senado"]),
        "apoio_agregado": support,
        "partidos": parties,
        "parlamentares": houses["camara"],
        "senadores": houses["senado"],
        "em_tramitacao": calendar.get("pending_bills", []),
        "votacoes": calendar.get("vote_history", [])[:30],
        "leis_aprovadas": calendar.get("laws_enacted", 0), "leis_rejeitadas": calendar.get("laws_failed", 0),
    }
