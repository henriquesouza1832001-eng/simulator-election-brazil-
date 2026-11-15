import { useMemo, useState } from 'react';
import { fmt } from './ui.jsx';

// Pior → melhor (quando se sabe o que é bom) ou menor → maior (neutro). Distinguíveis também sem cor: a legenda traz as faixas em texto.
const GOOD_SCALE = ['#e8695b', '#e9a15a', '#9aa7bd', '#7fc4a0', '#3fd27f'];
const FLAT_SCALE = ['#244a78', '#2f6aa3', '#5d8fc4', '#c9a73a', '#ffd23f'];

/** Mapa colorido (coropleto) em SVG puro. `map` vem de mapData.js; `values` é { id: número }.
 *  better: 'up' | 'down' | undefined — define se a escala vai de vermelho a verde. */
export default function GeoMap({ map, values, better, unit = '', digits = 1, names = {}, selected, onSelect, noData = 'sem dado no jogo' }) {
  const [hover, setHover] = useState(null);
  const nums = useMemo(() => Object.values(values).filter((v) => Number.isFinite(Number(v))).map(Number), [values]);
  const min = Math.min(...nums), max = Math.max(...nums);
  const scale = better ? GOOD_SCALE : FLAT_SCALE;
  const bin = (v) => {
    if (!Number.isFinite(Number(v)) || max === min) return -1;
    const k = Math.min(4, Math.floor(((Number(v) - min) / (max - min)) * 5));
    return better === 'down' ? 4 - k : k;
  };
  const colorOf = (id) => { const b = bin(values[id]); return b < 0 ? '#2a3a52' : scale[b]; };
  const shown = hover || selected;
  const step = (max - min) / 5;
  const legend = scale.map((c, i) => {
    const idx = better === 'down' ? 4 - i : i; // posição do bin na escala numérica
    return { c, from: min + step * idx, to: min + step * (idx + 1), order: idx };
  }).sort((a, b) => a.order - b.order);

  return <figure className="ds-geomap">
    <svg viewBox={map.viewBox} role="group" aria-label="Mapa">
      {map.items.map((it) => <path key={it.id} d={it.d} fill={colorOf(it.id)} stroke="var(--ds-bg)" strokeWidth="1"
        className={selected === it.id ? 'on' : ''} tabIndex={0} role="button" aria-label={`${names[it.id] || it.id}: ${Number.isFinite(Number(values[it.id])) ? `${fmt(values[it.id], digits)} ${unit}` : noData}`}
        onMouseEnter={() => setHover(it.id)} onMouseLeave={() => setHover(null)} onFocus={() => setHover(it.id)} onBlur={() => setHover(null)}
        onClick={() => onSelect?.(it.id)} onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onSelect?.(it.id); } }} />)}
    </svg>
    <figcaption>
      <div className="ds-geomap-read" aria-live="polite">{shown
        ? <><b>{names[shown] || shown}</b> <span>{Number.isFinite(Number(values[shown])) ? `${fmt(values[shown], digits)} ${unit}` : noData}</span></>
        : <span className="ds-muted">Passe o mouse ou toque em uma área.</span>}</div>
      <ul className="ds-geomap-legend">{legend.map((l) => <li key={l.order}><i style={{ background: l.c }} />{fmt(l.from, digits)} a {fmt(l.to, digits)}</li>)}
        <li><i style={{ background: '#2a3a52' }} />{noData}</li></ul>
      {better && <small className="ds-muted">Vermelho é pior, verde é melhor.</small>}
    </figcaption>
  </figure>;
}
