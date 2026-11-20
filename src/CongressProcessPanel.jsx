import { useEffect, useState } from 'react';
import './powers.css';
import './territory.css';
import { dataBr } from './format.js';

const STATUS = { concluída: 'concluída', aprovada: 'aprovada', rejeitada: 'rejeitada', pendente: 'a vir', 'dispensada (urgência)': 'dispensada (urgência)' };

export default function CongressProcessPanel({ request, state, onState, onNotice }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [open, setOpen] = useState({});
  const [cpis, setCpis] = useState([]);
  const load = () => request('/api/congress/process').then(setData).catch((e) => setError(e.message));
  useEffect(() => { load(); request('/api/cpi').then((r) => setCpis(r.cpis)).catch(() => setCpis([])); }, [state?.date]);

  async function negotiate(bill, party, offer) {
    try {
      const r = await request('/api/congress/negotiate', { method: 'POST', body: JSON.stringify({ bill: bill.id, party, offer }) });
      setData(r.overview); if (r.state) onState?.(r.state);
      onNotice?.(`Negociação com ${party} registrada${r.dilution < 1 ? `; texto com ${Math.round(r.dilution * 100)}% dos efeitos` : ''}.`);
    } catch (e) { onNotice?.(e.message); }
  }
  async function negotiateBloc(bill, bloc, offer) {
    try {
      const r = await request('/api/congress/negotiate-bloc', { method: 'POST', body: JSON.stringify({ bill: bill.id, bloc: bloc.id, offer }) });
      setData(r.overview); if (r.state) onState?.(r.state);
      onNotice?.(`Pacote fechado com o ${bloc.label} (líder: ${r.leader}, ${r.parties.length} ${r.parties.length === 1 ? 'partido' : 'partidos'}); o custo foi ${String(r.cost_factor).replace('.', ',')}× o de um partido só.`);
    } catch (e) { onNotice?.(e.message); }
  }
  async function urgency(bill) {
    try {
      const r = await request('/api/congress/urgency', { method: 'POST', body: JSON.stringify({ bill: bill.id }) });
      setData(r.overview); if (r.state) onState?.(r.state);
      onNotice?.(`Urgência pedida. Nova data de votação: ${dataBr(r.decision_date)}.`);
    } catch (e) { onNotice?.(e.message); }
  }

  if (error) return <section className="panel"><p className="meta-status meta-error" role="alert">{error}</p></section>;
  if (!data) return <section className="panel"><p className="meta-status" role="status">Carregando…</p></section>;

  return <section className="panel powers-page">
    <h2>Tramitação no Congresso</h2>
    <p className="page-description">{data.note}</p>
    {data.bills.length === 0 && cpis.length === 0 && (!data.local_bills || data.local_bills.length === 0) && <p className="meta-status">Nenhum projeto em tramitação com etapas. Envie um projeto pela aba Competências.</p>}
    {cpis.length > 0 && <>
      <h3 className="subheading">CPIs</h3>
      {cpis.map((c) => <article className="bill-card" key={c.id}>
        <h3 className="subheading">CPI sobre {c.subject}</h3>
        <p className="meta-count">{c.house} · {c.author === 'oposicao' ? 'pedida pela oposição contra o governo' : 'instalada por você'} · {c.status}{c.verdict ? ` · ${c.verdict}` : ''}</p>
        <ol className="bill-stages">{c.stages.map((s) => <li key={s.name} className={`stage-${s.status.split(' ')[0]}`}><b>{s.name}</b><small>{dataBr(s.date)} · {s.status}</small></li>)}</ol>
        {c.log.length > 0 && <ul className="meta-notes">{c.log.map((l, i) => <li key={i}>{dataBr(l.date)} — {dataBr(l.text).replace('Oitiva de o ', 'Oitiva do ')}</li>)}</ul>}
      </article>)}</>}
    {data.local_bills && data.local_bills.length > 0 && <>
      <h3 className="subheading">Meus projetos</h3>
      {data.local_bills.map((b) => <article className="bill-card" key={b.id}>
        <h3 className="subheading">{b.title}</h3>
        <p className="meta-count">{b.chamber} · {b.status} · votação prevista em {dataBr(b.decision_date)} · chance estimada de aprovação: {b.chance_pct}% · relator: {b.relator.name}{b.relator.party ? ` (${b.relator.party}${b.relator.state ? ', ' + b.relator.state : ''})` : ''}</p>
        <ol className="bill-stages">{b.stages.map((s) => <li key={s.name} className={`stage-${s.status.split(' ')[0]}`}><b>{s.name}</b><small>{dataBr(s.date)} · {STATUS[s.status] || s.status}</small></li>)}</ol>
      </article>)}</>}
    {data.bills.map((b) => <article className="bill-card" key={b.id}>
      <h3 className="subheading">{b.title}</h3>
      <p className="meta-count">{b.instrument} · votação prevista em {dataBr(b.decision_date)} · relator: {b.relator.name} ({b.relator.party}, {b.relator.state}) · chance de passar nas comissões: {b.committee_chance_pct}%{b.dilution < 1 ? ` · texto com ${Math.round(b.dilution * 100)}% dos efeitos` : ''}</p>
      <ol className="bill-stages">{b.stages.map((s) => <li key={s.name} className={`stage-${s.status.split(' ')[0]}`}><b>{s.name}</b><small>{dataBr(s.date)} · {STATUS[s.status] || s.status}{s.parecer ? ` · parecer ${s.parecer}` : ''}</small></li>)}</ol>
      <div className="company-actions">
        {b.can_urgency && <button className="secondary-button" onClick={() => urgency(b)}>Pedir urgência (art. 64)</button>}
        <button className="quiet-button" onClick={() => setOpen({ ...open, [b.id]: !open[b.id] })}>{open[b.id] ? 'Ocultar bancadas' : 'Negociar com as bancadas'}</button>
      </div>
      {open[b.id] && b.blocs?.length > 0 && <div className="bloc-grid" aria-label="Negociar por bloco">{b.blocs.map((bl) => <article key={bl.id} className={`bloc-card bloc-${bl.id}`}>
        <header><b>{bl.label}</b><span>{bl.seats} cadeiras · apoio previsto {bl.support_pct}%</span></header>
        <small>Líder: <b>{bl.leader}</b> · {bl.parties.join(', ')}</small>
        <div>{data.offers.map((o) => <button key={o.key} className="quiet-button" disabled={bl.parties.every((p) => b.outlook.find((x) => x.party === p)?.offered.includes(o.key))} title={`${o.text} Em pacote, cada partido do bloco recebe parte do efeito e o custo cresce com o tamanho do bloco.`} onClick={() => negotiateBloc(b, bl, o.key)}>{o.label.split(' ')[0]} (pacote)</button>)}</div>
      </article>)}</div>}
      {open[b.id] && <div className="territory-table-wrap"><table className="territory-table"><thead><tr><th>Partido</th><th>Cadeiras</th><th>Espectro</th><th>Apoio previsto</th><th>Relação</th><th>Oferecer</th></tr></thead>
        <tbody>{b.outlook.map((p) => <tr key={p.party}><td>{p.party}</td><td>{p.seats}</td><td>{p.spectrum}</td><td>{p.support_pct}%</td><td>{p.relation}</td>
          <td>{data.offers.map((o) => <button key={o.key} className="quiet-button" disabled={p.offered.includes(o.key)} title={o.text} onClick={() => negotiate(b, p.party, o.key)}>{o.label.split(' ')[0]}</button>)}</td></tr>)}</tbody></table></div>}
      {b.log.length > 0 && <ul className="meta-notes">{b.log.map((l, i) => <li key={i}>{dataBr(l.date)} — {dataBr(l.text).replace('Oitiva de o ', 'Oitiva do ')}</li>)}</ul>}
    </article>)}
  </section>;
}
