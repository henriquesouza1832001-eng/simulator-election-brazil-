import { useMemo, useState } from 'react';
import { Drawer, Segmented } from './ui.jsx';

const SOURCE = { atlas: 'Atlas (Censo 2010)', ibge: 'IBGE', estimado: 'estimativa do jogo' };

/** "Como os indicadores se ligam": um assunto por vez, cartões curtos e o detalhe em painel lateral. */
export default function IndicatorLinks({ registry, domainNames }) {
  const groups = useMemo(() => {
    const acc = {};
    registry.indicators.forEach((i) => { (acc[i.domain] ||= []).push(i); });
    return acc;
  }, [registry]);
  const byId = useMemo(() => Object.fromEntries(registry.indicators.map((i) => [i.id, i])), [registry]);
  const keys = Object.keys(groups);
  const [domain, setDomain] = useState(keys[0]);
  const [openId, setOpenId] = useState(null);
  const current = openId ? byId[openId] : null;
  const jump = (id) => { if (byId[id]) setOpenId(id); };
  const Tags = ({ list }) => <div className="ds-tags">{list.map((x) => {
    const id = x.from || x.id;
    return <button type="button" key={id} className="ds-tag" disabled={!byId[id]} onClick={() => jump(id)}>{x.sign > 0 ? '↑' : '↓'} {x.label}</button>;
  })}</div>;

  return <>
    <p className="ds-lead">{registry.count} indicadores. Escolha um assunto e toque em um indicador para ver o que o move, o que ele afeta e quem pode agir.</p>
    <Segmented label="Assunto" value={domain} onChange={setDomain} options={keys.map((k) => [k, `${domainNames[k] || k} (${groups[k].length})`])} />
    <div className="ds-link-grid">
      {groups[domain].map((i) => <button key={i.id} type="button" className="ds-inv" onClick={() => setOpenId(i.id)}>
        <b>{i.label}</b>
        <small className="ds-muted">{i.drivers.length} causa(s) · {i.influences.length} efeito(s)</small>
      </button>)}
    </div>
    {current && <Drawer title={current.label} onClose={() => setOpenId(null)}>
      <p className="ds-muted">{domainNames[current.domain] || current.domain} · {current.unit} · fonte: {SOURCE[current.source] || current.source}</p>
      {current.drivers.length > 0 && <><h4>O que faz isso mudar</h4><Tags list={current.drivers} /></>}
      {current.influences.length > 0 && <><h4>O que isso afeta</h4><Tags list={current.influences} /></>}
      {Object.keys(current.levers).length > 0 && <><h4>Quem pode agir</h4><p>{Object.entries(current.levers).map(([o, t]) => `${o}: ${t}`).join('. ')}.</p></>}
    </Drawer>}
  </>;
}
