Resumo Executivo
"Quatro Anos" possui uma arquitetura de simulação institucional incomum no cenário independente brasileiro: 71 módulos determinísticos em Python, dados reais do TSE/IBGE/SIORG e uma integração disciplinada com o Gemini que jamais viola a soberania matemática do motor. Contudo, o exame das capturas reais e dos textos das telas revela que o jogo sofre de dispersão operacional e esterilidade narrativa. Enquanto o motor calcula 513 votos nominais e curvas de juros reais, a interface fragmenta a ação em mais de 15 telas sem hierarquia de urgência, e os textos soam como notas técnicas de consultoria fiscal, não como sátira política. Além disso, há inconsistências numéricas visíveis entre telas simultâneas (como inflação e risco-país exibidos com valores diferentes na mesma sessão) e gargalos graves de manutenção em arquivos monolíticos (career.py com 2.006 linhas). Atingir 9,5 em todas as 12 dimensões exige congelar novos subsistemas, unificar o loop central em uma Mesa de Despacho, calibrar o motor contra séries históricas reais e injetar humor ácido nos textos.

1. Contestação da Autoavaliação
#	Dimensão	Sua Nota	Minha Nota	Faixa Sustentável	Veredito e Evidência Concreta
1	Clareza e fluxo	
5,0

4,5	4,0 – 5,0	
Discordo (mais baixa). Em capturas/gov_visao-geral.png e textos_das_telas/gov.md, o jogador enfrenta 15+ abas e rodapés "LIGADO A ESTA TELA" que empurram para 4 direções distintas sem indicar qual exige ação no turno. Na campanha (pref.md), a tela visao-geral diz "Hoje há tempo para uma atividade de campanha", mas obriga o jogador a clicar em "Acompanhar carreira" (CareerPanel.jsx) para agir.

2	Coerência dos números	
6,5

5,0	4,5 – 5,5	
Discordo (muito mais baixa). No mesmo instante da partida presidencial (textos_das_telas/gov.md, mês 3/4 de 48): a tela indicadores mostra Inflação: 4,0% a.a. no card de topo e Inflação (IPCA): 4,3% a.a. logo abaixo; já visao-geral mostra 4,1%. Pior: mercado exibe Risco-país: 220, enquanto orcamento exibe risco-país 279 na mesma rodada.

3	Profundidade política	
8,0

7,5	7,0 – 8,0	
Discordo (levemente mais baixa). A estrutura de legislature.py (513 deputados + 81 senadores com dados abertos), congress_process.py, regulators.py e appointments.py (31 pastas SIORG + vaga STF) é excelente. Porém, faltam coalizões formalizadas com lideranças partidárias, chantagem de bloco e governadores/prefeitos como atores ativos no jogo presidencial.

4	Motor eleitoral	
6,0

5,5	5,0 – 6,0	
Discordo (mais baixa). Em textos_das_telas/pref.md, o candidato do MDB em São Paulo tem 34,4% contra 28,1% do PSOL e 26,7% do PRTB, mas tv_time.py (38 linhas) apenas aplica um bônus passivo de até 6%. Não há negociação de coligação, tempo de TV cedido por aliados, nem segundo turno dinâmico com transferência de votos.

5	Economia e mercado	
7,5

7,0	6,5 – 7,5	
Discordo (levemente mais baixa). macro.py, fiscal.py e central_bank.py modelam bem juro real, dívida/PIB e Copom a cada 45 dias. Porém, na tela orcamento (gov.md), o único corte granular exposto ao presidente é "Viagens oficiais (R$ 2,4 bi)" e "Residência oficial (R$ 0,6 bi)", o que move o resultado primário em 0,000% do PIB — uma armadilha de interface que dá falsa agência fiscal.

6	Eventos, narrativa e sátira	
5,5

4,0	3,5 – 4,5	
Discordo (muito mais baixa). O jogo promete sátira, mas gov.md e pref.md parecem relatórios do IPEA. Exemplo real em gov.md: "Mercado em movimento: dólar -1,2%, bolsa +6,2%, risco-país +0 pontos no período. Reação simulada do mercado financeiro". Em redes (gov.md e pref.md), mesmo após 3 meses de mandato, aparece "Nada nas redes ainda".

7	Uso da IA	
8,0

8,0	7,5 – 8,5	
Concordo. A arquitetura em backend/app/ai/ (gateway.py, speech_reader.py, mapper_ai.py, local_interpreter.py) isola perfeitamente a IA dos cálculos, com fallback determinístico e testes (test_gemini_guards.py). Não chega a 9,5 porque narrator.py e question_ai.py estão desligados em produção e não há telemetria de custo/latência por turno.

8	Balanceamento e rejogabilidade	
5,0

4,5	4,0 – 5,0	
Discordo (mais baixa). Como admite o próprio briefing, nenhum humano jogou 48 meses completos na UI atual. Em gov.md (visao-geral), o bloco "POR QUE MUDOU?" mostra três vezes o mesmo texto genérico: "Tendência da economia e do período". Além disso, começar com 31 ministérios vagos (nomeacoes) sem penalidade imediata de paralisia administrativa distorce o início do mandato.

9	Visual e áudio	
5,0

4,0	3,5 – 4,5	
Discordo (mais baixa). Áudio é zero. Nas capturas (capturas/gov_visao-geral.png, capturas/ini_01_Montar_candidatura.png), a tipografia editorial limpa é agradável, mas há excesso de caixas vazias, listas textuais longas sem hierarquia visual e 53 artes ainda faltando (docs/IMAGENS_RESTANTES.md).

10	Dados reais e fidelidade	
8,0

8,0	7,5 – 8,5	
Concordo. O uso de malhas IBGE, eleitorado municipal (ex.: São Paulo com 11.911.337 habitantes, código 3550308 em pref.md), composition real da Câmara/Senado e normas constitucionais (leis-e-historia em gov.md) dá lastro excepcional. Falta automatizar a atualização anual e blindar nomes de parlamentares reais contra associação difamatória.

11	Qualidade técnica	
6,5

5,5	5,0 – 6,0	
Discordo (mais baixa). Ter 366 testes é ótimo, mas career.py tem 2.006 linhas, App.jsx tem 69,9 KB, CareerPanel.jsx tem 67,1 KB, main.py concentra 47 rotas e um mandato de 48 meses demora ~70 segundos para simular. Isso indica acoplamento severo e gargalo de I/O ou recálculo redundante por tick.

12	Pronto para publicar	
3,5

3,0	2,5 – 3,5	
Discordo (mais baixa). Sem áudio, sem telemetria de erro/sessão, sem fluxo mobile funcional, sem política de privacidade/termos para login e com menção explícita a "513 deputados e 81 senadores, com nomes, partidos e estados dos dados abertos" (gov.md) misturados a mecânicas de corrupção/CPI, o risco jurídico e de retenção impede lançamento comercial.

2. "O que falta para 9,5", Dimensão por Dimensão
Dimensão 1: Clareza e fluxo (4,5 → 9,5)
Entrega 1.1 — Mesa de Despacho Única (Inbox do Turno): Criar um componente central no topo de OverviewPanel.jsx que consolida pendências obrigatórias (sanções vencendo, crises ativas, vagas críticas de gabinete, ações semanais disponíveis) antes de liberar o botão "Avançar Tempo".

Critério de aceite: Em teste de usabilidade com 10 jogadores novos sem instrução prévia, ≥ 90% executam uma decisão de governo ou campanha e avançam o primeiro turno em menos de 120 segundos.

Esforço: M | Dependências: Nenhuma | Risco: Baixo.

Entrega 1.2 — Unificação do Loop Campanha/Carreira: Eliminar o salto obrigatório entre OverviewPanel.jsx e CareerPanel.jsx para executar a ação da semana (pref.md), permitindo escolher a atividade de campanha diretamente na tela principal.

Critério de aceite: Número de cliques para realizar uma ação de campanha reduzido de 4 para ≤ 2, verificado por teste E2E (docs/TESTE_E2E.md).

Esforço: M | Dependências: 1.1 | Risco: Médio (refatoração de CareerPanel.jsx).

Entrega 1.3 — Indicadores de Estado de Aba (Badges de Urgência): Exibir contadores numéricos nas abas da barra lateral (Imprensa (1), Nomeações (31 vagas), Crises (0)) e ocultar abas inativas no modo campanha (ex.: esconder Diplomacia e Congresso para candidato a prefeito).

Critério de aceite: Zero abas irrelevantes ao cargo atual visíveis no DOM; 100% das pendências com prazo exibem badge vermelho quando faltam ≤ 7 dias.

Esforço: P | Dependências: Nenhuma | Risco: Baixo.

Dimensão 2: Coerência dos números (5,0 → 9,5)
Entrega 2.1 — Fonte Única de Verdade no Snapshot da API: Eliminar cálculos duplicados entre indicators.py, macro.py, fiscal.py e o front-end. Garantir que inflacao, risco_pais e aprovacao venham de um único objeto snapshot serializado em state.py.

Critério de aceite: Teste automático (test_coerencia_telas.py) valida que todos os endpoints (/api/game, /api/macro, /api/budget) retornam exatamente o mesmo valor arredondado para cada indicador no mesmo tick.

Esforço: P | Dependências: Nenhuma | Risco: Baixo.

Entrega 2.2 — Decomposição Causal Real em drivers.py: Substituir o rótulo genérico "Tendência da economia e do período" (gov.md) pela listagem explícita dos componentes da fórmula (ex.: "Inércia inflacionária (-0,15 pp)", "Selic acima do neutro (-0,12 pp)").

Critério de aceite: Em 100% dos avanços de turno nos testes de bots, a soma dos drivers exibidos em /api/game corresponde a ≥ 95% da variação líquida do indicador, sem nenhum rótulo genérico quando houver variação > 0,05.

Esforço: M | Dependências: 2.1 | Risco: Baixo.

Dimensão 3: Profundidade política (7,5 → 9,5)
Entrega 3.1 — Sistema de Coalizões e Lideranças de Bloco: Evoluir politics.py e appointments.py para que partidos formem blocos (Base, Centrão, Oposição) com um líder negociável, exigindo cota de ministérios e emendas para manter quorum e fidelidade mínima.

Critério de aceite: Teste unitário comprova que deixar > 50% dos ministérios vagos por > 30 dias derruba a governabilidade em ≥ 15 pontos e trava pautas no Congresso.

Esforço: G | Dependências: Nenhuma | Risco: Médio.

Entrega 3.2 — Judicialização Ativa (STF e Órgãos de Controle): Expandir regulators.py para que medidas com "risco jurídico alto" (gov.md, ex.: revogar autonomia do BC) sejam automaticamente contestadas via ADI no STF, gerando suspensão liminar e desgaste político se o governo não tiver maioria na Corte.

Critério de aceite: 100% das ações marcadas com risco jurídico alto em powers_catalog.py disparam rito de revisão judicial em até 15 dias simulados.

Esforço: M | Dependências: Nenhuma | Risco: Baixo.

Entrega 3.3 — Federação Viva (Governadores e Prefeitos na Presidência): Conectar territory.py ao jogo presidencial, fazendo governadores dos 5 maiores colégios eleitorais apoiarem ou boicotarem reformas federais conforme repasses e obras regionais.

Critério de aceite: Aprovação de PECs/leis federais varia em até ±12% conforme o alinhamento dos governadores simulados.

Esforço: M | Dependências: 3.1 | Risco: Médio.

Dimensão 4: Motor eleitoral (5,5 → 9,5)
Entrega 4.1 — Coligações Pré-Eleitorais e Negociação de Tempo de TV: Expandir tv_time.py e campaign.py para permitir ceder vice ou secretarias futuras a partidos médios antes da convenção, somando tempo de rádio/TV e fundo eleitoral.

Critério de aceite: Formar coligação com 2 partidos médios aumenta o tempo de TV em ≥ 40% e reduz o custo por voto de ações de mídia em campaign_week.py.

Esforço: M | Dependências: Nenhuma | Risco: Baixo.

Entrega 4.2 — Segundo Turno e Transferência de Votos: Implementar em election_rules.py e electoral_field.py a rodada de segundo turno para cargos executivos em cidades > 200 mil eleitores, estados e presidência, com negociação de apoio dos derrotados.

Critério de aceite: Simulação em São Paulo (pref.md) com 34,4% no 1º turno dispara obrigatoriamente o 2º turno contra o 2º colocado, recalculando intenção de voto com base na migração ideológica.

Esforço: M | Dependências: 4.1 | Risco: Médio.

Entrega 4.3 — Debate Interativo de 4 Blocos: Expandir campaign_debate.py e debate.py com confronto direto entre candidatos, direito de resposta e impacto imediato nas pesquisas da semana seguinte.

Critério de aceite: Participar de debate altera intenção de voto em até ±4,5 pp dependendo da nota de speech_score.py e da consistência temática.

Esforço: M | Dependências: Nenhuma | Risco: Baixo.

Dimensão 5: Economia e mercado (7,0 → 9,5)
Entrega 5.1 — Alavancas Fiscais Macro Reais: Substituir o micro-corte de viagens/residências em FiscalPanel.jsx (gov.md) por decisões fiscais estruturais: contingenciamento de despesas discricionárias, revisão de subsídios/isenções, meta de resultado primário e política de dividendos de estatais.

Critério de aceite: Cada alavanca fiscal altera o resultado primário entre 0,2% e 1,5% do PIB, com impacto mensurável em risco-país (macro.py) e aprovação popular.

Esforço: M | Dependências: 2.1 | Risco: Baixo.

Entrega 5.2 — Impacto Fiscal Subnacional: Conectar subnational_fiscal.py às decisões de prefeitos e governadores, permitindo emitir dívida (sujeita à LRF), reajustar IPTU/ICMS e sofrer bloqueio de transferências voluntárias se estourar limite de pessoal.

Critério de aceite: Estourar 54% da RCL com folha em prefeitura dispara alerta do TCE e bloqueia convênios federais em career.py.

Esforço: M | Dependências: Nenhuma | Risco: Baixo.

Dimensão 6: Eventos, narrativa e sátira (4,0 → 9,5)
Entrega 6.1 — Reescrita Editorial Satírica (Guia de Voz): Revisar os templates de event_templates.py, story_catalog.py e social_feed.py para trocar linguagem burocrática ("Reação simulada do mercado financeiro") por sátira política brasileira afiada (ex.: "Analistas da Faria Lima entram em pânico existencial após declaração sobre juros; dólar sobe antes mesmo do fim da frase").

Critério de aceite: 100% das strings de noticiario e redes passam por revisão editorial; zero ocorrências da palavra "simulada/simulado" dentro da narrativa diegética (manter avisos legais apenas no rodapé).

Esforço: G | Dependências: Nenhuma | Risco: Baixo.

Entrega 6.2 — Povoamento Contínuo das Redes Sociais (social_feed.py): Garantir que toda semana de campanha e todo mês de governo gerem ao menos 4 a 6 posts satíricos nas 4 redes fictícias (Instante, Rostolivro, ZapZap, Passarinho) reagindo aos indicadores atuais, eliminando telas vazias como visto em gov.md e pref.md.

Critério de aceite: Zero ocorrências de "Nada nas redes ainda" após o turno 1 em qualquer modo de jogo.

Esforço: P | Dependências: 6.1 | Risco: Baixo.

Entrega 6.3 — Memória Narrativa e Cadeias de Consequência: Ampliar consequences.py para criar arcos de 3 a 5 episódios (ex.: obra superfaturada -> matéria investigativa -> pedido de CPI -> delação -> votação de cassação/impeachment) com biblioteca mínima de 250 eventos distintos.

Critério de aceite: Em 10 mandatos simulados consecutivos de 48 meses, a taxa de repetição de eventos na mesma partida é < 5%.

Esforço: G | Dependências: Nenhuma | Risco: Médio.

Dimensão 7: Uso da IA (8,0 → 9,5)
Entrega 7.1 — Ativação Controlada de narrator.py com Cache e Orçamento: Ligar narrator.py para gerar manchetes editoriais e reações de imprensa a partir dos fatos determinísticos do turno, com cache por hash de estado e teto de tokens por partida.

Critério de aceite: Custo médio por mandato completo de 48 meses ≤ US$ 0,03 usando modelo Flash/Lite; latência p95 < 1,5 s; 100% de fallback automático em caso de timeout.

Esforço: M | Dependências: Nenhuma | Risco: Baixo.

Entrega 7.2 — Transparência da Leitura Semântica (SpeechReading.jsx): Exibir imediatamente após o envio de texto livre o cartão estruturado (temas, tom, promessas, alvos) antes de consolidar o efeito, permitindo 1 ajuste por turno via InterpretationCorrection.jsx.

Critério de aceite: Taxa de divergência entre classificação do Gemini e avaliação humana em conjunto de 100 discursos de teste < 10%.

Esforço: P | Dependências: Nenhuma | Risco: Baixo.

Dimensão 8: Balanceamento e rejogabilidade (4,5 → 9,5)
Entrega 8.1 — Suite de Telemetria de Bots por Arquétipo: Expandir bots_balanceamento.py para rodar 500 partidas completas (5 arquétipos: Populista Gastador, Liberal Ortodoxo, Fisiológico do Centrão, Técnico Passivo, Radical Polarizador) e gerar matriz de vitória/derrota/impeachment.

Critério de aceite: Nenhum arquétipo vence > 65% ou < 15% das partidas na dificuldade Normal; estratégia "não fazer nada" perde em ≥ 95% das vezes.

Esforço: M | Dependências: 3.1, 5.1 | Risco: Baixo.

Entrega 8.2 — Cenários Assimétricos e Desafios Históricos: Transformar historical_play.py em modo de destaque no StartMenu.jsx com 8 cenários curados (ex.: "Crise Hídrica e Inflação", "Prefeitura Falida no Interior", "Minoria Absoluta no Congresso").

Critério de aceite: 8 cenários jogáveis com objetivos claros de vitória e pontuação no Placar da História (meta.py).

Esforço: M | Dependências: Nenhuma | Risco: Baixo.

Dimensão 9: Visual e áudio (4,0 → 9,5)
Entrega 9.1 — Paisagem Sonora Procedural/Discreta (Web Audio): Adicionar feedback sonoro opcional e leve: carimbo de despacho, burburinho de plenário, sino de abertura do pregão/mercado, flash de câmera em entrevista, urna eletrônica ("pililili") na apuração e música ambiente instrumental sutil.

Critério de aceite: 100% das ações principais e eventos de apuração possuem som dedicado com controle de mute persistente; peso total dos assets de áudio < 3 MB.

Esforço: M | Dependências: Nenhuma | Risco: Baixo.

Entrega 9.2 — Conclusão das 53 Ilustrações Editoriais: Gerar e integrar as 53 artes pendentes listadas em docs/IMAGENS_RESTANTES.md mantendo estilo unificado de gravura/xilogravura editorial brasileira (docs/DIRECAO_VISUAL.md).

Critério de aceite: Zero placeholders genéricos ou imagens quebradas em todas as telas e cartas de evento (CardArt.jsx).

Esforço: M | Dependências: Nenhuma | Risco: Baixo.

Dimensão 10: Dados reais e fidelidade (8,0 → 9,5)
Entrega 10.1 — Anonimização e Blindagem de Nomes Reais: Substituir os nomes reais dos 513 deputados e 81 senadores expostos na tela congresso (gov.md) por nomes fictícios gerados deterministicamente mantendo estado, partido e bancada reais do TSE/Câmara.

Critério de aceite: Zero nomes de parlamentares vivos encontrados na saída da API /api/game ou no banco SQLite de partida ativa, mantendo 100% de fidelidade na distribuição partidária e por UF.

Esforço: P | Dependências: Nenhuma | Risco: Baixo.

Dimensão 11: Qualidade técnica (5,5 → 9,5)
Entrega 11.1 — Decomposição dos Monolitos (career.py, App.jsx, CareerPanel.jsx): Quebrar career.py (2.006 linhas) em 5 módulos coesos (career_setup.py, career_campaign_tick.py, career_gov_tick.py, career_transitions.py, career_queries.py) e dividir App.jsx e CareerPanel.jsx usando contextos/hooks por domínio.

Critério de aceite: Nenhum arquivo Python ou JSX acima de 450 linhas; todos os 366+ testes existentes passando sem alteração de comportamento.

Esforço: G | Dependências: Nenhuma | Risco: Médio.

Entrega 11.2 — Otimização de Desempenho do Motor (< 5s por mandato): Perfilar o avanço de 48 meses (hoje ~70 s) para eliminar recálculos quadráticos em territory.py e indicator_engine.py, vetorizando ou cacheando agregações municipais.

Critério de aceite: Simulação completa de 48 meses executada em ≤ 5,0 segundos em benchmark automatizado.

Esforço: M | Dependências: 11.1 | Risco: Baixo.

Dimensão 12: Pronto para publicar (3,0 → 9,5)
Entrega 12.1 — Pacote Legal, Acessibilidade e Responsividade Mobile: Adicionar Termos de Uso, Política de Privacidade (LGPD), navegação completa por teclado/ARIA (WCAG 2.1 AA), layout responsivo para telas 360px–1920px e telemetria anônima de retenção/erros.

Critério de aceite: Score Lighthouse Accessibility ≥ 95; zero overflow horizontal em viewport 375x812; pipeline de erro capturando exceções de front e back.

Esforço: G | Dependências: 1.1, 10.1 | Risco: Baixo.

3. O Motor em Detalhe
Mecânicas que faltam ou estão rasas e como devem evoluir
Coalizões e Centrão (politics.py, novo coalitions.py): Hoje, cada deputado em legislature.py tem uma probabilidade individual de adesão. Na política brasileira, vota-se por liderança de bancada e federação. Deve existir um objeto CoalitionBlock (Base, Bloco Fisiológico/Centrão, Oposição) com um líder que negocia em pacote: "Entregue 2 ministérios de orçamento alto + R$ 4 bi em emendas e o bloco entrega 85% dos 190 votos". Se o governo atrasar o pagamento, o líder orienta obstrução.

STF e Judiciário (regulators.py, novo judiciary.py): Atualmente, regulators.py funciona como freio passivo. Quando o presidente assina decreto ou MP com risco jurídico alto (powers_catalog.py), um partido de oposição ou a PGR deve protocolar ação direta. O ministro relator sorteado (influenciado pelas indicações feitas via appointments.py) decide em 1–3 semanas pela liminar, criando crise institucional real se o Executivo ameaçar descumprir.

Imprensa Investigativa e Ciclo de Desgaste (interviews.py, consequences.py): A imprensa hoje apenas noticia o turno. Deve haver um indicador oculto de Pressão Investigativa: cortes na Lei de Acesso à Informação, nomeações sem critério técnico ou obras com aditivos alimentam dossiês que estouram na imprensa em momentos críticos (ex.: véspera de votação importante ou semana anterior à eleição).

Economia, Mercado e Setor Real (macro.py, fiscal.py, central_bank.py): O mercado hoje reage instantaneamente a coeficientes de design (mercado em gov.md). Falta o efeito defasado (lag de 3 a 9 meses): baixar juros na marra ou expandir gasto primário gera euforia de PIB e popularidade nos primeiros 6 meses, mas cobra a conta em inflação (IPCA) e perda de câmbio no ano 2 e 3, obrigando o Copom a subir a Selic às vésperas da eleição.

Território e Pacto Federativo (territory.py, subnational_fiscal.py): Governadores e prefeitos não podem ser passivos quando o jogador é presidente (nem o presidente ser ausente quando o jogador é prefeito). Criar transferências voluntárias (PAC/Convênios) e impacto regionalizado: obras no Nordeste aumentam aprovação lá, mas podem gerar crítica fiscal no Sudeste se não houver contrapartida.

Segurança Pública e Relações Exteriores (diplomacy.py, novo security_crisis.py): Segurança é um dos temas centrais do eleitorado brasileiro, mas hoje aparece apenas como indicador genérico. Deve gerar crises específicas (crise penitenciária, operação policial com repercussão, greve de PM estadual exigindo GLO). Em diplomacy.py, acordos comerciais devem alterar balança comercial e câmbio em macro.py, não apenas um índice abstrato de relação bilateral.

Validação do modelo (Calibração Plausível)
Calibração com séries históricas (2003–2026): Criar um script backend/scripts/calibrar_modelo.py que alimenta o motor com choques reais conhecidos (boom de commodities, crise fiscal de 2015, choque inflacionário pós-pandemia) e verifica se as trajetórias de IPCA, Selic, Câmbio e Dívida/PIB permanecem dentro de bandas históricas plausíveis:

Inflação (IPCA): [2,5%, 14,0%] em cenários normais (sem hiperinflação descontrolada por bug de multiplicador).

Aprovação presidencial: [12%, 78%], nunca travando em 0% ou 100% por saturação de soma.

Dívida/PIB: variação máxima plausível de -6 pp a +18 pp em 48 meses.

Comparação eleitoral com TSE (tse_votes.py): Rodar 100 eleições simuladas sem intervenção do jogador ("baseline histórico") nos 20 maiores municípios e estados; a correlação de Pearson entre a distribuição partidária simulada e os resultados oficiais do TSE (2016–2024) deve ser r ≥ 0,82.

Balanceamento automatizado
Diagnóstico de Estratégia Dominante e Espiral da Morte: Evoluir bots_balanceamento.py para registrar 3 métricas obrigatórias a cada simulação:

Índice de Estratégia Dominante: se qualquer perfil de bot atingir taxa de vitória > 65%, disparar falha no CI de balanceamento.

Detector de Espiral da Morte: identificar se o jogador fica com caixa < 0 E base_congresso < 25% E aprovacao < 15% antes do mês 24 sem nenhuma ação disponível no catálogo capaz de recuperar +5 pontos em 6 meses.

Detector de Turnos Mortos: contabilizar turnos em que nenhum indicador variou mais que 0,2 pp e nenhum evento ocorreu; a meta é < 10% dos turnos.

Aleatoriedade e justiça
RNG Determinístico por Seed com Telegrafia Prévia: Toda partida usa um gerador pseudoaleatório com seed explícita (seed salva no estado), garantindo reprodutibilidade total. Para evitar sensação de injustiça, crises graves nunca explodem sem aviso: 1 turno antes, surge um sinal fraco na imprensa ou redes (ex.: "Reservatórios do Sudeste atingem nível crítico"), dando ao jogador uma janela de ação preventiva que reduz o dano em 50%.

Desempenho e escala (~70s -> <5s)
Causas prováveis dos 70s em 48 meses: Recálculo completo dos 5.570 municípios em territory.py a cada avanço de dia/semana e serialização repetida de estados gigantes no SQLite (db.py).

Plano de refatoração:

Atualizar indicadores municipais em lote vetorizado (NumPy ou arrays planos) apenas na virada de mês, usando interpolação leve no front para semanas.

Separar career.py (2.006 linhas) por responsabilidade sem alterar assinaturas públicas das rotas em main.py, usando uma fachada (facade) temporária durante a migração para manter os 366 testes verdes a cada commit.

4. Tudo o Mais Até 9,5
Interface e fluxo: Unificar ações do turno na Mesa de Despacho; reduzir a navegação primária de 15+ itens para 5 pilares (Despacho, Política & Congresso, Economia & Contas, País & Obras, Imprensa & Redes). Critério de aceite: Todas as funções atuais acessíveis em ≤ 2 cliques a partir do menu principal.

Onboarding: Criar modo "Primeiros 100 Dias" (Tutorial Jogável Guiado) pré-carregado no botão principal do StartMenu.jsx, ensinando em 5 turnos guiados: nomear ministro, aprovar medida, responder crise e ler pesquisa. Critério de aceite: Taxa de conclusão do tutorial ≥ 85% em testes com jogadores novos.

Tom e humor: Contratar ou dedicar sprint exclusivo de redação humorística para reescrever os 300 textos mais frequentes (event_templates.py, social_feed.py, interviews.py), inspirados no jornalismo político brasileiro e na crônica de costumes. Critério de aceite: Avaliação média de "humor e personalidade" ≥ 4,5/5 em pesquisa pós-jogo com 20 testadores.

Volume e qualidade de conteúdo: Expandir o banco de eventos para 300+ ocorrências únicas com variações condicionais por região, cargo e ideologia. Critério de aceite: < 5% de eventos repetidos em 10 mandatos completos.

Arte e áudio: Finalizar as 53 ilustrações em docs/IMAGENS_RESTANTES.md e implementar trilha sonora adaptativa (calma na rotina, tensa em CPI/crise, festiva na apuração) + efeitos sonoros de interface. Critério de aceite: 100% das cartas com arte final e mixer de áudio funcional.

Acessibilidade: Garantir contraste mínimo 4.5:1 em todos os badges de partido e gráficos, suporte completo a leitores de tela (aria-live na apuração e notificações) e escalonamento de fonte sem quebra de layout. Critério de aceite: Zero erros críticos no axe-core em todas as 15 telas.

Desempenho no celular: Transformar a barra lateral em menu inferior (bottom bar) em viewports < 768px, adaptar tabelas largas (orcamento, congresso) para cards empilháveis e garantir alvos de toque ≥ 44x44px. Critério de aceite: Playtest completo de 1 campanha municipal em smartphone sem scroll horizontal ou texto truncado.

Localização: Embora o jogo seja profundamente brasileiro, preparar arquitetura i18n (pt-BR nativo + en com glossário explicativo de termos como Centrão, Medida Provisória, LRF) caso vise Steam global. Critério de aceite: 100% das strings de UI extraídas para dicionários JSON.

Segurança e privacidade: Remover scripts de envio de credenciais (deploy/oracle/enviar-chave-gemini.ps1) da árvore pública do jogo, aplicar rate limiting nas rotas de IA em main.py e anonimizar logs. Critério de aceite: Zero secrets ou scripts de credencial no repositório de aplicação; rate limit testado contra abuso de tokens.

Jurídico: Substituir nomes reais de parlamentares e candidatos nas partidas ativas por nomes fictícios (mantendo apenas siglas partidárias e dados agregados históricos com fonte citada), além de exibir disclaimer claro na tela inicial. Critério de aceite: Revisão jurídica preventiva aprovada; zero nomes de pessoas físicas vivas gerados em partidas.

Publicação em loja e suporte: Empacotar build desktop via Tauri/Electron (para Steam/Itch.io) além da versão Web PWA, com botão in-game "Reportar Bug / Sugerir Sátira" enviando snapshot anonimizado do turno. Critério de aceite: Build instalável rodando offline (com fallback local de IA) em Windows/Linux/macOS.

Métricas de produto e playtest: Instrumentar funil anônimo (início de partida -> fim de campanha -> mês 12 -> mês 24 -> mês 48 -> motivo de abandono) e rodar ciclo estruturado de playtest humano com 30 jogadores antes do lançamento. Critério de aceite: Retenção até o fim do 1º mandato ≥ 40% entre jogadores que concluem o tutorial.

5. Plano Até 9,5 (Marcos)
Marco M1 — Fundação Sólida, Coerência e Rapidez (Semanas 1–3)

Objetivo: Eliminar contradições numéricas, fatiar monolitos e fazer o motor rodar rápido.

Entregas: Fonte única de verdade para indicadores (2.1); decomposição real em drivers.py (2.2); anonimização dos 594 parlamentares (10.1); quebra de career.py e App.jsx (11.1); otimização de tick para < 5s (11.2).

Portão de passagem: 366+ testes verdes, zero divergência numérica entre telas, mandato de 48 meses simulado em ≤ 5s.

O que cortar: Qualquer nova mecânica política ou visual neste marco.

Marco M2 — Fluxo Único, Onboarding e Sátira Viva (Semanas 4–6)

Objetivo: Tornar o jogo imediatamente compreensível, divertido de ler e fluido nos primeiros 15 minutos.

Entregas: Mesa de Despacho Única (1.1); unificação do loop de campanha (1.2); menu de 5 pilares + badges (1.3); reescrita satírica dos eventos e povoamento obrigatório das redes (6.1, 6.2); cenário tutorial "100 Dias" (Onboarding).

Portão de passagem: 9/10 testadores novos entendem o que fazer em < 2 min sem ajuda; zero telas vazias de imprensa/redes após o turno 1.

O que cortar: Modo multiplayer (docs/MULTIPLAYER_ARQUITETURA.md) e editor de cenários.

Marco M3 — Profundidade Institucional e Eleitoral (Semanas 7–10)

Objetivo: Levar política, eleições e economia ao nível de excelência (≥ 9,0 em todas as dimensões).

Entregas: Coalizões e lideranças de bloco (3.1); STF e judicialização ativa (3.2); coligações, tempo de TV negociável e 2º turno (4.1, 4.2); alavancas fiscais estruturais e LRF subnacional (5.1, 5.2); ativação controlada do narrator.py (7.1).

Portão de passagem: Nenhuma dimensão abaixo de 9,0; calibração histórica aprovada e 500 partidas de bots sem estratégia dominante (>65%) ou espiral da morte.

O que cortar: Diplomacia multilateral complexa e cenários históricos secundários.

Marco M4 — Polimento 9,5, Arte, Áudio e Lançamento (Semanas 11–14)

Objetivo: Fechar todas as lacunas de acabamento, jurídico, mobile e publicação para atingir ≥ 9,5 global.

Entregas: Conclusão das 53 artes + paisagem sonora Web Audio (9.1, 9.2); expansão para 300+ eventos em arco (6.3); responsividade mobile + acessibilidade WCAG AA (12.1); pacote Steam/Web PWA + telemetria + playtest com 30 humanos.

Portão de passagem: Todas as 12 dimensões avaliadas em ≥ 9,5; retenção de mandato completo ≥ 40% no playtest final; zero bloqueios jurídicos ou de segurança.

6. Ideias Novas (Inéditas, Fora da Seção 7 do Briefing)
Voto de Cabresto Digital (Disparo em Massa no ZapZap): Permitir contratar "agências de comunicação informal" na campanha para impulsionar boatos segmentados por bairro/região; dá ganho rápido de intenção de voto, mas aumenta o risco de cassação da chapa pelo TSE após a eleição (electoral_integrity.py). Sobe: Motor eleitoral e Sátira | Esforço: M | Risco: Baixo.

Sabatina no Senado para Indicações ao STF e BC: Quando o jogador indica um nome em GovernmentAppointments.jsx, abrir uma mini-cena de sabatina na CCJ onde senadores da oposição fazem 3 perguntas-armadilha sobre declarações passadas do indicado. Sobe: Profundidade política | Esforço: M | Risco: Baixo.

Orçamento Secreto / Emendas de Relator ("RP-9"): Criar uma rubrica opaca no orçamento que compra votos difíceis no Congresso com o dobro da eficiência de emendas comuns, mas eleva silenciosamente o medidor de escândalo e atrai investigação do TCU/STF. Sobe: Profundidade política e Economia | Esforço: M | Risco: Baixo.

Boletim Focus Semanal Interativo: Toda segunda-feira de manhã, exibir um card compacto com as expectativas do mercado para PIB, IPCA, Câmbio e Selic; contrariar repetidamente o consenso do Focus encarece a rolagem da dívida pública (fiscal.py). Sobe: Economia e mercado | Esforço: P | Risco: Baixo.

Conflito de Agenda: Brasília vs. Base Eleitoral: Obrigar o jogador a dividir seus dias entre despachar no gabinete e viajar para inaugurar obras nos estados/bairros; ficar 6 meses sem pisar fora da capital derruba a aprovação regional mesmo com economia boa. Sobe: Clareza e Profundidade | Esforço: P | Risco: Baixo.

Delação Premiada como Mecânica de Contenção de Danos: Quando uma CPI (cpi.py) aperta um aliado, o jogador pode escolher entre blindá-lo (gastando capital político e STF) ou "jogar aos leões" (demitir e entregar, encerrando a crise rápido ao custo de perder a lealdade de todo o partido dele). Sobe: Eventos e narrativa | Esforço: M | Risco: Baixo.

Pesquisa Qualitativa (Grupo Focal Satírico): Gastar caixa de campanha para ouvir 4 eleitores-arquétipo fictícios (ex.: motorista de aplicativo, servidora pública, comerciante evangélico, estudante universitário) falando em linguagem coloquial o que realmente acharam do último discurso do jogador. Sobe: Motor eleitoral e Sátira | Esforço: P | Risco: Baixo.

Modo "Co-op de Chapa" (Presidente + Vice / Prefeito + Vice): Permitir que dois jogadores (ou jogador + IA com personalidade própria) dividam o mandato, onde o vice controla a articulação no Congresso enquanto o titular cuida do Executivo — e pode conspirar se a aprovação cair abaixo de 20%. Sobe: Balanceamento e rejogabilidade | Esforço: G | Risco: Médio.

Rádio Voz do Brasil / Pronunciamento em Cadeia Nacional: Mecânica de alto risco/alto retorno disponível a cada 90 dias: convocar cadeia nacional para defender uma reforma impopular, provocando "panelaço" (queda imediata se a aprovação estiver < 35%) ou virada de opinião se o discurso for bem avaliado. Sobe: Profundidade política e Áudio | Esforço: P | Risco: Baixo.

Linha do Tempo Comparativa Pós-Mandato ("O Brasil Real vs. Seu Brasil"): Na tela final (MandateReview.jsx), sobrepor os gráficos de IPCA, Dólar, PIB e Desemprego do mandato do jogador contra a curva histórica real do Brasil no mesmo período. Sobe: Dados reais e Rejogabilidade | Esforço: P | Risco: Baixo.

7. Riscos e Perguntas ao Criador
Os 5 Maiores Riscos para Atingir 9,5
Paralisia por Excesso de Escopo: Tentar manter 71 módulos crescendo simultaneamente sem podar telas redundantes fará o jogo parecer uma planilha gigantesca em vez de um jogo tenso e divertido.

Desconexão entre Dois Jogos no Mesmo Código: O modo Carreira Local (career.py) e o modo Presidência (state.py) correm o risco de virar dois jogos semi-acabados em vez de uma experiência contínua e coesa.

Passivo Jurídico com Nomes Reais: Exibir nomes reais de 594 parlamentares atuais (gov.md) em um jogo que simula corrupção, CPI e compra de apoio cria risco desnecessário de notificação extrajudicial ou bloqueio em lojas.

Dívida Técnica nos Monolitos: Continuar adicionando features em career.py (2.006 linhas) e App.jsx (69,9 KB) multiplicará bugs de regressão e manterá o tempo de simulação alto.

Fadiga de Leitura Sem Gancho Emocional: Se o humor satírico não for elevado drasticamente, o jogador médio abandonará a partida antes do 6º mês por cansaço cognitivo.

Perguntas e Recomendações para as Decisões em Aberto
Plataforma-alvo: Recomendação: Web PWA responsivo primeiro (para validação rápida com jogadores e custo zero de distribuição) seguido de Desktop Steam via Tauri (aproveitando o mesmo front React + backend Python empacotado, com IA local de fallback para modo offline).

Duração ideal de sessão: Recomendação: Mirar em 45 a 60 minutos por mandato completo (turnos mensais no governo com paradas apenas para crises/votações, e turnos semanais apenas nas 10 semanas finais de campanha), oferecendo um modo "Sessão Rápida (100 Dias)" de 15 minutos para descoberta.

Limite da sátira com cidades e dados reais: Recomendação: Manter 100% reais os municípios, estados, partidos (siglas/espectro), leis e séries macroeconômicas/eleitorais do IBGE/TSE, mas tornar 100% fictícios todos os nomes de pessoas físicas (candidatos, ministros, deputados, senadores, jornalistas).

Política de monetização: Recomendação: Jogo pago único (Buy-to-Play, faixa R$ 29,90–R$ 39,90 na Steam) com demo gratuita na Web (1 mandato municipal ou 100 dias na Presidência), evitando microtransações ou assinaturas que ferem a credibilidade de um simulador político.

Pergunta direta ao criador: Você aceita congelar a criação de novos subsistemas por 3 semanas para focar exclusivamente em refatorar os monolitos, unificar a Mesa de Despacho e reescrever os textos satíricos?

8. Backlog Legível por Máquina (Ordenado por Impacto / Esforço)
id	dimensão	título	critério de aceite	esforço	impacto (1 a 5)	depende de
B01	2. Coerência dos números	Unificar fonte de verdade do snapshot de indicadores	Teste test_coerencia_telas.py valida valores idênticos entre /api/game, /api/macro e /api/budget no mesmo tick	P	5	-
B02	6. Eventos, narrativa e sátira	Popular feed das redes sociais desde o turno 1	Zero ocorrências de "Nada nas redes ainda" após o primeiro avanço em governo ou campanha	P	5	-
B03	10. Dados reais e fidelidade	Anonimizar nomes dos 594 parlamentares ativos	Zero nomes de políticos vivos retornados por /api/game, mantendo partidos e UFs reais do TSE	P	5	-
B04	1. Clareza e fluxo	Adicionar badges de urgência e ocultar abas inativas por cargo	Candidato a prefeito não vê abas federais; pendências com prazo ≤ 7d exibem contador vermelho	P	4	-
B05	7. Uso da IA	Exibir cartão transparente da leitura semântica do discurso	SpeechReading.jsx mostra temas, tom e promessas antes de consolidar o cálculo do motor	P	4	-
B06	7. Uso da IA	Implementar rate limiting e remover scripts de chave do repo	Zero scripts de credencial na árvore principal; rotas de IA limitadas a 30 req/min por sessão	P	4	-
B07	5. Economia e mercado	Criar Boletim Focus semanal interativo	Card semanal exibe consenso de mercado e penaliza rolagem da dívida se contrariado repetidamente	P	4	B01
B08	8. Balanceamento e rejogabilidade	Criar modo "Sessão Rápida: Primeiros 100 Dias" no menu inicial	Botão principal no StartMenu.jsx inicia cenário jogável de 15 minutos sem configuração prévia	P	4	-
B09	6. Eventos, narrativa e sátira	Implementar memória de promessas de campanha no mandato	Motor registra 3 promessas da campanha e dispara cobrança na imprensa nos meses 18 e 42	P	4	-
B10	4. Motor eleitoral	Adicionar Pesquisa Qualitativa (grupo focal satírico)	Ação de campanha exibe reação coloquial de 4 arquétipos de eleitores ao último discurso	P	3	B02
B11	3. Profundidade política	Implementar Cadeia Nacional de Rádio e TV a cada 90 dias	Ação disponível trimestralmente com risco de panelaço se aprovação < 35% ou bônus se discurso > 8/10	P	3	B05
B12	8. Balanceamento e rejogabilidade	Exibir gráfico comparativo "Brasil Real vs. Seu Brasil" no fim	MandateReview.jsx plota séries históricas reais ao lado dos resultados do jogador	P	3	B01
B13	1. Clareza e fluxo	Criar Mesa de Despacho Única (Inbox do Turno)	≥ 90% dos testadores novos executam ação e avançam turno em < 120s sem tutorial externo	M	5	B04
B14	1. Clareza e fluxo	Unificar ação semanal de campanha na tela principal	Ação de campanha executada em ≤ 2 cliques sem sair de OverviewPanel.jsx	M	5	B13
B15	2. Coerência dos números	Substituir texto genérico em drivers.py por causas reais	Soma dos drivers explica ≥ 95% da variação do indicador sem rótulos genéricos	M	5	B01
B16	5. Economia e mercado	Substituir micro-corte de viagens por alavancas fiscais reais	Contingenciamento, subsídios e meta primária movem resultado fiscal em 0,2%–1,5% do PIB	M	5	B01
B17	4. Motor eleitoral	Implementar 2º turno e transferência de votos executivos	Eleições majoritárias sem maioria absoluta disparam 2º turno com negociação de apoio	M	5	-
B18	11. Qualidade técnica	Otimizar simulação de 48 meses de ~70s para ≤ 5s	Benchmark automatizado conclui 48 meses em ≤ 5,0 segundos	M	5	-
B19	8. Balanceamento e rejogabilidade	Expandir bots de balanceamento para 500 partidas e 5 arquétipos	Nenhum arquétipo vence > 65% ou < 15%; passividade total perde em ≥ 95%	M	5	B16
B20	7. Uso da IA	Ligar narrator.py com cache por hash e teto de custo	Custo ≤ US$ 0,03/mandato; latência p95 < 1,5s; 100% fallback determinístico	M	4	B06
B21	3. Profundidade política	Implementar judicialização ativa no STF para medidas de alto risco	100% das ações com risco jurídico alto em powers_catalog.py geram análise liminar em ≤ 15d	M	4	-
B22	3. Profundidade política	Conectar governadores dos 5 maiores estados ao jogo federal	Aprovação de reformas no Congresso varia até ±12% conforme alinhamento estadual	M	4	-
B23	4. Motor eleitoral	Implementar coligações pré-eleitorais e negociação de tempo de TV	Alianças partidárias somam tempo de TV em tv_time.py e reduzem custo de mídia	M	4	-
B24	4. Motor eleitoral	Criar debate interativo em 4 blocos com direito de resposta	Debate altera intenção de voto em até ±4,5 pp conforme nota de discurso e tema	M	4	B05
B25	5. Economia e mercado	Conectar LRF subnacional a bloqueio de repasses para prefeitos	Estourar 54% da RCL com folha dispara alerta do TCE e trava convênios federais	M	4	-
B26	5. Economia e mercado	Adicionar defasagem (lag 3–9 meses) entre juros/gasto e inflação	Expansão fiscal/juros baixos gera bônus imediato e cobra inflação nos trimestres seguintes	M	4	B16
B27	3. Profundidade política	Criar mecânica de Orçamento Secreto (emendas opacas)	Compra votos com 2x eficiência mas eleva risco de investigação TCU/STF	M	4	-
B28	3. Profundidade política	Implementar Sabatina no Senado para indicados ao STF e BC	Mini-cena de 3 perguntas antes da votação de confirmação no Senado	M	4	-
B29	6. Eventos, narrativa e sátira	Criar mecânica de delação premiada para conter CPIs	Demitir aliado investigado encerra CPI mas derruba lealdade do partido dele	M	4	-
B30	9. Visual e áudio	Implementar paisagem sonora procedural/discreta via Web Audio	Sons de carimbo, plenário, pregão e urna eletrônica com mute persistente (< 3 MB)	M	4	-
B31	9. Visual e áudio	Gerar e integrar as 53 ilustrações editoriais pendentes	Zero placeholders genéricos nas cartas de evento e telas principais	M	4	-
B32	8. Balanceamento e rejogabilidade	Curar 8 cenários históricos assimétricos jogáveis	historical_play.py oferece 8 desafios com condições próprias de vitória	M	4	B08
B33	4. Motor eleitoral	Adicionar disparo em massa no ZapZap com risco de cassação	Impulsiona votos na reta final mas eleva chance de ação no TSE pós-eleição	M	3	B02
B34	3. Profundidade política	Criar conflito de agenda entre Brasília e viagens às bases	Ausência regional por > 6 meses derruba aprovação nos estados não visitados	M	3	B22
B35	10. Dados reais e fidelidade	Criar script de calibração macro com séries históricas 2003–2026	Trajetórias simuladas de IPCA, Selic e Dívida/PIB dentro das bandas históricas	M	4	B26
B36	10. Dados reais e fidelidade	Validar correlação eleitoral baseline com dados do TSE	Correlação de Pearson r ≥ 0,82 entre baseline simulado e resultados oficiais TSE	M	4	B17
B37	6. Eventos, narrativa e sátira	Implementar sinais fracos 1 turno antes de crises graves	Crises severas exibem alerta preventivo 1 turno antes permitindo mitigação de 50%	M	4	-
B38	12. Pronto para publicar	Instrumentar funil anônimo de telemetria e botão de reporte	Dashboard captura retenção por mês e permite enviar snapshot anonimizado de bug	M	4	B06
B39	12. Pronto para publicar	Empacotar versão Desktop offline/híbrida via Tauri	Instalador Windows/Linux funcional com fallback local de IA sem internet	M	3	B18
B40	1. Clareza e fluxo	Implementar Tutorial Guiado Interativo "100 Dias"	≥ 85% dos novos jogadores concluem os 5 turnos guiados sem abandono	M	5	B13
B41	3. Profundidade política	Implementar sistema de coalizões e lideranças de bloco	Partidos negociam em bloco; deixar > 50% de pastas vagas derruba governabilidade em ≥ 15 pts	G	5	B13
B42	6. Eventos, narrativa e sátira	Reescrever 300 textos base para tom satírico brasileiro	Zero ocorrências de linguagem técnica "simulada" na narrativa; nota ≥ 4,5/5 em humor	G	5	B02
B43	6. Eventos, narrativa e sátira	Expandir biblioteca para 300+ eventos em arcos de 3–5 episódios	Taxa de repetição < 5% em 10 mandatos consecutivos de 48 meses	G	5	B42
B44	11. Qualidade técnica	Fatiar monolitos career.py, App.jsx e CareerPanel.jsx	Nenhum arquivo > 450 linhas; 366+ testes passando sem regressão	G	5	-
B45	12. Pronto para publicar	Adequar responsividade mobile, WCAG 2.1 AA e pacote LGPD	Lighthouse Accessibility ≥ 95; zero overflow em 375px; Termos/Privacidade publicados	G	5	B13
B46	3. Profundidade política	Criar crises de segurança pública (greve PM, GLO, sistema prisional)	Eventos de segurança exigem coordenação federativa e afetam aprovação urbana	M	3	B22
B47	5. Economia e mercado	Conectar acordos diplomáticos à balança comercial e câmbio	Missões comerciais bem-sucedidas em diplomacy.py impactam fluxo cambial em macro.py	M	3	B01
B48	3. Profundidade política	Implementar derrubada de veto presidencial com contagem regressiva	Vetos em congress_agenda.py abrem janela de negociação antes da sessão conjunta	P	3	B41
B49	3. Profundidade política	Criar obstrução regimental e pedido de vista nas comissões	Oposição pode atrasar projetos em 2 semanas; governo pode pedir urgência urgentíssima	P	3	B41
B50	3. Profundidade política	Implementar fogo amigo de ministros ambiciosos	Ministros com alta popularidade vazam notas ou lançam candidatura própria se contrariados	M	3	B41
B51	6. Eventos, narrativa e sátira	Criar gerador de Página da Wikipédia Fictícia ao fim do mandato	MandateReview.jsx gera biografia satírica com apelido histórico baseado nos feitos	P	3	B12
B52	8. Balanceamento e rejogabilidade	Implementar Desafio Semanal com seed fixa e ranking	Jogadores disputam o mesmo cenário semanal e comparam pontuação no Placar da História	M	3	B18
B53	12. Pronto para publicar	Preparar arquitetura i18n (pt-BR + glossário institucional en)	100% das strings de interface extraídas para arquivos de tradução	M	3	B44
B54	12. Pronto para publicar	Executar ciclo de playtest estruturado com 30 jogadores humanos	Retenção de mandato completo ≥ 40% e zero bugs bloqueadores reportados	M	5	B40
B55	2. Coerência dos números	Criar auditoria visual de tooltips em todos os indicadores	100% dos números na UI exibem fórmula resumida e variação acumulada no mandato	P	4	B15
B56	5. Economia e mercado	Implementar greves setoriais por arrocho salarial ou inflação	Inflação > 8% ou congelamento salarial dispara greves que reduzem PIB e aprovação	M	4	B26
B57	6. Eventos, narrativa e sátira	Criar 3 versões de manchete por decisão (Governista, Oposição, Tabloide)	Cada decisão relevante gera 3 manchetes com vieses distintos em NewsPanel.jsx	M	4	B20
B58	7. Uso da IA	Alimentar question_ai.py com as últimas 3 decisões do jogador	Perguntas de entrevista cobram especificamente contradições recentes do mandato	P	4	B20
B59	8. Balanceamento e rejogabilidade	Implementar Modo Sobrevivência ("Impeachment Iminente")	Cenário inicia no mês 30 com 14% de aprovação e pedido de impeachment protocolado	P	3	B32
B60	11. Qualidade técnica	Adicionar testes de propriedade (Hypothesis) para invariantes do motor	Testes garantem que nenhum indicador sai de [0, 100] ou gera NaN em 10.000 ticks aleatórios	M	4	B44