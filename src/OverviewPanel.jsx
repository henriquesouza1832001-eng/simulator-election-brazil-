import { useEffect, useState } from 'react';
import { MercadoFaixa } from './MercadoPanel.jsx';
import { Section, Stat, Badge, fmt } from './ui';
import Hero, { headline } from './Hero';
import MandateReview from './MandateReview';
import PainelMapa from './PainelMapa.jsx';

const dateLabel = (iso) => (iso ? new Date(`${iso}T12:00:00`).toLocaleDateString('pt-BR') : '—');

/** Visão geral: manchete do dia, números, próximo passo, agenda e balanço. Os dados chegam prontos do App. */
export default function OverviewPanel({ scope = 'nacional', rivals = [], rivalEvents = [], territory, request, state, term, stats, customize, next, upcoming, last, calendar, governing, skip, showReview, showBalance, go, pins = [], onUnpin }) {
  const [review, setReview] = useState(null);
  useEffect(() => {
    if (!showReview) return;
    request('/api/mandate/review').then(setReview).catch(() => setReview(null));
  }, [state?.date, showReview]);

  const crisis = state.active_crises?.[0];
  const hero = showReview && next.label !== 'FIM DO MANDATO'
    ? { ...headline(review, crisis), label: 'Hoje no país' }
    : { mood: next.urgent ? 'crise' : 'calmo', title: next.title, text: next.text, label: next.label };

  return <section className="ds-page">
    <Hero name="painel" mood={hero.mood} label={hero.label} title={hero.title} text={hero.text} badge={term ? `${term.label} ${term.value}${term.suffix}` : undefined} />

    {scope === 'nacional' && <MercadoFaixa request={request} state={state} go={go} />}

    <Section title={stats.title}>
      <div className="ds-stats">{stats.items.map((s) => <Stat key={s.label} label={s.label} value={s.value} unit={s.unit} note={s.note} />)}</div>
      {customize && <details className="ds-customize"><summary>Escolher quais números aparecem</summary>
        <div>{customize.options.map((o) => <label key={o.key}><input type="checkbox" checked={customize.selected.includes(o.key)} onChange={() => customize.toggle(o.key)} /> {o.label}</label>)}</div></details>}
    </Section>

    {scope === 'nacional' && <PorQueMudou why={state.why} />}

    <div className="ds-grid-2">
      {scope === 'nacional' ? <PainelMapa request={request} state={state} go={go} /> : <TerritorioCard territory={territory} rivals={rivals} events={rivalEvents} go={go} />}
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

/** Cargo local ou estadual: o painel fala do território do jogador, não do país. Em campanha, mostra quem disputa e quanto cada um tem. */
function TerritorioCard({ territory, rivals, events = [], go }) {
  const sorted = [...rivals].sort((a, b) => b.support - a.support);
  return <section className="ds-card ds-territorio" aria-label="Seu território">
    <header><h4>{rivals.length ? `Quem disputa ${territory || 'o cargo'}` : territory || 'Seu território'}</h4><button type="button" className="ds-link" onClick={() => go('Indicadores')}>ver indicadores</button></header>
    {rivals.length > 0
      ? <ul className="ds-rivals">{sorted.map((r) => <li key={r.id}><span><b>{r.party}</b><small>{r.ideology} · foco: {r.issue_focus_label || '—'}</small></span><strong>{fmt(r.support, 1)}%</strong><i style={{ width: `${Math.min(100, r.support * 2)}%` }} /></li>)}</ul>
      : <p className="ds-muted">Os indicadores deste painel são do seu território. Para o quadro nacional, use a tela Indicadores.</p>}
    {events.length > 0 && <div className="ds-rival-moves"><h5>Movimentos recentes</h5><ul>{events.slice(0, 3).map((e, i) => <li key={`${e.date}-${i}`}><time dateTime={e.date}>{dateLabel(e.date)}</time> {e.text}</li>)}</ul></div>}
    {rivals.length > 0 && <p className="ds-muted">Partidos que mais votaram na última eleição deste cargo, com força real do TSE; candidaturas simuladas.</p>}
  </section>;
}

const sign = (v) => `${v > 0 ? '+' : v < 0 ? '−' : ''}${Math.abs(v).toLocaleString('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 2 })}`;

/** Por que mudou? As maiores causas da variação de cada indicador desde o último avanço do calendário. */
function PorQueMudou({ why }) {
  const rows = Object.entries(why?.metrics || {}).filter(([, r]) => Math.abs(r.total) >= 0.05);
  if (!rows.length) return null;
  return <Section title="Por que mudou?">
    <p className="ds-muted">De {dateLabel(why.from)} a {dateLabel(why.to)}. Cada linha mostra o que mais pesou na variação.</p>
    <div className="ds-why">{rows.map(([key, r]) => {
      const good = (r.total > 0) === r.good_when_up;
      return <article key={key} className={good ? 'good' : 'bad'}>
        <header><b>{r.label}</b><strong>{sign(r.total)} {r.unit}</strong></header>
        <ul>{r.causes.map((c) => <li key={c.label}><span>{c.label}</span><em>{sign(c.delta)}</em></li>)}</ul>
      </article>;
    })}</div>
  </Section>;
}
