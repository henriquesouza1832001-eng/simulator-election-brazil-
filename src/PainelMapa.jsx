import { useEffect, useState } from 'react';
import GeoMap from './GeoMap.jsx';
import { BRASIL } from './mapData.js';

// Camadas do mapa do Painel: indicadores por estado que o motor mantém.
const LAYERS = [['seguranca', 'Segurança', 1, 'up'], ['pobreza', 'Pobreza %', 1, 'down'], ['saneamento_basico', 'Saneamento', 1, 'up'], ['mobilidade', 'Mobilidade', 1, 'up']];

/** Mapa do país no Painel: o jogador vê onde o país está melhor ou pior e abre o detalhe do estado. */
export default function PainelMapa({ request, state, go }) {
  const [data, setData] = useState(null);
  const [layer, setLayer] = useState(LAYERS[0][0]);
  const [uf, setUf] = useState(null);
  useEffect(() => { request('/api/territory').then(setData).catch(() => setData(null)); }, [state?.date]);
  if (!data?.states) return null;
  const [, , digits, better] = LAYERS.find((l) => l[0] === layer);
  const values = Object.fromEntries(data.states.map((s) => [s.uf, s.indicators[layer]]));
  const names = Object.fromEntries(data.states.map((s) => [s.uf, s.name]));
  const sel = data.states.find((s) => s.uf === uf);
  return <section className="ds-card ds-painel-mapa" aria-label="Mapa do país">
    <header><h4>O país agora</h4><button type="button" className="ds-link" onClick={() => go('Obras e mapa')}>abrir o mapa completo</button></header>
    <div className="ds-seg" role="group" aria-label="Camada do mapa">{LAYERS.map(([k, l]) => <button key={k} type="button" aria-pressed={layer === k} onClick={() => setLayer(k)}>{l}</button>)}</div>
    <GeoMap map={BRASIL} values={values} names={names} better={better} digits={digits} unit={LAYERS.find((l) => l[0] === layer)[1].includes('%') ? '%' : '/100'} selected={uf} onSelect={setUf} />
    {sel && <p className="ds-muted"><b>{sel.name}</b>: {LAYERS.map(([k, l, d]) => `${l} ${Number(sel.indicators[k]).toLocaleString('pt-BR', { minimumFractionDigits: d, maximumFractionDigits: d })}`).join(' · ')}</p>}
  </section>;
}
