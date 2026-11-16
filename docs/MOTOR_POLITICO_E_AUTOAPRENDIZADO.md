# Motor político do Quatro Anos: um Brasil que se comporta como o Brasil

Proposta de 15 nov. 2026. Reúne tudo o que foi pedido para o motor (projetos, crises, Congresso, eleições, leis, história, redes e aprendizado), o que o jogo já tem hoje e a ordem sugerida. Os números de versão são sugestão; a única decisão já tomada é que a 0.6 prepara o Gemini (ver `ROADMAP_VERSOES.md`).

## 0. Andamento (atualizado em 15 nov. 2026)

- **Feito: aba Projetos.** 37 projetos em 8 tipos, com ciclo em quatro fases, financiamento pela carteira da própria área e efeito nacional na entrega. Inclui o programa espacial: Centro de Lançamentos de Alcântara (base comercial), constelação de satélites, astronauta brasileiro em órbita e Missão Lunar Brasileira (R$ 150 bi, que exige remanejar o orçamento de Ciência). Cartões com arte própria em SVG, que a imagem real substitui quando existir.
- **Feito: competências ampliadas.** O catálogo de poderes foi de 51 para 75 ações, com saúde, educação, assistência social, meio ambiente, Justiça e Judiciário (indulto, anistia, mandato e número de ministros do STF), relação com o Legislativo (emendas, sessão extraordinária, reforma política), memória e regime militar e espaço. Cada uma com base legal e precedente real.
- **Feito: 8 de janeiro.** Entra como decisão de memória: indultar, apoiar anistia no Congresso ou não agir, com custo de confiança institucional e efeito na lealdade militar.
- **A fazer, nesta ordem:** crises por local (frente B), régua de escala do Gemini (frente C), MP com trancamento de pauta (frente D), mapa por município (frente E), base de leis e fatos (frente F), redes por plataforma (frente G), aprendizado (frente H).

## 1. Regra que organiza tudo

- **O motor decide.** Custo, efeito, voto, resultado e probabilidade saem de regras e tabelas em Python, com semente da partida (reproduzível).
- **A IA traduz e narra.** O Gemini transforma o texto do jogador em uma proposta estruturada; o motor confere, limita e calcula. Nenhum número do Gemini entra no jogo sem passar por uma régua do motor.
- **Realidade como memória, ficção como personagem.** Leis, datas, instituições e fatos reais servem de contexto e de régua. Pessoas reais só entram como sátira sob as regras de 1.0 (seção 9).
- **Tudo tem fonte e faixa.** Cada regra aponta para a norma ou o dado que a inspira e declara a faixa em que pode variar. Sem fonte, a regra fica marcada como "estimativa editorial".

## 2. Do que existe hoje (levantamento no código, 15 nov. 2026)

| Frente | Já existe | Lacuna |
|---|---|---|
| Obras | `works.py` com 6 obras e, desde 15 nov., 37 projetos (`works_catalog.py`) com aba Projetos | Sem licenciamento ambiental e TCU como fases com eventos próprios; custo ainda por catálogo, não por `custo unitário × tamanho` |
| Eventos e crises | 2.460 acontecimentos na biblioteca (`story_catalog`), 124 eventos históricos locais, corpus de **67 fatos** 2014–2026 (todos `source_verified: false`) | Poucas crises-tipo por local; nada ligado a risco geográfico real (barragem, encosta, enchente) |
| Congresso | Câmara 513 e Senado 81 com composição real, voto nominal simulado, PL e PEC, urgência, vetos e sanção (`congress_process`, `congress_agenda`); MP já vale na hora e vira projeto com prazo de 120 dias, revertida se não for convertida (`powers.py`) | MP sem trancamento de pauta aos 45 dias, prorrogação 60+60 e comissão mista; sem PDL e resolução do Senado; Senado como casa revisora ainda simples |
| Eleição | Pesquisa, campanha, TV, teto de gastos, apuração por estado, regiões e legenda, 2 turnos | **Mapa por município**; candidatos reais por município (dados TSE já importados em parte) |
| Leis e história | `COMPETENCIAS_E_PODERES.md`, regras eleitorais, regulação | Base de normas estruturantes com efeito no motor; memória histórica (8 de janeiro, regime militar) |
| Redes e sátira | `social_feed.py` com modelos por tipo de fato, perfis, alcance | Plataformas por perfil de público, grupos de família, boato; geração que aprende |
| Aprendizado | `learning/train` e `trainer.py` (exemplos corrigidos pelo jogador) | Aprendizado de eventos, calibração histórica e bots de simulação |
| Gemini | Interpretar, mapear e perguntas funcionam com o modelo mínimo (prova de 15 nov.) | Régua de escala (seção 5) |

## 3. Frente A: aba "Projetos" (melhor que o Planalto)

O Planalto lista obras num cartão. Aqui o governo tem um **portfólio de projetos** com ciclo de vida completo.

- **Aba própria "Projetos"**, separada de "Obras e mapa" (que fica só com o mapa). Filtros por tipo, região, fase, risco e quem paga.
- **Catálogo** (meta inicial: 120 tipos, cada um com ficha real de custo unitário): rodovias e duplicações, ferrovias, pontes e viadutos (entendi "alcantra" como obras de arte de engenharia; me corrija se for outra coisa), portos, aeroportos, hidrovias, metrô e BRT, saneamento, habitação, escolas e creches, hospitais e UPAs, barragens de contenção e drenagem, energia (hidrelétrica, eólica, solar, transmissão), reformas e retrofit, praças e equipamentos urbanos.
- **Ciclo**: ideia → estudo e projeto básico → licença ambiental → licitação (Lei 14.133) → obra → entrega → manutenção. Cada fase tem prazo, custo e um risco que o motor sorteia com semente.
- **Quem paga**: União, estado, município, convênio, emenda parlamentar, concessão ou PPP. O cargo do jogador limita o que ele pode iniciar sozinho.
- **Fiscalização e política**: TCU e tribunais de contas, aditivos, superfaturamento, empreiteira em crise, embargo por liminar, inauguração em ano eleitoral (a lei restringe), efeito no mapa e na base.
- **Custo por escala**: o custo vem de `custo_unitário × tamanho × índice regional`, não de um número fixo.

Aceite: abrir 3 obras de tipos diferentes, ver cada uma mudar de fase, estourar prazo em uma delas e ver o efeito nos indicadores locais e no Painel.

## 4. Frente B: crises e eventos por local

A ideia é que o evento dependa **de onde** o jogador governa, como acontece no país.

- **Mapa de exposição por município**: risco de enchente e deslizamento (encostas e planícies de inundação), seca (semiárido), incêndio (Cerrado, Pantanal, Amazônia), barragens de rejeito (Minas e Pará), epidemia (adensamento e saneamento), apagão, greve de transporte. Os dados saem de bases abertas (IBGE, CEMADEN/INPE, ANA, ANM) e ficam em `data/`, com a fonte ao lado.
- **Crises-modelo**, cada uma com fases, atores e dilema de resposta: rompimento de barragem (inspirado em Mariana 2015 e Brumadinho 2019), pandemia (inspirada na covid-19 em 2020), enchentes do Rio Grande do Sul em 2024, deslizamentos urbanos (Petrópolis 2022), seca e queimadas, crise hídrica, apagão, greve de caminhoneiros, crise bancária e cambial.
- **Federalismo na resposta**: quem decreta calamidade, quem recebe verba, quem fiscaliza; o prazo de resposta é parte do dilema.
- **Entrevistas e debates** (`interviews.py`, `question_bank.py`) passam a puxar a crise em curso: o jornalista pergunta sobre a barragem da sua cidade, não sobre um assunto genérico.
- **Gerador**: o sorteio usa risco do município × estação do ano × estado da obra e da fiscalização. Uma barragem sem manutenção aumenta a chance de rompimento; uma obra de drenagem concluída a reduz.

Aceite: a mesma partida em Petrópolis e em Sobral recebe crises diferentes; uma obra de drenagem concluída reduz a gravidade da enchente seguinte.

## 5. Frente C: Gemini como tradutor, motor como juiz

Fluxo:

1. O jogador escreve: "Quero um programa de renda para famílias do semiárido, uns R$ 15 bi por ano."
2. O Gemini devolve **só uma estrutura** (tipo de norma, objeto, público, abrangência, instrumento, custo declarado, restrições). Hoje já é assim (`interpreter.py`, `mapper_ai.py`).
3. **A régua do motor** (nova) confere o que o texto afirma:
   - Custo declarado × custo de referência: `beneficiários × valor × 12 meses`, `km × custo por km`, `leitos × custo por leito`. Quando a diferença passa de uma faixa, o motor mostra o próprio número e explica.
   - **Proporção com o cargo e o orçamento**: R$ 200 bi é uma fração grande de uma União e impossível para um município. O preview mostra "isto equivale a X% do orçamento do seu cargo" e exige fonte de custeio quando passa de um limite.
   - Competência: o cargo pode propor isso ou precisa do Congresso?
   - Efeito esperado (ex.: +R$ 15 bi de renda) vem de **elasticidades de tabela** por área, não do texto.
4. O motor calcula previsão e faixa de incerteza. O jogador confirma, ajusta ou corrige; a correção alimenta o aprendizado (seção 10).

Regra de segurança que já existe e fica: se o Gemini falhar, o interpretador local assume (já provado com chave inválida).

## 6. Frente D: Congresso por instrumento

Cada tipo de proposição tem rito, prazo e quórum próprios. Números do texto constitucional (Câmara 513, Senado 81):

| Instrumento | Rito resumido | Quórum de aprovação |
|---|---|---|
| Projeto de lei (PL) | comissões, plenário da Câmara, Senado como casa revisora, sanção ou veto | maioria simples |
| Lei complementar (PLP) | mesmo rito do PL | maioria absoluta: 257 deputados e 41 senadores |
| PEC | dois turnos em cada casa, sem sanção; as Mesas promulgam | 3/5: 308 deputados e 49 senadores |
| Medida provisória (MPV) | vale na hora; 60 dias prorrogáveis por mais 60; comissão mista; tranca a pauta após 45 dias; perde eficácia se não convertida | maioria simples |
| Decreto legislativo (PDL) e resoluções | sem sanção | maioria simples (casos específicos exigem mais) |
| Derrubada de veto | sessão conjunta | maioria absoluta nas duas casas |

Não identifiquei o que seria "mpp" na sua lista; tratei como MPV. Se for outra coisa, diga.

O motor modela: relator, comissões, calendário e urgência, **negociação** (emendas, cargos, pauta do presidente da Casa), bancadas temáticas e o custo político de cada derrota. A posição de cada parlamentar já existe (`legislature.py`); falta o trancamento de pauta da MP, a comissão mista, o PLP e o PDL.

O prazo de 120 dias da MP e a reversão já existem. Falta o trancamento de pauta no dia 46 e a comissão mista.

Aceite: uma MP editada no dia 1 tranca a pauta no dia 46, perde a eficácia no dia 121 se não for votada e o jogador vê isso na agenda.

## 7. Frente E: eleição com mapa por município

- Apuração em **cinco níveis**: Brasil, região, estado, microrregião e município (5.570), com boletins ao longo da noite (já existe por estado).
- Quem concorre vem dos dados do TSE importados (`tse_candidacies.py`), com o cenário fictício do jogador somado a eles.
- Mapa colorido pelo vencedor de cada município e por margem; clique abre a cidade (votos, comparecimento, abstenção, brancos e nulos).
- O voto municipal vem do perfil do município (renda, religião, urbanização, histórico de voto no atlas) e do efeito da campanha, TV e crises locais.

Aceite: uma eleição para governador mostra o mapa dos municípios do estado, e a soma deles bate com o total do estado.

## 8. Frente F: leis e história do Brasil como base de conhecimento

"Todas as leis do país" são centenas de milhares de normas. O jeito viável é em três camadas:

1. **Núcleo (150 a 300 normas)** que mudam o jogo e têm efeito no motor: Constituição de 1988, LRF, Lei 14.133 (licitações), Lei das Eleições, Ficha Limpa, Marco Civil, LGPD, improbidade, teto de gastos (EC 95), reforma da Previdência (EC 103), reforma trabalhista, marco do saneamento, Código Florestal, entre outras. Cada uma com instrumento, quórum, efeito e **link oficial** (Planalto/LexML).
2. **Índice de referência**: busca por assunto no LexML, sem efeito no jogo, para o jogador consultar.
3. **Leis fictícias geradas** a partir de padrões reais, para o jogador propor coisas novas.

**Fatos e história**: o corpus de 67 fatos passa a ser alimentado por fontes abertas (Agência Câmara, Agência Senado, IBGE, TSE), cada fato com fonte primária e `source_verified`.

- **8 de janeiro de 2023**: evento de memória com decisão do presidente: indulto individual, enviar projeto de anistia ao Congresso, ou não agir. O motor modela só consequências (STF, Forças Armadas, base, opinião, imprensa), com texto neutro e sem rotular pessoas.
- **Regime militar (1964 a 1985) e transição**: linha do tempo jogável em modo "memória": AI-5, Lei de Anistia (1979), Diretas Já (1984), Constituinte (1988), Comissão Nacional da Verdade (2012). Alimenta a métrica de lealdade militar e pautas de memória e justiça de transição.
- Temas sensíveis ficam atrás da regra: **fato verificado, sem opinião do jogo**, com fonte à vista.

## 9. Frente G: pares, adversários, redes e sátira

- **Atores**: aliados, adversários, imprensa, humor, influenciadores, bancadas, empresários e movimentos. Cada um tem posição, estilo de fala, alcance e humor próprio, e reage **ao que o motor decidiu** (voto, crise, escândalo, obra).
- **Plataformas**: foto e vídeo curto, rede de família e amigos, grupos de mensagem (onde nascem boatos), microblog e vídeo longo. Cada uma com público e dinâmica própria: alcance, viralização, desinformação e correção.
- **Nomes**: recomendo nomes fictícios de paródia para as plataformas no lugar das marcas reais (risco de marca numa loja como a Steam). O jogo já faz isso nas empresas e partidos fictícios.
- **Pessoas reais**: seguem a decisão de 1.0. A sátira de figuras públicas é protegida no Brasil (o STF derrubou restrições ao humor eleitoral na ADI 4451), mas uso de imagem e nome em produto comercial pede revisão jurídica antes. Até lá, adversários e pares são arquétipos e personagens gerados, com partidos reais.
- **Geração**: o texto sai de modelos + recuperação de exemplos + ranking aprendido (seção 10); o Gemini pode reescrever o tom quando a narração for ligada.

## 10. Frente H: motor que aprende (e o papel do GPT-6 Luna)

"Autoaprendizagem" aqui significa quatro coisas concretas, nesta ordem de risco crescente:

1. **Aprender com o jogador** (já existe, falta ampliar): cada correção de interpretação vira exemplo para o classificador local.
2. **Aprender por simulação (bots)**: milhares de mandatos jogados por bots com perfis variados, para achar eventos que quebram o equilíbrio, finais impossíveis e estratégias dominantes. Saída: relatório de balanceamento e ajuste das tabelas, não mudança automática no jogo.
3. **Calibrar com a história**: rodar o motor de 2014 a 2026 com os dados reais e comparar com o que aconteceu (inflação, desemprego, aprovação). Erro grande = tabela errada.
4. **Aprender o que sortear**: um ranqueador (bandit contextual) escolhe qual evento, manchete ou post mostrar, com recompensa que **penaliza repetição** e premia variedade e coerência com o estado do país.

**Camadas em tempo de jogo**: regras e tabelas (verdade) > recuperador local sobre o corpus de fatos e leis > modelos pequenos treinados (classificador de texto para ação, ranqueador) > Gemini de modelo mínimo só para interpretar. O jogo continua jogável sem internet.

**O GPT-6 Luna como professor, fora do jogo**:
- É o modelo eficiente da família GPT-6 (id `gpt-6-luna`, lançado em 22 set. 2026, acesso por API). Preço divulgado por agregadores: cerca de US$ 0,10 por milhão de tokens de entrada e US$ 0,50 de saída. **Confira na página oficial da OpenAI antes de gastar.**
- Uso: gerar em lote, offline, dados sintéticos para treinar os modelos pequenos: propostas variadas de jogador por cargo × região × tema × estilo (com o rótulo correto), variações de manchetes e posts por tom, perguntas de entrevista e cenários de crise.
- Ordem de grandeza: 100 mil exemplos de ~400 tokens de saída são ~40 milhões de tokens, algo como **US$ 20 a 40** no total. É barato; o custo real é a **revisão humana**.
- **Qualidade**: revisão por amostragem (5%), conjunto de teste cego escrito à mão (300 casos que o modelo nunca vê), remoção de duplicatas e registro de origem (qual modelo, qual data, qual instrução) em cada exemplo.
- **Cuidados**: conferir os termos de uso da OpenAI sobre o uso de saídas para treinar modelos; não enviar dados pessoais nem dados de jogadores; guardar a chave da OpenAI em `backend/.env` com o mesmo script do Gemini (nunca no chat).

## 11. Ordem sugerida

| Etapa | Entrega | Pré-requisito |
|---|---|---|
| 0.6 | Gemini provado (feito), prova com a chave da Oracle, régua de escala (seção 5) | chave na Oracle |
| 0.6b | Aba Projetos com 40 tipos de obra e ciclo completo | catálogo de custos |
| 0.7 | Crises por local (10 modelos) e entrevistas ligadas à crise; MP com trancamento de pauta e comissão mista, PLP e PDL | mapa de exposição |
| 0.8 | Eleição com mapa por município; núcleo de 150 normas; memória histórica (8 de janeiro, regime militar) | dados TSE completos |
| 0.9 | Redes por plataforma, bots de balanceamento, calibração histórica, mandato inteiro com Gemini | corpus e dados sintéticos |
| 1.0 | Imagens finais, sátira de figuras reais com revisão jurídica, Steam | revisão jurídica |

## 12. O que preciso de você

1. Confirmar a ordem acima ou reordenar.
2. O que é "mpp" na sua lista de instrumentos.
3. Se "alcantra" é obra de arte de engenharia (ponte e viaduto) ou outra coisa.
4. Chave da OpenAI, só quando chegar a etapa de dados sintéticos, gravada pelo script (não no chat).
5. Decidir se o jogo chega a nomes reais na sátira (1.0) e se haverá revisão jurídica.
