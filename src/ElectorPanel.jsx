import { useEffect, useState } from 'react';
import MunicipalityPicker from './MunicipalityPicker';
import './meta.css';

const UFS = ['AC', 'AL', 'AM', 'AP', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MG', 'MS', 'MT', 'PA', 'PB', 'PE', 'PI', 'PR', 'RJ', 'RN', 'RO', 'RR', 'RS', 'SC', 'SE', 'SP', 'TO'];
const NOTICE = 'Voto simulado: não é enviado à Justiça Eleitoral e não altera uma eleição real.';
const fmtDate = (iso) => new Date(`${iso}T12:00:00`).toLocaleDateString('pt-BR');

export default function ElectorPanel({ request }) {
  const [scenarios, setScenarios] = useState(null);
  const [error, setError] = useState('');
  const [year, setYear] = useState(null);
  const [rules, setRules] = useState(null);
  const [office, setOffice] = useState('');
  const [uf, setUf] = useState('');
  const [city, setCity] = useState({ id: '', name: '' });
  const [query, setQuery] = useState('');
  const [page, setPage] = useState(1);
  const [list, setList] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [voting, setVoting] = useState(false);
  const [official, setOfficial] = useState(null);

  useEffect(() => { request('/api/scenarios').then(setScenarios).catch((e) => setError(e.message)); }, []); // eslint-disable-line

  useEffect(() => {
    if (!year) return;
    setRules(null); setOffice(''); setUf(''); setCity({ id: '', name: '' }); setList(null); setResult(null);
    request(`/api/scenarios/${year}`).then(setRules).catch((e) => setError(e.message));
  }, [year]); // eslint-disable-line

  const info = rules?.rules?.offices?.[office];
  const scope = info?.scope;
  const ready = !!office && (scope === 'nacional' || (scope === 'uf' && uf) || (scope === 'municipio' && uf && city.id));

  useEffect(() => { setPage(1); setResult(null); }, [office, uf, city.id, query]);

  useEffect(() => {
    if (!ready) { setList(null); return; }
    let live = true;
    setLoading(true); setError('');
    const params = new URLSearchParams({ year, office, page, page_size: 30 });
    if (uf && scope !== 'nacional') params.set('uf', uf);
    if (scope === 'municipio') params.set('municipality_id', city.id);
    if (query.trim()) params.set('q', query.trim());
    request(`/api/elector/candidates?${params}`).then((d) => { if (live) setList(d); }).catch((e) => { if (live) { setList(null); setError(e.message); } }).finally(() => { if (live) setLoading(false); });
    return () => { live = false; };
  }, [ready, year, office, uf, city.id, page, query]); // eslint-disable-line

  useEffect(() => {
    if (!ready || !year || year >= 2028) { setOfficial(null); return; }
    let live = true;
    const params = new URLSearchParams({ year, office, limit: 10 });
    if (uf && scope !== 'nacional') params.set('uf', uf);
    if (scope === 'municipio') params.set('municipality_id', city.id);
    request(`/api/elector/results?${params}`).then((d) => { if (live) setOfficial(d); }).catch(() => { if (live) setOfficial(null); });
    return () => { live = false; };
  }, [ready, year, office, uf, city.id]); // eslint-disable-line

  async function vote(choice) {
    setVoting(true); setError('');
    try {
      const body = { year, office, choice };
      if (uf && scope !== 'nacional') body.uf = uf;
      if (scope === 'municipio') body.municipality_id = city.id;
      setResult(await request('/api/elector/vote', { method: 'POST', body: JSON.stringify(body) }));
    } catch (e) { setError(e.message); } finally { setVoting(false); }
  }

  const data = rules?.data;
  return <section className="panel meta-page elector" aria-label="Modo Eleitor">
    <h2>Consulte um pleito e vote em simulação</h2>
    <p className="elector-banner" role="note"><b>{NOTICE}</b> O jogo é uma sátira e não é um serviço eleitoral.</p>
    {error && <p className="meta-status meta-error" role="alert">{error}</p>}
    {!scenarios && !error && <p className="meta-status" role="status">Carregando cenários…</p>}

    {scenarios && <>
      <h3 className="subheading">1. Escolha o pleito</h3>
      <div className="meta-tabs" role="group" aria-label="Ano da eleição">
        {scenarios.scenarios.map((s) => <button key={s.year} className={year === s.year ? 'meta-tab active' : 'meta-tab'} aria-pressed={year === s.year} onClick={() => setYear(s.year)}>
          {s.year} · {s.type === 'geral' ? 'Geral' : 'Municipal'}{s.future_simulated ? ' · futuro simulado' : ''}</button>)}
      </div>
    </>}

    {rules && <>
      <div className="meta-cards">
        <article><span>1º TURNO</span><strong>{fmtDate(rules.rules.dates.first_round)}</strong><small>{rules.rules.dates.derived_from_rule ? 'Calculada pela regra constitucional' : 'Calendário do TSE'}</small></article>
        <article><span>2º TURNO</span><strong>{fmtDate(rules.rules.dates.second_round)}</strong><small>Quando houver</small></article>
        <article><span>DADOS</span><strong>{data.official_data ? `${data.candidacies.toLocaleString('pt-BR')} candidaturas` : data.future_simulated ? 'Fictícios' : 'Não importados'}</strong>
          <small>{data.official_data ? `${data.license} · coleta ${new Date(data.collected_at).toLocaleDateString('pt-BR')}` : data.message}</small></article>
      </div>
      {rules.rules.notes.map((n) => <p key={n} className="meta-status">{n}</p>)}
      {data.future_simulated && <p className="meta-status" role="alert"><b>Cenário futuro simulado.</b> O TSE ainda não publicou candidaturas oficiais para {year}. Os participantes abaixo são fictícios.</p>}
      <details className="elector-rules"><summary>Regras deste ano (com fonte e itens pendentes)</summary>
        <ul className="meta-notes">
          <li>Coligações em eleições proporcionais: {rules.rules.coalitions_proportional.allowed ? 'permitidas' : 'vedadas'} — {rules.rules.coalitions_proportional.source}</li>
          <li>Federações partidárias: {rules.rules.federations.allowed ? 'existem' : 'não existiam'} — {rules.rules.federations.source}</li>
          <li>Doação de empresas: {rules.rules.corporate_donations.allowed ? 'permitida' : 'vedada'} — {rules.rules.corporate_donations.source}</li>
          <li>Fundo público de campanha: {rules.rules.public_campaign_fund.exists ? 'existe' : 'não existia'} — {rules.rules.public_campaign_fund.source}</li>
          {rules.rules.senate_renewal && <li>Senado: renovação de {rules.rules.senate_renewal}</li>}
        </ul>
        <p className="meta-count"><b>Pendente de confirmação (não usado como fato):</b></p>
        <ul className="meta-notes">{rules.rules.pending.map((p) => <li key={p}>{p}</li>)}</ul>
        {data.official_data && <p className="meta-count">Fonte: <a href={data.source_url} target="_blank" rel="noreferrer">{data.source_url}</a> · arquivo {data.file} · SHA-256 {data.sha256.slice(0, 12)}… · {data.votes_note}</p>}
      </details>

      <h3 className="subheading">2. Cargo e território</h3>
      <div className="elector-filters">
        <label>Cargo <select value={office} onChange={(e) => setOffice(e.target.value)}>
          <option value="">Escolha…</option>
          {Object.entries(rules.rules.offices).map(([key, o]) => <option key={key} value={key}>{o.label} · mandato {o.term} anos</option>)}</select></label>
        {(scope === 'uf' || scope === 'municipio') && <label>UF <select value={uf} onChange={(e) => { setUf(e.target.value); setCity({ id: '', name: '' }); }}>
          <option value="">Escolha…</option>{UFS.map((u) => <option key={u} value={u}>{u}</option>)}</select></label>}
        {scope === 'municipio' && <MunicipalityPicker request={request} stateCode={uf} value={city.name} selectedId={city.id} required disabled={!uf} label="Município (código oficial do IBGE)" onSelect={(item) => setCity({ id: item.id, name: item.name })} />}
      </div>
      {info && <p className="meta-count">{info.label}: idade mínima {info.min_age} anos · {info.source}</p>}

      {ready && <>
        <h3 className="subheading">3. Candidatos {list ? `(${list.total.toLocaleString('pt-BR')})` : ''}</h3>
        <label className="week-region">Buscar por nome <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Nome ou nome de urna" maxLength={60} /></label>
        {loading && <p className="meta-status" role="status">Carregando candidatos…</p>}
        {list && !loading && list.items.length === 0 && <p className="meta-status">{data.official_data || data.future_simulated ? 'Nenhum candidato encontrado para esta disputa e filtro.' : data.message}</p>}
        {list?.scenario && <p className="meta-status" role="alert">{list.scenario}</p>}
        {official && official.available && <details className="official-results" open><summary>Resultado oficial: votos nominais por candidato</summary>
          {official.rounds.map((r) => <div key={r.round}><h4 className="subheading">{official.rounds.length > 1 ? `${r.round}º turno · ` : ''}{r.nominal_votes.toLocaleString('pt-BR')} votos nominais · {r.candidates_count} candidaturas</h4>
            <ol className="results-list">{r.candidates.map((c) => <li key={c.id}><span>{c.name} <small>({c.party})</small></span><b>{c.votes.toLocaleString('pt-BR')}</b><small>{c.share_pct}% · {c.result}</small></li>)}</ol></div>)}
          <small className="meta-count">{official.note}</small></details>}
        {official && !official.available && official.message && year < 2028 && <p className="meta-status">{official.message}</p>}

        {list && list.items.length > 0 && <ul className="candidate-list">{list.items.map((c) => <li key={c.id} className={c.fictional ? 'fictional' : ''}>
          <div className="cand-number" aria-label="Número">{c.number}</div>
          <div><b>{c.ballot_name}</b>{c.fictional && <span className="tag t-correcao">Fictício</span>}
            <small>{c.party || 's/ partido'}{c.party_name && c.party_name !== c.party ? ` · ${c.party_name}` : ''}{c.municipality && c.municipality !== 'BRASIL' ? ` · ${c.municipality}` : ''}</small>
            <small>Candidatura: {c.candidacy_status} · Situação (fonte): {c.result}</small></div>
          <button className="secondary-button" disabled={voting} onClick={() => vote(c.id)}>Votar (simulado)</button></li>)}</ul>}
        {list && list.total > list.page_size && <div className="meta-tabs">
          <button className="meta-tab" disabled={page <= 1} onClick={() => setPage(page - 1)}>Anterior</button>
          <span className="meta-count">Página {page} de {Math.ceil(list.total / list.page_size)}</span>
          <button className="meta-tab" disabled={page >= Math.ceil(list.total / list.page_size)} onClick={() => setPage(page + 1)}>Próxima</button></div>}
        <div className="meta-tabs"><button className="meta-tab" disabled={voting} onClick={() => vote('branco')}>Voto em branco (simulado)</button>
          <button className="meta-tab" disabled={voting} onClick={() => vote('nulo')}>Voto nulo (simulado)</button></div>
      </>}

      {result && <section className="meta-status" role="status" aria-live="polite">
        <h3 className="subheading">Seu voto simulado</h3>
        <p><b>{result.label}</b> {result.scenario_label && <span className="tag t-correcao">{result.scenario_label}</span>}</p>
        <p className="elector-banner">{result.notice}</p>
        {result.your_candidate_result && <p>Situação do seu candidato no cadastro oficial: <b>{result.your_candidate_result}</b>.</p>}
        {result.official.available ? <><p className="meta-count">{result.official.note}</p>
          <ul className="meta-notes">{result.official.elected.map((e) => <li key={e.id}>{e.ballot_name} ({e.party}) — {e.result}</li>)}</ul></> : <p>{result.official.message}</p>}
      </section>}
    </>}
  </section>;
}
