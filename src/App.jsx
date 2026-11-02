import { useEffect, useMemo, useState } from 'react';
import DiplomacyPanel from './DiplomacyPanel';
import FiscalPanel from './FiscalPanel';
import './diplomacy.css';

const fmt = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 1 });

function Metric({ label, value, unit = '', tone = '' , detail }) {
  return <article className="metric"><div className="metric-label">{label}</div><div className={`metric-value ${tone}`}>{fmt.format(value)}<small>{unit}</small></div>{detail && <div className="metric-detail">{detail}</div>}</article>;
}

const indicatorOptions = [
  { key: 'gdp_growth', label: 'Atividade econômica', unit: '%', detail: 'Crescimento anual do PIB', tone: 'green' },
  { key: 'inflation', label: 'Inflação', unit: '%', detail: 'Variação anual de preços', tone: 'amber' },
  { key: 'unemployment', label: 'Desemprego', unit: '%', detail: 'Força de trabalho' },
  { key: 'debt_gdp', label: 'Dívida pública', unit: '% do PIB', detail: 'Trajetória da dívida', tone: 'amber' },
  { key: 'primary_balance', label: 'Resultado fiscal', unit: '% do PIB', detail: 'Saldo antes dos juros' },
  { key: 'nominal_result', label: 'Resultado nominal', unit: '% PIB', detail: 'Saldo apos juros da divida', tone: 'amber' },
  { key: 'country_risk', label: 'Risco-pais', unit: 'pontos', detail: 'Premio de risco soberano', tone: 'amber' },
  { key: 'fiscal_credibility', label: 'Credibilidade fiscal', unit: '/100', detail: 'Confianca na trajetoria das contas', tone: 'blue' },
  { key: 'approval', label: 'Aprovação', unit: '%', detail: 'Apoio ao governo', tone: 'green' },
  { key: 'governability', label: 'Governabilidade', unit: '/100', detail: 'Capacidade de formar maioria', tone: 'green' },
  { key: 'integrity', label: 'Integridade', unit: '/100', detail: 'Confiança e transparência', tone: 'blue' },
  { key: 'regional_infrastructure', label: 'Infraestrutura regional', unit: '/100', detail: 'Resiliência de estradas e serviços', tone: 'blue' },
];

export default function App() {
  const [state, setState] = useState(null);
  const [measure, setMeasure] = useState('');
  const [preview, setPreview] = useState(null);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState('');
  const [correction, setCorrection] = useState('');
  const [activeTab, setActiveTab] = useState('Visão geral');
  const [ruptureInfo, setRuptureInfo] = useState(null);
  const [budgetView, setBudgetView] = useState(null);
  const [ministries, setMinistries] = useState([]);
  const [budgetSource, setBudgetSource] = useState('education');
  const [budgetTarget, setBudgetTarget] = useState('logistics');
  const [budgetAmount, setBudgetAmount] = useState('1');
  const [travelCutPct, setTravelCutPct] = useState(0);
  const [residenceCutPct, setResidenceCutPct] = useState(0);

  async function request(path, options) {
    const response = await fetch(path, { headers: { 'Content-Type': 'application/json' }, ...options });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Falha na solicitação');
    return data;
  }
  async function refresh() { setState(await request('/api/game')); }
  useEffect(() => { refresh().catch((e) => setNotice(e.message)); }, []);
  useEffect(() => {
    if (activeTab === 'Orçamento') Promise.all([request('/api/budget'), request('/api/government/ministries')])
      .then(([budget, cabinet]) => { setBudgetView(budget); setMinistries(cabinet.items || []); setTravelCutPct(budget.operating?.travel_cut_pct ?? 0); setResidenceCutPct(budget.operating?.residence_cut_pct ?? 0); })
      .catch((e) => setNotice(e.message));
  }, [activeTab]);

  const currentDate = useMemo(() => state?.date ? new Date(`${state.date}T12:00:00`) : null, [state?.date]);
  const dateLabel = currentDate ? currentDate.toLocaleDateString('pt-BR', { day: 'numeric', month: 'long', year: 'numeric' }) : 'Carregando…';

  async function advance(days) {
    setBusy(true); setNotice('');
    try { const data = await request('/api/game/advance', { method: 'POST', body: JSON.stringify({ days }) }); setState(data.state); setNotice(data.message); }
    catch (e) { setNotice(e.message); } finally { setBusy(false); }
  }
  async function interpret() {
    if (!measure.trim()) return;
    setBusy(true); setNotice(''); setPreview(null);
    try { setPreview(await request('/api/measures/preview', { method: 'POST', body: JSON.stringify({ text: measure }) })); }
    catch (e) { setNotice(e.message); } finally { setBusy(false); }
  }
  async function signMeasure() {
    if (!preview) return;
    setBusy(true);
    try { const data = await request('/api/measures/apply', { method: 'POST', body: JSON.stringify({ text: measure, interpretation: preview.interpretation }) }); setState(data.state); setPreview(null); setMeasure(''); setNotice(data.status === 'pending_legislation' ? `Projeto enviado ao Congresso. A votação simulada está prevista para ${data.effects[0].decision_date}; efeitos dependem de aprovação.` : 'Ato registrado. O Executivo tem agenda limitada e os efeitos seguem as regras do simulador.'); }
    catch (e) { setNotice(e.message); } finally { setBusy(false); }
  }
  async function saveCorrection() {
    if (!preview || !correction.trim()) return;
    setBusy(true);
    try { await request('/api/learning/corrections', { method: 'POST', body: JSON.stringify({ original_text: measure, corrected_interpretation: correction }) }); setNotice('Correção guardada na memória local para orientar interpretações futuras.'); setCorrection(''); }
    catch (e) { setNotice(e.message); } finally { setBusy(false); }
  }
  async function changeDifficulty(difficulty) {
    try { setState(await request('/api/game/difficulty', { method: 'PATCH', body: JSON.stringify({ difficulty }) })); }
    catch (e) { setNotice(e.message); }
  }
  async function toggleDashboardCard(key) {
    const current = state.dashboard_cards || indicatorOptions.slice(0, 6).map((item) => item.key);
    const cards = current.includes(key) ? current.filter((item) => item !== key) : [...current, key];
    try { setState(await request('/api/game/dashboard', { method: 'PATCH', body: JSON.stringify({ cards }) })); }
    catch (e) { setNotice(e.message); }
  }

  async function respondEvent(eventId, choice) {
    setBusy(true);
    try { const data = await request(`/api/events/${encodeURIComponent(eventId)}/respond`, { method: 'POST', body: JSON.stringify({ choice }) }); setState(data.state); setNotice(data.result.result); }
    catch (e) { setNotice(e.message); } finally { setBusy(false); }
  }

  async function loadRupturePreview() {
    try { setRuptureInfo(await request('/api/regime/rupture/preview')); } catch (e) { setNotice(e.message); }
  }

  async function attemptRupture() {
    if (!window.confirm('No cenário fictício, a tentativa pode levar você ao poder fora da ordem constitucional ou à prisão e remoção do cargo. Continuar?')) return;
    setBusy(true);
    try { const data = await request('/api/regime/rupture/attempt', { method: 'POST', body: '{}' }); setState(data.state); setNotice(data.result.message); setRuptureInfo(null); }
    catch (e) { setNotice(e.message); } finally { setBusy(false); }
  }

  async function submitBudgetTransfer() {
    setBusy(true);
    try {
      const data = await request('/api/budget/reallocate', { method: 'POST', body: JSON.stringify({ source: budgetSource, target: budgetTarget, amount_bi: Number(budgetAmount) }) });
      setBudgetView(data.budget); setState(data.state); setNotice(`Remanejamento registrado. A entrega está prevista para ${data.project.completion_date}.`);
    } catch (e) { setNotice(e.message); } finally { setBusy(false); }
  }

  async function submitOperatingBudget() {
    setBusy(true);
    try {
      const data = await request('/api/budget/operating', { method: 'POST', body: JSON.stringify({ travel_cut_pct: Number(travelCutPct), residence_cut_pct: Number(residenceCutPct) }) });
      setBudgetView(data.budget); setState(data.state);
      const annual = data.effects.find((item) => item.label === 'Economia anual recorrente')?.value_bi || 0;
      setNotice(annual >= 0 ? `Cortes registrados: R$ ${annual.toFixed(3)} bi a menos por ano em despesas recorrentes.` : `Recomposição registrada: R$ ${Math.abs(annual).toFixed(3)} bi a mais por ano em despesas recorrentes.`);
    } catch (e) { setNotice(e.message); } finally { setBusy(false); }
  }

  if (!state) return <main className="loading"><span className="brand-mark">M</span><p>Preparando o gabinete…</p>{notice && <p>{notice}</p>}</main>;
  const m = state.metrics;
  const termMonth = Math.min(48, Math.max(1, state.month || 1));
  const monthsRemaining = Math.max(0, 48 - termMonth);
  const operatingLines = budgetView?.operating?.lines || {};
  const proposedOperatingSavings = (Number(operatingLines.official_travel?.annual_cost_bi || 0) * Number(travelCutPct) / 100)
    + (Number(operatingLines.official_residence?.annual_cost_bi || 0) * Number(residenceCutPct) / 100);
  const currentOperatingSavings = Number(budgetView?.operating?.annual_savings_bi || 0);
  const fiscalReferenceGdp = Number(budgetView?.operating?.nominal_gdp_bi || 15000);
  const proposedPrimaryBalance = Number(m.primary_balance) + ((proposedOperatingSavings - currentOperatingSavings) / fiscalReferenceGdp * 100);
  const tabs = ['Visão geral', 'Medidas', 'Orçamento', 'Diplomacia', 'Crises', 'Eleição', 'Instituições', 'Agenda', 'Aprendizado'];
  const dashboardTab = activeTab === 'Visão geral' || activeTab === 'Medidas';

  return <div className="app-shell">
    <header className="topbar"><a className="brand" href="#"><span className="brand-mark">M</span><span>MANDATO<small>SIMULADOR DE GOVERNO</small></span></a><div className="date-block"><span>{dateLabel}</span><small>MÊS {termMonth} DE 48 · DIA {state.day_of_mandate} DE 1461 · {(state.office_status || 'incumbent').replaceAll('_', ' ')}</small></div><div className="top-actions"><label className="difficulty-picker"><span>DIFICULDADE</span><select value={state.difficulty || 'normal'} onChange={(e) => changeDifficulty(e.target.value)}><option value="tranquilo">Tranquilo</option><option value="normal">Normal</option><option value="dificil">Difícil</option><option value="complicado">Complicado</option><option value="realismo_puro">Realismo Puro</option></select></label><span className="live-dot">SIMULAÇÃO LOCAL</span><button className="quiet-button" onClick={() => advance(1)} disabled={busy}>Próximo dia <b>→</b></button></div></header>
    <nav className="tabs">{tabs.map((tab) => <button key={tab} className={activeTab === tab ? 'tab active' : 'tab'} onClick={() => setActiveTab(tab)}>{tab}</button>)}<div className="tab-spacer"/><button className="advance-link" onClick={() => advance(7)} disabled={busy}>Avançar 7 dias <span>↗</span></button><button className="advance-link" onClick={() => advance(30)} disabled={busy}>Avançar mês <span>↗</span></button></nav>

    <main className="content">
      <section className="welcome-row"><div><div className="eyebrow">GABINETE DA PRESIDÊNCIA <span>·</span> CICLO {state.term}</div><h1>O país, em movimento.</h1><p>Decida, acompanhe os efeitos e ajuste o rumo. Um mandato, um dia de cada vez.</p></div><div className="term-card"><span>MANDATO</span><strong>{termMonth}<small> / 48</small></strong><div className="progress"><i style={{ width: `${termMonth / 48 * 100}%` }}/></div><small>{monthsRemaining} meses restantes</small></div></section>

      {dashboardTab && <><div className="indicator-toolbar"><span>SEU PAINEL · {state.dashboard_cards?.length ?? 6} INDICADORES</span><details className="dashboard-customizer"><summary>Escolher indicadores</summary><div>{indicatorOptions.map((option) => <label key={option.key}><input type="checkbox" checked={(state.dashboard_cards || indicatorOptions.slice(0, 6).map((item) => item.key)).includes(option.key)} onChange={() => toggleDashboardCard(option.key)} />{option.label}</label>)}</div></details></div><section className="indicator-grid">
        {(state.dashboard_cards || indicatorOptions.slice(0, 6).map((item) => item.key)).map((key) => { const option = indicatorOptions.find((item) => item.key === key); if (!option) return null; const tone = key === 'primary_balance' ? (m.primary_balance < 0 ? 'red' : 'green') : option.tone; return <Metric key={key} label={option.label} value={m[key]} unit={option.unit} tone={tone || ''} detail={option.detail} />; })}
      </section>

      <div className="main-grid">
        <section className="panel measure-panel">
          <div className="panel-heading"><div><div className="eyebrow">CENTRO DE DECISÕES</div><h2>Escreva uma medida</h2><p>Descreva a ideia com suas palavras. O motor calcula os efeitos antes de você confirmar.</p></div><span className="ai-chip"><i/> INTERPRETAÇÃO IA</span></div>
          <label className="field-label" htmlFor="measure">PROPOSTA DO GOVERNO</label>
          <div className="cadence-summary"><span>Agenda executiva: uma decisão administrativa a cada 7 dias ({state.action_limits?.executive_days ?? 0} dia(s) de espera).</span><span>Pauta legislativa: um projeto a cada {state.legislative_calendar?.cooldown_days || 60} dias ({state.action_limits?.legislative_days ?? 0} dia(s) de espera); {state.action_limits?.pending_bills ?? 0} em tramitação · {state.action_limits?.laws_enacted ?? 0} leis aprovadas.</span></div>
          {state.legislative_calendar?.pending_bills?.map((bill) => <div className="pending-bill" key={bill.id}><span>TRAMITANDO · VOTAÇÃO {bill.decision_date}</span><b>{bill.title}</b><small>{bill.instrument} · aprovação por regra parlamentar do simulador</small></div>)}
          <textarea id="measure" value={measure} onChange={(e) => setMeasure(e.target.value)} placeholder="Ex.: revisar contratos renováveis, publicar os preços de referência e direcionar a economia comprovada à redução da dívida…" maxLength={3000}/>
          <div className="composer-footer"><span>{measure.length} / 3000 caracteres <span className="muted">· sem compromisso até simular</span></span><button className="primary-button" disabled={busy || !measure.trim()} onClick={interpret}>{busy ? 'Analisando…' : 'Interpretar e simular'}<b>→</b></button></div>
          {notice && <div className="notice">{notice}</div>}
          {preview && <div className="preview-card"><div className="preview-top"><div><div className="eyebrow">PRÉVIA · NÃO APLICADA</div><h3>{preview.interpretation.title}</h3></div><span className="confidence">{Math.round(preview.interpretation.confidence * 100)}% confiança</span></div><p>{preview.interpretation.summary}</p><div className="simulation-timing">{preview.timing}</div><div className="preview-tags"><span>{preview.interpretation.instrument}</span><span>{preview.interpretation.policy_area}</span><span>{preview.interpretation.duration_days ? `${preview.interpretation.duration_days} dias` : 'efeito permanente'}</span></div><div className="impact-row">{preview.forecast.map((item) => <div key={item.label}><span>{item.label}</span><strong className={item.tone}>{item.value}</strong></div>)}</div><div className="preview-bottom"><span>{preview.interpretation.constraints?.length ? preview.interpretation.constraints.join(' · ') : 'Regras e efeitos estimados pelo motor do jogo'}</span><button className="primary-button" onClick={signMeasure} disabled={busy}>Aplicar medida <b>→</b></button></div><details className="correction"><summary>Corrigir interpretação para melhorar as próximas leituras</summary><textarea value={correction} onChange={(e) => setCorrection(e.target.value)} placeholder="Escreva a interpretação correta em uma frase ou cole o resumo estruturado…"/><button className="secondary-button" onClick={saveCorrection} disabled={busy || !correction.trim()}>Guardar correção</button></details></div>}
        </section>

        <aside className="side-column"><section className="panel compact-panel"><div className="panel-heading small"><div><div className="eyebrow">ESTABILIDADE</div><h2>Capacidade de governar</h2></div><strong className="score">{m.governability}<small>/100</small></strong></div><div className="bar"><i style={{ width: `${m.governability}%` }}/></div><div className="mini-stats"><div><span>Base no Congresso</span><b>{m.congress_support}%</b></div><div><span>Confiança institucional</span><b>{m.institutional_trust}/100</b></div></div></section>
        <section className="panel compact-panel"><div className="panel-heading small"><div><div className="eyebrow">AGENDA PRÓXIMA</div><h2>O que vem pela frente</h2></div><button className="icon-button" onClick={() => setActiveTab('Agenda')}>↗</button></div>{state.events?.length ? state.events.slice(0, 3).map((event) => <div className="event" key={event.id}><span className="event-date">{event.days_until === 0 ? 'HOJE' : `EM ${event.days_until} DIAS`}</span><div><b>{event.title}</b><small>{event.description}</small></div></div>) : <p className="empty-state">Agenda tranquila por enquanto. Avance alguns dias para acompanhar o mandato.</p>}</section>
        <section className="panel compact-panel"><div className="panel-heading small"><div><div className="eyebrow">REGISTRO</div><h2>Últimas decisões</h2></div></div>{state.recent_actions?.length ? state.recent_actions.slice(0, 3).map((action) => <div className="decision" key={action.id}><span>✓</span><div><b>{action.title}</b><small>{new Date(`${action.date}T12:00:00`).toLocaleDateString('pt-BR')} · {action.kind}</small></div></div>) : <p className="empty-state">Nenhuma medida assinada ainda.</p>}</section></aside>
      </div></>}

      {activeTab === 'Agenda' && <section className="panel agenda-page"><div className="eyebrow">CALENDÁRIO DO MANDATO</div><h2>Agenda e acontecimentos</h2><p className="page-description">A linha do tempo acompanha o calendário real da campanha simulada. Avance um dia, uma semana ou um mês.</p>{state.events?.length ? state.events.map((event) => <div className="agenda-event" key={event.id}><div className="agenda-count">{event.days_until === 0 ? 'HOJE' : `${event.days_until} DIAS`}<small>{new Date(`${event.date}T12:00:00`).toLocaleDateString('pt-BR')}</small></div><div><h3>{event.title}</h3><p>{event.description}</p></div></div>) : <div className="empty-state">Não há eventos futuros cadastrados. Novos eventos aparecem conforme o conteúdo do jogo crescer.</div>}</section>}

      {activeTab === 'Diplomacia' && <DiplomacyPanel onState={setState} onNotice={setNotice} busy={busy} setBusy={setBusy} />}

      {activeTab === 'Aprendizado' && <section className="panel learning-page"><div className="eyebrow">MEMÓRIA E AGENTE PYTHON</div><h2>O sistema melhora com suas correções</h2><p className="page-description">Quando você corrige uma interpretação, o exemplo fica salvo localmente e pode orientar leituras parecidas. O motor continua calculando os efeitos com regras explícitas.</p><div className="learning-cards"><article><span>INTERPRETAÇÕES CORRIGIDAS</span><strong>{state.learning?.corrections_saved ?? 0}</strong><small>Exemplos guardados no SQLite deste jogo</small></article><article><span>POLÍTICA DO AGENTE</span><strong>Python</strong><small>Treino opcional com estados e efeitos sintéticos</small></article><article><span>IA DE TEXTO</span><strong>Gemini</strong><small>Classifica medidas; não decide os resultados numéricos</small></article></div><div className="learning-note"><b>Treinar a política base</b><code>python -m app.bot.trainer --episodes 3000</code><span>Execute no diretório <code>game/backend</code>. O treino não faz chamadas à API nem consome crédito de IA.</span></div></section>}
      {activeTab === 'Orçamento' && <section className="panel agenda-page">
        <div className="eyebrow">EXECUTIVO FEDERAL · DESPESAS E INVESTIMENTOS</div>
        <h2>Orçamento do governo</h2>
        <p className="page-description">Viagens oficiais e manutenção das residências entram nas despesas do governo. Reduza essas rubricas para melhorar o resultado primário; os valores são estimativas fictícias do simulador.</p>
        {budgetView ? <>
          <FiscalPanel data={budgetView.fiscal} />
          <div className="operating-budget">
            <div className="operating-heading">
              <div><span className="eyebrow">DESPESAS DE FUNCIONAMENTO</span><h3>Viagens e moradia oficial</h3><p>Revisão a cada 30 dias. O corte afeta o gasto anual e a trajetória fiscal.</p></div>
              <strong className="operating-saving">R$ {proposedOperatingSavings.toFixed(3)} bi<small>economia anual selecionada</small></strong>
            </div>
            <div className="operating-lines">
              {Object.entries(budgetView.operating.lines).map(([key, line]) => {
                const isTravel = key === 'official_travel';
                const cut = isTravel ? Number(travelCutPct) : Number(residenceCutPct);
                const max = isTravel ? 75 : 50;
                return <article key={key}>
                  <div><b>{line.label}</b><small>{line.description}</small><span>Orçamento: R$ {Number(line.annual_cost_bi).toFixed(1)} bi/ano · após o corte: R$ {(Number(line.annual_cost_bi) * (1 - cut / 100)).toFixed(3)} bi/ano</span></div>
                  <label>Reduzir<select value={cut} onChange={(event) => isTravel ? setTravelCutPct(Number(event.target.value)) : setResidenceCutPct(Number(event.target.value))}>{[0, 10, 25, 50, 75].filter((value) => value <= max).map((value) => <option value={value} key={value}>{value}%</option>)}</select></label>
                </article>;
              })}
            </div>
            <div className="operating-impact"><span>Resultado primário atual <b>{Number(m.primary_balance).toFixed(3)}% do PIB</b></span><span>Após aplicar <b>{Number(proposedPrimaryBalance).toFixed(3)}% do PIB</b></span><small>Estimativa proporcional ao PIB nominal de referência do simulador (R$ {(fiscalReferenceGdp / 1000).toFixed(0)} tri). A trajetória da dívida acumula o efeito ao longo dos dias.</small></div>
            <div className="operating-footer"><small>{budgetView.operating.days_until_review ? `Próxima revisão em ${budgetView.operating.days_until_review} dia(s).` : 'Ajuste disponível agora.'} As rubricas fazem parte da despesa primária anual. Os limites evitam cortar integralmente deslocamentos institucionais ou manutenção essencial.</small><button className="primary-button" disabled={busy || budgetView.operating.days_until_review > 0 || (Number(budgetView.operating.travel_cut_pct) === Number(travelCutPct) && Number(budgetView.operating.residence_cut_pct) === Number(residenceCutPct))} onClick={submitOperatingBudget}>Aplicar cortes</button></div>
          </div>
          {notice && <div className="notice">{notice}</div>}
          <h3 className="subheading">Carteira de investimentos</h3>
          <p className="page-description">Carteira simplificada em R$ bilhões anuais. O total não cresce: para ampliar uma área, remaneje verba de outra. Resultados chegam após a maturação do projeto.</p>
          <div className="budget-total"><span>Total anual da carteira de investimento</span><strong>R$ {budgetView.annual_investment_bi.toFixed(1)} bi</strong><small>Próxima revisão em {budgetView.days_until_reallocation} dia(s)</small></div>
          <div className="investment-grid">{Object.entries(budgetView.areas).map(([key, area]) => <article key={key}><span>{area.ministry}</span><h3>{area.label}</h3><strong>R$ {Number(budgetView.allocations[key] || 0).toFixed(1)} bi/ano</strong><small>Resultado estimado em {area.lag_days} dias</small></article>)}</div>
          <div className="budget-form"><h3>Remanejar investimento</h3><label>Retirar de<select value={budgetSource} onChange={(e) => setBudgetSource(e.target.value)}>{Object.entries(budgetView.areas).map(([key, area]) => <option key={key} value={key}>{area.label}</option>)}</select></label><label>Reforçar<select value={budgetTarget} onChange={(e) => setBudgetTarget(e.target.value)}>{Object.entries(budgetView.areas).map(([key, area]) => <option key={key} value={key}>{area.label}</option>)}</select></label><label>Valor anual (R$ bi)<input type="number" min="0.1" max={Math.min(10, Number(budgetView.allocations[budgetSource] || 0) * .2)} step="0.1" value={budgetAmount} onChange={(e) => setBudgetAmount(e.target.value)} /></label><button className="primary-button" disabled={busy || budgetView.days_until_reallocation > 0 || budgetSource === budgetTarget} onClick={submitBudgetTransfer}>Confirmar remanejamento</button></div>
          <h3 className="subheading">Investimentos em execução</h3>
          {budgetView.pipeline.length ? budgetView.pipeline.map((project) => <div className="agenda-event" key={project.id}><div className="agenda-count">EM CURSO<small>{project.completion_date}</small></div><div><h3>{budgetView.areas[project.area]?.label}</h3><p>Reforço de R$ {project.annual_increase_bi.toFixed(1)} bi/ano. Os efeitos aparecem na conclusão simulada.</p></div></div>) : <div className="empty-state">Nenhum investimento novo em maturação.</div>}
          <details className="ministry-roster"><summary>Ver pastas oficiais disponíveis ({ministries.length})</summary><div>{ministries.map((ministry) => <span key={ministry.name}>{ministry.name}</span>)}</div><small>Catálogo baseado no SIORG; estas pastas são fixas no jogo. A carteira de investimentos não cria ministérios.</small></details>
        </> : <div className="empty-state">Carregando o orçamento...</div>}
      </section>}
      {activeTab === 'Crises' && <section className="panel agenda-page"><div className="eyebrow">EVENTOS FICTÍCIOS · CONSEQUÊNCIAS NO MOTOR</div><h2>Crises e respostas</h2><p className="page-description">Os eventos são simulados. Enquanto uma crise estiver ativa, seus efeitos continuam; cada resposta altera orçamento, atividade e apoio.</p>{state.active_crises?.length ? state.active_crises.map((event) => <article className="crisis-card" key={event.id}><div className="crisis-heading"><div><span className="simulated-tag">SIMULAÇÃO</span><h3>{event.title}</h3></div><b>Gravidade {event.severity}/3</b></div><p>{event.description}</p><small>Ativa há {event.days_active} dias · impacto contínuo no PIB, infraestrutura e aprovação.</small><div className="crisis-actions">{event.options?.map((option) => <button key={option.id} className="secondary-button" disabled={busy} onClick={() => respondEvent(event.id, option.id)}>{option.label}<small>Custo simulado: R$ {option.cost_bi.toFixed(1)} bi</small></button>)}</div></article>) : <div className="empty-state">Nenhuma crise ativa. Eventos futuros podem surgir conforme o calendário e a dificuldade.</div>}<h3 className="subheading">Noticiário simulado recente</h3>{state.simulated_news?.slice(0, 8).map((item) => <div className="agenda-event" key={item.id}><div className="agenda-count">SIMULADO<small>{item.date}</small></div><div><h3>{item.title}</h3><p>{item.description}</p></div></div>)}</section>}

      {activeTab === 'Eleição' && <section className="panel agenda-page"><div className="eyebrow">CALENDÁRIO ELEITORAL FICTÍCIO</div><h2>{state.campaign_active ? 'Campanha aberta; governo em exercício' : 'Mandato e eleição'}</h2><p className="page-description">A campanha não pausa o governo. Você continua tomando decisões e respondendo a eventos até o resultado e, se perder, permanece como presidente em transição até 1º de janeiro.</p><div className="election-summary"><article><span>PRÓXIMA VOTAÇÃO</span><strong>{state.election_date}</strong></article><article><span>SITUAÇÃO NO CARGO</span><strong>{(state.office_status || 'incumbent').replaceAll('_', ' ')}</strong></article><article><span>RESULTADO</span><strong>{state.election?.result === 'lost' ? 'Derrota; transição até a posse' : state.election?.result === 'reelected' ? 'Reeleição; novo mandato na posse' : 'Ainda não apurado'}</strong></article></div><p>O resultado usa apoio, governabilidade, integridade, economia e variação aleatória reproduzível pela semente da campanha. Depois da transição, a carreira continua fora da Presidência.</p></section>}

      {activeTab === 'Instituições' && <section className="panel agenda-page"><div className="eyebrow">CENÁRIO INSTITUCIONAL FICTÍCIO</div><h2>Instituições e estabilidade</h2><p className="page-description">Indicadores agregados mudam com as decisões. A opção de ruptura é uma mecânica de alto risco, inteiramente abstrata; não há passos operacionais.</p><div className="institution-grid">{Object.entries(state.institutions || {}).map(([key, value]) => <article key={key}><span>{key.replaceAll('_', ' ')}</span><strong>{Math.round(value)}/100</strong><div className="bar"><i style={{ width: `${value}%` }}/></div></article>)}</div><div className="rupture-box"><h3>Ruptura institucional simulada</h3><p>Sucesso: governo de facto, resistência institucional, isolamento e choque econômico. Fracasso: prisão e remoção do cargo. Os resultados são calculados pelo motor e pela semente da partida.</p><button className="secondary-button" onClick={loadRupturePreview}>Ver chance e consequências</button>{ruptureInfo && <div className="rupture-preview"><b>Chance abstrata de sucesso: {ruptureInfo.chance}%</b><p>{ruptureInfo.success}</p><p>{ruptureInfo.failure}</p><button className="danger-button" disabled={busy} onClick={attemptRupture}>Tentar ruptura no cenário</button></div>}</div></section>}

      <footer className="footer"><span>MANDATO · protótipo de simulação</span><span>Eventos e projeções são ficção; resultados numéricos seguem regras do motor.</span></footer>
    </main>
  </div>;
}
