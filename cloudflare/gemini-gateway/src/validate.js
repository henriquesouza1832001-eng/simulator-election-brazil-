// Validadores das saídas do Gemini. Nenhuma saída é aceita sem passar por aqui.

const NUMBER = /\d+(?:[.,]\d+)?/g;

export function numbersIn(text) {
  return new Set((String(text).match(NUMBER) || []).map((n) => n.replace(",", ".")));
}

export function sanitizeFacts(facts) {
  if (!Array.isArray(facts)) return [];
  return facts.slice(0, 8).filter((f) => f && typeof f.topic === "string" && typeof f.text === "string").map((f) => ({ topic: f.topic.slice(0, 40), text: f.text.slice(0, 220) }));
}

export function parseJson(raw) {
  if (typeof raw !== "string") return null;
  try { return JSON.parse(raw); } catch { return null; }
}

export function validateChoice(raw, ids) {
  const data = parseJson(raw);
  if (!data || typeof data !== "object") return null;
  const choice = ids.includes(data.choice) ? data.choice : null;
  const questions = (Array.isArray(data.questions) ? data.questions : []).filter((q) => typeof q === "string" && q.trim().length >= 8 && q.trim().length <= 160 && q.trim().endsWith("?")).map((q) => q.trim()).slice(0, 2);
  return { choice, questions };
}

export function validateQuestions(raw, facts, count) {
  const data = parseJson(raw);
  if (!data || !Array.isArray(data.questions)) return [];
  const allowed = numbersIn(facts.map((f) => f.text).join(" "));
  const out = [];
  for (const q of data.questions) {
    if (!q || typeof q.prompt !== "string" || typeof q.topic !== "string") continue;
    const prompt = q.prompt.trim();
    if (prompt.length < 20 || prompt.length > 300 || !prompt.endsWith("?")) continue;
    if (![...numbersIn(prompt)].every((n) => allowed.has(n))) continue; // número inventado
    out.push({ topic: q.topic.trim().slice(0, 40), prompt });
    if (out.length >= count) break;
  }
  return out;
}

export function validateNarration(raw, facts) {
  if (typeof raw !== "string") return null;
  const text = raw.trim();
  if (text.length < 40 || text.length > 700) return null;
  const source = JSON.stringify(facts);
  const allowedNumbers = numbersIn(source);
  for (const n of ["2", "3", "4"]) allowedNumbers.add(n);
  if (![...numbersIn(text)].every((n) => allowedNumbers.has(n))) return null;
  const caps = /\b[A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+\b/g;
  const known = new Set((source.match(caps) || []).concat(["Na", "Simulação", "O", "A", "Os", "As", "Em", "Isso", "Com", "Mas", "Por", "Não", "Se", "Esse", "Essa", "No", "Uma", "Um"]));
  return (text.match(caps) || []).every((w) => known.has(w)) ? text : null;
}
