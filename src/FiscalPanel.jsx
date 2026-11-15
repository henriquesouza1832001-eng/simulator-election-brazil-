import './fiscal-panel.css';
import { br } from './format';

export default function FiscalPanel({ data }) {
  if (!data) return null;
  const kpis = [
    ['Receita anual estimada', `R$ ${br(data.annual_revenue_bi, 0)} bi`],
    ['Despesa primária', `R$ ${br(data.annual_primary_spending_bi, 0)} bi`],
    ['Resultado primário', `R$ ${br(data.primary_result_bi, 0)} bi`],
    ['Juros anuais estimados', `R$ ${br(data.annual_interest_bi, 0)} bi`],
    ['Resultado nominal', `R$ ${br(data.annual_nominal_result_bi, 0)} bi`],
    ['Dívida pública', `${br(data.debt_pct_gdp, 1)}% do PIB`],
    ['Despesas extraordinárias no ano', `R$ ${br(data.current_year_extra_spending_bi, 2)} bi`],
  ];
  return <section className="fiscal-overview">
    <div className="fiscal-kpis">{kpis.map(([label, value]) => <article key={label}><span>{label}</span><b>{value}</b></article>)}</div>
    <div className="fiscal-columns">
      <div><h3>Receitas por grupo</h3>{data.revenue.map((line) => <div className="fiscal-line" key={line.key}><span>{line.label}</span><b>R$ {br(line.annual_bi, 0)} bi</b></div>)}</div>
      <div><h3>Despesas primárias</h3>{data.primary_spending.map((line) => <div className="fiscal-line" key={line.key}><span>{line.label}{line.key === 'investment' && data.executive_investment && <small className="fiscal-investment-note">Programas presidenciais: R$ {br(data.executive_investment.committed_bi, 1)} bi comprometidos · R$ {br(data.executive_investment.available_bi, 1)} bi disponíveis dentro desta dotação. {data.executive_investment.overcommitted_bi > 0 ? `Compromissos excedem a dotação em R$ ${br(data.executive_investment.overcommitted_bi, 1)} bi.` : 'Já incluídos no total de investimentos.'}</small>}</span><b>R$ {br(line.annual_bi, 1)} bi</b></div>)}</div>
    </div>
    <small>{data.note} Saldo primário: {br(data.primary_balance_pct_gdp, 2)}% do PIB · custo médio da dívida {br(data.interest_rate_pct, 1)}% · risco-país {br(data.country_risk, 0)} · credibilidade fiscal {br(data.fiscal_credibility, 0)}/100.</small>
  </section>;
}
