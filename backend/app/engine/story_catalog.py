"""Catálogo de acontecimentos do mandato (conteúdo original; personagens e entidades fictícios).

Cada acontecimento tem condição de disparo, tipo (decisão, oportunidade ou informativo) e opções com
efeitos explícitos. Os números são abstrações de jogo, ajustáveis aqui. Nenhuma pessoa real aparece.
"""
from __future__ import annotations

from typing import Any, Callable

Cond = Callable[[dict[str, Any]], bool]


def _m(s: dict[str, Any], key: str, default: float = 50.0) -> float:
    return float(s.get("metrics", {}).get(key, default))


def _always(_s: dict[str, Any]) -> bool:
    return True


# effects: chaves de metrics (delta) ou "inst:<chave>" para instituições ou "rel:<SIGLA>" para relação com um partido.
EVENTS: dict[str, dict[str, Any]] = {
    "greve_transporte": {
        "kind": "decisao", "tags": ["trabalho", "economia"], "weight": 1.0, "cooldown": 120, "when": lambda s: _m(s, "inflation", 4) > 3.5,
        "title": "Paralisação do transporte de cargas",
        "text": "Entidades de caminhoneiros fictícias param rodovias de três estados exigindo reajuste do frete mínimo. Mercados e supermercados já relatam falta de itens.",
        "fallback": "ignorar",
        "choices": [
            {"id": "negociar", "label": "Abrir mesa de negociação", "hint": "Custa R$ 2 bi em subsídio ao diesel.", "tone": "dialogo", "cost_bi": 2.0,
             "effects": {"approval": 1.0, "inflation": 0.1, "governability": 1}, "outcome": "A mesa encerra a paralisação em dois dias, com custo fiscal."},
            {"id": "forcar", "label": "Acionar a Força Nacional", "hint": "Desbloqueia rápido, com desgaste político.", "tone": "dura",
             "effects": {"approval": -1.5, "governability": -2, "inst:civilian_legitimacy": -2}, "outcome": "As rodovias são liberadas, mas o governo é acusado de truculência."},
            {"id": "ignorar", "label": "Esperar a pressão diminuir", "hint": "Sem custo agora; a falta de itens pesa.", "tone": "passiva",
             "effects": {"approval": -2.0, "inflation": 0.3, "gdp_growth": -0.1}, "outcome": "Os bloqueios duram uma semana e a inflação sente."}]},
    "denuncia_assessor": {
        "kind": "decisao", "tags": ["integridade"], "weight": 0.9, "cooldown": 150, "when": lambda s: _m(s, "integrity", 70) < 85,
        "title": "Denúncia contra um assessor do gabinete",
        "text": "Uma reportagem fictícia aponta que um assessor da Presidência teria favorecido uma empresa em contratos de comunicação. O Planalto precisa responder hoje.",
        "fallback": "defender",
        "choices": [
            {"id": "afastar", "label": "Afastar e abrir apuração", "hint": "Custa pouco e protege a imagem.", "tone": "etica",
             "effects": {"integrity": 2, "approval": 0.5, "congress_support": -1}, "outcome": "O assessor sai, a apuração começa e o caso esfria."},
            {"id": "defender", "label": "Defender o assessor", "hint": "Mantém a equipe unida, mas arrisca a imagem.", "tone": "passiva",
             "effects": {"integrity": -3, "approval": -1.5}, "follow": [("cpi_pedido", 20)], "outcome": "A oposição ganha munição e promete pedir uma comissão de inquérito."},
            {"id": "ignorar_nota", "label": "Responder só com nota oficial", "hint": "Meio-termo.", "tone": "neutra",
             "effects": {"integrity": -1, "approval": -0.5}, "outcome": "A nota não convence todo mundo, mas o assunto sai da pauta."}]},
    "cpi_pedido": {
        "kind": "decisao", "tags": ["congresso", "integridade"], "weight": 0.0, "cooldown": 200, "when": _always,
        "title": "Oposição reúne assinaturas para uma CPI",
        "text": "Parlamentares de oposição fictícios coletam assinaturas para instalar uma comissão de inquérito sobre os contratos do gabinete.",
        "fallback": "resistir",
        "choices": [
            {"id": "colaborar", "label": "Colaborar e entregar documentos", "tone": "etica", "hint": "Reduz o desgaste a longo prazo.",
             "effects": {"integrity": 1.5, "congress_support": -1}, "outcome": "A comissão se instala sem surpresas e perde fôlego."},
            {"id": "resistir", "label": "Mobilizar a base para barrar", "tone": "dura", "hint": "Gasta capital político.",
             "effects": {"congress_support": -3, "governability": -2}, "follow": [("cpi_instalada", 25)], "outcome": "A base consegue adiar, mas o desgaste cresce."}]},
    "cpi_instalada": {
        "kind": "info", "tags": ["congresso"], "weight": 0.0, "cooldown": 300, "when": _always,
        "title": "CPI instalada no Congresso",
        "text": "A comissão foi instalada e convoca depoimentos nas próximas semanas. O noticiário acompanha cada audiência.",
        "choices": [{"id": "ok", "label": "Acompanhar", "effects": {"approval": -1.5, "integrity": -1}, "outcome": "As audiências desgastam o governo."}]},
    "seca_interior": {
        "kind": "decisao", "tags": ["clima", "economia"], "weight": 0.8, "cooldown": 240, "when": _always,
        "title": "Seca prolonga-se no interior",
        "text": "Reservatórios fictícios chegam a níveis críticos em uma região agrícola. Prefeitos pedem socorro federal e a safra está ameaçada.",
        "fallback": "esperar",
        "choices": [
            {"id": "socorro", "label": "Plano emergencial de água e crédito", "hint": "R$ 3 bi em socorro.", "tone": "dialogo", "cost_bi": 3.0,
             "effects": {"approval": 1.5, "gdp_growth": 0.05, "governability": 1}, "outcome": "O socorro chega e a safra é parcialmente preservada."},
            {"id": "esperar", "label": "Aguardar o fim do período seco", "hint": "Sem custo agora.", "tone": "passiva",
             "effects": {"approval": -2.0, "gdp_growth": -0.15, "inflation": 0.2}, "outcome": "A quebra da safra pressiona alimentos e a popularidade."}]},
    "enchente_sul": {
        "kind": "decisao", "tags": ["clima", "emergencia"], "weight": 0.7, "cooldown": 300, "when": _always,
        "title": "Enchentes atingem cidades do litoral",
        "text": "Chuvas intensas desabrigam famílias em cidades fictícias do litoral. Governadores pedem ajuda federal imediata.",
        "fallback": "visitar",
        "choices": [
            {"id": "visitar", "label": "Visitar a área e liberar verba", "hint": "R$ 1,5 bi e agenda cheia.", "tone": "dialogo", "cost_bi": 1.5,
             "effects": {"approval": 2.0, "governability": 1}, "outcome": "A presença e a verba rápida melhoram a imagem."},
            {"id": "enviar_ministro", "label": "Enviar o ministro responsável", "hint": "Custa menos.", "tone": "neutra", "cost_bi": 0.8,
             "effects": {"approval": 0.5}, "outcome": "A resposta é considerada correta, mas protocolar."}]},
    "oferta_cargo_estatal": {
        "kind": "oportunidade", "tags": ["congresso", "integridade"], "weight": 0.9, "cooldown": 120, "when": lambda s: _m(s, "congress_support", 50) < 65,
        "title": "Aliados pedem uma diretoria em estatal",
        "text": "Líderes de um partido do centro fictício oferecem votos garantidos nas próximas semanas em troca de uma diretoria em uma estatal.",
        "fallback": "recusar",
        "choices": [
            {"id": "aceitar", "label": "Aceitar o acordo", "hint": "Ganha base; perde integridade.", "tone": "fisiologica",
             "effects": {"congress_support": 6, "governability": 3, "integrity": -4}, "outcome": "Os votos aparecem, e a imprensa registra o toma-lá-dá-cá."},
            {"id": "recusar", "label": "Recusar e manter critérios técnicos", "hint": "Preserva a imagem.", "tone": "etica",
             "effects": {"congress_support": -2, "integrity": 1.5}, "outcome": "A base reclama, mas a gestão ganha credibilidade."}]},
    "paralisacao_apps": {
        "kind": "decisao", "tags": ["trabalho"], "weight": 0.8, "cooldown": 180, "when": _always,
        "title": "Motoristas de aplicativo paralisam as ruas",
        "text": "Motoristas fictícios de aplicativos fazem um protesto nacional por valor mínimo por corrida e proteção previdenciária.",
        "fallback": "ignorar",
        "choices": [
            {"id": "regular", "label": "Enviar projeto de regulação", "tone": "dialogo", "hint": "Abre uma pauta no Congresso.",
             "effects": {"approval": 1.0, "congress_support": -1}, "outcome": "O projeto acalma parte da categoria e divide o Congresso."},
            {"id": "ignorar", "label": "Não intervir", "tone": "passiva", "hint": "O protesto perde força sozinho.",
             "effects": {"approval": -1.2}, "outcome": "O protesto esfria, mas a categoria se sente abandonada."}]},
    "liminar_stf": {
        "kind": "decisao", "tags": ["justica", "instituicoes"], "weight": 0.7, "cooldown": 200, "when": _always,
        "title": "Liminar suspende uma medida do governo",
        "text": "Um ministro fictício do Supremo suspende uma medida do Executivo por falta de base legal. A AGU pede orientação.",
        "fallback": "acatar",
        "choices": [
            {"id": "recorrer", "label": "Recorrer ao plenário", "tone": "dura", "hint": "Pode desgastar a relação com a Corte.",
             "effects": {"inst:institutional_resistance": 2, "governability": 1, "approval": 0.3}, "outcome": "O recurso mantém a medida em disputa por semanas."},
            {"id": "acatar", "label": "Acatar e reescrever a medida", "tone": "etica", "hint": "Evita atrito.",
             "effects": {"inst:constitutional_order": 2, "governability": -1}, "outcome": "A medida volta ao Congresso em nova forma."}]},
    "cambio_pressao": {
        "kind": "decisao", "tags": ["economia"], "weight": 0.8, "cooldown": 150, "when": lambda s: _m(s, "primary_balance", 0) < -1.0,
        "title": "Câmbio dispara em dia de incerteza fiscal",
        "text": "O dólar sobe após sinais de piora nas contas públicas. Operadores esperam uma sinalização do governo.",
        "fallback": "sinalizar",
        "choices": [
            {"id": "sinalizar", "label": "Anunciar meta de ajuste fiscal", "tone": "dialogo", "hint": "Acalma o mercado, pede disciplina.",
             "effects": {"primary_balance": 0.1, "congress_support": -1.5, "approval": -0.3}, "outcome": "O mercado respira, mas a base reclama de cortes."},
            {"id": "minimizar", "label": "Minimizar o movimento", "tone": "passiva", "hint": "Aposta que passa.",
             "effects": {"inflation": 0.3, "primary_balance": -0.1, "approval": -0.5}, "outcome": "O câmbio fica nervoso por semanas e o custo aparece nos preços."}]},
    "hospital_universitario": {
        "kind": "oportunidade", "tags": ["saude"], "weight": 0.7, "cooldown": 200, "when": _always,
        "title": "Hospital universitário pede socorro",
        "text": "A direção de um hospital universitário fictício avisa que vai suspender cirurgias por falta de insumos. Há uma janela para agir antes de virar manchete.",
        "fallback": "ignorar",
        "choices": [
            {"id": "aportar", "label": "Liberar aporte emergencial", "tone": "dialogo", "hint": "R$ 0,6 bi.", "cost_bi": 0.6,
             "effects": {"approval": 1.2}, "outcome": "As cirurgias seguem e a imprensa elogia a reação."},
            {"id": "ignorar", "label": "Deixar com o ministério", "tone": "passiva", "hint": "Sem custo.",
             "effects": {"approval": -0.8}, "outcome": "As cirurgias são suspensas por duas semanas."}]},
    "descoberta_cientifica": {
        "kind": "oportunidade", "tags": ["ciencia"], "weight": 0.5, "cooldown": 300, "when": _always,
        "title": "Grupo de pesquisa anuncia descoberta",
        "text": "Uma universidade federal fictícia anuncia um avanço em energia limpa. A equipe pede apoio para escalar o projeto.",
        "fallback": "parabenizar",
        "choices": [
            {"id": "financiar", "label": "Financiar o projeto", "tone": "dialogo", "hint": "R$ 1 bi em cinco anos.", "cost_bi": 1.0,
             "effects": {"approval": 0.8, "gdp_growth": 0.03}, "outcome": "O projeto recebe verba e vira vitrine do governo."},
            {"id": "parabenizar", "label": "Só parabenizar publicamente", "tone": "neutra", "hint": "Sem custo.",
             "effects": {"approval": 0.2}, "outcome": "O reconhecimento é bem recebido, sem consequências."}]},
    "queda_entre_jovens": {
        "kind": "oportunidade", "tags": ["opiniao"], "weight": 0.8, "cooldown": 150, "when": lambda s: _m(s, "approval", 50) < 55,
        "title": "Pesquisa mostra queda entre os jovens",
        "text": "Um instituto fictício aponta que a aprovação entre eleitores de 16 a 29 anos caiu. A equipe de comunicação propõe uma resposta.",
        "fallback": "ignorar",
        "choices": [
            {"id": "campanha", "label": "Lançar campanha digital", "tone": "dialogo", "hint": "R$ 0,3 bi.", "cost_bi": 0.3,
             "effects": {"approval": 1.0}, "outcome": "A campanha recupera parte do terreno."},
            {"id": "ignorar", "label": "Deixar passar", "tone": "passiva", "hint": "Sem custo.",
             "effects": {"approval": -0.4}, "outcome": "A tendência continua por algum tempo."}]},
    "vazamento_audio": {
        "kind": "decisao", "tags": ["integridade", "imprensa"], "weight": 0.6, "cooldown": 240, "when": _always,
        "title": "Áudio de um ministro vaza na imprensa",
        "text": "Um áudio atribuído a um ministro fictício critica publicamente aliados do governo. A base exige uma resposta.",
        "fallback": "advertir",
        "choices": [
            {"id": "demitir", "label": "Demitir o ministro", "tone": "dura", "hint": "Corta o problema, abre um vazio.",
             "effects": {"approval": 0.3, "governability": -2, "congress_support": -1}, "outcome": "A saída dá fim ao episódio e abre uma disputa pela vaga."},
            {"id": "advertir", "label": "Advertir e manter", "tone": "neutra", "hint": "Preserva a equipe.",
             "effects": {"governability": -0.5, "integrity": -0.5}, "outcome": "O ministro fica, mas com autoridade reduzida."}]},
    "convite_cupula": {
        "kind": "oportunidade", "tags": ["diplomacia"], "weight": 0.5, "cooldown": 240, "when": _always,
        "title": "Convite para uma cúpula regional",
        "text": "Um bloco regional fictício convida o presidente para uma cúpula sobre comércio e infraestrutura.",
        "fallback": "enviar_vice",
        "choices": [
            {"id": "ir", "label": "Comparecer pessoalmente", "tone": "dialogo", "hint": "Custa dias de agenda.", "cost_bi": 0.05,
             "effects": {"inst:military_loyalty": 0, "approval": 0.4, "gdp_growth": 0.02}, "outcome": "Acordos de comércio avançam e a imagem externa melhora."},
            {"id": "enviar_vice", "label": "Enviar o vice-presidente", "tone": "neutra", "hint": "Sem custo.",
             "effects": {"approval": 0.1}, "outcome": "A representação é correta, sem grandes ganhos."}]},
    "alta_aprovacao_info": {
        "kind": "info", "tags": ["opiniao"], "weight": 0.4, "cooldown": 240, "when": lambda s: _m(s, "approval", 50) > 65,
        "title": "Pesquisa registra boa avaliação do governo",
        "text": "Um instituto fictício registra melhora na avaliação do governo. Aliados pedem pautas mais ambiciosas.",
        "choices": [{"id": "ok", "label": "Acompanhar", "effects": {"congress_support": 1.0}, "outcome": "A base se anima e pede votações."}]},
}
