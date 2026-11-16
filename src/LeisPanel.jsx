import { useEffect, useMemo, useState } from 'react';
import { Page, Section, Badge, Empty, Drawer } from './ui.jsx';

const TONE = { 'Regime militar': 'bad', Transição: 'warn', Democracia: 'good', Economia: '', Integridade: 'warn', Crise: 'bad', Instituições: 'warn' };

function Normas({ request, onGo }) {
  const [data, setData] = useState(null);
  const [q, setQ] = useState('');
  const [tipo, setTipo] = useState('Todos');
  const [open, setOpen] = useState(null);
  const [shown, setShown] = useState(18);
  useEffect(() => { request('/api/knowledge/laws').then(setData).catch(() => setData({ normas: [], tipos: [], total: 0, aviso: '' })); }, []);
  useEffect(() => { setShown(18); }, [q, tipo]);
  const list = useMemo(() => (data?.normas || []).filter((n) => (tipo === 'Todos' || n.tipo === tipo)
    && (!q || `${n.citacao} ${n.nome} ${n.assunto} ${n.resumo}`.toLowerCase().includes(q.toLowerCase()))), [data, q, tipo]);
  if (!data) return <Empty title="Carregando…" />;
  return <>
    <div className="ds-inv-filters">
      <div className="ds-seg" role="tablist" aria-label="Tipo de norma">{['Todos', ...data.tipos].map((t) => <button key={t} type="button" role="tab" aria-selected={tipo === t} className={tipo === t ? 'on' : ''} onClick={() => setTipo(t)}>{t}</button>)}</div>
      <label className="ds-search"><input aria-label="Buscar norma" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Buscar norma, assunto ou número" /></label>
    </div>
    {list.length === 0 ? <Empty title="Nada encontrado">Troque o filtro ou a busca.</Empty> : <>
      <div className="pj-grid">{list.slice(0, shown).map((n) => <button key={n.id} type="button" className="pj-card ds-law" onClick={() => setOpen(n)}>
        <div className="pj-body"><small>{n.tipo} · {n.ano}</small><b>{n.nome}</b><small>{n.assunto}</small>
          {n.acoes.length > 0 && <div className="pj-tags"><Badge tone="good">usada em {n.acoes.length} {n.acoes.length === 1 ? 'ação' : 'ações'}</Badge></div>}</div>
      </button>)}</div>
      {list.length > shown && <button type="button" className="secondary-button" onClick={() => setShown(shown + 18)}>Mostrar mais ({list.length - shown} restantes)</button>}
    </>}
    <p className="ds-hint">{data.aviso}</p>
    {open && <Drawer title={open.nome} onClose={() => setOpen(null)} footer={<a className="primary-button" href={open.busca} target="_blank" rel="noreferrer noopener">Buscar o texto oficial no LexML</a>}>
      <p>{open.resumo}</p>
      <dl className="pj-facts"><dt>Norma</dt><dd>{open.citacao}</dd><dt>Tipo</dt><dd>{open.tipo}, de {open.ano}</dd><dt>Assunto</dt><dd>{open.assunto}</dd></dl>
      <h4 className="subheading">No jogo</h4>
      {open.acoes.length ? <ul className="ds-list">{open.acoes.map((a) => <li key={a.id}>Base legal da ação: {a.title}</li>)}</ul>
        : <p className="ds-muted">Esta norma é referência de contexto. Ainda não é base legal de nenhuma ação do jogo.</p>}
    </Drawer>}
  </>;
}

function Linha({ request, onGo }) {
  const [data, setData] = useState(null);
  const [cat, setCat] = useState('Todas');
  useEffect(() => { request('/api/knowledge/memory').then(setData).catch(() => setData({ fatos: [], categorias: [], aviso: '' })); }, []);
  if (!data) return <Empty title="Carregando…" />;
  const fatos = data.fatos.filter((f) => cat === 'Todas' || f.categoria === cat);
  return <>
    <div className="ds-seg" role="tablist" aria-label="Categoria">{['Todas', ...data.categorias].map((c) => <button key={c} type="button" role="tab" aria-selected={cat === c} className={cat === c ? 'on' : ''} onClick={() => setCat(c)}>{c}</button>)}</div>
    <ol className="ds-timeline">
      {fatos.map((f) => <li key={f.ano + f.titulo}>
        <span className="ds-timeline-year">{f.ano}</span>
        <div><b>{f.titulo}</b> <Badge tone={TONE[f.categoria] || ''}>{f.categoria}</Badge>
          <p>{f.resumo}</p>
          {f.acoes.length > 0 && <p className="ds-hint">No jogo: {f.acoes.map((a) => a.title).join(' · ')}.</p>}
        </div>
      </li>)}
    </ol>
    <p className="ds-hint">{data.aviso}</p>
  </>;
}

export default function LeisPanel({ request }) {
  const [view, setView] = useState('Normas');
  return <Page title="Leis e história" lead="As normas que dão a régua do jogo e a memória do país que o motor usa nas decisões.">
    <div className="ds-seg" role="tablist" aria-label="Seção">{['Normas', 'Linha do tempo'].map((v) => <button key={v} type="button" role="tab" aria-selected={view === v} className={view === v ? 'on' : ''} onClick={() => setView(v)}>{v}</button>)}</div>
    <Section>{view === 'Normas' ? <Normas request={request} /> : <Linha request={request} />}</Section>
  </Page>;
}
