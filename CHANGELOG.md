# Changelog

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
