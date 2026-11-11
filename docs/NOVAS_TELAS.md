# Novas telas sugeridas

Proposta de telas que faltam para o jogo parecer um simulador completo, em ordem de valor. Cada uma indica de onde vêm os dados (já existem no motor ou precisam ser criados).

| # | Tela | Para que serve | Dados e estado |
| --- | --- | --- | --- |
| 1 | **Gabinete (centro de comando)** | Uma página inicial do mandato: decisões pendentes, prazos, ministros e secretários, relação com Congresso, e o que mudou desde a última visita. | Usa `consequences.pending`, `ledger`, `regulators.cases`, calendário. Falta o agregador. |
| 2 | **Mapa do Brasil** | Colorir estados e municípios por indicador (IDHM, Gini, mobilidade, aprovação) e abrir o detalhe ao tocar. | `territory` e Atlas já existem; falta mapa vetorial (malhas do IBGE). |
| 3 | **Sabatinas e entrevistas** | Perguntas encadeadas com avaliação clara (coerência, dados, tom), nota e efeito persistente. | Falta módulo; pode usar o gerador de perguntas e o mapeador de ações, com Gemini só para formular perguntas. |
| 4 | **Debates em etapas** | Abertura, blocos temáticos, direito de resposta e considerações finais, com pesquisa antes e depois. | `campaign_debate.py` tem um debate único; falta o fluxo em etapas. |
| 5 | **Congresso em detalhe** | Comissões, relator, emendas, urgência, obstrução, destaque; negociação por bancada com o que cada partido pede. | `legislature.py` tem votação nominal; faltam comissões e negociação. |
| 6 | **Relações (empresariado, sindicatos, igrejas, movimentos)** | Grupos de interesse com humor próprio, pedidos e reações às decisões. | Reações já existem (`consequences`); faltam os grupos como estado. |
| 7 | **Orçamento anual (LOA)** | Receita, despesa por função, emendas e resultado previsto × realizado por mês, para União, estados e municípios. | `subnational_fiscal` e `fiscal` existem; falta a visão por função e a aprovação pelo Legislativo. |
| 8 | **Eleições passadas jogáveis** | Escolher 2014–2026 e disputar como candidato, com resultados nominais comparáveis. | Candidaturas do TSE existem; faltam votos por candidato e regras históricas por ano. |
| 9 | **Painel do STF e dos reguladores** | Ministros com perfil, pauta, relatores e prazos; pedidos de vista. | `regulators` tem alinhamento agregado; falta composição individual. |
| 10 | **Conta e partidas na nuvem** | Entrar, ver partidas salvas, retomar de outro aparelho, backup e restauração. | Cognito opcional e saves por jogador existem; falta a tela de gestão. |

## Padrões de interface a manter
- Antes de confirmar: mostrar bloqueios, custo, prazo, território, base legal e risco.
- Depois: previsto e realizado lado a lado, com a diferença explicada (`ledger`).
- Pesquisas com data, margem e origem; crises que persistem e reaparecem.
- Separar ação do período, compromisso obrigatório e avanço do calendário.
- No celular: uma coluna, alvos de 44 px, sem rolagem horizontal fora de tabelas.
