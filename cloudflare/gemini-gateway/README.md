# Gateway do Gemini (Cloudflare Worker)

Serviço pequeno que fica entre o backend do Civiciclo e o Gemini. A chave do Gemini existe **só aqui**; o backend e o navegador nunca a veem. O Gemini é a última camada do jogo: o motor decide tudo; a IA só ajuda a entender texto livre, sugere perguntas e reescreve fatos já decididos.

Esta pasta pode virar um repositório próprio (`civiciclo-gemini-gateway`) sem mudanças.

## Rotas (POST, `Authorization: Bearer <GATEWAY_TOKEN>`)
| Rota | Entrada | Saída |
| --- | --- | --- |
| `/v1/interpret-action` | `text`, `candidates[{id,title}]`, `confirmed[]` | `{source, choice, questions[]}`; `choice` é sempre um id dos candidatos |
| `/v1/questions` | `facts[{topic,text}]`, `weak_topics[]`, `kind`, `count` | `{source, questions[{topic,prompt}]}`; números só se estiverem nos fatos |
| `/v1/narrate` | `facts{}` | `{source, text}`; números e nomes só se estiverem nos fatos |
| `GET /health` | — | `{ok:true}` |

Em qualquer falha (sem chave, timeout, resposta inválida) devolve `{"source":"none"}` e o jogo segue com as regras locais.

## Publicar (você faz, com sua conta Cloudflare)
```bash
cd cloudflare/gemini-gateway
npm install
npm test                         # validadores (node --test)
npx wrangler login
npx wrangler secret put GEMINI_API_KEY
npx wrangler secret put GATEWAY_TOKEN   # invente um token longo; use o mesmo no backend
npx wrangler deploy
```

No backend (variáveis de ambiente do servidor, nunca no front-end):
```
GEMINI_GATEWAY_URL=https://civiciclo-gemini-gateway.<sua-conta>.workers.dev
GEMINI_GATEWAY_TOKEN=<o mesmo GATEWAY_TOKEN>
```
Com o gateway configurado, o backend deixa de chamar o Google diretamente. Sem ele, usa `GEMINI_API_KEY` local (se existir) ou o modo local.

## Segurança e custo
- Rejeita corpos acima de 12 KB e limita a 60 chamadas por minuto por instância; para produção, ligue também uma regra de Rate Limiting da Cloudflare.
- Não envia dados pessoais: só texto da frase do jogador, títulos de ações e fatos numéricos do jogo.
- Respostas são validadas (ids, números, nomes) antes de sair; o backend valida de novo.
- Custo: uma chamada só quando há ambiguidade, ao abrir uma sessão de entrevista ou ao narrar.
