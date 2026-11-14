import { useEffect, useMemo, useState } from 'react';
import { Page, Section, Segmented, LineChart, Stat, Badge, Empty, Delta, fmt } from './ui';
import { effectText } from './format';

// id do motor, rótulo, unidade e o que é bom
const OPTIONS = [
  ['aprovacao', 'Aprovação', '%', 'up'], ['inflacao', 'Inflação', '% a.a.', 'down'], ['desemprego', 'Desemprego', '%', 'down'], ['divida_pib', 'Dívida', '% do PIB', 'down'],
  ['resultado_primario', 'Resultado primário', '% do PIB', 'up'], ['crescimento_pib', 'Crescimento do PIB', '% a.a.', 'up'], ['base_legislativa', 'Base no Congresso', '%', 'up'],
  ['confianca_institucional', 'Confiança institucional', '/100', 'up'], ['integridade', 'Integridade', '/100', 'up'], ['pobreza', 'Pobreza', '%', 'down'], ['gini', 'Desigualdade (Gini)', '', 'down'],
];
const monthName = (iso) => new Date(`${iso.slice(0, 7)}-15T12:00:00`).toLocaleDateString('pt-BR', { month: 'long', year: 'numeric' });
const dayName = (iso) => new Date(`${iso}T12:00:00`).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' });
const toneOf = (status = '') => (status.startsWith('aprovad') || status === 'respondida' ? 'good' : /rejeit|agravad|negad/.test(status) ? 'bad' : /tramit/.test(status) ? 'warn' : '');
const PAGE = 15;

export default function HistoryPanel({ request, state }) {
  const [view, setView] = useState('evolucao');
  const [key, setKey] = useState('aprovacao');
  const [series, setSeries] = useState(null);
  const [ledger, setLedger] = useState(null);
  const [budget, setBudget] = useState(null);
  const [shown, setShown] = useState(PAGE);

  useEffect(() => { request(`/api/indicators/nation/history?keys=${OPTIONS.map((o) => o[0]).join(',')}`).then((r) => setSeries(r.series)).catch(() => setSeries([])); }, [state?.date]);
  useEffect(() => { request('/api/ledger').then((r) => setLedger(r.entries || [])).catch(() => setLedger([])); }, [state?.date]);
  useEffect(() => { request('/api/budget/history').then(setBudget).catch(() => setBudget(null)); }, [state?.date]);

  const [, label, unit, better] = OPTIONS.find((o) => o[0] === key);
  const points = useMemo(() => (series || []).map((s) => ({ m: s.month, v: s[key] })), [series, key]);
  const valid = points.filter((p) => Number.isFinite(p.v));
  const first = valid[0], last = valid[valid.length - 1];
  const peak = valid.length ? valid.reduce((a, b) => (b.v > a.v ? b : a)) : null;
  const low = valid.length ? valid.reduce((a, b) => (b.v < a.v ? b : a)) : null;

  const entries = ledger || [];
  const groups = useMemo(() => {
    const out = [];
    entries.slice(0, shown).forEach((e) => {
      const m = (e.date || '').slice(0, 7);
      if (!out.length || out[out.length - 1].m !== m) out.push({ m, items: [] });
      out[out.length - 1].items.push(e);
    });
    return out;
  }, [entries, shown]);

  return <Page title="Histórico" lead="O que mudou no país e o que foi decidido, desde o primeiro dia da partida."
    actions={<Segmented label="Tipo de histórico" value={view} onChange={setView} options={[['evolucao', 'Evolução'], ['decisoes', 'Decisões'], ['orcamento', 'Orçamento']]} />}>

    {view === 'evolucao' && <>
      <div className="ds-pick" role="group" aria-label="Indicador">{OPTIONS.map(([k, l]) => <button key={k} type="button" aria-pressed={key === k} onClick={() => setKey(k)}>{l}</button>)}</div>
      {!series ? <p className="ds-muted" role="status">Carregando…</p> : <>
        <LineChart points={points} unit={unit} labels={first && last ? [monthName(first.m + '-01'), monthName(last.m + '-01')] : undefined} />
        {first && last && <Section>
          <div className="ds-stats">
            <Stat label="No início" value={fmt(first.v)} unit={unit} />
            <Stat label="Agora" value={fmt(last.v)} unit={unit} delta={last.v - first.v} better={better} />
            {peak && <Stat label="Ponto mais alto" value={fmt(peak.v)} unit={unit} note={monthName(peak.m + '-01')} />}
            {low && <Stat label="Ponto mais baixo" value={fmt(low.v)} unit={unit} note={monthName(low.m + '-01')} />}
          </div>
        </Section>}
      </>}
    </>}

    {view === 'decisoes' && <>
      {ledger === null ? <p className="ds-muted" role="status">Carregando…</p> : entries.length === 0
        ? <Empty title="Nenhuma decisão registrada ainda">Quando você decretar, enviar projetos ou responder a crises, cada decisão aparece aqui com o que se esperava e o que aconteceu.</Empty>
        : <>
          {groups.map((g) => <div key={g.m}>
            <h3 className="ds-month">{monthName(g.m + '-15')}</h3>
            <ul className="ds-timeline">{g.items.map((e) => <li key={e.id} className={toneOf(e.status)}>
              <time dateTime={e.date}>{dayName(e.date)}</time>
              <b>{e.title} {e.status && <Badge tone={toneOf(e.status)}>{e.status}</Badge>}</b>
              {(effectText(e.forecast) || effectText(e.result)) && <p>{effectText(e.forecast) && <>Esperado: {effectText(e.forecast)}. </>}{e.result ? (effectText(e.result) ? <>Resultado: {effectText(e.result)}.</> : 'Resultado: sem efeito medido.') : 'Aguardando resultado.'}</p>}
              {e.reason && <p className="ds-muted">{e.reason}</p>}
              {e.cost && <p className="ds-muted">Custo: {e.cost}</p>}
            </li>)}</ul>
          </div>)}
          {entries.length > shown && <button className="secondary-button" onClick={() => setShown(shown + PAGE)}>Mostrar mais ({entries.length - shown})</button>}
        </>}
    </>}

    {view === 'orcamento' && <>
      {!budget || budget.ytd.length === 0
        ? <Empty title="O orçamento começa a ser registrado depois do primeiro mês">Avance o calendário para ver o previsto e o executado de cada função.</Empty>
        : <Section title={`Investimento por função em ${budget.year}`} hint="Previsto é a dotação do ano dividida por 12; executado soma os gastos extras das suas decisões. Valores em R$ bilhões.">
          <div className="ds-table-wrap"><table className="ds-table"><thead><tr><th>Função</th><th>Previsto</th><th>Executado</th><th>Diferença</th></tr></thead>
            <tbody>{budget.ytd.map((r) => <tr key={r.function}><td>{r.label}</td><td>{fmt(r.planned_bi, 2)}</td><td>{fmt(r.executed_bi, 2)}</td>
              <td><Delta value={r.difference_bi} better="down" digits={2} /></td></tr>)}</tbody></table></div>
          <p className="ds-muted" style={{ fontSize: 13, marginTop: 10 }}>{budget.note}</p>
        </Section>}
    </>}
  </Page>;
}
