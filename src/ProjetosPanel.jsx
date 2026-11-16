import { useEffect, useMemo, useState } from 'react';
import { Page, Section, Badge, Empty, Drawer } from './ui.jsx';
import Select from './Choice.jsx';
import CardArt from './CardArt.jsx';
import { br, dataBr } from './format';
import './powers.css';

const NATIONAL = { approval: 'Aprovação do governo', institutional_trust: 'Confiança institucional', integrity: 'Integridade' };
const riskOf = (r) => (r < 0.1 ? ['baixo', 'good'] : r < 0.16 ? ['moderado', 'warn'] : r < 0.24 ? ['alto', 'bad'] : ['muito alto', 'bad']);
const years = (days) => { const y = days / 365; return `${br(y, y < 2 ? 1 : 0)} ${y < 1.5 ? 'ano' : 'anos'}`; };
const bi = (v) => `R$ ${br(v, v < 10 ? 1 : 0)} bi`;

function Phases({ project }) {
  return <ol className="pj-phases" aria-label="Fases do projeto">
    {project.phases.map((name, i) => <li key={name} className={project.status === 'delivered' || i < project.phase_index ? 'done' : i === project.phase_index ? 'now' : ''}><span>{name}</span></li>)}
  </ol>;
}

function Running({ project, onOpen }) {
  const pct = Math.round(project.progress * 100);
  const stalled = project.status === 'needs_decision';
  const done = project.status === 'delivered';
  return <button type="button" className={`pj-card pj-running ${stalled ? 'alert' : ''}`} onClick={() => onOpen(project)}>
    <CardArt group="obra" id={project.work_id} category={project.category} kind={project.kind} />
    <div className="pj-body">
      <b>{project.name}</b>
      <small>{project.route}</small>
      <div className="pj-bar" role="progressbar" aria-valuenow={pct} aria-valuemin="0" aria-valuemax="100"><i style={{ width: `${pct}%` }} /></div>
      <div className="pj-meta"><span>{done ? 'Entregue' : `${pct}% · ${project.phase}`}</span><span>{done ? dataBr(project.delivery_date) : `previsto ${dataBr(project.target_completion)}`}</span></div>
      {stalled && <Badge tone="bad">Parou: pede decisão</Badge>}
      {project.status === 'cancelled' && <Badge tone="warn">Cancelado</Badge>}
    </div>
  </button>;
}

export default function ProjetosPanel({ request, state, onState, onNotice }) {
  const [view, setView] = useState(null);
  const [error, setError] = useState('');
  const [category, setCategory] = useState('Todos');
  const [query, setQuery] = useState('');
  const [open, setOpen] = useState(null);       // item do catálogo
  const [openProject, setOpenProject] = useState(null); // projeto em andamento
  const [contractor, setContractor] = useState('');
  const [shown, setShown] = useState(12);
  const [busy, setBusy] = useState(false);

  const load = () => request('/api/budget').then((d) => { setView(d.works); setError(''); }).catch((e) => setError(e.message));
  useEffect(() => { load(); }, [state?.date]);
  useEffect(() => { if (view && !contractor) setContractor(view.contractors[0]?.id || ''); }, [view]);
  useEffect(() => { setShown(12); }, [category, query]);

  const categories = useMemo(() => ['Todos', ...Array.from(new Set((view?.options || []).map((o) => o.category)))], [view]);
  const list = useMemo(() => (view?.options || []).filter((o) => (category === 'Todos' || o.category === category)
    && (!query || `${o.name} ${o.kind} ${o.route} ${o.description}`.toLowerCase().includes(query.toLowerCase()))), [view, category, query]);

  async function post(url, body, after) {
    setBusy(true);
    try {
      const data = await request(url, { method: 'POST', body: JSON.stringify(body) });
      setView(data.budget.works); onState?.(data.state); after?.(data);
    } catch (e) { onNotice?.(e.message); } finally { setBusy(false); }
  }
  const start = (item) => post('/api/budget/works/start', { work_id: item.id, contractor_id: contractor }, (data) => {
    setOpen(null);
    onNotice?.(`Licitação aberta: ${data.result.project.name}. Custo contratado ${bi(data.result.project.contract_cost_bi)}, parcela anual de cerca de ${bi(data.result.annual_cost_bi)}.`);
  });
  const resolve = (project, choice) => post('/api/budget/works/resolve', { project_id: project.id, choice }, (data) => { setOpenProject(null); onNotice?.(data.result.message); });

  if (error) return <Page title="Projetos"><Empty title="Não foi possível carregar">{error}</Empty></Page>;
  if (!view) return <Page title="Projetos"><Empty title="Carregando">Abrindo o portfólio de projetos…</Empty></Page>;

  const running = view.projects.filter((p) => ['active', 'needs_decision'].includes(p.status));
  const past = view.projects.filter((p) => ['delivered', 'cancelled'].includes(p.status));
  const wait = view.days_until_next_award;

  return <Page title="Projetos" lead="Obras e programas do governo, do viaduto à missão à Lua. Cada projeto é pago pela carteira da sua área e passa por fases até a entrega.">
    <Section title="Carteiras" hint="Quanto cada área tem por ano e quanto já está comprometido.">
      <div className="pj-areas">
        {view.areas.map((a) => {
          const use = a.allocation_bi > 0 ? Math.min(100, Math.round((a.committed_bi / a.allocation_bi) * 100)) : 0;
          return <div key={a.key} className="pj-area"><span>{a.label}</span><div className="pj-bar"><i style={{ width: `${use}%` }} /></div><small>{bi(a.committed_bi)} de {bi(a.allocation_bi)} por ano</small></div>;
        })}
      </div>
    </Section>

    {running.length > 0 && <Section title={`Em andamento (${running.length})`}>
      <div className="pj-grid">{running.map((p) => <Running key={p.id} project={p} onOpen={setOpenProject} />)}</div>
    </Section>}

    <Section title="Catálogo" hint={wait > 0 ? `Nova licitação em ${wait} ${wait === 1 ? 'dia' : 'dias'}.` : 'Escolha um projeto para ver a ficha e abrir a licitação.'}>
      <div className="ds-inv-filters">
        <div className="ds-seg" role="tablist" aria-label="Tipo de projeto">{categories.map((c) => <button key={c} type="button" role="tab" aria-selected={category === c} className={category === c ? 'on' : ''} onClick={() => setCategory(c)}>{c}</button>)}</div>
        <label className="ds-search"><input aria-label="Buscar projeto" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Buscar projeto" /></label>
      </div>
      {list.length === 0 ? <Empty title="Nada encontrado">Troque o filtro ou a busca.</Empty> : <>
        <div className="pj-grid">
          {list.slice(0, shown).map((o) => { const [risk, tone] = riskOf(o.risk); return <button key={o.id} type="button" className={`pj-card ${o.affordable ? '' : 'off'}`} onClick={() => setOpen(o)}>
            <CardArt group="obra" id={o.id} category={o.category} kind={o.kind} />
            <div className="pj-body">
              <b>{o.name}</b>
              <small>{o.kind} · {o.route}</small>
              <div className="pj-meta"><span>{bi(o.quoted_cost_bi)}</span><span>{years(o.duration_days)}</span></div>
              <div className="pj-tags"><Badge tone={tone}>risco {risk}</Badge>{!o.affordable && <Badge tone="warn">não cabe na carteira</Badge>}</div>
            </div>
          </button>; })}
        </div>
        {list.length > shown && <button type="button" className="secondary-button" onClick={() => setShown(shown + 12)}>Mostrar mais ({list.length - shown} restantes)</button>}
      </>}
    </Section>

    {past.length > 0 && <Section title="Histórico"><div className="pj-grid">{past.map((p) => <Running key={p.id} project={p} onOpen={setOpenProject} />)}</div></Section>}

    {open && <Drawer title={open.name} onClose={() => setOpen(null)} footer={<>
      <button type="button" className="primary-button" disabled={busy || !open.affordable || wait > 0} onClick={() => start(open)}>Abrir licitação</button>
      <button type="button" className="secondary-button" onClick={() => setOpen(null)}>Fechar</button></>}>
      <CardArt group="obra" id={open.id} category={open.category} kind={open.kind} className="big" />
      <p>{open.description}</p>
      <dl className="pj-facts">
        <dt>Custo estimado hoje</dt><dd>{bi(open.quoted_cost_bi)}</dd>
        <dt>Prazo</dt><dd>{years(open.duration_days)} · entrega prevista em {dataBr(open.expected_completion)}</dd>
        <dt>Parcela anual</dt><dd>{bi(open.annual_cost_bi)} por ano, da carteira de {open.area_label}</dd>
        <dt>Região</dt><dd>{open.route}</dd>
        <dt>Risco de imprevistos</dt><dd>{riskOf(open.risk)[0]}</dd>
      </dl>
      <h4 className="subheading">Fases</h4>
      <ol className="pj-phases">{(open.phases || ['Estudos e projeto', 'Licenciamento', 'Execução', 'Testes e entrega']).map((name) => <li key={name}><span>{name}</span></li>)}</ol>
      <h4 className="subheading">O que muda quando fica pronto</h4>
      <ul className="ds-list">
        <li>Infraestrutura regional: +{br(open.effects.infrastructure || 0, 1)}; atividade econômica: +{br(open.effects.economic_activity || 0, 1)}.</li>
        {Object.entries(open.delivery || {}).map(([k, v]) => <li key={k}>{NATIONAL[k] || k}: +{br(v, 1)} ponto{v === 1 ? '' : 's'}.</li>)}
      </ul>
      {!open.affordable && <p className="ds-hint">A parcela anual não cabe no que resta da carteira de {open.area_label}. Remaneje recursos em Orçamento &gt; Investimentos.</p>}
      <label className="contractor-picker">Empresa da licitação<Select value={contractor} onChange={(e) => setContractor(e.target.value)}>{view.contractors.map((c) => <option key={c.id} value={c.id}>{c.name} · custo {br(c.price_factor, 2)}× · risco financeiro {Math.round(c.financial_risk * 100)}%</option>)}</Select></label>
      <p className="ds-hint">Empresas e ocorrências são fictícias. Durante a execução, problemas financeiros ou alertas de integridade podem parar a obra e pedir uma decisão sua.</p>
    </Drawer>}

    {openProject && <Drawer title={openProject.name} onClose={() => setOpenProject(null)}>
      <CardArt group="obra" id={openProject.work_id} category={openProject.category} kind={openProject.kind} className="big" />
      <p>{openProject.description}</p>
      <Phases project={openProject} />
      <dl className="pj-facts">
        <dt>Contratada</dt><dd>{openProject.contractor}</dd>
        <dt>Custo contratado hoje</dt><dd>{bi(openProject.current_cost_bi)}</dd>
        <dt>Início</dt><dd>{dataBr(openProject.start_date)}</dd>
        <dt>Previsão de entrega</dt><dd>{dataBr(openProject.target_completion)}</dd>
      </dl>
      {openProject.issue && <>
        <h4 className="subheading">{openProject.issue.title}</h4>
        <p>{openProject.issue.description}</p>
        <div className="ds-actions">{openProject.issue.options.map((o) => <button key={o.id} type="button" className="secondary-button" disabled={busy} onClick={() => resolve(openProject, o.id)}><b>{o.label}</b><small>{o.detail}</small></button>)}</div>
      </>}
    </Drawer>}
  </Page>;
}
