// Nomes legíveis dos efeitos que as decisões produzem (usado por Competências, Histórico e outras telas).
export const EFFECT = { trust: 'confiança', reputation: 'reputação', mobilidade: 'mobilidade', seguranca: 'segurança', saude_atencao: 'saúde', educacao_fundamental: 'educação básica', educacao_medio: 'ensino médio', saneamento_basico: 'saneamento', agua_encanada: 'água', esgoto_inadequado: 'esgoto inadequado', adensamento: 'adensamento', logistica: 'custo logístico', homicidios: 'homicídios', mortalidade_infantil: 'mortalidade infantil', idhm_educacao: 'IDHM educação', gini: 'Gini', divida_pib: 'dívida', approval: 'aprovação', gdp_growth: 'PIB', inflation: 'inflação', unemployment: 'desemprego', institutional_trust: 'confiança institucional', integrity: 'integridade', governability: 'governabilidade', congress_support: 'base no Congresso', primary_balance: 'resultado primário', military_loyalty: 'lealdade militar' };

export function effectText(effects) {
  return Object.entries(effects || {}).map(([k, v]) => {
    const n = Number(v);
    const sign = n > 0 ? '+' : n < 0 ? '−' : '';
    const abs = Math.abs(n).toLocaleString('pt-BR', { maximumFractionDigits: 2 });
    return `${sign}${abs} ${EFFECT[k] || k}`;
  }).join(' · ');
}

// Número no formato brasileiro (vírgula decimal e ponto de milhar); usar no lugar de toFixed em textos para o jogador.
export const br = (v, d = 1) => (Number.isFinite(Number(v)) ? Number(v).toLocaleString('pt-BR', { minimumFractionDigits: d, maximumFractionDigits: d }) : '—');
