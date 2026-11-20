import { br } from './format';

const FORECAST_LABEL = {
  primary_balance: ['Resultado primário', 'p.p. do PIB', 3], gdp_growth: ['Crescimento do PIB', 'p.p.', 2], approval: ['Aprovação', 'p.p.', 1],
  congress_support: ['Base no Congresso', 'p.p.', 1], institutional_trust: ['Confiança institucional', 'pts', 1], governability: ['Governabilidade', 'pts', 1], integrity: ['Integridade', 'pts', 1],
};
const GOOD_WHEN_UP = new Set(Object.keys(FORECAST_LABEL));

const sign = (v, d) => `${v > 0 ? '+' : v < 0 ? '−' : ''}${br(Math.abs(v), d)}`;

/** Alavancas fiscais de peso (Presidência): cada opção mostra a previsão do motor antes de confirmar. */
export default function FiscalLevers({ levers = [], history = [], busy, onUse }) {
  if (!levers.length) return null;
  return <section className="fiscal-levers" aria-label="Alavancas fiscais">
    <div className="operating-heading"><div><span className="eyebrow">DECISÕES DE PESO</span><h3>Alavancas fiscais</h3>
      <p>Cada uma mexe no resultado primário de verdade e cobra um preço em atividade, aprovação ou Congresso. Há um intervalo de 60 dias entre elas.</p></div></div>
    <div className="lever-grid">{levers.map((lever) => <article key={lever.id} className="lever-card">
      <h4>{lever.label}</h4>
      <p>{lever.about}</p>
      <ul>{lever.options.map((opt) => <li key={opt.id} className={opt.available ? '' : 'blocked'}>
        <div><b>{opt.label}</b>
          <small>{Object.entries(opt.forecast).map(([k, v]) => { const meta = FORECAST_LABEL[k]; if (!meta) return null; const good = (v > 0) === GOOD_WHEN_UP.has(k); return <span key={k} className={good ? 'good' : 'bad'}>{meta[0]} {sign(v, meta[2])} {meta[1]}</span>; })}</small>
          {!opt.available && opt.reason && <em>{opt.reason}</em>}
        </div>
        <button type="button" className="secondary-button" disabled={busy || !opt.available} onClick={() => onUse(lever.id, opt.id, opt.label)}>Aplicar</button>
      </li>)}</ul>
    </article>)}</div>
    {history.length > 0 && <p className="indicator-footnote">Últimas decisões: {history.map((h) => h.title).join(' · ')}</p>}
  </section>;
}
