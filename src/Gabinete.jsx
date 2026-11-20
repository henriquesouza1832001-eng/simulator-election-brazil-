import { br } from './format';
import './gabinete.css';

const METERS = [
  { key: 'approval', label: 'Aprovação', unit: '%', good: true, bar: (v) => v, alertBelow: 45 },
  { key: 'inflation', label: 'Inflação · a.a.', unit: '%', good: false, bar: (v) => v * 8 },
  { key: 'gdp_growth', label: 'Crescimento do PIB', unit: '%', good: true, bar: (v) => 50 + v * 10 },
  { key: 'congress_support', label: 'Apoio no Congresso', unit: '%', good: true, bar: (v) => v, alertBelow: 50 },
  { key: 'institutional_trust', label: 'Confiança institucional', unit: '/100', good: true, bar: (v) => v },
];

const clamp = (v) => Math.max(0, Math.min(100, v));
const dateBr = (iso) => (iso ? new Date(`${iso}T12:00:00`).toLocaleDateString('pt-BR') : '');
const signed = (v) => `${v > 0 ? '+' : v < 0 ? '−' : ''}${br(Math.abs(v), 2)}`;
const sign = (v) => `${v > 0 ? '▲' : v < 0 ? '▼' : ''} ${br(Math.abs(v), 1)}`.trim();

/** Gabinete: a visão geral em papel. Responde, na ordem, "o que está acontecendo", "como estou" e "o que decido agora". */
export default function Gabinete({ state, despacho, go, advance, busy }) {
  const m = state.metrics || {};
  const why = state.why?.metrics || {};
  const top = despacho.find((d) => d.urgent);
  const crisis = Boolean(top);
  const view = state.scenario_view;
  const whyRows = Object.entries(state.why?.metrics || {}).filter(([, r]) => Math.abs(r.total) >= 0.05);
  const open = (item) => go(item.decide ? 'Decidir' : item.tab);

  return <section className="gb" aria-label="Gabinete">
    <header className="gb-head">
      <div className="gb-eyebrow">Governo · mês {Math.min(48, Math.floor((state.day_of_mandate || 1) / 30.4) + 1)} de 48</div>
      <h1>Gabinete</h1>
      <p className="gb-lead">O que você decide agora muda o próximo mês.</p>
    </header>

    {view && view.status === 'concluido' && <section className="gb-panel" aria-label="Balanço dos 100 dias" style={{ marginBottom: 16 }}>
      <div className="gb-eyebrow">Fim do cenário</div><h3 style={{ fontSize: 19 }}>Balanço dos 100 dias: {view.result.title}</h3>
      <p className="gb-note">{view.result.text} ({view.result.done} de {view.result.total} metas)</p>
      {view.goals.map((g) => <div key={g.id} className={`gb-goal ${g.done ? 'done' : ''}`}><span className="gb-check">{g.done ? '✓' : '✗'}</span><span>{g.label} <strong>({g.progress})</strong></span></div>)}
      <div className="gb-actions"><span /><button type="button" className="gb-btn soft" onClick={() => go('Histórico')}>Ver a evolução do governo</button></div>
    </section>}

    <section className={`gb-situation ${crisis ? 'crisis' : ''}`} aria-label="Situação">
      <div>
        <div className="gb-eyebrow">{crisis ? 'Situação · pede resposta' : 'Situação · sem crise aberta'}</div>
        <h2>{crisis ? top.title : 'A agenda segue sem crise em aberto'}</h2>
        <p>{crisis ? top.detail : 'Escolha uma pasta, confira os efeitos antes de assinar e depois avance o mês.'}</p>
      </div>
      <div className="gb-icon" aria-hidden="true">{crisis ? '!' : '✓'}</div>
    </section>

    <section className="gb-meters" aria-label="Indicadores principais">
      {METERS.map((mt) => {
        const v = Number(m[mt.key]);
        const d = why[mt.key]?.total;
        const goodMove = d == null || Math.abs(d) < 0.05 ? null : (d > 0) === mt.good;
        return <div key={mt.key} className={`gb-meter ${mt.alertBelow && v < mt.alertBelow ? 'alert' : ''}`}>
          <div className="gb-meter-top"><span>{mt.label}</span>{d != null && Math.abs(d) >= 0.05 ? <span className={`gb-delta ${goodMove ? 'good' : 'bad'}`}>{sign(d)}</span> : <span className="gb-delta flat">estável</span>}</div>
          <div className="gb-meter-value">{br(v, 1)}<small>{mt.unit}</small></div>
          <div className="gb-track"><span style={{ width: `${clamp(mt.bar(v))}%` }} /></div>
        </div>;
      })}
    </section>

    <div className="gb-layout">
      <section aria-label="Mesa de despacho">
        <div className="gb-section-head"><h2>Mesa de despacho</h2><span className="gb-meta">{despacho.length ? `${despacho.length} ${despacho.length === 1 ? 'assunto' : 'assuntos'} por urgência` : 'tudo em dia'}</span></div>
        {despacho.length === 0
          ? <p className="gb-note">Nada pede decisão agora. Você pode avançar o mês.</p>
          : <ul className="gb-list">{despacho.slice(0, 5).map((it) => <li key={it.key} className={`gb-card ${it.urgent ? 'urgent' : it.kind === 'Votação' ? 'vote' : ''}`}>
            <span className="gb-kind">{it.kind}</span>
            <div className="gb-card-copy"><h3>{it.title}</h3><p>{it.detail}{it.days != null ? ` · ${it.days <= 0 ? 'vence hoje' : it.days === 1 ? 'falta 1 dia' : `faltam ${it.days} dias`}` : ''}</p></div>
            <button type="button" className={`gb-btn ${it.urgent ? 'danger' : 'soft'}`} onClick={() => open(it)}>Abrir</button>
          </li>)}</ul>}
        <div className="gb-footer"><p>Fez suas escolhas? Avance o mês para ver as consequências.</p>
          <button type="button" className="gb-btn primary" disabled={busy} onClick={() => advance(30)}>{busy ? 'Avançando…' : 'Avançar mês →'}</button></div>
      </section>

      {view && view.status === 'em_andamento' && <aside className="gb-scenario" aria-label="Cenário dos 100 dias">
        <div className="gb-eyebrow">Cenário 100 dias</div>
        <h3>Os primeiros 100 dias</h3>
        <div className="gb-bar" role="img" aria-label={`Dia ${view.day} de 100`}><span style={{ width: `${view.day}%` }} /></div>
        <div className="gb-meta">Dia {view.day} de 100 · {view.goals.filter((g) => g.done).length}/{view.goals.length} metas</div>
        {view.goals.map((g) => <div key={g.id} className={`gb-goal ${g.done ? 'done' : ''}`}><span className="gb-check">{g.done ? '✓' : ''}</span><span>{g.label} <strong>({g.progress})</strong></span></div>)}
      </aside>}
    </div>

    {whyRows.length > 0 && <section className="gb-panel" style={{ marginTop: 16 }} aria-label="Por que mudou?">
      <div className="gb-section-head"><h2>Por que mudou?</h2><span className="gb-meta">De {dateBr(state.why.from)} a {dateBr(state.why.to)}</span></div>
      <div className="gb-why-grid">{whyRows.map(([key, r]) => <article key={key}>
        <h3><span>{r.label}</span><span className={`gb-delta ${(r.total > 0) === r.good_when_up ? 'good' : 'bad'}`}>{signed(r.total)} {r.unit}</span></h3>
        {r.causes.map((c) => <div className="gb-cause" key={c.label}><span>{c.label}</span><b>{signed(c.delta)}</b></div>)}
      </article>)}</div>
    </section>}
  </section>;
}
