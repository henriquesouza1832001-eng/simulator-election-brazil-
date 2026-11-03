# Mapa de telas e regras do Mandato

Este documento organiza o simulador por áreas de trabalho, inspirado na navegação ampla do PLANALTO, com regras e identidade próprias. A interface deve mostrar uma tarefa por vez: resumo curto, detalhes recolhidos e impactos explicados antes da confirmação.

## Mapa principal

| Área | Pergunta que responde | Telas internas |
| --- | --- | --- |
| **Painel** | O que exige atenção hoje? | Briefing do dia, seis indicadores escolhidos, crise prioritária e próxima decisão. |
| **Governo** | Como o Executivo está funcionando? | Gabinete e ministérios existentes, execução, agenda, promessas e coordenação federativa. |
| **País** | Como as pessoas e regiões estão? | Indicadores agrupados, mapa regional, grupos sociais, serviços, clima e segurança. |
| **Economia** | De onde vem e para onde vai o dinheiro? | Contas públicas, impostos simplificados, empresas, estatais, investimentos e obras. |
| **Diplomacia** | O que o Brasil negocia com outros países? | Países, visitas, cúpulas, acordos, compromissos e deslocamentos com duração. |
| **Campanha** | Como disputar o próximo cargo? | Plano, território, agenda, imprensa, debates, alianças, pesquisa, votação e transição. |
| **Instituições** | Quais são os limites e equilíbrios do poder? | Congresso, Justiça, eleições, órgãos de controle e estabilidade institucional. |
| **Arquivo** | O que já aconteceu e por quê? | Diário, medidas, notícias simuladas, promessas, votações e histórico de indicadores. |

O menu pode adaptar itens ao cargo. Uma prefeitura não mostra decisões federais como se fossem atribuição municipal; o presidente não administra diretamente serviços locais. O primeiro protótipo continua no cargo de presidente e expande para outras carreiras em fatias próprias.

## Estrutura curta de cada tela

1. **Contexto:** uma frase sobre a situação e a data.
2. **Decisão principal:** uma ação disponível e seus limites.
3. **Prévia:** custo, tempo consumido, afetados, efeito imediato e possível consequência futura.
4. **Confirmação:** registrar a escolha no motor Python.
5. **Retorno:** o que mudou, por qual regra e quando revisar.

Detalhes extensos ficam em páginas internas, acordeões ou histórico. A visão geral não repete toda a base de dados, todas as notícias e todos os formulários. O conteúdo narrativo identifica claramente ficção, dado importado e estimativa do jogo.

## Regras centrais do simulador

### Painéis e indicadores

- O painel inicial aceita até seis cartões escolhidos pelo jogador. A aba Indicadores reúne os demais dados em grupos recolhíveis para evitar uma tela única comprida.
- Os grupos cobrem economia e trabalho, contas públicas, apoio e governabilidade, instituições, serviços e investimento, diplomacia e regiões, população e qualidade de vida.
- As linhas de base de IDH, Gini, pobreza, expectativa de vida, mortalidade infantil, homicídios, saneamento, conclusão escolar e população são estimativas fictícias do cenário, não estatísticas oficiais.
- No avanço do calendário, os indicadores sociais mudam lentamente em resposta ao crescimento, desemprego e às entregas acumuladas de educação, saúde, segurança e infraestrutura.

### Calendário

- Um dia é a menor unidade comum. Avançar dias executa todos os eventos, entregas, compromissos e votações vencidos nesse intervalo.
- Ações têm duração própria: visita, obra, campanha e negociação consomem dias; medidas administrativas e projetos seguem cadências e prazos distintos.
- O calendário político continua durante campanha e viagem. A ausência não pausa crises, obras ou processos legislativos.
- O jogador pode avançar um dia, sete dias ou um mês; o motor para na data de um resultado eleitoral ou transição importante.
- Uma crise adiada deixa memória no estado. Seca, pressão de saúde, falha digital e questionamento de contrato podem reaparecer cerca de 90 dias depois; o jogo registra a decisão anterior e limita a cadeia a dois retornos.
- O sorteio mensal de crises usa a semente da partida para ser reproduzível, mas ajusta as probabilidades por estação, região, infraestrutura, integridade e capacidade de saúde; os resultados continuam variáveis entre partidas.
- Antes de responder a uma crise, cada opção apresenta custo, variação estimada no PIB e na aprovação, explicação imediata e consequência futura. O motor aplica os valores determinísticos da opção selecionada.
- **Posse:** uma partida nova começa com pronunciamento pendente. Após uma posse eleitoral, a exigência se repete. O jogador escreve entre 80 e 1.200 caracteres; o motor aplica uma rubrica reproduzível e não aceita outras ações mutáveis até a fala ser registrada. Saves antigos não recebem a exigência retroativamente.

### Campanha eleitoral — primeira regra jogável

- As eleições municipais simuladas ocorrem no primeiro domingo de outubro dos anos pares do ciclo municipal (2028, 2032...). As eleições estaduais e federais usam o primeiro domingo de outubro do ciclo geral (2026, 2030, 2034...).
- A campanha simulada abre 90 dias antes da eleição do cargo escolhido. Antes disso, a carreira fica em pré-campanha e mostra as datas de abertura e votação; atividades de campanha só ficam disponíveis na janela legal simulada.
- A posse ocorre em 1º de janeiro para cargos municipais, estaduais e legislativos, e em 5 de janeiro para a Presidência. O mandato dura quatro anos, ou oito para o Senado; a próxima eleição é marcada no ciclo correspondente.
- Na fase aberta, o jogador pode fazer uma atividade por intervalo de sete dias: comício, entrevista, debate ou encontro regional.
- Cada atividade tem custo de campanha separado do Tesouro, duração em dias, região e tema. Não se pode usar verba pública para pagar a campanha nesta regra inicial.
- Um discurso/resposta é avaliado por uma rubrica determinística: pertinência ao tema, proposta concreta, conexão humana, responsabilidade, clareza, promessas vagas e ataques pessoais. A nota e seus componentes ficam visíveis.
- O resultado afeta apoio regional e de grupos sociais. O cálculo eleitoral incorpora o apoio acumulado e uma variação reproduzível pela semente da partida.
- Vereador e deputado usam uma distribuição proporcional simplificada por D'Hondt entre legendas fictícias; a candidatura do jogador é o primeiro nome simulado da lista. Governador, prefeito, presidente e senador usam disputa majoritária simplificada.
- Fazer campanha avança o calendário e mantém o governo em funcionamento. A derrota não encerra o jogo: a transição continua até a posse, depois abre o percurso de carreira.
- A carreira política oferece uma rota inicial para vereador, prefeito, deputado estadual, deputado federal, senador, governador e presidente. O mesmo personagem conserva reputação e histórico ao disputar outro cargo após concluir a fase atual.
- Três canais sociais fictícios (grupos de mensagem, vídeo/imagem e debate público) diferem em alcance, público, custo e chance de viralização. O motor pode gerar adesão ou reação negativa; o texto não altera diretamente o resultado eleitoral.
- A passagem de mandato inclui gabinete fictício de ministérios catalogados e indicação ao STF sujeita a votação simulada no Senado. São sistemas iniciais, não uma representação completa dos processos institucionais.
- O modelo é uma abstração, não previsão eleitoral. A pré-campanha já respeita a data e a janela do cargo, mas ainda faltam atividades próprias de organização partidária, adversários com plataformas próprias, arrecadação detalhada, pesquisas públicas, propaganda, debates em vários turnos e magnitude de distritos reais para a apuração proporcional.

### Medidas, leis e decisões

- A interpretação de texto sugere tipo e intenção; o motor valida alçada, prazo, custo e regra antes de aplicar efeitos.
- **Fronteira canônica IA/motor:** o motor Python valida ações, altera o estado e calcula custos, probabilidades, efeitos e resultados. A IA classifica intenção, sugere rótulos e redige explicações; números do texto do jogador só entram após validação no servidor contra a proposta original. Saída numérica do modelo nunca é, por si só, uma regra ou um efeito. Ver pendência concreta de `fiscal_cost_bi` em [`VALIDACAO_CRUZADA_PROPOSTAS.md`](VALIDACAO_CRUZADA_PROPOSTAS.md).
- Medidas executivas têm intervalo de agenda. Projetos têm prazo e votação simulada; o envio não é aprovação.
- A tela apresenta custo/financiamento, grupos afetados, prazo, incerteza, efeitos agora e consequências em meses futuros.
- Toda decisão é registrada com data, parâmetros, resultado e origem. Prévia não aplicada e correção humana também têm registros próprios por jogador; saída automática não é rótulo de treino e avaliação de narrativa fica separada.

### Orçamento, serviços e obras

- Toda despesa tem uma fonte e pertence a um orçamento do ente correspondente.
- Remanejamentos identificam área de origem e destino; custos de moradia, viagens, investimento e obras entram na conta do governo.
- Obras mantêm modalidade, região, custo na contratação, correção de preços, fonte, cronograma, execução física, risco e manutenção.
- Eventos podem atrasar contratos, reduzir entrega, expor irregularidade ou exigir decisão; impactos persistem no tempo e no histórico.
- O jogador não cria ministérios por decisão de interface. A estrutura de ministérios vem de catálogo oficial datado e limites legais.

### Eventos, notícia e IA

- Regras do motor decidem gatilho, efeitos, duração, grupos afetados e semente. IA escreve narrativa/opções dentro desse resultado.
- Cada item exibe um selo: **simulado**, **histórico com fonte**, ou **dado público importado**.
- Uma inundação ou crise precisa alterar serviços, logística, orçamento e indicadores ao longo do tempo; não pode ser apenas uma escolha textual isolada.
- RAG recupera documentos com fonte e data. Não é treinamento: serve contexto. Correções confirmadas ajudam a avaliar e treinar interpretação; avaliação de narrativa fica em tarefa e dados separados. A integração do RAG ao fluxo narrativo ainda está pendente.

### Integridade eleitoral

- Cada atividade oferece, por padrão, condução dentro das regras. O jogador também pode escolher um atalho irregular abstrato e inteiramente simulado; o jogo não apresenta métodos reais de fraude ou abuso.
- O motor calcula a chance de detecção a partir da integridade, da resistência institucional, da confiança e da independência judicial registrada na partida.
- Uma irregularidade não detectada pode dar um ganho pequeno e imediato, mas deixa exposição para revisão eleitoral. Se detectada, derruba apoio e confiança. A apuração final aplica a penalidade e sorteia uma revisão adicional com semente reproduzível.
- A escolha, o risco mostrado antes dela e o desfecho ficam no histórico. O governo continua administrando durante a eleição.

### Dificuldades

Os cinco modos usam as mesmas regras centrais, com parâmetros diferentes para frequência e gravidade de crises, volatilidade econômica, pressão eleitoral e flexibilidade da coalizão em votações e indicações. Tranquilo dá mais margem para acordos; Normal usa o ponto de referência; Difícil e Complicado elevam a resistência e a pressão; Realismo Puro combina volatilidade econômica maior com resistência política intermediária. Eventos e números continuam sendo simulações fictícias: este modo ainda não é calibrado por uma série histórica validada.

## Sequência de construção

1. **Campanha eleitoral:** agenda semanal, rubrica de fala, apoio territorial e apuração conectada ao calendário. Esta fatia está iniciada.
2. **Painel/indicadores:** catálogo único, fontes, histórico e explicação do que moveu cada valor.
3. **Governo e orçamento:** gabinete funcional, orçamento por origem/destino e consequências de programas/obras.
4. **Carreira:** candidatura, eleição, transição, posse com pronunciamento, mandato simplificado, oposição e continuidade já estão iniciados; aprofundar poderes e orçamento conforme o cargo.
5. **Legislativo e instituições:** bancadas, comissões, votações, nomeações e controles com competências próprias.
6. **Diplomacia, redes e imprensa:** mais países, agenda física, canais simulados e reações com efeitos persistentes.
7. **Dados e RAG:** importadores oficiais, proveniência por item, recuperação de fontes e avaliação do interpretador.

Cada etapa é uma fatia completa de regra Python, estado salvo, endpoint, tela orientada e atualização desta especificação. Não se deve redesenhar tudo numa única página longa.
