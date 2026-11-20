import { br, dataBr, roundHalfUp } from './format';

// Constantes e funções puras do painel (rótulos, precisão de indicadores, leitura de valores do estado). Saíram de App.jsx.
export const fmt = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 1 });
export const difficultyLabels = { tranquilo: 'Tranquilo', normal: 'Normal', dificil: 'Difícil', complicado: 'Complicado', realismo_puro: 'Realismo Puro' };

export const indicatorPrecision = {
  human_development_index: { minimumFractionDigits: 3, maximumFractionDigits: 3 },
  gini_index: { minimumFractionDigits: 3, maximumFractionDigits: 3 },
  country_risk: { minimumFractionDigits: 0, maximumFractionDigits: 0 },
  // indicadores em % ou pontos com uma casa fixa: "4,0" e não "4", para o jogador comparar de relance
  gdp_growth: { minimumFractionDigits: 1, maximumFractionDigits: 1 },
  inflation: { minimumFractionDigits: 1, maximumFractionDigits: 1 },
  unemployment: { minimumFractionDigits: 1, maximumFractionDigits: 1 },
  debt_gdp: { minimumFractionDigits: 1, maximumFractionDigits: 1 },
  primary_balance: { minimumFractionDigits: 1, maximumFractionDigits: 1 },
  approval: { minimumFractionDigits: 1, maximumFractionDigits: 1 },
};
export const indicatorFormatters = new Map();

export function formatIndicator(value, key) {
  const numericValue = Number(value);
  if (!Number.isFinite(numericValue)) return '—';
  const precision = indicatorPrecision[key] ?? { minimumFractionDigits: 0, maximumFractionDigits: 1 };
  const formatKey = `${precision.minimumFractionDigits}:${precision.maximumFractionDigits}`;
  if (!indicatorFormatters.has(formatKey)) {
    indicatorFormatters.set(formatKey, new Intl.NumberFormat('pt-BR', {
      minimumFractionDigits: precision.minimumFractionDigits,
      maximumFractionDigits: precision.maximumFractionDigits,
    }));
  }
  const out = indicatorFormatters.get(formatKey).format(roundHalfUp(numericValue, precision.maximumFractionDigits));
  // evita "-0" quando o valor é pequeno e negativo: mostra duas casas
  if (/^[-−]0(,0+)?$/.test(out) && numericValue !== 0) return numericValue.toLocaleString('pt-BR', { maximumFractionDigits: 2 });
  return out;
}

export function Metric({ label, value, unit = '', tone = '', detail, indicatorKey }) {
  return <article className="metric"><div className="metric-label">{label}</div><div className={`metric-value ${tone}`}>{formatIndicator(value, indicatorKey)}<small>{unit}</small></div>{detail && <div className="metric-detail">{detail}</div>}</article>;
}

export const indicatorOptions = [
  { key: 'gdp_growth', label: 'Atividade econômica', unit: '%', detail: 'Crescimento anual do PIB', tone: 'green' },
  { key: 'inflation', label: 'Inflação', unit: '%', detail: 'Variação anual de preços', tone: 'amber' },
  { key: 'unemployment', label: 'Desemprego', unit: '%', detail: 'Força de trabalho' },
  { key: 'debt_gdp', label: 'Dívida pública', unit: '% do PIB', detail: 'Trajetória da dívida', tone: 'amber' },
  { key: 'primary_balance', label: 'Resultado fiscal', unit: '% do PIB', detail: 'Saldo antes dos juros' },
  { key: 'nominal_result', label: 'Resultado nominal', unit: '% PIB', detail: 'Saldo após juros da dívida', tone: 'amber' },
  { key: 'country_risk', label: 'Risco-país', unit: 'pontos', detail: 'Prêmio de risco soberano', tone: 'amber' },
  { key: 'fiscal_credibility', label: 'Credibilidade fiscal', unit: '/100', detail: 'Confiança na trajetória das contas', tone: 'blue' },
  { key: 'approval', label: 'Aprovação', unit: '%', detail: 'Apoio ao governo', tone: 'green' },
  { key: 'governability', label: 'Governabilidade', unit: '/100', detail: 'Capacidade de formar maioria', tone: 'green' },
  { key: 'integrity', label: 'Integridade', unit: '/100', detail: 'Confiança e transparência', tone: 'blue' },
  { key: 'regional_infrastructure', label: 'Infraestrutura regional', unit: '/100', detail: 'Resiliência de estradas e serviços', tone: 'blue' },
  { key: 'nominal_gdp_bi', label: 'PIB nominal', unit: 'R$ bi', detail: 'Tamanho nominal da economia no cenário', source: 'fiscal' },
  { key: 'annual_revenue_bi', label: 'Receita anual', unit: 'R$ bi', detail: 'Arrecadação anual estimada', source: 'fiscal', tone: 'green' },
  { key: 'annual_primary_spending_bi', label: 'Despesa primária', unit: 'R$ bi', detail: 'Despesa antes dos juros da dívida', source: 'fiscal', tone: 'amber' },
  { key: 'annual_interest_bi', label: 'Juros anuais', unit: 'R$ bi', detail: 'Custo anual estimado da dívida', source: 'fiscal', tone: 'amber' },
  { key: 'interest_rate_pct', label: 'Juro médio da dívida', unit: '%', detail: 'Taxa média aplicada ao estoque da dívida', source: 'fiscal', tone: 'amber' },
  { key: 'population_millions', label: 'População', unit: 'mi', detail: 'População total do cenário', source: 'social' },
  { key: 'human_development_index', label: 'IDH', unit: '/1', detail: 'Desenvolvimento humano agregado', source: 'social', tone: 'blue' },
  { key: 'gini_index', label: 'Desigualdade (Gini)', unit: '/1', detail: 'Desigualdade de renda; menor é melhor', source: 'social', tone: 'amber' },
  { key: 'poverty_rate_pct', label: 'Pobreza', unit: '%', detail: 'Parcela estimada da população em pobreza', source: 'social', tone: 'amber' },
  { key: 'life_expectancy_years', label: 'Expectativa de vida', unit: 'anos', detail: 'Expectativa de vida ao nascer no cenário', source: 'social' },
  { key: 'infant_mortality_per_1000', label: 'Mortalidade infantil', unit: '/1.000', detail: 'Óbitos infantis estimados por mil nascidos vivos', source: 'social', tone: 'amber' },
  { key: 'homicide_rate_per_100k', label: 'Homicídios', unit: '/100 mil', detail: 'Taxa estimada de homicídios', source: 'social', tone: 'amber' },
  { key: 'sanitation_coverage_pct', label: 'Cobertura de saneamento', unit: '%', detail: 'Cobertura estimada de saneamento', source: 'social' },
  { key: 'school_completion_pct', label: 'Conclusão escolar', unit: '%', detail: 'Conclusão escolar estimada', source: 'social' },
];

export const detailedIndicatorGroups = [
  { title: 'Economia e trabalho', items: [
    { label: 'Crescimento do PIB', key: 'gdp_growth', unit: '%', source: 'metric', detail: 'Variação anual estimada da atividade econômica.' },
    { label: 'Inflação', key: 'inflation', unit: '%', source: 'metric', detail: 'Variação anual de preços no cenário.' },
    { label: 'Desemprego', key: 'unemployment', unit: '%', source: 'metric', detail: 'Parcela estimada da força de trabalho sem ocupação.' },
  ] },
  { title: 'Contas públicas', items: [
    { label: 'Resultado primário', key: 'primary_balance', unit: '% do PIB', source: 'metric', detail: 'Receitas menos despesas antes dos juros.' },
    { label: 'Resultado nominal', key: 'nominal_result', unit: '% do PIB', source: 'metric', detail: 'Saldo depois dos juros da dívida.' },
    { label: 'Dívida pública', key: 'debt_gdp', unit: '% do PIB', source: 'metric', detail: 'Estoque da dívida em relação ao tamanho da economia.' },
    { label: 'Credibilidade fiscal', key: 'fiscal_credibility', unit: '/100', source: 'metric', detail: 'Confiança calculada pelo modelo fiscal do jogo.' },
    { label: 'Risco-país', key: 'country_risk', unit: 'pontos', source: 'metric', detail: 'Prêmio de risco estimado pelo modelo.' },
    { label: 'PIB nominal', key: 'nominal_gdp_bi', unit: 'R$ bi', source: 'fiscal', detail: 'Tamanho nominal da economia no cenário; não é uma série oficial.' },
    { label: 'Receita anual', key: 'annual_revenue_bi', unit: 'R$ bi', source: 'fiscal', detail: 'Arrecadação agregada estimada no livro-caixa fiscal do jogo.' },
    { label: 'Despesa primária anual', key: 'annual_primary_spending_bi', unit: 'R$ bi', source: 'fiscal', detail: 'Despesas antes dos juros, incluindo itens obrigatórios e discricionários.' },
    { label: 'Juros anuais da dívida', key: 'annual_interest_bi', unit: 'R$ bi', source: 'fiscal', detail: 'Estimativa anual de juros sobre a dívida pública simulada.' },
    { label: 'Juro médio da dívida', key: 'interest_rate_pct', unit: '%', source: 'fiscal', detail: 'Taxa média estimada do estoque; não representa diretamente a Selic.' },
    { label: 'Investimento público anual', key: 'annual_investment_bi', unit: 'R$ bi', source: 'budget', detail: 'Dotação anual simulada para investimentos federais.' },
  ] },
  { title: 'Apoio e capacidade de governar', items: [
    { label: 'Aprovação', key: 'approval', unit: '%', source: 'metric', detail: 'Apoio nacional ao governo.' },
    { label: 'Governabilidade', key: 'governability', unit: '/100', source: 'metric', detail: 'Capacidade de sustentar decisões e formar maioria.' },
    { label: 'Apoio no Congresso', key: 'congress_support', unit: '%', source: 'metric', detail: 'Apoio parlamentar agregado no cenário.' },
    { label: 'Confiança institucional', key: 'institutional_trust', unit: '/100', source: 'metric', detail: 'Confiança geral nas instituições.' },
    { label: 'Integridade', key: 'integrity', unit: '/100', source: 'metric', detail: 'Transparência pública e exposição a escândalos.' },
  ] },
  { title: 'Instituições e estabilidade', items: [
    { label: 'Lealdade militar à Constituição', key: 'military_loyalty', unit: '/100', source: 'institution', detail: 'Relação institucional das Forças Armadas com a ordem constitucional.' },
    { label: 'Ordem constitucional', key: 'constitutional_order', unit: '/100', source: 'institution', detail: 'Estabilidade das regras e continuidade institucional.' },
    { label: 'Legitimidade civil', key: 'civilian_legitimacy', unit: '/100', source: 'institution', detail: 'Reconhecimento da autoridade civil no cenário.' },
    { label: 'Resistência institucional', key: 'institutional_resistance', unit: '/100', source: 'institution', detail: 'Capacidade de instituições conterem rupturas simuladas.' },
  ] },
  { title: 'Serviços e investimento', items: [
    { label: 'Educação', key: 'education', unit: '/100', source: 'outcome', detail: 'Resultado acumulado dos investimentos em educação.' },
    { label: 'Saúde', key: 'health', unit: '/100', source: 'outcome', detail: 'Resultado acumulado dos investimentos em saúde.' },
    { label: 'Segurança pública', key: 'security', unit: '/100', source: 'outcome', detail: 'Resultado acumulado dos investimentos em segurança.' },
    { label: 'Infraestrutura', key: 'infrastructure', unit: '/100', source: 'outcome', detail: 'Entrega agregada de infraestrutura financiada.' },
    { label: 'Produtividade', key: 'productivity', unit: '/100', source: 'outcome', detail: 'Efeito dos investimentos produtivos.' },
    { label: 'Resiliência rural', key: 'rural_resilience', unit: '/100', source: 'outcome', detail: 'Capacidade de adaptação rural a choques climáticos.' },
  ] },
  { title: 'Diplomacia e regiões', items: [
    { label: 'Influência multilateral', key: 'multilateral_influence', unit: '/100', source: 'diplomacy', detail: 'Presença e influência do país em fóruns internacionais.' },
    { label: 'Relação média com países', key: 'average_relation', unit: '/100', source: 'diplomacy', detail: 'Média das relações bilaterais cadastradas no cenário.' },
    { label: 'Apoio regional médio', key: 'support', unit: '%', source: 'regional', detail: 'Média das regiões atualmente representadas na partida.' },
    { label: 'Atividade regional média', key: 'economic_activity', unit: '/100', source: 'regional', detail: 'Atividade econômica regional relativa no cenário.' },
    { label: 'Infraestrutura regional', key: 'regional_infrastructure', unit: '/100', source: 'metric', detail: 'Resiliência agregada de estradas e serviços no cenário.' },
  ] },
  { title: 'População e qualidade de vida', items: [
    { label: 'População', key: 'population_millions', unit: 'milhões', source: 'social', detail: 'População total simulada; varia lentamente ao longo dos anos.' },
    { label: 'IDH', key: 'human_development_index', unit: '/1', source: 'social', detail: 'Índice agregado ligado a educação, saúde e produtividade.' },
    { label: 'Desigualdade (Gini)', key: 'gini_index', unit: '/1', source: 'social', detail: 'Estimativa agregada; valores menores representam menor desigualdade.' },
    { label: 'Pobreza', key: 'poverty_rate_pct', unit: '%', source: 'social', detail: 'Estimativa influenciada por crescimento, emprego e educação.' },
    { label: 'Expectativa de vida', key: 'life_expectancy_years', unit: 'anos', source: 'social', detail: 'Indicador de longo prazo influenciado por saúde e segurança.' },
    { label: 'Mortalidade infantil', key: 'infant_mortality_per_1000', unit: 'por 1.000', source: 'social', detail: 'Estimativa influenciada pela saúde e pela cobertura de saneamento.' },
    { label: 'Homicídios', key: 'homicide_rate_per_100k', unit: 'por 100 mil', source: 'social', detail: 'Taxa estimada influenciada por segurança e condições econômicas.' },
  ] },
  { title: 'Serviços básicos', items: [
    { label: 'Cobertura de saneamento', key: 'sanitation_coverage_pct', unit: '%', source: 'social', detail: 'Estimativa de cobertura que melhora gradualmente com infraestrutura.' },
    { label: 'Conclusão escolar', key: 'school_completion_pct', unit: '%', source: 'social', detail: 'Estimativa que responde lentamente a resultados de educação.' },
  ] },
];

export const institutionLabels = {
  military_loyalty: 'Lealdade militar à Constituição',
  constitutional_order: 'Ordem constitucional',
  civilian_legitimacy: 'Legitimidade civil',
  institutional_resistance: 'Resistência institucional',
};

export const OFFICE_STATUS_LABEL = { incumbent: 'em exercício', incumbent_caretaker: 'em transição após a eleição', reelected_transition: 'reeleito, em transição', former_president: 'ex-presidente', detained_after_failed_rupture: 'preso após ruptura fracassada' };

export function readIndicator(item, state) {
  // Itens sem `source` (cartões do painel inicial) vivem em state.metrics.
  if (!item.source || item.source === 'metric') return state.metrics?.[item.key];
  if (item.source === 'institution') return state.institutions?.[item.key];
  if (item.source === 'outcome') return state.budget?.outcomes?.[item.key];
  if (item.source === 'fiscal') return state.fiscal?.[item.key];
  if (item.source === 'budget') return state.budget?.[item.key];
  if (item.source === 'social') return state.social_indicators?.[item.key];
  if (item.source === 'diplomacy' && item.key === 'multilateral_influence') return state.diplomacy?.multilateral_influence;
  if (item.source === 'diplomacy' && item.key === 'average_relation') {
    const relations = Object.values(state.diplomacy?.countries || {}).map((country) => Number(country.relation)).filter(Number.isFinite);
    return relations.length ? relations.reduce((sum, value) => sum + value, 0) / relations.length : undefined;
  }
  if (item.source === 'regional') {
    const values = Object.values(state.regional_metrics || {}).map((region) => Number(region[item.key])).filter(Number.isFinite);
    return values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : undefined;
  }
  return undefined;
}

export function indicatorTrend(item, state) {
  const history = state.indicator_history || [];
  if (history.length < 2) return null;
  const baselineIndex = Math.max(0, history.length - 13);
  const baseline = Number(readIndicator(item, history[baselineIndex]));
  const current = Number(readIndicator(item, state));
  if (!Number.isFinite(baseline) || !Number.isFinite(current)) return null;
  const delta = current - baseline;
  const unit = item.unit === '%' || item.unit.includes('%') ? ' p.p.' : ` ${item.unit}`;
  return `${history.length >= 13 ? '12m' : 'desde início'} ${delta > 0 ? '+' : ''}${formatIndicator(delta, item.key)}${unit}`;
}

