# Sistema de design do Civiciclo (redesenho das telas)

Revisão de 10 nov. 2026. Modo de design: **operar** (é um app: consistência, contraste e leitura acima de expressão). **Logos e marca ficaram de fora e ficam a cargo do Codex**: `Brand.jsx`, `public/assets/brand/`, retratos e as regras CSS `.brand*` foram preservados byte a byte.

## O que foi decidido

- **Uma família tipográfica só: DM Sans** (já carregada pelo `@import` do `styles.css`), com pilha de sistema como reserva. Fim do uso de fonte monoespaçada como estilo de rótulo. Números com `tabular-nums`. Escala fixa em `rem` (0,81 / 0,94 / 1 / 1,19 / 1,44 / 1,75).
- **Tema claro único.** O app nasceu escuro e a migração ficou pela metade: painéis de Diplomacia, Orçamento, Carreira, Eleição e Nomeações ainda tinham fundo preto com texto verde escuro quase invisível. As cores escuras dos CSS legados foram remapeadas por luminância (fundo escuro → superfície clara, texto claro → tinta escura).
- **Tokens e componentes em `src/theme.css`** (carregado por último): tinta `#1b2b25`, texto secundário `#46564f`, superfície `#fbfaf6`, acento `#1f7a4f`/`#17613f`, foco azul de 3 px, controles de 44 px, cartões planos (sem gradiente, sem sombra), `details` padronizado, abas legíveis e cabeçalho compacto no celular.
- **Estrutura:** a faixa de abertura (título, personagem, "Mandato 5/48") só aparece em *Visão geral* e *Indicadores*; nas demais abas ela duplicava o título do próprio painel. Listas longas agora mostram o essencial e deixam o resto sob demanda (Congresso: 20 por vez; Placar: 10; Semana: ações indisponíveis recolhidas; Acontecimentos: histórico recolhido; Diplomacia: seções recolhidas no celular).
- **Etiquetas em caixa-alta acima de títulos** foram removidas das telas novas e viram rótulo comum (ou somem, quando precedem um título) nas antigas. Faixas coloridas laterais de 2–3 px nos cartões foram reduzidas a 1 px.

## Defeitos reais encontrados e corrigidos no caminho

| Defeito | Causa | Correção |
| --- | --- | --- |
| Os 6 indicadores da *Visão geral* mostravam só "— %" | já existia no repositório: a lista de cartões não tem `source` e `readIndicator` devolvia `undefined` | itens sem `source` leem de `state.metrics` |
| Status "incumbent" em inglês no topo | rótulo cru do motor | mapa de rótulos em português |
| Textos sem acento ("Relacao", "America do Sul", "Previdencia") | dados do backend e JSX | corrigidos em literais de texto (diplomacia, fiscal, orçamento) |
| Botões do topo parecendo desativados | contraste | ver `theme.css` |

## Medidas (alturas de página, mesmos estados de jogo, antes → depois)

| Tela | Desktop | Celular |
| --- | ---: | ---: |
| Congresso | 3.527 → 2.117 | **12.078 → 3.234** |
| Coleção | 1.478 → 1.253 | 4.762 → 2.176 |
| Acontecimentos | 1.372 → 903 | 2.071 → 1.373 |
| Placar | 1.822 → 1.551 | 2.581 → 2.263 |
| Orçamento | 1.854 → 1.627 | 3.047 → 2.730 |
| Visão geral | 1.049 → 988 | 1.957 → 1.976 |

Todas as 22 telas: **0 erros de console e nenhuma rolagem horizontal** em 1280 px e 390 px. O detector mecânico do Impeccable devolveu `[]` para todos os CSS e JSX.

## Limites e pendências

- **Semana** (3.201 px no celular), **Orçamento** (2.730) e **Diplomacia** continuam longas; a altura de Diplomacia no teste está inflada porque as seções abrem conforme a largura na primeira renderização, e a medição reduz a janela depois. Falta recolher as colunas de receitas e despesas do Orçamento no celular.
- O remapeamento de cores foi **mecânico**: conferi por captura as telas principais (Visão geral, Orçamento, Diplomacia, Carreira, Nomeações, início), mas não cada estado de cada tela (ex.: resultado de eleição, crise ativa, votação em andamento). Podem restar contrastes a ajustar em estados raros.
- **Privacidade:** `styles.css` importa fontes do Google (`fonts.googleapis.com`) a cada carregamento, o que envia o IP de quem joga a um terceiro. Como a tipografia da marca depende disso, deixei como está para o Codex decidir; a saída é hospedar as fontes localmente.
- Faltam tela de carregamento com esqueleto e tratamento de estados vazios em várias telas antigas.
- Não houve revisão de acessibilidade com leitor de tela; verificados apenas contraste, foco visível, alvos de 44 px e rolagem.
