import test from "node:test";
import assert from "node:assert/strict";
import { validateChoice, validateQuestions, validateNarration, sanitizeFacts } from "../src/validate.js";

test("escolha fora da lista de candidatos é descartada", () => {
  assert.equal(validateChoice(JSON.stringify({ choice: "inventado", questions: [] }), ["a", "b"]).choice, null);
  assert.equal(validateChoice(JSON.stringify({ choice: "a", questions: ["Qual rodovia você quer asfaltar?", "x"] }), ["a", "b"]).choice, "a");
  assert.deepEqual(validateChoice(JSON.stringify({ choice: "a", questions: ["Qual rodovia você quer asfaltar?", "x"] }), ["a"]).questions, ["Qual rodovia você quer asfaltar?"]);
  assert.equal(validateChoice("não é json", ["a"]), null);
});

test("perguntas só passam com números presentes nos fatos", () => {
  const facts = sanitizeFacts([{ topic: "inflação", text: "A inflação está em 4,5% ao ano." }]);
  const ok = JSON.stringify({ questions: [{ topic: "inflação", prompt: "A inflação está em 4,5% ao ano. O que o governo fará nos próximos meses?" }] });
  const bad = JSON.stringify({ questions: [{ topic: "inflação", prompt: "A inflação passou de 9,8% ao ano. O que o governo fará agora?" }, { topic: "x", prompt: "Sem interrogação no fim" }] });
  assert.equal(validateQuestions(ok, facts, 3).length, 1);
  assert.equal(validateQuestions(bad, facts, 3).length, 0);
});

test("narração rejeita números e nomes que não estão nos fatos", () => {
  const facts = { title: "Recapear vias", forecast: { mobilidade: 2 }, result: { mobilidade: 2 } };
  assert.ok(validateNarration("Na simulação, a obra elevou a mobilidade em 2 pontos, como previsto pelo motor.", facts));
  assert.equal(validateNarration("A obra reduziu o tempo de viagem em 37 minutos segundo o prefeito Carlos.", facts), null);
});
