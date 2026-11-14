import { useEffect, useState } from 'react';
import './powers.css';

const fmt = (v, d = 1) => (v == null ? '—' : Number(v).toLocaleString('pt-BR', { minimumFractionDigits: d, maximumFractionDigits: d }));

export default function MandateReview({ request, state }) {
  const [data, setData] = useState(null);
  useEffect(() => { request('/api/mandate/review').then(setData).catch(() => setData(null)); }, [state?.date]);
  if (!data) return null;
  const { decisions, cpis } = data;
  return <details className={`fold mandate-review ${data.final ? 'final' : ''}`} open={data.final}>
    <summary>{data.final ? 'Fim do mandato: balanço final' : 'Balanço do mandato até agora'} <span>{data.headline} · nota {data.score}/100 ({data.letter})</span></summary>
    {data.final && <p className="page-description">Os 48 meses acabaram. Veja abaixo o que mudou desde o primeiro dia e como o governo foi avaliado. Você pode continuar jogando ou abrir uma nova partida em “Partidas”.</p>}
    <div className="territory-table-wrap"><table className="territory-table"><thead><tr><th>Indicador</th><th>Início</th><th>Agora</th><th>Variação</th></tr></thead>
      <tbody>{data.metrics.map((r) => <tr key={r.key}><td>{r.label}</td><td>{fmt(r.start)} {r.unit}</td><td>{fmt(r.now)} {r.unit}</td>
        <td className={r.good == null ? '' : r.good ? 'pos' : 'neg'}>{r.delta == null ? '—' : `${r.delta > 0 ? '+' : ''}${fmt(r.delta, 1)}`}</td></tr>)}</tbody></table></div>
    <p className="meta-count">{decisions.recorded} decisões registradas, {decisions.approved} aprovadas e {decisions.setbacks} revezes (rejeições ou crises sem resposta).
      {cpis.total > 0 ? ` ${cpis.total} CPI(s), ${cpis.against_government} contra o governo e ${cpis.with_indictments} com pedido de indiciamento.` : ''}</p>
    <p className="meta-count">{data.note}</p>
  </details>;
}
