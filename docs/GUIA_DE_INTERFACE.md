# Guia de interface do Quatro Anos (0.5 → 0.8)

Documento de trabalho. Serve para mim (como mapa de implantação) e para o jogador (cada tela se liga a outras).
Princípio: **o motor decide, a interface mostra; cada número leva ao seu porquê, e cada porquê leva a uma ação.**

## 1. O que o jogador reclamou (resumo)

1. A cor e o conjunto parecem "estranhos" e simples demais: é direcionado, mas não parece simulador de governo.
2. Botões em pílula e cartões quadrados têm "cara de IA". Precisamos de um meio-termo.
3. Menu lateral pouco útil: poucos atalhos, sem fixar.
4. Painel: metade da informação é inútil; falta equilíbrio entre rolagem e informação.
5. Telas isoladas: cada uma deve poder mostrar dados de outra, quando fizer sentido (árvore de ligações).
6. Falta ver o país em tempo real (mapa) e, no dia da eleição, a apuração ponto a ponto.
7. Eleição deve simular de verdade (voto por cargo, capital, alcance de publicações, sátira de redes sociais entregue pelo motor).

## 2. Linguagem visual (decisão proposta)

Referência: **sala de situação / diário oficial**, não app de startup.

| Elemento | Hoje | Alvo |
|---|---|---|
| Fundo e superfícies | azul-marinho saturado | grafite azulado, baixa saturação; superfície um degrau acima |
| Acento | amarelo vivo (#ffd23f) | dourado fosco (usado só em ação principal, seleção e destaque) |
| Cantos | 10 px em tudo, pílula (999 px) nos filtros | 6 px em cartões, 4 px em controles; **sem pílula** |
| Filtros (Segmented) | pílulas amarelas | abas retas com linha inferior (como "guias" de processo) |
| Cartões | caixa com borda em todos os lados | bloco com régua superior e título em caixa-alta pequena (como cabeçalho de órgão) |
| Números | cartões grandes soltos | tabelas densas com variação e mini-gráfico (sparkline) |
| Cor semântica | verde/vermelho/amarelo | mantida, mas só para bom/ruim/atenção, nunca decorativa |
| Tipografia | serifada nos títulos, mono nos números | mantida; títulos de seção em caixa-alta pequena espaçada |

Regras: uma cor de acento; sem sombra decorativa; sem gradiente; ícone só quando ajuda a achar; texto antes de enfeite.

## 3. Árvore de telas e ligações

Cada nó é uma tela; cada seta é um link que o jogador consegue clicar (número → origem → ação).

```
Painel (centro de comando)
├─ Mapa do país (tempo real)            → Indicadores (estado) → Obras e mapa (cidades) → Crises
├─ Manchete do dia                      → Imprensa → Acontecimentos
├─ Números-chave (6, escolhidos)        → Indicadores (cada um abre o detalhe e o "o que move")
├─ Pendências                           → Crises, Tramitação, Nomeações, Agenda
└─ Atalhos fixados (pelo jogador)       → qualquer tela

Governo
├─ Medidas ──────────── Competências ─── Tramitação (projeto vira lei) ─── Congresso
├─ Orçamento ────────── Investimentos ── Obras e mapa ─── Indicadores
├─ Empresas ─────────── Banco Central (Selic) ─── Orçamento (juros) ─── Indicadores (inflação)
├─ Nomeações ────────── Congresso (base) ─── Instituições
└─ Crises ───────────── Agenda ─── Imprensa

Política
├─ Carreira ──────────── Eleição ─── Mapa de apuração
├─ Congresso ─────────── Tramitação
├─ Instituições ──────── Reguladores
└─ Eleição (campanha) ── Território (apoio por estado/município) ── Redes (publicações) ── Pesquisa

Agenda
├─ Compromissos ──────── Painel (pendências)
├─ Imprensa ──────────── Acontecimentos
└─ Entrevistas, sabatinas e debates ── Eleição (pesquisa)

Mundo
└─ Diplomacia ────────── Comércio ── Indicadores (câmbio, exportações)
```

Regra de ligação: **todo número tem origem clicável** (componente `IndicatorLinks`), **toda decisão mostra onde aparece depois** (Imprensa, Histórico, indicador afetado).

## 4. Menu lateral

- Grupos atuais (Painel, Governo, Política, Agenda, Mais) continuam.
- **Atalhos fixados**: o jogador fixa qualquer tela (ícone de alfinete); a lista aparece no topo do menu e no Painel. Guardada no navegador (por partida).
- **Acesso rápido**: mostrar contador de pendências em Governo (crises), Política (projetos e nomeações) e Agenda (compromissos).
- Menu recolhido mostra só ícones com contador; aberto mostra nomes e os atalhos fixados.

## 5. Painel como centro de comando

Meta: caber o essencial em 1 a 1,5 tela, sem rolagem inútil.

- **Faixa superior**: manchete do dia (curta) + 6 números-chave com tendência e sparkline.
- **Coluna principal**: mapa do Brasil em tempo real (camada alternável: aprovação, inflação, desemprego, crises, obras), com legenda e clique que abre o estado.
- **Coluna lateral**: pendências ordenadas por prazo; atalhos fixados; última decisão.
- **Balanço final** (fim de mandato) vira uma tela própria (Histórico), não bloco fixo do Painel.
- Itens sem dado ficam fora (não mostrar "nenhum compromisso próximo" ocupando espaço).

## 6. Mapa do país em tempo real

- Fonte: o motor já tem indicadores por estado (`nation`, `territory`). O mapa SVG (IBGE) já existe.
- Camadas: aprovação, inflação, desemprego, crises ativas, obras, eventos de imprensa.
- Atualiza a cada avanço de tempo; mostra a variação desde o último avanço.
- No dia da eleição (seção 7), vira o mapa de apuração.

## 7. Eleição simulada (modo jogável)

Objetivo: simular de verdade como uma eleição funciona, na proporção de cada cargo.

**Sistema por cargo**
- Vereador e deputado: voto proporcional. Quociente eleitoral = votos válidos ÷ vagas; cada partido ganha vagas pelo quociente e pelas sobras; dentro do partido, ordem pelos votos nominais.
- Prefeito, governador, presidente: majoritário. Segundo turno quando houver mais de 200 mil eleitores e ninguém passar de 50% dos válidos.
- Senador: majoritário (1 ou 2 vagas por ciclo).

**De onde vêm os votos**
- Base de voto por região/estado/município (dados TSE já importados) × afinidade partido/ideologia × conhecimento do nome × rejeição.
- **Capital de campanha** (dinheiro, tempo de TV, estrutura, militância) define alcance e conhecimento; teto de gastos por cargo.
- **Capital político**: alianças, apoio de lideranças, máquina do governo (quando no cargo).
- Escala: vereador disputa bairro/cidade; presidente disputa o país; a campanha mostra o alcance real de cada ação.

**Publicações e sátira de redes**
- O motor gera o evento (alcance, tom, quem engaja, efeito em conhecimento/rejeição) e entrega uma publicação de rede social satírica (usuários fictícios).
- Até a 0.6: textos de modelo guiados pelo motor. Na 0.7: o Gemini narra, sem decidir nada.
- Cada fala do jogador (debate, entrevista, post) vira publicação com resposta de aliados, adversários e imprensa.

**Dia da eleição**
- Apuração ponto a ponto: por zona/município, com mapa colorindo à medida que as urnas fecham (ordem real: do Acre ao Distrito Federal por horário).
- Placar por cargo, projeção, ponto de virada e narração curta.
- Registro final: quem ganhou, onde, e por quê (decisões que mais pesaram).

## 8. Plano em fases (ordem de implantação)

| Fase | Entrega | Onde mexe |
|---|---|---|
| **A** | Linguagem visual (cantos, cor, abas retas, cabeçalho de seção) | `design.css`, `shell.css` |
| **B** | Menu lateral com atalhos fixados e contadores | `Shell.jsx`, `App.jsx` |
| **C** | Painel como centro de comando (mapa, pendências, fixados) | `OverviewPanel`, `GeoMap` |
| **D** | Ligações entre telas (blocos "relacionado" nas telas principais) | `IndicatorLinks`, telas |
| **E** | Mapa de apuração + simulação de eleição por cargo | motor (`election`), `CampaignPanel` |
| **F** | Publicações e sátira de redes (modelos) | motor, `CampaignPanel` |
| **G** | Gemini narrando (0.7) | motor de narração |

Cada fase fecha com: captura das telas em 1280 px, checagem de largura em 390 px, auditoria de contraste e commit.

## 9. Perguntas em aberto

- Dourado fosco ou um acento diferente (verde-musgo, vermelho-tijolo)? A recomendação é manter o dourado, mais discreto.
- Atalhos fixados valem por partida ou para todo o jogo? Recomendação: por partida.
- O mapa do Painel mostra estados ou municípios? Recomendação: estados na 0.5, municípios na eleição.
