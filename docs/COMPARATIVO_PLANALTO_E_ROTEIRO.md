# Auditoria funcional do PLANALTO e roteiro do Mandato

Data da leitura do PLANALTO: 2 nov. 2026. O produto de referência é uma sátira política; este projeto reaproveita categorias de sistemas e ritmo, não textos, personagens, arte ou regras proprietárias.

## O que o PLANALTO oferece

| Sistema | Elementos observados |
| --- | --- |
| Entrada e campanha | Começar campanha presidencial de 13 semanas ou assumir a Presidência em 2027; convenção, comícios, debates, imprensa e apuração. |
| Mandato | 48 meses, medidas em texto livre, calendário, decisões executivas, projetos, MPs e PECs. |
| Legislativo | Câmara com 513 votos individuais, Senado, frentes, coalizões, emendas, cargos, CPIs e pautas. |
| País | 32 grupos sociais, 27 governadores, aprovação segmentada, inflação, câmbio, dívida, risco-país e reações públicas. |
| Economia | Orçamento, impostos, previdência, estatais, energia, abastecimento, rodovias, política monetária e investimentos por área/região. |
| Governo | Nomeações, ministérios, agenda de execução, políticas, obras e continuidade entre governos. |
| Diplomacia | Visitas bilaterais, acordos, cúpulas e efeitos de posição internacional. |
| Crises e imprensa | Eventos com escolhas, respostas públicas, figuras que reagem, noticiário e efeitos persistentes. O conteúdo é rotulado como sátira/ficção. |
| Outros percursos | Político, jornalista, advogado e empresário; a descrição do produto inclui eleições, cobertura jornalística, casos até o STF e empresas em sete setores. |
| Instituições | STF, nomeações, disputas constitucionais, votação e possibilidade de ruptura no universo ficcional. |
| Meta-jogo | Ranking, coleção de 120 conquistas, histórico de mandatos e modo multiplayer separado. |
| Conta | Conta individual, mandatos guardados, sessões/dispositivos e controle de acesso por jogador. |

Fonte: [PLANALTO — página do jogo, recursos e Diário Oficial v1.32](https://planalto.fun/). A página anuncia uma pessoa por cargo, medidas escritas pelo jogador, votos individualizados e reações econômicas e sociais.

## O que já existe neste protótipo

- Interface React/Vite e API FastAPI em Python, empacotadas em Docker.
- Hospedagem numa EC2 com SQLite persistente, CloudFront HTTPS e Cognito. O origin exige cabeçalho secreto; o acesso pelo IP retorna 403.
- Calendário diário e progressão por dias/semanas/meses.
- Painel configurável com economia, inflação, desemprego, dívida, saldo primário, aprovação e governabilidade.
- Prévia de medida em linguagem natural, regras de efeito numérico e correção do jogador; Gemini opcional e fallback local.
- Economia fiscal simplificada, orçamento e investimento por área, custos de viagens e residência.
- Diplomacia com visitas e eventos multilaterais.
- Eventos/crises simulados, memória de ações e calendário legislativo fictício.
- Dificuldades, instituições, mecânica abstrata de ruptura, campanha diária e carreira inicial com eleição, posse, mandatos sucessivos e arquivo.
- Importador manual de candidaturas do TSE, consulta paginada e filtros por ano/UF/cargo/nome, catálogo SIORG e notas sobre proveniência.

## Capturas recebidas e fluxo de referência

As capturas de 2 nov. 2026 mostram etapas que servirão como referência funcional. A meta é reorganizar esses padrões para o Mandato, sem reproduzir a identidade, os textos ou os retratos do PLANALTO.

### Entrada, campanha e continuidade

- A tela inicial reúne partidas salvas, situação do mandato, prazo, botão para continuar, eleição, posse e arquivo/noticiário.
- A campanha aparece como percurso próprio antes da posse; o governo continua como outra fase do mesmo calendário.
- O usuário apontou um problema explícito na referência: rolagem muito longa e excesso de informação simultânea. A interface do Mandato deve mostrar uma prioridade por tela e levar o restante a abas, grupos recolhíveis ou detalhes sob demanda.

### Sabatinas e debates

- A preparação informa formato, participantes, duração de cada turno e regra de avaliação antes de abrir o estúdio.
- A sabatina individual mostra jornalista, pressão da imprensa, pergunta, cronômetro, limite de caracteres e campo de resposta.
- Depois de responder, a tela explica a nota e quais grupos do público reagiram; o jogador avança para a próxima pergunta.
- No debate, a sequência separa pergunta da mediação, resposta, réplica, tréplica, pergunta a um adversário e considerações finais.
- Ao encerrar, o jogo resume o desempenho, mostra quem mudou de opinião e traz um trecho simulado do bloco que ocorreu sem o jogador.
- Uma faixa lateral de campanha registra fatos simultâneos — atos, alianças e organização regional — para mostrar que a campanha continua entre entrevistas.

### Visão de governo e gabinete

- A visão do país mostra cartões de indicadores, fato do dia, medida em tramitação e um resumo regional; as telas de governo aprofundam as pastas, o Congresso e as instituições.
- O gabinete organiza as áreas e os titulares, com decisões específicas ligadas ao papel de cada cargo.
- No Mandato, esses dados passam a ser apresentados em níveis: resumo diário, indicadores por grupo e páginas próprias para decisão, orçamento, instituições e relações exteriores.

### Reorganização iniciada

- A página inicial do Mandato agora concentra até seis indicadores escolhidos e uma prioridade de hoje, com atalhos para a agenda, crises e criação de medidas.
- A lista completa de indicadores saiu da visão geral e está numa aba própria, em grupos recolhíveis.
- A composição de medidas fica numa aba separada; assim, consultar o país não abre automaticamente o editor longo.
- O orçamento agora se divide em três tarefas — contas públicas, investimentos e obras — para não empilhar controles fiscais e projetos numa única rolagem.
- A campanha de carreira já está conectada ao calendário: atividade por tema, fala avaliada, limite semanal, fundo separado, apoio acumulado, continuidade de personagem e três canais sociais com alcance simulado. Sabatinas, debates em turnos e regras específicas por cargo seguem como próximas fatias.
- A posse exige pronunciamento de 80 a 1.200 caracteres. O motor mostra uma rubrica de 12 pontos e impede ações mutáveis até o registro.
- O painel completo de indicadores inclui contas anuais de receita, gasto primário, juros e dívida; esses valores são estimativas do simulador e podem ser escolhidos entre os seis cartões iniciais.

## Lacunas principais

1. **Identidade e isolamento:** Cognito, validação de JWT e separação de campanhas, histórico de ações e correções por jogador estão implementados. Saves antigos migram para uma campanha inicial com ID `default`.
2. **Carreira jogável:** campanhas para sete cargos, resultado, transição, posse, mandato inicial e retorno após derrota ou mandato concluído estão implementados. Falta separar competências, orçamentos, serviços e legislação de cada ente.
3. **Legislativo:** não há Câmara/Senado com integrantes e bancadas individualizados no motor; apoio agregado substitui negociações, pauta, comissão, emenda e voto nominal.
4. **Orçamento executável:** há valores de referência e ajustes, mas ainda não uma LOA/fonte por programa, execução mensal, transferências federativas, empenho, contratos e conciliação entre mudança e entrega.
5. **Estados e municípios:** popularidade regional existe em protótipo; falta governo estadual/municipal, competências próprias, câmara local, transferências e serviços de cada ente.
6. **Eleição e campanha:** eleição presidencial é uma abstração. Faltam calendários consistentes para cada cargo, candidatos/partidos, arrecadação, alianças, pesquisa, debate, propaganda, turnos e transição.
7. **STF e nomeações:** catálogo e sabatina/votos independentes ainda são incompletos. Regras legais precisam de data de referência e fontes.
8. **Eventos:** aumentar a variedade sem deixar a IA inventar causalidade ou efeitos. Regras determinísticas escolhem o acontecimento e calculam impactos; IA fica na narrativa e explicação, sempre com selo simulado ou fonte histórica.
9. **Conteúdo/dados:** o importador TSE de candidaturas e a consulta com proveniência funcionam após a importação manual; faltam resultados nominais, composição atual dos cargos e bases da Câmara, Senado, IBGE, Tesouro e Banco Central. Retratos públicos e caricaturas ficam em conjuntos separados.
10. **Experiência:** substituir a sensação de “painel gerado por IA” por uma mesa de governo editorial: manchete/assunto do dia, agenda curta, poucas métricas selecionadas e telas temáticas profundas com explicação e histórico.
11. **Operação:** domínio e HTTPS, autenticação, cópias automáticas testadas, limite/alerta de custos e recuperação de conta antes de liberar o serviço publicamente.

12. **Geografia, personagens e aprendizagem:** três propostas foram revisadas em conjunto. As decisões de IDs municipais, temas canônicos, vetores ideológicos, logs de interpretação/narrativa e ordem de implementação estão em [`VALIDACAO_CRUZADA_PROPOSTAS.md`](VALIDACAO_CRUZADA_PROPOSTAS.md). O catálogo municipal, as campanhas nomeadas e a validação fiscal no servidor já têm fatias iniciais implementadas.

## Modelo de jogo proposto

- Um relógio diário comum, mas decisões consomem intervalos coerentes: agenda executiva, propostas legislativas, eleições, viagens e negociações têm cadências distintas.
- O cargo define competências e recursos; o jogador nunca pode executar uma ação fora da alçada. Vereador, prefeito, deputado estadual/federal, senador, governador e presidente têm ciclos e indicadores próprios.
- Derrota eleitoral muda o caminho, não apaga o personagem: oposição, partido, jornalismo, advocacia, negócios, assessoria ou futura candidatura seguem disponíveis quando fizerem sentido.
- Campanha e governo coexistem durante eleição. A máquina pública continua funcionando e eventos não pausam porque há debate.
- Um motor determinístico versionado transforma decisões em efeitos; IA interpreta linguagem e redige contexto. Toda previsão aparece como simulação, não como fato certo.
- Dificuldade altera parâmetros e eventos de modo explícito. “Realismo puro” usa parâmetros documentados e não promete previsão do mundo real.
- Eventos têm gatilho, evidência, efeitos, prazo, grupos afetados, contramedidas e semente reproduzível; catástrofes como enchentes mudam serviço, orçamento e trajetória ao longo do tempo.

## Sequência de implementação

### Base imediata

- [x] Inventariar a aplicação e a referência PLANALTO.
- [x] Preparar saves, ações e correções com `player_id`; backend valida JWT Cognito quando configurado.
- [x] Criar o User Pool e configurar HTTPS para habilitar cadastro real.
- [x] Validar token Cognito no backend e filtrar dados pelo identificador verificado do jogador.
- [x] Criar importador TSE com origem/licença, armazenamento de campos minimizados e consulta filtrada; os anos são importados manualmente no servidor.
- [x] Criar várias campanhas por jogador, com nome, cargo e dificuldade configuráveis.
- [ ] Definir as entidades centrais: jogador, personagem, campanha, cargo, mandato, evento, medida, orçamento e fonte.

### Vertical slice de carreira

- [x] Começar como candidato a qualquer um dos sete cargos eletivos, com campanha, apuração, transição e posse simuladas.
- [ ] Implementar mandatos municipais e estaduais com orçamento, serviços, câmaras e calendários eleitorais próprios.
- [x] Consultar candidaturas eleitorais históricas do TSE com origem, licença e aviso de escopo.
- [x] Manter reputação e histórico após derrota ou término de mandato; nomeações federais têm módulo inicial separado.

### Governo e país

- [ ] Voto por partido e parlamentares, coalizões, comissões e Senado.
- [ ] Orçamento detalhado e revisão de gasto com origem, regra, cronograma, entrega e consequência.
- [ ] Indicadores locais e nacionais de saúde, educação, segurança, infraestrutura, economia e confiança.
- [ ] Eventos persistentes de clima, saúde, segurança, diplomacia e economia.
- [ ] Conselho de ministros, órgãos existentes e catálogo de cargos conforme estrutura oficial.

### Conteúdo e qualidade

- [ ] RAG com trechos oficiais datados; exibir fonte/limite de conhecimento.
- [ ] Avaliações do intérprete e do agente Python com estados sintéticos, métricas e revisão humana.
- [ ] Retratos caricaturais originais apenas para elenco curto; placeholder fictício para os demais.
- [ ] Backup semanal fora da instância, teste de restauração, logs, limites de uso e alertas.

## Arquitetura de conta e campanha

- Cognito User Pool ativo para cadastro/login; o navegador usa e-mail e senha via SRP, com app client público sem segredo. O pré-cadastro confirma a conta sem marcar o e-mail como verificado; URL HTTPS atual: `https://d2dpmk0vrt66wn.cloudfront.net`.
- O frontend usa cookies Secure e SameSite=Lax para tokens; o backend valida JWT em todas as rotas privadas.
- API valida JWT em toda rota privada. O identificador imutável `sub` vira `player_id`; nunca confiar em um `player_id` enviado pelo navegador.
- O estado e as ações estão filtrados por `player_id` e `campaign_id`; correções e interpretações são isoladas por `player_id`.
- A próxima migração deve adicionar modo, personagem, cargo, calendário, estado e trilha de eventos versionada a cada campanha, sem alterar partidas existentes.
- Não criar tabela de senha própria. A implantação exige conta autenticada; o modo local permanece disponível apenas no desenvolvimento.
- A tela **Conta** permite validar o e-mail opcionalmente para que o Cognito habilite recuperação de senha. Contas ainda sem e-mail verificado não podem usar recuperação automática.

## Decisões de interface

- Início: “o que mudou hoje”, calendário, no máximo seis indicadores escolhidos e próxima decisão relevante.
- Navegação por trabalho: Governo, Território, Economia, Congresso, Diplomacia, Campanha, Instituições e Arquivo.
- Cada indicador abre composição, evolução, fonte/abstração e alavancas; remover abreviações sem contexto.
- Medida mostra interpretação, instrumento, competência, custo/financiamento, grupos afetados, incerteza, cronograma e consequência; assinatura exige revisão explícita.
- Evitar caixas e gradientes repetidos. Tipografia editorial, superfícies claras de hierarquia, cores semânticas consistentes, foco/teclado, celular e contraste.
