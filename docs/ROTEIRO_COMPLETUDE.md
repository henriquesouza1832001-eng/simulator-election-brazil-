# Situação do jogo e o que falta (10 nov. 2026)

Resumo honesto do que existe, do que é parcial e do que ainda não existe. Substitui a lista de pendências dispersa nos documentos anteriores como ponto de partida.

## Verificado agora
- 115 testes de backend e `npm run build` passam.
- Fluxo de carreira municipal (militante → pré-candidatura → campanha → eleição → posse ou derrota → continuação) roda no navegador em 390, 768 e 1280 px, sem rolagem horizontal e sem erros de console.
- Mandato presidencial de 48 meses simulado por API, com eleição, reeleição ou derrota.

## Pronto (base aceitável)
| Área | O que existe |
| --- | --- |
| Carreira | Eleitor → militante → filiado → dirigente → candidato; vereador, prefeito, deputados, governador, senador, presidente |
| Eleições | Calendário 2014–2030, Modo Eleitor com candidaturas oficiais do TSE, apuração proporcional simulada |
| Congresso | 513 deputados e 81 senadores reais, partidos reais com ideologia, votação nominal simulada |
| Eventos | Biblioteca de ~2.500 eventos em dados, remix fora de época, níveis por cargo |
| Competências | Aba por papel com base legal; 46 ações presidenciais (decreto, MP, lei, PEC, tratado, vedadas) |
| Indicadores | Registro de ~65 indicadores com grafo de influências e alavancas por cargo; 35 séries reais por município (Atlas 2010) |
| Território | País, regiões, 27 estados, municípios; obras de transporte e urbanismo com custo, prazo e competência |
| Design | Tema único, responsivo, Placar como tela inicial |

## Entregue depois da primeira versão deste roteiro (10 nov. 2026)
- **Motor unificado** (`engine/indicator_engine.py`): métricas nacionais alimentam o grafo do registro; efeitos se espalham pelos indicadores do país e chegam aos municípios a cada avanço do calendário. Aba Território > Brasil hoje.
- **Ações executáveis para vereador, prefeito, deputados, governador e senador** (`engine/office_powers.py`): custo em reserva ou capital político, votação simulada com chance mostrada, efeitos em confiança, reputação e indicadores do território.
- **Livro-razão previsto × realizado** (`engine/ledger.py`): toda ação de competência e toda obra registram previsão, resultado e a explicação da diferença.
- **Narrador** (`ai/narrator.py`): texto local por padrão; Gemini (se `GEMINI_API_KEY` no servidor) só reescreve os fatos do motor e é descartado se inventar números ou nomes.
- **Contas locais e LRF** (`engine/subnational_fiscal.py`): folha, dívida, limites, resumo mensal e obras pagas pela reserva do cargo.
- **Reguladores** (`engine/regulators.py`, `docs/REGULADORES.md`): STF suspende ou mantém atos de risco, AGU emite parecer prévio, tribunais de contas auditam obras, PF/MP abrem inquérito quando a integridade cai e o TSE mostra a conduta de campanha.
- **Trajetória partidária** leva também a governador, senador e presidente, após ao menos um mandato cumprido.

## Parcial (existe, mas incompleto ou raso)
1. **Competências só executam na Presidência.** Vereador, prefeito, governador, deputados e senador só leem o que cabe ao cargo. Falta o catálogo executável de cada um (lei municipal, CPI, ICMS, polícia estadual, sabatina…).
2. **O grafo de indicadores ainda não move o jogo.** `propagate()` é usado só pelas obras. Os indicadores nacionais do painel (`metrics`) seguem fórmulas antigas separadas do registro.
3. **Indicadores territoriais são de 2010 e estáticos.** Só mudam por obras do jogador; não evoluem sozinhos com a economia, nem há histórico.
4. **Obras e privatizações** usam custo único, sem orçamento anual, licitação, atraso, estouro ou contratação (o módulo antigo `works.py` tem isso, mas está separado do novo).
5. **Medidas em texto livre** têm 8 categorias e efeitos rasos; não passam pelo catálogo de competências nem verificam se o cargo pode fazer aquilo.
6. **Gemini:** só interpreta medidas e gera lotes de eventos offline. Não narra acontecimentos, resultados de eleição nem notícias durante a partida.
7. **Congresso:** votação nominal existe, mas sem comissões, relatores, emendas, urgência, obstrução ou vetos.
8. **Estados e municípios:** orçamento subnacional existe em dados, mas governador e prefeito não gerem receitas, folha, LRF nem repasses.
9. **Resultados eleitorais por candidato do TSE** não importados (só quem foi eleito).
10. **Posse em 5 de janeiro de 2027 (EC 111/2021)** ainda não aplicada.

## Não existe ainda
- STF, AGU, TSE, PF, Ministério Público e polícias como atores com decisões próprias (você definiu como etapa seguinte).
- Mídia e opinião pública (pesquisas por região, fake news, redes), sindicatos, empresariado, igrejas, movimentos.
- Crises e desastres com resposta federativa (enchente, seca, pandemia) ligadas a estados e municípios.
- Economia setorial e regional (agro, indústria, serviços) com choques externos (juros dos EUA, preço de commodities).
- Salvamento em nuvem entre dispositivos com conta, multijogador e ranking compartilhado (apenas documentado).
- Mapa interativo do Brasil.
- Testes de interface automatizados no repositório (a auditoria de navegador é um script local).

## Ordem sugerida
1. **Unificar o motor:** fazer o painel nacional e o territorial lerem do registro de indicadores e propagar efeitos a cada avanço de tempo (item 2 e 3). É a base de tudo que vem depois.
2. **Catálogo executável por cargo** (item 1), reaproveitando `powers.py`, com custos em capital político e orçamento.
3. **Orçamento e obras unificados** (item 4, 8), com LRF.
4. **Gemini narrador** (item 6): recebe fatos do motor e escreve; nunca decide número.
5. **Atores institucionais** (STF, AGU, TSE, PF, MP, polícias) e mídia/opinião pública.
6. **Séries anuais** por município (RAIS/Caged, SIM/Sinan, Siconfi, TSE votos) com importadores próprios.
7. **Conta, nuvem e multijogador.**
8. Revisão jurídica das bases legais e dos números de design por especialistas.
