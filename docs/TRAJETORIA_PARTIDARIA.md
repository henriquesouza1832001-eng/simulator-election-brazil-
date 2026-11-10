# Trajetória partidária (militante → partidário → candidato)

Camada anterior à carreira eleitoral. Código: `backend/app/engine/party_path.py`, `backend/app/party_routes.py`, `src/PartyPathPanel.jsx`.

## Fluxo

1. **Eleitor engajado**: sem partido; faz reuniões, atos e estudo até acumular militância (15).
2. **Militante**: panfletagem, abaixo-assinado, debate local, ajuda a campanhas. Com militância 30 e contatos 10, pode **pedir filiação**.
3. **Filiação**: análise de 14 dias; pode ser **recusada** (carência de 60 dias). Pesam afinidade entre a sua posição política e a linha do partido (dimensões separadas), militância, contatos e reputação. Partido real do catálogo do TSE ou **fictício validado** (sem termos nazistas/fascistas, sem se passar por partido existente).
4. **Filiado**: tarefas, reuniões do diretório, padrinho político. Com prestígio 40 e 90 dias de casa, **disputa cargo no diretório**.
5. **Quadro do partido**: depois de 180 dias de casa, pode lançar uma pré-candidatura se atingir os requisitos do cargo. O município é validado pelo código IBGE para cargos municipais; cargos estaduais e federais usam a UF escolhida. A reputação é levada ao motor de carreira.

| Cargo | Prestígio | Contatos | Reputação | Eleição |
|---|---:|---:|---:|---|
| Vereador(a) | 55 | 35 | 45 | Municipal |
| Deputado(a) estadual | 62 | 45 | 52 | Geral |
| Prefeito(a) | 70 | 55 | 60 | Municipal |
| Deputado(a) federal | 72 | 58 | 60 | Geral |

A campanha termina com apuração proporcional simulada para vereador e deputados. As cadeiras são distribuídas por D'Hondt entre legendas fictícias; dentro da legenda, a posição depende dos votos nominais simulados. Uma derrota preserva personagem e histórico e devolve o jogador ao diretório para preparar outra disputa. A vitória segue para transição e mandato. Eventos próprios do mandato legislativo aparecem durante os mandatos de vereador e deputados.

Mecânicas: energia (recupera com o tempo; abaixo de 35 tudo rende 60%), retorno decrescente por repetição, risco de gafe em algumas ações, inatividade corrói reputação e prestígio, acontecimentos próprios de militante (60) e de partido (48).

## Verificado

Testes de ponta a ponta: `tests/test_party_path.py` cobre a progressão até a primeira candidatura; `tests/test_municipal_career_flow.py` cobre campanha, apuração, derrota, retorno ao partido e nova candidatura, além do caminho de vitória até o mandato legislativo. O modelo proporcional também verifica que a força de campanha altera a chance de eleição e que um custo remixed é aplicado uma única vez.

## Limites e simplificações (não são regra legal)

- Os prazos de filiação e de "tempo de casa" são **simplificações de jogo**. O prazo legal real por ciclo está marcado como pendente em `election_rules`.
- A rota partidária lança vereador, prefeito, deputado estadual e deputado federal. Senador, governador, presidente, vice, assessor parlamentar e cargos de nomeação ainda não têm rota por esse fluxo.
- Magnitudes de distrito, lista de candidatos e comparecimento são simplificações do jogo; não representam uma apuração oficial. Votos e personagens da lista são simulados.
- Não há vida interna completa de partido (alas com votos, fundo partidário, ética, expulsão).
- O painel mostra as próximas eleições municipais e gerais calculadas pelo calendário do jogo. Datas futuras são cenários simulados até a publicação do calendário oficial.
