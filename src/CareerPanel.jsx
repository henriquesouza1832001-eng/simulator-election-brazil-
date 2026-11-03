import { useEffect, useMemo, useState } from 'react';
import TSEArchivePanel from './TSEArchivePanel';
import MunicipalityPicker from './MunicipalityPicker';
import './career.css';

const number = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 1 });
const dateLabel = (value) => value ? new Date(`${value}T12:00:00`).toLocaleDateString('pt-BR', { day: 'numeric', month: 'long', year: 'numeric' }) : '—';

export default function CareerPanel({ state, request, onState, onNotice, busy, setBusy }) {
  const overview = state.career_overview;
  const municipalityProfile = overview?.municipality_profile;
  const [options, setOptions] = useState(null);
  const [archives, setArchives] = useState([]);
  const [section, setSection] = useState('Carreira');
  const [office, setOffice] = useState('vereador');
  const [stateCode, setStateCode] = useState('SP');
  const [municipality, setMunicipality] = useState('');
  const [municipalityId, setMunicipalityId] = useState('');
  const [party, setParty] = useState('Partido da Renovação');
  const [ideology, setIdeology] = useState('Centro');
  const [candidateName, setCandidateName] = useState('');
  const [activity, setActivity] = useState('comicio');
  const [conduct, setConduct] = useState('regular');
  const [issue, setIssue] = useState('economia');
  const [message, setMessage] = useState('');
  const [result, setResult] = useState(null);
  const [governmentAction, setGovernmentAction] = useState('');
  const [governmentIssue, setGovernmentIssue] = useState('');
  const [governmentResult, setGovernmentResult] = useState(null);
  const [showSetup, setShowSetup] = useState(!overview);
  const [selectedArchive, setSelectedArchive] = useState('');
  const [historyExpanded, setHistoryExpanded] = useState(false);

  useEffect(() => {
    let mounted = true;
    Promise.all([request('/api/career/options'), request('/api/game/archives')])
      .then(([catalog, saved]) => { if (mounted) { setOptions(catalog); setArchives(saved.items || []); } })
      .catch((error) => onNotice(error.message));
    return () => { mounted = false; };
  }, []);

  const chosenOffice = useMemo(() => options?.offices.find((item) => item.key === office), [options, office]);
  const chosenCalendar = useMemo(() => options?.calendar_previews?.[office], [options, office]);
  const chosenActivity = useMemo(() => overview?.activity_options?.find((item) => item.key === activity), [overview, activity]);
  const sections = ['Carreira', overview?.phase === 'office' ? 'Mandato' : 'Campanha', 'Apoio', 'Histórico', 'Dados do TSE'];

  useEffect(() => { if (!sections.includes(section)) setSection(sections[0]); }, [overview?.phase]);
  useEffect(() => { if (!governmentAction && overview?.governance_actions?.length) setGovernmentAction(overview.governance_actions[0].key); }, [overview?.governance_actions]);

  async function start(event) {
    event.preventDefault();
    const archiveMessage = overview ? 'O personagem e o histórico permanecem na mesma carreira. Iniciar outra disputa?' : 'A partida atual será arquivada e poderá ser restaurada depois. Iniciar esta nova carreira?';
    const confirmed = window.confirm(archiveMessage);
    if (!confirmed) return;
    setBusy(true);
    try {
      const data = await request('/api/career/start', { method: 'POST', body: JSON.stringify({ office, state_code: stateCode, municipality, municipality_id: municipalityId, party, ideology, candidate_name: candidateName, difficulty: state.difficulty || 'normal' }) });
      onState(data.state);
      if (!overview) {
        const saved = await request('/api/game/archives');
        setArchives(saved.items || []);
      }
      setShowSetup(false);
      setSection('Campanha');
      setResult(null);
      const started = data.state.career_overview;
      onNotice(started.phase === 'pre_campaign'
        ? `Carreira iniciada. A campanha abre em ${dateLabel(started.campaign_start_date)} e a eleição será em ${dateLabel(started.election_date)}.`
        : `Carreira iniciada. A campanha está aberta; eleição simulada em ${dateLabel(started.election_date)}.`);
    } catch (error) { onNotice(error.message); }
    finally { setBusy(false); }
  }

  async function act(event) {
    event.preventDefault();
    setBusy(true);
    try {
      const data = await request('/api/career/action', { method: 'POST', body: JSON.stringify({ activity_type: activity, issue, message, conduct }) });
      onState(data.state);
      setResult(data.result);
      setMessage('');
      onNotice(data.calendar_message || data.result.message);
    } catch (error) { onNotice(error.message); }
    finally { setBusy(false); }
  }

  async function restore() {
    if (!selectedArchive) return;
    if (!window.confirm('A carreira atual será arquivada; a partida selecionada voltará a ser ativa. Continuar?')) return;
    setBusy(true);
    try {
      const data = await request(`/api/game/archives/${selectedArchive}/restore`, { method: 'POST', body: '{}' });
      onState(data.state);
      setArchives(data.archives || []);
      setShowSetup(false);
      onNotice('Partida restaurada. A carreira que estava ativa também ficou arquivada.');
    } catch (error) { onNotice(error.message); }
    finally { setBusy(false); }
  }

  async function govern(event) {
    event.preventDefault();
    setBusy(true);
    try {
      const data = await request('/api/career/govern', { method: 'POST', body: JSON.stringify({ action: governmentAction, issue: governmentIssue }) });
      onState(data.state);
      setGovernmentResult(data.result);
      setGovernmentIssue('');
      onNotice(data.result.summary);
    } catch (error) { onNotice(error.message); }
    finally { setBusy(false); }
  }

  if (!options) return <section className="panel career-page"><p>Carregando as regras de carreira…</p></section>;

  const setup = <form className="career-setup panel" onSubmit={start}>
    <div className="career-section-heading"><div><span className="eyebrow">{overview ? 'NOVA DISPUTA · MESMO PERSONAGEM' : 'NOVA PARTIDA POLÍTICA'}</span><h2>{overview ? 'Escolha o próximo cargo' : 'Escolha onde começa sua carreira'}</h2><p>{overview ? `Sua trajetória fica registrada com ${overview.history?.length || 0} disputa(s) anterior(es). O mandato ou a transição atual não pode ser abandonado.` : 'A campanha, a eleição, o mandato e a oposição compartilham o mesmo calendário. A partida atual será arquivada antes da troca.'}</p></div><span className="career-step">1 / 3</span></div>
    <div className="career-form-grid">
      <label>Cargo<select value={office} onChange={(event) => setOffice(event.target.value)}>{options.offices.map((item) => <option value={item.key} key={item.key}>{item.label}</option>)}</select></label>
      <label>Estado<select value={stateCode} onChange={(event) => { setStateCode(event.target.value); setMunicipality(''); setMunicipalityId(''); }}>{options.states.map((item) => <option value={item.code} key={item.code}>{item.name}</option>)}</select></label>
      <MunicipalityPicker request={request} stateCode={stateCode} value={municipality} selectedId={municipalityId} onSelect={(item) => { setMunicipality(item.name); setMunicipalityId(item.id); }} />
      <label>Partido simulado<select value={party} onChange={(event) => setParty(event.target.value)}>{options.parties.map((item) => <option key={item}>{item}</option>)}</select></label>
      <label>Posicionamento<select value={ideology} onChange={(event) => setIdeology(event.target.value)}>{options.ideologies.map((item) => <option key={item}>{item}</option>)}</select></label>
      <label>Nome na urna<input value={candidateName} onChange={(event) => setCandidateName(event.target.value)} maxLength={80} placeholder={overview?.candidate_name || 'Nome do personagem'} /></label>
    </div>
    {chosenOffice && <div className="career-office-preview"><div><span>MANDATO</span><b>{chosenOffice.term_years} anos</b></div><div><span>ELEITORADO</span><b>{chosenOffice.electorate}</b></div><div><span>ESCOPO</span><b>{chosenOffice.scope === 'municipal' ? 'Município' : chosenOffice.scope === 'estadual' ? 'Estado' : 'País'}</b></div><div><span>PRÓXIMA ELEIÇÃO</span><b>{dateLabel(chosenCalendar?.election_date)}</b><small>Campanha abre em {dateLabel(chosenCalendar?.campaign_start)} · posse em {dateLabel(chosenCalendar?.inauguration_date)}</small></div><div className="career-powers"><span>O cargo permite</span><ul>{chosenOffice.powers.map((power) => <li key={power}>{power}</li>)}</ul></div></div>}
    <div className="career-setup-footer"><small>{options.simulated_notice}</small><button className="primary-button" disabled={busy || !municipalityId}>Iniciar carreira simulada <b>→</b></button></div>
  </form>;

  return <section className="career-page">
    {!overview || showSetup ? <>{setup}<details className="career-data-shortcut"><summary>Consultar candidaturas históricas do TSE</summary><TSEArchivePanel request={request} stateCode={stateCode} /></details></> : <>
      <header className="career-hero panel">
        <div className="career-hero-main"><span className="eyebrow">CARREIRA POLÍTICA · SIMULAÇÃO</span><h2>{overview.candidate_name}</h2><p>{overview.office_label} · {overview.municipality}/{overview.state_code} · {overview.party} · {overview.ideology}</p><div className="career-tags"><span>{overview.phase === 'campaign' ? 'EM CAMPANHA' : overview.phase === 'pre_campaign' ? 'PRÉ-CAMPANHA' : overview.phase === 'transition' ? 'TRANSIÇÃO' : overview.phase === 'office' ? 'NO CARGO' : overview.phase === 'opposition' ? 'NA OPOSIÇÃO' : 'MANDATO ENCERRADO'}</span><span>{overview.electorate}</span><span>ELEIÇÃO · {dateLabel(overview.election_date)}</span><span>REPUTAÇÃO · {number.format(overview.reputation)}/100</span></div>{municipalityProfile && <div className="career-municipality-context"><b>{municipalityProfile.city_size_label} · {number.format(municipalityProfile.population_estimate)} habitantes</b><span>Estimativa municipal do IBGE, referência {municipalityProfile.population_reference_year} · código {municipalityProfile.ibge_code}</span></div>}</div>
        <div className="career-poll"><span>{overview.phase === 'office' ? 'AVALIAÇÃO DO MANDATO' : overview.phase === 'pre_campaign' ? 'APOIO INICIAL' : 'INTENÇÃO DE VOTO'}</span><strong>{overview.result ? `${number.format(overview.vote_share)}%` : `${number.format(overview.poll_support)}%`}</strong><small>{overview.result === 'won' ? 'vitória simulada' : overview.result === 'lost' ? 'resultado simulado' : overview.phase === 'office' ? 'apoio ao mandato' : overview.phase === 'pre_campaign' ? `campanha abre em ${overview.days_until_campaign} dias` : `eleição em ${overview.days_until_election} dias`}</small></div>
      </header>
      <nav className="career-subnav" aria-label="Seções da carreira">{sections.map((item) => <button key={item} className={section === item ? 'active' : ''} onClick={() => setSection(item)}>{item}</button>)}<span/>{overview.can_start_campaign && <button onClick={() => setShowSetup(true)}>Nova candidatura</button>}</nav>

      {section === 'Carreira' && <div className="career-columns">
        <section className="panel career-status-panel"><span className="eyebrow">FASE ATUAL</span><h3>{overview.phase === 'campaign' ? 'Construa apoio antes da votação' : overview.phase === 'pre_campaign' ? 'Organize sua base antes da campanha' : overview.phase === 'transition' ? 'Prepare a posse' : overview.phase === 'office' ? `Mandato de ${overview.term_years} anos` : overview.phase === 'opposition' ? 'A disputa terminou; a carreira continua' : 'Mandato encerrado'}</h3><p>{overview.phase === 'campaign' ? `A eleição para ${overview.office_label} acontece em ${dateLabel(overview.election_date)}. A cada atividade, o motor mostra o efeito no apoio e o tempo que passa.` : overview.phase === 'pre_campaign' ? `A eleição para ${overview.office_label} será em ${dateLabel(overview.election_date)}. A campanha oficial abre em ${dateLabel(overview.campaign_start_date)}; até lá, o calendário do país continua avançando.` : overview.phase === 'transition' ? `A votação terminou. A posse simulada está prevista para ${dateLabel(overview.inauguration_date)}.` : overview.phase === 'office' ? `Você ocupa o cargo até ${dateLabel(overview.term_end)}. A avaliação combina confiança, entregas e atividades de campanha; indicadores e decisões do mandato estão sendo expandidos por cargo.` : overview.result === 'lost' ? `Você recebeu ${number.format(overview.vote_share)}% dos votos simulados. A partida permanece ativa e o próximo passo pode ser uma nova disputa.` : 'O registro fica na carreira e você pode iniciar outra candidatura.'}</p>{overview.phase === 'campaign' && <div className="career-countdown"><div><span>DIAS ATÉ A ELEIÇÃO</span><b>{overview.days_until_election}</b></div><div><span>FUNDO SIMULADO</span><b>R$ {number.format(overview.campaign_fund_mi)} mi</b></div><div><span>APOIO NO TERRITÓRIO</span><b>{number.format(overview.local_support)}%</b></div></div>}
          {overview.result && <div className={`career-result ${overview.result}`}><b>{overview.result === 'won' ? 'Vitória eleitoral simulada' : 'Derrota eleitoral simulada'}</b><span>Votos: {number.format(overview.vote_share)}% · adversário: {number.format(overview.opponent_share)}%</span>{overview.electoral_result?.system === 'proporcional_simulado' && <small>A legenda obteve {overview.electoral_result.party_seats} de {overview.electoral_result.district_magnitude} cadeiras simuladas; sua candidatura ocupava a primeira posição fictícia da lista. Distribuição proporcional simplificada.</small>}{overview.conduct_review?.attempts > 0 && <small>{overview.conduct_review.detected} irregularidade(s) detectada(s); revisão final {overview.conduct_review.reviewed ? 'aberta' : 'não aberta'}; penalidade de {number.format(overview.conduct_review.vote_penalty)} pontos.</small>}</div>}
        </section>
        <aside className="panel career-rules"><span className="eyebrow">PODERES DO CARGO</span><ul>{overview.powers.map((item) => <li key={item}>{item}</li>)}</ul><div className="career-appointment"><b>Outros caminhos</b>{overview.appointment_paths.map((item) => <p key={item.key} className={item.available ? 'available' : 'locked'}>{item.label}<small>{item.available ? item.description : `Disponível após exercer: ${item.requires.map((key) => options.offices.find((role) => role.key === key)?.label).join(', ')}`}</small></p>)}</div>{overview.can_start_campaign && <button className="secondary-button career-next-office" onClick={() => setShowSetup(true)}>Escolher próximo cargo</button>}</aside>
      </div>}

      {section === 'Campanha' && <div className="career-columns">
        <form className="panel career-action" onSubmit={act}><div className="career-section-heading"><div><span className="eyebrow">UMA AÇÃO DE CADA VEZ</span><h3>{overview.campaign_active ? 'Fale com o eleitorado' : overview.phase === 'pre_campaign' ? 'A campanha ainda não abriu' : overview.phase === 'office' ? 'A eleição está fora da janela de campanha' : 'Campanha encerrada'}</h3></div><span className="career-cooldown">{overview.campaign_active ? overview.days_until_action ? `EM ${overview.days_until_action} DIAS` : 'DISPONÍVEL' : overview.phase === 'pre_campaign' ? `EM ${overview.days_until_campaign} DIAS` : overview.phase}</span></div>
          {overview.campaign_active ? <><div className="career-form-grid"><label>Atividade<select value={activity} onChange={(event) => setActivity(event.target.value)}>{overview.activity_options.map((item) => <option value={item.key} key={item.key}>{item.label} · {item.days} dia(s) · R$ {number.format(item.cost_mi)} mi</option>)}</select></label><label>Tema<select value={issue} onChange={(event) => setIssue(event.target.value)}>{overview.issue_options.map((item) => <option value={item.key} key={item.key}>{item.label}</option>)}</select></label></div><details className="career-conduct"><summary>Conduta eleitoral · padrão dentro das regras</summary><label>Forma de conduzir a atividade<select value={conduct} onChange={(event) => setConduct(event.target.value)}><option value="regular">Dentro das regras</option><option value="irregular">Atalho irregular (simulação)</option></select></label><p>{conduct === 'irregular' ? `Detecção: ${number.format(overview.conduct_preview?.detection_pct || 0)}%. Revisão final após esta ação: ${number.format(overview.conduct_preview?.review_if_not_detected_pct || 0)}% a ${number.format(overview.conduct_preview?.review_if_detected_pct || 0)}%. Efeito agora: +0,6 p.p. se não detectada ou −3 p.p. se detectada.` : 'Sem risco adicional de sanção eleitoral.'} {overview.conduct_preview?.notice}</p></details><label className="career-message-label">Fala, proposta ou resposta<textarea value={message} onChange={(event) => setMessage(event.target.value)} maxLength={600} minLength={12} placeholder="Diga qual problema você quer resolver, como vai agir e que resultado o eleitor poderá cobrar." required /></label><div className="career-form-footer"><small>{message.length}/600 · {chosenActivity?.days || 1} dia(s) de calendário e R$ {number.format(chosenActivity?.cost_mi || 0)} mi do fundo de campanha.</small><button className="primary-button" disabled={busy || !overview.can_act || message.trim().length < 12}>{busy ? 'Calculando…' : overview.can_act ? 'Realizar atividade' : overview.days_until_action ? `Agenda em ${overview.days_until_action} dia(s)` : 'Ação indisponível'}</button></div></> : <p className="empty-state">{overview.phase === 'pre_campaign' ? `A campanha oficial abre em ${dateLabel(overview.campaign_start_date)}. Avance os dias para acompanhar eventos, governo e formação da base até a janela eleitoral.` : 'O calendário da campanha e do mandato continua avançando dia a dia. Novas atividades abrem no período eleitoral.'}</p>}
          {result && <div className="career-result-box"><div><span>NOTA DA ATIVIDADE</span><b>{result.score}/100</b></div><p>Pesquisa: {number.format(result.poll_support)}% · apoio no município: {number.format(result.local_support)}% · apoio estadual: {number.format(result.state_support)}%.</p>{result.activity?.conduct && <p className="career-conduct-result">{result.activity.conduct.summary}</p>}<div>{result.forecast?.map((item) => <article key={item.horizon}><b>{item.horizon}</b><span>{item.effect}</span></article>)}</div><details><summary>Ver os critérios da nota</summary><ul>{Object.entries(result.rubric).map(([key, value]) => <li key={key}>{key}: {value > 0 ? '+' : ''}{value}</li>)}</ul></details></div>}
          {result?.social_result && <div className={`career-social-result ${result.social_result.group_effect < 0 ? 'negative' : ''}`}><span>CANAL SIMULADO · {result.social_result.platform}</span><b>{result.social_result.event}</b><p>Chance estimada de alcance: {result.social_result.virality_pct}% · efeito de {result.social_result.group_effect > 0 ? '+' : ''}{number.format(result.social_result.group_effect)} p.p. entre {result.social_result.audience.join(' e ')}.</p><small>{result.social_result.explanation}</small></div>}
        </form>
        <aside className="panel career-rules"><span className="eyebrow">COMO A CAMPANHA FUNCIONA</span><ol><li>Uma ação a cada sete dias simulados.</li><li>Comícios e visitas consomem mais dias e alcançam mais eleitores.</li><li>Propostas com prazo, equipe, recurso e resultado verificável recebem melhor nota.</li><li>Promessas vagas e ataques pessoais reduzem credibilidade.</li><li>A votação considera apoio, organização, fadiga, dificuldade e variação eleitoral.</li></ol><div className="career-fund"><span>FUNDO RESTANTE</span><b>R$ {number.format(overview.campaign_fund_mi)} mi</b><small>Gasto registrado: R$ {number.format(overview.spent_mi)} mi</small></div></aside>
      </div>}

      {section === 'Mandato' && <div className="career-columns">
        <form className="panel career-action" onSubmit={govern}><div className="career-section-heading"><div><span className="eyebrow">DECISÕES DO CARGO</span><h3>Transforme autoridade em entrega</h3><p>As ações disponíveis dependem do cargo. A agenda libera uma decisão a cada 30 dias simulados.</p></div><span className="career-cooldown">{overview.governance_wait_days ? `EM ${overview.governance_wait_days} DIAS` : 'AGENDA ABERTA'}</span></div>
          {overview.governance_actions?.length ? <><label className="career-message-label">Ação<select value={governmentAction} onChange={(event) => setGovernmentAction(event.target.value)}>{overview.governance_actions.map((item) => <option value={item.key} key={item.key}>{item.label}{item.cost_mi ? ` · R$ ${number.format(item.cost_mi)} mi` : ''}</option>)}</select></label><label className="career-message-label">Assunto, política ou objeto da decisão<input value={governmentIssue} onChange={(event) => setGovernmentIssue(event.target.value)} maxLength={160} placeholder="Ex.: manutenção de escolas municipais" /></label><div className="career-form-footer"><small>{overview.governance_budget_mi ? `Reserva anual disponível: R$ ${number.format(overview.governance_budget_mi)} mi.` : `Capital político: ${number.format(overview.political_capital)} pontos.`} {overview.governance_wait_days ? `Próxima ação em ${overview.governance_wait_days} dias.` : 'A ação pode ser tomada agora.'}</small><button className="primary-button" disabled={busy || Boolean(overview.governance_wait_days)}>{busy ? 'Processando…' : 'Executar decisão'}</button></div></> : <div className="empty-state">Este cargo não tem uma ação de mandato disponível nesta etapa. A administração do Executivo e a atividade legislativa seguem atribuições diferentes.</div>}
          {governmentResult && <div className="career-result-box"><div><span>EFEITO REGISTRADO</span><b>{governmentResult.action?.status || 'ativo'}</b></div><p>{governmentResult.summary}</p>{governmentResult.governance?.outcomes && <div className="career-outcomes">{Object.entries(governmentResult.governance.outcomes).map(([key, value]) => <article key={key}><b>{key}</b><span>{number.format(value)}/100</span></article>)}</div>}</div>}
        </form>
        <aside className="panel career-rules"><span className="eyebrow">MANDATO EM CURSO</span><div className="career-countdown career-mandate-metrics"><div><span>FIM DO MANDATO</span><b>{dateLabel(overview.term_end)}</b></div><div><span>CONFIANÇA</span><b>{number.format(overview.governance?.trust ?? 50)}/100</b></div><div><span>ENTREGAS</span><b>{overview.governance?.delivery ?? 0}</b></div></div><h4>Programas e votações em curso</h4>{overview.governance?.pipeline?.length ? overview.governance.pipeline.map((item) => <article className="career-pipeline" key={item.id}><b>{item.title}</b><small>{item.kind === 'bill' ? 'Votação prevista' : 'Conclusão prevista'} · {dateLabel(item.due_date)}</small></article>) : <p className="empty-state">Nenhum programa ou proposta pendente.</p>}<p className="career-scope-note">Orçamento e resultados do cargo são estimativas do simulador. A reserva não representa o orçamento oficial de uma prefeitura, estado ou da União.</p></aside>
      </div>}

      {section === 'Apoio' && <section className="panel career-support"><div className="career-section-heading"><div><span className="eyebrow">PESQUISA SIMULADA</span><h3>Quem e onde está com a candidatura</h3><p>Apoio de grupos e território muda com cada atividade e com a passagem do tempo.</p></div><span className="career-support-total">{number.format(overview.poll_support)}%</span></div><div className="career-bars">{overview.groups.map((item) => <article key={item.key}><div><span>{item.label}</span><b>{number.format(item.support)}%</b></div><i><em style={{ width: `${item.support}%` }}/></i></article>)}</div><div className="career-area-card"><span>BASE ELEITORAL</span><b>{overview.municipality} · {overview.state_name}</b><small>{municipalityProfile ? `${number.format(municipalityProfile.population_estimate)} habitantes · estimativa IBGE ${municipalityProfile.population_reference_year} · ` : ''}{overview.electorate}. Candidatura e pesquisa inteiramente simuladas.</small>{overview.scope === 'municipal' && municipalityProfile && <small>Regra do jogo: o porte altera o alcance simulado de cada ação para ×{number.format(municipalityProfile.municipal_campaign_reach_multiplier)}. Não representa uma estimativa eleitoral oficial.</small>}</div></section>}

      {section === 'Histórico' && <section className="panel career-history"><span className="eyebrow">LINHA DO TEMPO</span><h3>Atividades, eleições e partidas arquivadas</h3>{overview.history?.map((item, index) => <article key={`${item.date}-${item.office}-${index}`}><div><b>{item.office} · {item.municipality}/{item.state_code}</b><span>{item.result === 'won' ? 'ELEITO' : item.result === 'lost' ? 'NÃO ELEITO' : 'MANDATO CONCLUÍDO'}</span></div><small>{dateLabel(item.date)} · {item.vote_share == null ? `${item.term_years} anos de mandato` : `${number.format(item.vote_share)}% dos votos`} · reputação ${number.format(item.reputation)}/100</small></article>)}{overview.activities.length ? (historyExpanded ? overview.activities : overview.activities.slice(0, 8)).map((item) => <article key={item.id}><div><b>{item.label} · {item.issue_label}</b><span>{item.score}/100</span></div><p>{item.message}</p><small>{dateLabel(item.date)} · {item.days_cost} dia(s) · R$ {number.format(item.cost_mi)} mi · apoio local {item.local_change > 0 ? '+' : ''}{number.format(item.local_change)} p.p.{item.municipality_id ? ` · alcance municipal simulado ×${number.format(item.city_reach_multiplier || 1)}` : ''}{item.social_result ? ` · ${item.social_result.platform}: ${item.social_result.event}` : ''}</small></article>) : <p className="empty-state">As atividades registradas durante a campanha aparecem aqui.</p>}{overview.activities.length > 8 && <button className="secondary-button career-history-more" onClick={() => setHistoryExpanded(!historyExpanded)}>{historyExpanded ? 'Mostrar menos atividades' : `Ver mais ${overview.activities.length - 8} atividades`}</button>}
        <div className="career-archives"><div><b>Partidas arquivadas</b><small>A partida atual foi guardada quando você iniciou uma nova carreira.</small></div><select value={selectedArchive} onChange={(event) => setSelectedArchive(event.target.value)}><option value="">Escolher partida para restaurar</option>{archives.map((item) => <option value={item.id} key={item.id}>{item.title} · {dateLabel(item.archived_at?.slice(0, 10))}</option>)}</select><button className="secondary-button" disabled={busy || !selectedArchive} onClick={restore}>Restaurar partida</button></div>
      </section>}
      {section === 'Dados do TSE' && <TSEArchivePanel request={request} stateCode={overview.state_code} />}
    </>}
    {!overview && archives.length > 0 && <section className="panel career-archive-shortcut"><b>Partidas arquivadas</b><select value={selectedArchive} onChange={(event) => setSelectedArchive(event.target.value)}><option value="">Restaurar uma partida anterior</option>{archives.map((item) => <option value={item.id} key={item.id}>{item.title}</option>)}</select><button className="secondary-button" disabled={busy || !selectedArchive} onClick={restore}>Restaurar</button></section>}
  </section>;
}
