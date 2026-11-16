import { useEffect, useState } from 'react';
import { Page, Section, Empty, Badge, LineChart } from './ui.jsx';
import { br, dataBr } from './format';

const FORMAT = {
  cambio: (v) => `R$ ${br(v, 2)}`,
  bolsa: (v) => `${br(v / 1000, 1)} mil`,
  selic: (v) => `${br(v, 2)}%`,
  risco: (v) => br(v, 0),
  expect: (v) => `${br(v, 1)}%`,
};
const SERIES = [['cambio', 'Dólar (R$)', 'cambio'], ['bolsa', 'Bolsa (pontos)', 'bolsa'], ['risco', 'Risco-país (pontos)', 'risco'], ['selic', 'Selic (% a.a.)', 'selic']];

function Quote({ row }) {
  const up = row.change_pct > 0.05, down = row.change_pct < -0.05;
  const good = (row.better === 'up' && up) || (row.better === 'down' && down);
  const bad = (row.better === 'up' && down) || (row.better === 'down' && up);
  return <article className={`ds-quote ${good ? 'good' : bad ? 'bad' : ''}`}>
    <span>{row.label}</span>
    <b>{FORMAT[row.id](row.value)}</b>
    <em>{up ? '▲' : down ? '▼' : '■'} {br(Math.abs(row.change_pct), 1)}% desde o início</em>
  </article>;
}

export default function MercadoPanel({ request, state }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  useEffect(() => { request('/api/macro').then(setData).catch((e) => setError(e.message)); }, [state?.date]);
  if (error) return <Page title="Mercado"><Empty title="Não foi possível carregar">{error}</Empty></Page>;
  if (!data) return <Page title="Mercado"><Empty title="Carregando…" /></Page>;
  const hist = data.history || [];
  return <Page title="Mercado" lead="Dólar, bolsa, juros e risco-país reagem na hora às suas decisões e seguem as contas públicas, a inflação e a confiança.">
    <div className="ds-quotes">{data.indicators.map((row) => <Quote key={row.id} row={row} />)}</div>
    <Section title="Por que o mercado está assim" hint={`Juro real de ${br(data.real_rate, 1)}% a.a. · confiança de empresas e consumidores em ${br(data.confianca, 0)} de 100.`}>
      <ul className="ds-list">{data.drivers.map((d) => <li key={d}>{d}</li>)}</ul>
    </Section>
    <Section title="O que moveu o mercado" hint="As últimas reações a decisões, votações, crises e ao movimento do período.">
      {data.news.length === 0 ? <Empty title="Nada ainda">Quando você decidir algo, a reação aparece aqui.</Empty> : <ul className="ds-market-news">
        {data.news.map((n, i) => <li key={`${n.date}-${i}`}>
          <time>{dataBr(n.date)}</time>
          <p>{n.text}</p>
          <div className="ds-market-tags">
            <Badge tone={n.bolsa_pct >= 0 ? 'good' : 'bad'}>bolsa {n.bolsa_pct > 0 ? '+' : ''}{br(n.bolsa_pct, 1)}%</Badge>
            <Badge tone={n.cambio_pct <= 0 ? 'good' : 'bad'}>dólar {n.cambio_pct > 0 ? '+' : ''}{br(n.cambio_pct, 1)}%</Badge>
            <Badge tone={n.risco_bps <= 0 ? 'good' : 'bad'}>risco {n.risco_bps > 0 ? '+' : ''}{n.risco_bps}</Badge>
          </div>
        </li>)}
      </ul>}
    </Section>
    <Section title="Evolução">
      <div className="ds-charts">{SERIES.map(([key, title]) => <div key={key} className="ds-card"><h4>{title}</h4>
        <LineChart points={hist.map((h) => ({ m: h.month, v: h[key] }))} unit="" /></div>)}</div>
    </Section>
    <p className="ds-muted">{data.note}</p>
  </Page>;
}


/** Faixa compacta para o Painel: dólar, bolsa, risco e Selic com a variação desde o início. */
export function MercadoFaixa({ request, state, go }) {
  const [data, setData] = useState(null);
  useEffect(() => { request('/api/macro').then(setData).catch(() => setData(null)); }, [state?.date]);
  if (!data) return null;
  return <button type="button" className="ds-market-strip" onClick={() => go('Mercado')} aria-label="Abrir a tela Mercado">
    {data.indicators.filter((r) => ['cambio', 'bolsa', 'risco', 'selic'].includes(r.id)).map((r) => {
      const up = r.change_pct > 0.05, down = r.change_pct < -0.05;
      const good = (r.better === 'up' && up) || (r.better === 'down' && down), bad = (r.better === 'up' && down) || (r.better === 'down' && up);
      return <span key={r.id} className={good ? 'good' : bad ? 'bad' : ''}><small>{r.label}</small><b>{FORMAT[r.id](r.value)}</b><em>{up ? '▲' : down ? '▼' : '■'} {br(Math.abs(r.change_pct), 1)}%</em></span>;
    })}
  </button>;
}
