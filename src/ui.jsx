import { useState } from 'react';

// Componentes do sistema de design (0.4). Usam só as classes `ds-` de design.css.

export const fmt = (v, d = 1) => (Number.isFinite(Number(v)) && v !== null && v !== '' ? Number(v).toLocaleString('pt-BR', { minimumFractionDigits: d, maximumFractionDigits: d }) : '—');

export function Page({ title, lead, actions, children }) {
  return <section className="ds-page">
    <header className="ds-head">
      <div><h2>{title}</h2>{lead && <p className="ds-lead">{lead}</p>}</div>
      {actions}
    </header>
    {children}
  </section>;
}

export function Section({ title, hint, children }) {
  return <section className="ds-section">
    {title && <h3>{title}</h3>}
    {hint && <p className="ds-hint">{hint}</p>}
    {children}
  </section>;
}

export function Segmented({ options, value, onChange, label }) {
  return <div className="ds-seg" role="group" aria-label={label}>
    {options.map(([key, text]) => <button key={key} type="button" aria-pressed={value === key} onClick={() => onChange(key)}>{text}</button>)}
  </div>;
}

/** Variação com seta; `better` diz se subir é bom ('up'), ruim ('down') ou neutro. */
export function Delta({ value, better = 'up', digits = 1, suffix = '' }) {
  const n = Number(value);
  if (!Number.isFinite(n) || Math.abs(n) < 0.05 * Math.pow(10, 1 - digits)) return <span className="ds-delta flat">estável</span>;
  const good = better === 'neutral' ? null : (n > 0) === (better === 'up');
  const cls = good === null ? 'flat' : good ? 'good' : 'bad';
  return <span className={`ds-delta ${cls}`}>{n > 0 ? '▲' : '▼'} {fmt(Math.abs(n), digits)}{suffix}</span>;
}

export function Stat({ label, value, unit, delta, better, digits = 1, note }) {
  return <div className="ds-stat">
    <span>{label}</span>
    <b>{value}{unit && <small>{unit}</small>}</b>
    {delta !== undefined && delta !== null && <em><Delta value={delta} better={better} digits={digits} /> <span className="ds-muted">desde o início</span></em>}
    {note && <em className="ds-muted">{note}</em>}
  </div>;
}

export function Spark({ values = [], tone = '' }) {
  const pts = values.filter((v) => Number.isFinite(v));
  if (pts.length < 2) return <svg className="ds-spark" viewBox="0 0 96 26" aria-hidden="true"><line x1="0" y1="13" x2="96" y2="13" stroke="currentColor" strokeOpacity=".35" strokeDasharray="3 3" /></svg>;
  const min = Math.min(...pts), max = Math.max(...pts), span = max - min || 1;
  const d = pts.map((v, i) => `${i ? 'L' : 'M'}${(i / (pts.length - 1)) * 96},${24 - ((v - min) / span) * 22}`).join(' ');
  return <svg className={`ds-spark ${tone}`} viewBox="0 0 96 26" preserveAspectRatio="none" aria-hidden="true"><path d={d} fill="none" stroke="currentColor" strokeWidth="2" vectorEffect="non-scaling-stroke" /></svg>;
}

/** Linha de indicador: nome, valor, variação e tendência; abre uma explicação ao clicar. */
export function IndicatorRow({ name, value, unit, delta, better, digits = 1, series, onOpen, children }) {
  const [open, setOpen] = useState(false);
  const good = better === 'neutral' || !Number.isFinite(Number(delta)) || Math.abs(Number(delta)) < 0.05 ? '' : (Number(delta) > 0) === (better === 'up') ? 'good' : 'bad';
  return <li className="ds-row">
    <button type="button" aria-expanded={open} onClick={() => { setOpen(!open); if (!open) onOpen?.(); }}>
      <span className="ds-name">{name}</span>
      <span className="ds-value">{value}{unit && <small>{unit}</small>}</span>
      <Delta value={delta} better={better} digits={digits} />
      <Spark values={series} tone={good} />
    </button>
    {open && <div className="ds-row-more">{children}</div>}
  </li>;
}

export function Group({ title, meta, open = false, children }) {
  return <details className="ds-group" open={open}>
    <summary>{title}{meta && <span className="ds-meta">{meta}</span>}</summary>
    <div className="ds-body">{children}</div>
  </details>;
}

export function Badge({ tone = '', children }) { return <span className={`ds-badge ${tone}`}>{children}</span>; }

export function Empty({ title, children }) { return <div className="ds-empty"><b>{title}</b>{children}</div>; }

export function LineChart({ points, unit = '', labels }) {
  const vals = points.filter((p) => Number.isFinite(p.v));
  if (vals.length < 2) return <Empty title="Ainda não há série suficiente">Avance alguns meses para ver a evolução.</Empty>;
  const min = Math.min(...vals.map((p) => p.v)), max = Math.max(...vals.map((p) => p.v)), span = max - min || 1;
  const d = vals.map((p, i) => `${i ? 'L' : 'M'}${(i / (vals.length - 1)) * 600},${170 - ((p.v - min) / span) * 150}`).join(' ');
  const last = vals[vals.length - 1];
  return <div className="ds-chart">
    <svg viewBox="0 0 600 180" preserveAspectRatio="none" role="img" aria-label={`De ${fmt(vals[0].v)} a ${fmt(last.v)} ${unit}`}>
      <line x1="0" y1="170" x2="600" y2="170" stroke="currentColor" strokeOpacity=".2" />
      <path d={d} fill="none" stroke="currentColor" strokeWidth="2.5" vectorEffect="non-scaling-stroke" />
    </svg>
    <div className="ds-chart-axis"><span>{labels?.[0] ?? vals[0].m} · {fmt(vals[0].v)} {unit}</span><span>mín. {fmt(min)} · máx. {fmt(max)}</span><span>{labels?.[1] ?? last.m} · {fmt(last.v)} {unit}</span></div>
  </div>;
}
