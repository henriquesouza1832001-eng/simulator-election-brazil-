import { useEffect, useState } from 'react';
import './powers.css';

const STATUS = { suspenso: 'Suspenso', mantido: 'Mantido', aberto: 'Aberto', 'com ressalvas': 'Com ressalvas' };

export default function RegulatorsPanel({ request, state }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  useEffect(() => { request('/api/regulators').then(setData).catch((e) => setError(e.message)); }, [state?.date]);

  if (error) return <section className="panel"><p className="meta-status meta-error" role="alert">{error}</p></section>;
  if (!data) return <section className="panel"><p className="meta-status" role="status">Carregando…</p></section>;

  return <section className="panel powers-page">
    <h2>Reguladores e controle</h2>
    <p className="page-description">Nenhum cargo age sozinho. Estes órgãos avaliam, limitam e investigam o que você faz. {data.note}</p>
    <ul className="powers-list">{data.regulators.map((r) => <li key={r.id}><div>
      <b>{r.name}</b>
      <small>{r.role}</small>
      <small className="powers-meta">Pode: {r.can.join('; ')}.</small>
      <small className="powers-meta">Não pode: {r.cannot.join('; ')}.</small>
      <small className="meta-count">Base: {r.basis}</small>
      {r.id === 'stf' && <small className="powers-effects">Alinhamento com o governo: {Math.round(r.alignment * 100)}% (cresce com ministros que você indica e o Senado confirma) · processos abertos: {r.open_cases.length}</small>}
      {r.id === 'stf' && r.open_cases.length > 0 && <small>Em julgamento: {r.open_cases.map((c) => `${c.title} (decisão até ${c.decide_on}, risco ${Math.round(c.risk * 100)}%)`).join('; ')}.</small>}
      {r.id === 'tse' && (r.conduct ? <small className="powers-effects">Sua campanha: {r.conduct.attempts} conduta(s) irregular(es) tentada(s), {r.conduct.detected} detectada(s), penalidade de votos {r.conduct.vote_penalty}.</small> : <small className="meta-count">Atua nas campanhas de carreira; sem campanha ativa agora.</small>)}
    </div></li>)}</ul>
    {data.decisions.length > 0 && <><h3 className="subheading">Decisões recentes</h3>
      <ul className="meta-notes">{data.decisions.map((d) => <li key={d.id}>{d.decided || d.filed} — {d.title}: <b>{STATUS[d.status] || d.status}</b>{d.chance_pct != null ? ` (risco de suspensão era ${d.chance_pct}%)` : ''}</li>)}</ul></>}
  </section>;
}
