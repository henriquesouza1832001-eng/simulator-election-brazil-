// Uso: CAMPAIGN_ID=<id da partida> node tools/contrast-audit.mjs "Visão geral" "Indicadores" ...
// Precisa do site em http://localhost:5179 (vite com API_URL) e de um Chrome com --remote-debugging-port=9222.
// Auditoria de contraste: percorre as abas e lista textos com contraste menor que o mínimo (WCAG AA 4.5, ou 3 para texto grande).
const WEB = 'http://localhost:5179';
const tabs = process.argv.slice(2);
const tab = await (await fetch('http://127.0.0.1:9222/json/new?about:blank', { method: 'PUT' })).json();
const ws = new WebSocket(tab.webSocketDebuggerUrl); await new Promise((r) => (ws.onopen = r));
let id = 0; const pending = new Map();
ws.onmessage = (m) => { const d = JSON.parse(m.data); if (d.id && pending.has(d.id)) { pending.get(d.id)(d); pending.delete(d.id); } };
const send = (method, params = {}) => new Promise((r) => { const i = ++id; pending.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
const ev = async (e) => (await send('Runtime.evaluate', { expression: e, awaitPromise: true, returnByValue: true })).result?.result?.value;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
await send('Runtime.enable'); await send('Page.enable');
await send('Emulation.setDeviceMetricsOverride', { width: 1280, height: 900, deviceScaleFactor: 1, mobile: false });
await send('Page.navigate', { url: WEB + '/' }); await sleep(1500);
await ev(`localStorage.setItem('mandato.activeCampaign', '${process.env.CAMPAIGN_ID}')`);
await send('Page.navigate', { url: WEB + '/' }); await sleep(3500);
await ev("(()=>{const b=[...document.querySelectorAll('button')].find(x=>x.innerText.trim().startsWith('Continuar'));if(b)b.click()})()"); await sleep(1500);

const AUDIT = `(() => {
  const parse = (s) => { const m = s.match(/rgba?\\(([^)]+)\\)/); if (!m) return null; const p = m[1].split(/[ ,\\/]+/).filter(Boolean).map(Number); return { r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1 }; };
  const over = (top, bottom) => ({ r: top.r * top.a + bottom.r * (1 - top.a), g: top.g * top.a + bottom.g * (1 - top.a), b: top.b * top.a + bottom.b * (1 - top.a), a: 1 });
  const lum = (c) => { const f = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }; return 0.2126 * f(c.r) + 0.7152 * f(c.g) + 0.0722 * f(c.b); };
  const bgOf = (el) => {
    const layers = [];
    for (let e = el; e; e = e.parentElement) {
      const cs = getComputedStyle(e);
      let c = parse(cs.backgroundColor);
      if ((!c || c.a === 0) && cs.backgroundImage && cs.backgroundImage !== 'none' && cs.backgroundImage.includes('gradient')) { c = parse(cs.backgroundImage); }
      if (c && c.a > 0) { layers.push(c); if (c.a >= 0.99) break; }
    }
    let base = { r: 10, g: 17, b: 21, a: 1 };
    for (let i = layers.length - 1; i >= 0; i--) base = over(layers[i], base);
    return base;
  };
  const out = new Map();
  const walker = document.createTreeWalker(document.querySelector('#root') || document.body, NodeFilter.SHOW_TEXT);
  let n;
  while ((n = walker.nextNode())) {
    const text = n.nodeValue.trim(); if (text.length < 2) continue;
    const el = n.parentElement; if (!el || el.closest('script,style')) continue;
    const cs = getComputedStyle(el); if (cs.visibility === 'hidden' || cs.display === 'none' || Number(cs.opacity) === 0) continue;
    const r = el.getBoundingClientRect(); if (r.width === 0 || r.height === 0) continue;
    const fg = parse(cs.color); if (!fg) continue;
    const bg = bgOf(el); const f = over({ ...fg, a: fg.a * Number(cs.opacity) }, bg);
    const l1 = lum(f), l2 = lum(bg); const ratio = (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
    const size = parseFloat(cs.fontSize), bold = Number(cs.fontWeight) >= 700;
    const need = (size >= 24 || (size >= 18.66 && bold)) ? 3 : 4.5;
    if (ratio < need) {
      const cls = [...el.classList].slice(0, 2).join('.'); const par = el.parentElement ? [...el.parentElement.classList].slice(0, 2).join('.') : '';
      const key = el.tagName.toLowerCase() + (cls ? '.' + cls : '') + ' < ' + (par || el.parentElement?.tagName.toLowerCase());
      const e = out.get(key) || { key, n: 0, ratio: 99, sample: '', fg: cs.color, bg: 'rgb(' + [bg.r, bg.g, bg.b].map(Math.round).join(',') + ')' };
      e.n++; if (ratio < e.ratio) { e.ratio = Number(ratio.toFixed(2)); e.sample = text.slice(0, 50); } out.set(key, e);
    }
  }
  return [...out.values()];
})()`;

const all = new Map();
for (const t of tabs) {
  const slug = t.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');   // mesmo endereço de tela do HashRoute
  const ok = await ev(`(()=>{location.hash='#/${slug}';return true})()`);
  await sleep(1400);
  // abre todos os <details> para auditar também o conteúdo recolhido
  await ev("document.querySelectorAll('details').forEach(d=>d.open=true)"); await sleep(300);
  const rows = await ev(AUDIT);
  if (!ok) console.log(`[${t}] aba não encontrada`);
  for (const r of rows || []) { const k = r.key; const e = all.get(k) || { ...r, tabs: new Set(), n: 0 }; e.n += r.n; e.tabs.add(t); if (r.ratio < e.ratio) { e.ratio = r.ratio; e.sample = r.sample; e.bg = r.bg; e.fg = r.fg; } all.set(k, e); }
  console.log(`[${t}] ${rows?.length ?? 0} grupos com contraste baixo`);
}
const list = [...all.values()].sort((a, b) => a.ratio - b.ratio);
console.log('\nPIORES (razão  ocorrências  seletor  | exemplo | fg -> bg | abas)');
for (const r of list.slice(0, 60)) console.log(`${String(r.ratio).padEnd(5)} x${String(r.n).padEnd(4)} ${r.key} | "${r.sample}" | ${r.fg} -> ${r.bg} | ${[...r.tabs].slice(0, 3).join(',')}`);
console.log('\nTOTAL grupos:', list.length);
ws.close();
