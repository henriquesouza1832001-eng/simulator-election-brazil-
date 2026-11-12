import { useEffect, useMemo, useState } from 'react';
import './powers.css';

const OPTIONS = [
  ['aprovacao', 'Aprovação', '%'], ['inflacao', 'Inflação', '% a.a.'], ['desemprego', 'Desemprego', '%'], ['divida_pib', 'Dívida', '% do PIB'],
  ['resultado_primario', 'Resultado primário', '% do PIB'], ['crescimento_pib', 'Crescimento do PIB', '%'], ['gini', 'Gini', ''], ['pobreza', 'Pobreza', '%'],
  ['base_legislativa', 'Base no Congresso', '%'], ['confianca_institucional', 'Confiança institucional', ''], ['integridade', 'Integridade', ''],
];

function Spark({ values }) {
  const pts = values.filter((v) => Number.isFinite(v));
  if (pts.length < 2) return <svg className="spark" viewBox="0 0 120 32" preserveAspectRatio="none" role="img" aria-label="Sem série suficiente"><line x1="0" y1="16" x2="120" y2="16" stroke="currentColor" strokeOpacity=".3" /></svg>;
  const min = Math.min(...pts), max = Math.max(...pts), span = max - min || 1;
  const d = pts.map((v, i) => `${i ? 'L' : 'M'}${(i / (pts.length - 1)) * 120},${30 - ((v - min) / span) * 28}`).join(' ');
  return <svg className="spark" viewBox="0 0 120 32" preserveAspectRatio="none" role="img" aria-label={`De ${pts[0]} a ${pts[pts.length - 1]}`}><path d={d} fill="none" stroke="currentColor" strokeWidth="2" vectorEffect="non-scaling-stroke" /></svg>;
}

export default function HistoryPanel({ request, state }) {
  const [picked, setPicked] = useState(['aprovacao', 'inflacao', 'desemprego', 'divida_pib']);
  const [series, setSeries] = useState(null);
  const [ledger, setLedger] = useState([]);
  const [error, setError] = useState('');
  const keys = useMemo(() => picked.join(','), [picked]);

  useEffect(() => { request(`/api/indicators/nation/history?keys=${keys}`).then((r) => setSeries(r.series)).catch((e) => setError(e.message)); }, [keys, state?.date]);
  useEffect(() => { request('/api/ledger').then((r) => setLedger(r.entries || [])).catch(() => {}); }, [state?.date]);

  if (error) return <section className="panel"><p className="meta-status meta-error" role="alert">{error}</p></section>;
  const toggle = (k) => setPicked((p) => (p.includes(k) ? p.filter((x) => x !== k) : [...p, k].slice(-8)));
  const fmt = (v) => (Number.isFinite(v) ? Number(v).toLocaleString('pt-BR', { maximumFractionDigits: 2 }) : '—');

  return <section className="panel powers-page">
    <h2>Histórico do mandato</h2>
    <p className="page-description">Série mensal dos indicadores nacionais desde o início da partida e o que você decidiu em cada período.</p>
    <div className="powers-filter" role="group" aria-label="Indicadores">{OPTIONS.map(([k, l]) => <button key={k} className={picked.includes(k) ? 'meta-tab active' : 'meta-tab'} aria-pressed={picked.includes(k)} onClick={() => toggle(k)}>{l}</button>)}</div>
    {!series ? <p className="meta-status" role="status">Carregando…</p> : series.length < 2 ? <p className="meta-status">A série começa a ser registrada depois do primeiro mês. Avance o calendário.</p>
      : <ul className="history-grid">{OPTIONS.filter(([k]) => picked.includes(k)).map(([k, l, u]) => {
        const vals = series.map((s) => s[k]);
        const first = vals.find((v) => Number.isFinite(v)), last = [...vals].reverse().find((v) => Number.isFinite(v));
        return <li key={k}><span>{l}</span><b>{fmt(last)}<small> {u}</small></b><Spark values={vals} /><small>{series[0].month} a {series[series.length - 1].month} · {last - first >= 0 ? '+' : ''}{fmt(last - first)} no período</small></li>;
      })}</ul>}
    <h3 className="subheading">Decisões e resultados</h3>
    {ledger.length === 0 ? <p className="meta-status">Nenhuma decisão registrada ainda.</p> : <ul className="meta-notes ledger-brief">{ledger.slice(0, 25).map((e) => <li key={e.id}><b>{e.date}</b> — {e.title} <small>({e.status}{e.cost ? ` · ${e.cost}` : ''})</small></li>)}</ul>}
  </section>;
}
