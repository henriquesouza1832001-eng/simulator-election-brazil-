import { useEffect, useState } from 'react';
import { Group, Delta, fmt } from './ui';

// O que é bom em cada indicador do balanço.
const BETTER = { approval: 'up', congress_support: 'up', institutional_trust: 'up', integrity: 'up', gdp_growth: 'up', inflation: 'down', unemployment: 'down', debt_gdp: 'down' };

export default function MandateReview({ request, state, data: given }) {
  const [own, setOwn] = useState(null);
  useEffect(() => { if (given === undefined) request('/api/mandate/review').then(setOwn).catch(() => setOwn(null)); }, [state?.date, given]);
  const data = given === undefined ? own : given;
  if (!data) return null;
  const { decisions, cpis } = data;
  return <Group title={data.final ? 'Fim do mandato: balanço final' : 'Balanço do mandato até agora'} meta={`${data.headline} · nota ${data.score}/100 (${data.letter})`} open={data.final}>
    {data.final && <p className="ds-lead" style={{ margin: '0 4px 12px' }}>Os 48 meses acabaram. Veja o que mudou desde o primeiro dia e como o governo foi avaliado. Você pode continuar jogando ou abrir uma nova partida em “Partidas”.</p>}
    <div className="ds-table-wrap"><table className="ds-table"><thead><tr><th>Indicador</th><th>Início</th><th>Agora</th><th>Variação</th></tr></thead>
      <tbody>{data.metrics.map((r) => <tr key={r.key}><td>{r.label}</td><td>{fmt(r.start)} {r.unit}</td><td>{fmt(r.now)} {r.unit}</td><td><Delta value={r.delta} better={BETTER[r.key] || 'up'} /></td></tr>)}</tbody></table></div>
    <p className="ds-muted" style={{ margin: '12px 4px 0', fontSize: 14 }}>{decisions.recorded} decisões registradas, {decisions.approved} aprovadas e {decisions.setbacks} revezes (rejeições ou crises sem resposta).
      {cpis.total > 0 ? ` ${cpis.total} ${Number(cpis.total) === 1 ? 'CPI' : 'CPIs'}, ${cpis.against_government} contra o governo e ${cpis.with_indictments} com pedido de indiciamento.` : ''}</p>
    <p className="ds-muted" style={{ margin: '6px 4px 4px', fontSize: 13 }}>{data.note}</p>
  </Group>;
}
