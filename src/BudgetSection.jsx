import FiscalLevers from './FiscalLevers.jsx';
import FiscalPanel from './FiscalPanel';
import InvestmentsPanel from './InvestmentsPanel';
import { br } from './format';

/** Parte de App.jsx: Orçamento. Recebe do App o estado e as ações de que precisa. */
export default function BudgetSection({ applyFiscalLever, budgetSection, budgetView, busy, fiscalReferenceGdp, m, ministries, notice, proposedOperatingSavings, proposedPrimaryBalance, residenceCutPct, setActiveTab, setBudgetSection, setResidenceCutPct, setTravelCutPct, submitBudgetTransfer, submitOperatingBudget, travelCutPct }) {
  return (
    <section className="panel agenda-page">
        <div className="eyebrow">EXECUTIVO FEDERAL · DESPESAS E INVESTIMENTOS</div>
        <h2>Orçamento do governo</h2>
        <p className="page-description">Viagens oficiais e manutenção das residências entram nas despesas do governo. Para mexer de verdade no resultado primário, use as alavancas fiscais; cortes de viagens e residências rendem pouco.</p>
        {budgetView ? <>
          <div className="budget-subnav" role="tablist" aria-label="Seções do orçamento">{['Contas públicas', 'Investimentos', 'Obras'].map((section) => <button key={section} role="tab" aria-selected={budgetSection === section} className={budgetSection === section ? 'active' : ''} onClick={() => setBudgetSection(section)}>{section}</button>)}</div>
          {notice && <div className="notice">{notice}</div>}
          {budgetSection === 'Contas públicas' && <>
          <FiscalPanel data={budgetView.fiscal} />
          <FiscalLevers levers={budgetView.levers} history={budgetView.levers_history} busy={busy} onUse={applyFiscalLever} />
          <div className="operating-budget">
            <div className="operating-heading">
              <div><span className="eyebrow">DESPESAS DE FUNCIONAMENTO</span><h3>Viagens e moradia oficial</h3><p>Revisão a cada 30 dias. O corte afeta o gasto anual e a trajetória fiscal.</p></div>
              <strong className="operating-saving">R$ {br(proposedOperatingSavings, 3)} bi<small>economia anual selecionada</small></strong>
            </div>
            <div className="operating-lines">
              {Object.entries(budgetView.operating.lines).map(([key, line]) => {
                const isTravel = key === 'official_travel';
                const cut = isTravel ? Number(travelCutPct) : Number(residenceCutPct);
                const max = isTravel ? 75 : 50;
                return <article key={key}>
                  <div><b>{line.label}</b><small>{line.description}</small><span>Orçamento: R$ {br(Number(line.annual_cost_bi), 1)} bi/ano · após o corte: R$ {br(Number(line.annual_cost_bi) * (1 - cut / 100), 3)} bi/ano</span></div>
                  <div className="ds-seg" role="group" aria-label={`Reduzir ${line.label}`}>{[0, 10, 25, 50, 75].filter((value) => value <= max).map((value) => <button type="button" key={value} aria-pressed={cut === value} onClick={() => isTravel ? setTravelCutPct(value) : setResidenceCutPct(value)}>{value === 0 ? 'Manter' : `−${value}%`}</button>)}</div>
                </article>;
              })}
            </div>
            <div className="operating-impact"><span>Resultado primário atual <b>{br(Number(m.primary_balance), 3)}% do PIB</b></span><span>Após aplicar <b>{br(Number(proposedPrimaryBalance), 3)}% do PIB</b></span><small>Estimativa proporcional ao PIB nominal de referência do simulador (R$ {br(fiscalReferenceGdp / 1000, 0)} tri). A trajetória da dívida acumula o efeito ao longo dos dias.</small></div>
            <div className="operating-footer"><small>{budgetView.operating.days_until_review ? `Próxima revisão em ${budgetView.operating.days_until_review} ${Number(budgetView.operating.days_until_review) === 1 ? 'dia' : 'dias'}.` : 'Ajuste disponível agora.'} As rubricas fazem parte da despesa primária anual. Os limites evitam cortar integralmente deslocamentos institucionais ou manutenção essencial.</small><button className="primary-button" disabled={busy || budgetView.operating.days_until_review > 0 || (Number(budgetView.operating.travel_cut_pct) === Number(travelCutPct) && Number(budgetView.operating.residence_cut_pct) === Number(residenceCutPct))} onClick={submitOperatingBudget}>Aplicar cortes</button></div>
          </div>
          </>}
          {budgetSection === 'Investimentos' && <>
          <InvestmentsPanel view={budgetView} busy={busy} onTransfer={submitBudgetTransfer} />
          <details className="ministry-roster"><summary>Ver pastas oficiais disponíveis ({ministries.length})</summary><div>{ministries.map((ministry) => <span key={ministry.name}>{ministry.name}</span>)}</div><small>Catálogo baseado no SIORG; estas pastas são fixas no jogo. A carteira de investimentos não cria ministérios.</small></details>
          </>}
          {budgetSection === 'Obras' && <section className="works-section">
            <div className="operating-heading"><div><span className="eyebrow">CARTEIRA NACIONAL</span><h3>As obras agora ficam em Projetos</h3><p>Lá estão os 37 projetos (do viaduto à missão à Lua), as fases de cada um e a carteira de cada área. O dinheiro continua vindo daqui: ajuste em Investimentos.</p></div></div>
            <button type="button" className="primary-button" onClick={() => setActiveTab('Projetos')}>Abrir Projetos</button>
            <p className="indicator-footnote">Em andamento: {budgetView.works.projects.filter((p) => ['active', 'needs_decision'].includes(p.status)).length} · comprometido por ano em Transportes: R$ {br(budgetView.works.annual_committed_bi, 1)} bi.</p>
          </section>}
        </> : <div className="empty-state">Carregando o orçamento...</div>}
      </section>
  );
}
