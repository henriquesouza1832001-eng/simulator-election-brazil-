import { useMemo, useState } from 'react';

// Adesão ao governo: baixa → alta (vermelho a verde), com faixas em texto na legenda.
const SCALE = ['#e8695b', '#e9a15a', '#9aa7bd', '#7fc4a0', '#3fd27f'];
const binOf = (pct) => Math.max(0, Math.min(4, Math.floor(pct / 20)));

/** Plenário em semicírculo: uma bolinha por cadeira, agrupada por partido (base do governo à esquerda).
 *  parties: [{ id, name, seats, adesao }]. Clique em uma cadeira filtra o partido. */
export default function Hemicycle({ parties, selected, onSelect }) {
  const [hover, setHover] = useState(null);
  const ordered = useMemo(() => [...parties].filter((p) => p.seats > 0).sort((a, b) => b.adesao - a.adesao), [parties]);
  const total = ordered.reduce((n, p) => n + p.seats, 0);

  const seats = useMemo(() => {
    if (!total) return [];
    const rows = total > 200 ? 9 : total > 60 ? 6 : 3;
    const r1 = 100, r0 = 42;
    const radii = Array.from({ length: rows }, (_, i) => r0 + (i * (r1 - r0)) / (rows - 1));
    const sum = radii.reduce((a, b) => a + b, 0);
    let per = radii.map((r) => Math.round((r / sum) * total));
    per[per.length - 1] += total - per.reduce((a, b) => a + b, 0);
    const pts = [];
    radii.forEach((r, i) => {
      const n = per[i];
      for (let k = 0; k < n; k += 1) {
        const a = Math.PI - (n === 1 ? Math.PI / 2 : (k / (n - 1)) * Math.PI);
        pts.push({ x: 110 + r * Math.cos(a), y: 108 - r * Math.sin(a), a, r });
      }
    });
    pts.sort((p, q) => q.a - p.a || p.r - q.r);
    const out = [];
    let idx = 0;
    ordered.forEach((p) => { for (let k = 0; k < p.seats; k += 1) { if (pts[idx]) out.push({ ...pts[idx], party: p }); idx += 1; } });
    return out;
  }, [ordered, total]);

  const dot = total > 200 ? 1.8 : total > 60 ? 4.2 : 5;
  const shown = hover || ordered.find((p) => p.id === selected);
  return <figure className="ds-hemi">
    <svg viewBox="0 0 220 116" role="group" aria-label="Plenário por partido">
      {seats.map((s, i) => <circle key={i} cx={s.x} cy={s.y} r={dot} fill={SCALE[binOf(s.party.adesao)]}
        opacity={selected && selected !== s.party.id ? 0.25 : 1} onMouseEnter={() => setHover(s.party)} onMouseLeave={() => setHover(null)}
        onClick={() => onSelect?.(selected === s.party.id ? 'todos' : s.party.id)} />)}
      <text x="110" y="96" textAnchor="middle" className="ds-hemi-total">{total}</text>
      <text x="110" y="108" textAnchor="middle" className="ds-hemi-sub">cadeiras</text>
    </svg>
    <figcaption>
      <div className="ds-geomap-read" aria-live="polite">{shown
        ? <><b>{shown.id}</b> <span>{shown.name ? `${shown.name} · ` : ''}{shown.seats} cadeiras · adesão {shown.adesao}%</span></>
        : <span className="ds-muted">Passe o mouse em uma cadeira ou toque em um partido abaixo.</span>}</div>
      <ul className="ds-geomap-legend">{SCALE.map((c, i) => <li key={c}><i style={{ background: c }} />adesão {i * 20}–{i === 4 ? 100 : i * 20 + 19}%</li>)}</ul>
    </figcaption>
  </figure>;
}
