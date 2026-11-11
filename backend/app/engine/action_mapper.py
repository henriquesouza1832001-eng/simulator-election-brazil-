"""Mapeia texto livre para ações do catálogo de competências.

Camadas, da mais forte à mais fraca:
  1. Regras locais: normalização, sinônimos e pontuação por palavras (determinístico, sem IA).
  2. Aprendizado: correções anteriores do jogador (mesma frase ou muito parecida) pesam mais.
  3. Gemini (opcional, por último): só quando o resultado local é ambíguo ou vazio. Ele escolhe UM id dentre os
     candidatos e sugere até duas perguntas de esclarecimento. Nunca cria ação, número ou efeito.
O motor valida competência do cargo, aprovação exigida e efeitos; a IA apenas ajuda a entender o que o jogador quis dizer.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any

SYNONYMS: dict[str, list[str]] = {
    "infra_asfaltar": ["asfaltar", "pavimentar", "pavimentacao", "asfalto", "recapear estrada", "rodovia federal"],
    "infra_duplicar": ["duplicar", "duplicacao", "ampliar pistas", "mais faixas"],
    "infra_conceder": ["conceder", "concessao", "pedagio", "leilao de rodovia", "privatizar rodovia"],
    "infra_vender_concessao": ["vender concessao", "transferir concessao", "relicitar", "relicitacao"],
    "infra_ferrovia": ["ferrovia", "trem", "ferrograo", "trilhos"],
    "infra_porto": ["porto", "aeroporto", "terminal portuario"],
    "defesa_alcantara": ["alcantara", "base de lancamento", "foguete", "lancamento comercial"],
    "defesa_bomba": ["bomba nuclear", "arma nuclear", "bomba atomica", "armas nucleares"],
    "defesa_nuclear_civil": ["angra", "usina nuclear", "energia nuclear", "programa nuclear"],
    "defesa_glo": ["glo", "garantia da lei e da ordem", "exercito nas ruas", "forcas armadas na seguranca"],
    "defesa_intervencao": ["intervencao federal", "intervir no estado"],
    "defesa_estado_defesa": ["estado de defesa", "estado de sitio", "sitio"],
    "defesa_guerra": ["declarar guerra", "guerra"],
    "reg_forma_governo": ["parlamentarismo", "mudar a forma de governo", "sistema de governo", "semipresidencialismo"],
    "reg_monarquia": ["monarquia", "rei", "imperio", "restaurar a monarquia"],
    "reg_abolir_federacao": ["abolir a federacao", "acabar com o voto", "fim das eleicoes"],
    "reg_reeleicao": ["reeleicao", "fim da reeleicao", "mandato unico"],
    "seg_armas_afrouxar": ["porte de arma", "posse de arma", "liberar armas", "facilitar armas", "armamento"],
    "seg_armas_restringir": ["restringir armas", "desarmamento", "controle de armas", "proibir armas"],
    "seg_desmilitarizar": ["desmilitarizar", "desmilitarizacao", "policia militar", "pm unificada", "policia unica"],
    "bc_autonomia_constitucional": ["autonomia do banco central na constituicao", "constitucionalizar banco central"],
    "bc_revogar_autonomia": ["acabar com a autonomia do banco central", "revogar autonomia", "banco central sob controle do governo", "controlar o banco central"],
    "bc_restaurar_autonomia": ["restaurar autonomia", "banco central independente", "banco central autonomo"],
    "bc_meta_inflacao": ["meta de inflacao", "meta inflacionaria"],
    "bc_pressao_juros": ["criticar juros", "baixar os juros", "pressionar o banco central", "reduzir selic"],
    "bc_moeda_comum": ["moeda comum", "moeda sul-americana", "moeda da america do sul", "sur", "moeda unica"],
    "bc_diretor": ["presidente do banco central", "diretor do banco central", "indicar banco central"],
    "empresa_privatizar": ["privatizar", "privatizacao", "vender estatal", "vender a petrobras", "vender os correios", "vender empresa"],
    "empresa_estatizar": ["estatizar", "estatizacao", "comprar empresa", "comprar participacao", "nacionalizar"],
    "empresa_criar": ["criar empresa publica", "nova estatal"],
    "empresa_monopolio_petroleo": ["monopolio do petroleo", "petroleo", "pre-sal"],
    "empresa_itaipu": ["itaipu", "tarifa de itaipu"],
    "ext_brics_entrar": ["entrar no brics", "aprofundar brics"],
    "ext_brics_sair": ["sair do brics", "deixar o brics"],
    "ext_otan": ["otan", "nato", "aderir a otan"],
    "ext_opep": ["opep", "opep+", "cartel do petroleo", "entrar na opep"],
    "ext_opep_sair": ["sair da opep", "deixar a opep"],
    "ext_mercosul": ["mercosul", "tarifa externa comum"],
    "ext_acordo_comercial": ["acordo comercial", "acordo com a china", "acordo com a uniao europeia", "livre comercio"],
    "eco_reforma_tributaria": ["reforma tributaria", "reformar impostos", "simplificar impostos"],
    "eco_teto": ["teto de gastos", "regra fiscal", "arcabouco fiscal"],
    "eco_previdencia": ["previdencia", "aposentadoria", "reforma da previdencia"],
    "eco_bolsa": ["bolsa familia", "transferencia de renda", "renda minima", "auxilio"],
    "eco_salario_minimo": ["salario minimo", "reajuste do minimo"],
    "eco_desoneracao": ["desoneracao", "desonerar", "reduzir impostos", "isencao"],
    "eco_confisco": ["congelar precos", "tabelamento", "controle de precos", "confisco", "congelar poupanca"],
    "eco_mp": ["medida provisoria"],
    "p_recapear": ["recapear", "tapar buraco", "asfaltar rua", "pavimentar rua", "vias da cidade"],
    "p_onibus": ["onibus", "transporte coletivo", "linhas de onibus", "tarifa de onibus"],
    "p_ubs": ["posto de saude", "ubs", "unidade de saude", "saude da familia"],
    "p_creches": ["creche", "educacao infantil"],
    "p_esgoto": ["esgoto", "saneamento", "agua encanada"],
    "p_guarda": ["guarda municipal", "iluminacao publica", "seguranca do bairro"],
    "p_iptu": ["iptu", "imposto predial"],
    "g_rodovia": ["rodovia estadual", "duplicar estrada", "rodoanel"],
    "g_policia": ["policia militar", "policia civil", "reforcar a policia", "viaturas"],
    "g_icms": ["icms", "imposto estadual"],
    "v_cpi": ["cpi", "comissao parlamentar"],
    "de_cpi": ["cpi", "comissao parlamentar"],
    "df_cpi": ["cpi", "comissao parlamentar"],
}
STOP = {"de", "da", "do", "das", "dos", "a", "o", "as", "os", "e", "em", "no", "na", "nos", "nas", "para", "por", "com", "um", "uma", "que", "ao", "se", "quero", "vou", "fazer", "pode", "ser"}
AMBIGUITY_MARGIN = 0.25
MIN_SCORE = 1.5


def plain(text: str) -> str:
    text = "".join(c for c in unicodedata.normalize("NFKD", text.lower()) if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9+ ]+", " ", text)


def tokens(text: str) -> list[str]:
    out = []
    for w in plain(text).split():
        if w in STOP or len(w) < 3:
            continue
        for suffix in ("coes", "oes", "ar", "er", "ir", "s"):
            if w.endswith(suffix) and len(w) - len(suffix) >= 4:
                w = w[: -len(suffix)]
                break
        out.append(w)
    return out


def _score(text_plain: str, text_tokens: set[str], candidate: dict[str, Any]) -> float:
    score = 0.0
    for phrase in SYNONYMS.get(candidate["id"], []):
        p = plain(phrase).strip()
        if p and p in text_plain:
            score += 3.0 + 0.5 * len(p.split())
    own = set(tokens(candidate["title"])) | set(tokens(candidate.get("summary", ""))[:12])
    score += 0.8 * len(text_tokens & own)
    return score


def _option_guess(text_plain: str, options: list[str]) -> str | None:
    for opt in options:
        key = plain(opt).strip()
        head = key.split("(")[0].strip()
        if head and head in text_plain:
            return opt
        compact = re.sub(r"[^a-z0-9]", "", key.split("(")[0])
        if compact and compact in re.sub(r"[^a-z0-9]", "", text_plain):
            return opt
    return None


def rank(text: str, candidates: list[dict[str, Any]], corrections: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    tp = plain(text)
    tk = set(tokens(text))
    learned = {c.get("action_id") for c in (corrections or []) if c.get("action_id")}
    rows = []
    for cand in candidates:
        s = _score(tp, tk, cand)
        if cand["id"] in learned:
            s += 2.0   # o jogador já confirmou esse mapeamento antes
        if s >= MIN_SCORE:
            rows.append({"id": cand["id"], "title": cand["title"], "score": round(s, 2), "available": cand.get("available", True), "reason": cand.get("reason"),
                         "option_guess": _option_guess(tp, cand.get("options", [])), "options": cand.get("options", []), "approval": cand.get("approval"),
                         "basis": cand.get("basis"), "legal": cand.get("legal")})
    rows.sort(key=lambda r: -r["score"])
    return rows[:5]


def questions_for(text: str, matches: list[dict[str, Any]]) -> list[str]:
    """Perguntas de esclarecimento determinísticas, a partir do que falta ou do empate."""
    out: list[str] = []
    if not matches:
        return ["Não identifiquei uma ação do seu cargo nessa frase. Qual área você quer mexer: economia, segurança, infraestrutura, relações exteriores ou instituições?"]
    top = matches[0]
    if top["options"] and not top["option_guess"]:
        out.append(f"Em qual destes: {', '.join(top['options'])}?")
    if len(matches) > 1 and matches[0]["score"] - matches[1]["score"] < AMBIGUITY_MARGIN * matches[0]["score"]:
        out.append(f"Você quer “{matches[0]['title']}” ou “{matches[1]['title']}”?")
    if not top["available"] and top.get("reason"):
        out.append(f"{top['title']} não está disponível agora: {top['reason']} Prefere outra ação parecida?")
    return out[:2]


def needs_ai(matches: list[dict[str, Any]]) -> bool:
    if not matches:
        return True
    return len(matches) > 1 and matches[0]["score"] - matches[1]["score"] < AMBIGUITY_MARGIN * matches[0]["score"]
