// Gateway do Gemini para o Civiciclo (Cloudflare Worker).
// A chave do Gemini existe só aqui (wrangler secret). O backend chama este Worker com um token compartilhado.
// O Gemini é a ÚLTIMA camada: só desempata ações, sugere perguntas e reescreve fatos que o motor já decidiu.
// Toda saída é validada (ids de candidatos, números e nomes presentes nos fatos); se falhar, devolve source "none".

import { validateChoice, validateQuestions, validateNarration, sanitizeFacts } from "./validate.js";

const MAX_BODY = 12_000;
const JSON_HEADERS = { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" };
const bucket = new Map(); // limite simples por isolate; use o binding de Rate Limiting em produção (ver README)

function reply(status, body) { return new Response(JSON.stringify(body), { status, headers: JSON_HEADERS }); }

function authorized(request, env) {
  const header = request.headers.get("authorization") || "";
  const token = header.startsWith("Bearer ") ? header.slice(7) : "";
  return Boolean(env.GATEWAY_TOKEN) && token.length === env.GATEWAY_TOKEN.length && timingSafeEqual(token, env.GATEWAY_TOKEN);
}

function timingSafeEqual(a, b) {
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

function limited(env) {
  const minute = Math.floor(Date.now() / 60_000);
  const key = String(minute);
  const used = (bucket.get(key) || 0) + 1;
  bucket.clear();
  bucket.set(key, used);
  return used > Number(env.RATE_PER_MINUTE || 60);
}

async function gemini(env, system, userJson, schema, maxTokens = 400) {
  const model = /^[A-Za-z0-9._-]{3,80}$/.test(env.GEMINI_MODEL || "") ? env.GEMINI_MODEL : "gemini-2.5-flash";
  const generationConfig = { maxOutputTokens: maxTokens, thinkingConfig: { thinkingLevel: "low" } };
  if (schema) generationConfig.responseFormat = { text: { mimeType: "APPLICATION_JSON", schema } };
  const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent`, {
    method: "POST",
    headers: { "x-goog-api-key": env.GEMINI_API_KEY, "content-type": "application/json" },
    body: JSON.stringify({ systemInstruction: { parts: [{ text: system }] }, contents: [{ role: "user", parts: [{ text: JSON.stringify(userJson) }] }], generationConfig }),
    signal: AbortSignal.timeout(12_000),
  });
  if (!response.ok) return null;
  const data = await response.json();
  const part = data?.candidates?.[0]?.content?.parts?.find((p) => typeof p?.text === "string");
  return part ? part.text : null;
}

const SYSTEM_ACTION = "Você ajuda um simulador político a entender o que o jogador quis fazer. Escolha no máximo UM id da lista de candidatos ou 'nenhum'. Se estiver em dúvida, sugira até duas perguntas curtas em português do Brasil. Não crie ações novas, não cite números.";
const SYSTEM_QUESTIONS = "Você escreve perguntas de jornalistas e mediadores para um simulador político, em português do Brasil. Use SOMENTE os fatos fornecidos (números e nomes). Cada pergunta tem no máximo 280 caracteres, termina com '?', é neutra e específica. Priorize os temas em que o jogador foi pior. Não invente dados.";
const SYSTEM_NARRATE = "Você escreve notícias curtas e neutras em português do Brasil para um simulador. Use SOMENTE os fatos fornecidos; não invente números, nomes, datas ou citações. 2 a 4 frases; deixe claro que é simulação.";

async function interpretAction(body, env) {
  const candidates = (body.candidates || []).slice(0, 8).filter((c) => c && typeof c.id === "string" && typeof c.title === "string");
  if (!candidates.length || typeof body.text !== "string") return { source: "none" };
  const ids = candidates.map((c) => c.id);
  const schema = { type: "OBJECT", properties: { choice: { type: "STRING", enum: [...ids, "nenhum"] }, questions: { type: "ARRAY", items: { type: "STRING" }, maxItems: 2 } }, required: ["choice", "questions"] };
  const raw = await gemini(env, SYSTEM_ACTION, { texto_do_jogador: body.text.slice(0, 400), candidatos: candidates.map((c) => ({ id: c.id, titulo: c.title })), exemplos_confirmados: (body.confirmed || []).slice(0, 3) }, schema, 300);
  const out = validateChoice(raw, ids);
  return out ? { source: "gemini", ...out } : { source: "none" };
}

async function questions(body, env) {
  const facts = sanitizeFacts(body.facts);
  if (!facts.length) return { source: "none" };
  const count = Math.min(Math.max(Number(body.count) || 3, 1), 5);
  const schema = { type: "OBJECT", properties: { questions: { type: "ARRAY", maxItems: count, items: { type: "OBJECT", properties: { topic: { type: "STRING" }, prompt: { type: "STRING" } }, required: ["topic", "prompt"] } } }, required: ["questions"] };
  const raw = await gemini(env, SYSTEM_QUESTIONS, { fatos: facts, temas_fracos: (body.weak_topics || []).slice(0, 5), cargo: String(body.office || "").slice(0, 40), quantidade: count, formato: body.kind === "debate" ? "debate" : body.kind === "sabatina" ? "sabatina" : "entrevista" }, schema, 700);
  const out = validateQuestions(raw, facts, count);
  return out.length ? { source: "gemini", questions: out } : { source: "none" };
}

async function narrate(body, env) {
  const facts = body.facts && typeof body.facts === "object" ? body.facts : null;
  if (!facts) return { source: "none" };
  const raw = await gemini(env, SYSTEM_NARRATE, { fatos: facts }, null, 400);
  const text = validateNarration(raw, facts);
  return text ? { source: "gemini", text } : { source: "none" };
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === "/health") return reply(200, { ok: true, model: env.GEMINI_MODEL || "gemini-2.5-flash" });
    if (request.method !== "POST") return reply(405, { error: "método não permitido" });
    if (!authorized(request, env)) return reply(401, { error: "não autorizado" });
    if (!env.GEMINI_API_KEY) return reply(200, { source: "none", reason: "chave não configurada" });
    if (limited(env)) return reply(429, { error: "limite por minuto atingido" });
    const text = await request.text();
    if (text.length > MAX_BODY) return reply(413, { error: "corpo grande demais" });
    let body;
    try { body = JSON.parse(text); } catch { return reply(400, { error: "JSON inválido" }); }
    try {
      if (url.pathname === "/v1/interpret-action") return reply(200, await interpretAction(body, env));
      if (url.pathname === "/v1/questions") return reply(200, await questions(body, env));
      if (url.pathname === "/v1/narrate") return reply(200, await narrate(body, env));
    } catch {
      return reply(200, { source: "none", reason: "gemini indisponível" });
    }
    return reply(404, { error: "rota desconhecida" });
  },
};
