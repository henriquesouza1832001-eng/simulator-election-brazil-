# Roteiro de versões do Quatro Anos

Proposta de roteiro. Os números 0.4, 0.7 e 1.0 vêm de você; os demais são sugestão para ajustarmos.

## 0.4 — Base de interface e informação (concluída em 14 nov. 2026)

O objetivo é uma base visual e de navegação robusta, em que qualquer informação do jogo seja fácil de achar e de entender.

**Pronto**
- Sistema de design único (`src/design.css` + `src/ui.jsx`): uma paleta, um tipo de bloco, componentes reutilizáveis (página, seção, número em destaque, linha de indicador, grupo recolhível, linha do tempo, gráfico, tabela).
- Auditoria automática de contraste (todas as abas, 0 achados nas telas auditadas) e correção dos resquícios do tema claro.
- Navegação em duas linhas; **Perfil** (Placar, Carimbos, Diário) fora da partida; Aprendizado e instruções de desenvolvedor removidos da tela do jogador.
- **Indicadores**: país ou uma cidade, com variação, tendência e "o que faz mudar / o que afeta".
- **Histórico**: evolução (um gráfico por vez), decisões em linha do tempo e orçamento.
- **Guia** em painel lateral, com o que cada aba faz, busca e glossário.
- Balanço do mandato com nota; CPI em etapas.

- Visão geral, Agenda, Imprensa e Sobre reescritos; pré-campanha longa com botão para pular até o ano da eleição.
- Telas antigas uniformizadas (mesma superfície, borda e tipografia) e sem artes decorativas de eventos.

**Refinos visuais (passam para a 0.5, que é a versão de direção visual)**
- Reescrever com os componentes novos (hoje só herdam o visual): Competências, Orçamento, Crises, Entrevistas, Carreira, Trajetória, Instituições, Nomeações, Empresas, Reguladores, Tramitação, Congresso, Diplomacia, Eleição e Semana.
- Remover os arquivos de CSS antigos (`editorial.css`, `views.css` e outros) quando nenhuma tela depender deles.
- Pré-campanha do vereador como militante (alternativa ao pulo), se ainda fizer sentido.

## 0.5 — Direção visual (próxima)
Identidade visual sólida e específica: manchete com imagem, números em destaque, navegação em trilho (computador) e barra inferior (celular), indicadores em lista e detalhe, desempenho. Guia completo em [DIRECAO_VISUAL.md](DIRECAO_VISUAL.md) e protótipo em `docs/visual/prototipo.html`.

## 0.6 — Motor: economia e Estado (sugestão)
Empresas com várias decisões ao mesmo tempo (comprar, vender, privatizar, financiar), Banco Central e Selic (influência, autonomia, juros), concessões, Eletrobras e demais estatais, rodovias e ferrovias. É a base do que vira o 1.0 para a Presidência.

## 0.7 — Gemini conectado
Hoje o Gemini está só provisionado (gateway na Cloudflare e variáveis de ambiente), sem ligação ao jogo em produção. Na 0.7 ele passa a:
- ler texto livre e mapear para ações do cargo (o motor valida);
- sugerir perguntas de entrevista e debate a partir do aprendizado;
- narrar fatos que o motor já decidiu.

Regra que não muda: o motor decide, o Gemini só interpreta e narra, e tudo que ele devolve é validado contra números e nomes do próprio motor.

## 0.8 — Congresso, eleições, contas e nuvem (sugestão)
Calendário de sessões, negociação por bancada para projetos de outros cargos, CPI completa, regras eleitorais por ano, Ficha Limpa; login, partidas na nuvem, ranking real e a base para jogar com outras pessoas (hoje só documentada).

## 0.9 — Balanceamento e acabamento (sugestão)
Simulações de 48 meses por estratégia, ajuste de dificuldade, acessibilidade, desempenho em celular e carga.

## 1.0 — Completo
Todos os cargos de vereador a presidente jogáveis ponta a ponta, reguladores com decisões próprias, empresas e Banco Central completos, dados oficiais atualizados e interface sem telas "de protótipo".
