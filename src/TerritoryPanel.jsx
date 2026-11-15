import { useEffect, useMemo, useState } from 'react';
import { Page, Section, Segmented, Delta, Badge, Empty, Drawer } from './ui.jsx';
import IndicatorLinks from './IndicatorLinks.jsx';
import GeoMap from './GeoMap.jsx';
import { BRASIL } from './mapData.js';
import './territory.css';

const DOMAIN_NAMES = { economia: 'Economia', fiscal: 'Contas públicas', trabalho: 'Trabalho e renda', desigualdade: 'Pobreza e desigualdade', educacao: 'Educação', saude: 'Saúde', saneamento: 'Saneamento e moradia', infraestrutura: 'Transporte e infraestrutura', seguranca: 'Segurança', ambiente: 'Meio ambiente', instituicoes: 'Instituições e política', demografia: 'População', externo: 'Setor externo' };
const SOURCE = { atlas: 'Atlas (Censo 2010)', ibge: 'IBGE', estimado: 'estimativa do jogo' };
const COLS = [['idhm', 'IDHM', 3], ['gini', 'Gini', 3], ['pobreza', 'Pobreza %', 1], ['esperanca_vida', 'Esperança de vida', 1], ['mortalidade_infantil', 'Mort. infantil', 1], ['saneamento_basico', 'Saneamento', 1], ['mobilidade', 'Mobilidade', 1], ['seguranca', 'Segurança', 1]];
const BETTER = { idhm: 'up', gini: 'down', pobreza: 'down', esperanca_vida: 'up', mortalidade_infantil: 'down', saneamento_basico: 'up', mobilidade: 'up', seguranca: 'up' };
const KIND = { transporte: 'Transporte', urbanismo: 'Urbanismo', mobilidade: 'Mobilidade' };
const EFFECT = { mobilidade: 'mobilidade', seguranca: 'segurança', saneamento_basico: 'saneamento', pobreza: 'pobreza', emprego: 'emprego', pib: 'PIB', gdp_growth: 'PIB', unemployment: 'desemprego', approval: 'aprovação' };
const fmt = (v, d = 1) => (Number.isFinite(Number(v)) ? Number(v).toLocaleString('pt-BR', { minimumFractionDigits: d, maximumFractionDigits: d }) : '—');

// Valor com a unidade ao lado: "7,2%", "R$ 797,7", "93,7 de 100", "74,5 anos".
function valueText(i) {
  if (i.unit === '0 a 1') return fmt(i.value, 3);
  if (i.unit === '0 a 100') return `${fmt(i.value, 1)} de 100`;
  if (i.unit === '%') return `${fmt(i.value, 1)}%`;
  if (i.unit === 'R$') return `R$ ${fmt(i.value, 1)}`;
  return `${fmt(i.value, 1)} ${i.unit || ''}`.trim();
}

function IndicatorTable({ items, showSource }) {
  return <div className="ds-table-wrap"><table className="ds-table">
    <thead><tr><th>Indicador</th><th>Valor</th><th>{showSource ? 'Fonte' : 'Desde o início'}</th></tr></thead>
    <tbody>{items.map((i) => <tr key={i.id}>
      <td>{i.label}</td><td><b>{valueText(i)}</b></td>
      <td>{showSource ? <span className="ds-muted">{SOURCE[i.source] || i.source}{i.delta ? ` · efeito das obras ${i.delta > 0 ? '+' : ''}${fmt(i.delta, 3)}` : ''}</span>
        : i.change_since_start ? <Delta value={i.change_since_start} better={i.better} digits={i.unit === '0 a 1' ? 3 : 2} /> : <span className="ds-muted">estável</span>}</td>
    </tr>)}</tbody></table></div>;
}

const groupBy = (items) => items.reduce((acc, i) => { (acc[i.domain] ||= []).push(i); return acc; }, {});

export default function TerritoryPanel({ request, state, onState, onNotice }) {
  const [view, setView] = useState('nacional');
  const [domain, setDomain] = useState(null);
  const [mapKey, setMapKey] = useState('idhm');
  const [mapUf, setMapUf] = useState(null);
  const [overview, setOverview] = useState(null);
  const [error, setError] = useState('');
  const [level, setLevel] = useState('states');
  const [query, setQuery] = useState('');
  const [found, setFound] = useState([]);
  const [city, setCity] = useState(null);
  const [cityDomain, setCityDomain] = useState(null);
  const [projects, setProjects] = useState(null);
  const [registry, setRegistry] = useState(null);
  const [openProject, setOpenProject] = useState(null);
  const [chosenUf, setChosenUf] = useState('');
  const [chosenCity, setChosenCity] = useState(null);
  const [cityQuery, setCityQuery] = useState('');
  const [cityFound, setCityFound] = useState([]);

  useEffect(() => { request('/api/territory').then(setOverview).catch((e) => setError(e.message)); }, [state?.date]);
  useEffect(() => { if (view === 'obras') request('/api/territory/projects').then(setProjects).catch((e) => setError(e.message)); }, [view, state?.date]);
  useEffect(() => { if (view === 'indicadores' && !registry) request('/api/indicators/registry').then(setRegistry).catch((e) => setError(e.message)); }, [view]);

  const nationGroups = useMemo(() => (overview?.nation ? groupBy(overview.nation.indicators) : {}), [overview]);
  const cityGroups = useMemo(() => (city ? groupBy(city.indicators) : {}), [city]);
  const ORDER = Object.keys(DOMAIN_NAMES);
  const domains = Object.keys(nationGroups).sort((a, b) => ORDER.indexOf(a) - ORDER.indexOf(b));
  const activeDomain = domain && nationGroups[domain] ? domain : domains[0];
  const cityDomains = Object.keys(cityGroups).sort((a, b) => ORDER.indexOf(a) - ORDER.indexOf(b));
  const activeCityDomain = cityDomain && cityGroups[cityDomain] ? cityDomain : cityDomains[0];

  async function search(e) {
    e.preventDefault();
    if (query.trim().length < 2) return;
    try { setFound((await request(`/api/territory/search?q=${encodeURIComponent(query)}`)).items); } catch (err) { onNotice?.(err.message); }
  }
  async function open(code) { try { setCity(await request(`/api/territory/city/${code}`)); setCityDomain(null); } catch (err) { onNotice?.(err.message); } }
  async function searchProjectCity(e) {
    e.preventDefault();
    if (cityQuery.trim().length < 2) return;
    try { setCityFound((await request(`/api/territory/search?q=${encodeURIComponent(cityQuery)}`)).items); } catch (err) { onNotice?.(err.message); }
  }
  function openDrawer(p) { setOpenProject(p); setChosenUf(p.uf || ''); setChosenCity(null); setCityQuery(''); setCityFound([]); }
  async function start(p) {
    try {
      const r = await request('/api/territory/projects/start', { method: 'POST', body: JSON.stringify({ project_id: p.id, uf: p.uf || chosenUf, city: p.city || chosenCity?.ibge_code || null }) });
      if (r.state) onState?.(r.state);
      onNotice?.(`Obra iniciada: ${r.project.name} (R$ ${r.project.cost_bi} bi, conclusão em ${r.project.end}).`);
      setProjects(await request('/api/territory/projects'));
      setOpenProject(null);
    } catch (err) { onNotice?.(err.message); }
  }

  if (error) return <Page title="Território e indicadores"><p className="meta-status meta-error" role="alert">{error}</p></Page>;
  if (!overview) return <Page title="Território e indicadores"><Empty title="Carregando…" /></Page>;
  const rows = level === 'states' ? overview.states : overview.regions;

  return <Page title="Território e indicadores" lead="O país, os estados, as cidades e as obras: onde as decisões viram resultado."
    actions={<Segmented label="Visões" value={view} onChange={setView} options={[['nacional', 'Brasil hoje'], ['mapa', 'Estados e regiões'], ['cidade', 'Cidades'], ['obras', 'Obras'], ['indicadores', 'Como se ligam']]} />}>

    {view === 'nacional' && overview.nation && <>
      <p className="ds-muted">Quando PIB, inflação, emprego ou contas mudam, os demais indicadores se ajustam a cada avanço do calendário e chegam aos municípios. {overview.nation.months_recorded} {overview.nation.months_recorded === 1 ? 'mês registrado' : 'meses registrados'}.</p>
      <Segmented label="Assunto" value={activeDomain} onChange={setDomain} options={domains.map((d) => [d, `${DOMAIN_NAMES[d] || d} (${nationGroups[d].length})`])} />
      {activeDomain && <IndicatorTable items={nationGroups[activeDomain]} />}
    </>}

    {view === 'mapa' && <>
      <Segmented label="Nível" value={level} onChange={setLevel} options={[['states', 'Estados'], ['regions', 'Regiões']]} />
      {level === 'states' && (() => {
        const col = COLS.find(([k]) => k === mapKey) || COLS[0];
        const values = Object.fromEntries(overview.states.map((s) => [s.uf, s.indicators[col[0]]]));
        const names = Object.fromEntries(overview.states.map((s) => [s.uf, s.name]));
        const sel = overview.states.find((s) => s.uf === mapUf);
        return <div className="ds-map-layout">
          <div>
            <Segmented label="Indicador do mapa" value={mapKey} onChange={setMapKey} options={COLS.map(([k, l]) => [k, l])} />
            <GeoMap map={BRASIL} values={values} names={names} better={BETTER[col[0]]} digits={col[2]} unit={col[1]} selected={mapUf} onSelect={setMapUf} />
          </div>
          <aside className="ds-map-side">
            {sel ? <><h4>{sel.name}</h4><p className="ds-muted">{fmt(sel.population, 0)} habitantes · PIB R$ {fmt(sel.gdp_bi, 0)} bi</p>
              <ul>{COLS.map(([k, l, d]) => <li key={k}><span>{l}</span><b>{fmt(sel.indicators[k], d)}</b></li>)}</ul></>
              : <p className="ds-muted">Toque em um estado para ver todos os indicadores dele.</p>}
          </aside>
        </div>;
      })()}
      <details className="agenda-more"><summary>Ver tabela completa</summary>
        <div className="ds-table-wrap"><table className="ds-table">
          <thead><tr><th>{level === 'states' ? 'Estado' : 'Região'}</th><th>População</th><th>PIB (R$ bi)</th>{COLS.map(([k, l]) => <th key={k}>{l}</th>)}</tr></thead>
          <tbody><tr><td><b>Brasil</b></td><td>{fmt(overview.country.population, 0)}</td><td>{fmt(overview.country.gdp_bi, 0)}</td>{COLS.map(([k, , d]) => <td key={k}>{fmt(overview.country.indicators[k], d)}</td>)}</tr>
            {rows.map((r) => <tr key={r.uf || r.code}><td>{r.name}</td><td>{fmt(r.population, 0)}</td><td>{fmt(r.gdp_bi, 0)}</td>{COLS.map(([k, , d]) => <td key={k}>{fmt(r.indicators[k], d)}</td>)}</tr>)}</tbody>
        </table></div>
      </details>
      <p className="ds-muted">{overview.note}</p>
    </>}

    {view === 'cidade' && <>
      <form className="ds-search" onSubmit={search}>
        <input type="search" aria-label="Buscar município" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Buscar município (ex.: Belo Horizonte)" />
        <button className="primary-button" type="submit" disabled={query.trim().length < 2}>Buscar</button>
      </form>
      {found.length > 0 && <div className="ds-pick-list" role="list">{found.map((c) => <button key={c.ibge_code} type="button" aria-pressed={city?.ibge_code === c.ibge_code} onClick={() => open(c.ibge_code)}><span>{c.name} · {c.uf}</span><small>{fmt(c.population, 0)} hab.</small></button>)}</div>}
      {!city && found.length === 0 && <Empty title="Escolha uma cidade">Busque pelo nome para ver os indicadores do município e o efeito das obras.</Empty>}
      {city && <Section title={`${city.name} · ${city.uf} · ${city.region}`} hint={`População ${fmt(city.population, 0)} · PIB R$ ${fmt(city.gdp_bi, 2)} bi · PIB per capita R$ ${fmt(city.gdp_per_capita, 0)}`}>
        <Segmented label="Assunto" value={activeCityDomain} onChange={setCityDomain} options={cityDomains.map((d) => [d, DOMAIN_NAMES[d] || d])} />
        {activeCityDomain && <IndicatorTable items={cityGroups[activeCityDomain]} showSource />}
        <p className="ds-muted">{city.note}</p>
      </Section>}
    </>}

    {view === 'obras' && projects && <>
      <p className="ds-muted">Projetos de transporte e urbanismo, com custo corrigido pelo índice de preços e prazo de obra. Cada cargo só vê o que lhe cabe.</p>
      <div className="ds-inv-grid">{projects.catalog.map((p) => <button key={p.id} type="button" className="ds-inv" onClick={() => openDrawer(p)}>
        <span className="ds-muted">{KIND[p.kind] || p.kind}{p.uf ? ` · ${p.uf}` : ''}</span><b>{p.name}</b>
        <small className="ds-muted">R$ {p.cost_bi} bi · {p.months} meses</small>
        {p.done ? <Badge tone="warn">já feito ou em andamento</Badge> : !p.available ? <Badge>indisponível para o seu cargo</Badge> : projects.can_start ? <Badge tone="good">pode iniciar</Badge> : <Badge>só consulta</Badge>}
      </button>)}</div>
      {projects.projects.length > 0 && <Section title="Obras do seu governo">
        <div className="ds-table-wrap"><table className="ds-table"><thead><tr><th>Obra</th><th>UF</th><th>Situação</th><th>Custo</th><th>Término</th></tr></thead>
          <tbody>{projects.projects.map((p) => <tr key={p.id}><td>{p.name}</td><td>{p.uf}</td><td>{p.status}</td><td>R$ {p.cost_bi} bi</td><td>{String(p.end).split('-').reverse().join('/')}</td></tr>)}</tbody></table></div>
      </Section>}
      {!projects.can_start && <p className="ds-muted">Obras só podem ser iniciadas por quem está no exercício de um cargo executivo.</p>}
      {openProject && <Drawer title={openProject.name} onClose={() => setOpenProject(null)}>
        <p>{openProject.text}</p>
        <div className="ds-after"><span>Custo<b>R$ {openProject.cost_bi} bi</b></span><span>Prazo<b>{openProject.months} meses</b></span><span>Tipo<b>{KIND[openProject.kind] || openProject.kind}</b></span></div>
        <h4>Efeitos ao concluir</h4>
        <ul className="ds-list">{Object.entries(openProject.effects).map(([k, v]) => <li key={k}><span className="ds-when">{v > 0 ? '+' : ''}{v}</span><b>{EFFECT[k] || k.replaceAll('_', ' ')}</b></li>)}</ul>
        <p className="ds-muted">Cargos que podem iniciar: {openProject.who.join(', ')}.</p>
        {openProject.done && <p className="neg">Esta obra já foi feita ou está em andamento.</p>}
        {!openProject.available && !openProject.done && <p className="neg">{openProject.reason}</p>}
        {projects.can_start && openProject.available && <>
          {!openProject.uf && <><h4>Onde</h4>
            <div className="ds-party-chips" role="group" aria-label="Estado da obra">{overview.states.map((s) => <button key={s.uf} type="button" aria-pressed={chosenUf === s.uf} title={s.name} onClick={() => { setChosenUf(s.uf); setChosenCity(null); }}><b>{s.uf}</b><span /><small>{s.name}</small></button>)}</div></>}
          {!openProject.city && <><h4>Município (opcional)</h4>
            <form className="ds-search" onSubmit={searchProjectCity}><input type="search" aria-label="Buscar município da obra" value={cityQuery} onChange={(e) => setCityQuery(e.target.value)} placeholder="Nome do município" /><button className="secondary-button" type="submit" disabled={cityQuery.trim().length < 2}>Buscar</button></form>
            {chosenCity && <p><Badge tone="good">{chosenCity.name} · {chosenCity.uf}</Badge> <button type="button" className="ds-link" onClick={() => setChosenCity(null)}>tirar</button></p>}
            <div className="ds-pick-list">{cityFound.filter((c) => !openProject.uf || c.uf === openProject.uf).slice(0, 8).map((c) => <button key={c.ibge_code} type="button" aria-pressed={chosenCity?.ibge_code === c.ibge_code} onClick={() => { setChosenCity(c); setChosenUf(c.uf); }}><span>{c.name} · {c.uf}</span><small>{fmt(c.population, 0)} hab.</small></button>)}</div></>}
          <button type="button" className="primary-button" disabled={!openProject.uf && !chosenUf} onClick={() => start(openProject)}>Iniciar obra{chosenUf && !openProject.uf ? ` em ${chosenUf}` : ''}</button>
        </>}
      </Drawer>}
    </>}

    {view === 'indicadores' && registry && <IndicatorLinks registry={registry} domainNames={DOMAIN_NAMES} />}
  </Page>;
}
