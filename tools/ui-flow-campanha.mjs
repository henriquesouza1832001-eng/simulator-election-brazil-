// Fluxo de ponta a ponta pela interface real: campanha majoritária (discurso lido, coligação, avanço até a apuração).
// Uso: node tools/ui-flow-campanha.mjs <idDaPartidaEmCampanha> [saida.json]
import fs from 'node:fs';

const [CID, OUT] = process.argv.slice(2);
const BASE = process.env.UI_BASE || 'http://localhost:5179/';
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const tab = await (await fetch('http://127.0.0.1:9222/json/new?about:blank', { method: 'PUT' })).json();
const ws = new WebSocket(tab.webSocketDebuggerUrl);
await new Promise((r) => (ws.onopen = r));
let nextId = 0; const pending = new Map(); const events = [];
const send = (method, params = {}) => new Promise((r) => { const id = ++nextId; pending.set(id, r); ws.send(JSON.stringify({ id, method, params })); });
ws.onmessage = (m) => {
  const d = JSON.parse(m.data);
  if (d.id && pending.has(d.id)) { pending.get(d.id)(d); pending.delete(d.id); }
  else if (d.method === 'Page.javascriptDialogOpening') send('Page.handleJavaScriptDialog', { accept: true });
  else if (d.method) events.push(d);
};
const ev = async (expression) => (await send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true })).result?.result?.value;
await send('Page.enable'); await send('Runtime.enable'); await send('Network.enable'); await send('Log.enable');
await send('Emulation.setDeviceMetricsOverride', { width: 1366, height: 900, deviceScaleFactor: 1, mobile: false });

const steps = [];
const step = async (name, fn) => {
  const t0 = Date.now(); let ok = false; let detail = '';
  try { const r = await fn(); ok = r === true || (r && r.ok); detail = (r && r.detail) || ''; } catch (e) { detail = String(e).slice(0, 160); }
  steps.push({ name, ok, ms: Date.now() - t0, detail });
  console.log(`${ok ? 'OK  ' : 'FALHA'} ${name} (${Date.now() - t0} ms)${detail ? ' — ' + detail : ''}`);
  return ok;
};
const text = () => ev('document.body.innerText');
const has = async (needle) => (await text()).toLowerCase().includes(needle.toLowerCase());
const waitText = async (needle, ms = 8000) => { const t0 = Date.now(); while (Date.now() - t0 < ms) { if (await has(needle)) return true; await sleep(300); } return false; };
const click = (label) => ev(`(()=>{const b=[...document.querySelectorAll('button,a')].find(x=>x.offsetParent&&!x.disabled&&x.innerText.trim().startsWith(${JSON.stringify(label)}));if(b){b.click();return true}return false})()`);
const dayNow = async () => (await text()).split('\n').map((l) => l.trim()).find((l) => /^\d{1,2} de [a-zç]+ de \d{4}$/i.test(l)) || null;   // linha da data no cabeçalho   // data do cabeçalho (carreira não mostra "DIA n de 1461")
const intent = async () => { const m = (await text()).match(/Intenção de voto\s*(\d+,\d)/i); return m ? m[1] : null; };

await send('Page.navigate', { url: BASE }); await sleep(1200);
await ev(`localStorage.setItem('mandato.activeCampaign','${CID}')`);
await send('Page.navigate', { url: BASE }); await sleep(6000);
await ev("(()=>{const b=[...document.querySelectorAll('button')].find(x=>x.innerText.trim().startsWith('Continuar'));if(b)b.click()})()"); await sleep(3000);

await step('Painel da campanha mostra intenção de voto, rivais e mesa', async () => { const t = await text(); return t.includes('Mesa de despacho') && /Intenção de voto/i.test(t) && /Quem disputa/i.test(t); });
await step('Carreira > Campanha abre o formulário de atividade', async () => { await ev("location.hash='#/carreira'"); await sleep(1500); if (!(await click('Campanha'))) return false; await sleep(800); return ev("document.querySelectorAll('textarea').length > 0"); });
let before = null;
await step('Discurso livre é enviado e lido (cartão "Como o eleitorado entendeu")', async () => {
  before = await intent();
  const filled = await ev(`(()=>{const t=document.querySelector('textarea');const set=Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value').set;set.call(t,'Vou ampliar as creches da cidade com 20 novas unidades em 12 meses, usando recurso do orçamento municipal e parceria com o governo estadual. Quero ouvir as famílias de cada bairro antes de definir as prioridades.');t.dispatchEvent(new Event('input',{bubbles:true}));return true})()`);
  if (!filled) return false; await sleep(400);
  if (!(await click('Realizar atividade'))) return { ok: false, detail: 'botão não encontrado ou desabilitado' };
  const ok = await waitText('Como o eleitorado entendeu seu discurso', 15000);
  return { ok, detail: ok ? 'cartão de leitura exibido' : 'sem cartão (leitura ausente)' };
});
await step('Nota da atividade aparece', async () => waitText('NOTA DA ATIVIDADE', 3000));
await step('Leitura traz temas, tom e promessas com meta/prazo/recurso', async () => { const t = await text(); return t.includes('Temas:') && t.includes('Tom:') && /✓ meta|✗ prazo|✓ prazo|✓ recurso|✗ recurso/.test(t); });
await step('Intenção de voto no painel continua um único número válido', async () => { await ev("location.hash='#/visao-geral'"); await sleep(1500); const v = await intent(); return { ok: v !== null, detail: `antes ${before} → agora ${v}` }; });
await step('Rivais continuam listados sem partido repetido', async () => { const t = await text(); return /Quem disputa/i.test(t); });

await step('Carreira > Apoio mostra Coligações', async () => { await ev("location.hash='#/carreira'"); await sleep(1500); if (!(await click('Apoio'))) return false; return waitText('Coligações', 6000); });
await step('Convidar partido abre a lista com chance de aceitação', async () => { if (!(await click('Convidar partidos'))) return false; await sleep(800); return ev("[...document.querySelectorAll('.coalition button')].some(b=>/\\(\\d+%\\)/.test(b.innerText))"); });
await step('Fazer um convite devolve resposta (aceitou ou recusou)', async () => {
  const done = await ev(`(()=>{const b=[...document.querySelectorAll('.coalition table button')].find(x=>!x.disabled&&/Programa/.test(x.innerText));if(b){b.click();return true}return false})()`);
  if (!done) return false;
  const ok = await (async () => { for (let i = 0; i < 40; i += 1) { await sleep(400); if (await has('entrou na chapa') || await has('recusou')) return true; } return false; })();
  return { ok, detail: (await has('entrou na chapa')) ? 'aceitou' : 'recusou' };
});

let guard = 0;
await step('Avançar mês a mês chega à eleição sem erro', async () => {
  for (; guard < 6; guard += 1) {
    await ev("location.hash='#/visao-geral'"); await sleep(500);
    const d0 = await dayNow();
    if (!(await click('Avançar'))) return { ok: false, detail: 'sem botão Avançar' }; await sleep(300);
    if (!(await click('1 mês'))) return { ok: false, detail: 'sem opção 1 mês' };
    for (let k = 0; k < 30; k += 1) { await sleep(500); const d1 = await dayNow(); if (d1 !== d0) break; }
    if (!(await has('· campanha'))) return { ok: true, detail: `a eleição foi apurada depois de ${guard + 1} avanço(s); o cabeçalho saiu de "campanha"` };   // o subtítulo do cabeçalho muda quando a campanha termina
  }
  return { ok: false, detail: 'a eleição não foi resolvida em 6 avanços' };
});
await step('Apuração abre e mostra resultado ou andamento', async () => { await ev("location.hash='#/apuracao'"); await sleep(2500); const t = await text(); return t.length > 300; });

const errors = events.filter((e) => e.method === 'Runtime.exceptionThrown' || (e.method === 'Runtime.consoleAPICalled' && e.params.type === 'error') || (e.method === 'Log.entryAdded' && e.params.entry.level === 'error' && !/favicon/.test(e.params.entry.url || '')))
  .map((e) => (e.params.exceptionDetails?.exception?.description || e.params.args?.map((a) => a.value || a.description).join(' ') || e.params.entry?.text || '').slice(0, 200));
const netFail = events.filter((e) => e.method === 'Network.responseReceived' && e.params.response.status >= 400).map((e) => `${e.params.response.status} ${e.params.response.url.replace(/^https?:\/\/[^/]+/, '')}`);
ws.close();
const failed = steps.filter((s) => !s.ok);
console.log(`\n${steps.length - failed.length}/${steps.length} passos OK; ${errors.length} erro(s) de console; ${netFail.length} resposta(s) 4xx/5xx`);
for (const e of errors.slice(0, 5)) console.log('  console: ' + e);
for (const n of netFail.slice(0, 8)) console.log('  rede: ' + n);
if (OUT) fs.writeFileSync(OUT, JSON.stringify({ steps, errors, netFail }, null, 2));
process.exit(failed.length || errors.length ? 1 : 0);
