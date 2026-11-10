# Changelog

## 0.6 — 10 nov. 2026 (redesenho das telas antigas)

- Sistema de design único (`src/theme.css`, `docs/DESIGN_SISTEMA.md`): tema claro, DM Sans, escala tipográfica fixa, contraste e foco verificados, controles de 44 px.
- Painéis escuros legados (Diplomacia, Orçamento, Carreira, Eleição, Nomeações) migrados para o tema claro.
- Listas longas recolhidas ou paginadas (Congresso 12.078 → 3.234 px no celular).
- Corrigidos: números dos 6 indicadores da Visão geral (já ausentes no repositório), status em inglês, textos sem acento, botões do topo ilegíveis.
- **Logos e marca não foram alterados** (a cargo do Codex).

## 0.5 — 9 nov. 2026 (biblioteca de eventos e trajetória partidária)

### Também nesta versão
- **Corpus de 67 fatos e temas** e **124 eventos inspirados em fatos reais**, gerados localmente e aprovados por validação automática (sem revisão humana; fontes a anexar).
- **Remix fora de época:** esses eventos mudam de lugar, intensidade e redação a cada partida (`engine/event_remix.py`).
- **Workflows:** `ci.yml` (validação antes do merge, sem AWS) e `events-generate.yml` (gera eventos e abre PR de revisão). Ver `docs/WORKFLOWS_E_AWS.md`.
- O gerador recusa rodar sem a trava de nomes reais; a importação do TSE confirma por lote.

### Novo
- **Biblioteca de acontecimentos em dados:** 2.276 eventos válidos (28 famílias, 230 encadeamentos), esquema com condições declarativas e limites de efeito, ritmo por família e níveis (`federal`, `estadual`, `municipal`, `legislativo`, `partido`, `militante`). Ver `docs/BIBLIOTECA_DE_EVENTOS.md`.
- **Gerador de eventos** com Gemini opcional e adaptação local, a partir de um corpus histórico com fonte; saída **pendente de revisão**; trava contra nomes de candidatos reais do TSE (`python -m app.ai.event_generator`).
- **Trajetória partidária:** eleitor engajado → militante → filiado (com recusa) → quadro (cargo no diretório) → pré-candidato a vereador, ligada ao motor de carreira. Quarto modo na tela inicial. Ver `docs/TRAJETORIA_PARTIDARIA.md`.
- API: `/api/party-path/*`, `/api/story/library`.

### Corrigido
- Acontecimentos que nasciam durante um avanço de vários dias venciam antes de o jogador vê-los (valia sempre a opção padrão).
- Custo único de um acontecimento virava déficit anual permanente.
- O placar quebrava com o texto de resultado da eleição.
- Equilíbrio: decidir bem sobe a aprovação, ignorar ou decidir mal derruba (teste de regressão em `tests/test_story_balance.py`).

### Pendente
- Corpus histórico real (arquivo do autor) e primeiro lote gerado.
- Gemini como narrador em tempo de jogo; interface de revisão de eventos.
- Outros papéis (prefeito, deputado, vice, assessor, cargos de nomeação) e vida interna do partido.
- Redesenho das telas antigas.

## 0.4 — 9 nov. 2026 (fatia: cenários eleitorais e Modo Eleitor)

### Novo
- **Calendário de cenários 2014–2030** com regras por ano e cargo e fontes (`engine/election_rules.py`), validação de cargo, UF e município (código IBGE).
- **Importador de candidaturas do TSE com proveniência** (`app/data/tse_candidacies.py`): apenas o recurso "Candidatos", SHA-256, licença, data de coleta e contadores de descarte. Anos importados: 2014, 2016, 2018, 2020, 2022, 2024 e 2026.
- **Modo Eleitor**: pleito, cargo, território, candidatos oficiais paginados e busca sem acento, urna simulada com aviso fixo e comparativo com a situação de totalização oficial. 2028 e 2030 usam elenco fictício rotulado "cenário futuro simulado".
- API: `/api/scenarios`, `/api/scenarios/{ano}`, `/api/scenarios/validate`, `/api/elector/candidates`, `/api/elector/vote`, `/api/elector/votes`.
- Congresso nominal (513 + 81), campanha semanal com debate, compromissos de campanha, motor de acontecimentos, placar, coleção e diário (ver `docs/ROTEIRO_AMPLIACAO.md`).
- Documentação: `docs/ELEICOES_E_CENARIOS.md`, `docs/MULTIPLAYER_ARQUITETURA.md`, `docs/REGISTRO_OBSERVACAO_PLANALTO.md`, `docs/MODELO_DE_DADOS_PLANALTO.md`.

### Corrigido
- Defeito do importador antigo do TSE que sobrescrevia candidaturas completas por linhas vazias (descrição em `docs/ELEICOES_E_CENARIOS.md`). A tabela antiga não foi tocada.

### Pendente
- Jogar como candidato em anos passados; votos por candidato e resultados agregados; fotos oficiais e caricaturas por candidatura na tela; migração dos endpoints antigos do TSE; multiplayer (somente documentado).
