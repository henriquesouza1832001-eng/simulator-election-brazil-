import { useEffect, useMemo, useState } from 'react';
import { Page, Section, Segmented, Stat, Group, IndicatorRow, Empty, Badge, fmt } from './ui';

const DOMAIN_NAMES = {
  economia: 'Economia', fiscal: 'Contas públicas', trabalho: 'Trabalho e renda', desigualdade: 'Pobreza e desigualdade', educacao: 'Educação',
  saude: 'Saúde', saneamento: 'Saneamento e moradia', infraestrutura: 'Transporte e infraestrutura', seguranca: 'Segurança', ambiente: 'Meio ambiente',
  instituicoes: 'Instituições e política', demografia: 'População', externo: 'Setor externo',
};
const OFFICE_NAMES = { vereador: 'Vereador', prefeito: 'Prefeito', deputado_estadual: 'Deputado estadual', governador: 'Governador', deputado_federal: 'Deputado federal', senador: 'Senador', presidente: 'Presidente' };
const SOURCE = { atlas: 'Atlas do Desenvolvimento Humano (Censo 2010)', ibge: 'IBGE', estimado: 'estimativa do jogo' };
// Os seis números do topo: chave do motor, rótulo, unidade e o que é bom.
const HEADLINE = [
  ['approval', 'Aprovação do governo', '%', 'up'], ['gdp_growth', 'Crescimento do PIB', '% a.a.', 'up'], ['inflation', 'Inflação', '% a.a.', 'down'],
  ['unemployment', 'Desemprego', '%', 'down'], ['debt_gdp', 'Dívida pública', '% do PIB', 'down'], ['congress_support', 'Base no Congresso', '%', 'up'],
];
const CITY_HEADLINE = ['idhm', 'gini', 'pobreza', 'desemprego', 'esperanca_vida', 'agua_encanada'];

const digitsFor = (unit, value) => (unit === '0 a 1' ? 3 : unit === 'hab.' || Math.abs(Number(value)) >= 1000 ? 0 : 1);
const show = (row) => fmt(row.value, digitsFor(row.unit, row.value));
const unitLabel = (unit) => (unit === '0 a 1' || unit === '0 a 100' ? '' : unit);

function Explain({ meta, row, office }) {
  if (!meta) return <p className="ds-muted">Carregando explicação…</p>;
  const levers = Object.entries(meta.levers || {});
  return <>
    {meta.note && <p>{meta.note}</p>}
    {meta.drivers?.length > 0 && <p><b>O que faz isso mudar:</b></p>}
    {meta.drivers?.length > 0 && <div className="ds-tags">{meta.drivers.map((d) => <span className="ds-tag" key={d.from}>{d.sign > 0 ? '↑' : '↓'} {d.label}</span>)}</div>}
    {meta.influences?.length > 0 && <p><b>O que isso afeta:</b></p>}
    {meta.influences?.length > 0 && <div className="ds-tags">{meta.influences.slice(0, 6).map((d) => <span className="ds-tag" key={d.id}>{d.label}</span>)}</div>}
    {levers.length > 0 && <p><b>Quem pode agir:</b> {levers.map(([k, v]) => `${OFFICE_NAMES[k] || k} (${v})`).join('; ')}.</p>}
    {row.base !== undefined && <p className="ds-muted">Base de partida: {fmt(row.base, digitsFor(row.unit, row.base))} · Fonte: {SOURCE[row.source] || row.source}</p>}
    {!meta.note && !meta.drivers?.length && !levers.length && <p className="ds-muted">Este indicador não tem ligações cadastradas ainda.</p>}
  </>;
}

function Groups({ rows, history, registry, loadRegistry, deltaOf, series, openFirst }) {
  const byDomain = useMemo(() => {
    const acc = {};
    rows.forEach((r) => { (acc[r.domain] ||= []).push(r); });
    return Object.entries(acc).sort((a, b) => Object.keys(DOMAIN_NAMES).indexOf(a[0]) - Object.keys(DOMAIN_NAMES).indexOf(b[0]));
  }, [rows]);
  return byDomain.map(([domain, items], index) => {
    const better = items.filter((r) => { const d = Number(deltaOf(r)); return Number.isFinite(d) && Math.abs(d) >= 0.05 && r.better !== 'neutral' && (d > 0) === (r.better === 'up'); }).length;
    const worse = items.filter((r) => { const d = Number(deltaOf(r)); return Number.isFinite(d) && Math.abs(d) >= 0.05 && r.better !== 'neutral' && (d > 0) !== (r.better === 'up'); }).length;
    const meta = `${items.length} ${items.length === 1 ? 'indicador' : 'indicadores'}${better ? ` · ${better} melhoram` : ''}${worse ? ` · ${worse} pioram` : ''}`;
    return <Group key={domain} title={DOMAIN_NAMES[domain] || domain} meta={meta} open={openFirst && index === 0}>
      <ul className="ds-rows">{items.map((r) => <IndicatorRow key={r.id} name={r.label} value={show(r)} unit={unitLabel(r.unit)} delta={deltaOf(r)} better={r.better} digits={digitsFor(r.unit, r.value) > 1 ? 3 : 1}
        series={series?.(r)} onOpen={loadRegistry}><Explain meta={registry?.[r.id]} row={r} /></IndicatorRow>)}</ul>
    </Group>;
  });
}

export default function IndicatorsPanel({ request, state }) {
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
  const series = (r) => (history || []).slice(-24).map((h) => h[r.id]);

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

  return <Page title="Indicadores" lead={scope === 'pais' ? 'Como o país está agora e como mudou desde o início da partida. Clique em um indicador para ver o que o move.' : 'Como está a cidade escolhida. Os valores de partida vêm do Atlas do Desenvolvimento Humano (Censo 2010); o jogo soma o efeito das suas decisões.'}
    actions={<Segmented label="Escopo" value={scope} onChange={setScope} options={[['pais', 'País'], ['cidade', 'Uma cidade']]} />}>

    {scope === 'pais' && <>
      <Section title="O país em seis números">
        <div className="ds-stats">{HEADLINE.map(([key, label, unit, better]) => { const m = rowsByKey[key]; return m
          ? <Stat key={key} label={label} value={fmt(m.now)} unit={unit} delta={m.delta} better={better} /> : null; })}</div>
      </Section>
      <Section title="Todos os indicadores" hint="Agrupados por assunto. A seta mostra a variação desde o início; verde é melhora, vermelho é piora.">
        <Groups rows={nation} history={history} registry={registry} loadRegistry={loadRegistry} deltaOf={(r) => r.change_since_start} series={series} openFirst />
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
        <Section title="A cidade em seis números">
          <div className="ds-stats">{CITY_HEADLINE.map((id) => { const c = cityByKey[id]; if (!c) return null; const n = nationByKey[id];
            return <Stat key={id} label={c.label.replace(/ \(.*\)/, '')} value={show(c)} unit={unitLabel(c.unit)} delta={c.delta} better={c.better} digits={digitsFor(c.unit, c.value) > 1 ? 3 : 1}
              note={n ? `Brasil: ${show(n)}${unitLabel(n.unit) ? ' ' + unitLabel(n.unit) : ''}` : undefined} />; })}</div>
        </Section>
        <Section title="Todos os indicadores da cidade" hint="A seta mostra a mudança causada pelas decisões da partida em relação ao ponto de partida.">
          <Groups rows={city.indicators} registry={registry} loadRegistry={loadRegistry} deltaOf={(r) => r.delta} openFirst />
        </Section>
        <p className="ds-muted" style={{ fontSize: 13 }}>{city.note}</p>
      </>}
    </>}
  </Page>;
}
