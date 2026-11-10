# Dossiê de exploração do PLANALTO

Objetivo: registrar o funcionamento observado no jogo para orientar o design do simulador Mandato. A exploração usa uma partida fictícia de campanha presidencial no modo Normal; nomes, falas, pesquisas e eventos são conteúdo satírico do jogo, não afirmações sobre pessoas reais. As capturas REA são evidência da interface e do texto que ela apresentou, não validação factual.

## Sessão e estado atual

- Site explorado: `https://planalto.fun/jogar`.
- Navegação: Chrome visível via CDP local `127.0.0.1:9333`; REA observa passivamente a origem autorizada e grava estrutura/acessibilidade. Cliques, digitação e escolhas são feitos na sessão do navegador.
- Campanha: presidencial, eleição simulada de 2026, 13 semanas, modo Normal.
- Personagem: Augusto Cury (AVANTE), selecionado da lista pronta. Foi uma seleção acidental causada pela posição dos cartões; mantida para preservar a partida.
- Candidato em 6,1% na semana 3; a pesquisa agregada só foi renovada na semana 5, quando passou a 8,1% (+2,0). Lula aparece com 36,8% e Flávio Bolsonaro com 29,6% na abertura da semana 6.
- Semana 6: choque cambial de 6%, primeiro debate na Band realizado; resultado do debate 61 (“empate”, favorece quem lidera), +1,8 momentum. A semana foi fechada com visita à Expointer no RS, descanso e live sobre o câmbio.
- Semana 7: calendário trouxe Sete de Setembro no DF e Grito dos Excluídos em SP; denúncia de contratos envolvendo gráfica ligada a aliado foi respondida com abertura de contas e chamada à imprensa. Visita ao Grito em São Paulo rendeu +5,6 pontos de intenção somados no país.
- Aliados aceitos: Fausto Pinato (SP), Ratinho Júnior (PR), Raquel Lyra (PE), Helder Barbalho (PA). Cada apoio pede um ministério para o partido; obrigações registradas até março do primeiro ano. O jogo também mostra apoio acumulado de +1,88 ponto por semana.

## Ciclo da campanha observado

1. A semana abre com notícia/evento, manchete, agenda local e às vezes sabatina ou debate obrigatório.
2. O jogador pode escolher uma resposta ao evento antes de fechar a agenda.
3. Existem três ações semanais de campanha, além de compromissos extraordinários (sabatina/debate). A agenda bloqueia o fechamento enquanto faltar resposta obrigatória ou ação.
4. Ações gastam caixa e energia; deslocamento pode acrescentar custo de energia. O sistema mostra efeitos imediatos, grupos atingidos e efeitos persistentes.
5. Na virada, chegam novos fatos, apoios, doações, adesões e mudanças nas intenções. As pesquisas públicas podem estar defasadas; pesquisa interna estadual pode ser comprada.
6. Em tela de encerramento, o jogo apresenta uma nota, diagnóstico de retórica, reação por grupos e um trecho de debate que ocorreu sem o jogador.

## Mecânicas e dados já observados

### Calendário, campanha e pesquisa

- A campanha presidencial dura 13 semanas e tem primeiro turno em 4 de outubro. A tela mostra intenção nacional, faixa entre institutos, energia, caixa, tempo de TV, estados com estrutura e variação de grupos.
- O agregado inicial na semana 2 era Lula 39,1%, Flávio Bolsonaro 25,7%, Renan Santos 7,9%, Augusto Cury 6,1%, Zema 4,2% e Caiado 3,5%; as leituras públicas vinham de dois institutos.
- Na semana 5, a média mudou para Cury 8,1% (intervalo exibido 5,4–10,4), Lula 36,8% e Flávio 29,6%. A UI atribuiu ao jogador +2,0 p.p. na semana e registrou manchete de alta.
- A pesquisa interna estadual custa R$ 0,4 mi. Em São Paulo: semana 3, 9,1% e mobilização +0,6; semana 5, 12,6% e mobilização +2,0. A pesquisa pública do AtlasIntel, semana 2, mostrava 10,4% ±2,5.
- A sala de guerra apresenta probabilidade de vitória, simulação de segundo turno, margens estaduais e potencial nacional estimado por deslocamento de voto. Na semana 5, todas as probabilidades de vitória ainda eram 0%; Cury aparecia atrás de Lula por 17,1 pontos no confronto direto (26,1 contra 43,2). São Paulo era o maior potencial estimado (+0,87 nacional para deslocar 4 pontos), seguido por MG (+0,40), RJ (+0,32), RS (+0,29), PA (+0,27), PR (+0,23), GO (+0,17) e SC (+0,15).

### Ações de campanha e recursos

- Caminhada em São Paulo: R$ 0,4 mi, energia −10, +1,8 p.p. nacional.
- Contratação de cabos eleitorais no Paraná: R$ 2,5 mi, estrutura +9 e +0,8 p.p. nacional recorrente até a eleição. A tentativa de mudar a seleção para SP não foi aplicada; a ação ficou em PR.
- Comício em São Paulo na semana 4: resultado informado de +6,5 p.p. nacional, +6,2 p.p. estadual, R$ 2 mi e energia −15, mais 2 de viagem. A lista semanal exibiu +7,2 p.p.; discrepância entre resultado e resumo.
- Culto em São Paulo: +2,4 p.p. nacional; efeito com religiosos e reação negativa de parte dos jovens. O candidato tinha traço de personagem que dobrava rendimento de culto e missa.
- Festa do Peão de Barretos (SP): +5,7 p.p. nacional; o jogo diz que agronegócio exportador e São Paulo perceberam a visita.
- Reunião com profissionais de saúde: simpatia +2,7, descrita como conversão gradual em voto ao longo das semanas.
- Entrevista Flow Podcast: total 63, respostas 58/73/58, −12 energia. O retorno foi “saiu maior do que entrou”.
- Ao fim da semana 5, energia 47/100 e caixa R$ 25,9 mi; após a virada, semana 6 mostrou energia 59/100 e caixa R$ 27,8 mi, com R$ 2,8 mi em doações.

### Redes sociais

- As redes simuladas têm clipes com visualizações, conteúdo, semana de origem e opção de impulsionar por R$ 0,5 mi em um estado por duas semanas.
- O clipe da live da semana 5 passou de 1,4 mi de alcance orgânico para “impulsionado em São Paulo”. O editor permitiu selecionar estado; não ofereceu segmentação por grupo nessa tela.
- Clipes observados: “drone romântico” (9,5 mi, impulsionado em SP), “a outra vida” do Flow (5,6 mi), live “o drone” (1,4 mi antes do impulso). A tela duplicava os mesmos itens em “Os que estão rodando” e “Todos os vivos”.
- A live foi escrita com 280 caracteres. O texto reconhecia erro ao chamar o drone de detalhe, prometia integração com botão de emergência e atendimento, com custo e privacidade. Resultado: alcance 1,4 mi, +0,6 momentum e seis reações simuladas; várias apoiavam a intenção, mas cobravam rede de atendimento.

### Horário eleitoral e promessas

- O bloco de TV distribui tempo entre biografia, proposta, ataque, depoimento e jingle; pode selecionar alcance e alvo. Ataques aumentam rejeição e dão direito de resposta.
- A chapa tinha 35 segundos/dia. A explicação declarava 12 segundos iguais + 24 proporcionais usando 5 deputados do AVANTE entre 282, mas o total mostrado era 35; componentes e total não fecham.
- O programa registrado traz três promessas: privatizar Correios (até dezembro do 2º ano), privatizar Embrapa (até dezembro do 2º ano) e restabelecer teto de gastos (até dezembro do 1º ano). A tela estima R$ 2,6 bi/ano de prejuízo dos Correios e R$ 4 bi/ano da Embrapa. Se não cumprir, mercado e empresariado −5 de aprovação; cada promessa de ministério também afeta relação partidária em −20.

### Apoios, coalizões e notícias

- Apoios de governadores e parlamentares oferecem ganho territorial semanal, pedem uma pasta ao partido e têm prazo para resposta. Recusar pode levar o aliado a um rival, com chance indicada de 75%.
- Semana 5: Helder Barbalho aceito (MDB, Pará, +0,46/semana); Ibaneis Rocha recusado (MDB, DF, mesma taxa). A tela registra que Ibaneis depois foi para Lula.
- Semana 6 ofereceu Paulo Dantas (MDB, AL, +0,40/semana) e Wilson Lima (UNIÃO, AM, +0,40/semana); ainda não respondido.
- Entre semanas, o jogo encadeia fatos: governadores sobem em palanques, candidatos anunciam vice, aliados fecham com concorrentes, eventos alteram pauta e doações reagem às pesquisas. Exemplo: notícia fictícia sobre aliado de Flávio preso em operação sobre emendas e fotografia conjunta circulando nacionalmente.
- A tela “Por baixo do pano” existe junto ao palanque, com indicador de risco e gasto de segurança. Apenas observada; nenhuma opção clandestina foi executada.

## Primeiro debate nacional: Band, semana 6

O debate tem etapas sequenciais com cronômetros e limite de 600 caracteres: preparação; pergunta da mediação (90 s); pergunta de adversário e réplica; escolha de adversário e flanco para pergunta própria (60 s); considerações finais (60 s); placar e comentários; trecho de debate ocorrido sem o jogador.

- Lula, Flávio Bolsonaro e Zema faltaram; a banca tinha nove pessoas. A tela atribuiu mediação à Band.
- A mediação perguntou sobre venda dos Correios, dólar, alianças com Ibaneis/Helder e prioridade entre drone e economia. Resposta fiscal técnica: 58. O diagnóstico reclamou falta de efeito imediato na conta doméstica.
- Renan Santos questionou se o drone era só viral e se o candidato tinha experiência. Resposta: 58 (“passou”, sem frase memorável).
- Tréplica sobre suposta censura do TSE e Correios vendidos “a preço de banana”. Resposta esclareceu que não foram vendidos, pediu avaliação/leilão transparentes e respeito a recurso legal. Nota 58; diagnóstico considerou resposta seca/técnica.
- Pergunta do jogador foi direcionada a Renan sobre “as dezesseis contas não declaradas”. A cobrança pediu explicação de gastos e publicação de documentos para auditoria. Nota 75; +2 para classe média, jovens e empresariado; retorno elogiou cobrança direta e transparência.
- Consideração final sobre custo de vida, serviço universal e segurança de mulheres: 58; grupos classe média, periferia, jovens e evangélicos +1. Diagnóstico pediu exemplo cotidiano ou frase emocional memorável.
- Placar final: 61, empate que favorece quem lidera, +1,8 momentum. O jogo disse que 4 de 4 institutos publicariam vitória do candidato, apesar da nota “empate”. Guardar como possível divergência entre score/placar/manchete.
- No trecho paralelo, Rui Costa Pimenta venceu Edmilson Costa em discussão sobre dívida, recompra da Eletrobras e soberania.

## Semana 6: Expointer, redes e fechamento

- A visita à Expointer no RS custou 10 de energia e R$ 0,5 mi de caixa; resultado +4,8 pontos de intenção somados no país, incorporados à média quando a semana fechou.
- Descansar recuperou 25 de energia. A live sobre o câmbio alcançou 2,8 milhões de pessoas por tratar do assunto da semana e somou +0,3 de momentum; seis perfis responderam com apoio, crítica ou neutralidade.
- Ao fechar a semana, a média apresentada ficou em Cury 8,1%, caixa R$ 30,1 mi e energia 71. A campanha organiza cada semana em três ações.

## Semana 7: evento, denúncia e visita

- Dois eventos coincidiram no calendário: Sete de Setembro em Brasília, com benefício ao grupo Militar, e Grito dos Excluídos em São Paulo, com benefício à Periferia e trabalho informal.
- Uma denúncia sobre contratos da campanha apresentou fatos não comprovados e três respostas: abrir contas e chamar a imprensa; atacar a revista; ou responder com nota jurídica. Escolher transparência encerrou a tela da denúncia e abriu a agenda, mas sem mostrar uma resolução narrativa ou efeito numérico claro. Feedback insuficiente/ambíguo.
- “Visitar obra ou tragédia” abre uma lista de UFs. Cada cartão antecipa apoio estadual, eleitorado, custo de deslocamento e energia; a opção atual apareceu marcada como “você está aqui”. São Paulo indicava 44,4 mi de eleitores e cobrava 9 de energia e R$ 0,5 mi de viagem, além dos 10 de energia-base da ação.
- São Paulo foi selecionado para coincidir com o Grito dos Excluídos. Resultado: “Periferia e trabalho informal viu, e São Paulo anotou”; +5,6 pontos de intenção somados pelo país, para entrar na média ao fechar a semana. A recompensa está vinculada ao calendário e à região, sem especificar qual obra ou interação ocorreu.
- Apoios disponíveis no início da semana: Tarcísio de Freitas (Republicanos/SP), +0,40 p.p. por semana e pedido de ministério; Renzo Braz (PP/MG), +0,23 p.p. por semana e pedido de ministério. Recusar Tarcísio informa 75% de chance de adesão a Flávio Bolsonaro. Decisões pendentes.

## Semana 7: conclusão da agenda e apoios

- A live com o tema “o dossiê: a denúncia” usou tom “falando como gente” e alcançou 2,8 mi por ser o assunto da semana. A reescrita da fala enfatizou abrir as contas; seis perfis reagiram, incluindo crítica de Fábio Porchat à situação e apoio de Pablo Marçal, Galvão Bueno, Silas Malafaia, Craque Neto e Rafinha Bastos. Resultado: +0,5 momentum. A pontuação da resposta foi 58, ainda que o momentum fosse positivo.
- Tentei um palanque com Ratinho Júnior no Paraná. A tela disse antes da ação “Já está no seu palanque”, mas na resolução revelou falta de 10 pontos de disposição: Ratinho preferiu neutralidade, ficou um pouco mais receptivo e a ação rendeu −0,3 ponto nacional. A interface não preveniu a ação inviável.
- A agenda foi: visita ao Grito dos Excluídos em SP (+5,6), live (0,0 na lista; +0,5 momentum separado) e palanque com o governador no PR (−0,3). Sem descanso, a energia chegou a 26; o jogo avisou que abaixo de 35 as ações rendem 60% e o próximo debate perde 8 pontos. Caixa no fechamento: R$ 29,6 mi.
- Aceitei Tarcísio de Freitas (Republicanos/SP) e Renzo Braz (PP/MG): apoios recorrentes passaram a +2,48 p.p./semana, cada um com promessa de ministério ao partido.

## Semana 8: consequência, sabatina e debate

- A abertura mostrou Cury em 7,7% (−0,4 na semana) contra Lula em 38,3%; caixa R$ 32,5 mi, energia 38 e apoio recorrente +2,48 p.p./semana antes dos dois apoios novos. O aviso de teto natural em 8% pelo caso do drone continuava ativo.
- A denúncia anterior virou “O dossiê: as contas abertas”. Após três dias revisando os livros, jornalistas encontraram uma nota de R$ 180 mil por serviço de gráfica não entregue; o restante estava em ordem. Escolhi devolver o valor e demitir quem assinou; o cartão saiu da tela. A consequência visível confirma transparência com custo reputacional concreto, sem esclarecer se o tema se encerrou permanentemente.
- Sabatina 2: TV Popular, José Luiz Datena, três perguntas de 90 segundos; fuga retorna com 60 segundos e menos paciência. Q1 exigiu número exato de viaturas. A resposta prometeu mil veículos no primeiro ano, priorizando PF/PRF e convênios estaduais dentro do orçamento; nota 74. O avaliador premiou responder com número e passo concreto.
- Q2 perguntou quantos policiais civis e militares seriam contratados em 12 meses. A resposta distinguiu competência federal e estadual, comprometeu 2.000 vagas federais PF/PRF e convênios; nota 58 (“entendida, sem empolgar”). O sistema pede precisão e linha memorável, mesmo quando a resposta explica limites institucionais.
- Q3 perguntou como desmontar organizações armadas sem violar direitos humanos. A resposta propôs integração federal/estadual, rastreamento financeiro e mandados judiciais; nota 58, “correta, sem susto”. Média da sabatina: 63, “saiu maior do que entrou”.
- Debate de podcast 2, Inteligência Ltda. e Metrópoles: mediação de Rogério Vilela, 11 na mesa, Flávio Bolsonaro ausente. A versão livre permitiu apenas assistir de casa, com nota fixa 45 e sem risco; o resumo disse que Caiado levou a melhor sobre Zema no bloco em que o jogador não estava. A resposta ao vivo estava marcada como Pro; faltar custaria −2 momentum e cadeira vazia por duas semanas.
- Aceitei Eduardo Leite (PSD/RS) e Clécio Luís (União/AP), ambos com +0,32 p.p./semana indicado e exigência de ministério. O apoio total subiu de +2,48 para +3,09 p.p./semana, mostrando redução marginal do ganho de novos aliados.

## Lições para o design do Mandato

- Tornar claro o calendário: separar notícias e obrigações extraordinárias das três ações semanais; mostrar por que a agenda está travada e o que falta.
- Mostrar atualidade e data de cada pesquisa ao lado do número grande; a tela usa média defasada enquanto notícias podem sugerir corrida nova.
- Exibir custo, energia, alcance geográfico, duração e efeitos de cada ação antes de confirmar; registrar resultado previsto e resultado real lado a lado.
- Validar mudanças de estado antes da ação; destacar o estado selecionado para evitar o caso de contratar estrutura no Paraná após tentar selecionar SP.
- No TV, reconciliar cada componente com o total e mostrar a fórmula completa.
- Nas redes, informar custo e janela de efeito junto à escolha do estado, indicar se público-alvo por grupo é possível e evitar duplicar a mesma lista sem contexto.
- Para debates, separar avaliação da resposta, preferência por grupos, popularidade do clipe e posição agregada; permitir rascunho sem cronômetro, treino e feedback específico com exemplos concretos.
- A saída do debate deve preservar um resumo legível das notas, efeitos e manchete, sem esconder o restante abaixo de rolagem longa.
- Desacoplar a simulação da retórica gerada: o texto pode variar, mas o cálculo dos efeitos precisa de regras auditáveis.

## Evidências REA

- [Mapa estadual, semana 3](planalto-map-week3-2026-11-09.json)
- [Pesquisas e sala de guerra, semana 3](planalto-polls-week3-2026-11-09.json) · [sala de guerra](planalto-war-room-week3-2026-11-09.json)
- [TV e campanha, semana 4](planalto-campaign-week4-2026-11-09.json) · [editor de TV](planalto-tv-block-editor-week4-2026-11-09.json)
- [Campanha, semana 5](planalto-campaign-week5-actions-2026-11-09.json) · [pesquisa em SP após atualização](planalto-map-sp-after-week5-poll-2026-11-09.json) · [sala de guerra](planalto-war-room-week5-2026-11-09.json)
- [Impulsionamento da live em SP](planalto-redes-week5-boost-2026-11-09.json)
- [Evento e câmbio, semana 6](planalto-campaign-week6-event-2026-11-09.json) · [primeira resposta do debate](planalto-debate1-answer1-week6-2026-11-09.json) · [avaliação final](planalto-debate1-final-week6-2026-11-09.json) · [resultado do debate](planalto-debate1-results-week6-2026-11-09.json)
- [Fechamento da semana 6](planalto-campaign-week6-actions-2026-11-09.json) · [denúncia da semana 7](planalto-campaign-week7-scandal-2026-11-09.json) · [resposta à denúncia](planalto-week7-scandal-response-2026-11-09.json) · [visita a São Paulo](planalto-visit-sp-week7-2026-11-09.json)
- [Live sobre a denúncia](planalto-live-dossier-week7-2026-11-09.json) · [agenda 3/3](planalto-week7-agenda-fulfilled-2026-11-09.json) · [apoio a Tarcísio](planalto-week7-support-tarcisio-2026-11-09.json) · [abertura da semana 8](planalto-week8-opening-2026-11-09.json) · [resultados e novos apoios](planalto-week8-results-and-allies-2026-11-09.json) · [sabatina 2](planalto-sabatina2-results-week8-2026-11-09.json) · [debate 2 assistido de casa](planalto-debate2-home-week8-2026-11-09.json)

## Exploração pendente

- Explorar a resposta ao debate 2 e as ações da semana 8, aceitar ou recusar novos apoios dentro do prazo, e avançar até o primeiro turno.
- Continuar as semanas restantes até o primeiro turno, inclusive eleição, apuração, crise de campanha e eventual segundo turno. Se perder, iniciar outra campanha conforme a instrução do jogador.
- Explorar telas de candidato, carreata, pesquisa nacional/estadual, recursos de denúncia/justiça eleitoral no jogo, arrecadação, apoios, pesquisas legais, agenda local, publicidade, seleção de flanco, contratação e composição de chapa.
- Depois da eleição, se vencer, mapear transição, posse, gabinete, orçamento e governabilidade; se perder, observar encerramento e reiniciar.
- Manter este arquivo atualizado por rodada e adicionar capturas REA das mecânicas novas, evitando capturas redundantes de cada clique.
