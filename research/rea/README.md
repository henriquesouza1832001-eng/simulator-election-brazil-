# Exploração do PLANALTO com REA

Este diretório compartilha evidências locais com o Claude Code enquanto a partida é explorada no Chrome.

O resumo detalhado, regras observadas, decisões, efeitos, inconsistências e roteiro de exploração está em [DOSSIER.md](DOSSIER.md).

## Sessão observada (pausada)

- Site: `https://planalto.fun/jogar`
- CDP local: `http://127.0.0.1:9333`
- Origem permitida: `https://planalto.fun`
- Alvo atual: `F78E36C80ECC84AF4232BCF8B95D40ED`
- Estado atual: campanha presidencial, semana 9 de 13; pausa solicitada pelo jogador. A agenda da semana 9 está em 0/3 e a campanha não foi avançada além da resposta ao evento inicial. Personagem: Augusto Cury (AVANTE), no modo Normal. Na tela de corrida, Cury aparece em 3º com 9,5%, atrás de Lula (42,0%) e Flávio Bolsonaro (29,4%); o resultado eleitoral não foi observado.
- Evidência REA: [planalto-map-week3-2026-11-09.json](planalto-map-week3-2026-11-09.json)
- Evidência REA com São Paulo selecionado: [planalto-map-sp-detail-week3-2026-11-09.json](planalto-map-sp-detail-week3-2026-11-09.json)
- Evidência REA após a pesquisa interna em São Paulo: [planalto-map-sp-internal-poll-week3-2026-11-09.json](planalto-map-sp-internal-poll-week3-2026-11-09.json)
- Evidência REA da tela de pesquisas: [planalto-polls-week3-2026-11-09.json](planalto-polls-week3-2026-11-09.json)
- Evidência REA da tela de redes: [planalto-redes-week3-2026-11-09.json](planalto-redes-week3-2026-11-09.json)
- Evidência REA da sala de guerra: [planalto-war-room-week3-2026-11-09.json](planalto-war-room-week3-2026-11-09.json)
- Evidência REA do painel de campanha na semana 4: [planalto-campaign-week4-2026-11-09.json](planalto-campaign-week4-2026-11-09.json)
- Evidência REA do editor de horário eleitoral: [planalto-tv-block-editor-week4-2026-11-09.json](planalto-tv-block-editor-week4-2026-11-09.json)
- Evidência REA da explicação do tempo de TV: [planalto-tv-time-source-week4-2026-11-09.json](planalto-tv-time-source-week4-2026-11-09.json)
- Evidência REA do debate e fechamento da semana 6, mais as decisões da semana 7: [DOSSIER.md](DOSSIER.md#semana-6-expointer-redes-e-fechamento) · [denúncia](planalto-campaign-week7-scandal-2026-11-09.json) · [resposta](planalto-week7-scandal-response-2026-11-09.json) · [visita a SP](planalto-visit-sp-week7-2026-11-09.json)
- Evidência REA de semana 8, sabatina, podcast e apoios: [abertura](planalto-week8-opening-2026-11-09.json) · [sabatina 2](planalto-sabatina2-results-week8-2026-11-09.json) · [debate 2 em casa](planalto-debate2-home-week8-2026-11-09.json) · [apoios](planalto-week8-results-and-allies-2026-11-09.json)
- Evidência REA do fechamento da semana 8 e da semana 9 pausada: [agenda 3/3](planalto-week8-agenda-fulfilled-2026-11-09.json) · [live](planalto-live-week8-2026-11-09.json) · [abertura da semana 9](planalto-week9-opening-2026-11-09.json) · [desfecho do dossiê](planalto-week9-scandal-resolution-2026-11-09.json) · [tela após resposta ao evento](planalto-week9-event-response-2026-11-09.json) · [corrida eleitoral](current-browser.png)

## Como continuar pelo Claude Code

O REA já está registrado para Claude Code em `C:\Users\Dell\.claude.json`; `rea doctor --client claude_code --json` confirmou a configuração alinhada. Use o MCP do REA com o endpoint loopback acima e limite a observação à origem `https://planalto.fun`.

Para cada tela, `list_browser_targets` encontra o alvo atual e `inspect_web_page` captura estrutura, acessibilidade e metadados. `capture_web_screenshot` registra a área visível. O REA observa passivamente: não navega, não clica nem avança a partida. A navegação e as decisões continuam sendo feitas na sessão visível do Chrome.

As capturas atuais omitem texto de console, código-fonte de scripts e conteúdo de armazenamento. Rede e WebSocket guardam apenas formatos e metadados, sem valores. Não habilitar coleta de armazenamento ou de fontes de script para esta exploração.

## Notas de jogo

- A primeira caminhada foi feita em São Paulo: R$ 0,4 mi, 10 de energia e +1,8 ponto nacional.
- Foram contratados cabos eleitorais no Paraná: R$ 2,5 mi, estrutura +9 e +0,8 ponto nacional. A tentativa de selecionar São Paulo não alterou a seleção; o jogo executou a ação no Paraná.
- O mapa da campanha mostra intenção por estado, margem, indecisos, estrutura, embalo, últimas visitas, governador, rejeição, mobilização e pesquisa. O SVG apresenta 27 unidades federativas e seus dados de intenção, composição parlamentar e governador.
- No detalhe de São Paulo: intenção de Cury 9,1%; Lula 31,3%; Flávio 26,7%; Renan Santos 8,8%; pesquisa AtlasIntel da semana 2: Cury 10,4% ±2,5; governador Tarcísio de Freitas (REPUBLICANOS); 70 deputados, 3 senadores e 2% de indecisos. O painel também mostra a campanha dos candidatos que estiveram no estado e o histórico da própria campanha.
- A pesquisa interna no estado custa R$ 0,4 mi e retorna Cury 9,1% com mobilização +0,6.
- A tela de pesquisas tem média nacional, curva semanal, estados grandes por instituto e erro amostral, mais o histórico por rodada. Na semana 2, a média é Lula 39,1%, Flávio 25,7%, Renan 7,9%, Cury 6,1%, Zema 4,2%, Caiado 3,5%; os demais somam 7,5%. As duas linhas nacionais exibidas são AtlasIntel (Lula 37,9; Flávio 26,3; Renan 7,0; Cury 6,9; Zema 3,8; Caiado 3,1; indecisos 5) e PoderData (40,3; 25,1; 8,8; 5,2; 4,5; 3,8; indecisos 5). As oito pesquisas estaduais listadas são SP/AtlasIntel, MG/PoderData, RJ/Datafolha, BA/Quaest, PR/AtlasIntel, RS/PoderData, PE/Datafolha e CE/Quaest.
- A tela de redes lista cortes simulados, visualizações e assuntos da semana. O vídeo “drone romântico” tinha 3,2 mi de visualizações; foi impulsionado em São Paulo, por duas semanas, pelo custo de R$ 0,5 mi.
- A sala de guerra exibe quatro probabilidades (presidência, vitória no 1º turno, chegar ao 2º e vencer o 2º), comparação de segundo turno e oito estados onde há margem para crescer. Na semana 3, as quatro probabilidades são 0%; Cury marca 23,6% contra 44,7% de Lula no confronto direto. Potencial nacional indicado: SP +1,34; RJ +0,66; GO +0,35; PR +0,52; MG +0,81; SC +0,37; RS +0,53; MT +0,18 pontos.
- Após fechar a semana 3, a campanha segue na semana 4, com três ações semanais. Cury ficou em 6,1% (+0,0), energia 94/100 e caixa de R$ 25,0 mi; TV 35 s/dia. O painel lista um aliado de Lula preso em operação de emendas, sem ação obrigatória aparente.
- Ofertas de apoio pedem ministério e duram duas semanas. Aceitei Raquel Lyra (PE, +0,53 p.p./semana) e recusei Fábio Mitidieri (SE, +0,53), mantendo a promessa de ministério ao PSD por Ratinho Júnior. O jogo registra as promessas de ministério como compromissos para março do primeiro ano.
- O editor do horário eleitoral divide 35 s/dia entre biografia, proposta, ataque, depoimento e jingle; ataque aumenta a rejeição e abre 20% de direito de resposta. Configurei 10 s biografia, 18 s proposta, 7 s depoimento, 0 ataque, 0 jingle, alcance nacional e sem alvo de ataque.
- A ajuda do horário diz que a chapa recebe 12 s iguais + 24 s proporcionais aos 5 deputados de AVANTE (de 282 nas chapas), mas declara total de 35 s/dia; os componentes exibidos não reproduzem esse total. Guardar como possível inconsistência de cálculo/UI para validar.
- A captura do mapa foi feita depois das duas ações da semana, antes de fechá-la.


## Continuação da campanha: semanas 4 e 5

- Semana 4 fechada com comício em São Paulo (+6,5 p.p. nacionais no resultado da ação; a agenda exibiu +7,2 p.p. na lista ao fechar), entrevista no Flow Podcast (Igor 3K, nota 63: respostas 58/73/58) e culto em São Paulo (+2,4 p.p. nacionais, simpatia religiosa persistente e reação negativa de parte dos jovens). O saldo antes da virada foi energia 59 e caixa R$ 23,0 mi.
- Na semana 5, a notícia do drone exigiu uma decisão antes de agir. Escolhi "Dobrar a aposta: apresentar o aplicativo" - integrar botão de pânico, delegacia e rede - em vez de insistir que era detalhe ou retirar a proposta. O painel ainda mostrava teto de 8% depois da escolha; conferir em rodadas futuras.
- Aceitei a sabatina especial do Jornal Nacional (César Tralli): nota total 69, com respostas 75/75/58. O jogo valorizou reconhecer o erro da fala sobre o drone e admitir o maior erro de gestão; considerou técnica e pouco convincente a explicação dos compromissos ministeriais.
- Visita à Festa do Peão de Barretos, em SP: +5,7 p.p. nacionais; a resposta da ação diz que o Agronegócio exportador viu a visita. Live com tom "falando como gente" e texto de 280 caracteres: alcance 1,4 mi, +0,6 momentum; seis perfis simulados responderam e a maioria defendeu a proposta, com crítica recorrente ao drone sem estrutura de atendimento.
- Reunião com Profissionais de saúde: simpatia +2,7, descrita como efeito gradual que vira voto ao longo das semanas. Energia ao fim das três ações: 47/100; caixa R$ 25,9 mi; Cury permanecia em 6,1% antes de fechar a semana.
- Apoios da semana 5: aceitei Helder Barbalho (MDB) no Pará (+0,46 p.p./semana, com pedido de ministério) e recusei Ibaneis Rocha (MDB) no DF para evitar prometer outra pasta ao mesmo partido por um território menor. O jogo registra a recusa e o aceite separadamente.
- Agenda da semana 5: 3/3 ações - visita em SP, live e reunião setorial. Ainda falta fechar a semana e conferir intenção, grupos, notícias, doações e eventuais novos apoios.
- Captura REA pós-ação: [planalto-campaign-week5-actions-2026-11-09.json](planalto-campaign-week5-actions-2026-11-09.json). A REA continua apenas observando a origem autorizada; decisões e cliques foram feitos na janela visível do Chrome.
