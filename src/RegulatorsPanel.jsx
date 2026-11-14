import { useEffect, useState } from 'react';
import { Page, Section, Badge, Empty } from './ui.jsx';

const STATUS = { suspenso: ['Suspenso', 'bad'], mantido: ['Mantido', 'good'], aberto: ['Aberto', 'warn'], 'com ressalvas': ['Com ressalvas', 'warn'] };

function Situation({ r }) {
  if (r.id === 'stf') {
    const open = r.open_cases || [];
    return <div className="ds-reg-now">
      <span>Alinhamento com o governo</span><b>{Math.round(r.alignment * 100)}%</b>
      <small>Cresce com ministros que você indica e o Senado confirma.</small>
      {open.length > 0 && <ul>{open.map((c) => <li key={c.title}>{c.title}: decisão até {c.decide_on}, risco {Math.round(c.risk * 100)}%</li>)}</ul>}
    </div>;
  }
  if (r.id === 'tse') {
    return r.conduct
      ? <div className="ds-reg-now"><span>Sua campanha</span><b>{r.conduct.detected} de {r.conduct.attempts} irregularidades detectadas</b><small>Penalidade de votos: {r.conduct.vote_penalty}.</small></div>
      : <div className="ds-reg-now"><small>Atua nas campanhas de carreira. Sem campanha ativa agora.</small></div>;
  }
  return null;
}

export default function RegulatorsPanel({ request, state }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  useEffect(() => { request('/api/regulators').then(setData).catch((e) => setError(e.message)); }, [state?.date]);

  if (error) return <Page title="Quem fiscaliza você"><p className="meta-status meta-error" role="alert">{error}</p></Page>;
  if (!data) return <Page title="Quem fiscaliza você"><Empty title="Carregando…" /></Page>;

  return <Page title="Quem fiscaliza você" lead={`Nenhum cargo age sozinho. Estes órgãos avaliam, limitam e investigam o que você faz. ${data.note || ''}`}>
    <Section title="Órgãos de controle" hint="Toque em um órgão para ver o que ele pode e o que não pode fazer.">
      <div className="ds-reg-grid">
        {data.regulators.map((r) => <article key={r.id} className="ds-card ds-reg">
          <h4>{r.name}</h4>
          <p className="ds-reg-role">{r.role}</p>
          <Situation r={r} />
          <details className="ds-reg-more"><summary>Pode e não pode</summary>
            <p><b>Pode:</b> {r.can.join('; ')}.</p>
            <p><b>Não pode:</b> {r.cannot.join('; ')}.</p>
            <p className="ds-muted">Base: {r.basis}</p>
          </details>
        </article>)}
      </div>
    </Section>
    <Section title="Decisões recentes">
      {data.decisions.length === 0
        ? <Empty title="Nenhuma decisão ainda">Quando um órgão decidir algo sobre você, aparece aqui.</Empty>
        : <ul className="ds-reg-decisions">{data.decisions.map((d) => {
          const [label, tone] = STATUS[d.status] || [d.status, ''];
          return <li key={d.id}><span className="ds-muted">{d.decided || d.filed}</span><b>{d.title}</b><Badge tone={tone}>{label}</Badge>{d.chance_pct != null && <small className="ds-muted">risco de suspensão era {d.chance_pct}%</small>}</li>;
        })}</ul>}
    </Section>
  </Page>;
}
