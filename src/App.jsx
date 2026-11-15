import { useEffect, useMemo, useState } from 'react';
import { Amplify } from 'aws-amplify';
import { fetchAuthSession, getCurrentUser, signOut } from 'aws-amplify/auth';
import { cognitoUserPoolsTokenProvider } from 'aws-amplify/auth/cognito';
import { CookieStorage } from 'aws-amplify/utils';
import DiplomacyPanel from './DiplomacyPanel';
import FiscalPanel from './FiscalPanel';
import CampaignPanel from './CampaignPanel';
import CareerPanel from './CareerPanel';
import GovernmentAppointments from './GovernmentAppointments';
import InauguralAddress from './InauguralAddress';
import AuthPanel from './AuthPanel';
import AccountPanel from './AccountPanel';
import WelcomePanel from './WelcomePanel';
import GameSetupPanel from './GameSetupPanel';
import GameGuide from './GameGuide';
import { Nav, AdvanceMenu, MoreSheet } from './Shell';
import { TAB_HELP } from './guideContent';
import Brand from './Brand';
import InterpretationCorrection from './InterpretationCorrection';
import MeasureForecast from './MeasureForecast';
import IndicatorsPanel from './IndicatorsPanel';
import OverviewPanel from './OverviewPanel';
import ApuracaoPanel from './ApuracaoPanel';
import RedesPanel from './RedesPanel';
import Related from './Related';
import PartyPathPanel from './PartyPathPanel';
import PowersPanel from './PowersPanel';
import RegulatorsPanel from './RegulatorsPanel';
import NewsPanel from './NewsPanel';
import InterviewsPanel from './InterviewsPanel';
import CompaniesPanel from './CompaniesPanel';
import CongressProcessPanel from './CongressProcessPanel';
import MandateReview from './MandateReview';
import HistoryPanel from './HistoryPanel';
import './territory.css';
import TerritoryPanel from './TerritoryPanel';
import { StoryPanel, CampaignWeekPanel, CongressPanel, RankingPanel, CollectionPanel, DiaryPanel } from './MetaPanels';
import AgendaPanel from './AgendaPanel';
import AboutPanel from './AboutPanel';
import InvestmentsPanel from './InvestmentsPanel';
import './diplomacy.css';
import './ai-status.css';

const fmt = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 1 });
const difficultyLabels = { tranquilo: 'Tranquilo', normal: 'Normal', dificil: 'Difícil', complicado: 'Complicado', realismo_puro: 'Realismo Puro' };

const indicatorPrecision = {
  human_development_index: { minimumFractionDigits: 3, maximumFractionDigits: 3 },
  gini_index: { minimumFractionDigits: 3, maximumFractionDigits: 3 },
  country_risk: { minimumFractionDigits: 0, maximumFractionDigits: 0 },
};
const indicatorFormatters = new Map();

function formatIndicator(value, key) {
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
  return indicatorFormatters.get(formatKey).format(numericValue);
}

function Metric({ label, value, unit = '', tone = '', detail, indicatorKey }) {
  return <article className="metric"><div className="metric-label">{label}</div><div className={`metric-value ${tone}`}>{formatIndicator(value, indicatorKey)}<small>{unit}</small></div>{detail && <div className="metric-detail">{detail}</div>}</article>;
}

const indicatorOptions = [
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

const detailedIndicatorGroups = [
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
    { label: 'Aprovação', key: 'approval', unit: '%', source: 'metric', detail: 'Apoio nacional simulado ao governo.' },
    { label: 'Governabilidade', key: 'governability', unit: '/100', source: 'metric', detail: 'Capacidade de sustentar decisões e formar maioria.' },
    { label: 'Apoio no Congresso', key: 'congress_support', unit: '%', source: 'metric', detail: 'Apoio parlamentar agregado no cenário.' },
    { label: 'Confiança institucional', key: 'institutional_trust', unit: '/100', source: 'metric', detail: 'Confiança geral nas instituições.' },
    { label: 'Integridade', key: 'integrity', unit: '/100', source: 'metric', detail: 'Indicador simulado de transparência e exposição a escândalos.' },
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
    { label: 'Produtividade', key: 'productivity', unit: '/100', source: 'outcome', detail: 'Efeito simulado de investimentos produtivos.' },
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

const institutionLabels = {
  military_loyalty: 'Lealdade militar à Constituição',
  constitutional_order: 'Ordem constitucional',
  civilian_legitimacy: 'Legitimidade civil',
  institutional_resistance: 'Resistência institucional',
};

const OFFICE_STATUS_LABEL = { incumbent: 'em exercício', incumbent_caretaker: 'em transição após a eleição', reelected_transition: 'reeleito, em transição', former_president: 'ex-presidente', detained_after_failed_rupture: 'preso após ruptura fracassada' };

function readIndicator(item, state) {
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

function indicatorTrend(item, state) {
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

export default function App() {
  const [authConfig, setAuthConfig] = useState(null);
  const [aiStatus, setAiStatus] = useState('unknown');
  const [authUser, setAuthUser] = useState(null);
  const [authReady, setAuthReady] = useState(false);
  const [showAuthPanel, setShowAuthPanel] = useState(false);
  const [showAccountPanel, setShowAccountPanel] = useState(false);
  const [showGameMenu, setShowGameMenu] = useState(true);
  const [state, setState] = useState(null);
  const [campaignId, setCampaignId] = useState(() => window.localStorage.getItem('mandato.activeCampaign') || 'default');
  const pinKey = `qa.pins.${campaignId || 'default'}`;
  const readPins = () => { try { const v = JSON.parse(window.localStorage.getItem(pinKey) || '[]'); return Array.isArray(v) ? v.filter((x) => typeof x === 'string').slice(0, 8) : []; } catch { return []; } };
  const [pins, setPins] = useState(readPins);
  useEffect(() => { setPins(readPins()); }, [pinKey]);
  const togglePin = (tab) => setPins((cur) => { const next = cur.includes(tab) ? cur.filter((x) => x !== tab) : [...cur, tab].slice(-8); try { window.localStorage.setItem(pinKey, JSON.stringify(next)); } catch { /* sem armazenamento: vale só nesta sessão */ } return next; });
  const [measure, setMeasure] = useState('');
  const [preview, setPreview] = useState(null);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState('');
  const [rawTab, setActiveTab] = useState(null);
  const [gameGuideOpen, setGameGuideOpen] = useState(false);
  const [advanceOpen, setAdvanceOpen] = useState(false);
  const [advanceFabOpen, setAdvanceFabOpen] = useState(false);
  const [moreOpen, setMoreOpen] = useState(false);
  const [railOpen, setRailOpen] = useState(() => { try { const v = window.localStorage.getItem('quatroanos.rail'); return v ? v === 'open' : window.innerWidth >= 1280; } catch { return false; } });
  const toggleRail = () => setRailOpen((open) => { const next = !open; try { window.localStorage.setItem('quatroanos.rail', next ? 'open' : 'closed'); } catch { /* sem armazenamento */ } return next; });
  const [ruptureInfo, setRuptureInfo] = useState(null);
  const [budgetView, setBudgetView] = useState(null);
  const [budgetSection, setBudgetSection] = useState('Contas públicas');
  const [ministries, setMinistries] = useState([]);
  const [budgetSource, setBudgetSource] = useState('education');
  const [budgetTarget, setBudgetTarget] = useState('logistics');
  const [budgetAmount, setBudgetAmount] = useState('1');
  const [selectedContractorId, setSelectedContractorId] = useState('consorcio_horizonte');
  const [travelCutPct, setTravelCutPct] = useState(0);
  const [residenceCutPct, setResidenceCutPct] = useState(0);

  async function request(path, options) {
    const headers = { 'Content-Type': 'application/json', 'X-Mandato-Campaign': campaignId, ...(options?.headers || {}) };
    if (authConfig?.enabled && authUser && !authUser.isGuest) {
      const session = await fetchAuthSession();
      const token = session.tokens?.accessToken?.toString();
      if (!token) throw new Error('Sua sessão expirou. Entre novamente.');
      headers.Authorization = `Bearer ${token}`;
    }
    const response = await fetch(path, { ...options, headers, credentials: 'same-origin' });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Falha na solicitação');
    return data;
  }
  function acceptCampaignState(nextState) {
    if (nextState?.campaign_id) {
      setCampaignId(nextState.campaign_id);
      window.localStorage.setItem('mandato.activeCampaign', nextState.campaign_id);
    }
    setState(nextState);
  }
  async function refresh() { acceptCampaignState(await request('/api/game')); }
  async function startGuest() {
    setBusy(true); setNotice('');
    try {
      const response = await fetch('/api/guest/session', { method: 'POST', credentials: 'same-origin' });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Não foi possível iniciar a partida.');
      setAuthUser({ username: 'guest', isGuest: true });
    } catch (error) { setNotice(error.message || 'Não foi possível iniciar a partida.'); }
    finally { setBusy(false); }
  }
  useEffect(() => {
    let mounted = true;
    fetch('/api/health')
      .then((response) => response.ok ? response.json() : Promise.reject(new Error('Health check indisponível')))
      .then((health) => {
        if (mounted) setAiStatus(health.ai === 'gemini' ? 'gemini' : health.ai === 'local-fallback' ? 'local-fallback' : 'unknown');
      })
      .catch(() => { if (mounted) setAiStatus('unknown'); });
    return () => { mounted = false; };
  }, []);
  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const response = await fetch('/api/auth/config');
        const config = await response.json();
        if (!mounted) return;
        setAuthConfig(config);
        if (config.enabled) {
          Amplify.configure({ Auth: { Cognito: { userPoolId: config.user_pool_id, userPoolClientId: config.client_id, loginWith: { email: true,
            oauth: { domain: config.domain, scopes: ['openid', 'email'], redirectSignIn: [window.location.origin],
              redirectSignOut: [window.location.origin], responseType: 'code' } } } } });
          // Amplify.configure resets its token provider, so select secure cookies afterward.
          cognitoUserPoolsTokenProvider.setKeyValueStorage(new CookieStorage({ secure: true, sameSite: 'lax', path: '/', expires: 7 }));
          try { setAuthUser(await getCurrentUser()); } catch {
            const setupMode = new URLSearchParams(window.location.search).get('novo');
            if (['presidency', 'career', 'party'].includes(setupMode)) {
              const guestResponse = await fetch('/api/guest/session', { method: 'POST', credentials: 'same-origin' });
              setAuthUser(guestResponse.ok ? { username: 'guest', isGuest: true } : null);
            } else setAuthUser(null);
          }
        } else setAuthUser({ username: 'local' });
      } catch (e) { if (mounted) setNotice(`Não foi possível carregar a configuração de acesso: ${e.message}`); }
      finally { if (mounted) setAuthReady(true); }
    })();
    return () => { mounted = false; };
  }, []);
  useEffect(() => { if (authReady && authUser) refresh().catch((e) => setNotice(e.message)); }, [authReady, authUser]);
  useEffect(() => {
    if (rawTab === 'Orçamento') Promise.all([request('/api/budget'), request('/api/government/ministries')])
      .then(([budget, cabinet]) => { setBudgetView(budget); setMinistries(cabinet.items || []); setTravelCutPct(budget.operating?.travel_cut_pct ?? 0); setResidenceCutPct(budget.operating?.residence_cut_pct ?? 0); })
      .catch((e) => setNotice(e.message));
  }, [rawTab]);

  const currentDate = useMemo(() => state?.date ? new Date(`${state.date}T12:00:00`) : null, [state?.date]);
  const dateLabel = currentDate ? currentDate.toLocaleDateString('pt-BR', { day: 'numeric', month: 'long', year: 'numeric' }) : 'Carregando…';

  async function advance(days) {
    setBusy(true); setNotice('');
    try { const data = await request('/api/game/advance', { method: 'POST', body: JSON.stringify({ days }) }); setState(data.state); if (rawTab === 'Orçamento') setBudgetView(await request('/api/budget')); setNotice(data.message); }
    catch (e) { setNotice(e.message); } finally { setBusy(false); }
  }
  async function interpret() {
    if (!measure.trim()) return;
    setBusy(true); setNotice(''); setPreview(null);
    try { const data = await request('/api/measures/preview', { method: 'POST', body: JSON.stringify({ text: measure }) }); setPreview(data); setState((current) => current ? ({ ...current, learning: { ...current.learning, ...data.learning } }) : current); }
    catch (e) { setNotice(e.message); } finally { setBusy(false); }
  }
  async function signMeasure() {
    if (!preview) return;
    setBusy(true);
    try { const data = await request('/api/measures/apply', { method: 'POST', body: JSON.stringify({ text: measure, interpretation_id: preview.interpretation_id }) }); setState(data.state); setPreview(null); setMeasure(''); setNotice(data.status === 'pending_legislation' ? `Projeto enviado ao Congresso. A votação simulada está prevista para ${data.effects[0].decision_date}; efeitos dependem de aprovação.` : 'Ato registrado. O Executivo tem agenda limitada e os efeitos seguem as regras do simulador.'); }
    catch (e) { setNotice(e.message); } finally { setBusy(false); }
  }
  async function skipToElectionYear() {
    setBusy(true);
    try {
      const data = await request('/api/career/skip-to-election-year', { method: 'POST' });
      setState(data.state);
      setNotice(data.message);
    } catch (e) { setNotice(e.message); } finally { setBusy(false); }
  }

  async function toggleDashboardCard(key) {
    const current = state.dashboard_cards || indicatorOptions.slice(0, 6).map((item) => item.key);
    if (!current.includes(key) && current.length >= 6) {
      setNotice('O painel inicial aceita até seis cartões. Remova um para escolher outro.');
      return;
    }
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

  async function submitBudgetTransfer(source, target, amount) {
    setBusy(true);
    try {
      const data = await request('/api/budget/reallocate', { method: 'POST', body: JSON.stringify({ source, target, amount_bi: amount }) });
      setBudgetView(data.budget); setState(data.state); setNotice(`Remanejamento registrado. A entrega está prevista para ${data.project.completion_date}.`);
    } catch (e) { setNotice(e.message); } finally { setBusy(false); }
  }

  async function startPublicWork(workId) {
    setBusy(true);
    try {
      const data = await request('/api/budget/works/start', { method: 'POST', body: JSON.stringify({ work_id: workId, contractor_id: selectedContractorId }) });
      setBudgetView(data.budget); setState(data.state);
      setNotice(`Leilão simulado aberto para ${data.result.project.name}. Custo contratado: R$ ${data.result.project.contract_cost_bi.toFixed(2)} bi; parcela anual aproximada de R$ ${data.result.annual_cost_bi.toFixed(2)} bi.`);
    } catch (e) { setNotice(e.message); } finally { setBusy(false); }
  }

  async function resolvePublicWork(projectId, choice) {
    setBusy(true);
    try {
      const data = await request('/api/budget/works/resolve', { method: 'POST', body: JSON.stringify({ project_id: projectId, choice }) });
      setBudgetView(data.budget); setState(data.state); setNotice(data.result.message);
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

  if (!authReady || (authUser && !state)) return <main className="loading"><img className="brand-mark" src="/assets/brand/civiciclo-marca.png" alt="" aria-hidden="true"/><p>Preparando o gabinete…</p>{notice && <p>{notice}</p>}</main>;
  if (authConfig?.enabled && !authUser) return showAuthPanel
    ? <AuthPanel onAuthenticated={(user) => { setState(null); setShowGameMenu(true); setAuthUser(user); setShowAuthPanel(false); }} onCancel={() => setShowAuthPanel(false)} notice={notice} setNotice={setNotice} />
    : <WelcomePanel onGuest={startGuest} onSignIn={() => { setShowAuthPanel(true); setNotice(''); }} busy={busy} notice={notice} />;
  if (authConfig?.enabled && authUser?.isGuest && showAuthPanel) return <AuthPanel onAuthenticated={(user) => { setState(null); setShowGameMenu(true); setAuthUser(user); setShowAuthPanel(false); }} onCancel={() => setShowAuthPanel(false)} notice={notice} setNotice={setNotice} />;
  if (!state) return <main className="loading"><img className="brand-mark" src="/assets/brand/civiciclo-marca.png" alt="" aria-hidden="true"/><p>Preparando o gabinete…</p>{notice && <p>{notice}</p>}</main>;
  if (showGameMenu) return <><GameSetupPanel state={state} request={request} onState={acceptCampaignState} onContinue={() => { const url = new URL(window.location.href); url.searchParams.delete('novo'); window.history.replaceState(null, '', url); setShowGameMenu(false); }} busy={busy} setBusy={setBusy} authConfig={authConfig} authUser={authUser} onSignIn={() => { setShowAuthPanel(true); setNotice(''); }} onAccount={() => setShowAccountPanel(true)} />{showAccountPanel && <AccountPanel onClose={() => setShowAccountPanel(false)} />}</>;
  const m = state.metrics;
  const termMonth = Math.min(48, Math.max(1, state.month || 1));
  const monthsRemaining = Math.max(0, 48 - termMonth);
  const careerPhase = state.career_overview?.phase;
  const careerElectionPhase = ['campaign', 'runoff_campaign', 'runoff_observer'].includes(careerPhase);
  const careerCardLabel = careerPhase === 'campaign' ? 'ELEIÇÃO' : careerPhase === 'runoff_campaign' ? '2º TURNO' : careerPhase === 'runoff_observer' ? 'APURAÇÃO' : careerPhase === 'office' ? 'MANDATO' : careerPhase === 'transition' ? 'POSSE' : 'CARREIRA';
  const careerWaiting = careerPhase === 'pre_campaign' || careerPhase === 'opposition' || careerPhase === 'term_complete';
  const careerCardValue = careerElectionPhase ? state.career_overview?.days_until_election : careerPhase === 'transition' ? state.career_overview?.days_until_inauguration : careerPhase === 'office' ? state.career_overview?.term_years : careerWaiting ? state.career_overview?.days_until_campaign : '—';
  const careerCardSuffix = careerElectionPhase || careerPhase === 'transition' || careerWaiting ? ' dias' : careerPhase === 'office' ? ' anos' : '';
  const careerCardNote = careerWaiting ? (careerPhase === 'pre_campaign' ? 'para abrir a campanha — prepare-se antes' : 'para a próxima campanha') : careerPhase === 'campaign' ? 'dias até a votação' : careerPhase === 'runoff_campaign' || careerPhase === 'runoff_observer' ? 'dias até o segundo turno' : careerPhase === 'transition' ? 'dias até a posse' : careerPhase === 'office' ? `campanha abre em ${state.career_overview?.days_until_campaign} dias` : 'escolha o próximo passo';
  const careerCardProgress = careerElectionPhase ? Math.max(3, 100 - (state.career_overview?.days_until_election || 0) / (careerPhase === 'campaign' ? 90 : 28) * 100) : state.career_overview?.governing ? 100 * Math.min(1, ((state.career_overview?.term_years || 4) * 365 - (state.career_overview?.next_campaign_days || 0)) / ((state.career_overview?.term_years || 4) * 365)) : careerPhase === 'transition' ? 85 : 0;
  const operatingLines = budgetView?.operating?.lines || {};
  const proposedOperatingSavings = (Number(operatingLines.official_travel?.annual_cost_bi || 0) * Number(travelCutPct) / 100)
    + (Number(operatingLines.official_residence?.annual_cost_bi || 0) * Number(residenceCutPct) / 100);
  const currentOperatingSavings = Number(budgetView?.operating?.annual_savings_bi || 0);
  const fiscalReferenceGdp = Number(budgetView?.operating?.nominal_gdp_bi || 15000);
  const proposedPrimaryBalance = Number(m.primary_balance) + ((proposedOperatingSavings - currentOperatingSavings) / fiscalReferenceGdp * 100);
  const careerMode = Boolean(state.career_overview?.mode);
  const careerOverview = state.career_overview;
  const careerOffice = careerOverview?.office;
  const partyMode = state.mode === 'party_path' && Boolean(state.party_path?.active);
  const playerCharacter = state.player_character || state.career_overview?.character || null;
  const aiStatusLabel = aiStatus === 'gemini' ? 'GEMINI CONFIGURADO'
    : aiStatus === 'local-fallback' ? 'MOTOR LOCAL'
      : 'STATUS DA IA INDISPONÍVEL';
  const aiStatusTitle = aiStatus === 'gemini'
    ? 'A chave Gemini está configurada no servidor. A interpretação pode recorrer ao motor local se o serviço falhar; custos e efeitos seguem as regras Python.'
    : aiStatus === 'local-fallback'
      ? 'Gemini ainda não está configurado. A prévia usa regras locais; custos e efeitos seguem as regras Python.'
      : 'Não foi possível consultar o estado do serviço. O jogo continua disponível e usa o fallback local quando necessário.';
  const presidentCareer = !careerMode || (careerOffice === 'presidente' && careerOverview?.governing);
  const localCareer = careerMode && careerOffice !== 'presidente';
  const careerCards = localCareer ? [
    { label: 'Intenção de voto', value: careerOverview.poll_support, unit: '%', detail: 'Pesquisa simulada no seu território', tone: 'green' },
    { label: 'Apoio local', value: careerOverview.local_support, unit: '%', detail: careerOverview.campaign_territory },
    { label: 'Reputação', value: careerOverview.reputation, unit: '/100', detail: 'Construída na militância e no mandato' },
    { label: 'Fundo de campanha', value: careerOverview.campaign_fund_mi, unit: ' mi', detail: 'Recurso fictício disponível', tone: 'amber' },
    { label: 'Embalo', value: careerOverview.momentum, unit: '', detail: 'Tendência recente da campanha' },
    { label: 'Compromissos pendentes', value: careerOverview.pending_campaign_promises, unit: '', detail: 'Promessas que podem ser cobradas' },
  ] : [];
  const careerNextStep = !localCareer ? null : careerPhase === 'pre_campaign'
    ? { label: 'PRÉ-CAMPANHA', title: 'Monte sua base antes de a campanha abrir', text: `Faltam ${careerOverview.days_until_campaign} dias para a campanha e ${careerOverview.days_until_election} para a votação. Use a preparação para ganhar organização e reconhecimento.` }
    : careerPhase === 'campaign'
      ? { label: 'CAMPANHA', title: careerOverview.can_act ? 'Hoje há tempo para uma atividade de campanha' : `Próxima atividade em ${careerOverview.days_until_action} dia(s)`, text: `Votação em ${careerOverview.days_until_election} dias. Debate, comícios e visitas movem a intenção de voto; o fundo é limitado.` }
      : careerPhase === 'transition'
        ? { label: 'POSSE', title: 'Resultado apurado', text: `A posse acontece em ${careerOverview.days_until_inauguration} dias. Veja na aba Carreira como foi a votação.` }
        : careerPhase === 'office'
          ? { label: 'MANDATO', title: `Exercendo o cargo de ${careerOverview.office_label}`, text: `A próxima campanha abre em ${careerOverview.days_until_campaign} dias. Use a aba do cargo para decidir e acompanhe os acontecimentos.` }
          : { label: 'DEPOIS DA ELEIÇÃO', title: 'A carreira continua', text: 'Reconstrua prestígio na Trajetória ou prepare uma nova candidatura.' };
  const officeTabLabel = ({
    vereador: 'Câmara municipal', prefeito: 'Prefeitura', deputado_estadual: 'Assembleia estadual',
    governador: 'Governo estadual', deputado_federal: 'Câmara dos Deputados', senador: 'Senado',
    presidente: 'Presidência',
  })[careerOffice] || 'Mandato';
  const baseGroups = partyMode ? [
    { label: 'Militância', items: careerMode ? ['Trajetória', 'Carreira', 'Competências', 'Indicadores', 'Acontecimentos'] : ['Trajetória', 'Competências', 'Indicadores', 'Acontecimentos'] },
    { label: 'Sobre', items: ['O jogo', 'Termos', 'Créditos'] },
  ] : [
    { label: 'Painel', items: ['Visão geral', 'Indicadores', 'Histórico'] },
    { label: careerMode && careerOverview?.governing ? officeTabLabel : 'Governo', items: careerMode ? (careerOverview?.governing ? ['Mandato', 'Competências', ...(['presidente', 'governador'].includes(careerOffice) ? ['Empresas'] : []), ...(['presidente', 'governador', 'prefeito'].includes(careerOffice) ? ['Obras e mapa'] : [])] : []) : ['Medidas', 'Competências', 'Empresas', 'Orçamento', 'Obras e mapa', 'Crises'] },
    { label: 'Política', items: careerMode ? ['Carreira', 'Apuração', 'Instituições', 'Reguladores', ...(careerOffice === 'presidente' && careerOverview?.governing ? ['Tramitação', 'Nomeações'] : []), ...(['vereador', 'deputado_estadual', 'deputado_federal', 'senador', 'governador', 'prefeito'].includes(careerOffice) && careerOverview?.governing ? ['Tramitação'] : [])] : ['Carreira', 'Eleição', 'Apuração', 'Semana', 'Congresso', 'Tramitação', 'Instituições', 'Reguladores', 'Nomeações'] },
    { label: 'Mundo', items: presidentCareer ? ['Diplomacia'] : [] },
    { label: 'Agenda', items: ['Agenda', 'Imprensa', 'Redes', 'Entrevistas', 'Acontecimentos'] },
    { label: 'Sobre', items: ['O jogo', 'Termos', 'Créditos'] },
  ].filter((group) => group.items.length);
  const tabGroups = [...baseGroups, { label: 'Perfil', hidden: true, items: ['Placar', 'Carimbos', 'Diário'] }];
  const availableTabs = tabGroups.flatMap((group) => group.items);
  const activeTab = rawTab && availableTabs.includes(rawTab) ? rawTab : baseGroups[0].items[0];
  const selectedTabGroup = tabGroups.find((group) => group.items.includes(activeTab)) || baseGroups[0];
  const dashboardTab = ['Visão geral', 'Medidas'].includes(activeTab);
  const pageGuidance = {
    'Visão geral': localCareer ? ['Sua carreira em movimento.', 'Veja onde você está no calendário e escolha o próximo passo.'] : (monthsRemaining === 0 && termMonth >= 48 ? ['O mandato terminou.', 'Veja o balanço final abaixo e decida se continua jogando ou abre uma nova partida.'] : ['O país, em movimento.', 'Veja o que pede atenção hoje e escolha o próximo passo.']),
    'Indicadores': ['Como está o país?', 'Abra os grupos para acompanhar os dados sem sobrecarregar o painel inicial.'],
    'Medidas': ['Prepare uma decisão.', 'Descreva a proposta; revise a interpretação e os efeitos antes de aplicar.'],
    'Orçamento': ['Onde usar os recursos?', 'Escolha entre contas públicas, investimentos e obras. Cada área tem sua própria tela.'],
    'Diplomacia': ['Relações com o mundo.', 'Planeje visitas e compromissos; deslocamentos consomem dias de calendário.'],
    'Crises': ['Responder também é governar.', 'Veja o impacto em curso e compare as opções disponíveis.'],
    'Eleição': ['A disputa também consome tempo.', 'Planeje uma atividade, leia os efeitos e mantenha o governo em funcionamento.'],
    'Carreira': ['Sua carreira, passo a passo.', 'Escolha um cargo, dispute a eleição e veja as consequências no território e no mandato.'],
    'Nomeações': ['Quem ocupa os cargos.', 'Escolha ministros e acompanhe indicações ao STF e decisões do Senado.'],
    'Instituições': ['Regras e estabilidade.', 'Acompanhe as instituições e os limites do cargo.'],
    'Agenda': ['O que vem pela frente?', 'Compromissos e acontecimentos seguem a data da partida.'],
  }[activeTab] || ['Governo em exercício.', 'Acompanhe o calendário e as consequências das decisões.'];

  const selectedCards = (state.dashboard_cards || indicatorOptions.slice(0, 6).map((item) => item.key)).slice(0, 6);
  const upcomingEvents = (state.events || []).slice(0, 3);
  const nextCrisis = state.active_crises?.[0];
  const nextEvent = state.events?.[0];
  const mainTab = careerMode ? 'Carreira' : 'Medidas';
  const mainLabel = careerMode ? 'Acompanhar carreira' : 'Preparar uma decisão';
  const overviewNext = localCareer
    ? { label: careerNextStep.label, title: careerNextStep.title, text: careerNextStep.text, urgent: false, actions: [{ label: mainLabel, tab: mainTab, primary: true }, { label: 'Ver acontecimentos', tab: 'Acontecimentos' }] }
    : nextCrisis ? { label: 'Crise em andamento', title: nextCrisis.title, text: nextCrisis.description, urgent: true, actions: [{ label: careerMode ? 'Ver situação da carreira' : 'Ver opções de resposta', tab: careerMode ? 'Carreira' : 'Crises', primary: true }, { label: 'Abrir agenda', tab: 'Agenda' }] }
      : nextEvent ? { label: nextEvent.days_until === 0 ? 'Acontece hoje' : `Próximo evento · em ${nextEvent.days_until} dias`, title: nextEvent.title, text: nextEvent.description, urgent: false, actions: [{ label: mainLabel, tab: mainTab, primary: true }, { label: 'Abrir agenda', tab: 'Agenda' }] }
        : { label: 'Sem pendências', title: 'Nada urgente agora', text: 'Use o tempo para preparar uma decisão ou avance o calendário.', urgent: false, actions: [{ label: mainLabel, tab: mainTab, primary: true }] };
  const monthsToElection = careerOverview?.days_until_campaign;
  const overviewProps = {
    request, state, go: setActiveTab, pins, onUnpin: togglePin,
    title: activeTab === 'Visão geral' ? pageGuidance[0] : 'Visão geral', lead: activeTab === 'Visão geral' ? pageGuidance[1] : undefined,
    term: partyMode ? null : { label: careerMode ? careerCardLabel : 'Mandato', value: careerMode ? careerCardValue : termMonth, suffix: careerMode ? careerCardSuffix : ' / 48', progress: careerMode ? careerCardProgress : termMonth / 48 * 100, note: careerMode ? careerCardNote : `${monthsRemaining} meses restantes` },
    stats: localCareer
      ? { title: `Sua situação · ${careerOverview.office_label}`, items: careerCards.map((c) => ({ label: c.label, value: formatIndicator(c.value), unit: c.unit?.trim(), note: c.detail })) }
      : { title: 'Seus números', items: selectedCards.map((key) => { const option = indicatorOptions.find((item) => item.key === key); return option ? { label: option.label, value: formatIndicator(readIndicator(option, state), key), unit: option.unit?.trim(), note: option.detail } : null; }).filter(Boolean) },
    customize: localCareer ? null : { options: indicatorOptions, selected: selectedCards, toggle: toggleDashboardCard },
    next: overviewNext, upcoming: upcomingEvents, last: state.recent_actions?.[0] || null,
    calendar: localCareer ? [['Campanha abre', careerOverview.campaign_start_date], ['Votação', careerOverview.election_date], ['Posse', careerOverview.inauguration_date]] : null,
    governing: localCareer ? null : { governability: m.governability, congress_support: m.congress_support, institutional_trust: m.institutional_trust },
    skip: localCareer && careerPhase === 'pre_campaign' && monthsToElection > 120 && String(careerOverview?.election_date || '').slice(0, 4) !== String(state.date || '').slice(0, 4) ? { text: `A campanha abre em ${monthsToElection} dias. Se preferir não esperar, o jogo pode avançar sozinho até o ano da eleição (os meses passam normalmente, com economia e acontecimentos).`, label: 'Pular para o ano da eleição', busy, onSkip: skipToElectionYear } : null,
    showReview: !localCareer && !partyMode,
    showBalance: !localCareer && !partyMode && monthsRemaining === 0 && termMonth >= 48,
  };
  const railGroups = tabGroups.filter((group) => !group.hidden && !['Mundo', 'Sobre'].includes(group.label))
    .map((group) => ({ ...group, rail: ['Painel', 'Política', 'Agenda', 'Militância'].includes(group.label) ? group.label : 'Governo', icon: ['Painel', 'Política', 'Agenda'].includes(group.label) ? group.label : group.label === 'Militância' ? 'Política' : 'Governo' }));
  const moreEntries = [
    ...(tabGroups.find((group) => group.label === 'Mundo')?.items || []).map((tab) => ({ label: tab, icon: 'Mundo', hint: TAB_HELP[tab], go: () => setActiveTab(tab) })),
    { label: 'Guia', hint: 'O que cada aba faz e o glossário', go: () => setGameGuideOpen(true) },
    ...(tabGroups.find((group) => group.label === 'Sobre')?.items || []).map((tab) => ({ label: tab, icon: 'Sobre', hint: TAB_HELP[tab], go: () => setActiveTab(tab) })),
    { label: 'Partidas', hint: 'Trocar ou começar uma partida', go: () => setShowGameMenu(true) },
    ...(authConfig?.enabled ? (authUser?.isGuest
      ? [{ label: 'Entrar / criar conta', icon: 'Perfil', go: () => { setShowAuthPanel(true); setNotice(''); } }]
      : [{ label: 'Conta', icon: 'Perfil', go: () => setShowAccountPanel(true) }, { label: 'Sair', icon: 'Perfil', go: async () => { await signOut(); setAuthUser(null); setState(null); setShowGameMenu(true); } }]) : []),
  ];
  return <div className={`app-shell ${railOpen ? 'rail-open' : ''}`}>
    <header className="ds-top"><Brand /><div className="ds-date"><span>{dateLabel}</span><small>{careerMode ? `${state.career_overview.office_label} · ${state.career_overview.campaign_territory || state.career_overview.state_name} · ${({ pre_campaign: 'pré-campanha', campaign: 'campanha', transition: 'transição para a posse', office: 'no mandato', opposition: 'fora do cargo', term_complete: 'mandato concluído', runoff_campaign: 'segundo turno', runoff_observer: 'apuração do segundo turno' })[state.career_overview.phase] || state.career_overview.phase.replaceAll('_', ' ')}` : (partyMode ? `TRAJETÓRIA PARTIDÁRIA · ${String(state.party_path.stage).replaceAll('_', ' ').toUpperCase()}` : `MÊS ${termMonth} DE 48 · DIA ${state.day_of_mandate} DE 1461 · ${OFFICE_STATUS_LABEL[state.office_status || 'incumbent'] || String(state.office_status).replaceAll('_', ' ')}`)}</small></div><div className="ds-top-actions">{authConfig?.enabled && (authUser?.isGuest ? <button className="ds-btn" onClick={() => { setShowAuthPanel(true); setNotice(""); }}>Entrar / criar conta</button> : <><button className="ds-btn" onClick={() => setShowAccountPanel(true)}>Conta</button><button className="ds-btn" onClick={async () => { await signOut(); setAuthUser(null); setState(null); setShowGameMenu(true); }}>Sair</button></>)}<button type="button" className="ds-btn" onClick={() => setGameGuideOpen((open) => !open)} aria-pressed={gameGuideOpen}>Guia</button><button type="button" className="ds-btn" onClick={() => setShowGameMenu(true)}>Partidas</button><AdvanceMenu open={advanceOpen} setOpen={setAdvanceOpen} busy={busy} advance={advance} /></div></header>
    <Nav expanded={railOpen} onToggle={toggleRail} items={railGroups} current={selectedTabGroup.label} moreActive={['Mundo', 'Sobre', 'Perfil'].includes(selectedTabGroup.label)} onGo={(group) => { if (!group.items.includes(activeTab)) setActiveTab(group.items[0]); }} onMore={() => setMoreOpen(true)} pins={pins} activePin={activeTab} onPin={setActiveTab} />
    <MoreSheet open={moreOpen} onClose={() => setMoreOpen(false)} entries={moreEntries} />
    <AdvanceMenu floating open={advanceFabOpen} setOpen={setAdvanceFabOpen} busy={busy} advance={advance} />
    {(selectedTabGroup.items.length > 1 || selectedTabGroup.hidden) && <nav className="ds-tabs" aria-label={`Seções de ${selectedTabGroup.label}`}>{selectedTabGroup.hidden && <button type="button" className="ds-tab back" onClick={() => setActiveTab(baseGroups[0].items[0])}>← Voltar ao jogo</button>}{selectedTabGroup.items.map((tab) => <button key={tab} className="ds-tab" aria-selected={activeTab === tab} onClick={() => setActiveTab(tab)}>{tab}</button>)}<button type="button" className="ds-tab-pin" aria-pressed={pins.includes(activeTab)} title={pins.includes(activeTab) ? 'Tirar do menu lateral' : 'Fixar no menu lateral'} onClick={() => togglePin(activeTab)}>{pins.includes(activeTab) ? '★ Fixada' : '☆ Fixar'}</button></nav>}

    <main className="content">



      {activeTab === 'Visão geral' && <OverviewPanel {...overviewProps} />}

      {dashboardTab && <>

      {activeTab === 'Medidas' && <div className="main-grid">
        <section className="panel measure-panel">
          <div className="panel-heading"><div><div className="eyebrow">CENTRO DE DECISÕES</div><h2>Escreva uma medida</h2><p>Descreva a ideia com suas palavras. O motor calcula os efeitos antes de você confirmar.</p></div><span className={`ai-chip ai-chip--${aiStatus}`} title={aiStatusTitle}><i/> {aiStatusLabel}</span></div>
          <label className="field-label" htmlFor="measure">PROPOSTA DO GOVERNO</label>
          <div className="cadence-summary"><span>Agenda executiva: uma decisão administrativa a cada 7 dias ({state.action_limits?.executive_days ?? 0} dia(s) de espera).</span><span>Pauta legislativa: um projeto a cada {state.legislative_calendar?.cooldown_days || 60} dias ({state.action_limits?.legislative_days ?? 0} dia(s) de espera); {state.action_limits?.pending_bills ?? 0} em tramitação · {state.action_limits?.laws_enacted ?? 0} leis aprovadas.</span></div>
          {state.legislative_calendar?.pending_bills?.map((bill) => <div className="pending-bill" key={bill.id}><span>TRAMITANDO · VOTAÇÃO {bill.decision_date}</span><b>{bill.title}</b><small>{bill.instrument} · aprovação por regra parlamentar do simulador</small></div>)}
          <textarea id="measure" value={measure} onChange={(e) => setMeasure(e.target.value)} placeholder="Ex.: revisar contratos renováveis, publicar os preços de referência e direcionar a economia comprovada à redução da dívida…" maxLength={3000}/>
          <div className="composer-footer"><span>{measure.length} / 3000 caracteres <span className="muted">· sem compromisso até simular</span></span><button className="primary-button" disabled={busy || !measure.trim()} onClick={interpret}>{busy ? 'Analisando…' : 'Interpretar e simular'}<b>→</b></button></div>
          {notice && <div className="notice">{notice}</div>}
          {preview && <div className="preview-card"><div className="preview-top"><div><div className="eyebrow">PRÉVIA · NÃO APLICADA</div><h3>{preview.interpretation.title}</h3></div><div className="preview-provenance"><span>{preview.interpretation.source === 'gemini' ? 'Gemini' : 'Leitura local'}</span><span className="confidence">{Math.round(preview.interpretation.confidence * 100)}% confiança</span></div></div><p>{preview.interpretation.summary}</p><div className="simulation-timing">{preview.timing}<br/><b>Custo fiscal usado no motor: R$ {Number(preview.interpretation.fiscal_cost_bi || 0).toLocaleString('pt-BR', { maximumFractionDigits: 3 })} bi.</b> {preview.interpretation.fiscal_cost_note}</div><div className="preview-tags"><span>{preview.interpretation.instrument}</span><span>{preview.interpretation.policy_area}</span><span>{preview.interpretation.duration_days ? `${preview.interpretation.duration_days} dias` : 'efeito permanente'}</span></div><MeasureForecast forecast={preview.forecast} /><div className="preview-bottom"><span>{preview.interpretation.constraints?.length ? preview.interpretation.constraints.join(' · ') : 'Regras e efeitos estimados pelo motor do jogo'}</span><button className="primary-button" onClick={signMeasure} disabled={busy}>Aplicar medida <b>→</b></button></div><InterpretationCorrection preview={preview} measure={measure} request={request} onSaved={(data) => setState((current) => current ? ({ ...current, learning: { ...current.learning, corrections_saved: data.corrections_saved } }) : current)} onNotice={setNotice} busy={busy} setBusy={setBusy} /></div>}
        </section>

        <aside className="side-column"><section className="panel compact-panel"><div className="panel-heading small"><div><div className="eyebrow">ESTABILIDADE</div><h2>Capacidade de governar</h2></div><strong className="score">{formatIndicator(m.governability, 'governability')}<small>/100</small></strong></div><div className="bar"><i style={{ width: `${m.governability}%` }}/></div><div className="mini-stats"><div><span>Base no Congresso</span><b>{formatIndicator(m.congress_support, 'congress_support')}%</b></div><div><span>Confiança institucional</span><b>{formatIndicator(m.institutional_trust, 'institutional_trust')}/100</b></div></div></section>
        <section className="panel compact-panel"><div className="panel-heading small"><div><div className="eyebrow">AGENDA PRÓXIMA</div><h2>O que vem pela frente</h2></div><button className="icon-button" onClick={() => setActiveTab('Agenda')}>↗</button></div>{state.events?.length ? state.events.slice(0, 3).map((event) => <div className="event" key={event.id}><span className="event-date">{event.days_until === 0 ? 'HOJE' : `EM ${event.days_until} DIAS`}</span><div><b>{event.title}</b><small>{event.description}</small></div></div>) : <p className="empty-state">Agenda tranquila por enquanto. Avance alguns dias para acompanhar o mandato.</p>}</section>
        <section className="panel compact-panel"><div className="panel-heading small"><div><div className="eyebrow">REGISTRO</div><h2>Últimas decisões</h2></div></div>{state.recent_actions?.length ? state.recent_actions.slice(0, 3).map((action) => <div className="decision" key={action.id}><span>✓</span><div><b>{action.title}</b><small>{new Date(`${action.date}T12:00:00`).toLocaleDateString('pt-BR')} · {action.kind}</small></div></div>) : <p className="empty-state">Nenhuma medida assinada ainda.</p>}</section></aside>
      </div>}</>}

      {activeTab === 'Agenda' && <AgendaPanel state={state} />}

      {activeTab === 'Diplomacia' && <DiplomacyPanel date={state.date} authEnabled={authConfig?.enabled} onState={setState} onNotice={setNotice} busy={busy} setBusy={setBusy} />}

      {activeTab === 'Indicadores' && <IndicatorsPanel request={request} state={state} onAct={() => setActiveTab(careerMode ? (careerOverview?.governing ? 'Mandato' : 'Carreira') : 'Medidas')} actLabel={careerMode ? (careerOverview?.governing ? 'Ir para o mandato' : 'Ver minha carreira') : 'Preparar uma medida'} />}

      {activeTab === 'Obras e mapa' && <TerritoryPanel request={request} state={state} onState={setState} onNotice={setNotice} />}

      {activeTab === 'Histórico' && <HistoryPanel request={request} state={state} />}

      {activeTab === 'Tramitação' && <CongressProcessPanel request={request} state={state} onState={setState} onNotice={setNotice} />}

      {activeTab === 'Empresas' && <CompaniesPanel request={request} state={state} onState={setState} onNotice={setNotice} />}

      {activeTab === 'Entrevistas' && <InterviewsPanel request={request} state={state} onState={setState} onNotice={setNotice} />}

      {activeTab === 'Apuração' && <ApuracaoPanel request={request} state={state} />}
      {activeTab === 'Redes' && <RedesPanel request={request} state={state} go={setActiveTab} />}
      {activeTab === 'Imprensa' && <NewsPanel request={request} state={state} onState={setState} onNotice={setNotice} />}

      {activeTab === 'Reguladores' && <RegulatorsPanel request={request} state={state} federalExecutive={!careerMode || careerOffice === 'presidente'} />}

      {activeTab === 'Competências' && <PowersPanel request={request} state={state} onState={setState} onNotice={setNotice} />}

        {activeTab === 'Trajetória' && partyMode && <PartyPathPanel state={state} request={request} onNotice={setNotice} onLaunched={(next) => { acceptCampaignState(next); setActiveTab('Carreira'); }} />}
        {activeTab === 'Acontecimentos' && <StoryPanel state={state} request={request} onNotice={setNotice} />}
        {activeTab === 'Semana' &&<CampaignWeekPanel request={request} onNotice={setNotice} />}
        {activeTab === 'Congresso' &&<CongressPanel state={state} request={request} />}
        {activeTab === 'Placar' && <RankingPanel state={state} request={request} onNotice={setNotice} />}
        {activeTab === 'Carimbos' && <CollectionPanel state={state} request={request} />}
        {activeTab === 'Diário' && <DiaryPanel request={request} />}
        {['O jogo', 'Termos', 'Créditos'].includes(activeTab) && <AboutPanel section={activeTab} />}
      {activeTab === 'Orçamento' && <section className="panel agenda-page">
        <div className="eyebrow">EXECUTIVO FEDERAL · DESPESAS E INVESTIMENTOS</div>
        <h2>Orçamento do governo</h2>
        <p className="page-description">Viagens oficiais e manutenção das residências entram nas despesas do governo. Reduza essas rubricas para melhorar o resultado primário; os valores são estimativas fictícias do simulador.</p>
        {budgetView ? <>
          <div className="budget-subnav" role="tablist" aria-label="Seções do orçamento">{['Contas públicas', 'Investimentos', 'Obras'].map((section) => <button key={section} role="tab" aria-selected={budgetSection === section} className={budgetSection === section ? 'active' : ''} onClick={() => setBudgetSection(section)}>{section}</button>)}</div>
          {notice && <div className="notice">{notice}</div>}
          {budgetSection === 'Contas públicas' && <>
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
                  <div className="ds-seg" role="group" aria-label={`Reduzir ${line.label}`}>{[0, 10, 25, 50, 75].filter((value) => value <= max).map((value) => <button type="button" key={value} aria-pressed={cut === value} onClick={() => isTravel ? setTravelCutPct(value) : setResidenceCutPct(value)}>{value === 0 ? 'Manter' : `−${value}%`}</button>)}</div>
                </article>;
              })}
            </div>
            <div className="operating-impact"><span>Resultado primário atual <b>{Number(m.primary_balance).toFixed(3)}% do PIB</b></span><span>Após aplicar <b>{Number(proposedPrimaryBalance).toFixed(3)}% do PIB</b></span><small>Estimativa proporcional ao PIB nominal de referência do simulador (R$ {(fiscalReferenceGdp / 1000).toFixed(0)} tri). A trajetória da dívida acumula o efeito ao longo dos dias.</small></div>
            <div className="operating-footer"><small>{budgetView.operating.days_until_review ? `Próxima revisão em ${budgetView.operating.days_until_review} dia(s).` : 'Ajuste disponível agora.'} As rubricas fazem parte da despesa primária anual. Os limites evitam cortar integralmente deslocamentos institucionais ou manutenção essencial.</small><button className="primary-button" disabled={busy || budgetView.operating.days_until_review > 0 || (Number(budgetView.operating.travel_cut_pct) === Number(travelCutPct) && Number(budgetView.operating.residence_cut_pct) === Number(residenceCutPct))} onClick={submitOperatingBudget}>Aplicar cortes</button></div>
          </div>
          </>}
          {budgetSection === 'Investimentos' && <>
          <InvestmentsPanel view={budgetView} busy={busy} onTransfer={submitBudgetTransfer} />
          <details className="ministry-roster"><summary>Ver pastas oficiais disponíveis ({ministries.length})</summary><div>{ministries.map((ministry) => <span key={ministry.name}>{ministry.name}</span>)}</div><small>Catálogo baseado no SIORG; estas pastas são fixas no jogo. A carteira de investimentos não cria ministérios.</small></details>
          </>}
          {budgetSection === 'Obras' && <section className="works-section">
            <div className="operating-heading"><div><span className="eyebrow">CARTEIRA NACIONAL · OBRAS SIMULADAS</span><h3>Rodovias, ferrovias, hidrovias e serviços</h3><p>O índice de obras atualiza a projeção de custo dos contratos ativos; a proposta de cada leilão mostra o valor inicial e a parcela anual.</p></div><strong className="operating-saving">R$ {budgetView.works.annual_available_bi.toFixed(2)} bi<small>livres por ano em Transportes e logística</small></strong></div>
            <div className="works-index"><span>Índice de custo de obras <b>{budgetView.works.price_index.toFixed(3)}×</b></span><span>Carteira anual <b>R$ {budgetView.works.annual_allocation_bi.toFixed(1)} bi</b></span><span>Comprometido <b>R$ {budgetView.works.annual_committed_bi.toFixed(2)} bi/ano</b></span>{budgetView.works.annual_overrun_bi > 0 && <span className="red">Pressão sobre o orçamento <b>+R$ {budgetView.works.annual_overrun_bi.toFixed(2)} bi/ano</b></span>}<small>{budgetView.works.price_note}</small></div>
            <label className="contractor-picker">Empresa do leilão<select value={selectedContractorId} onChange={(event) => setSelectedContractorId(event.target.value)}>{budgetView.works.contractors.map((company) => <option key={company.id} value={company.id}>{company.name} · custo {company.price_factor.toFixed(2)}× · risco financeiro {Math.round(company.financial_risk * 100)}%</option>)}</select></label>
            <div className="works-catalog">{budgetView.works.options.map((work) => { const company = budgetView.works.contractors.find((item) => item.id === selectedContractorId) || budgetView.works.contractors[0]; const total = work.quoted_cost_bi * company.price_factor; const annual = total * 365 / work.duration_days; const scale = Math.min(2, total / 20); const canFund = annual <= budgetView.works.annual_available_bi + 1e-9; return <article className="work-card" key={work.id}><div className="work-kind">{work.kind}<span>{work.regions.map((region) => region.replaceAll('_', ' ')).join(' · ')}</span></div><h4>{work.name}</h4><p>{work.description}</p><small className="work-route">{work.route}</small><div className="work-costs"><span>Custo no leilão<strong>R$ {total.toFixed(2)} bi</strong></span><span>Parcela anual aprox.<strong>R$ {annual.toFixed(2)} bi/ano</strong></span><span>Prazo base<strong>{Math.ceil(work.duration_days / 365)} anos</strong></span><span>Risco técnico<strong>{Math.round(work.risk * 100)}%</strong></span></div><small className="contractor-profile">{company.profile} Risco financeiro: {Math.round(company.financial_risk * 100)}%; risco de integridade: {Math.round(company.integrity_risk * 100)}%.</small><div className="work-forecast"><b>Se contratar agora</b><span>Reserva R$ {annual.toFixed(2)} bi/ano da carteira de Transportes.</span><span>Entrega estimada: {new Date(`${work.expected_completion}T12:00:00`).toLocaleDateString('pt-BR')}.</span><span>Na entrega: infraestrutura regional +{(work.effects.infrastructure * scale).toFixed(1)}, atividade +{(work.effects.economic_activity * scale).toFixed(1)} e PIB +{(.08 * scale).toFixed(2)} p.p. estimados.</span><span>Custos podem subir; incidentes podem suspender o cronograma e abrir uma decisão.</span></div><button className="secondary-button" disabled={busy || budgetView.works.days_until_next_award > 0 || !canFund} onClick={() => startPublicWork(work.id)}>{budgetView.works.days_until_next_award > 0 ? `Novo leilão em ${budgetView.works.days_until_next_award} dias` : !canFund ? 'Remaneje verba para Transportes' : 'Abrir leilão simulado'}</button></article>; })}</div>
            <h4 className="subheading">Obras em execução e histórico</h4>
            {budgetView.works.projects.length ? <div className="works-projects">{budgetView.works.projects.map((project) => <article className="work-running" key={project.id}><div className="work-running-head"><div><span className="work-kind">{project.kind} · {project.route}</span><h4>{project.name}</h4></div><b className={`work-status ${project.status}`}>{project.status === 'active' ? 'EM EXECUÇÃO' : project.status === 'needs_decision' ? 'AGUARDA DECISÃO' : project.status === 'delivered' ? 'ENTREGUE' : 'CANCELADA'}</b></div><p>{project.description}</p><div className="work-progress"><i style={{ width: `${Math.min(100, project.progress * 100)}%` }}/></div><div className="work-running-meta"><span>{Math.round(project.progress * 100)}% concluída</span><span>Contratada: {project.contractor}</span><span>Estimativa atual: R$ {project.current_cost_bi.toFixed(2)} bi</span><span>Previsão: {project.target_completion}</span></div>{project.issue && <div className="work-issue"><b>{project.issue.title}</b><p>{project.issue.description}</p><div>{project.issue.options.map((option) => <button className="secondary-button" key={option.id} disabled={busy} onClick={() => resolvePublicWork(project.id, option.id)}>{option.label}<small>{option.detail}</small></button>)}</div></div>}{project.resolved_issues?.length > 0 && <small className="work-history">Ocorrências resolvidas: {project.resolved_issues.length} · registradas no histórico simulado.</small>}</article>)}</div> : <div className="empty-state">Nenhuma obra nacional contratada ainda.</div>}
            <p className="indicator-footnote">Empresas e ocorrências são fictícias. Durante a execução, problemas financeiros ou alertas de integridade podem suspender a obra e exigir uma decisão; atrasos e sobrecustos ficam no histórico.</p>
          </section>}
        </> : <div className="empty-state">Carregando o orçamento...</div>}
      </section>}
      {activeTab === 'Crises' && <section className="panel agenda-page"><div className="eyebrow">EVENTOS FICTÍCIOS · CONSEQUÊNCIAS NO MOTOR</div><h2>Crises e respostas</h2><p className="page-description">Os eventos são simulados. Enquanto uma crise estiver ativa, seus efeitos continuam; cada resposta altera orçamento, atividade e apoio.</p>{state.active_crises?.length ? state.active_crises.map((event) => <article className="crisis-card" key={event.id}><div className="crisis-heading"><div><span className="simulated-tag">SIMULAÇÃO</span><h3>{event.title}</h3></div><b>Gravidade {event.severity}/3</b></div><p>{event.description}</p><small>Ativa há {event.days_active} dias · impacto contínuo no PIB, infraestrutura e aprovação.</small><div className="crisis-actions">{event.options?.map((option) => <button key={option.id} className="secondary-button" disabled={busy} onClick={() => respondEvent(event.id, option.id)}><b>{option.label}</b><small>Custo R$ {option.cost_bi.toFixed(1)} bi · PIB {option.forecast?.gdp_pp >= 0 ? '+' : ''}{option.forecast?.gdp_pp ?? 0} p.p. · apoio {option.forecast?.approval_pp >= 0 ? '+' : ''}{option.forecast?.approval_pp ?? 0} p.p.</small><small>{option.forecast?.summary || 'O efeito aparece após registrar a resposta.'}</small><small className="forecast-later">{option.forecast?.future || 'Os efeitos mensais da crise ativa param após a resposta.'}</small></button>)}</div></article>) : <div className="empty-state">Nenhuma crise ativa. Eventos futuros podem surgir conforme o calendário e a dificuldade.</div>}<h3 className="subheading">Noticiário simulado recente</h3>{state.simulated_news?.length ? <ul className="ds-timeline">{Object.values(state.simulated_news.reduce((acc, item) => { const g = acc[item.title] || { ...item, count: 0 }; g.count += 1; acc[item.title] = g; return acc; }, {})).slice(0, 8).map((item) => <li key={item.id}><time dateTime={item.date}>{item.date.split('-').reverse().join('/')}</time><b>{item.title}{item.count > 1 && <span className="ds-muted"> · {item.count} vezes</span>}</b><p className="ds-muted">{item.description}</p></li>)}</ul> : <p className="empty-state">Ainda não há notícia simulada registrada.</p>}</section>}

      {activeTab === 'Eleição' && <CampaignPanel state={state} request={request} onState={setState} busy={busy} setBusy={setBusy} onNotice={setNotice} />}
      {['Carreira', 'Mandato'].includes(activeTab) && <CareerPanel state={state} request={request} onState={setState} onNotice={setNotice} busy={busy} setBusy={setBusy} standaloneMandate={activeTab === 'Mandato'} />}

      {activeTab === 'Instituições' && <section className="panel agenda-page"><div className="eyebrow">CENÁRIO INSTITUCIONAL FICTÍCIO</div><h2>Instituições e estabilidade</h2><p className="page-description">Indicadores agregados mudam com as decisões. A opção de ruptura é uma mecânica de alto risco, inteiramente abstrata; não há passos operacionais.</p><div className="institution-grid">{Object.entries(state.institutions || {}).map(([key, value]) => <article key={key}><span>{institutionLabels[key] || key.replaceAll('_', ' ')}</span><strong>{formatIndicator(value, key)}/100</strong><div className="bar"><i style={{ width: `${value}%` }}/></div></article>)}</div>{presidentCareer && <div className="rupture-box"><h3>Ruptura institucional simulada</h3><p>Sucesso: governo de facto, resistência institucional, isolamento e choque econômico. Fracasso: prisão e remoção do cargo. Os resultados são calculados pelo motor e pela semente da partida.</p><button className="secondary-button" onClick={loadRupturePreview}>Ver chance e consequências</button>{ruptureInfo && <div className="rupture-preview"><b>Chance abstrata de sucesso: {ruptureInfo.chance}%</b><p>{ruptureInfo.success}</p><p>{ruptureInfo.failure}</p><button className="danger-button" disabled={busy} onClick={attemptRupture}>Tentar ruptura no cenário</button></div>}</div>}</section>}

      {activeTab === 'Nomeações' && <GovernmentAppointments state={state} request={request} onState={setState} onNotice={setNotice} busy={busy} setBusy={setBusy} />}

      <Related tab={activeTab} exists={new Set(tabGroups.flatMap((g) => g.items))} go={setActiveTab} />
      <footer className="footer"><span>QUATRO ANOS · v0.5 · em desenvolvimento</span><span>Eventos e projeções são ficção; resultados numéricos seguem regras do motor.</span></footer>
    </main>
    {state.communications?.inauguration?.required && <InauguralAddress request={request} onState={setState} onNotice={setNotice} onChooseCareer={() => setActiveTab('Carreira')} busy={busy} setBusy={setBusy} />}
    {showAccountPanel && <AccountPanel onClose={() => setShowAccountPanel(false)} />}
    {gameGuideOpen && <GameGuide groups={tabGroups} activeTab={activeTab} onGo={setActiveTab} onClose={() => setGameGuideOpen(false)} />}
    {!gameGuideOpen && <button type="button" className="ds-guide-fab" aria-label="Abrir o guia do jogo" title="Guia do jogo" onClick={() => setGameGuideOpen(true)}>?</button>}
  </div>;
}
