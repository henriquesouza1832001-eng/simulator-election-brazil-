// Rastreador de interface: percorre as telas de uma partida em desktop e celular e mede o que costuma quebrar.
// Uso: node tools/ui-crawler.mjs <idDaPartida> <rotulo> <rota1,rota2,...> [saida.json]
// Requer Chrome com --remote-debugging-port=9222 e o front em http://localhost:5179 (vite) com o backend em 8000.
import fs from 'node:fs';

const [CID, LABEL, ROUTES, OUT] = process.argv.slice(2);
const BASE = process.env.UI_BASE || 'http://localhost:5179/';
const VIEWPORTS = [{ name: 'desktop', width: 1366, height: 900, mobile: false }, { name: 'celular', width: 390, height: 844, mobile: true }];
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const BAD_TEXT = /undefined|NaN|\[object|Infinity|null%|\{\{|%s\b|\bnull\b(?! )/;

const tab = await (await fetch('http://127.0.0.1:9222/json/new?about:blank', { method: 'PUT' })).json();
const ws = new WebSocket(tab.webSocketDebuggerUrl);
await new Promise((r) => (ws.onopen = r));
let nextId = 0; const pending = new Map(); let events = [];
ws.onmessage = (m) => {
  const d = JSON.parse(m.data);
  if (d.id && pending.has(d.id)) { pending.get(d.id)(d); pending.delete(d.id); } else if (d.method) events.push(d);
};
const send = (method, params = {}) => new Promise((r) => { const id = ++nextId; pending.set(id, r); ws.send(JSON.stringify({ id, method, params })); });
const evaluate = async (expression) => (await send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true })).result?.result?.value;
await send('Page.enable'); await send('Runtime.enable'); await send('Network.enable'); await send('Log.enable');

const probe = `(() => {
  const main = document.querySelector('main') || document.body;
  const text = main.innerText || '';
  const bad = (text.match(${BAD_TEXT.toString()}g) || []).slice(0, 5);
  const noName = [...document.querySelectorAll('button, a[role=button], [role=tab]')].filter((b) => { const r = b.getBoundingClientRect(); return r.width > 0 && r.height > 0 && !(b.innerText || b.textContent || '').trim() && !b.getAttribute('aria-label') && !b.getAttribute('title'); }).length;
  const broken = [...document.images].filter((i) => i.complete && i.naturalWidth === 0).map((i) => i.src.slice(-60)).slice(0, 5);
  const small = [...document.querySelectorAll('button, a')].filter((b) => { const r = b.getBoundingClientRect(); return r.width > 0 && r.height > 0 && (r.height < 30 || r.width < 30) && (b.innerText || '').trim(); }).length;
  const wide = document.documentElement.scrollWidth - window.innerWidth;
  const offenders = wide > 2 ? [...document.querySelectorAll('main *')].filter((e) => e.getBoundingClientRect().right > window.innerWidth + 2).slice(0, 3).map((e) => e.tagName + '.' + String(e.className).slice(0, 40)) : [];
  return { chars: text.length, loading: /Carregando|Preparando o gabinete/.test(text), bad, noName, broken, small, wide, offenders, empty: text.trim().length < 60 };
})()`;

const report = { label: LABEL, cid: CID, when: new Date().toISOString(), routes: [] };
for (const vp of VIEWPORTS) {
  await send('Emulation.setDeviceMetricsOverride', { width: vp.width, height: vp.height, deviceScaleFactor: 1, mobile: vp.mobile });
  await send('Page.navigate', { url: BASE }); await sleep(1200);
  await evaluate(`localStorage.setItem('mandato.activeCampaign','${CID}')`);
  await send('Page.navigate', { url: BASE }); await sleep(6500);
  await evaluate("(()=>{const b=[...document.querySelectorAll('button')].find(x=>x.innerText.trim().startsWith('Continuar'));if(b)b.click()})()"); await sleep(3000);
  for (const slug of ROUTES.split(',')) {
    events = [];
    const t0 = Date.now();
    await evaluate(`location.hash='#/${slug}'`);
    let m = null;
    for (let i = 0; i < 16; i += 1) { await sleep(400); m = await evaluate(probe); if (m && !m.loading && !m.empty) break; }
    const renderMs = Date.now() - t0;
    const consoleErrors = events.filter((e) => (e.method === 'Runtime.exceptionThrown') || (e.method === 'Runtime.consoleAPICalled' && ['error'].includes(e.params.type)) || (e.method === 'Log.entryAdded' && e.params.entry.level === 'error' && !/favicon/.test(e.params.entry.url || ''))).map((e) => (e.params.exceptionDetails?.exception?.description || e.params.args?.map((a) => a.value || a.description).join(' ') || e.params.entry?.text || '').slice(0, 160));
    const netFail = events.filter((e) => e.method === 'Network.responseReceived' && e.params.response.status >= 400).map((e) => `${e.params.response.status} ${e.params.response.url.replace(/^https?:\/\/[^/]+/, '')}`.slice(0, 110));
    const netDead = events.filter((e) => e.method === 'Network.loadingFailed' && !e.params.canceled).map((e) => e.params.errorText).slice(0, 3);
    const present = await evaluate("document.querySelector('main') ? location.hash : 'sem main'");
    report.routes.push({ viewport: vp.name, slug, hash: present, renderMs, ...m, consoleErrors, netFail, netDead });
  }
}
ws.close();

const problems = [];
for (const r of report.routes) {
  const where = `${r.viewport}/${r.slug}`;
  if (r.consoleErrors.length) problems.push(`${where}: erro de console: ${r.consoleErrors[0]}`);
  if (r.netFail.length) problems.push(`${where}: rede ${r.netFail[0]}`);
  if (r.netDead.length) problems.push(`${where}: requisição morta ${r.netDead[0]}`);
  if (r.bad?.length) problems.push(`${where}: texto quebrado ${JSON.stringify(r.bad)}`);
  if (r.loading) problems.push(`${where}: ficou em "Carregando"`);
  if (r.empty) problems.push(`${where}: tela praticamente vazia (${r.chars} caracteres)`);
  if (r.wide > 2) problems.push(`${where}: rolagem lateral de ${r.wide}px em ${r.offenders.join(', ')}`);
  if (r.noName) problems.push(`${where}: ${r.noName} botão(ões) sem nome acessível`);
  if (r.broken?.length) problems.push(`${where}: imagem quebrada ${r.broken[0]}`);
  if (r.renderMs > 4000) problems.push(`${where}: demorou ${r.renderMs} ms para renderizar`);
  if (r.viewport === 'celular' && r.small > 6) problems.push(`${where}: ${r.small} alvos de toque menores que 30px`);
}
report.problems = problems;
if (OUT) fs.writeFileSync(OUT, JSON.stringify(report, null, 2));
const slow = report.routes.filter((r) => r.renderMs > 2500).length;
console.log(`${LABEL}: ${report.routes.length} telas medidas, ${problems.length} problema(s), ${slow} lenta(s)`);
for (const p of problems) console.log(' - ' + p);
