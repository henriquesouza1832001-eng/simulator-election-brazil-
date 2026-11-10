# Corpus de fatos históricos (entrada do gerador de acontecimentos)

Coloque aqui arquivos `.jsonl` (uma linha JSON por fato). Campos:

| Campo | Obrigatório | Descrição |
| --- | --- | --- |
| `id` | sim | identificador único do fato no seu banco |
| `date` | não | data do fato (AAAA-MM-DD) |
| `title` | não | título curto e factual |
| `summary` | sim | resumo factual em 1 a 3 frases (sem opinião) |
| `area` | não | `economia`, `saude`, `seguranca`, `clima`, `trabalho`, `integridade`, `congresso`, `diplomacia`... |
| `level` | não | `federal`, `estadual`, `municipal`, `legislativo`, `partido`, `militante` |
| `source_name` / `source_url` | **um dos dois** | fonte do fato; linhas sem fonte são ignoradas |

Exemplo:

```json
{"id":"f001","date":"2023-05-01","title":"Greve em refinarias","summary":"Trabalhadores paralisam refinarias e o abastecimento de combustíveis é afetado.","area":"trabalho","level":"federal","source_name":"Agência Brasil","source_url":"https://agenciabrasil.ebc.com.br/..."}
```

Geração (a saída é **pendente de revisão** e não entra no jogo sozinha):

```
cd backend
python -m app.ai.event_generator generate --corpus data/events/corpus/fatos.jsonl --limit 50          # usa o Gemini se houver GEMINI_API_KEY
python -m app.ai.event_generator generate --corpus data/events/corpus/fatos.jsonl --limit 50 --local  # sem Gemini
python -m app.ai.event_generator approve data/events/generated/<arquivo>.json                          # depois de revisar
```

Regras: o evento gerado é **ficção inspirada** no fato, sem pessoas reais (a validação reprova nomes de candidatos do TSE).
Eventos aprovados são lidos de `backend/data/events/**/*.json` ao iniciar o backend.
