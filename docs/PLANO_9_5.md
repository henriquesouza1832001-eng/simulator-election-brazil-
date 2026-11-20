# Plano até 9,5 (rodada 2 com o Gemini, 19 nov. 2026)

Fonte: `docs/revisoes/GEMINI_RODADA_2.md` (resposta completa). Abaixo, o que conferi no código, o que já corrigi e o que depende de você.

## Conferido no código
| Achado do Gemini | Resultado |
|---|---|
| Inflação 4,0 (topo) × 4,3 (IPCA) × 4,1 (Painel) na mesma rodada | **Verdadeiro.** A cópia dos indicadores era feita antes do passo da economia. **Corrigido:** Indicadores passam a copiar o valor depois da economia (`state.py`) |
| Risco-país 220 (Mercado) × 279 (Orçamento) | **Verdadeiro.** O Orçamento usava uma fórmula fiscal antiga. **Corrigido:** usa o risco do mercado (`fiscal.py`) |
| Teste de fonte única | Novo: `test_fonte_unica_indicadores.py` |
| "Por que mudou?" repete "Tendência da economia" | **Desatualizado:** a captura foi tirada antes de reavançar o mês. Hoje cada termo de inflação, PIB e desemprego aparece com nome |
| Redes: "Nada nas redes ainda" mesmo após meses de governo | **Verdadeiro.** Posts só nascem de crise, decisão ou pesquisa. Entra no plano (6.2) |
| Corte de viagens e residência move 0,000% do PIB | Verdadeiro no desenho: são R$ 3 bi num PIB de R$ 15 tri. Falta alavanca fiscal de peso (5.1) |
| Arquivos grandes, 70 s por mandato | Confirmado (`career.py` 2.006 linhas) |
| Nomes reais de 513 deputados e 81 senadores na tela Congresso | Verdadeiro; ver decisão (a) |

## Decisões suas
a. **Nomes reais de parlamentares.** Você pediu antes Congresso real; o Gemini recomenda nomes fictícios (mantendo partido, estado e bancada reais) por risco jurídico em jogo com CPI e corrupção. Minha sugestão: nomes fictícios gerados de forma estável, e manter só números e bancadas reais.
b. **Congelar novos subsistemas por ~3 semanas** para refatorar monolitos, mesa de despacho e textos. Sugestão: sim, por 2 semanas, só fechando o que a campanha e a presidência já começaram.
c. **Cortar multiplayer e editor de cenários** do caminho até 9,5 (ficam documentados, sem desenvolvimento).
d. **Menu de 5 pilares** no lugar de 15+ itens.
e. **Plataforma e preço:** recomendação dele é web PWA primeiro, desktop depois, jogo pago único com demo grátis. Fica para depois do M2.

## Ordem de execução (junta a sugestão dele com a nossa)
**M1 — coerência e rapidez**
1. Fonte única dos números: feito para inflação, PIB, desemprego, aprovação e risco-país; falta revisar dólar, Selic e dívida (2.1).
2. "Por que mudou?" com termos nomeados: feito para o Painel nacional (2.2); falta nos cargos locais.
3. Anonimizar nomes (10.1), depende da decisão (a).
4. Perfilar e acelerar o mandato de 48 meses (11.2).
5. Dividir `career.py`, `App.jsx` e `CareerPanel.jsx` por fatias (11.1).

**M2 — fluxo, onboarding e tom**
6. Mesa de despacho no Painel (1.1) e badges nas abas (1.3).
7. Redes e Imprensa nunca vazias (6.2).
8. Cenário "100 dias" (onboarding).
9. Guia de voz e reescrita de textos (6.1).

**M3 — profundidade:** coalizões e líderes de bloco (3.1), judicialização no STF (3.2), coligações, tempo de TV e segundo turno (4.1, 4.2), alavancas fiscais (5.1), narrador com cache e teto de custo (7.1).

**M4 — acabamento:** 53 artes, áudio, mobile e acessibilidade, 300+ eventos, playtest com 30 pessoas.

## Rodadas seguintes com o Gemini
Depois de cada marco: reenviar zip + capturas novas + `INVENTARIO_AUTOMATICO.md` regenerado, pedindo nota por dimensão e só o delta. Meta de cada rodada: nenhuma dimensão cair e as abertas subirem.

## Andamento (19 nov. 2026)
Decisões do criador: manter nomes reais com aviso de sátira, congelar novos sistemas por ~2 semanas, cortar multiplayer e editor de cenários, menu em 5 pilares.
- **Feito:** aviso de paródia no Congresso (tela e lista de parlamentares); redes nunca vazias (posts de rotina por quinzena, por cenário); mesa de despacho no Painel; menu em pilares (Painel, Governo, Política, Imprensa, Mais; Agenda foi para o Painel; Mercado só para presidente); cenário "Os primeiros 100 dias" com 5 metas e balanço (`engine/scenario_100.py`, botão na tela inicial).
- **Próximo (M1/M2):** perfilar o mandato de 48 meses (hoje ~70 s), dividir `career.py`, guia de voz e reescrita dos textos mais frequentes, "Por que mudou?" nos cargos locais.
- **Desempenho medido (19/11):** o mandato de 48 meses leva ~7 s pela API (146 ms por avanço, cerca de 65 a 90 ms dentro do processo), não 70 s como constava no briefing. Ajustes: exposição das crises em cache e `synchronous=NORMAL` no SQLite. A meta "menos de 5 s" não foi atingida pela API; o motor sozinho gasta ~1 a 3 s. Trava de regressão em `test_desempenho_mandato.py`.
- **`career.py` dividido:** de 2.006 linhas em fachada de 133 linhas + 11 módulos `career_*.py` (maior: 457 antes, `career_election` 280 e `career_calendar` 176 depois da última divisão). Teste `test_career_modulos.py` garante a fachada e o limite de 450 linhas.

## Rodada 3 com o Gemini — triagem (20 nov. 2026)
Resposta guardada em `docs/revisoes/GEMINI_RODADA_3.md`. Notas: média 6,0 (rodada 2: ~5,4); todos os arquivos e testes que ele citou existem.

**Aceito e corrigido na hora**
- D1 Aprovação 47,7 × 47,6 e deltas 4,8 × 4,9: causa era arredondamento de valores no meio (`47,65`) em formatadores diferentes. Agora um só arredondamento "meio para cima" (`roundHalfUp` em `format.js`, usado por `fmt`, `br` e `formatIndicator`).
- D2 "dia 30 de 100" × "DIA 31": o cenário passa a contar o primeiro dia como dia 1, igual ao cabeçalho.
- D3 botão "?" sobrepondo conteúdo: removido (o botão "Guia" do cabeçalho faz o mesmo).
- D4 mesmo perfil em dois posts seguidos: regra no `social_feed.py`, com teste.
- D5 caixas coladas no cenário: espaçamento maior.
- "Tendência" na Base no Congresso: dois fatores nomeados (volta ao equilíbrio; veto derrubado).
- Imprensa vazia na campanha: cada pesquisa publicada vira notícia, e os movimentos dos rivais saem com data própria e três variantes de texto cada (antes repetiam).
- "Avaliação simulada" no pronunciamento de posse e rótulos "simulado/fictício" em cartões e na tela de Crises: reescritos.

**Não aceito, com motivo**
- "(fictício)" nos nomes de veículos (Jornal da Manhã (fictício)): fica, como proteção contra confusão com marcas reais.
- Falta de "Movimentos recentes" em `pref.md`: a partida usada nas capturas tinha sido criada antes dessa função; a tela mostra os movimentos quando existem.
- Limite de 450 linhas para `App.jsx` e `CareerPanel.jsx`: o problema desses arquivos é tamanho em KB (linhas muito longas), então o teste deve medir KB.

**Próximo (do plano dele, que concordo)**
E1.3 alavancas fiscais reais e LRF subnacional · E1.4 coalizões, líderes e STF · E1.5 coligações, TV, debate e 2º turno · E1.6 voz em crises, entrevistas e debates · E1.7 bots por perfil e primeira partida humana · depois E2.1 fatiar `App.jsx` e `CareerPanel.jsx`.

## Andamento (20 nov. 2026)
- **E1.3 alavancas fiscais feito:** `engine/fiscal_levers.py` (contingenciamento de 5, 10 ou 15%, revisão de subsídios e dividendos extraordinários), rota `POST /api/budget/lever`, catálogo em `GET /api/budget` e cartões em Orçamento > Contas públicas com a previsão do motor antes de confirmar. Cada uma move o resultado primário em 0,07 a 0,24% do PIB (antes viagens e residência movia 0,000%), reage no mercado, na imprensa e no livro-razão, aparece em "Por que mudou?" e cobra preço em PIB, aprovação ou Congresso. Intervalo de 60 dias entre alavancas, limite anual para subsídios e dividendos, teto de 15% acumulado no contingenciamento. Testes: `test_alavancas_fiscais.py` (8).
- **Próximo:** E1.4 coalizões, líderes de bancada e STF.
- **E1.4 coalizões e STF feito (20/11):** (1) **Liminar do STF** em `regulators.py`: ato de risco jurídico alto (risco efetivo a partir de 0,30) recebe pedido de liminar em 7 a 15 dias; liminar concedida suspende o ato (reverte estrutura e efeitos) até o mérito; se o mérito mantém, a liminar é revogada e o ato volta (`_restore`); `test_stf_liminar.py` (5). O STF, a AGU e o julgamento de mérito já existiam: a rodada 3 do Gemini descreveu o STF como passivo, o que não é verdade. (2) **Blocos no Congresso** em `congress_process.py`: partidos agrupados em Base, Centrão e Oposição pelo apoio previsto ao projeto, com líder (maior bancada) e negociação em pacote (`POST /api/congress/negotiate-bloc`): o líder recebe o efeito pleno, os demais 70%, e o custo cresce 50% por partido adicional; botões "pacote" em Tramitação; `test_blocos_congresso.py` (5).
- **Também:** textos de STF, PF e Tribunal de Contas sem a palavra "simulação".
- **Próximo:** E1.5 coligações, tempo de TV, debate e segundo turno.
