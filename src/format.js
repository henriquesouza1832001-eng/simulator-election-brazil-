// Nomes legíveis dos efeitos que as decisões produzem (usado por Competências, Histórico e outras telas).
export const EFFECT = { trust: 'confiança', reputation: 'reputação', mobilidade: 'mobilidade', seguranca: 'segurança', saude_atencao: 'saúde', educacao_fundamental: 'educação básica', educacao_medio: 'ensino médio', saneamento_basico: 'saneamento', agua_encanada: 'água', esgoto_inadequado: 'esgoto inadequado', adensamento: 'adensamento', logistica: 'custo logístico', homicidios: 'homicídios', mortalidade_infantil: 'mortalidade infantil', idhm_educacao: 'IDHM educação', gini: 'Gini', divida_pib: 'dívida', approval: 'aprovação', gdp_growth: 'PIB', inflation: 'inflação', unemployment: 'desemprego', institutional_trust: 'confiança institucional', integrity: 'integridade', governability: 'governabilidade', congress_support: 'base no Congresso', primary_balance: 'resultado primário', military_loyalty: 'lealdade militar' };

export function effectText(effects) {
  return Object.entries(effects || {}).map(([k, v]) => `${v > 0 ? '+' : ''}${v} ${EFFECT[k] || k}`).join(' · ');
}
