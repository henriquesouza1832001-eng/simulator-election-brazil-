import { Page, Section, Stat, Group, Badge, fmt } from './ui';
import MandateReview from './MandateReview';

const dateLabel = (iso) => (iso ? new Date(`${iso}T12:00:00`).toLocaleDateString('pt-BR') : '—');

/** Visão geral: o resumo do dia. Os dados chegam já prontos do App; aqui só se decide como mostrar. */
export default function OverviewPanel({ request, state, title, lead, term, stats, customize, next, upcoming, last, calendar, governing, skip, showReview, go }) {
  return <Page title={title} lead={lead}
    actions={term && <div className="ds-term" aria-label="Progresso do mandato"><span>{term.label}</span><b>{term.value}<small>{term.suffix}</small></b><i style={{ '--p': `${Math.max(0, Math.min(100, term.progress))}%` }} /><small>{term.note}</small></div>}>

    <Section title={stats.title}>
      <div className="ds-stats">{stats.items.map((s) => <Stat key={s.label} label={s.label} value={s.value} unit={s.unit} note={s.note} />)}</div>
      {customize && <details className="ds-customize"><summary>Escolher quais números aparecem</summary>
        <div>{customize.options.map((o) => <label key={o.key}><input type="checkbox" checked={customize.selected.includes(o.key)} onChange={() => customize.toggle(o.key)} /> {o.label}</label>)}</div></details>}
    </Section>

    <div className="ds-grid-2">
      <section className="ds-card ds-next">
        <Badge tone={next.urgent ? 'bad' : ''}>{next.label}</Badge>
        <h3>{next.title}</h3>
        <p>{next.text}</p>
        {skip && <div className="ds-skip"><p>{skip.text}</p><button type="button" className="secondary-button" disabled={skip.busy} onClick={skip.onSkip}>{skip.busy ? 'Avançando…' : skip.label}</button></div>}
        <div className="ds-actions">
          {next.actions.map((a) => <button key={a.label} type="button" className={a.primary ? 'primary-button' : 'secondary-button'} onClick={() => go(a.tab)}>{a.label}</button>)}
        </div>
      </section>

      <div className="ds-side">
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
        <section className="ds-card">
          <h4>O que vem pela frente <button type="button" className="ds-link" onClick={() => go('Agenda')}>ver agenda</button></h4>
          {upcoming.length ? <ul className="ds-list">{upcoming.map((e) => <li key={e.id}><span className="ds-muted">{e.days_until === 0 ? 'hoje' : `em ${e.days_until} dias`}</span><b>{e.title}</b></li>)}</ul> : <p className="ds-muted">Nenhum compromisso próximo.</p>}
        </section>
        {last && <section className="ds-card"><h4>Última decisão</h4><p className="ds-last"><b>{last.title}</b><span className="ds-muted">{dateLabel(last.date)} · {last.kind}</span></p></section>}
      </div>
    </div>

    {showReview && <Section><MandateReview request={request} state={state} /></Section>}
  </Page>;
}
