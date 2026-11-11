import { useEffect, useState } from 'react';
import './powers.css';

const KIND = { imprensa: 'Imprensa', congresso: 'Congresso', mercado: 'Mercado', crise: 'Crise', regulador: 'Regulador', resposta: 'Resposta do governo' };
const EFFECT = { approval: 'aprovação', trust: 'confiança', integrity: 'integridade', governability: 'governabilidade', congress_support: 'base no Congresso', institutional_trust: 'confiança institucional', gdp_growth: 'PIB', inflation: 'inflação', primary_balance: 'resultado primário' };
const text = (effects) => Object.entries(effects || {}).map(([k, v]) => `${v > 0 ? '+' : ''}${v} ${EFFECT[k] || k}`).join(' · ') || 'sem efeito direto';

export default function NewsPanel({ request, state, onState, onNotice }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const load = () => request('/api/consequences').then(setData).catch((e) => setError(e.message));
  useEffect(() => { load(); }, [state?.date]);

  async function answer(crisis, option) {
    try {
      const r = await request(`/api/consequences/${encodeURIComponent(crisis.id)}/respond?option=${encodeURIComponent(option.id)}`, { method: 'POST', body: '{}' });
      setData(r.overview);
      if (r.state) onState?.(r.state);
      onNotice?.(`Resposta registrada: ${option.label}. Efeitos: ${text(r.effects)}.`);
    } catch (e) { onNotice?.(e.message); }
  }

  if (error) return <section className="panel"><p className="meta-status meta-error" role="alert">{error}</p></section>;
  if (!data) return <section className="panel"><p className="meta-status" role="status">Carregando…</p></section>;

  return <section className="panel powers-page">
    <h2>Imprensa e reações</h2>
    <p className="page-description">Toda decisão importante gera notícias, reações de bancadas e do mercado, e às vezes uma crise. Reações são simuladas e usam só fatos do jogo.</p>

    {data.pending.length > 0 && <>
      <h3 className="subheading">Decisões que esperam resposta</h3>
      <ul className="powers-list">{data.pending.map((c) => <li key={c.id}><div>
        <b>{c.title}</b><small>{c.text}</small><small className="neg">Prazo: {c.deadline}. Sem resposta, vale a última opção.</small>
        <div className="crisis-options">{c.options.map((o, i) => <button key={o.id} className={i === c.options.length - 1 ? 'quiet-button' : 'secondary-button'} onClick={() => answer(c, o)}>{o.label}<small>{text(o.effects)}</small></button>)}</div>
      </div></li>)}</ul></>}

    <h3 className="subheading">Linha do tempo</h3>
    {data.feed.length === 0 ? <p className="meta-status">Nenhuma reação ainda. Tome uma decisão e acompanhe a repercussão nos dias seguintes.</p>
      : <ul className="powers-list">{data.feed.map((n) => <li key={n.id}><div>
        <small className="powers-meta"><span className="powers-kind">{KIND[n.kind] || n.kind}</span> {n.date}</small>
        <b>{n.headline}</b><small>{n.body}</small></div></li>)}</ul>}
    {data.scheduled > 0 && <p className="meta-count">{data.scheduled} reação(ões) ainda por vir.</p>}
  </section>;
}
