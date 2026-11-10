"""Trajetória partidária: eleitor engajado → militante → filiado → quadro → pré-candidato → candidato.

Camada anterior à carreira eleitoral. Ao lançar a pré-candidatura, entrega ao motor de carreira existente
(`career.start_career`) levando a reputação construída. Os prazos e números são **simplificações de jogo**:
o prazo legal real de filiação/domicílio por ciclo está marcado como pendente em `election_rules`.
Sorteios são determinísticos (hash da semente, do dia e da chave).
"""
from __future__ import annotations

import hashlib
from datetime import date, timedelta
from typing import Any

from .career import IDEOLOGY_SPECTRUM, SPECTRUM_ORDER, start_career, validate_party_name

STAGES = ["eleitor", "militante", "filiado", "quadro", "pre_candidato"]
STAGE_LABEL = {"eleitor": "Eleitor engajado", "militante": "Militante", "filiado": "Filiado(a)", "quadro": "Quadro do partido",
               "pre_candidato": "Pré-candidato(a)", "candidato": "Candidato(a)"}
CAUSES = {"moradia": "Moradia", "saude": "Saúde", "educacao": "Educação", "transporte": "Transporte", "seguranca": "Segurança",
          "ambiente": "Meio ambiente", "cultura": "Cultura", "esporte": "Esporte", "trabalho": "Trabalho e renda", "mulheres": "Direitos das mulheres",
          "juventude": "Juventude", "idosos": "Pessoas idosas"}

ENERGY_MAX = 100
ENERGY_REGEN_PER_DAY = 6
LOW_ENERGY = 35
LOW_ENERGY_FACTOR = 0.6
AFFILIATION_ANALYSIS_DAYS = 14
REFUSAL_COOLDOWN_DAYS = 60
MIN_DAYS_AS_MEMBER_TO_LAUNCH = 180   # simplificação de jogo; prazo legal real: pendente (ver election_rules)
INACTIVITY_DAYS = 45

# id: rótulo, texto, energia, estágios permitidos, efeitos {reputation, network, militancy, standing}, recarga em dias, requer partido
ACTIONS: dict[str, dict[str, Any]] = {
    "acompanhar": {"label": "Acompanhar a política local", "text": "Ler, ouvir e entender quem decide o quê na sua cidade.", "energy": 5,
                   "stages": ["eleitor", "militante"], "effects": {"militancy": 1.0, "reputation": 0.1}, "cooldown": 0},
    "reuniao_bairro": {"label": "Participar de reunião de bairro", "text": "Escutar moradores e se apresentar.", "energy": 10,
                       "stages": ["eleitor", "militante", "filiado", "quadro"], "effects": {"network": 1.5, "militancy": 2.0, "reputation": 0.4}, "cooldown": 0},
    "ato_publico": {"label": "Ir a um ato público", "text": "Marcar presença e fazer contatos.", "energy": 12,
                    "stages": ["eleitor", "militante", "filiado", "quadro"], "effects": {"network": 2.0, "militancy": 2.5}, "cooldown": 0},
    "panfletagem": {"label": "Fazer panfletagem pela sua causa", "text": "Distribuir material e conversar com quem passa.", "energy": 14,
                    "stages": ["militante", "filiado", "quadro"], "effects": {"militancy": 3.5, "reputation": 0.8, "network": 1.0}, "cooldown": 0},
    "abaixo_assinado": {"label": "Organizar um abaixo-assinado", "text": "Reunir apoio para uma demanda concreta do bairro.", "energy": 16,
                        "stages": ["militante", "filiado", "quadro"], "effects": {"reputation": 2.0, "network": 2.5, "militancy": 2.0}, "cooldown": 7},
    "debate_local": {"label": "Participar de um debate local", "text": "Defender suas ideias em público.", "energy": 15,
                     "stages": ["militante", "filiado", "quadro"], "effects": {"reputation": 2.5, "militancy": 1.5, "network": 1.0}, "cooldown": 7, "risk": 0.15},
    "cabo_eleitoral": {"label": "Ajudar a campanha de outro candidato", "text": "Trabalho voluntário que gera gratidão.", "energy": 18,
                       "stages": ["militante", "filiado", "quadro"], "effects": {"network": 3.0, "standing": 1.5, "militancy": 2.0}, "cooldown": 5},
    "voluntariado": {"label": "Fazer trabalho voluntário na comunidade", "text": "Ações solidárias que constroem reputação.", "energy": 12,
                     "stages": ["eleitor", "militante", "filiado", "quadro", "pre_candidato"], "effects": {"reputation": 1.8, "network": 1.2}, "cooldown": 0},
    "estudar": {"label": "Estudar legislação e políticas públicas", "text": "Ganhar base técnica para disputar o debate.", "energy": 8,
                "stages": ["eleitor", "militante", "filiado", "quadro", "pre_candidato"], "effects": {"reputation": 1.0, "militancy": 0.5}, "cooldown": 0},
    "reuniao_partido": {"label": "Participar de reunião do diretório", "text": "Mostrar serviço dentro do partido.", "energy": 10,
                        "stages": ["filiado", "quadro", "pre_candidato"], "effects": {"standing": 2.5, "network": 1.0}, "cooldown": 0, "needs_party": True},
    "tarefa_partido": {"label": "Assumir uma tarefa do partido", "text": "Mobilização, cadastro ou formação política.", "energy": 15,
                       "stages": ["filiado", "quadro"], "effects": {"standing": 3.5, "network": 1.5}, "cooldown": 3, "needs_party": True},
    "buscar_padrinho": {"label": "Buscar um padrinho político", "text": "Conquistar o apoio de uma liderança do partido.", "energy": 12,
                        "stages": ["filiado", "quadro", "pre_candidato"], "effects": {"standing": 4.0, "network": 2.0}, "cooldown": 14, "needs_party": True, "risk": 0.25},
    "redes_sociais": {"label": "Produzir conteúdo nas redes", "text": "Ganhar alcance com a sua causa.", "energy": 8,
                      "stages": ["eleitor", "militante", "filiado", "quadro", "pre_candidato"], "effects": {"reputation": 1.2, "network": 1.0}, "cooldown": 1, "risk": 0.2},
    "descansar": {"label": "Descansar", "text": "Recupera 25 de energia.", "energy": -25, "stages": ["eleitor", "militante", "filiado", "quadro", "pre_candidato"],
                  "effects": {}, "cooldown": 0},
}


def _roll(state: dict[str, Any], day: date, key: str) -> float:
    digest = hashlib.sha256(f"{state.get('campaign_seed', 203001)}|party|{day.isoformat()}|{key}".encode()).digest()
    return int.from_bytes(digest[:8], "big") / 2 ** 64


def _clamp(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, v))


def init_state(state: dict[str, Any], *, name: str, state_code: str, municipality_id: str, municipality: str, spectrum: str, cause: str) -> dict[str, Any]:
    if cause not in CAUSES:
        raise ValueError("Escolha uma causa para começar.")
    state["mode"] = "party_path"
    state.setdefault("communications", {}).setdefault("inauguration", {})["required"] = False
    state["party_path"] = {
        "active": True, "stage": "eleitor", "name": name, "state_code": state_code, "municipality_id": municipality_id, "municipality": municipality,
        "spectrum": spectrum, "cause": cause, "energy": ENERGY_MAX, "reputation": 35.0, "network": 8.0, "militancy": 0.0, "standing": 0.0,
        "party": None, "ideology": None, "party_since": None, "post": None, "affiliation": {"status": None}, "last_action": None,
        "counts": {}, "last_by_action": {}, "log": [], "started": state["date"],
    }
    return state["party_path"]


def _pp(state: dict[str, Any]) -> dict[str, Any]:
    pp = state.get("party_path")
    if not pp or not pp.get("active"):
        raise ValueError("Não há trajetória partidária em andamento nesta partida.")
    return pp


def story_level(state: dict[str, Any]) -> str | None:
    pp = state.get("party_path")
    if not pp or not pp.get("active"):
        return None
    return "militante" if pp["stage"] in ("eleitor", "militante") else "partido"


def _days_as_member(pp: dict[str, Any], today: date) -> int:
    return (today - date.fromisoformat(pp["party_since"])).days if pp.get("party_since") else 0


def _log(pp: dict[str, Any], today: date, text: str) -> None:
    pp["log"].insert(0, {"date": today.isoformat(), "text": text})
    del pp["log"][40:]


def _affinity(pp: dict[str, Any], ideology: str) -> float:
    gap = abs(SPECTRUM_ORDER.index(pp["spectrum"]) - SPECTRUM_ORDER.index(IDEOLOGY_SPECTRUM.get(ideology, "centro")))
    return 1 - gap / 4  # 1 = mesma linha, 0 = extremos opostos


def _blocked(state: dict[str, Any], pp: dict[str, Any], key: str) -> str | None:
    a = ACTIONS[key]
    today = date.fromisoformat(state["date"])
    if pp["stage"] not in a["stages"]:
        return "Indisponível neste estágio."
    if a.get("needs_party") and not pp.get("party"):
        return "Exige estar filiado a um partido."
    if a["energy"] > 0 and pp["energy"] < a["energy"]:
        return "Energia insuficiente. Descanse."
    last = pp["last_by_action"].get(key)
    if a["cooldown"] and last and (today - date.fromisoformat(last)).days < a["cooldown"]:
        return f"Disponível de novo em {a['cooldown'] - (today - date.fromisoformat(last)).days} dia(s)."
    return None


def next_stage_requirements(state: dict[str, Any]) -> dict[str, Any]:
    pp = _pp(state)
    today = date.fromisoformat(state["date"])
    stage = pp["stage"]
    if stage == "eleitor":
        return {"goal": "Tornar-se militante", "items": [{"label": "Militância", "value": round(pp["militancy"], 1), "need": 15}], "ready": pp["militancy"] >= 15,
                "how": "Participe de reuniões e atos até acumular militância. A promoção é automática."}
    if stage == "militante":
        return {"goal": "Filiar-se a um partido", "items": [{"label": "Militância", "value": round(pp["militancy"], 1), "need": 30}, {"label": "Contatos", "value": round(pp["network"], 1), "need": 10}],
                "ready": pp["militancy"] >= 30 and pp["network"] >= 10 and pp["affiliation"].get("status") not in ("analise",),
                "how": "Peça a filiação. O partido analisa por 14 dias e pode recusar."}
    if stage == "filiado":
        return {"goal": "Assumir um cargo no diretório", "items": [{"label": "Prestígio no partido", "value": round(pp["standing"], 1), "need": 40},
                                                                    {"label": "Dias de casa", "value": _days_as_member(pp, today), "need": 90}],
                "ready": pp["standing"] >= 40 and _days_as_member(pp, today) >= 90, "how": "Faça tarefas e participe do diretório; depois dispute um cargo."}
    if stage == "quadro":
        return {"goal": "Lançar a pré-candidatura", "items": [{"label": "Prestígio no partido", "value": round(pp["standing"], 1), "need": 55},
                                                              {"label": "Contatos", "value": round(pp["network"], 1), "need": 35}, {"label": "Reputação", "value": round(pp["reputation"], 1), "need": 45},
                                                              {"label": "Dias de casa", "value": _days_as_member(pp, today), "need": MIN_DAYS_AS_MEMBER_TO_LAUNCH}],
                "ready": pp["standing"] >= 55 and pp["network"] >= 35 and pp["reputation"] >= 45 and _days_as_member(pp, today) >= MIN_DAYS_AS_MEMBER_TO_LAUNCH,
                "how": "Cumpra as metas e lance a pré-candidatura a vereador na sua cidade."}
    return {"goal": "Disputar a eleição", "items": [], "ready": False, "how": "Você já é pré-candidato."}


def overview(state: dict[str, Any]) -> dict[str, Any]:
    pp = state.get("party_path")
    if not pp:
        return {"active": False}
    today = date.fromisoformat(state["date"])
    actions = []
    if pp.get("active"):
        for key, a in ACTIONS.items():
            reason = _blocked(state, pp, key)
            if pp["stage"] in a["stages"]:
                actions.append({"key": key, "label": a["label"], "text": a["text"], "energy": a["energy"], "available": reason is None, "reason": reason})
    election = date(2028, 10, 1)
    return {"active": bool(pp.get("active")), "simulated": True, "stage": pp["stage"], "stage_label": STAGE_LABEL.get(pp["stage"], pp["stage"]), "date": state["date"],
            "name": pp["name"], "municipality": pp["municipality"], "state_code": pp["state_code"], "cause": CAUSES.get(pp["cause"], pp["cause"]),
            "meters": {"energy": round(pp["energy"]), "energy_max": ENERGY_MAX, "reputation": round(pp["reputation"], 1), "network": round(pp["network"], 1),
                       "militancy": round(pp["militancy"], 1), "standing": round(pp["standing"], 1)},
            "low_energy": pp["energy"] < LOW_ENERGY, "party": pp["party"], "ideology": pp.get("ideology"), "post": pp["post"], "days_as_member": _days_as_member(pp, today),
            "affiliation": pp["affiliation"], "next": next_stage_requirements(state) if pp.get("active") else None, "actions": actions, "log": pp["log"][:15],
            "days_to_municipal_election": (election - today).days,
            "note": "Prazos de filiação e domicílio são simplificações do jogo; o prazo legal real está pendente de conferência."}


def perform(state: dict[str, Any], key: str) -> dict[str, Any]:
    pp = _pp(state)
    if key not in ACTIONS:
        raise ValueError("Ação desconhecida.")
    reason = _blocked(state, pp, key)
    if reason:
        raise ValueError(reason)
    a = ACTIONS[key]
    today = date.fromisoformat(state["date"])
    repeat_count = pp["counts"].get(key, 0)
    decay = max(0.4, 0.93 ** repeat_count)  # retorno decrescente por repetição
    factor = decay * (LOW_ENERGY_FACTOR if pp["energy"] < LOW_ENERGY else 1.0)
    applied: dict[str, float] = {}
    gaffe = False
    if a.get("risk") and _roll(state, today, f"risk:{key}:{repeat_count}") < a["risk"]:
        gaffe = True
        factor *= -0.5  # a ação dá errado: parte do ganho vira perda
    for metric, base in a["effects"].items():
        delta = round(base * factor, 2)
        pp[metric] = round(_clamp(pp[metric] + delta), 2)
        applied[metric] = delta
    pp["energy"] = _clamp(pp["energy"] - a["energy"], 0, ENERGY_MAX)
    pp["counts"][key] = repeat_count + 1
    pp["last_by_action"][key] = today.isoformat()
    pp["last_action"] = today.isoformat()
    _log(pp, today, f"{a['label']}{' — deu errado' if gaffe else ''}")
    promoted = _auto_promote(state, pp, today)
    return {"result": {"action": key, "label": a["label"], "applied": applied, "gaffe": gaffe, "repeat_factor": round(decay, 2), "low_energy": pp["energy"] < LOW_ENERGY},
            "promoted": promoted, "overview": overview(state)}


def _auto_promote(state: dict[str, Any], pp: dict[str, Any], today: date) -> str | None:
    if pp["stage"] == "eleitor" and pp["militancy"] >= 15:
        pp["stage"] = "militante"
        _log(pp, today, "Você passou a atuar como militante.")
        return "militante"
    return None


def request_affiliation(state: dict[str, Any], party: str, ideology: str) -> dict[str, Any]:
    pp = _pp(state)
    today = date.fromisoformat(state["date"])
    if pp["stage"] != "militante":
        raise ValueError("A filiação é pedida por quem já atua como militante.")
    if ideology not in IDEOLOGY_SPECTRUM:
        raise ValueError("Escolha uma linha partidária disponível.")
    party = validate_party_name(party)
    aff = pp["affiliation"]
    if aff.get("status") == "analise":
        raise ValueError("Já existe um pedido de filiação em análise.")
    if aff.get("refused_until") and today < date.fromisoformat(aff["refused_until"]):
        raise ValueError(f"O último pedido foi recusado. Novo pedido a partir de {date.fromisoformat(aff['refused_until']).strftime('%d/%m/%Y')}.")
    if pp["militancy"] < 30 or pp["network"] < 10:
        raise ValueError("Acumule militância (30) e contatos (10) antes de pedir a filiação.")
    pp["affiliation"] = {"status": "analise", "party": party, "ideology": ideology, "request_date": today.isoformat(),
                         "decision_date": (today + timedelta(days=AFFILIATION_ANALYSIS_DAYS)).isoformat()}
    _log(pp, today, f"Pedido de filiação enviado a {party}. Análise em {AFFILIATION_ANALYSIS_DAYS} dias.")
    return overview(state)


def _decide_affiliation(state: dict[str, Any], pp: dict[str, Any]) -> None:
    aff = pp["affiliation"]
    decision = date.fromisoformat(aff["decision_date"])
    affinity = _affinity(pp, aff["ideology"])
    chance = _clamp(0.25 + 0.45 * affinity + 0.004 * pp["militancy"] + 0.003 * pp["network"] + 0.002 * pp["reputation"], 0.1, 0.95)
    if _roll(state, decision, f"filiacao:{aff['party']}") < chance:
        pp.update(party=aff["party"], ideology=aff["ideology"], party_since=decision.isoformat(), stage="filiado", standing=max(pp["standing"], 5.0))
        pp["affiliation"] = {"status": "filiado", "party": aff["party"], "decision_date": decision.isoformat()}
        _log(pp, decision, f"Filiação aprovada em {aff['party']}.")
    else:
        pp["affiliation"] = {"status": "recusado", "party": aff["party"], "decision_date": decision.isoformat(),
                             "refused_until": (decision + timedelta(days=REFUSAL_COOLDOWN_DAYS)).isoformat()}
        _log(pp, decision, f"Pedido de filiação recusado por {aff['party']}. Prestígio baixo ou pouca afinidade.")


def run_for_party_post(state: dict[str, Any]) -> dict[str, Any]:
    pp = _pp(state)
    today = date.fromisoformat(state["date"])
    if pp["stage"] != "filiado":
        raise ValueError("Só filiados disputam cargo no diretório.")
    req = next_stage_requirements(state)
    if not req["ready"]:
        raise ValueError("Cumpra as metas de prestígio e de tempo de casa antes de disputar um cargo.")
    chance = _clamp(0.2 + 0.006 * pp["standing"] + 0.004 * pp["network"] + 0.003 * pp["reputation"], 0.1, 0.9)
    won = _roll(state, today, "diretorio") < chance
    if won:
        pp["stage"] = "quadro"
        pp["post"] = "Secretário(a) do diretório municipal"
        pp["standing"] = round(_clamp(pp["standing"] + 6), 2)
        _log(pp, today, f"Eleito(a) {pp['post']}.")
    else:
        pp["standing"] = round(_clamp(pp["standing"] - 4), 2)
        _log(pp, today, "Derrota na eleição do diretório. Prestígio abalado, mas você segue filiado(a).")
    return {"won": won, "chance": round(chance, 2), "overview": overview(state)}


def launch_candidacy(state: dict[str, Any], office: str = "vereador") -> dict[str, Any]:
    """Entrega ao motor de carreira: abre a pré-candidatura a vereador no município do jogador."""
    pp = _pp(state)
    today = date.fromisoformat(state["date"])
    if pp["stage"] != "quadro":
        raise ValueError("A pré-candidatura é lançada por quadros do partido.")
    if office != "vereador":
        raise ValueError("Nesta versão, a trajetória leva à candidatura a vereador na sua cidade.")
    req = next_stage_requirements(state)
    if not req["ready"]:
        raise ValueError("Cumpra as metas de prestígio, contatos, reputação e tempo de casa antes de lançar a pré-candidatura.")
    character = dict(state.get("player_character") or {})
    character.setdefault("name", pp["name"])
    character["political_spectrum"] = pp["spectrum"]
    previous = state.get("career")
    state["career"] = {"reputation": round(_clamp(pp["reputation"] * 0.6 + pp["standing"] * 0.25 + pp["network"] * 0.15 + 8), 1)}
    try:
        start_career(state, office, pp["state_code"], pp["municipality"], pp["party"], pp["ideology"], pp["name"], character, pp["municipality_id"])
    except ValueError:
        if previous is None:
            state.pop("career", None)
        else:
            state["career"] = previous
        raise
    pp["stage"] = "candidato"
    pp["active"] = False
    pp["launched"] = today.isoformat()
    _log(pp, today, "Pré-candidatura a vereador lançada. A campanha segue no módulo de carreira.")
    return {"launched": True, "career_phase": state["career"].get("phase")}


def tick(state: dict[str, Any], before: date, after: date) -> list[str]:
    pp = state.get("party_path")
    if not pp or not pp.get("active"):
        return []
    messages: list[str] = []
    days = (after - before).days
    pp["energy"] = _clamp(pp["energy"] + ENERGY_REGEN_PER_DAY * days, 0, ENERGY_MAX)
    aff = pp["affiliation"]
    if aff.get("status") == "analise" and date.fromisoformat(aff["decision_date"]) <= after:
        _decide_affiliation(state, pp)
        messages.append("Filiação aprovada." if pp["affiliation"]["status"] == "filiado" else "Pedido de filiação recusado.")
    last = pp.get("last_action")
    if last:
        idle = (after - date.fromisoformat(last)).days
        if idle > INACTIVITY_DAYS:
            lost = round(0.04 * min(days, idle - INACTIVITY_DAYS), 2)
            pp["reputation"] = round(_clamp(pp["reputation"] - lost), 2)
            if pp.get("party"):
                pp["standing"] = round(_clamp(pp["standing"] - lost * 1.5), 2)
            if lost:
                messages.append("Inatividade corrói reputação e prestígio.")
    return messages
