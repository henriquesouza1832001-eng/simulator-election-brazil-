import { useEffect, useMemo, useState } from 'react';
import { Page, Section, Segmented, Stat, Delta, LineChart, Empty, fmt } from './ui';

const DOMAIN_NAMES = {
  economia: 'Economia', fiscal: 'Contas públicas', trabalho: 'Trabalho e renda', desigualdade: 'Pobreza e desigualdade', educacao: 'Educação',
  saude: 'Saúde', saneamento: 'Saneamento e moradia', infraestrutura: 'Transporte e infraestrutura', seguranca: 'Segurança', ambiente: 'Meio ambiente',
  instituicoes: 'Instituições e política', demografia: 'População', externo: 'Setor externo',
};
const ORDER = Object.keys(DOMAIN_NAMES);
const OFFICE_NAMES = { vereador: 'Vereador', prefeito: 'Prefeito', deputado_estadual: 'Deputado estadual', governador: 'Governador', deputado_federal: 'Deputado federal', senador: 'Senador', presidente: 'Presidente' };
const SOURCE = { atlas: 'Atlas do Desenvolvimento Humano (Censo 2010)', ibge: 'IBGE', estimado: 'estimativa do jogo' };
const HEADLINE = [['approval', 'Aprovação', '%', 'up'], ['inflation', 'Inflação', '% a.a.', 'down'], ['unemployment', 'Desemprego', '%', 'down'], ['debt_gdp', 'Dívida pública', '% do PIB', 'down']];
const CITY_HEADLINE = ['idhm', 'pobreza', 'desemprego', 'esperanca_vida'];

const digitsFor = (unit, value) => (unit === '0 a 1' ? 3 : unit === 'hab.' || Math.abs(Number(value)) >= 1000 ? 0 : 1);
const show = (row) => fmt(row.value, digitsFor(row.unit, row.value));
const unitLabel = (unit) => (unit === '0 a 1' || unit === '0 a 100' ? '' : unit);
const isBetter = (r, d) => Number.isFinite(d) && Math.abs(d) >= 0.05 && r.better !== 'neutral' && (d > 0) === (r.better === 'up');
const isWorse = (r, d) => Number.isFinite(d) && Math.abs(d) >= 0.05 && r.better !== 'neutral' && (d > 0) !== (r.better === 'up');

function Detail({ row, delta, meta, series, open, onClose, fav, onFav, onAct, actLabel }) {
  if (!row) return <aside className={`ds-detail ${open ? 'open' : ''}`}><p className="ds-empty-detail">Escolha um indicador na lista para ver o detalhe.</p></aside>;
  const levers = Object.entries(meta?.levers || {});
  const unit = unitLabel(row.unit);
  const points = (series || []).map((v, i) => ({ m: String(i + 1), v }));
  return <aside className={`ds-detail ${open ? 'open' : ''}`} aria-label={`Detalhe: ${row.label}`}>
    <div className="ds-label">{DOMAIN_NAMES[row.domain] || row.domain}</div>
    <h2>{row.label}</h2>
    <div className="ds-big">{show(row)}{unit && <small>{unit}</small>}</div>
    <Delta value={delta} better={row.better} digits={digitsFor(row.unit, row.value) > 1 ? 3 : 1} /> <span className="ds-muted">desde o início</span>
    {points.filter((p) => Number.isFinite(p.v)).length >= 2 && <LineChart points={points} unit={unit} labels={['início', 'agora']} />}
    {!meta && <p className="ds-muted" style={{ marginTop: 14 }}>Carregando explicação…</p>}
    {meta?.note && <><h3>Em uma frase</h3><p>{meta.note}</p></>}
    {meta?.drivers?.length > 0 && <><h3>O que faz isso mudar</h3><div className="ds-tags">{meta.drivers.map((d) => <span className="ds-tag" key={d.from}>{d.sign > 0 ? '↑' : '↓'} {d.label}</span>)}</div></>}
    {meta?.influences?.length > 0 && <><h3>O que isso afeta</h3><div className="ds-tags">{meta.influences.slice(0, 6).map((d) => <span className="ds-tag" key={d.id}>{d.label}</span>)}</div></>}
    {levers.length > 0 && <><h3>Quem pode agir</h3><p>{levers.map(([k, v]) => `${OFFICE_NAMES[k] || k}: ${v}`).join('. ')}.</p></>}
    {row.base !== undefined && <><h3>Ponto de partida</h3><p>{fmt(row.base, digitsFor(row.unit, row.base))}{unit ? ` ${unit}` : ''} · {SOURCE[row.source] || row.source}</p></>}
    <div className="ds-detail-actions">
      {onFav && <button type="button" className="ds-btn" aria-pressed={fav} onClick={onFav}>{fav ? '★ Nos meus indicadores' : '☆ Fixar no topo'}</button>}
      {onAct && <button type="button" className="ds-btn primary" onClick={onAct}>{actLabel || 'Agir sobre isso'}</button>}
      <button type="button" className="ds-btn ds-close" onClick={onClose}>Fechar</button>
    </div>
  </aside>;
}

function Master({ rows, deltaOf, seriesOf, registry, loadRegistry, pick, favs, toggleFav, onAct, actLabel }) {
  const subjects = useMemo(() => {
    const acc = {};
    rows.forEach((r) => { (acc[r.domain] ||= []).push(r); });
    return Object.entries(acc).sort((a, b) => ORDER.indexOf(a[0]) - ORDER.indexOf(b[0]));
  }, [rows]);
  const [domain, setDomain] = useState(null);
  const [selected, setSelected] = useState(null);
  const [open, setOpen] = useState(false);
  const active = subjects.find(([k]) => k === domain) || subjects[0];
  const items = active ? active[1] : [];
  const row = items.find((r) => r.id === selected) || items[0];

  useEffect(() => { loadRegistry(); }, []);
  useEffect(() => { if (pick) { const r = rows.find((x) => x.id === pick.id); if (r) { setDomain(r.domain); setSelected(r.id); setOpen(true); } } }, [pick]);
  if (!active) return <Empty title="Sem indicadores para mostrar" />;

  return <div className="ds-master">
    <nav className="ds-subjects" aria-label="Assuntos">
      {subjects.map(([key, list]) => {
        const better = list.filter((r) => isBetter(r, deltaOf(r))).length, worse = list.filter((r) => isWorse(r, deltaOf(r))).length;
        return <button key={key} type="button" className="ds-subject" aria-pressed={active[0] === key} onClick={() => { setDomain(key); setSelected(null); setOpen(false); }}>
          <b>{DOMAIN_NAMES[key] || key}</b>
          <small>{list.length} {list.length === 1 ? 'indicador' : 'indicadores'}{better ? ` · ${better} melhoram` : ''}{worse ? ` · ${worse} pioram` : ''}</small>
        </button>;
      })}
    </nav>
    <div className="ds-items" role="listbox" aria-label={`Indicadores de ${DOMAIN_NAMES[active[0]] || active[0]}`}>
      {items.map((r) => <button key={r.id} type="button" role="option" aria-selected={row?.id === r.id} className="ds-item" onClick={() => { setSelected(r.id); setOpen(true); }}>
        <span className="ds-n">{r.label}</span>
        <span className="ds-v">{show(r)}{unitLabel(r.unit) && <small>{unitLabel(r.unit)}</small>}</span>
        <Delta value={deltaOf(r)} better={r.better} digits={digitsFor(r.unit, r.value) > 1 ? 3 : 1} />
      </button>)}
    </div>
    <Detail row={row} delta={row ? deltaOf(row) : null} meta={row ? registry?.[row.id] : null} series={row ? seriesOf?.(row) : null} open={open} onClose={() => setOpen(false)} fav={row ? favs?.includes(row.id) : false} onFav={toggleFav && row ? () => toggleFav(row.id) : null} onAct={onAct} actLabel={actLabel} />
  </div>;
}

export default function IndicatorsPanel({ request, state, onAct, actLabel }) {
  const [pick, setPick] = useState(null);
  const [favs, setFavs] = useState(() => { try { return JSON.parse(window.localStorage.getItem('quatroanos.favs') || '[]'); } catch { return []; } });
  const toggleFav = (id) => setFavs((cur) => { const next = cur.includes(id) ? cur.filter((x) => x !== id) : [...cur, id].slice(-6); try { window.localStorage.setItem('quatroanos.favs', JSON.stringify(next)); } catch { /* sem armazenamento */ } return next; });
  const [scope, setScope] = useState('pais');
  const [nation, setNation] = useState(null);
  const [history, setHistory] = useState(null);
  const [review, setReview] = useState(null);
  const [registry, setRegistry] = useState(null);
  const [city, setCity] = useState(null);
  const [cityCode, setCityCode] = useState(null);
  const [query, setQuery] = useState('');
  const [found, setFound] = useState([]);
  const [error, setError] = useState('');

  useEffect(() => {
    request('/api/territory').then((t) => {
      setNation(t.nation.indicators);
      const keys = t.nation.indicators.map((i) => i.id).join(',');
      request(`/api/indicators/nation/history?keys=${keys}`).then((h) => setHistory(h.series)).catch(() => setHistory([]));
    }).catch((e) => setError(e.message));
    request('/api/mandate/review').then(setReview).catch(() => setReview(null));
  }, [state?.date]);

  useEffect(() => {
    if (scope !== 'cidade' || cityCode) return;
    request('/api/territory/home').then((h) => { if (h.ibge_code) setCityCode(h.ibge_code); }).catch(() => {});
  }, [scope]);
  useEffect(() => { if (cityCode) request(`/api/territory/city/${cityCode}`).then(setCity).catch((e) => setError(e.message)); }, [cityCode, state?.date]);

  const loadRegistry = () => { if (!registry) request('/api/indicators/registry').then((r) => setRegistry(Object.fromEntries(r.indicators.map((i) => [i.id, i])))).catch(() => {}); };
  const seriesOf = (r) => (history || []).map((h) => h[r.id]);

  async function search(e) {
    e.preventDefault();
    if (query.trim().length < 2) return;
    setFound((await request(`/api/territory/search?q=${encodeURIComponent(query)}`)).items);
  }

  if (error) return <Page title="Indicadores"><p className="ds-empty" role="alert">{error}</p></Page>;
  if (!nation) return <Page title="Indicadores"><p className="ds-muted" role="status">Carregando…</p></Page>;

  const rowsByKey = Object.fromEntries((review?.metrics || []).map((m) => [m.key, m]));
  const cityByKey = city ? Object.fromEntries(city.indicators.map((i) => [i.id, i])) : {};
  const nationByKey = Object.fromEntries(nation.map((i) => [i.id, i]));
  const scored = nation.map((r) => ({ r, d: r.change_since_start, rel: Math.abs(r.change_since_start) / Math.max(Math.abs(r.base ?? r.value), 0.5) })).filter((x) => Number.isFinite(x.d) && x.r.better !== 'neutral' && Math.abs(x.d) >= 0.05).sort((a, b) => b.rel - a.rel);
  const moves = { up: scored.filter((x) => isBetter(x.r, x.d)).slice(0, 3).map((x) => x.r), down: scored.filter((x) => isWorse(x.r, x.d)).slice(0, 3).map((x) => x.r) };

  return <Page title="Indicadores" lead={scope === 'pais' ? 'Como o país está agora e como mudou desde o início. Escolha um assunto e um indicador para ver o que o move.' : 'Como está a cidade escolhida. Os valores de partida vêm do Atlas do Desenvolvimento Humano (Censo 2010); o jogo soma o efeito das suas decisões.'}
    actions={<Segmented label="Escopo" value={scope} onChange={setScope} options={[['pais', 'País'], ['cidade', 'Uma cidade']]} />}>

    {scope === 'pais' && <>
      <Section title={favs.length ? 'Meus indicadores' : undefined} hint={favs.length ? undefined : 'Abra um indicador e use "Fixar no topo" para montar sua lista.'}>
        <div className="ds-stats">{favs.length ? favs.map((id) => { const r = nationByKey[id]; return r ? <button key={id} type="button" className="ds-stat-btn" onClick={() => setPick({ id, n: Date.now() })}><Stat label={r.label.replace(/ (.*)/, '')} value={show(r)} unit={unitLabel(r.unit)} delta={r.change_since_start} better={r.better} digits={digitsFor(r.unit, r.value) > 1 ? 3 : 1} /></button> : null; }) : HEADLINE.map(([key, label, unit, better]) => { const m = rowsByKey[key]; return m ? <Stat key={key} label={label} value={fmt(m.now)} unit={unit} delta={m.delta} better={better} /> : null; })}</div>
      </Section>
      {moves.up.length + moves.down.length > 0 && <Section title="O que mudou desde o início" hint="As maiores melhoras e quedas, em relação ao ponto de partida. Toque para abrir.">
        <div className="ds-moves">
          {[['Melhoraram', moves.up, 'good'], ['Pioraram', moves.down, 'bad']].map(([title, list, tone]) => <article key={title} className="ds-card"><h4>{title}</h4>{list.length === 0 ? <p className="ds-muted">Nada relevante.</p> : <ul>{list.map((r) => <li key={r.id}><button type="button" onClick={() => setPick({ id: r.id, n: Date.now() })}><span>{r.label}</span><Delta value={r.change_since_start} better={r.better} digits={digitsFor(r.unit, r.value) > 1 ? 3 : 1} /></button></li>)}</ul>}</article>)}
        </div>
      </Section>}
      <Section title="Todos os indicadores">
        <Master pick={pick} favs={favs} toggleFav={toggleFav} onAct={onAct} actLabel={actLabel} rows={nation} deltaOf={(r) => r.change_since_start} seriesOf={seriesOf} registry={registry} loadRegistry={loadRegistry} />
      </Section>
    </>}

    {scope === 'cidade' && <>
      <form className="ds-card" onSubmit={search} style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 16 }}>
        <input aria-label="Buscar cidade" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Buscar outra cidade (ex.: Belo Horizonte)" style={{ flex: '1 1 240px', minHeight: 40, padding: '0 12px', borderRadius: 8, border: '1px solid var(--ds-line-2)', background: 'var(--ds-bg)', color: 'var(--ds-ink)', font: 'inherit' }} />
        <button className="secondary-button" type="submit">Buscar</button>
      </form>
      {found.length > 0 && <div className="ds-tags" style={{ marginBottom: 16 }}>{found.slice(0, 12).map((c) => <button key={c.ibge_code} type="button" className="ds-tag" style={{ cursor: 'pointer', background: 'transparent' }} onClick={() => { setCityCode(c.ibge_code); setFound([]); setQuery(''); }}>{c.name} · {c.state_code || c.uf}</button>)}</div>}
      {!city && <Empty title="Escolha uma cidade">Busque pelo nome acima. Se você jogar a carreira, a cidade do seu cargo abre sozinha.</Empty>}
      {city && <>
        <p className="ds-lead" style={{ margin: '0 0 14px' }}><b style={{ color: 'var(--ds-ink)' }}>{city.name}</b> · {city.uf} · {city.region}{city.population ? ` · ${Number(city.population).toLocaleString('pt-BR')} habitantes` : ''}{city.gdp_per_capita ? ` · PIB per capita R$ ${Number(city.gdp_per_capita).toLocaleString('pt-BR')}` : ''}</p>
        <Section>
          <div className="ds-stats">{CITY_HEADLINE.map((id) => { const c = cityByKey[id]; if (!c) return null; const n = nationByKey[id];
            return <Stat key={id} label={c.label.replace(/ \(.*\)/, '')} value={show(c)} unit={unitLabel(c.unit)} delta={c.delta} better={c.better} digits={digitsFor(c.unit, c.value) > 1 ? 3 : 1}
              note={n ? `Brasil: ${show(n)}${unitLabel(n.unit) ? ' ' + unitLabel(n.unit) : ''}` : undefined} />; })}</div>
        </Section>
        <Section title="Todos os indicadores da cidade" hint="A seta mostra a mudança causada pelas decisões da partida em relação ao ponto de partida.">
          <Master rows={city.indicators} deltaOf={(r) => r.delta} registry={registry} loadRegistry={loadRegistry} />
        </Section>
        <p className="ds-muted" style={{ fontSize: 13 }}>{city.note}</p>
      </>}
    </>}
  </Page>;
}
