# Roadmap do simulador

## Situação atual

- **Já funciona:** calendário diário, avanço por vários dias, eventos, votações simuladas e maturação de investimentos.
- **Já funciona:** orçamento federal simplificado, despesas operacionais, investimento por área e motor fiscal com dívida, juros, resultado e risco.
- **Já funciona:** dificuldade em cinco níveis, medidas interpretadas com prévia, crises, diplomacia e autenticação Cognito quando configurada.
- **Já funciona:** o jogador escolhe até seis cartões entre os indicadores de economia, contas, instituições, diplomacia, regiões e serviços.
- **Esta entrega:** a visão geral mostra seis cartões e uma prioridade diária; a aba completa agrupa os indicadores em seções recolhíveis e inclui população, IDH, Gini, pobreza, expectativa de vida, mortalidade infantil, homicídios, saneamento e conclusão escolar.
- **Esta entrega:** os novos indicadores sociais têm linhas de base simuladas e evoluem gradualmente com crescimento, desemprego e entregas acumuladas de educação, saúde, segurança e infraestrutura.
- **Esta entrega:** o orçamento foi separado em contas públicas, investimentos e obras, evitando carregar todas as decisões numa rolagem única.
- **Fatia municipal entregue:** catálogo versionado com 5.571 municípios, códigos IBGE e estimativas populacionais de 2026; campanha exige escolher uma cidade válida e mostra fonte, data, porte e a regra simulada de alcance.
- **Fatia de temas entregue:** campanha presidencial e carreira usam IDs compartilhados para saúde e educação, mantendo `servicos` como alias compatível com partidas anteriores.
- **Ainda parcial:** eleitorado municipal, perfil econômico, IDHM e temas-âncora não estão importados; estados e União ainda não têm agenda de campanha cidade a cidade.
- **Ainda parcial:** eleitores municipais, perfil econ?mico, IDHM e temas-?ncora n?o est?o importados; estados e Uni?o ainda n?o t?m agenda de campanha cidade a cidade.
- **Esta entrega:** primeira regra de campanha presidencial: janela de 90 dias, uma atividade a cada sete dias, custo fora do Tesouro, texto com rubrica explicável, apoio regional e efeito no cálculo eleitoral; atividade também avança o calendário do governo.
- **Ainda parcial:** a previsão de medida usa coeficientes amplos por categoria; ainda não explica a curva mês a mês nem aplica uma trajetória específica por instrumento.
- **Agora implementado em versão inicial:** catálogo de seis obras simuladas — rodovias, ferrovia, hidrovias, porto e saneamento — com leilão, parcela anual, previsão de entrega e preço registrado na contratação.
- **Agora implementado em versão inicial:** custos futuros usam índice de obra que cresce com a inflação do cenário; compromissos anuais consomem a dotação de Transportes e logística, e estouros entram no resultado fiscal.
- **Agora implementado em versão inicial:** contratadas fictícias têm perfis de preço e risco; dificuldade financeira ou alerta de integridade pode suspender um projeto e abrir uma decisão com custo, prazo e consequência.
- **Agora implementado em versão inicial:** viagens bilaterais e participação em eventos internacionais consomem dias de calendário; missão ativa aparece com rota, destino, retorno previsto e custo, e os efeitos só entram na conclusão.
- **Agora implementado em versão inicial:** campanha política para sete cargos eletivos, resultado eleitoral, transição, mandato simplificado, oposição e histórico do mesmo personagem; a derrota não apaga a carreira.
- **Agora implementado:** calendário de eleições municipais e gerais, abertura da campanha 90 dias antes, pré-campanha visível e posse em janeiro; reeleição respeita a duração do mandato e o ciclo correspondente.
- **Agora implementado em versão inicial:** vereador e deputado disputam vagas proporcionais entre legendas fictícias pelo método D'Hondt; executivo e Senado usam disputa majoritária simplificada. A tela explicita as cadeiras simuladas e a hipótese de lista.
- **Agora implementado em versão inicial:** três canais sociais fictícios têm alcance, público, custo e chance de viralização próprios; o motor calcula efeitos positivos e reações adversas.
- **Agora implementado:** a campanha oferece conduta regular ou um atalho irregular abstrato; a integridade institucional define a chance de detecção, e a apuração pode aplicar revisão e penalidade eleitoral.
- **Agora implementado em versão inicial:** nomeação para ministérios de catálogo fixo, formação simulada de gabinete e indicação ao STF com sabatina/votação no Senado.
- **Agora implementado em versão inicial:** posse abre um pronunciamento obrigatório de 80 a 1.200 caracteres. A rubrica é determinística, seus efeitos ficam visíveis e o backend bloqueia outras ações até a fala ser registrada.
- **Agora implementado em versão inicial:** indicadores comparáveis das cinco regiões e eventos mensais com efeitos persistentes sobre serviços, economia, orçamento e grupos afetados.
- **Agora implementado:** decisões de crise mostram custo e efeitos previstos antes da resposta. Adiar seca, pressão na saúde, falha digital ou questionamento de contrato cria uma memória; o fato pode voltar em cerca de 90 dias, no máximo duas vezes.
- **Agora implementado em versão inicial:** importador opcional do TSE guarda candidaturas com ano, território, cargo, situação declarada e licença; a aba de carreira consulta o arquivo e informa quando falta importar o conjunto.
- **Agora implementado:** entrada Cognito por e-mail e senha, cadastro sem etapa de confirmação, recuperação de senha quando o e-mail está verificado e confirmação opcional de e-mail dentro do jogo. Senhas não passam pelo backend do simulador.
- **Ainda parcial:** esta carteira usa custos de jogo e não substitui projeto executivo, cronograma físico-financeiro por lote ou dados reais de execução.
- **Ainda parcial:** viagem diplomática tem deslocamento, custo e duração aproximados; ainda falta uma animação de rota entre países e uma agenda completa de reuniões durante a missão.
- **Ainda parcial:** os mandatos de vereador, prefeito, deputado, senador e governador têm ações genéricas; faltam orçamento, poderes, serviços e calendário legislativo específicos de cada ente.
- **Ainda parcial:** a pré-campanha aguarda o início da janela oficial; faltam ações de organização partidária antes dela, magnitude real dos distritos, pesquisas por candidato, propaganda, arrecadação detalhada e debates em vários turnos.
- **Ainda parcial:** nomeações e STF usam personagens fictícios e parâmetros agregados; ainda faltam convites para a carreira do jogador e trilhas de decisão separadas para cada instituição.
- **Ainda parcial:** eventos têm sorteio reproduzível por partida, peso regional e sazonal, memória de adiamentos e impactos no tempo; falta ampliar o catálogo de eventos empresariais, climáticos e políticos e ligar promessas de campanha e investigações a eventos de retorno.

## Próximas entregas, em ordem

### 0. Geografia, personagens e interpretação local

Catálogo municipal e temas canônicos já têm primeira implementação e testes. A próxima camada geográfica depende de adicionar eleitorado, perfil econômico e IDHM com fonte e data, depois ligar visitas territoriais aos cargos estaduais/federais. Campanhas nomeadas e a separação entre logs de interpretação e avaliação narrativa continuam como frentes próprias. A [validação cruzada das três propostas](VALIDACAO_CRUZADA_PROPOSTAS.md) registra os contratos e critérios de aceite.

### 1. Indicadores e explicação das decisões

- Manter um catálogo único no motor com nome, unidade, grupo, fonte, explicação e histórico de cada indicador.
- Distinguir valor observado no cenário, estimativa do jogo e dado importado com fonte/data.
- Expandir a prévia de ação para mostrar efeito imediato e estimativas de 1, 3 e 12 meses, com incerteza e condições. A mesma trajetória deverá ser aplicada pelo motor ao avançar o calendário.
- Mostrar por que o resultado mudou: medidas, eventos, preços, juros, coalizão ou execução de orçamento.

### 2. Orçamento e obras nacionais

- Completar o catálogo de rodovias, ferrovias, hidrovias, portos, energia, saneamento e conectividade com fases e opções por região.
- Cada projeto terá estado, custo estimado na data, correção anual de preços, fonte de recursos, desembolso, prazo, entrega física, efeito regional e risco de atraso.
- Dar às empreiteiras fichas persistentes, carteira de contratos, capacidade, saúde financeira e histórico de investigação, além dos perfis fictícios iniciais.
- Toda decisão exibirá custo neste ano, custo futuro, origem do recurso, regiões beneficiadas e efeitos colaterais.
- Próxima camada: etapas por lote, desembolso mensal, medição física, manutenção após entrega e ocorrências ligadas ao tipo de obra e ao clima regional.

### 3. Calendário, viagens e comunicação

- Preservar avanço dia a dia; compromissos consomem duração real e não pulam automaticamente o mês.
- **Parcialmente entregue:** visitas e eventos internacionais usam uma duração aproximada, custo de viagem e uma rota animada; o efeito diplomático chega ao retorno. Eventos nacionais continuam durante a ausência.
- Falta detalhar etapas de preparação e permanência, compromissos paralelos, consequências de agenda perdida e a rota geográfica por país.
- Tornar obrigatório o pronunciamento de posse e adicionar agenda de entrevistas, discursos e coletivas com consequências em grupos e notícias simuladas.
- Trazer fatos antigos de volta por memória de eventos, promessas, investigação e respostas anteriores.

### 4. Carreira e eleições

- **Parcialmente entregue:** começar em qualquer um dos sete cargos eletivos; fazer campanha, receber resultado, assumir após transição e seguir para nova disputa mantendo personagem, reputação e histórico.
- Cada nível terá território, atribuições legais, orçamento, calendário, aliados e indicadores apropriados.
- **Parcialmente entregue:** importar e consultar candidaturas históricas do TSE com origem e licença. Ainda faltam resultados nominais, ocupantes atuais e dados de partidos/mandatos; candidatura não é prova de cargo atual, ideologia ou conduta.
- **Parcialmente entregue:** há campanha de carreira por atividade, tema, fundo separado, avaliação de texto, apoio por grupo e região e canais sociais próprios. Ainda faltam preparação prévia, adversários, financiamento detalhado, propaganda, pesquisa pública, turnos de debate e apuração proporcional.

### 5. Redes e imprensa simuladas

- **Parcialmente entregue:** grupos de mensagem, vídeo/imagem e debate público têm público, custo e viralidade diferentes. Faltam linha do tempo persistente, moderação, desinformação como evento, veículos regionais e resposta da imprensa.
- O motor Python determina efeitos e limites; Gemini/RAG pode redigir publicações, respostas e notícias a partir do estado do jogo e da memória da partida.
- Conspiração, abuso de poder, fraude e ruptura só existem como escolhas ficcionais, com evidências, instituições, imprensa, Justiça e consequências persistentes. A IA não ensina métodos reais para cometer esses atos.

### 6. Dificuldade, visual e contas

- **Parcialmente entregue:** os cinco modos ajustam crises, volatilidade econômica, pressão eleitoral e flexibilidade de coalizão. Realismo Puro tem volatilidade econômica maior e resistência política intermediária; falta calibrar parâmetros com séries históricas validadas antes de apresentá-los como dados reais.
- Adotar identidade visual brasileira sem transformar cada tela em painel denso: visão resumida, grupos de indicadores e modais com impacto agora/depois.
- Criar elenco de retratos/caricaturas originais e fichas de personagens fictícios; dados e imagens de figuras públicas terão fonte e contexto.
- Expandir o login atual para múltiplas campanhas nomeadas por conta, exportação e recuperação de saves. Cadastro não confirma o e-mail; sem verificar o endereço na área Conta, o Cognito não consegue enviar recuperação de senha.

## Ciclo de implementação

Cada etapa será entregue como uma fatia pequena: modelo de dados, regra determinística em Python, endpoint, tela explicativa e documentação. Eventos gerados por IA são sempre marcados como simulados; resultados numéricos vêm do motor, não do texto gerado. Não vamos importar uma lista indiscriminada de pessoas: elenco e dados serão adicionados por cargo, região, eleição e fonte.

## Ordem prática a partir da base atual

1. Fechar o primeiro ciclo eleitoral até posse, pronunciamento obrigatório, mandato, prestação de contas, nova eleição e continuidade após vitória ou derrota.
2. Dar regras e orçamento separados aos mandatos municipais, estaduais e federais; limitar cada ação às competências do cargo.
3. Melhorar a tela de campanha com calendário, pesquisa, imprensa, debate e conversão de votos para cada tipo de eleição.
4. Aprofundar orçamento e obras: execução mensal, manutenção, companhias persistentes, licitações e risco climático regional.
5. Expandir eventos e memória da partida, conectando causas antigas a novas crises e compromissos vencidos.
6. Completar a camada de dados eleitorais com resultados nominais e mandatos atuais, mantendo ano, cargo, território, licença e data de extração distintos.
7. Finalizar conta, saves por jogador, backup/restauração, animação de viagem e identidade visual regional.

## Limites do modelo fiscal atual

Os valores de referência são abstrações do simulador, não uma reprodução da LOA ou do Siafi. A conta separa fluxos anuais, mas ainda precisa de execução mensal detalhada, vinculações legais, transferências entre entes e amortização explícita da dívida.
