import { useEffect, useState } from 'react';
import './powers.css';
import './territory.css';

const APPROVAL = {
  decreto: ['Decreto', 'Vale na hora'],
  mp: ['Medida provisória', 'Vale na hora; o Congresso precisa converter'],
  pl: ['Projeto de lei', 'Maioria nas duas casas'],
  plp: ['Lei complementar', 'Maioria absoluta nas duas casas'],
  pec: ['Emenda constitucional', '3/5 em dois turnos nas duas casas'],
  tratado: ['Tratado', 'Congresso aprova e o Presidente ratifica'],
  blocked: ['Vedado', 'A Constituição não permite'],
};
const DOMAINS = { banco: 'Banco e moeda', empresas: 'Empresas e patrimônio', infraestrutura: 'Infraestrutura', defesa: 'Defesa e Forças Armadas', seguranca: 'Segurança e armas', exterior: 'Relações exteriores', regime: 'Regime e instituições', economia: 'Economia e tributos' };
const EFFECT = { trust: 'confiança', reputation: 'reputação', mobilidade: 'mobilidade', seguranca: 'segurança', saude_atencao: 'saúde', educacao_fundamental: 'educação básica', educacao_medio: 'ensino médio', saneamento_basico: 'saneamento', agua_encanada: 'água', esgoto_inadequado: 'esgoto inadequado', adensamento: 'adensamento', logistica: 'custo logístico', homicidios: 'homicídios', mortalidade_infantil: 'mortalidade infantil', idhm_educacao: 'IDHM educação', gini: 'Gini', divida_pib: 'dívida', approval: 'aprovação', gdp_growth: 'PIB', inflation: 'inflação', unemployment: 'desemprego', institutional_trust: 'confiança institucional', integrity: 'integridade', governability: 'governabilidade', congress_support: 'base no Congresso', primary_balance: 'resultado primário', military_loyalty: 'lealdade militar' };
const STRUCTURE_NAMES = { central_bank: 'Banco Central', guns: 'Armas', police_model: 'Polícia', government_system: 'Sistema de governo', currency: 'Moeda' };

function effectText(effects) {
  return Object.entries(effects || {}).map(([k, v]) => `${v > 0 ? '+' : ''}${v} ${EFFECT[k] || k}`).join(' · ');
}

export default function PowersPanel({ request, state, onState, onNotice }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [domain, setDomain] = useState('todos');
  const [options, setOptions] = useState({});
  const [busy, setBusy] = useState('');
  const [ledger, setLedger] = useState([]);
  const [fiscal, setFiscal] = useState(null);

  useEffect(() => {
    let live = true;
    request('/api/powers').then((d) => { if (live) setData(d); }).catch((e) => { if (live) setError(e.message); });
    return () => { live = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state?.date, state?.career_overview?.office, state?.party_path?.stage]);

  useEffect(() => { request('/api/ledger').then((r) => setLedger(r.entries || [])).catch(() => {}); }, [state?.date, data?.history?.length]);

  useEffect(() => { request('/api/fiscal/local').then((r) => setFiscal(r.fiscal)).catch(() => setFiscal(null)); }, [state?.date, ledger.length]);

  async function narrate(entry) {
    try {
      const out = await request(`/api/ledger/${entry.id}/narrate`, { method: 'POST', body: '{}' });
      setLedger((rows) => rows.map((r) => (r.id === entry.id ? { ...r, narrative: out } : r)));
    } catch (e) { onNotice?.(e.message); }
  }

  async function run(action) {
    setBusy(action.id);
    try {
      const result = await request('/api/powers/execute', { method: 'POST', body: JSON.stringify({ action: action.id, option: options[action.id] || null }) });
      setData(result.catalog);
      if (result.state) onState?.(result.state);
      const gained = result.result ? Object.entries(result.result).map(([k, v]) => `${v > 0 ? '+' : ''}${v} ${EFFECT[k] || k}`).join(' · ') : '';
      onNotice?.(`${result.message}${result.chance != null ? ` (chance estimada ${Math.round(result.chance * 100)}%)` : ''}${gained ? ` Resultado: ${gained}.` : ''}`);
    } catch (e) { onNotice?.(e.message); } finally { setBusy(''); }
  }

  if (error) return <section className="panel"><p className="meta-status meta-error" role="alert">{error}</p></section>;
  if (!data) return <section className="panel"><p className="meta-status" role="status">Carregando…</p></section>;
  const { role } = data;
  const actions = (data.actions || []).filter((a) => domain === 'todos' || a.domain === domain);
  const domains = [...new Set((data.actions || []).map((a) => a.domain))];

  return <section className="panel powers-page">
    <h2>{role.label}: o que cabe a este papel</h2>
    <p className="page-description">Resumo da Constituição e das leis citadas, feito para o jogo. Não é parecer jurídico.</p>
    <div className="powers-roles">
      <div><h3 className="subheading">Pode</h3><ul>{role.pode.map((t) => <li key={t}>{t}</li>)}</ul></div>
      <div><h3 className="subheading">Não pode</h3><ul>{role.nao_pode.map((t) => <li key={t}>{t}</li>)}</ul></div>
    </div>
    <p className="meta-count">Base: {role.base}</p>

    {data.structure && <div className="powers-structure" aria-label="Situação do país">
      {Object.entries(data.structure).map(([k, v]) => <article key={k}><span>{STRUCTURE_NAMES[k]}</span><b>{v.label}</b></article>)}
      <article><span>Blocos</span><b>{Object.entries(data.blocs).filter(([, on]) => on === true).map(([k]) => k.toUpperCase()).join(', ') || 'nenhum'}</b></article>
      <article><span>Empresas controladas pela União</span><b>{Object.entries(data.companies).filter(([, v]) => v !== 'privada').map(([k]) => k).join(', ')}</b></article>
    </div>}

    {fiscal && <div className="fiscal-box" aria-label="Contas do cargo e LRF">
      <h3 className="subheading">Contas do cargo e Lei de Responsabilidade Fiscal</h3>
      <div className="powers-structure">
        <article><span>Reserva disponível no ano</span><b>R$ {Number(fiscal.reserve_available_mi).toLocaleString('pt-BR')} mi</b><small>de R$ {Number(fiscal.annual_reserve_mi).toLocaleString('pt-BR')} mi</small></article>
        <article className={`lrf-${fiscal.personnel_level}`}><span>Despesa com pessoal</span><b>{fiscal.personnel_pct}% da RCL</b><small>limite {fiscal.personnel_limit}% · situação: {fiscal.personnel_level}</small></article>
        <article><span>Dívida</span><b>{fiscal.debt_pct}% da RCL</b><small>limite {fiscal.debt_limit}%</small></article>
        <article><span>Receita corrente líquida (modelo)</span><b>R$ {Number(fiscal.rcl_mi).toLocaleString('pt-BR')} mi/ano</b></article>
      </div>
      {fiscal.commitments.length > 0 && <p className="meta-count">Obras comprometendo a reserva: {fiscal.commitments.map((c) => `${c.name} (R$ ${c.annual_mi} mi/ano até ${c.end})`).join('; ')}.</p>}
      {fiscal.summaries.length > 0 && <div className="territory-table-wrap"><table className="territory-table"><thead><tr><th>Mês</th><th>Executado (mi)</th><th>Folha %RCL</th><th>Dívida %RCL</th><th>Situação</th></tr></thead>
        <tbody>{fiscal.summaries.map((m) => <tr key={m.month}><td>{m.month}</td><td>{m.executed_mi}</td><td>{m.personnel_pct}</td><td>{m.debt_pct}</td><td>{m.level}</td></tr>)}</tbody></table></div>}
      <p className="meta-count">{fiscal.basis}. {fiscal.note}</p>
    </div>}

    {data.reference?.length > 0 && <>
      <h3 className="subheading">Principais iniciativas do cargo</h3>
      <ul className="powers-reference">{data.reference.map((r) => <li key={r.title}><b>{r.title}</b><small>{r.text}</small><small className="meta-count">{r.basis}</small></li>)}</ul>
      <p className="meta-count">Nesta versão, estas ações ainda são descritivas; use a aba do cargo para as decisões do mandato.</p></>}

    {data.actions?.length > 0 && <>
      <div className="powers-filter" role="group" aria-label="Áreas">
        <button className={domain === 'todos' ? 'meta-tab active' : 'meta-tab'} onClick={() => setDomain('todos')}>Todas</button>
        {domains.map((d) => <button key={d} className={domain === d ? 'meta-tab active' : 'meta-tab'} onClick={() => setDomain(d)}>{DOMAINS[d] || d}</button>)}
      </div>
      <ul className="powers-list">{actions.map((a) => {
        const [kind, rule] = APPROVAL[a.approval];
        return <li key={a.id} className={a.available ? '' : 'blocked'}>
          <div>
            <b>{a.title}</b>
            <small>{a.summary}</small>
            <small className="powers-meta"><span className={`powers-kind ${a.approval}`}>{kind}</span> {rule} · {a.basis}</small>
            {a.legal && <small className={`powers-meta legal-${a.legal.level}`}>Parecer da AGU: risco jurídico {a.legal.level} ({a.legal.risk_pct}% de chance de o STF suspender). {a.legal.note}</small>}
            {a.cost_text && <small className="powers-meta">Custo: {a.cost_text}{a.chance != null ? ` · chance de aprovação ${Math.round(a.chance * 100)}%` : ''}</small>}
            {effectText(a.effects) && <small className="powers-effects">Efeito estimado: {effectText(a.effects)}{a.cost_bi ? ` · ${a.cost_bi > 0 ? 'custo' : 'receita'} R$ ${Math.abs(a.cost_bi)} bi` : ''}</small>}
            {a.precedent && <small className="powers-precedent">Precedente: {a.precedent}</small>}
            {!a.available && <small className="neg">{a.reason}</small>}
          </div>
          {data.executable && a.available && <div className="powers-actions">
            {a.options.length > 0 && <select aria-label={`Opções de ${a.title}`} value={options[a.id] || ''} onChange={(e) => setOptions({ ...options, [a.id]: e.target.value })}>
              <option value="">Escolher…</option>{a.options.map((o) => <option key={o} value={o}>{o}</option>)}</select>}
            <button className="secondary-button" disabled={busy === a.id || (a.options.length > 0 && !options[a.id])} onClick={() => run(a)}>{busy === a.id ? 'Enviando…' : (a.kind === 'leg' ? 'Levar à votação' : (['decreto', 'mp'].includes(a.approval) ? 'Assinar' : 'Enviar ao Congresso'))}</button>
          </div>}
        </li>;
      })}</ul>
      {data.history?.length > 0 && <><h3 className="subheading">Atos recentes</h3><ul className="meta-notes">{data.history.map((h, i) => <li key={i}>{h.date} — {h.title}</li>)}</ul></>}
    </>}
    {ledger.length > 0 && <>
      <h3 className="subheading">Previsto e realizado</h3>
      <ul className="powers-list ledger-list">{ledger.slice(0, 12).map((e) => <li key={e.id}><div>
        <b>{e.title}</b> <small>{e.date} · {e.status}{e.cost ? ` · ${e.cost}` : ''}</small>
        <small>Previsto: {effectText(e.forecast) || 'sem efeito numérico'}</small>
        <small>Realizado: {e.result ? (effectText(e.result) || 'nenhum efeito') : 'aguardando'}</small>
        {e.reason && <small className="powers-precedent">{e.reason}</small>}
        {e.narrative && <small className="powers-narrative">{e.narrative.text} <em>({e.narrative.source === 'gemini' ? 'Gemini, a partir dos fatos do motor' : 'texto local'})</em></small>}
      </div>{!e.narrative && <div className="powers-actions"><button className="secondary-button" onClick={() => narrate(e)}>Narrar</button></div>}</li>)}</ul>
    </>}
  </section>;
}
