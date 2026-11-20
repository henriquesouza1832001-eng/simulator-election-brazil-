import { useEffect, useMemo, useState } from 'react';
import { br } from './format';
import { Amplify } from 'aws-amplify';
import { fetchAuthSession, getCurrentUser, signOut } from 'aws-amplify/auth';
import { cognitoUserPoolsTokenProvider } from 'aws-amplify/auth/cognito';
import { CookieStorage } from 'aws-amplify/utils';
import DiplomacyPanel from './DiplomacyPanel';
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
import IndicatorsPanel from './IndicatorsPanel';
import OverviewPanel from './OverviewPanel';
import ApuracaoPanel from './ApuracaoPanel';
import RedesPanel from './RedesPanel';
import Related from './Related';
import HashRoute from './HashRoute.jsx';
import ProjetosPanel from './ProjetosPanel.jsx';
import LeisPanel from './LeisPanel.jsx';
import MercadoPanel from './MercadoPanel.jsx';
import PartyPathPanel from './PartyPathPanel';
import PowersPanel from './PowersPanel';
import RegulatorsPanel from './RegulatorsPanel';
import NewsPanel from './NewsPanel';
import InterviewsPanel from './InterviewsPanel';
import CompaniesPanel from './CompaniesPanel';
import CongressProcessPanel from './CongressProcessPanel';
import HistoryPanel from './HistoryPanel';
import './territory.css';
import TerritoryPanel from './TerritoryPanel';
import { StoryPanel, CampaignWeekPanel, CongressPanel, RankingPanel, CollectionPanel, DiaryPanel } from './MetaPanels';
import AgendaPanel from './AgendaPanel';
import AboutPanel from './AboutPanel';
import './diplomacy.css';
import './ai-status.css';
import { OFFICE_STATUS_LABEL, formatIndicator, indicatorOptions, readIndicator } from './appData.jsx';
import BudgetSection from './BudgetSection.jsx';
import CrisesSection from './CrisesSection.jsx';
import InstitutionsSection from './InstitutionsSection.jsx';
import MeasuresSection from './MeasuresSection.jsx';
import TopBar from './TopBar.jsx';
import TabNav from './TabNav.jsx';

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

  async function submitOperatingBudget() {
    setBusy(true);
    try {
      const data = await request('/api/budget/operating', { method: 'POST', body: JSON.stringify({ travel_cut_pct: Number(travelCutPct), residence_cut_pct: Number(residenceCutPct) }) });
      setBudgetView(data.budget); setState(data.state);
      const annual = data.effects.find((item) => item.label === 'Economia anual recorrente')?.value_bi || 0;
      setNotice(annual >= 0 ? `Cortes registrados: R$ ${br(annual, 3)} bi a menos por ano em despesas recorrentes.` : `Recomposição registrada: R$ ${br(Math.abs(annual), 3)} bi a mais por ano em despesas recorrentes.`);
    } catch (e) { setNotice(e.message); } finally { setBusy(false); }
  }

  async function applyFiscalLever(lever, option, label) {
    if (!window.confirm(`Aplicar: ${label}? A decisão entra em vigor agora e não pode ser desfeita.`)) return;
    setBusy(true);
    try {
      const data = await request('/api/budget/lever', { method: 'POST', body: JSON.stringify({ lever, option }) });
      setBudgetView(data.budget); setState(data.state); setNotice(data.result.message);
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
  const careerCardNote = careerWaiting ? (careerPhase === 'pre_campaign' ? 'para abrir a campanha — prepare-se antes' : 'para a próxima campanha') : careerPhase === 'campaign' ? 'dias até a votação' : careerPhase === 'runoff_campaign' || careerPhase === 'runoff_observer' ? 'dias até o segundo turno' : careerPhase === 'transition' ? 'dias até a posse' : careerPhase === 'office' ? `campanha abre em ${state.career_overview?.days_until_campaign} ${Number(state.career_overview?.days_until_campaign) === 1 ? 'dia' : 'dias'}` : 'escolha o próximo passo';
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
  const careerCards = localCareer && careerOverview?.governing ? [
    { label: 'Aprovação do mandato', value: careerOverview.poll_support, unit: '%', detail: `Avaliação em ${careerOverview.campaign_territory || careerOverview.state_name}`, tone: 'green' },
    { label: 'Reputação', value: careerOverview.reputation, unit: '/100', detail: 'Construída na militância e no mandato' },
    { label: 'Compromissos pendentes', value: careerOverview.pending_campaign_promises, unit: '', detail: 'Promessas de campanha que podem ser cobradas' },
  ] : localCareer ? [
    { label: 'Intenção de voto', value: careerOverview.vote_intent ?? careerOverview.poll_support, unit: '%', detail: `Projeção para a eleição em ${careerOverview.campaign_territory || 'seu território'}`, tone: 'green' },
    ...(careerOverview.rivals?.length ? [(() => { const top = [...careerOverview.rivals].sort((a, b) => b.support - a.support)[0]; return { label: 'Maior rival', value: top.support, unit: '%', detail: `${top.party} · foco: ${top.issue_focus_label || '—'}`, tone: 'amber' } })()] : []),
    { label: 'Reputação', value: careerOverview.reputation, unit: '/100', detail: 'Construída na militância e no mandato' },
    { label: 'Fundo de campanha', value: careerOverview.campaign_fund_mi, unit: ' mi', detail: 'Recurso disponível para a campanha', tone: 'amber' },
    { label: 'Embalo', value: careerOverview.momentum, unit: '', detail: 'Tendência recente da campanha' },
    { label: 'Compromissos pendentes', value: careerOverview.pending_campaign_promises, unit: '', detail: 'Promessas que podem ser cobradas' },
  ] : [];
  const careerNextStep = !localCareer ? null : careerPhase === 'pre_campaign'
    ? { label: 'PRÉ-CAMPANHA', title: 'Monte sua base antes de a campanha abrir', text: `Faltam ${careerOverview.days_until_campaign} ${Number(careerOverview.days_until_campaign) === 1 ? 'dia' : 'dias'} para a campanha e ${careerOverview.days_until_election} para a votação. Use a preparação para ganhar organização e reconhecimento.` }
    : careerPhase === 'campaign'
      ? { label: 'CAMPANHA', title: careerOverview.can_act ? 'Hoje há tempo para uma atividade de campanha' : `Próxima atividade em ${careerOverview.days_until_action} ${Number(careerOverview.days_until_action) === 1 ? 'dia' : 'dias'}`, text: `Votação em ${careerOverview.days_until_election} ${Number(careerOverview.days_until_election) === 1 ? 'dia' : 'dias'}. Debate, comícios e visitas movem a intenção de voto; o fundo é limitado.` }
      : careerPhase === 'transition'
        ? { label: 'POSSE', title: 'Resultado apurado', text: `A posse acontece em ${careerOverview.days_until_inauguration} ${Number(careerOverview.days_until_inauguration) === 1 ? 'dia' : 'dias'}. Veja na aba Carreira como foi a votação.` }
        : careerPhase === 'office'
          ? { label: 'MANDATO', title: `Exercendo o cargo de ${careerOverview.office_label}`, text: `A próxima campanha abre em ${careerOverview.days_until_campaign} ${Number(careerOverview.days_until_campaign) === 1 ? 'dia' : 'dias'}. Use a aba do cargo para decidir e acompanhe os acontecimentos.` }
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
    { label: 'Painel', items: ['Visão geral', 'Agenda', ...(!careerMode || careerOffice === 'presidente' ? ['Mercado'] : []), 'Indicadores', 'Histórico', 'Carimbos'] },
    { label: careerMode && careerOverview?.governing ? officeTabLabel : 'Governo', items: careerMode ? (careerOverview?.governing ? ['Mandato', 'Competências', ...(['presidente', 'governador'].includes(careerOffice) ? ['Empresas'] : []), ...(careerOffice === 'presidente' ? ['Projetos'] : []), ...(['presidente', 'governador', 'prefeito'].includes(careerOffice) ? ['Obras e mapa'] : [])] : []) : ['Medidas', 'Competências', 'Empresas', 'Orçamento', 'Projetos', 'Obras e mapa', 'Crises'] },
    { label: 'Política', items: careerMode ? ['Carreira', 'Apuração', ...(careerOffice === 'presidente' ? ['Instituições', 'Reguladores'] : []), ...(careerOffice === 'presidente' && careerOverview?.governing ? ['Tramitação', 'Nomeações'] : []), ...(['vereador', 'deputado_estadual', 'deputado_federal', 'senador', 'governador', 'prefeito'].includes(careerOffice) && careerOverview?.governing ? ['Tramitação'] : [])] : ['Carreira', 'Eleição', 'Apuração', 'Semana', 'Congresso', 'Tramitação', 'Instituições', 'Reguladores', 'Nomeações'] },
    { label: 'Mundo', items: [...(presidentCareer ? ['Diplomacia'] : []), 'Leis e história'] },
    { label: 'Imprensa', items: ['Imprensa', 'Redes', 'Entrevistas', 'Acontecimentos'] },
    { label: 'Sobre', items: ['O jogo', 'Termos', 'Créditos'] },
  ].filter((group) => group.items.length);
  const tabGroups = [...baseGroups, { label: 'Perfil', hidden: true, items: ['Placar', 'Diário'] }];
  const availableTabs = tabGroups.flatMap((group) => group.items);
  const activeTab = rawTab && availableTabs.includes(rawTab) ? rawTab : baseGroups[0].items[0];
  const selectedTabGroup = tabGroups.find((group) => group.items.includes(activeTab)) || baseGroups[0];
  const dashboardTab = ['Visão geral', 'Medidas'].includes(activeTab);
  const pageGuidance = {
    'Visão geral': localCareer ? ['Sua carreira em movimento.', 'Veja onde você está no calendário e escolha o próximo passo.'] : (monthsRemaining === 0 && termMonth >= 48 ? ['O mandato terminou.', 'Veja o balanço final abaixo e decida se continua jogando ou abre uma nova partida.'] : ['O país, em movimento.', 'Veja o que pede atenção hoje e escolha o próximo passo.']),
    'Indicadores': ['Como está o país?', 'Abra os grupos para acompanhar os dados sem sobrecarregar o painel inicial.'],
    'Medidas': ['Prepare uma decisão.', 'Descreva a proposta; revise a interpretação e os efeitos antes de aplicar.'],
    'Mercado': ['Como o mercado reage?', 'Dólar, bolsa, juros e risco-país mudam com cada decisão sua e com as contas do governo.'],
    'Leis e história': ['O país por trás das regras.', 'Normas que o jogo usa como régua e a linha do tempo da democracia, do regime militar aos dias de hoje.'],
    'Projetos': ['Que obra ou programa abrir?', 'Do viaduto à missão à Lua: escolha o projeto, a empresa e acompanhe as fases até a entrega.'],
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
  const mandateOver = !partyMode && !localCareer && ['former_president', 'detained_after_failed_rupture', 'former_official'].includes(state.office_status);
  const overviewNext = mandateOver
    ? { label: 'FIM DO MANDATO', title: 'Seu mandato terminou', text: 'Não há mais decisões do cargo a tomar. Veja o balanço do mandato e o histórico ou comece uma nova carreira.', urgent: false, actions: [{ label: 'Começar nova carreira', tab: 'Carreira', primary: true }, { label: 'Ver histórico', tab: 'Histórico' }] }
    : localCareer
    ? { label: careerNextStep.label, title: careerNextStep.title, text: careerNextStep.text, urgent: false, actions: [{ label: mainLabel, tab: mainTab, primary: true }, { label: 'Ver acontecimentos', tab: 'Acontecimentos' }] }
    : nextCrisis ? { label: 'Crise em andamento', title: nextCrisis.title, text: nextCrisis.description, urgent: true, actions: [{ label: careerMode ? 'Ver situação da carreira' : 'Ver opções de resposta', tab: careerMode ? 'Carreira' : 'Crises', primary: true }, { label: 'Abrir agenda', tab: 'Agenda' }] }
      : nextEvent ? { label: nextEvent.days_until === 0 ? 'Acontece hoje' : `Próximo evento · em ${nextEvent.days_until} ${Number(nextEvent.days_until) === 1 ? 'dia' : 'dias'}`, title: nextEvent.title, text: nextEvent.description, urgent: false, actions: [{ label: mainLabel, tab: mainTab, primary: true }, { label: 'Abrir agenda', tab: 'Agenda' }] }
        : { label: 'Sem pendências', title: 'Nada urgente agora', text: 'Use o tempo para preparar uma decisão ou avance o calendário.', urgent: false, actions: [{ label: mainLabel, tab: mainTab, primary: true }] };
  const daysTo = (iso) => (iso ? Math.round((new Date(`${iso}T12:00:00`) - new Date(`${state.date}T12:00:00`)) / 864e5) : null);
  const despacho = mandateOver || partyMode ? [] : [
    ...(state.scenario_view?.status === 'em_andamento' ? state.scenario_view.goals.filter((g) => !g.done).slice(0, 2).map((g) => ({ key: `m-${g.id}`, kind: 'Meta', title: g.label, detail: g.progress, days: null, tab: g.tab, urgent: false })) : []),
    ...(localCareer ? [] : (state.consequences?.pending || []).map((c) => ({
      key: `p-${c.id}`, kind: String(c.action_id || '').startsWith('pauta_') ? 'Sanção' : c.regulator ? 'Regulador' : 'Crise', title: c.title, detail: 'Escolha uma resposta antes do prazo; sem resposta vale a pior opção.', days: daysTo(c.deadline), tab: 'Imprensa', urgent: true }))),
    ...((localCareer ? [] : state.active_crises || []).filter((c) => c.status === 'active').map((c) => ({
      key: `c-${c.id}`, kind: 'Crise', title: c.title, detail: 'Está em andamento e muda indicadores todo mês.', days: null, tab: 'Crises', urgent: true }))),
    ...(localCareer && careerOverview?.can_act && ['campaign', 'runoff_campaign'].includes(careerPhase) ? [{ key: 'camp', kind: 'Campanha', title: 'Atividade de campanha liberada', detail: `Faltam ${careerOverview.days_until_election} dias para a eleição.`, days: null, tab: 'Carreira', urgent: false }] : []),
    ...(!localCareer && Number.isFinite(state.action_limits?.executive_days) && state.action_limits.executive_days === 0 && state.office_status === 'incumbent' ? [{ key: 'exec', kind: 'Decisão', title: 'Você pode assinar uma decisão do Executivo', detail: 'Decreto ou medida provisória liberados agora.', days: null, tab: careerMode ? 'Competências' : 'Medidas', urgent: false }] : []),
    ...((state.legislative_calendar?.pending_bills || []).slice(0, 3).map((b) => ({ key: `b-${b.id}`, kind: 'Votação', title: b.title, detail: 'Projeto aguardando votação no plenário.', days: daysTo(b.decision_date), tab: 'Tramitação', urgent: false }))),
  ].sort((a, b) => (b.urgent - a.urgent) || ((a.days ?? 999) - (b.days ?? 999)));
  const monthsToElection = careerOverview?.days_until_campaign;
  const overviewProps = {
    despacho,
    request, state, go: setActiveTab, pins, onUnpin: togglePin,
    scope: !careerMode || careerOffice === 'presidente' ? 'nacional' : 'local',
    rivals: careerOverview?.rivals || [], rivalEvents: careerOverview?.rival_events || [], territory: careerOverview ? (careerOverview.campaign_territory || careerOverview.municipality || careerOverview.state_name) : null,
    title: activeTab === 'Visão geral' ? pageGuidance[0] : 'Visão geral', lead: activeTab === 'Visão geral' ? pageGuidance[1] : undefined,
    term: partyMode ? null : { label: careerMode ? careerCardLabel : 'Mandato', value: careerMode ? careerCardValue : termMonth, suffix: careerMode ? careerCardSuffix : ' / 48', progress: careerMode ? careerCardProgress : termMonth / 48 * 100, note: careerMode ? careerCardNote : `${monthsRemaining} meses restantes` },
    stats: localCareer
      ? { title: `Sua situação · ${careerOverview.office_label}`, items: careerCards.map((c) => ({ label: c.label, value: formatIndicator(c.value), unit: c.unit?.trim(), note: c.detail })) }
      : { title: 'Seus números', items: selectedCards.map((key) => { const option = indicatorOptions.find((item) => item.key === key); return option ? { label: option.label, value: formatIndicator(readIndicator(option, state), key), unit: option.unit?.trim(), note: option.detail } : null; }).filter(Boolean) },
    customize: localCareer ? null : { options: indicatorOptions, selected: selectedCards, toggle: toggleDashboardCard },
    next: overviewNext, upcoming: upcomingEvents, last: state.recent_actions?.[0] || null,
    calendar: localCareer ? [['Campanha abre', careerOverview.campaign_start_date], ['Votação', careerOverview.election_date], ['Posse', careerOverview.inauguration_date]] : null,
    governing: localCareer ? null : { governability: m.governability, congress_support: m.congress_support, institutional_trust: m.institutional_trust },
    skip: localCareer && careerPhase === 'pre_campaign' && monthsToElection > 120 && String(careerOverview?.election_date || '').slice(0, 4) !== String(state.date || '').slice(0, 4) ? { text: `A campanha abre em ${monthsToElection} ${Number(monthsToElection) === 1 ? 'dia' : 'dias'}. Se preferir não esperar, o jogo pode avançar sozinho até o ano da eleição (os meses passam normalmente, com economia e acontecimentos).`, label: 'Pular para o ano da eleição', busy, onSkip: skipToElectionYear } : null,
    showReview: !localCareer && !partyMode,
    showBalance: !localCareer && !partyMode && monthsRemaining === 0 && termMonth >= 48,
  };
  // contadores do menu: o que está pedindo atenção em cada grupo (só entra o que o jogo realmente tem)
  const pendingByTab = { Crises: (state.active_crises || []).length, Tramitação: (state.legislative_calendar?.pending_bills || []).length, Agenda: (state.events || []).filter((e) => Number(e.days_until) <= 7).length, Imprensa: (state.consequences?.pending || []).length };
  const badgeOf = (group) => group.items.reduce((n, tab) => n + (pendingByTab[tab] || 0), 0);
  const railGroups = tabGroups.filter((group) => !group.hidden && !['Mundo', 'Sobre'].includes(group.label))
    .map((group) => ({ ...group, badge: badgeOf(group), rail: ['Painel', 'Política', 'Imprensa', 'Militância'].includes(group.label) ? group.label : 'Governo', icon: ['Painel', 'Política', 'Imprensa'].includes(group.label) ? group.label : group.label === 'Militância' ? 'Política' : 'Governo' }));
  const moreEntries = [
    ...(tabGroups.find((group) => group.label === 'Mundo')?.items || []).map((tab) => ({ label: tab, icon: 'Mundo', hint: TAB_HELP[tab], go: () => setActiveTab(tab) })),
    { label: 'Placar', icon: 'Placar', hint: TAB_HELP.Placar, go: () => setActiveTab('Placar') },
    { label: 'Diário', icon: 'Diário', hint: TAB_HELP['Diário'], go: () => setActiveTab('Diário') },
    { label: 'Guia', hint: 'O que cada aba faz e o glossário', go: () => setGameGuideOpen(true) },
    ...(tabGroups.find((group) => group.label === 'Sobre')?.items || []).map((tab) => ({ label: tab, icon: 'Sobre', hint: TAB_HELP[tab], go: () => setActiveTab(tab) })),
    { label: 'Partidas', hint: 'Trocar ou começar uma partida', go: () => setShowGameMenu(true) },
    ...(authConfig?.enabled ? (authUser?.isGuest
      ? [{ label: 'Entrar / criar conta', icon: 'Perfil', go: () => { setShowAuthPanel(true); setNotice(''); } }]
      : [{ label: 'Conta', icon: 'Perfil', go: () => setShowAccountPanel(true) }, { label: 'Sair', icon: 'Perfil', go: async () => { await signOut(); setAuthUser(null); setState(null); setShowGameMenu(true); } }]) : []),
  ];
  return <div className={`app-shell ${railOpen ? 'rail-open' : ''}`}>
    <HashRoute tab={activeTab} tabs={tabGroups.flatMap((g) => g.items)} go={setActiveTab} />
    <TopBar advance={advance} advanceOpen={advanceOpen} authConfig={authConfig} authUser={authUser} busy={busy} careerMode={careerMode} dateLabel={dateLabel} gameGuideOpen={gameGuideOpen} partyMode={partyMode} setAdvanceOpen={setAdvanceOpen} setAuthUser={setAuthUser} setGameGuideOpen={setGameGuideOpen} setNotice={setNotice} setShowAccountPanel={setShowAccountPanel} setShowAuthPanel={setShowAuthPanel} setShowGameMenu={setShowGameMenu} setState={setState} state={state} termMonth={termMonth} />
    <Nav expanded={railOpen} onToggle={toggleRail} items={railGroups} current={selectedTabGroup.label} moreActive={['Mundo', 'Sobre', 'Perfil'].includes(selectedTabGroup.label)} onGo={(group) => { if (!group.items.includes(activeTab)) setActiveTab(group.items[0]); }} onMore={() => setMoreOpen(true)} pins={pins} activePin={activeTab} onPin={setActiveTab} />
    <MoreSheet open={moreOpen} onClose={() => setMoreOpen(false)} entries={moreEntries} />
    <AdvanceMenu floating open={advanceFabOpen} setOpen={setAdvanceFabOpen} busy={busy} advance={advance} />
    {(selectedTabGroup.items.length > 1 || selectedTabGroup.hidden) && <TabNav activeTab={activeTab} baseGroups={baseGroups} pins={pins} selectedTabGroup={selectedTabGroup} setActiveTab={setActiveTab} togglePin={togglePin} />}

    <main className="content">



      {activeTab === 'Visão geral' && <OverviewPanel {...overviewProps} />}

      {dashboardTab && <>

      {activeTab === 'Medidas' && <MeasuresSection aiStatus={aiStatus} aiStatusLabel={aiStatusLabel} aiStatusTitle={aiStatusTitle} busy={busy} interpret={interpret} m={m} measure={measure} notice={notice} preview={preview} request={request} setActiveTab={setActiveTab} setBusy={setBusy} setMeasure={setMeasure} setNotice={setNotice} setState={setState} signMeasure={signMeasure} state={state} />}</>}

      {activeTab === 'Agenda' && <AgendaPanel state={state} goals={state.scenario_view?.goals || careerOverview?.goals || []} campaign={Boolean(careerOverview?.campaign_active)} go={setActiveTab} />}

      {activeTab === 'Diplomacia' && <DiplomacyPanel date={state.date} authEnabled={authConfig?.enabled} onState={setState} onNotice={setNotice} busy={busy} setBusy={setBusy} />}

      {activeTab === 'Indicadores' && <IndicatorsPanel request={request} state={state} onAct={() => setActiveTab(careerMode ? (careerOverview?.governing ? 'Mandato' : 'Carreira') : 'Medidas')} actLabel={careerMode ? (careerOverview?.governing ? 'Ir para o mandato' : 'Ver minha carreira') : 'Preparar uma medida'} />}

      {activeTab === 'Mercado' && <MercadoPanel request={request} state={state} />}
      {activeTab === 'Leis e história' && <LeisPanel request={request} />}
      {activeTab === 'Projetos' && <ProjetosPanel request={request} state={state} onState={setState} onNotice={setNotice} />}
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
      {activeTab === 'Orçamento' && <BudgetSection applyFiscalLever={applyFiscalLever} budgetSection={budgetSection} budgetView={budgetView} busy={busy} fiscalReferenceGdp={fiscalReferenceGdp} m={m} ministries={ministries} notice={notice} proposedOperatingSavings={proposedOperatingSavings} proposedPrimaryBalance={proposedPrimaryBalance} residenceCutPct={residenceCutPct} setActiveTab={setActiveTab} setBudgetSection={setBudgetSection} setResidenceCutPct={setResidenceCutPct} setTravelCutPct={setTravelCutPct} submitBudgetTransfer={submitBudgetTransfer} submitOperatingBudget={submitOperatingBudget} travelCutPct={travelCutPct} />}
      {activeTab === 'Crises' && <CrisesSection busy={busy} respondEvent={respondEvent} state={state} />}

      {activeTab === 'Eleição' && <CampaignPanel state={state} request={request} onState={setState} busy={busy} setBusy={setBusy} onNotice={setNotice} />}
      {['Carreira', 'Mandato'].includes(activeTab) && <CareerPanel state={state} request={request} onState={setState} onNotice={setNotice} busy={busy} setBusy={setBusy} standaloneMandate={activeTab === 'Mandato'} />}

      {activeTab === 'Instituições' && <InstitutionsSection attemptRupture={attemptRupture} busy={busy} loadRupturePreview={loadRupturePreview} presidentCareer={presidentCareer} ruptureInfo={ruptureInfo} state={state} />}

      {activeTab === 'Nomeações' && <GovernmentAppointments state={state} request={request} onState={setState} onNotice={setNotice} busy={busy} setBusy={setBusy} />}

      <Related tab={activeTab} exists={new Set(tabGroups.flatMap((g) => g.items))} go={setActiveTab} />
      <footer className="footer"><span>QUATRO ANOS · v0.5 · em desenvolvimento</span><span>Eventos e projeções são ficção; resultados numéricos seguem regras do motor.</span></footer>
    </main>
    {state.communications?.inauguration?.required && <InauguralAddress request={request} onState={setState} onNotice={setNotice} onChooseCareer={() => setActiveTab('Carreira')} busy={busy} setBusy={setBusy} />}
    {showAccountPanel && <AccountPanel onClose={() => setShowAccountPanel(false)} />}
    {gameGuideOpen && <GameGuide groups={tabGroups} activeTab={activeTab} onGo={setActiveTab} onClose={() => setGameGuideOpen(false)} />}
  </div>;
}
