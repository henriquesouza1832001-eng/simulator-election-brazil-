# Direção visual do Quatro Anos (guia da versão 0.5)

Protótipo navegável deste documento: [`docs/visual/prototipo.html`](visual/prototipo.html). Abra no navegador e redimensione a janela; abaixo de 760 px ele vira a versão de celular.

## 1. O que o Planalto faz (estudo de estrutura, não de conteúdo)

Base: capturas e dossiês em `extrato/` e `research/rea/`. Só estrutura e padrões visuais; não copiamos fonte, imagem, texto nem conteúdo.

- **Emoção vem da imagem.** Fotografia em tela cheia no começo de cada tela, escurecida embaixo, com o título em cima. A imagem muda conforme o estado (na escolha de dificuldade: primavera verde, seca, incêndio).
- **Três vozes tipográficas.** Títulos largos e pesados em caixa-alta, texto corrido com serifa, e números em fonte monoespaçada.
- **Um acento só.** Um verde forte para ação e para o número principal; um amarelo fino para seleção e aviso.
- **Rótulos pequenos e espaçados** em caixa-alta no topo de cada bloco ("SEMANA 7 · AGENDA", "COMO FOI").
- **Uma ideia por tela.** O cartão de resultado tem *um número grande, uma frase e um botão*.
- **Ajuda sob demanda.** Um "?" em cada bloco, em vez de parágrafos explicativos; o detalhe técnico fica em "Por baixo do pano", recolhido.
- **O que fica fraco lá:** muito texto pequeno em tela, e a cara de "cartão de jogo mobile". Não vamos por esse caminho.

## 2. Onde o Quatro Anos está hoje

Funciona, mas é um painel genérico: sem imagem, tudo com o mesmo peso, muitos blocos que abrem e fecham, navegação em duas linhas no topo e, no celular, apenas o desktop encolhido. Falta uma identidade que dê vontade de abrir o jogo.

## 3. Conceito: "Brasília à noite, em papel de diário oficial"

Três ideias que decidem qualquer escolha de design:

1. **Monumental e sóbrio.** Vem da arquitetura de Brasília: linhas retas, grandes vazios, concreto, céu enorme. Telas calmas, números grandes, pouca decoração.
2. **Editorial.** Cada tela abre com uma **manchete** que diz a situação ("A inflação sobe pelo terceiro mês seguido"), escrita pelo motor a partir dos números, sem IA. Depois vêm os dados que a sustentam.
3. **Satírico com elegância.** A ironia está no texto das manchetes e dos eventos, nunca em caricatura gráfica de pessoas.

### O que nos diferencia do Planalto
Eles são **cinematográficos e pesados** (fotos dramáticas, fonte larga). Nós somos **editoriais e silenciosos**: serifa elegante nos títulos, duas cores de imagem (verde-noite e ouro, as cores da nossa marca) e muito espaço. Quem olhar não confunde os dois.

## 4. Sistema visual

### Cor (cada cor tem uma função única)
| Papel | Valor | Uso |
|---|---|---|
| Noite | `#0b1216` | fundo da página |
| Superfície | `#111b21` / `#172730` | blocos e blocos em destaque |
| Linha | `#26383f` / `#365058` | bordas de 1 px |
| Tinta | `#ecf3f1` / `#bccbce` / `#95aab0` | texto principal, secundário e de apoio |
| **Verde-bandeira** | `#2fa97c` (claro `#4cc79a`) | **só** ação principal e melhora |
| **Ouro** | `#d8b25a` | **só** seleção, prestígio e datas |
| **Tijolo** | `#e5776c` | **só** piora, risco e crise |
| Céu | `#86bfff` | informação neutra e links |

Regra: nenhuma cor é decorativa. Se o jogador vê verde, significa "bom" ou "faça isto". Todo texto tem contraste mínimo de 4,5:1 (a auditoria `tools/contrast-audit.mjs` garante).

### Tipografia (três vozes)
- **Títulos e manchetes:** Fraunces 700 (serifa), tamanhos 22, 28 e 44.
- **Texto:** DM Sans 400/600, 15 e 16.
- **Números e datas:** DM Mono 500, sempre com algarismos tabulares, tamanhos 17, 32 e 40.
- **Rótulos:** DM Sans 600, 12 px, caixa-alta, espaçamento .14em.
- As fontes ficam **dentro do jogo** (`public/fonts/`): o servidor só aceita arquivos do próprio site (política de segurança), então não dá para usar o Google Fonts.

### Forma e movimento
- Bloco: raio 12 px, borda de 1 px, sem sombra. Botão e etiqueta: pílula.
- Foco: contorno verde de 2 px, sempre visível.
- Transições de 150 a 220 ms; números não piscam; respeita "reduzir movimento".

### Ícones
Um conjunto só, de linha com 1,5 px (família Lucide), 24 px. Necessários agora: Painel, Governo, Política, Agenda, Mais, Guia, Perfil, Avançar, Fechar, Filtro, Seta para cima/baixo.

### Imagens
Duas cores (verde-noite e ouro), com leve granulação, **sem texto, sem rosto real e sem brasão oficial**. Uma imagem por seção, não por evento. Veja o pedido na seção 8.

## 5. Estrutura e navegação

### Regras de ouro
1. **No máximo 5 destinos** por nível de menu.
2. **No máximo 1 nível de "abre e fecha"** por tela. Chega de bloco dentro de bloco dentro de bloco.
3. Detalhe aparece em **painel lateral** (computador) ou **folha na base da tela** (celular), nunca expandindo no lugar e empurrando o resto.
4. Cada tela segue o mesmo molde: **manchete com imagem, faixa de 4 números, bloco principal, ação.**

### Computador (a partir de 1100 px)
Barra fina no topo (marca, data, Guia, Perfil, **Avançar**) e **trilho vertical à esquerda** com cinco seções: Painel, Governo, Política, Agenda e Mais. Dentro de cada seção, as subtelas viram **abas na própria página** (no máximo cinco). Acaba o menu de duas linhas.

### Tablet (760 a 1099 px)
O trilho continua só com ícones e rótulo curto. O painel de detalhe desce para baixo da lista.

### Celular (até 760 px)
- **Barra inferior** com 5 destinos: Painel, Governo, Política, Agenda, Mais.
- **Botão flutuante "Avançar"**, que abre uma folha com *1 dia, 7 dias, 1 mês*. Sai da barra de cima.
- **"Mais"** abre uma folha com Mundo, Perfil, Guia e Sobre.
- Barra de cima só com a data (uma linha).
- Subseções como **abas rolagem horizontal** no topo da página; assuntos viram **chips**.
- Todo detalhe abre numa **folha na base**, com botão Fechar.

## 6. Indicadores (menos "dropdown")

Hoje são 13 grupos que abrem e fecham. O novo desenho é **lista e detalhe**, sem acordeão:

- **Computador:** coluna da esquerda com os assuntos (com "3 melhoram · 1 piora"), no centro a lista de indicadores do assunto, **sempre aberta**; à direita o detalhe do indicador escolhido (gráfico de 24 meses, o que o move, o que ele afeta, quem pode agir).
- **Celular:** chips de assuntos, a lista, e o detalhe numa folha na base.
- No topo, só **quatro números e uma manchete**. "Escolher quais números aparecem" vira um ícone de engrenagem.
- O mesmo princípio vale para Histórico (abas Evolução/Decisões/Orçamento, sem blocos recolhidos) e Competências (filtro por área em chips, ação em cartão com "Detalhes" no painel).

## 7. Padrões de tela

| Padrão | Estrutura | Onde entra |
|---|---|---|
| **Manchete** | imagem, rótulo, título serifado de 1 a 2 linhas, uma frase | topo de toda seção |
| **Faixa de números** | 4 números grandes com variação | Visão geral, Indicadores, Orçamento |
| **Decisão** | pergunta, 2 a 3 opções, cada uma com custo e efeito, prazo visível | Crises, Medidas, Imprensa |
| **Resultado ("Como foi")** | um número grande, uma frase, um botão | depois de toda decisão e de cada mês |
| **Lista e detalhe** | assuntos, itens, painel | Indicadores, Congresso, Empresas |
| **Linha do tempo** | por mês, com selo de tipo | Histórico, Agenda, Imprensa |

Por tela (resumo do que muda):
- **Visão geral:** manchete do mês + 4 números + "próximo passo" + agenda. Já existe uma versão; ganha imagem e a manchete do motor.
- **Competências:** chips de área; cada ação em uma linha com tipo de aprovação à esquerda e botão à direita; detalhes no painel.
- **Orçamento:** faixa de números e uma tabela limpa; investimentos e obras como abas.
- **Crises e Imprensa:** padrão Decisão, com contagem regressiva do prazo.
- **Empresas:** lista e detalhe (a lista com saúde e relação, o detalhe com as decisões).
- **Carreira e Trajetória:** linha do tempo do cargo (pré-campanha, campanha, posse) com a etapa atual destacada.
- **Congresso:** lista e detalhe (bancadas, parlamentar).

## 8. Imagens a gerar (pedido para o chat de imagens)

Estilo comum a todas: *fotografia noturna ou crepuscular de Brasília, tratamento em duas cores (verde-noite `#0b1a1c` e ouro `#d8b25a`), granulação leve, composição ampla e calma, grande área de céu, sem texto, sem pessoas reconhecíveis, sem brasões ou símbolos oficiais.* Formato 21:9, 2560×1100, WebP até 250 KB (exportar também 960×420 para celular).

| Arquivo | Para que serve | Cena |
|---|---|---|
| `hero-painel-calmo` | Painel quando tudo vai bem | Esplanada dos Ministérios ao amanhecer, céu limpo |
| `hero-painel-tenso` | Painel com sinais de alerta | a mesma cena, céu carregado, luz baixa |
| `hero-painel-crise` | Painel em crise | a mesma cena, tempestade e relâmpagos distantes |
| `hero-governo` | seção Governo | a fachada com colunas do Palácio, sem brasão, em contraluz |
| `hero-politica` | seção Política | a cúpula do plenário vista de baixo (sem pessoas) |
| `hero-agenda` | seção Agenda | calendário de mesa e relógio antigo, sobre mármore |
| `hero-mais` | Mundo, Perfil e Sobre | globo de mesa e mapa do Brasil em relevo |
| `hero-economia` | Indicadores e Orçamento | porto e silos ao pôr do sol, vistos de longe |
| `hero-carreira` | Carreira | escadaria de prédio público, vazia, ao amanhecer |
| `hero-eleicao` | campanha e eleição | urna eletrônica em primeiro plano, fundo desfocado |

Mais um conjunto de **8 ilustrações pequenas** (512×512, mesma paleta, traço simples, sem texto) para as categorias de evento: economia, clima, segurança, saúde, educação, política, internacional, instituições. Uma por categoria, não uma por evento.

**Sugestão de pedido:** *"[cena]. Fotografia noturna, estilo editorial, duas cores (verde-escuro e ouro), granulação leve, composição ampla e calma, sem texto, sem pessoas, sem brasões. 21:9."* Gere a primeira da lista (`hero-painel-calmo`) e me mande para validarmos o estilo antes das outras.

## 9. Desempenho como parte da experiência

Medido nesta rodada (partida nova com o banco do TSE importado):
- O **primeiro avanço de tempo levava 23 a 33 segundos**: a biblioteca de eventos conferia, evento por evento, se citava uma pessoa real lendo de novo os 485 mil nomes de candidatos do banco. Corrigido: índice no banco, busca por trechos de palavras e pré-aquecimento ao ligar o servidor. **Hoje: 1,5 s.**
- O resumo do território (usado em Indicadores) era recalculado a cada mês (0,4 s). Agora é guardado e só recalcula quando uma decisão mexe nos indicadores.
- A cada avanço, as telas pedem várias coisas ao servidor ao mesmo tempo. Na 0.5: carregar só o que a tela mostra, com esqueleto de carregamento em vez de página em branco.
- Na VM pequena (CPU compartilhada) os números são maiores. Meta: avançar um mês em menos de 1 s e abrir uma tela em menos de 300 ms.

## 10. Como executar a 0.5

1. **Fundação:** fontes hospedadas, tokens (cores, tamanhos), ícones e o novo trilho/barra inferior/folha de detalhe.
2. **Visão geral e Indicadores** no molde novo (lista e detalhe).
3. **Imagens** da seção 8, assim que o estilo for aprovado.
4. **As demais telas**, uma por vez, com a sua revisão a cada uma.
5. **Apagar o CSS antigo** (`editorial.css`, `views.css` etc.).

**Critérios de pronto:** auditoria de contraste sem achados; teste de ponta a ponta verde; nenhuma tela com rolagem lateral em 390 px; Visão geral abre em menos de 1 s na VM.
