import { useState } from 'react';
import { Section, Badge, Empty, Drawer, fmt } from './ui.jsx';

const MAX_MOVE_SHARE = 0.2; // o motor só deixa tirar até 20% da área de origem
const MAX_MOVE_BI = 10;

/** Carteira de investimentos: cartões com a fatia de cada área e um painel lateral para reforçar uma delas. */
export default function InvestmentsPanel({ view, busy, onTransfer }) {
  const [target, setTarget] = useState(null);
  const [source, setSource] = useState(null);
  const [amount, setAmount] = useState(1);
  const areas = Object.entries(view.areas).map(([key, a]) => ({ key, ...a, value: Number(view.allocations[key] || 0) }));
  const total = Number(view.annual_investment_bi) || 1;
  const waiting = view.days_until_reallocation > 0;
  const sorted = [...areas].sort((a, b) => b.value - a.value);

  const open = (key) => {
    const first = sorted.find((a) => a.key !== key);
    setTarget(key); setSource(first?.key || null); setAmount(1);
  };
  const t = areas.find((a) => a.key === target);
  const s = areas.find((a) => a.key === source);
  const cap = s ? Math.max(0.1, Math.min(MAX_MOVE_BI, s.value * MAX_MOVE_SHARE)) : 0.1;
  const value = Math.min(Math.max(0.1, Number(amount) || 0.1), cap);
  const confirm = async () => { await onTransfer(source, target, Number(value.toFixed(1))); setTarget(null); };

  return <>
    <Section title="Onde o dinheiro está" hint={`Total fixo de R$ ${fmt(total)} bi por ano. Toque em uma área para reforçá-la com verba de outra.`}>
      <p className="ds-muted">{waiting ? `Próximo remanejamento liberado em ${view.days_until_reallocation} ${Number(view.days_until_reallocation) === 1 ? 'dia' : 'dias'}.` : 'Remanejamento liberado agora.'}</p>
      <div className="ds-inv-grid">
        {sorted.map((a) => <button key={a.key} type="button" className="ds-inv" onClick={() => open(a.key)}>
          <span className="ds-muted">{a.ministry}</span>
          <b>{a.label}</b>
          <strong>R$ {fmt(a.value)} bi<small>/ano</small></strong>
          <i className="ds-inv-bar"><u style={{ width: `${Math.round((a.value / total) * 100)}%` }} /></i>
          <small className="ds-muted">{Math.round((a.value / total) * 100)}% da carteira · efeito em {a.lag_days} {Number(a.lag_days) === 1 ? 'dia' : 'dias'}</small>
        </button>)}
      </div>
    </Section>

    <Section title="Em andamento">
      {view.pipeline.length === 0
        ? <Empty title="Nada em maturação">Quando você reforçar uma área, o projeto aparece aqui até concluir.</Empty>
        : <ul className="ds-reg-decisions">{view.pipeline.map((p) => <li key={p.id}><span className="ds-muted">{p.completion_date}</span><b>{view.areas[p.area]?.label}</b><Badge tone="warn">+R$ {fmt(p.annual_increase_bi)} bi/ano</Badge></li>)}</ul>}
    </Section>

    {t && <Drawer title={`Reforçar ${t.label}`} onClose={() => setTarget(null)} footer={
      <button className="primary-button" disabled={busy || waiting || !s} onClick={confirm}>{waiting ? `Libera em ${view.days_until_reallocation} ${Number(view.days_until_reallocation) === 1 ? 'dia' : 'dias'}` : `Mover R$ ${fmt(value)} bi`}</button>}>
      <p className="ds-muted">Hoje: R$ {fmt(t.value)} bi/ano. Efeito em {t.lag_days} {Number(t.lag_days) === 1 ? 'dia' : 'dias'}.</p>
      <h4>1. Tirar de</h4>
      <div className="ds-pick-list">
        {sorted.filter((a) => a.key !== target).map((a) => <button key={a.key} type="button" aria-pressed={source === a.key} onClick={() => setSource(a.key)}>
          <span>{a.label}</span><small>R$ {fmt(a.value)} bi</small>
        </button>)}
      </div>
      <h4>2. Quanto (R$ bi por ano)</h4>
      <input type="range" min="0.1" max={cap} step="0.1" value={value} onChange={(e) => setAmount(e.target.value)} aria-label="Valor anual em bilhões" />
      <div className="ds-amount"><b>R$ {fmt(value)} bi</b><small className="ds-muted">máximo agora: R$ {fmt(cap)} bi (20% da área de origem, até R$ 10 bi)</small></div>
      {s && <div className="ds-after">
        <span>{t.label}<b>R$ {fmt(t.value)} → {fmt(t.value + value)} bi</b></span>
        <span>{s.label}<b>R$ {fmt(s.value)} → {fmt(s.value - value)} bi</b></span>
      </div>}
    </Drawer>}
  </>;
}
