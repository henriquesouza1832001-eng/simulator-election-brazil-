import { useEffect, useState } from 'react';
import './powers.css';
import './territory.css';

const DOMAIN_NAMES = { economia: 'Economia', fiscal: 'Contas públicas', trabalho: 'Trabalho e renda', desigualdade: 'Pobreza e desigualdade', educacao: 'Educação', saude: 'Saúde', saneamento: 'Saneamento e moradia', infraestrutura: 'Transporte e infraestrutura', seguranca: 'Segurança', ambiente: 'Meio ambiente', instituicoes: 'Instituições e política', demografia: 'População', externo: 'Setor externo' };
const SOURCE = { atlas: 'Atlas (Censo 2010)', ibge: 'IBGE', estimado: 'estimativa do jogo' };
const COLS = [['idhm', 'IDHM', 3], ['gini', 'Gini', 3], ['pobreza', 'Pobreza %', 1], ['esperanca_vida', 'Esperança de vida', 1], ['mortalidade_infantil', 'Mort. infantil', 1], ['saneamento_basico', 'Saneamento', 1], ['mobilidade', 'Mobilidade', 1], ['seguranca', 'Segurança', 1]];
const fmt = (v, d = 1) => (Number.isFinite(Number(v)) ? Number(v).toLocaleString('pt-BR', { minimumFractionDigits: d, maximumFractionDigits: d }) : '—');

export default function TerritoryPanel({ request, state, onState, onNotice }) {
  const [view, setView] = useState('mapa');
  const [overview, setOverview] = useState(null);
  const [error, setError] = useState('');
  const [level, setLevel] = useState('states');
  const [query, setQuery] = useState('');
  const [found, setFound] = useState([]);
  const [city, setCity] = useState(null);
  const [projects, setProjects] = useState(null);
  const [registry, setRegistry] = useState(null);
  const [pick, setPick] = useState({});

  useEffect(() => { request('/api/territory').then(setOverview).catch((e) => setError(e.message)); }, [state?.date]);
  useEffect(() => { if (view === 'obras') request('/api/territory/projects').then(setProjects).catch((e) => setError(e.message)); }, [view, state?.date]);
  useEffect(() => { if (view === 'indicadores' && !registry) request('/api/indicators/registry').then(setRegistry).catch((e) => setError(e.message)); }, [view]);

  async function search(e) {
    e.preventDefault();
    if (query.trim().length < 2) return;
    const r = await request(`/api/territory/search?q=${encodeURIComponent(query)}`);
    setFound(r.items);
  }
  async function open(code) { setCity(await request(`/api/territory/city/${code}`)); }
  async function start(p) {
    const sel = pick[p.id] || {};
    try {
      const r = await request('/api/territory/projects/start', { method: 'POST', body: JSON.stringify({ project_id: p.id, uf: p.uf || sel.uf, city: p.city || sel.city || null }) });
      if (r.state) onState?.(r.state);
      onNotice?.(`Obra iniciada: ${r.project.name} (R$ ${r.project.cost_bi} bi, conclusão em ${r.project.end}).`);
      setProjects(await request('/api/territory/projects'));
    } catch (err) { onNotice?.(err.message); }
  }

  if (error) return <section className="panel"><p className="meta-status meta-error" role="alert">{error}</p></section>;
  if (!overview) return <section className="panel"><p className="meta-status" role="status">Carregando…</p></section>;
  const rows = level === 'states' ? overview.states : overview.regions;
  const byDomain = city ? city.indicators.reduce((acc, i) => { (acc[i.domain] ||= []).push(i); return acc; }, {}) : {};

  return <section className="panel powers-page territory-page">
    <h2>Território e indicadores</h2>
    <div className="powers-filter" role="group" aria-label="Visões">
      {[['mapa', 'Estados e regiões'], ['cidade', 'Cidades'], ['obras', 'Obras e transporte'], ['indicadores', 'Como os indicadores se ligam']].map(([k, l]) => <button key={k} className={view === k ? 'meta-tab active' : 'meta-tab'} onClick={() => setView(k)}>{l}</button>)}
    </div>

    {view === 'mapa' && <>
      <div className="powers-filter">
        <button className={level === 'states' ? 'meta-tab active' : 'meta-tab'} onClick={() => setLevel('states')}>Estados</button>
        <button className={level === 'regions' ? 'meta-tab active' : 'meta-tab'} onClick={() => setLevel('regions')}>Regiões</button>
      </div>
      <div className="territory-table-wrap"><table className="territory-table">
        <thead><tr><th>{level === 'states' ? 'Estado' : 'Região'}</th><th>População</th><th>PIB (R$ bi)</th>{COLS.map(([k, l]) => <th key={k}>{l}</th>)}</tr></thead>
        <tbody><tr className="country"><td>Brasil</td><td>{fmt(overview.country.population, 0)}</td><td>{fmt(overview.country.gdp_bi, 0)}</td>{COLS.map(([k, , d]) => <td key={k}>{fmt(overview.country.indicators[k], d)}</td>)}</tr>
          {rows.map((r) => <tr key={r.uf || r.code}><td>{r.name}</td><td>{fmt(r.population, 0)}</td><td>{fmt(r.gdp_bi, 0)}</td>{COLS.map(([k, , d]) => <td key={k}>{fmt(r.indicators[k], d)}</td>)}</tr>)}</tbody>
      </table></div>
      <p className="meta-count">{overview.note}</p>
    </>}

    {view === 'cidade' && <>
      <form className="territory-search" onSubmit={search}>
        <label htmlFor="city-q">Buscar município</label>
        <input id="city-q" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Ex.: Belo Horizonte" />
        <button className="secondary-button" type="submit">Buscar</button>
      </form>
      {found.length > 0 && <ul className="territory-found">{found.map((c) => <li key={c.ibge_code}><button className="quiet-button" onClick={() => open(c.ibge_code)}>{c.name} · {c.uf} · {fmt(c.population, 0)} hab.</button></li>)}</ul>}
      {city && <div className="territory-city"><h3 className="subheading">{city.name} · {city.uf} · {city.region}</h3>
        <p className="meta-count">População {fmt(city.population, 0)} · PIB R$ {fmt(city.gdp_bi, 2)} bi · PIB per capita R$ {fmt(city.gdp_per_capita, 0)}</p>
        {Object.entries(byDomain).map(([d, items]) => <div key={d}><h4 className="territory-domain">{DOMAIN_NAMES[d] || d}</h4>
          <ul className="territory-indicators">{items.map((i) => <li key={i.id}><span>{i.label}</span><b>{fmt(i.value, i.unit === '0 a 1' ? 3 : 1)}<small> {i.unit}</small></b>
            <small>{SOURCE[i.source]}{i.delta ? ` · efeito das obras ${i.delta > 0 ? '+' : ''}${fmt(i.delta, 3)}` : ''}</small></li>)}</ul></div>)}
        <p className="meta-count">{city.note}</p></div>}
    </>}

    {view === 'obras' && projects && <>
      <p className="page-description">Projetos de transporte e urbanismo, com custo corrigido pelo índice de preços e prazo de obra. Cada cargo só vê o que lhe cabe.</p>
      <ul className="powers-list">{projects.catalog.map((p) => <li key={p.id} className={p.available ? '' : 'blocked'}>
        <div><b>{p.name}</b><small>{p.text}</small>
          <small className="powers-meta">{p.kind} · R$ {p.cost_bi} bi · {p.months} meses {p.uf ? `· ${p.uf}` : ''} · cargos: {p.who.join(', ')}</small>
          <small className="powers-effects">Efeitos ao concluir: {Object.entries(p.effects).map(([k, v]) => `${v > 0 ? '+' : ''}${v} ${k}`).join(' · ')}</small>
          {p.done && <small className="neg">Já feito ou em andamento.</small>}{!p.available && !p.done && <small className="neg">{p.reason}</small>}</div>
        {projects.can_start && p.available && <div className="powers-actions">
          {!p.city && <><input aria-label="UF" maxLength={2} placeholder="UF" value={pick[p.id]?.uf || ''} onChange={(e) => setPick({ ...pick, [p.id]: { ...pick[p.id], uf: e.target.value.toUpperCase() } })} />
            <input aria-label="Código IBGE do município (opcional)" placeholder="Código IBGE (opcional)" value={pick[p.id]?.city || ''} onChange={(e) => setPick({ ...pick, [p.id]: { ...pick[p.id], city: e.target.value } })} /></>}
          <button className="secondary-button" onClick={() => start(p)}>Iniciar obra</button></div>}
      </li>)}</ul>
      {projects.projects.length > 0 && <><h3 className="subheading">Obras do seu governo</h3><ul className="meta-notes">{projects.projects.map((p) => <li key={p.id}>{p.name} ({p.uf}) — {p.status}; R$ {p.cost_bi} bi; término {p.end}</li>)}</ul></>}
      {!projects.can_start && <p className="meta-count">Obras só podem ser iniciadas por quem está no exercício de um cargo executivo.</p>}
    </>}

    {view === 'indicadores' && registry && <>
      <p className="page-description">{registry.count} indicadores. Para cada um: o que o influencia, o que ele influencia e quais cargos agem sobre ele.</p>
      {Object.entries(registry.indicators.reduce((a, i) => { (a[i.domain] ||= []).push(i); return a; }, {})).map(([d, items]) => <details key={d} className="agenda-more"><summary>{DOMAIN_NAMES[d] || d} ({items.length})</summary>
        <ul className="powers-list">{items.map((i) => <li key={i.id}><div><b>{i.label}</b> <small>({i.unit} · fonte: {SOURCE[i.source] || i.source})</small>
          {i.drivers.length > 0 && <small>Depende de: {i.drivers.map((x) => `${x.sign > 0 ? '+' : '−'}${x.label}`).join(', ')}</small>}
          {i.influences.length > 0 && <small>Influencia: {i.influences.map((x) => `${x.sign > 0 ? '+' : '−'}${x.label}`).join(', ')}</small>}
          {Object.keys(i.levers).length > 0 && <small className="powers-effects">Quem age: {Object.entries(i.levers).map(([o, t]) => `${o}: ${t}`).join(' · ')}</small>}</div></li>)}</ul></details>)}
    </>}
  </section>;
}
