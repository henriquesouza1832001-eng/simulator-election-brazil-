# Análise de referência: Domínio Político

Revisão do repositório público [`saymonthedev/dominio-politico`](https://github.com/saymonthedev/dominio-politico) para orientar a evolução do Civiciclo. O clone local está em `C:\projetos\dominio-politico`, branch `main`, HEAD `df46a02` (snapshot de 7 nov. 2026). Esta é uma leitura de arquitetura e design; não copia código nem assets.

## O que a referência faz

O Domínio Político simula uma carreira desde a vida civil até cargos eletivos, com mundos iniciados no dia seguinte a eleições presidenciais reais de 2002 a 2026. O ponto de partida usa dados públicos daquele período; o que ocorre depois é marcado como simulação. Há sete cargos, partidos históricos, calendário e regras eleitorais por época, economia mensal, campanhas, eleições majoritárias e proporcionais, vida diária e histórias com escolhas.

O motor diário coordena economia, eleições, governos, finanças, partidos e histórias numa sequência explícita ([`tick.ts`](https://github.com/saymonthedev/dominio-politico/blob/main/packages/engine/src/tick.ts)). As regras eleitorais são selecionadas pelo ano ([`ruleset.ts`](https://github.com/saymonthedev/dominio-politico/blob/main/packages/engine/src/ruleset.ts)); o módulo eleitoral calcula disputas, pesquisas, debates, apuração, mandatos e representação proporcional ([`elections.ts`](https://github.com/saymonthedev/dominio-politico/blob/main/packages/engine/src/elections.ts)). Municípios têm prefeitos e câmaras de referência, com disputas detalhadas nas capitais e cidades de jogadores ([`cities.ts`](https://github.com/saymonthedev/dominio-politico/blob/main/packages/engine/src/cities.ts)).

Os acontecimentos têm tipos distintos — informativo, oportunidade ou decisão —, prazo, resposta padrão, limites de repetição e histórias que podem voltar depois ([`story/director.ts`](https://github.com/saymonthedev/dominio-politico/blob/main/packages/engine/src/story/director.ts), [`story/types.ts`](https://github.com/saymonthedev/dominio-politico/blob/main/packages/engine/src/story/types.ts)). O motor separa pessoas reais de personagens procedurais quando escolhe quem pode agir em histórias ([`story/world.ts`](https://github.com/saymonthedev/dominio-politico/blob/main/packages/engine/src/story/world.ts)). A aleatoriedade é reproduzível a partir de semente, subsistema, data de jogo e evento ([`rng.ts`](https://github.com/saymonthedev/dominio-politico/blob/main/packages/engine/src/rng.ts)).

O repositório separa aplicação web, motor puro e dados versionados: Next.js, pacote TypeScript sem dependência de React ou banco, snapshots eleitorais e migrações Supabase. A interface oferece páginas de campanha, eleições, governo, mapa, carreira, finanças e investigações. O projeto também dá opção de mundo compartilhado, pessoal ou inteiramente fictício. O README documenta fotos eleitorais atribuídas ao TSE e regras claras para distinguir fatos e ficção ([README do projeto](https://github.com/saymonthedev/dominio-politico/blob/main/README.md)).

## O que complementa o Civiciclo

O Civiciclo tem uma fantasia diferente: gestão dia a dia do governo, orçamento e gastos, indicadores, obras, diplomacia, crises e uma campanha que pode levar o jogador a sete cargos. A referência é mais profunda na carreira política antes e entre mandatos, nas regras históricas das eleições e na vida simulada de personagens; não substitui o ciclo de decisão executiva que estamos construindo.

| Tema | Domínio Político | Civiciclo | Aplicação recomendada |
| --- | --- | --- | --- |
| Relógio | Um processamento diário reúne sistemas e, no mundo compartilhado, o calendário também avança sem o jogador. | Avanço diário controlado, viagens e ações consomem tempo. | Manter o controle do jogador; adotar uma única sequência diária auditável e eventos com prazos. Deixar tempo compartilhado como modo futuro opcional. |
| Carreira | Vida civil, partido, campanhas, sete cargos e regras de elegibilidade em vários ciclos históricos. | Sete cargos e transições já existem; o foco principal inclui a Presidência e o mandato de 48 meses. | Usar a carreira como trilha persistente, preservando a escolha de começar direto na posse e a gestão do país durante a eleição. |
| Eleições | Calendário por ano, convenções, regras de filiação/domicílio, FEFC, federações, coligações históricas, quociente e apuração. | Calendários, pesquisas, campanha, resultados e segundo turno inicial já existem; regras e financiamento ainda estão simplificados. | Priorizar uma camada versionada de regras eleitorais e tornar visíveis etapa, prazos, elegibilidade, custos, pesquisa e consequência de cada ação. |
| Território | Dados de 5.570 municípios; eleição municipal completa nas capitais e cidades de jogadores, com outras cidades resolvidas deterministicamente. | Município validado pelo IBGE e TSE, campanhas e custos locais já têm fatias iniciais; orçamento subnacional e câmaras ainda são parciais. | Evoluir primeiro a cidade/UF efetivamente escolhida pelo jogador e oferecer comparações territoriais progressivas; não simular em detalhe todos os municípios em cada tela. |
| Personagens | Personagens fictícios têm identidade e relações persistentes; figuras reais são contextualizadas por fontes e limitadas em histórias inventadas. | Perfil de jogador, ministros e alguns NPCs existem, mas elenco persistente e histórico relacional ainda são incompletos. | Próxima camada forte: IDs estáveis, papéis, vínculos, aparições e histórico para ministros, parlamentares, imprensa e lideranças fictícias. |
| Eventos | Catálogo contextual, prazos, escolha padrão, cadência, cooldown e encadeamento entre dias ou meses. | Eventos diários e memórias já existem; falta aumentar variedade e amarrar melhor causas, respostas e retornos. | Guardar gatilho, prova simulada, custo, efeito imediato, efeito futuro, prazo, grupos afetados e condição de retorno em cada evento. |
| Reprodutibilidade | Sementes separadas por subsistema/data/evento; testes da simulação e das regras históricas. | Motor Python determinístico, logs e testes já existem; interpretação/treino ficam separados das regras. | Adotar sementes determinísticas independentes por sistema e registrar versão do motor, regra e cenário no save para reproduzir uma crise ou eleição. |
| Interface | Páginas temáticas e campanha com mapa, pesquisa, apoios e agenda. | A interface está sendo simplificada para poucas informações centrais e detalhes agrupados. | Reutilizar profundidade de conteúdo em páginas específicas; manter o painel diário curto, com “agora”, “depois” e abrir detalhes sob demanda. |
| Dados e conteúdo | Snapshots históricos e proveniência. O README informa 5.702 fotos eleitorais e distingue dado de partida e simulação. | TSE/IBGE já são importados com metadados; retratos próprios e continuidade automática da ingestão estão pendentes. | Registrar URL, órgão, ano, licença e data por fato/asset. Distinguir retrato oficial de caricatura original e usar elenco por etapas. |

## Recomendações para o próximo ciclo do Civiciclo

1. **Fechar os contratos do calendário político.** Definir por ano de eleição os prazos de filiação e domicílio, convenções, registro, propaganda, turnos, mandato e posse. Ligar cada cargo à regra e ao território corretos. O modo Normal pode abstrair resultados; Realismo Puro deve expor as hipóteses e ainda ser identificado como simulação.
2. **Persistir o elenco que sustenta a história.** Criar IDs duráveis para personagens fictícios e guardar relações, cargo, partido, estado/cidade, aparições, promessas e eventos. Isso permite que uma crise, entrevista ou investigação volte com contexto coerente, sem gerar uma pessoa nova a cada tela.
3. **Dar a cada acontecimento um ciclo completo.** Um evento deve dizer o que ocorreu, o que se sabe, o que ainda não se sabe, quais respostas estão disponíveis, quanto custam, o que muda imediatamente e o que pode voltar depois. Respostas vencidas precisam de consequência padrão explícita. O motor aplica os números; Gemini escreve e resume dentro desses limites.
4. **Separar determinismo por subsistema.** Uma decisão de diplomacia não deveria trocar o sorteio de uma eleição futura só por ter consumido números aleatórios antes. Usar chaves reproduzíveis derivadas de campanha, data, sistema e evento torna incidentes e resultados mais depuráveis.
5. **Aprofundar campanha sem transformar a home em painel eleitoral gigante.** O resumo pode mostrar cargo, etapa, intenção atual, tendência, caixa/energia e próximo prazo. Uma tela de campanha abre convenção, apoios, mapa, propaganda, debates, pesquisa e regras de apuração em seções separadas.
6. **Aproveitar as eleições para a continuidade do mandato.** A disputa precisa ocorrer enquanto o governo continua: agenda, orçamento, crises e equipes seguem ativos. Vitória inicia transição/posse; derrota conserva personagem, partido, reputação e caminhos de oposição, como já prevê a direção do Civiciclo.
7. **Expandir por território jogável, não por cobertura uniforme do Brasil.** Priorizar orçamento, serviços, câmara e calendário da cidade ou estado da partida. A base nacional pode apresentar resultados determinísticos resumidos até o jogador entrar naquele território.

## O que não trazer agora

- **Relógio automático compartilhado:** diverge do uso solo e do avanço diário escolhido pelo jogador. Pode ser um cenário multiplayer separado depois.
- **RPG de vida obrigatório:** carreira antes do cargo deve ser uma opção; posse imediata continua disponível.
- **Complexidade integral em todas as cidades e telas:** a referência tem muitos sistemas. No Civiciclo, a regra pode ser profunda sem mostrar todos os controles simultaneamente.
- **Dependência de IA para consequências:** sorteio, cálculo eleitoral, orçamento e efeito de decisão devem continuar no motor Python; IA interpreta ou narra.
- **Milhares de caricaturas na primeira entrega:** primeiro validar um conjunto pequeno dos personagens mais recorrentes e criar pipeline de atribuição e revisão. Foto eleitoral pública e caricatura original são classes de asset distintas.
- **Crimes ou falas fictícias atribuídos a pessoas reais:** separar claramente fatos com fonte e simulações. Histórias de escândalo, corrupção, saúde, citação e ação inventada devem usar personagens fictícios; aviso de sátira não deve servir de único controle editorial.

## Licença e reuso

O clone público revisado não tem arquivo `LICENSE` rastreado no snapshot `df46a02`. Portanto, esta análise aproveita ideias de produto e padrões observáveis; não incorpora código, screenshots, fotos ou outros assets do repositório. Qualquer reuso futuro exige confirmar a licença e a autorização aplicável.

## Referências locais

- Clone para leitura: `C:\projetos\dominio-politico` (branch `main`, `df46a02`).
- Estado e motor atuais do Civiciclo: [`README.md`](../README.md), [`ETAPAS_DO_JOGO.md`](ETAPAS_DO_JOGO.md), [`ROTEIRO_AMPLIACAO.md`](ROTEIRO_AMPLIACAO.md), [`SISTEMAS_E_REGRAS.md`](SISTEMAS_E_REGRAS.md) e [`VALIDACAO_CRUZADA_PROPOSTAS.md`](VALIDACAO_CRUZADA_PROPOSTAS.md).
