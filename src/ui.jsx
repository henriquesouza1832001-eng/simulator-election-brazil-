import { useEffect, useState } from 'react';
import { roundHalfUp } from './format.js';

// Componentes do sistema de design (0.4). Usam só as classes `ds-` de design.css.

export const fmt = (v, d = 1) => (Number.isFinite(Number(v)) && v !== null && v !== '' ? roundHalfUp(v, d).toLocaleString('pt-BR', { minimumFractionDigits: d, maximumFractionDigits: d }) : '—');

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

const RANGES = [['6', '6 meses', 6], ['12', '1 ano', 12], ['24', '2 anos', 24], ['all', 'Tudo', Infinity]];

/** Gráfico de linha com filtro de período (6 meses, 1 ano, 2 anos, tudo). O filtro só aparece quando há pontos suficientes. */
export function LineChart({ points, unit = '', labels }) {
  const [range, setRange] = useState('all');
  const all = points.filter((p) => Number.isFinite(p.v));
  const usable = RANGES.filter(([, , n]) => n === Infinity || n < all.length);
  const active = usable.some(([k]) => k === range) ? range : 'all';
  const limit = RANGES.find(([k]) => k === active)[2];
  const vals = limit === Infinity ? all : all.slice(-(limit + 1));
  if (all.length < 2) return <Empty title="Ainda não há série suficiente">Avance alguns meses para ver a evolução.</Empty>;
  const min = Math.min(...vals.map((p) => p.v)), max = Math.max(...vals.map((p) => p.v)), span = max - min || 1;
  const d = vals.map((p, i) => `${i ? 'L' : 'M'}${(i / (vals.length - 1)) * 600},${170 - ((p.v - min) / span) * 150}`).join(' ');
  const last = vals[vals.length - 1];
  const firstLabel = active === 'all' ? (labels?.[0] ?? vals[0].m) : `há ${limit} meses`;
  return <div className="ds-chart">
    {usable.length > 1 && <div className="ds-chart-range" role="group" aria-label="Período do gráfico">{usable.map(([k, label]) => <button key={k} type="button" aria-pressed={active === k} onClick={() => setRange(k)}>{label}</button>)}</div>}
    <svg viewBox="0 0 600 180" preserveAspectRatio="none" role="img" aria-label={`De ${fmt(vals[0].v)} a ${fmt(last.v)} ${unit}`}>
      <line x1="0" y1="170" x2="600" y2="170" stroke="currentColor" strokeOpacity=".2" />
      <path d={d} fill="none" stroke="currentColor" strokeWidth="2.5" vectorEffect="non-scaling-stroke" />
    </svg>
    <div className="ds-chart-axis"><span>{firstLabel} · {fmt(vals[0].v)} {unit}</span><span>mín. {fmt(min)} · máx. {fmt(max)}</span><span>{labels?.[1] ?? last.m} · {fmt(last.v)} {unit}</span></div>
  </div>;
}

/** Painel lateral à direita (no celular ocupa a largura toda). Fecha com Esc, clique fora ou no ×. */
export function Drawer({ title, onClose, children, footer }) {
  useEffect(() => {
    const onKey = (e) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);
  return <div className="ds-drawer-backdrop" onClick={onClose}>
    <aside className="ds-drawer" role="dialog" aria-modal="true" aria-label={title} onClick={(e) => e.stopPropagation()}>
      <header><b>{title}</b><button type="button" onClick={onClose} aria-label="Fechar">×</button></header>
      <div className="ds-drawer-body">{children}</div>
      {footer && <footer>{footer}</footer>}
    </aside>
  </div>;
}
