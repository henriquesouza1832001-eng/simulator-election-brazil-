import { useEffect, useState } from 'react';
import Select from './Choice.jsx';
import { Drawer } from './ui.jsx';
import './powers.css';
import './territory.css';
import { EFFECT, effectText, br, dataBr } from './format';

const APPROVAL = {
  decreto: ['Decreto', 'Vale na hora'],
  mp: ['Medida provisória', 'Vale na hora; o Congresso precisa converter'],
  pl: ['Projeto de lei', 'Maioria nas duas casas'],
  plp: ['Lei complementar', 'Maioria absoluta nas duas casas'],
  pec: ['Emenda constitucional', '3/5 em dois turnos nas duas casas'],
  tratado: ['Tratado', 'Congresso aprova e o Presidente ratifica'],
  blocked: ['Vedado', 'A Constituição não permite'],
};
const DOMAINS = { banco: 'Banco e moeda', empresas: 'Empresas e patrimônio', infraestrutura: 'Infraestrutura', defesa: 'Defesa e Forças Armadas', seguranca: 'Segurança e armas', exterior: 'Relações exteriores', regime: 'Regime e instituições', economia: 'Economia e tributos', saude: 'Saúde', educacao: 'Educação', social: 'Assistência social', ambiente: 'Meio ambiente', justica: 'Justiça e Judiciário', legislativo: 'Relação com o Legislativo', memoria: 'Memória e regime militar', espaco: 'Espaço e ciência' };
const STRUCTURE_NAMES = { central_bank: 'Banco Central', guns: 'Armas', police_model: 'Polícia', government_system: 'Sistema de governo', currency: 'Moeda' };


export default function PowersPanel({ request, state, onState, onNotice }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [domain, setDomain] = useState('');
  const [shown, setShown] = useState(8);
  const [options, setOptions] = useState({});
  const [busy, setBusy] = useState('');
  const [ledger, setLedger] = useState([]);
  const [fiscal, setFiscal] = useState(null);
  const [text, setText] = useState('');
  const [mapped, setMapped] = useState(null);
  const [sel, setSel] = useState(null);

  useEffect(() => {
    let live = true;
    request('/api/powers').then((d) => { if (live) setData(d); }).catch((e) => { if (live) setError(e.message); });
    return () => { live = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state?.date, state?.career_overview?.office, state?.party_path?.stage]);

  useEffect(() => { request('/api/ledger').then((r) => setLedger(r.entries || [])).catch(() => {}); }, [state?.date, data?.history?.length]);

  useEffect(() => { request('/api/fiscal/local').then((r) => setFiscal(r.fiscal)).catch(() => setFiscal(null)); }, [state?.date, ledger.length]);

  async function understand(e) {
    e.preventDefault();
    if (text.trim().length < 4) return;
    try {
      const r = await request('/api/powers/interpret', { method: 'POST', body: JSON.stringify({ text }) });
      setMapped(r);
      const guesses = {};
      r.matches.forEach((m) => { if (m.option_guess) guesses[m.id] = m.option_guess; });
      setOptions((o) => ({ ...guesses, ...o }));
    } catch (err) { onNotice?.(err.message); }
  }

  async function runMapped(match) {
    const chosen = data.actions.find((a) => a.id === match.id);
    if (!chosen) return;
    try { await request(`/api/powers/confirm?action=${encodeURIComponent(match.id)}${options[match.id] ? `&option=${encodeURIComponent(options[match.id])}` : ''}`, { method: 'POST', body: JSON.stringify({ text }) }); } catch { /* aprendizado é opcional */ }
    await run(chosen);
    setMapped(null);
  }

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
      const gained = result.result ? effectText(result.result) : '';
      onNotice?.(`${result.message}${result.chance != null ? ` (chance estimada ${Math.round(result.chance * 100)}%)` : ''}${gained ? ` Resultado: ${gained}.` : ''}`);
    } catch (e) { onNotice?.(e.message); } finally { setBusy(''); }
  }

  if (error) return <section className="panel"><p className="meta-status meta-error" role="alert">{error}</p></section>;
  if (!data) return <section className="panel"><p className="meta-status" role="status">Carregando…</p></section>;
  const { role } = data;
  const domains = [...new Set((data.actions || []).map((a) => a.domain))];
  const activeDomain = domain || domains[0] || 'todos';
  const allActions = (data.actions || []).filter((a) => activeDomain === 'todos' || a.domain === activeDomain);
  const actions = allActions.slice(0, shown);
  const chosen = sel ? (data.actions || []).find((x) => x.id === sel) : null;

  return <section className="panel powers-page">
    <h2>Competências · {role.label}</h2>
    <p className="page-description">Escolha uma ação abaixo. Cada cargo só faz o que a Constituição permite; o resumo jurídico é para o jogo, não é parecer.</p>
    <details className="fold">
      <summary>O que cabe a este cargo <span>e o que não cabe</span></summary>
      <div className="powers-roles">
        <div><h3 className="subheading">Pode</h3><ul>{role.pode.map((t) => <li key={t}>{t}</li>)}</ul></div>
        <div><h3 className="subheading">Não pode</h3><ul>{role.nao_pode.map((t) => <li key={t}>{t}</li>)}</ul></div>
      </div>
      <p className="meta-count">Base: {role.base}</p>
    </details>

    {data.structure && <details className="fold">
      <summary>Situação do país <span>banco, armas, polícia, moeda, blocos e empresas</span></summary>
      <div className="powers-structure" aria-label="Situação do país">
        {Object.entries(data.structure).map(([k, v]) => <article key={k}><span>{STRUCTURE_NAMES[k]}</span><b>{v.label}</b></article>)}
        <article><span>Blocos</span><b>{Object.entries(data.blocs).filter(([, on]) => on === true).map(([k]) => k.toUpperCase()).join(', ') || 'nenhum'}</b></article>
        <article><span>Empresas controladas pela União</span><b>{Object.entries(data.companies).filter(([, v]) => v !== 'privada').map(([k]) => k).join(', ')}</b></article>
      </div>
    </details>}

    {(data.actions || []).length > 0 && <form className="mapper-box" onSubmit={understand}>
      <label htmlFor="mapper-text"><b>Diga o que quer fazer</b></label>
      <small className="meta-count">O motor entende a frase pelas regras do jogo e mostra as ações do seu cargo que combinam. A IA (Gemini), se estiver ativa, só ajuda a desempatar e a fazer perguntas.</small>
      <div className="territory-search"><input id="mapper-text" value={text} maxLength={400} onChange={(e) => setText(e.target.value)} placeholder="Ex.: duplicar a BR-381, liberar o porte de arma, sair do BRICS" />
        <button className="secondary-button" type="submit">Entender</button></div>
      {mapped && <div className="mapper-result">
        {mapped.matches.length === 0 && <p className="meta-status">Nenhuma ação do seu cargo combina com essa frase.</p>}
        {mapped.matches.map((m) => <div className="mapper-match" key={m.id}>
          <div><b>{m.title}</b> <small>({m.basis})</small>
            {m.legal && <small className={`legal-${m.legal.level}`}>Risco jurídico {m.legal.level}</small>}
            {!m.available && <small className="neg">{m.reason}</small>}</div>
          {m.available && data.executable && <div className="powers-actions">
            {m.options.length > 0 && <Select aria-label={`Opção para ${m.title}`} value={options[m.id] || ''} onChange={(e) => setOptions({ ...options, [m.id]: e.target.value })}><option value="">Escolher…</option>{m.options.map((o) => <option key={o} value={o}>{o}</option>)}</Select>}
            <button className="secondary-button" disabled={m.options.length > 0 && !options[m.id]} onClick={() => runMapped(m)}>Usar esta ação</button></div>}
        </div>)}
        {mapped.questions.map((q) => <p className="mapper-question" key={q}>{q}</p>)}
        <small className="meta-count">Leitura: {mapped.source === 'gemini' ? 'regras do jogo + Gemini (desempate)' : 'regras do jogo'}. {mapped.note}</small>
      </div>}
    </form>}

    {fiscal && <details className="fold fiscal-box" aria-label="Contas do cargo e LRF">
      <summary>Contas do cargo e Lei de Responsabilidade Fiscal <span>reserva, folha e dívida</span></summary>
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
    </details>}

    {data.reference?.length > 0 && <details className="fold">
      <summary>Principais iniciativas do cargo <span>{data.reference.length} itens</span></summary>
      <ul className="powers-reference">{data.reference.map((r) => <li key={r.title}><b>{r.title}</b><small>{r.text}</small><small className="meta-count">{r.basis}</small></li>)}</ul>
      <p className="meta-count">Nesta versão, estas ações ainda são descritivas; use a aba do cargo para as decisões do mandato.</p></details>}

    {data.actions?.length > 0 && <>
      <div className="powers-filter" role="group" aria-label="Áreas">
        {domains.map((d) => <button key={d} className={activeDomain === d ? 'meta-tab active' : 'meta-tab'} aria-pressed={activeDomain === d} onClick={() => { setDomain(d); setShown(8); }}>{DOMAINS[d] || d}</button>)}
        <button className={activeDomain === 'todos' ? 'meta-tab active' : 'meta-tab'} onClick={() => { setDomain('todos'); setShown(8); }}>Todas</button>
      </div>
      <div className="ds-inv-grid ds-power-grid">{actions.map((a) => {
        const [kind] = APPROVAL[a.approval];
        return <button key={a.id} type="button" className={'ds-inv' + (a.available ? '' : ' blocked')} onClick={() => setSel(a.id)}>
          <span className="ds-muted">{kind}{a.legal ? ' · risco jurídico ' + a.legal.level : ''}</span>
          <b>{a.title}</b>
          <small className="ds-muted">{effectText(a.effects) || a.summary}</small>
          {!a.available && <small className="neg">indisponível agora</small>}
        </button>;
      })}</div>
      {chosen && <Drawer title={chosen.title} onClose={() => setSel(null)} footer={data.executable && chosen.available
        ? <button className="primary-button" disabled={busy === chosen.id || (chosen.options.length > 0 && !options[chosen.id])} onClick={async () => { await run(chosen); setSel(null); }}>{busy === chosen.id ? 'Enviando…' : (chosen.kind === 'leg' ? 'Levar à votação' : (['decreto', 'mp'].includes(chosen.approval) ? 'Assinar' : 'Enviar ao Congresso'))}</button>
        : null}>
        <p>{chosen.summary}</p>
        <p className="powers-meta"><span className={`powers-kind ${chosen.approval}`}>{APPROVAL[chosen.approval][0]}</span> {APPROVAL[chosen.approval][1]}{chosen.legal ? <span className={`legal-chip legal-${chosen.legal.level}`}>risco jurídico {chosen.legal.level}</span> : null}</p>
        {effectText(chosen.effects) && <p className="powers-effects">Efeito estimado: {effectText(chosen.effects)}{chosen.cost_bi ? ` · ${chosen.cost_bi > 0 ? 'custo' : 'receita'} R$ ${br(Math.abs(chosen.cost_bi), 2)} bi` : ''}</p>}
        {!chosen.available && <p className="neg">{chosen.reason}</p>}
        {chosen.options.length > 0 && chosen.available && <><h4>Escolha uma opção</h4>
          <div className="ds-pick-list">{chosen.options.map((o) => <button key={o} type="button" aria-pressed={options[chosen.id] === o} onClick={() => setOptions({ ...options, [chosen.id]: o })}><span>{o}</span></button>)}</div></>}
        <details className="more"><summary>Base legal e detalhes</summary>
          <p className="powers-meta">Base: {chosen.basis}</p>
          {chosen.legal && <p className={`powers-meta legal-${chosen.legal.level}`}>Parecer da AGU: {chosen.legal.risk_pct}% de chance de o STF suspender. {chosen.legal.note}</p>}
          {chosen.cost_text && <p className="powers-meta">Custo: {chosen.cost_text}{chosen.chance != null ? ` · chance de aprovação ${Math.round(chosen.chance * 100)}%` : ''}</p>}
          {chosen.precedent && <p className="powers-precedent">Precedente: {chosen.precedent}</p>}
        </details>
      </Drawer>}
      {allActions.length > shown && <button className="secondary-button" onClick={() => setShown(shown + 12)}>Mostrar mais ({allActions.length - shown})</button>}
      {data.history?.length > 0 && <details className="fold"><summary>Atos recentes <span>{data.history.length}</span></summary><ul className="meta-notes">{data.history.map((h, i) => <li key={i}>{dataBr(h.date)} — {h.title}</li>)}</ul></details>}
    </>}
    {ledger.length > 0 && <details className="fold">
      <summary>Previsto e realizado <span>{ledger.length} {ledger.length === 1 ? "decisão" : "decisões"}</span></summary>
      <ul className="powers-list ledger-list">{ledger.slice(0, 12).map((e) => <li key={e.id}><div>
        <b>{e.title}</b> <small>{dataBr(e.date)} · {e.status}{e.cost ? ` · ${e.cost}` : ''}</small>
        <small>Previsto: {effectText(e.forecast) || 'sem efeito numérico'}</small>
        <small>Realizado: {e.result ? (effectText(e.result) || 'nenhum efeito') : 'aguardando'}</small>
        {e.reason && <small className="powers-precedent">{e.reason}</small>}
        {e.narrative && <small className="powers-narrative">{e.narrative.text} <em>({e.narrative.source === 'gemini' ? 'Gemini, a partir dos fatos do motor' : 'texto local'})</em></small>}
      </div>{!e.narrative && <div className="powers-actions"><button className="secondary-button" onClick={() => narrate(e)}>Narrar</button></div>}</li>)}</ul>
    </details>}
  </section>;
}
