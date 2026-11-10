# Trajetória partidária (militante → partidário → candidato)

Camada anterior à carreira eleitoral. Código: `backend/app/engine/party_path.py`, `backend/app/party_routes.py`, `src/PartyPathPanel.jsx`.

## Fluxo

1. **Eleitor engajado**: sem partido; faz reuniões, atos e estudo até acumular militância (15).
2. **Militante**: panfletagem, abaixo-assinado, debate local, ajuda a campanhas. Com militância 30 e contatos 10, pode **pedir filiação**.
3. **Filiação**: análise de 14 dias; pode ser **recusada** (carência de 60 dias). Pesam afinidade entre a sua posição política e a linha do partido (dimensões separadas), militância, contatos e reputação. Partido real do catálogo do TSE ou **fictício validado** (sem termos nazistas/fascistas, sem se passar por partido existente).
4. **Filiado**: tarefas, reuniões do diretório, padrinho político. Com prestígio 40 e 90 dias de casa, **disputa cargo no diretório**.
5. **Quadro do partido**: com prestígio 55, contatos 35, reputação 45 e 180 dias de casa, **lança a pré-candidatura a vereador** na sua cidade (código IBGE validado). A reputação construída é levada ao motor de carreira existente, que assume a campanha, a eleição e o mandato.

Mecânicas: energia (recupera com o tempo; abaixo de 35 tudo rende 60%), retorno decrescente por repetição, risco de gafe em algumas ações, inatividade corrói reputação e prestígio, acontecimentos próprios de militante (60) e de partido (48).

## Verificado

Teste de ponta a ponta (`tests/test_party_path.py`): do início à pré-candidatura a vereador em menos de 420 dias de jogo, com recusa de filiação possível e carência; efeitos de eventos aplicados; só eventos do nível certo disparam.

## Limites e simplificações (não são regra legal)

- Os prazos de filiação e de "tempo de casa" são **simplificações de jogo**. O prazo legal real por ciclo está marcado como pendente em `election_rules`.
- Só leva a **vereador**. Prefeito, deputado, vice, assessor parlamentar e cargos de nomeação ainda não têm rota.
- Não há vida interna completa de partido (alas com votos, fundo partidário, ética, expulsão).
- Começa em 1º de janeiro de 2027, rumo à eleição municipal de 2028.
