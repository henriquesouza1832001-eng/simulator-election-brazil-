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

## 0.5 — Direção visual (fechada em 15 nov. 2026)

**Entregue**
- Casca nova (trilho e barra inferior), fontes próprias, linguagem visual institucional (grafite, dourado fosco, cantos retos, abas com linha) e Painel como centro de comando, com mapa do país, pendências e atalhos fixados. Guia completo em [GUIA_DE_INTERFACE.md](GUIA_DE_INTERFACE.md) e [DIRECAO_VISUAL.md](DIRECAO_VISUAL.md).
- Navegação por endereço (`#/orcamento`), botão voltar, contadores no menu lateral; fim dos dropdowns (lista em painel lateral) e das telas longas (cartões, filtros e painéis).
- Telas refeitas: Indicadores, Orçamento, Investimentos, Empresas (71), Território, Congresso (plenário), Diplomacia (mapa), Imprensa, Entrevistas, Nomeações, Crises, Apuração e Redes.
- Eleição simulada: apuração por boletins (estado, regiões, quociente por legenda), primeiro e segundo turnos, horário eleitoral e teto de gastos na campanha de carreira.
- Redes sociais fictícias geradas pelo motor; sanções e vetos no Congresso; carimbos por partida; Placar e Diário no menu.
- Revisão de texto (pt-BR, plurais, acentos) e auditorias de contraste e de rolagem lateral nas telas do jogo; passada ponta a ponta nos sete cargos.
- Antecipado da 0.6: Copom e Selic, compra e venda de participação da União.

**Fica para depois**
- Fotos e caricaturas (1.0); Gemini (0.7); contas e nuvem (0.8).
- Mapa por município na apuração (exige o desenho dos municípios); tempo de TV e partido no modo Presidência.
- Pré-campanha do vereador como militante (alternativa ao pulo).

## 0.6 — Preparar o Gemini (em andamento desde 15 nov. 2026)
Objetivo: descobrir se o Gemini funciona de verdade antes de ligá-lo ao jogo na 0.7, e deixar o caminho pronto para jogar um mandato inteiro (48 meses) com ele na 0.7 ou na 0.9.
- Prova real: `backend/scripts/provar_gemini.py` (precisa de `GEMINI_API_KEY` no ambiente ou em `backend/.env`, que o Git ignora). Mostra se a chave vale, quais modelos existem, o erro cru do Google em cada formato de envio, qual recurso do jogo cai no texto local sem avisar e quanto tempo leva um mandato.
- Já corrigido: o narrador recusava todo texto com decimal em português ("0,9" contra "0.9" do motor); os recursos usavam modelos padrão diferentes e agora usam um só (`gateway.DEFAULT_MODEL`).
- Falta: rodar a prova com a chave real, ajustar o formato de envio ao que o modelo aceitar, mostrar na interface quando o texto veio do Gemini ou do reserva local, e registrar custo por mandato.
- A definir: onde entra o que estava sugerido para a 0.6 (empresas com várias decisões, concessões, rodovias e ferrovias). Não foi reatribuído a nenhuma versão.
## 0.7 — Gemini conectado (ou 0.9 para o mandato inteiro)
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
