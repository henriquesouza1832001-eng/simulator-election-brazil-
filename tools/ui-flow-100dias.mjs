// Fluxo de ponta a ponta pela interface real: cenário "100 dias" do botão inicial até o balanço.
// Uso: node tools/ui-flow-100dias.mjs [saida.json]   (Chrome na porta 9222, vite em 5179 e backend em 8000)
import fs from 'node:fs';

const OUT = process.argv[2];
const BASE = process.env.UI_BASE || 'http://localhost:5179/';
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const tab = await (await fetch('http://127.0.0.1:9222/json/new?about:blank', { method: 'PUT' })).json();
const ws = new WebSocket(tab.webSocketDebuggerUrl);
await new Promise((r) => (ws.onopen = r));
let nextId = 0; const pending = new Map(); let events = []; let dialogs = 0;
const send = (method, params = {}) => new Promise((r) => { const id = ++nextId; pending.set(id, r); ws.send(JSON.stringify({ id, method, params })); });
ws.onmessage = (m) => {
  const d = JSON.parse(m.data);
  if (d.id && pending.has(d.id)) { pending.get(d.id)(d); pending.delete(d.id); }
  else if (d.method === 'Page.javascriptDialogOpening') { dialogs += 1; send('Page.handleJavaScriptDialog', { accept: true }); }
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
const dayNow = async () => { const m = (await text()).match(/DIA (\d+) DE 1461/); return m ? Number(m[1]) : 0; };
const click = (label, root = 'document') => ev(`(()=>{const b=[...${root}.querySelectorAll('button,a')].find(x=>x.offsetParent&&x.innerText.trim().startsWith(${JSON.stringify(label)}));if(b){b.click();return true}return false})()`);
const waitText = async (needle, ms = 8000) => { const t0 = Date.now(); while (Date.now() - t0 < ms) { if ((await text()).toLowerCase().includes(needle.toLowerCase())) return true; await sleep(300); } return false; };

await send('Page.navigate', { url: BASE }); await sleep(1500);
await ev('localStorage.clear(); sessionStorage.clear()');
await send('Page.navigate', { url: BASE }); await sleep(5500);

await step('Tela inicial mostra o botão do cenário', async () => (await text()).includes('Os primeiros 100 dias'));
await step('Clicar em "Jogar agora" cria a partida', async () => { if (!(await click('Jogar agora'))) return false; return waitText('Pronunciamento de posse', 12000); });
await step('Pronunciamento de posse é aceito', async () => {
  const filled = await ev(`(()=>{const t=document.querySelector('.inaugural-card textarea');if(!t)return false;const set=Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value').set;set.call(t,'Assumo o governo com compromisso com a responsabilidade fiscal, o diálogo com o Congresso e a proteção dos mais vulneráveis. Vamos priorizar saúde, educação e emprego, prestar contas todo mês e respeitar as instituições.');t.dispatchEvent(new Event('input',{bubbles:true}));return true})()`);
  if (!filled) return { ok: false, detail: 'campo não encontrado' };
  await sleep(300);
  const sent = await ev(`(()=>{const f=document.querySelector('.inaugural-card');const b=f&&[...f.querySelectorAll('button')].find(x=>x.type==='submit'||/Registrar|Enviar|Fazer|Confirmar/.test(x.innerText));if(b){b.click();return true}return false})()`);
  if (!sent) return { ok: false, detail: 'botão de envio não encontrado' };
  const gone = await (async () => { for (let i = 0; i < 20; i += 1) { await sleep(400); if (!(await ev("!!document.querySelector('.inaugural-card')"))) return true; } return false; })();
  return { ok: gone, detail: gone ? '' : 'o modal não fechou' };
});
await step('Painel mostra o cenário e a mesa de despacho', async () => { const t = await text(); return t.includes('Os primeiros 100 dias') && t.includes('Mesa de despacho'); });
await step('Metas aparecem com os números iniciais', async () => (await text()).includes('44,0% agora') || (await text()).includes('44,'));

await step('Avançar "1 mês" muda a data', async () => {
  const before = await dayNow();
  if (!(await click('Avançar'))) return { ok: false, detail: 'botão Avançar não achado' };
  await sleep(400);
  if (!(await click('1 mês'))) return { ok: false, detail: 'opção "1 mês" não achada' };
  for (let i = 0; i < 24; i += 1) { await sleep(500); const now = await dayNow(); if (now > before) return { ok: true, detail: `dia ${before} → ${now}` }; }
  return { ok: false, detail: `a data ficou em ${before}` };
});
await step('"Por que mudou?" aparece depois de avançar', async () => waitText('Por que mudou?', 6000));
await step('Botão "Abrir" da mesa leva a outra tela', async () => {
  const before = await ev('location.hash');
  await ev(`(()=>{const sec=document.querySelector('.ds-despacho:last-of-type')||document.querySelector('[aria-label="Mesa de despacho"]');const b=sec&&[...sec.querySelectorAll('button')].find(x=>x.innerText.trim()==='Abrir');if(b)b.click()})()`);
  await sleep(1500); const after = await ev('location.hash');
  return { ok: before !== after, detail: `${before} → ${after}` };
});
await step('Orçamento mostra as alavancas fiscais', async () => { await ev("location.hash='#/orcamento'"); for (let i = 0; i < 25; i += 1) { await sleep(400); if (await ev("document.querySelectorAll('.lever-card button').length > 0")) return true; } return false; });
await step('Aplicar uma alavanca fiscal (com confirmação) entra em vigor', async () => {
  const clicked = await ev(`(()=>{const b=[...document.querySelectorAll('.lever-card button')].find(x=>!x.disabled);if(b){b.click();return true}return false})()`);
  if (!clicked) return { ok: false, detail: 'nenhum botão disponível' };
  const ok = await waitText('em vigor', 8000);
  return { ok, detail: `diálogos de confirmação aceitos: ${dialogs}` };
});
await step('Segunda alavanca é bloqueada pelo intervalo de 60 dias', async () => { await sleep(500); return ev(`!![...document.querySelectorAll('.lever-card button')].every(x=>x.disabled)`); });

await step('Tramitação abre sem erro', async () => { await ev("location.hash='#/tramitacao'"); return waitText('Tramitação no Congresso', 6000); });
await step('Medidas: texto livre é interpretado e simulado', async () => {
  await ev("location.hash='#/medidas'"); await sleep(1200);
  const typed = await ev(`(()=>{const t=document.querySelector('#measure');if(!t)return false;const set=Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value').set;set.call(t,'Reduzir em 10% as despesas com viagens e eventos do governo e usar a economia para ampliar o atendimento nos postos de saúde, com prestação de contas trimestral.');t.dispatchEvent(new Event('input',{bubbles:true}));return true})()`);
  if (!typed) return { ok: false, detail: 'campo de medida não encontrado' };
  await sleep(300);
  if (!(await click('Interpretar e simular'))) return { ok: false, detail: 'botão desabilitado ou ausente' };
  for (let i = 0; i < 60; i += 1) { await sleep(500); if (await ev("!![...document.querySelectorAll('button')].find(b=>b.innerText.trim().startsWith('Aplicar medida'))")) return { ok: true, detail: `prévia em ${(i + 1) * 0.5}s` }; }
  return { ok: false, detail: 'a prévia não apareceu em 30s' };
});
await step('Medidas: aplicar a medida registra o efeito', async () => {
  if (!(await click('Aplicar medida'))) return false;
  for (let i = 0; i < 30; i += 1) { await sleep(400); if (!(await ev("!![...document.querySelectorAll('button')].find(b=>b.innerText.trim().startsWith('Aplicar medida'))"))) return true; }
  return { ok: false, detail: 'o botão continuou na tela' };
});
await step('Mercado mostra manchetes', async () => { await ev("location.hash='#/mercado'"); return waitText('POR QUE O MERCADO ESTÁ ASSIM', 6000); });

for (let i = 0; i < 3; i += 1) {
  await step(`Avançar mais um mês (${i + 2}º) muda a data`, async () => {
    await ev("location.hash='#/visao-geral'"); await sleep(600);
    const before = await dayNow();
    if (!(await click('Avançar'))) return false; await sleep(300); if (!(await click('1 mês'))) return false;
    for (let k = 0; k < 24; k += 1) { await sleep(500); const now = await dayNow(); if (now > before) return { ok: true, detail: `dia ${before} → ${now}` }; }
    return { ok: false, detail: `a data ficou em ${before}` };
  });
}
await step('No 100º dia aparece o balanço do cenário', async () => {
  await ev("location.hash='#/visao-geral'");
  const ok = await waitText('Balanço dos 100 dias', 6000);
  return { ok, detail: ok ? (await ev("document.querySelector('[aria-label=\"Balanço dos 100 dias\"] h3')?.innerText || ''")) : 'balanço não apareceu' };
});

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
