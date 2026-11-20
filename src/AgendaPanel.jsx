import { useMemo } from 'react';
import { Page, Section, Badge, Empty } from './ui';

const monthName = (iso) => new Date(`${iso.slice(0, 7)}-15T12:00:00`).toLocaleDateString('pt-BR', { month: 'long', year: 'numeric' });
const dayName = (iso) => new Date(`${iso}T12:00:00`).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' });
const when = (days) => (days === 0 ? 'hoje' : days === 1 ? 'amanhã' : `em ${days} ${Number(days) === 1 ? 'dia' : 'dias'}`);

/** Agenda: o que vem pela frente no calendário e quando o jogador pode agir. */
export default function AgendaPanel({ state, goals = [], go, campaign = false }) {
  const events = state.events || [];
  const bills = state.legislative_calendar?.pending_bills || [];
  const exec = campaign ? undefined : state.action_limits?.executive_days;
  const groups = useMemo(() => {
    const out = [];
    events.forEach((e) => {
      const m = e.date.slice(0, 7);
      if (!out.length || out[out.length - 1].m !== m) out.push({ m, items: [] });
      out[out.length - 1].items.push(e);
    });
    return out;
  }, [events]);

  return <Page title="Agenda" lead="O que fazer agora e o que vem pela frente. O tempo só passa quando você avança: um dia, sete dias ou um mês.">
    {goals.length > 0 && <Section title="Metas desta fase">
      <ul className="ds-goals">{goals.map((g) => <li key={g.id} className={g.done ? 'done' : ''}>
        <span className="ds-goal-mark" aria-hidden="true">{g.done ? '✓' : '○'}</span>
        <div><b>{g.label}</b><small>{g.detail}</small></div>
        <em>{g.progress}</em>
        {go && g.tab && <button type="button" className="ds-link" onClick={() => go(g.tab)}>abrir</button>}
      </li>)}</ul>
    </Section>}
    {(Number.isFinite(exec) || bills.length > 0) && <Section title="Quando posso agir">
      <div className="ds-card">
        <dl className="ds-kv">
          {Number.isFinite(exec) && [<dt key="e">Próxima decisão do Executivo</dt>, <dd key="ev">{exec === 0 ? 'liberada agora' : `em ${exec} ${Number(exec) === 1 ? 'dia' : 'dias'}`}</dd>]}
          {bills.map((b) => [<dt key={`${b.id}-t`}>Votação: {b.title}</dt>, <dd key={`${b.id}-d`}>{dayName(b.decision_date)}</dd>])}
        </dl>
      </div>
    </Section>}

    <Section title="Próximos compromissos">
      {events.length === 0 ? <Empty title="Nada marcado no calendário">Novos compromissos aparecem conforme o jogo avança.</Empty>
        : groups.map((g) => <div key={g.m}>
          <h4 className="ds-month">{monthName(g.m + '-15')}</h4>
          <ul className="ds-timeline ds-agenda-line">{g.items.map((e) => <li key={e.id}>
            <time dateTime={e.date}>{dayName(e.date)} · <Badge tone={e.days_until === 0 ? 'warn' : ''}>{when(e.days_until)}</Badge></time>
            <b>{e.title}</b>
            {e.description && <p>{e.description}</p>}
          </li>)}</ul>
        </div>)}
    </Section>
  </Page>;
}
