import './fiscal-panel.css';

export default function FiscalPanel({ data }) {
  if (!data) return null;
  const kpis = [
    ['Receita anual estimada', `R$ ${data.annual_revenue_bi.toFixed(0)} bi`],
    ['Despesa primária', `R$ ${data.annual_primary_spending_bi.toFixed(0)} bi`],
    ['Resultado primário', `R$ ${data.primary_result_bi.toFixed(0)} bi`],
    ['Juros anuais estimados', `R$ ${data.annual_interest_bi.toFixed(0)} bi`],
    ['Resultado nominal', `R$ ${data.annual_nominal_result_bi.toFixed(0)} bi`],
    ['Dívida pública', `${data.debt_pct_gdp.toFixed(1)}% do PIB`],
    ['Despesas extraordinárias no ano', `R$ ${data.current_year_extra_spending_bi.toFixed(2)} bi`],
  ];
  return <section className="fiscal-overview">
    <div className="fiscal-kpis">{kpis.map(([label, value]) => <article key={label}><span>{label}</span><b>{value}</b></article>)}</div>
    <div className="fiscal-columns">
      <div><h3>Receitas por grupo</h3>{data.revenue.map((line) => <div className="fiscal-line" key={line.key}><span>{line.label}</span><b>R$ {line.annual_bi.toFixed(0)} bi</b></div>)}</div>
      <div><h3>Despesas primárias</h3>{data.primary_spending.map((line) => <div className="fiscal-line" key={line.key}><span>{line.label}{line.key === 'investment' && data.executive_investment && <small className="fiscal-investment-note">Programas presidenciais: R$ {data.executive_investment.committed_bi.toFixed(1)} bi comprometidos · R$ {data.executive_investment.available_bi.toFixed(1)} bi disponíveis dentro desta dotação. {data.executive_investment.overcommitted_bi > 0 ? `Compromissos excedem a dotação em R$ ${data.executive_investment.overcommitted_bi.toFixed(1)} bi.` : 'Já incluídos no total de investimentos.'}</small>}</span><b>R$ {line.annual_bi.toFixed(1)} bi</b></div>)}</div>
    </div>
    <small>{data.note} Saldo primário: {data.primary_balance_pct_gdp.toFixed(2)}% do PIB · custo médio da dívida {data.interest_rate_pct.toFixed(1)}% · risco-país {data.country_risk.toFixed(0)} · credibilidade fiscal {data.fiscal_credibility.toFixed(0)}/100.</small>
  </section>;
}
