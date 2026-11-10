# Biblioteca de acontecimentos

Os acontecimentos do jogo são **dados**, não código: cada evento é um objeto com condições declarativas, opções, efeitos limitados e encadeamentos. Isso permite milhares de eventos, geração por IA e revisão humana.

## Números atuais (9 nov. 2026)

| Medida | Valor |
| --- | ---: |
| Eventos válidos | 2.276 |
| Eventos de entrada (disparam sozinhos) | 2.046 |
| Eventos que só entram por encadeamento | 230 |
| Famílias de acontecimento | 28 |
| Por nível | federal 2.180 · militante 60 · partido 48 · estadual 36 · municipal 36 |
| Inválidos descartados | 0 |

**Honestidade sobre o que isso é:** 2.260 vêm de **geradores por famílias** (arquétipos com encaixes de setor, estado, gravidade...). Têm texto e efeitos distintos por combinação, mas são variações de um mesmo arquétipo; não são 2.260 histórias independentes. A camada de variedade real vem do corpus histórico + Gemini (abaixo). Os níveis estadual e municipal ainda têm poucos eventos (só preços de alimentos).

## Esquema (resumo)

`id`, `kind` (`decisao`, `oportunidade`, `info`), `levels`, `tags`, `family`, `weight` (0 = só por continuação), `cooldown`, `conditions` (lista de `{metric, op, value}`), `title`, `text`, `choices[]` (`id`, `label`, `hint`, `tone`, `cost_bi`, `effects`, `outcome`, `follow: [[id, dias]]`), `fallback`, `source` (`modelo`, `historico_inspirado`, `gemini`, `manual`), `review` (`aprovado`, `pendente`, `rejeitado`). Código: `backend/app/engine/event_schema.py`.

- **Limites de efeito** impedem evento gerado de quebrar o jogo (ex.: aprovação ±6, inflação ±1, reputação ±12).
- **Ritmo:** no máximo 2 pendentes, 7 dias tranquilos entre eventos, intervalo de 75 dias por família e assunto repetido pesa menos.
- **Prazo:** decisões que nascem durante um avanço de vários dias só começam a contar prazo quando o jogador retoma o controle.
- **Determinismo:** sorteio por hash de semente, dia e chave.

## Geração com corpus histórico e Gemini

1. Coloque fatos em `backend/data/events/corpus/*.jsonl` (formato e exemplo em `corpus/README.md`; **fonte obrigatória** por linha).
2. `python -m app.ai.event_generator generate --corpus data/events/corpus/fatos.jsonl --limit 50` (usa o Gemini se `GEMINI_API_KEY` estiver em `backend/.env`; com `--local`, adaptação por regras, sem IA).
3. A saída vai para `backend/data/events/generated/` com `review: "pendente"`: **não entra no jogo**.
4. Depois de revisar: `python -m app.ai.event_generator approve <arquivo>`.

Validação automática (reprova antes de gravar): esquema e limites de efeito; **nome de qualquer candidato de maior visibilidade do TSE** (presidente, governador, senador, deputado federal desde 2014) no texto; opção padrão inexistente; tom inválido. O prompt também exige ficção inspirada, sem pessoas reais, mas a validação não depende do prompt.

A chave do Gemini fica só no backend. Nada é enviado a um serviço externo sem a chave configurada. O corpus de fatos reais **ainda não foi carregado** (precisa do arquivo do autor do projeto).

## Pendente

- Carregar o corpus histórico e gerar o primeiro lote para revisão.
- Gemini como narrador em tempo de jogo (hoje só gera eventos fora do jogo).
- Eventos estaduais, municipais e legislativos em volume; hoje a Presidência concentra quase tudo.
- Interface de revisão (hoje é por arquivo e linha de comando).
