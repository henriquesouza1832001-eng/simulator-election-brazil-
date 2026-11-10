# Prompt mestre para o Claude — Civiciclo

Copie o bloco abaixo para o Claude Code aberto na pasta `C:\projetos\planalto\game`.

---

## PROMPT

Você está trabalhando no **Civiciclo**, um simulador político brasileiro para navegador, em React/Vite no frontend e Python/FastAPI no motor. O repositório já contém telas e sistemas em desenvolvimento. Sua tarefa é evoluir o jogo existente com mudanças concretas, preservando o trabalho local e avançando em fatias jogáveis. Não reconstrua o projeto do zero.

### 1. Comece pelo estado real do repositório

1. Leia `AGENTS.md` (se existir), `README.md` e os documentos de `docs/`, em especial os documentos de regras, personagem, retratos, roteiro de ampliação e comparação de referências.
2. Examine `git status --short`, a árvore de arquivos, as rotas React, os endpoints FastAPI, os modelos de estado, a persistência e a configuração de deploy.
3. Há alterações locais que podem ainda não estar commitadas. **Não descarte, sobrescreva, reverta, formate em massa ou inclua no seu commit alterações que você não produziu.** Faça mudanças pequenas, revise o diff e só faça commit das suas próprias alterações com arquivos explicitamente selecionados.
4. Não faça deploy nem crie recursos pagos na AWS nesta tarefa. Não exponha chaves, tokens, dados de conta ou credenciais em logs, código, navegador ou documentação.
5. Não pare depois de escrever um plano: faça primeiro uma fatia vertical jogável, documente o que ficou para as próximas etapas e informe o que foi realmente alterado.

### 2. Produto e experiência

O Civiciclo é uma sátira/simulação, não um serviço eleitoral. O jogador pode:

- entrar como visitante, sem conta; login opcional deve servir para sincronizar ou recuperar partidas;
- escolher entre **Modo Eleitor**, **Campanha e carreira** e **Posse direta na Presidência**;
- selecionar dificuldade antes de começar, com explicação objetiva do que ela altera;
- criar um personagem fictício opcional com nome público, cidade natal, origem familiar, costumes/vínculos, traços de atuação, espectro político em mais de um eixo e biografia curta;
- escolher cargo e território de campanha em uma etapa separada da criação de personagem. Cidade natal e município da candidatura são campos diferentes. Para eleição municipal, a cidade deve ser validada por código oficial do IBGE; para cargos estaduais/federais, valide UF e circunscrição;
- escolher um partido que realmente existia naquele ano ou criar um partido fictício. Não misture partido real e partido fictício. Posição ideológica do partido e perfil do personagem são dimensões separadas; não atribua automaticamente uma ideologia a alguém só por causa do partido. Ofereça nomes fictícios plausíveis e barre termos de ódio, nazistas/fascistas, difamatórios ou que se façam passar por partido real;
- disputar eleições, vencer ou perder, continuar a carreira, aguardar o próximo pleito e, quando fizer sentido, ocupar cargos de nomeação em governos. Perder uma disputa não apaga a partida;
- acompanhar efeitos das decisões no dia, no mês e no horizonte futuro, com causas explicadas em linguagem simples.

A interface deve ser clara em tela pequena e desktop: uma decisão principal por etapa, títulos e fontes legíveis, contraste forte, cartões agrupados, detalhes recolhíveis, nada de uma página interminável com dezenas de painéis abertos. No painel inicial, mostre poucos indicadores escolhidos pelo jogador e deixe o restante agrupado por tema. Indicadores que exigem precisão, como IDH, risco, juros e valores fiscais, devem manter casas decimais coerentes e unidade explícita.

O tutorial guiado deve ser curto, contextual, pulável e retomável. Ensine data/avanço do tempo, campanha, votação simulada, orçamento, eventos e leitura dos efeitos. A entrada direta na Presidência também deve estar disponível sem obrigar criação extensa de personagem.

### 3. Calendário eleitoral que deve existir

O seletor de cenário deve oferecer estes pleitos brasileiros:

| Ano | Tipo de eleição |
|---|---|
| 2014 | Geral |
| 2016 | Municipal |
| 2018 | Geral |
| 2020 | Municipal |
| 2022 | Geral |
| 2024 | Municipal |
| 2026 | Geral |
| 2028 | Municipal |
| 2030 | Geral |

O tipo/cargo e a circunscrição disponíveis devem depender do ano: eleições gerais incluem Presidência, governos estaduais, Senado e casas legislativas; municipais incluem prefeituras e câmaras municipais. Mantenha regras distintas por ano e por cargo. A linha do tempo precisa modelar pré-campanha, convenções, registro, campanha, votação, apuração, transição, posse e exercício do mandato. Respeite datas e duração de mandato próprios de cada cargo, incluindo o mandato de senador.

Permita dois usos eleitorais distintos:

1. **Modo Eleitor:** consultar candidatos e dados de um pleito real e escolher, dentro do jogo, um voto simulado; depois comparar com o resultado real oficial.
2. **Modo Campanha/Carreira:** jogar como candidato e atravessar campanha, eleição e eventual mandato; se perder, continuar a carreira e avançar para outros papéis ou pleitos.

Toda urna do jogo precisa exibir claramente: **“Voto simulado: não é enviado à Justiça Eleitoral e não altera uma eleição real.”** Não conecte o jogo a urna, pesquisa, serviço de votação ou coleta de voto real. Não transforme escolhas do jogador em opinião política pública sem consentimento explícito.

### 4. Candidatos e fatos: TSE como fonte primária

Para pleitos já realizados, use nomes, partidos, cargos, UF/município, números, situação do registro, candidaturas, resultados e votos oficiais do TSE. Não invente nem complete candidaturas por memória do modelo. A fonte deve acompanhar cada registro. Confira licença e obrigação de atribuição em cada conjunto de dados e ano; não presuma que todas as bases têm a mesma licença.

Fontes iniciais oficiais:

- Resultados de eleições do TSE (1933–2024 e links para estatísticas/dados): https://www.tse.jus.br/eleicoes/resultados-eleicoes
- Eleições anteriores e páginas por ano: https://www.tse.jus.br/eleicoes/eleicoes-anteriores
- Portal de Dados Abertos do TSE: https://dadosabertos.tse.jus.br/
- Exemplo de conjunto de candidaturas 2014: https://dadosabertos.tse.jus.br/dataset/candidatos-2014
- Exemplo de conjunto de candidaturas 2016: https://dadosabertos.tse.jus.br/dataset/candidatos-2016
- Registro e requisitos de candidatura: https://www.tse.jus.br/eleicoes/historia/processo-eleitoral-brasileiro/candidaturas/registro-de-candidatos
- Calendário eleitoral do TSE: https://www.tse.jus.br/eleicoes/calendario-eleitoral/calendario-eleitoral
- Lei nº 9.504/1997, texto consolidado no Planalto: https://www.planalto.gov.br/ccivil_03/leis/l9504.htm
- Constituição Federal consolidada: https://www.planalto.gov.br/ccivil_03/constituicao/constituicao.htm

Para 2026, use os arquivos oficiais do TSE correspondentes ao pleito e indique a data da extração. Para 2028 e 2030, não existem ainda candidaturas oficiais registradas em novembro de 2026. **Não adivinhe nomes de pessoas reais como candidatos futuros.** Crie elencos ficcionais marcados “cenário futuro simulado” até o TSE publicar registros oficiais; torne possível atualizar/importar os candidatos sem alterar o motor.

Construa importação versionada, reproduzível e com proveniência (`election_year`, `office`, código de UF/município, identificador TSE, partido naquele ano, situação, fonte, licença/atribuição, data da coleta e checksum do arquivo). Não faça download de grandes CSVs no navegador. Pesquise candidatos por filtros e paginação. Valide o número de registros e os resultados contra os relatórios oficiais; mostre a fonte na tela de detalhes.

Mantenha fatos históricos separados de acontecimentos simulados. Um acontecimento alternativo gerado pelo jogo deve carregar um rótulo de ficção. Nunca atribua a pessoa real crime, fala, doença, decisão, apoio, promessa ou escândalo fictício. Nomes e siglas reais só aparecem em informações verificáveis do TSE e do período correspondente. Uma nota dizendo “sátira” não substitui fonte, atribuição, respeito a direitos de imagem, licenças ou revisão jurídica antes de publicação.

### 5. Regras eleitorais com versão histórica

Não aplique a regra atual retroativamente a todo o período. Crie um `ElectionRuleset` por ano/cargo com fonte, data de vigência e resumo legível. Verifique, para o ciclo correspondente, pelo menos:

- idade mínima, domicílio eleitoral, filiação, elegibilidade e desincompatibilização;
- convenções, registro e calendário de campanha;
- primeiro e segundo turno e os critérios aplicáveis;
- eleição majoritária versus sistema proporcional, distribuição de vagas, federações e coligações;
- duração de mandato, posse, reeleição e calendário subsequente;
- financiamento, limites de gastos, prestação de contas, propaganda e regras de doação;
- alterações excepcionais de calendário, como as que afetaram 2020.

Use Constituição, Lei das Eleições, leis complementares e resoluções oficiais do TSE vigentes em cada data. Se a regra não puder ser confirmada, não fabrique precisão: deixe o dado marcado como pendente e não o use para um resultado apresentado como factual. Separe o **resultado histórico oficial** da **simulação alternativa** depois que o jogador toma decisões.

### 6. Motor do jogo e espaço de crescimento

O motor Python decide efeitos e resultados; a IA pode interpretar texto livre e redigir explicações/eventos, mas não decide sozinha o estado do país nem altera números sem regra validada. Use uma interface estruturada e validada entre frontend, motor e IA. Decisões precisam registrar estado anterior, mudança aplicada, motivo, data, efeitos imediatos e projeções com incerteza.

Modele a competência real de cada cargo. Prefeito não controla política federal; vereador não governa a cidade sozinho; governador e presidente têm orçamento, legislativo e limites próprios. Considere orçamento, receitas, despesas obrigatórias e discricionárias, investimento/obras, inflação de custos, cronograma e atrasos. As ações devem ser compatíveis com o nível de governo e com o calendário. Não permita aprovar dezenas de leis em um mandato por uma simples repetição de botão.

Eventos podem surgir de dados, calendário, condições regionais e sementes reproduzíveis. Eventos históricos reais devem ser identificados como tais e vinculados a fonte. Eventos alternativos são ficção. A IA produz texto depois que o motor determina o que aconteceu. Deixe claro o efeito imediato e o que pode reverberar nos próximos dias/meses.

A tela de indicadores deve agrupar detalhes por economia/trabalho, contas públicas, serviços, qualidade de vida, segurança, infraestrutura, instituições, regiões e relações exteriores. Mostre decimais adequados, unidade, período, fonte ou rótulo “estimativa do jogo”. Explicações distinguem dados públicos de números simulados.

### 7. Multiplayer: preparar agora, construir depois da base solo

O modo solo continua como prioridade e precisa funcionar sem login. Documente a arquitetura futura de multiplayer sem ativar serviços pagos nem complicar a partida solo. Preveja:

- sala/partida com cenário, dificuldade, calendário e jogadores;
- papéis distintos (candidatos, partido, equipe, governo ou oposição) com permissões explícitas;
- estado autoritativo no servidor, relógio compartilhado, log imutável de ações e mecanismo para evitar sobrescrita de saves;
- votações **dentro da partida** para decisões coletivas (por exemplo, escolha de candidato, aliança, prioridade partidária ou decisão de governo), com prazo, quórum, empate, abstenção, resultado e trilha auditável;
- opções para cada pessoa votar em privado quando apropriado e divulgação apenas do resultado agregado;
- moderação, bloqueio de abuso, reconexão, convites e limites de sala.

Não confunda votação entre jogadores com voto real. Primeiro entregue dados de cenário, partida solo e persistência; deixe multiplayer atrás de feature flag até que autenticação, regras e sincronização estejam prontas.

### 8. Retratos, cenários, marca

Use os arquivos recém-adicionados em `public/assets/backgrounds/` e `public/assets/portraits/caricatures/`. O catálogo `public/assets/portraits/catalog.json` já separa caricatura de foto oficial e registra aviso de sátira. Preserve essa separação.

Para candidatos históricos, priorize foto do TSE com atribuição/licença e identificador do registro. A caricatura é outra arte, deve ficar vinculada ao personagem e à candidatura corretos e exibir aviso de sátira. Não gere 1.000–1.200 retratos indiscriminadamente agora: primeiro defina o elenco que aparece no caminho jogável, prove o fluxo de metadados e revisão, depois amplie por lotes priorizados. Cada arte precisa de nome/ID, referência e origem, autor ou método de geração, data, licença/atribuição aplicável, ano/candidatura relacionada e aviso claro. Não use caricatura como se fosse prova de um fato.

Revise a identidade visual existente e use “Civiciclo” como nome de trabalho. Se propuser outro nome, faça uma verificação básica de colisões em lojas/domínios/marcas e explique que isso não substitui busca jurídica de marca. Evite logotipos ou imagens sem origem e licença clara. Use as imagens novas como cenários, não como fundos que prejudiquem a leitura.

### 9. Ordem de execução — faça, não apenas recomende

**Entrega A — fluxo jogável prioritário**

- Tela inicial curta para escolher Modo Eleitor, Campanha/Carreira ou Posse direta.
- Passos visíveis para ano, dificuldade, cargo, território e personagem; incluir início em qualquer ano da lista.
- Validar municípios/UF e impedir combinações incoerentes entre tipo de eleição, cargo e território.
- No Modo Eleitor, carregar candidatos históricos oficiais quando houver dados e entregar uma urna de simulação explicitamente não real.
- Para 2028/2030, exibir o aviso de cenário futuro e participantes ficcionais.
- Manter visitante sem conta; deixar login como opção para salvar/sincronizar.

**Entrega B — dados e regras**

- Criar modelos e importação de datasets de candidaturas/resultados do TSE para anos históricos.
- Registrar fontes/licenças e regras por ano/cargo.
- Implementar uma primeira rota jogável de carreira: criação do personagem → campanha → votação/apuração → posse ou derrota → continuação.
- Garantir que disputa perdida não destrua save e que passar os dias não salte uma fase obrigatória.

**Entrega C — multiplayer e expansão**

- Documentar contratos/API e migrações futuras para sala, jogador, voto interno e sincronização.
- Não fingir que multiplayer está pronto se ainda não estiver implementado.
- Planejar integração posterior de eventos/RAG e lote de retratos sem bloquear a versão solo.

Após a primeira fatia, mostre um resumo com: arquivos alterados, fluxo que agora funciona, fonte dos dados usados, decisões simuladas versus fatos, limitações ainda abertas e instruções exatas para eu abrir e jogar localmente. Registre cada item futuro como uma etapa concreta; não encerre dizendo que “está completo” sem estar.

### 10. Definição de pronto para esta rodada

- O jogador consegue iniciar como visitante sem falha de Cognito/login.
- Pode escolher um ano válido, cargo e território coerentes, com cidade validada por fonte oficial.
- Os anos históricos mostram apenas candidatos/dados confirmados e a referência consultável.
- 2028/2030 não apresentam candidatos reais como confirmados.
- O botão de votar descreve explicitamente uma simulação e nunca envia dados a uma eleição real.
- A primeira fatia campanha/eleição avança e preserva a partida tanto em vitória quanto em derrota.
- Texto e indicadores são legíveis, agrupados e explicam fonte, unidade e precisão.
- Documentação, changelog e diff identificam o trabalho entregue e o que permanece pendente.

Comece agora pela auditoria do repositório e depois implemente a menor fatia vertical que satisfaça esses critérios sem quebrar os sistemas já existentes. Não peça esclarecimentos sobre escolhas rotineiras; tome decisões pequenas, registre-as e siga em frente.

---
