import { useEffect, useState } from 'react';
import { Section, Stat, Badge, fmt } from './ui';
import Hero, { headline } from './Hero';
import MandateReview from './MandateReview';
import PainelMapa from './PainelMapa.jsx';

const dateLabel = (iso) => (iso ? new Date(`${iso}T12:00:00`).toLocaleDateString('pt-BR') : '—');

/** Visão geral: manchete do dia, números, próximo passo, agenda e balanço. Os dados chegam prontos do App. */
export default function OverviewPanel({ request, state, term, stats, customize, next, upcoming, last, calendar, governing, skip, showReview, showBalance, go, pins = [], onUnpin }) {
  const [review, setReview] = useState(null);
  useEffect(() => {
    if (!showReview) return;
    request('/api/mandate/review').then(setReview).catch(() => setReview(null));
  }, [state?.date, showReview]);

  const crisis = state.active_crises?.[0];
  const hero = showReview
    ? { ...headline(review, crisis), label: 'Hoje no país' }
    : { mood: next.urgent ? 'crise' : 'calmo', title: next.title, text: next.text, label: next.label };

  return <section className="ds-page">
    <Hero name="painel" mood={hero.mood} label={hero.label} title={hero.title} text={hero.text} badge={term ? `${term.label} ${term.value}${term.suffix}` : undefined} />

    <Section title={stats.title}>
      <div className="ds-stats">{stats.items.map((s) => <Stat key={s.label} label={s.label} value={s.value} unit={s.unit} note={s.note} />)}</div>
      {customize && <details className="ds-customize"><summary>Escolher quais números aparecem</summary>
        <div>{customize.options.map((o) => <label key={o.key}><input type="checkbox" checked={customize.selected.includes(o.key)} onChange={() => customize.toggle(o.key)} /> {o.label}</label>)}</div></details>}
    </Section>

    <div className="ds-grid-2">
      <PainelMapa request={request} state={state} go={go} />
      <div className="ds-side">
        <section className="ds-card ds-next">
          <Badge tone={next.urgent ? 'bad' : ''}>{next.label}</Badge>
          {next.title !== hero.title && <h3>{next.title}</h3>}
          <p>{next.text}</p>
          {skip && <div className="ds-skip"><p>{skip.text}</p><button type="button" className="secondary-button" disabled={skip.busy} onClick={skip.onSkip}>{skip.busy ? 'Avançando…' : skip.label}</button></div>}
          <div className="ds-actions">
            {next.actions.map((a) => <button key={a.label} type="button" className={a.primary ? 'primary-button' : 'secondary-button'} onClick={() => go(a.tab)}>{a.label}</button>)}
          </div>
        </section>
        {governing && <section className="ds-card">
          <h4>Capacidade de governar</h4>
          <div className="ds-meter" role="img" aria-label={`${fmt(governing.governability, 0)} de 100`}><i style={{ width: `${Math.max(0, Math.min(100, governing.governability))}%` }} /></div>
          <dl className="ds-kv">
            <dt>Governabilidade</dt><dd>{fmt(governing.governability, 0)}/100</dd>
            <dt>Base no Congresso</dt><dd>{fmt(governing.congress_support, 1)}%</dd>
            <dt>Confiança institucional</dt><dd>{fmt(governing.institutional_trust, 0)}/100</dd>
          </dl>
        </section>}
        {calendar && <section className="ds-card">
          <h4>Datas da sua carreira</h4>
          <dl className="ds-kv">{calendar.map(([k, v]) => [<dt key={`${k}-t`}>{k}</dt>, <dd key={`${k}-d`}>{dateLabel(v)}</dd>])}</dl>
          <p className="ds-muted">Datas do ciclo simulado do jogo.</p>
        </section>}
        {upcoming.length > 0 && <section className="ds-card">
          <h4>O que vem pela frente <button type="button" className="ds-link" onClick={() => go('Agenda')}>ver agenda</button></h4>
          <ul className="ds-list">{upcoming.map((e) => <li key={e.id}><span className="ds-when">{e.days_until === 0 ? 'hoje' : `em ${e.days_until} d`}</span><b>{e.title}</b></li>)}</ul>
        </section>}
        {pins.length > 0 && <section className="ds-card ds-pinned"><h4>Atalhos fixados</h4><div>{pins.map((p) => <span key={p}><button type="button" className="ds-link" onClick={() => go(p)}>{p}</button><button type="button" aria-label={`Tirar ${p} dos fixados`} onClick={() => onUnpin(p)}>×</button></span>)}</div></section>}
        {last && <section className="ds-card"><h4>Última decisão</h4><p className="ds-last"><b>{last.title}</b><span className="ds-muted">{dateLabel(last.date)} · {last.kind}</span></p></section>}
      </div>
    </div>

    {showBalance && <details className="ds-fold"><summary>Balanço do mandato</summary><MandateReview request={request} state={state} data={review} /></details>}
  </section>;
}
