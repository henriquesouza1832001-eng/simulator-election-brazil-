import { useEffect, useState } from 'react';
import { Page, Section, Badge, Empty, Drawer, Stat, fmt } from './ui.jsx';
import './powers.css';

const tone = (v) => (v >= 65 ? 'good' : v >= 35 ? 'warn' : 'bad');

export default function CompaniesPanel({ request, state, onState, onNotice }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [openId, setOpenId] = useState(null);
  const [choosing, setChoosing] = useState(null); // chave da ação cujas opções estão abertas
  const [pick, setPick] = useState('');
  const [filter, setFilter] = useState('todas');
  const [bank, setBank] = useState(null);
  const load = () => request('/api/companies').then(setData).catch((e) => setError(e.message));
  useEffect(() => { load(); request('/api/central-bank').then(setBank).catch(() => setBank(null)); }, [state?.date]);

  async function act(company, action, option) {
    try {
      const r = await request('/api/companies/act', { method: 'POST', body: JSON.stringify({ company: company.id, action: action.key, option: option || null }) });
      setData(r.overview);
      if (r.state) onState?.(r.state);
      onNotice?.(r.announcement || `${company.name}: decisão registrada.`);
      setChoosing(null); setPick('');
    } catch (e) { onNotice?.(e.message); }
  }

  async function privatize(company) {
    try {
      const r = await request('/api/powers/execute', { method: 'POST', body: JSON.stringify({ action: 'empresa_privatizar', option: company.privatize_key }) });
      if (r.state) onState?.(r.state);
      onNotice?.(r.message);
      load();
    } catch (e) { onNotice?.(e.message); }
  }

  if (error) return <Page title="Empresas e bancos públicos"><p className="meta-status meta-error" role="alert">{error}</p></Page>;
  if (!data) return <Page title="Empresas e bancos públicos"><Empty title="Carregando…" /></Page>;

  const controls = ['todas', ...new Set(data.companies.map((c) => c.control))];
  const list = data.companies.filter((c) => filter === 'todas' || c.control === filter);
  const c = data.companies.find((x) => x.id === openId);
  const close = () => { setOpenId(null); setChoosing(null); setPick(''); };

  return <Page title="Empresas e bancos públicos" lead={data.note}>
    {bank?.applies && <Section title="Banco Central e Selic" hint={bank.note}>
      <div className="ds-stats">
        <Stat label="Selic" value={fmt(bank.selic, 2)} unit="% a.a." note={`Copom busca ${fmt(bank.desired, 2)}% sem pressão`} />
        <Stat label="Próxima reunião do Copom" value={bank.days_to_meeting} unit={bank.days_to_meeting === 1 ? ' dia' : ' dias'} note={bank.next_meeting.split('-').reverse().join('/')} />
        <Stat label="Credibilidade" value={fmt(bank.credibility, 0)} unit="/100" note={bank.autonomy_label} />
        <Stat label="Inflação x meta" value={fmt(bank.inflation, 1)} unit="% a.a." note={`meta ${fmt(bank.target, 1)}%`} />
      </div>
      {bank.pressure > 0 && <p className="ds-muted">Você criticou os juros {bank.pressure} vez(es) nos últimos 4 meses; isso aproxima o Copom do que o governo quer, com custo em credibilidade.</p>}
      {bank.history.length > 0 && <details className="agenda-more"><summary>Decisões recentes do Copom ({bank.history.length})</summary>
        <ul className="ds-reg-decisions">{bank.history.map((h) => <li key={h.date}><span className="ds-muted">{h.date.split('-').reverse().join('/')}</span><b>{h.text}</b><small className="ds-muted">equilíbrio {fmt(h.desired, 2)}%</small></li>)}</ul></details>}
      <p className="ds-muted">Para mudar a autonomia, os diretores ou criticar os juros, use Competências &gt; Banco e moeda.</p>
    </Section>}
    <Section hint="Toque em uma empresa para ver a situação e as decisões possíveis.">
      <div className="ds-seg" role="group" aria-label="Filtrar por controle">
        {controls.map((k) => <button key={k} type="button" aria-pressed={filter === k} onClick={() => setFilter(k)}>{k === 'todas' ? 'Todas' : k}</button>)}
      </div>
      <div className="ds-inv-grid" style={{ marginTop: 12 }}>
        {list.map((x) => <button key={x.id} type="button" className="ds-inv" onClick={() => setOpenId(x.id)}>
          <span className="ds-muted">{x.sector}{x.strategic ? ' · estratégica' : ''}</span>
          <b>{x.name}</b>
          <small className="ds-muted">{x.control}{x.stake != null ? ` · União ${fmt(x.stake, 0)}%` : ''}</small>
          <span>Saúde <Badge tone={tone(x.health)}>{x.health}</Badge> · Relação <Badge tone={tone(x.relation)}>{x.relation}</Badge></span>
        </button>)}
      </div>
    </Section>
    <p className="ds-muted">Os efeitos de cada decisão aparecem no histórico de previsto e realizado (aba Competências) e na linha do tempo da Imprensa.</p>

    {c && <Drawer title={c.name} onClose={close}>
      <p className="ds-muted">{c.sector} · {c.control}{c.strategic ? ' · estratégica' : ''} · sede {c.hq}</p>
      <p>{c.note}</p>
      <div className="ds-after">
        <span>Saúde da empresa<b>{c.health}/100</b></span>
        <span>Relação com o governo<b>{c.relation}/100</b></span>
        {c.stake != null && <span>Participação da União<b>{fmt(c.stake, 1)}%</b></span>}
        {c.value_bi != null && <span>Valor de referência (fictício)<b>R$ {fmt(c.value_bi, 1)} bi</b></span>}
      </div>
      <h4>Decisões</h4>
      <div className="ds-pick-list">
        {c.actions.map((a) => <div key={a.key}>
          <button type="button" disabled={!a.available} aria-pressed={choosing === a.key}
            onClick={() => (a.options.length ? (setChoosing(choosing === a.key ? null : a.key), setPick('')) : act(c, a))}>
            <span>{a.label}</span><small>{a.available ? (a.options.length ? 'escolher' : 'aplicar') : 'indisponível'}</small>
          </button>
          {!a.available && a.reason && <small className="neg">{a.reason}</small>}
          {choosing === a.key && a.available && <div className="ds-pick-list" style={{ marginTop: 6 }}>
            {a.options.map((o) => <button key={o} type="button" aria-pressed={pick === o} onClick={() => setPick(o)}><span>{o}</span></button>)}
            <button type="button" className="primary-button" disabled={!pick} onClick={() => act(c, a, pick)}>Aplicar</button>
          </div>}
        </div>)}
      </div>
      {c.can_privatize && <button type="button" className="quiet-button" onClick={() => privatize(c)}>Propor a privatização (exige lei)</button>}
    </Drawer>}
  </Page>;
}
