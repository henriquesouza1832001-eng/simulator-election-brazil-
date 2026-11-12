import { useEffect, useState } from 'react';
import './powers.css';

const EFFECT = { approval: 'aprovação', inflation: 'inflação', unemployment: 'desemprego', gdp_growth: 'PIB', primary_balance: 'resultado primário', integrity: 'integridade', congress_support: 'base no Congresso' };

export default function CompaniesPanel({ request, state, onState, onNotice }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [picks, setPicks] = useState({});
  const load = () => request('/api/companies').then(setData).catch((e) => setError(e.message));
  useEffect(() => { load(); }, [state?.date]);

  async function act(company, action) {
    const k = `${company.id}:${action.key}`;
    try {
      const r = await request('/api/companies/act', { method: 'POST', body: JSON.stringify({ company: company.id, action: action.key, option: picks[k] || null }) });
      setData(r.overview);
      if (r.state) onState?.(r.state);
      onNotice?.(r.announcement || `${company.name}: decisão registrada.`);
    } catch (e) { onNotice?.(e.message); }
  }

  async function privatize(company) {
    try {
      const r = await request('/api/powers/execute', { method: 'POST', body: JSON.stringify({ action: 'empresa_privatizar', option: company.privatize_key }) });
      if (r.state) onState?.(r.state);
      onNotice?.(r.message);
      load();
    } catch (e) { onNotice?.(e.message); }
  }

  if (error) return <section className="panel"><p className="meta-status meta-error" role="alert">{error}</p></section>;
  if (!data) return <section className="panel"><p className="meta-status" role="status">Carregando…</p></section>;

  return <section className="panel powers-page">
    <h2>Empresas e bancos públicos</h2>
    <p className="page-description">{data.note}</p>
    <ul className="powers-list company-list">{data.companies.map((c) => <li key={c.id}><div>
      <b>{c.name}</b> <small>{c.sector} · sede {c.hq} · {c.control}{c.strategic ? ' · estratégica' : ''}</small>
      <small>{c.note}</small>
      <div className="company-meters">
        <label>Saúde da empresa <meter min="0" max="100" low="35" high="65" optimum="85" value={c.health}>{c.health}</meter> <span>{c.health}</span></label>
        <label>Relação com o governo <meter min="0" max="100" low="35" high="65" optimum="85" value={c.relation}>{c.relation}</meter> <span>{c.relation}</span></label>
      </div>
      <div className="company-actions">{c.actions.map((a) => {
        const k = `${c.id}:${a.key}`;
        return <span className="company-action" key={a.key} title={a.reason || a.text}>
          {a.options.length > 0 && a.available && <select aria-label={`${a.label} de ${c.name}`} value={picks[k] || ''} onChange={(e) => setPicks({ ...picks, [k]: e.target.value })}><option value="">{a.label}…</option>{a.options.map((o) => <option key={o} value={o}>{o}</option>)}</select>}
          <button className="secondary-button" disabled={!a.available || (a.options.length > 0 && !picks[k])} onClick={() => act(c, a)}>{a.options.length && a.available ? 'Aplicar' : a.label}</button>
          {!a.available && <small className="neg">{a.reason}</small>}
        </span>;
      })}</div>
      {c.can_privatize && <div className="company-actions"><button className="quiet-button" onClick={() => privatize(c)}>Propor a privatização (exige lei)</button></div>}
    </div></li>)}</ul>
    <p className="meta-count">Efeitos de cada decisão aparecem no histórico de previsto e realizado (aba Competências) e na linha do tempo da Imprensa.</p>
  </section>;
}
