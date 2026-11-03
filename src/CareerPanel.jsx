import { useEffect, useMemo, useState } from 'react';
import TSEArchivePanel from './TSEArchivePanel';
import MunicipalityPicker from './MunicipalityPicker';
import './career.css';
import './career-debate.css';

const number = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 1 });
const campaignTravelDays = (origin, destination) => {
  if (!origin || !destination || origin.municipality_id === destination.ibge_code) return 0;
  return origin.state_code === destination.state_code || origin.macroregion === destination.macroregion ? 1 : 2;
};
const dateLabel = (value) => value ? new Date(`${value}T12:00:00`).toLocaleDateString('pt-BR', { day: 'numeric', month: 'long', year: 'numeric' }) : '—';
const outcomeLabels = { education: 'Educação', health: 'Saúde', security: 'Segurança', mobility: 'Mobilidade', sanitation: 'Saneamento', infrastructure: 'Infraestrutura', employment: 'Emprego e renda' };
const promiseStatus = { pending: 'EM ACOMPANHAMENTO', fulfilled: 'CUMPRIDA', questioned: 'COBRADA', not_assessed: 'SEM AVALIAÇÃO' };
const spectrumIndex = { esquerda: 0, centro_esquerda: 1, centro: 2, centro_direita: 3, direita: 4 };
const ideologyToSpectrum = { Esquerda: 'esquerda', 'Centro-esquerda': 'centro_esquerda', Centro: 'centro', 'Centro-direita': 'centro_direita', Direita: 'direita' };
const bannedPartyTerms = ['nazista', 'nazismo', 'fascista', 'fascismo', 'nsdap'];

export default function CareerPanel({ state, request, onState, onNotice, busy, setBusy }) {
  const overview = state.career_overview;
  const municipalityProfile = overview?.municipality_profile;
  const currentCharacter = state.player_character || overview?.character || {};
  const [options, setOptions] = useState(null);
  const [archives, setArchives] = useState([]);
  const [section, setSection] = useState('Carreira');
  const [office, setOffice] = useState('vereador');
  const [stateCode, setStateCode] = useState('SP');
  const [municipality, setMunicipality] = useState('');
  const [municipalityId, setMunicipalityId] = useState('');
  const [party, setParty] = useState('Partido da Renovação');
  const [customParty, setCustomParty] = useState('');
  const [ideology, setIdeology] = useState('Centro');
  const [alignmentConfirmed, setAlignmentConfirmed] = useState(false);
  const [candidateName, setCandidateName] = useState('');
  const [activity, setActivity] = useState('comicio');
  const [conduct, setConduct] = useState('regular');
  const [issue, setIssue] = useState('economia');
  const [message, setMessage] = useState('');
  const [activityStateCode, setActivityStateCode] = useState('SP');
  const [activityMunicipality, setActivityMunicipality] = useState('');
  const [activityMunicipalityId, setActivityMunicipalityId] = useState('');
  const [activityMunicipalityProfile, setActivityMunicipalityProfile] = useState(null);
  const [result, setResult] = useState(null);
  const [preparationResult, setPreparationResult] = useState(null);
  const [preparationAction, setPreparationAction] = useState('mapear_prioridades');
  const [governmentAction, setGovernmentAction] = useState('');
  const [governmentIssue, setGovernmentIssue] = useState('');
  const [governmentResult, setGovernmentResult] = useState(null);
  const [showSetup, setShowSetup] = useState(!overview);
  const [selectedArchive, setSelectedArchive] = useState('');
  const [historyExpanded, setHistoryExpanded] = useState(false);
  const isPresidentialCampaign = office === 'presidente';
  const requiresCampaignCity = options?.offices.find((item) => item.key === office)?.scope === 'municipal';
  const selectedParty = party === '__custom__' ? customParty.trim() : party;
  const candidateSpectrum = currentCharacter.political_spectrum || 'centro';
  const alignmentGap = Math.abs((spectrumIndex[candidateSpectrum] ?? 2) - (spectrumIndex[ideologyToSpectrum[ideology]] ?? 2));
  const customPartyNormalized = customParty.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  const invalidCustomParty = party === '__custom__' && bannedPartyTerms.some((term) => customPartyNormalized.includes(term));
  const partyReady = Boolean(selectedParty && selectedParty.length >= 3 && !invalidCustomParty);

  useEffect(() => {
    let mounted = true;
    Promise.all([request('/api/career/options'), request('/api/game/archives')])
      .then(([catalog, saved]) => { if (mounted) { setOptions(catalog); setArchives(saved.items || []); setParty(catalog.parties?.[0] || 'MDB — Movimento Democrático Brasileiro'); } })
      .catch((error) => onNotice(error.message));
    return () => { mounted = false; };
  }, []);

  useEffect(() => {
    if (overview?.office) {
      setActivityStateCode(overview.office === 'presidente' ? 'SP' : overview.state_code || 'SP');
      setActivityMunicipality('');
      setActivityMunicipalityId('');
      setActivityMunicipalityProfile(null);
    }
  }, [overview?.office, overview?.state_code, state.campaign_id]);

  const chosenOffice = useMemo(() => options?.offices.find((item) => item.key === office), [options, office]);
  const chosenCalendar = useMemo(() => options?.calendar_previews?.[office], [options, office]);
  const chosenActivity = useMemo(() => overview?.activity_options?.find((item) => item.key === activity), [overview, activity]);
  const chosenPreparation = useMemo(() => overview?.preparation_options?.find((item) => item.key === preparationAction), [overview, preparationAction]);
  const previousPublicPoll = overview?.public_polls?.[1];
  const publicPollTrend = overview?.latest_public_poll && previousPublicPoll
    ? overview.latest_public_poll.candidate_support - previousPublicPoll.candidate_support
    : null;
  const campaignActivityLocation = overview?.scope === 'municipal'
    ? overview.municipality_profile
    : activityMunicipalityProfile;
  const travelDays = chosenActivity?.requires_travel
    ? campaignTravelDays(overview?.campaign_team_location, campaignActivityLocation)
    : 0;
  const campaignActivityDays = (chosenActivity?.days || 1) + travelDays;
  const chosenGovernmentAction = overview?.governance_actions?.find((item) => item.key === governmentAction);
  const sections = ['Carreira', ...(overview?.governing ? ['Mandato'] : []), 'Campanha', 'Apoio', 'Histórico', 'Dados do TSE'];

  useEffect(() => { if (!sections.includes(section)) setSection(sections[0]); }, [overview?.phase, overview?.governing]);
  useEffect(() => { if (!governmentAction && overview?.governance_actions?.length) setGovernmentAction(overview.governance_actions[0].key); }, [overview?.governance_actions]);

  async function start(event) {
    event.preventDefault();
    if (alignmentGap > 0 && !alignmentConfirmed) {
      onNotice('A linha escolhida para o partido diverge do espectro do personagem. Confirme para iniciar com esse atrito simulado.');
      return;
    }
    if (!partyReady) {
      onNotice(invalidCustomParty ? 'Esse nome não está disponível para partidos personalizados.' : 'Informe um nome para o partido da simulação.');
      return;
    }
    const archiveMessage = overview ? 'O personagem e o histórico permanecem na mesma carreira. Iniciar outra disputa?' : 'A partida atual será arquivada e poderá ser restaurada depois. Iniciar esta nova carreira?';
    const confirmed = window.confirm(archiveMessage);
    if (!confirmed) return;
    setBusy(true);
    try {
      const candidate = { ...currentCharacter, birth_state_code: currentCharacter.birth_municipality_id ? currentCharacter.birth_state_code : '', birth_municipality_id: currentCharacter.birth_municipality_id || null };
      const data = await request('/api/career/start', { method: 'POST', body: JSON.stringify({ office, state_code: isPresidentialCampaign ? 'DF' : stateCode, municipality: requiresCampaignCity || municipalityId ? municipality : '', municipality_id: requiresCampaignCity || municipalityId ? municipalityId : null, party: selectedParty, ideology, candidate_name: candidateName || currentCharacter.name || '', character: candidate, difficulty: state.difficulty || 'normal' }) });
      onState(data.state);
      if (!overview) {
        const saved = await request('/api/game/archives');
        setArchives(saved.items || []);
      }
      setShowSetup(false);
      setSection('Campanha');
      setResult(null);
      setPreparationResult(null);
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
      const data = await request('/api/career/action', { method: 'POST', body: JSON.stringify({
        activity_type: activity, issue, message, conduct,
        municipality_id: overview.scope === 'municipal' ? overview.municipality_id : activityMunicipalityId || null,
      }) });
      onState(data.state);
      setResult(data.result);
      setMessage('');
      onNotice(`${data.result.message}${data.calendar_message ? ` ${data.calendar_message}` : ''}`);
    } catch (error) { onNotice(error.message); }
    finally { setBusy(false); }
  }

  async function prepareCampaign(event) {
    event.preventDefault();
    setBusy(true);
    try {
      const data = await request('/api/career/preparation', { method: 'POST', body: JSON.stringify({ action: preparationAction }) });
      onState(data.state);
      setPreparationResult(data.result);
      onNotice(`${data.result.message}${data.calendar_message ? ` ${data.calendar_message}` : ''}`);
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
      onNotice(data.calendar_message ? `${data.result.summary} ${data.calendar_message}` : data.result.summary);
    } catch (error) { onNotice(error.message); }
    finally { setBusy(false); }
  }

  if (!options) return <section className="panel career-page"><p>Carregando as regras de carreira…</p></section>;

  const setup = <form className="career-setup panel" onSubmit={start}>
    <div className="career-section-heading"><div><span className="eyebrow">{overview ? 'NOVA DISPUTA · MESMO PERSONAGEM' : 'NOVA PARTIDA POLÍTICA'}</span><h2>{overview ? 'Escolha o próximo cargo' : 'Escolha onde começa sua carreira'}</h2><p>{overview ? `Sua trajetória fica registrada com ${overview.history?.length || 0} disputa(s) anterior(es). O mandato ou a transição atual não pode ser abandonado.` : 'A campanha, a eleição, o mandato e a oposição compartilham o mesmo calendário. A partida atual será arquivada antes da troca.'}</p></div><span className="career-step">1 / 3</span></div>
    <div className="career-form-grid">
      <label>Cargo<select value={office} onChange={(event) => { setOffice(event.target.value); setMunicipality(''); setMunicipalityId(''); setAlignmentConfirmed(false); }}>{options.offices.map((item) => <option value={item.key} key={item.key}>{item.label}</option>)}</select></label>
      {!isPresidentialCampaign && <label>Estado da candidatura<select value={stateCode} onChange={(event) => { setStateCode(event.target.value); setMunicipality(''); setMunicipalityId(''); }}>{options.states.map((item) => <option value={item.code} key={item.code}>{item.name}</option>)}</select></label>}
      {isPresidentialCampaign ? <p className="career-territory-note"><b>Território da eleição: Brasil</b><small>Não há uma cidade de campanha para a disputa presidencial.</small></p>
        : <MunicipalityPicker request={request} stateCode={stateCode} value={municipality} selectedId={municipalityId} required={Boolean(requiresCampaignCity)} label={requiresCampaignCity ? 'Cidade da candidatura' : 'Cidade de referência (opcional)'} onSelect={(item) => { setMunicipality(item.name); setMunicipalityId(item.id); }} />}
      <label>Partido da simulação<select value={party} onChange={(event) => { setParty(event.target.value); setAlignmentConfirmed(false); }}>{options.parties.map((item) => <option key={item} value={item}>{item}</option>)}<option value="__custom__">Criar partido fictício…</option></select></label>
      <label>Linha do partido na simulação<select value={ideology} onChange={(event) => { setIdeology(event.target.value); setAlignmentConfirmed(false); }}>{options.ideologies.map((item) => <option key={item}>{item}</option>)}</select></label>
      {party === '__custom__' && <label>Nome do partido fictício<input value={customParty} onChange={(event) => setCustomParty(event.target.value.slice(0, 60))} minLength={3} maxLength={60} placeholder="Ex.: Movimento Cívico" /><small className={invalidCustomParty ? 'field-error' : ''}>{invalidCustomParty ? 'Esse nome não está disponível.' : 'Evite nomes de ideologias extremistas ou ataques a grupos.'}</small></label>}
      <label>Nome na urna<input value={candidateName} onChange={(event) => setCandidateName(event.target.value)} maxLength={80} placeholder={overview?.candidate_name || 'Nome do personagem'} /></label>
    </div>
    <p className="party-data-note">A lista real contém apenas siglas e nomes publicados pelo TSE. A linha partidária é uma opção desta partida, sem atribuição oficial. <a href={options.party_source?.url} target="_blank" rel="noreferrer">Fonte TSE · {options.party_source?.checked_on}</a></p>
    {alignmentGap > 0 && <label className="party-alignment-warning"><span>O personagem está {alignmentGap} posição(ões) distante da linha escolhida para a legenda. O jogo simula atrito interno e pequena redução no apoio inicial; isso não afirma uma posição real do partido.</span><input type="checkbox" checked={alignmentConfirmed} onChange={(event) => setAlignmentConfirmed(event.target.checked)} /> Confirmo essa divergência para a simulação</label>}
    {chosenOffice && <div className="career-office-preview"><div><span>MANDATO</span><b>{chosenOffice.term_years} anos</b></div><div><span>ELEITORADO</span><b>{chosenOffice.electorate}</b></div><div><span>ESCOPO</span><b>{chosenOffice.scope === 'municipal' ? 'Município' : chosenOffice.scope === 'estadual' ? 'Estado' : 'País'}</b></div><div><span>PRÓXIMA ELEIÇÃO</span><b>{dateLabel(chosenCalendar?.election_date)}</b><small>Campanha abre em {dateLabel(chosenCalendar?.campaign_start)} · posse em {dateLabel(chosenCalendar?.inauguration_date)}</small></div><div className="career-powers"><span>O cargo permite</span><ul>{chosenOffice.powers.map((power) => <li key={power}>{power}</li>)}</ul></div></div>}
    <div className="career-setup-footer"><small>{options.simulated_notice}</small><button className="primary-button" disabled={busy || (requiresCampaignCity && !municipalityId) || !partyReady || (alignmentGap > 0 && !alignmentConfirmed)}>Iniciar carreira simulada <b>→</b></button></div>
  </form>;

  return <section className="career-page">
    {!overview || showSetup ? <>{setup}<details className="career-data-shortcut"><summary>Consultar candidaturas históricas do TSE</summary><TSEArchivePanel request={request} stateCode={stateCode} /></details></> : <>
      <header className="career-hero panel">
        <div className="career-hero-main"><span className="eyebrow">CARREIRA POLÍTICA · SIMULAÇÃO</span><h2>{overview.candidate_name}</h2><p>{overview.office_label} · {overview.campaign_territory || overview.state_name} · {overview.party} · {overview.ideology}</p><div className="career-tags"><span>{overview.phase === 'campaign' ? 'EM CAMPANHA' : overview.phase === 'runoff_campaign' ? '2º TURNO' : overview.phase === 'runoff_observer' ? 'AGUARDA 2º TURNO' : overview.phase === 'pre_campaign' ? 'PRÉ-CAMPANHA' : overview.phase === 'transition' && !overview.governing ? 'TRANSIÇÃO' : overview.governing ? (overview.phase === 'outgoing' ? 'GOVERNO DE SAÍDA' : 'NO CARGO') : overview.phase === 'opposition' ? 'NA OPOSIÇÃO' : 'MANDATO ENCERRADO'}</span><span>{overview.electorate}</span><span>ELEIÇÃO · {dateLabel(overview.election_date)}</span><span>REPUTAÇÃO · {number.format(overview.reputation)}/100</span></div>{overview.character?.birthplace && <div className="career-municipality-context"><b>Natural de {overview.character.birthplace.municipality}/{overview.character.birthplace.state_code}</b><span>Cidade natal do personagem; o território eleitoral é {overview.campaign_territory || overview.state_name}.</span></div>}{municipalityProfile && <div className="career-municipality-context"><b>{municipalityProfile.city_size_label} · {number.format(municipalityProfile.population_estimate)} habitantes</b><span>Estimativa municipal do IBGE, referência {municipalityProfile.population_reference_year} · código {municipalityProfile.ibge_code}</span></div>}</div>
        <div className="career-poll"><span>{overview.phase === 'runoff_campaign' ? 'PROJEÇÃO NO 2º TURNO' : overview.campaign_active ? 'INTENÇÃO DE VOTO' : overview.governing ? 'AVALIAÇÃO DO MANDATO' : overview.phase === 'pre_campaign' ? 'APOIO INICIAL' : 'INTENÇÃO DE VOTO'}</span><strong>{overview.phase === 'runoff_campaign' && overview.runoff_projection?.length ? `${number.format(overview.runoff_projection.find((item) => item.is_player)?.support || 0)}%` : overview.result ? `${number.format(overview.vote_share)}%` : `${number.format(overview.poll_support)}%`}</strong><small>{overview.phase === 'runoff_campaign' ? 'projeção atual ? não é pesquisa' : overview.result === 'won' ? 'vitória simulada' : overview.result === 'lost' ? 'resultado simulado' : overview.governing ? 'apoio ao mandato' : overview.phase === 'pre_campaign' ? `campanha abre em ${overview.days_until_campaign} dias` : `eleição em ${overview.days_until_election} dias`}</small></div>
      </header>
      <nav className="career-subnav" aria-label="Seções da carreira">{sections.map((item) => <button key={item} className={section === item ? 'active' : ''} onClick={() => setSection(item)}>{item}</button>)}<span/>{overview.can_start_campaign && <button onClick={() => setShowSetup(true)}>Nova candidatura</button>}</nav>

      {section === 'Carreira' && <div className="career-columns">
        <section className="panel career-status-panel">
          <span className="eyebrow">FASE ATUAL</span>
          <h3>{overview.phase === 'campaign' ? 'Construa apoio antes da votação' : overview.phase === 'runoff_campaign' ? 'Decida a reta final' : overview.phase === 'runoff_observer' ? 'A votação continua sem sua candidatura' : overview.phase === 'pre_campaign' ? 'Organize sua base antes da campanha' : overview.phase === 'transition' && !overview.governing ? 'Prepare a posse' : overview.governing ? `Mandato de ${overview.term_years} anos` : overview.phase === 'opposition' ? 'A disputa terminou; a carreira continua' : 'Mandato encerrado'}</h3>
          <p>{overview.phase === 'campaign' ? `A eleição para ${overview.office_label} acontece em ${dateLabel(overview.election_date)}. Cada atividade altera o apoio e avança o calendário.` : overview.phase === 'runoff_campaign' ? `Você avançou ao segundo turno, em ${dateLabel(overview.election_date)}. O mandato continua e a campanha pode realizar novas atividades.` : overview.phase === 'runoff_observer' ? `Você não avançou ao segundo turno. A disputa termina em ${dateLabel(overview.election_date)}; até lá, você continua no cargo e o governo segue funcionando.` : overview.phase === 'pre_campaign' ? `A eleição para ${overview.office_label} será em ${dateLabel(overview.election_date)}. A campanha oficial abre em ${dateLabel(overview.campaign_start_date)}; até lá, o calendário do país continua avançando.` : overview.phase === 'transition' && !overview.governing ? `A votação terminou. A posse simulada está prevista para ${dateLabel(overview.inauguration_date)}.` : overview.governing ? `Você ocupa o cargo até ${dateLabel(overview.term_end)}. A avaliação combina confiança, entregas e atividades de campanha.` : overview.result === 'lost' ? `Você recebeu ${number.format(overview.vote_share)}% dos votos simulados. A partida permanece ativa e o próximo passo pode ser uma nova disputa.` : 'O registro fica na carreira e você pode iniciar outra candidatura.'}</p>
          {(overview.phase === 'campaign' || overview.phase === 'runoff_campaign' || overview.phase === 'runoff_observer') && <div className="career-countdown"><div><span>{overview.phase === 'campaign' ? 'DIAS ATÉ A ELEIÇÃO' : 'DIAS ATÉ O 2º TURNO'}</span><b>{overview.days_until_election}</b></div><div><span>FUNDO SIMULADO</span><b>R$ {number.format(overview.campaign_fund_mi)} mi</b></div><div><span>APOIO NO TERRITÓRIO</span><b>{number.format(overview.local_support)}%</b></div></div>}
          {overview.runoff_active && <section className="career-runoff" aria-label="Resultado do primeiro turno">
            <div className="career-runoff-heading"><span className="eyebrow">ELEIÇÃO EM DOIS TURNOS · SIMULAÇÃO</span><h4>Apuração do primeiro turno</h4><p>{overview.phase === 'runoff_campaign' ? `As duas candidaturas mais votadas disputam a rodada final em ${dateLabel(overview.runoff_date)}.` : `As duas candidaturas mais votadas disputam a rodada final em ${dateLabel(overview.runoff_date)}. Você permanece no cargo até o fim do mandato.`}</p></div>
            <ol className="career-runoff-candidates">{overview.first_round_results?.map((candidate) => <li key={candidate.id} className={`${candidate.is_player ? 'player ' : ''}${overview.runoff_finalists?.some((item) => item.id === candidate.id) ? 'finalist' : ''}`}><span><b>{candidate.name}{candidate.is_player ? ' · você' : ''}</b><small>{candidate.party}{overview.runoff_finalists?.some((item) => item.id === candidate.id) ? ' · classificada(o)' : ''}</small></span><strong>{number.format(candidate.support)}%</strong></li>)}</ol>
            {overview.phase === 'runoff_campaign' && <small>Você pode seguir fazendo campanha. O segundo turno terá uma nova pesquisa e uma apuração própria.</small>}
          </section>}
          {overview.result && <div className={`career-result ${overview.result}`}><b>{overview.result === 'won' ? 'Vitória eleitoral simulada' : 'Derrota eleitoral simulada'}</b><span>{overview.runoff_results?.some((candidate) => candidate.is_player) ? `Votos no segundo turno: ${number.format(overview.vote_share)}%` : overview.runoff_results?.length ? `Sua votação no primeiro turno: ${number.format(overview.vote_share)}%` : `Votos: ${number.format(overview.vote_share)}% · maior concorrente: ${number.format(overview.opponent_share)}%`}</span>
            {overview.first_round_results?.length > 0 && <details className="career-candidate-results"><summary>Apuração do primeiro turno</summary><ol>{overview.first_round_results.map((candidate) => <li key={candidate.id}><span>{candidate.name} · {candidate.party}</span><b>{number.format(candidate.support)}%</b></li>)}</ol></details>}
            {overview.runoff_results?.length > 0 && <details className="career-candidate-results"><summary>Apuração do segundo turno</summary><ol>{overview.runoff_results.map((candidate) => <li key={candidate.id}><span>{candidate.name}{candidate.is_player ? ' · você' : ''} · {candidate.party}</span><b>{number.format(candidate.support)}%</b></li>)}</ol></details>}
            {!overview.first_round_results?.length && overview.candidate_results?.length > 0 && <details className="career-candidate-results"><summary>Ver a apuração das candidaturas simuladas</summary><ol>{overview.candidate_results.map((candidate) => <li key={candidate.id}><span>{candidate.name} · {candidate.party}{candidate.issue_focus_label && <small>Foco: {candidate.issue_focus_label}</small>}</span><b>{number.format(candidate.support)}%</b></li>)}</ol></details>}
            {overview.electoral_result?.system === 'proporcional_simulado' && <small>A legenda obteve {overview.electoral_result.party_seats} de {overview.electoral_result.district_magnitude} cadeiras simuladas; sua candidatura ocupava a primeira posição fictícia da lista. Distribuição proporcional simplificada.</small>}
            {overview.conduct_review?.attempts > 0 && <small>{overview.conduct_review.detected} irregularidade(s) detectada(s); revisão final {overview.conduct_review.reviewed ? 'aberta' : 'não aberta'}; penalidade de {number.format(overview.conduct_review.vote_penalty)} pontos.</small>}
          </div>}
        </section>
        <aside className="panel career-rules"><span className="eyebrow">PODERES DO CARGO</span><ul>{overview.powers.map((item) => <li key={item}>{item}</li>)}</ul><div className="career-appointment"><b>Outros caminhos</b>{overview.appointment_paths.map((item) => <p key={item.key} className={item.available ? 'available' : 'locked'}>{item.label}<small>{item.available ? item.description : `Disponível após exercer: ${item.requires.map((key) => options.offices.find((role) => role.key === key)?.label).join(', ')}`}</small></p>)}</div>{overview.can_start_campaign && <button className="secondary-button career-next-office" onClick={() => setShowSetup(true)}>Escolher próximo cargo</button>}</aside>
      </div>}

      {overview.latest_public_poll && (section === 'Campanha' || section === 'Apoio') && <section className="panel career-poll-card">
        <div><span className="eyebrow">PESQUISA PÚBLICA · {overview.latest_public_poll.round === 2 ? '2º TURNO' : 'SIMULAÇÃO'}</span><h3>{overview.latest_public_poll.candidate_name}: {number.format(overview.latest_public_poll.candidate_support)}%</h3><p>{overview.latest_public_poll.round === 2 ? 'Disputa simulada entre as duas candidaturas finalistas' : `Demais candidaturas: ${number.format(overview.latest_public_poll.other_candidates_support)}%`} · margem ±{number.format(overview.latest_public_poll.margin_of_error)} · amostra {number.format(overview.latest_public_poll.sample_size)}.</p>{overview.latest_public_poll.opponents?.length > 0 && <div className="career-poll-opponents"><span>OUTRAS CANDIDATURAS · SIMULADAS</span>{overview.latest_public_poll.opponents.map((candidate) => <article key={candidate.id}><b>{candidate.name}</b><small>{candidate.party} · foco: {candidate.issue_focus_label}</small><strong>{number.format(candidate.support)}%</strong></article>)}</div>}{publicPollTrend != null && <small>{publicPollTrend > 0 ? '+' : ''}{number.format(publicPollTrend)} p.p. desde {dateLabel(previousPublicPoll.date)}.</small>}<small>Levantamento fictício gerado pelas regras do jogo; não representa pesquisa real.</small></div>
        <details><summary>Evolução das pesquisas ({overview.public_polls.length})</summary><ol>{overview.public_polls.map((poll) => <li key={poll.date}><b>{dateLabel(poll.date)}</b><span>{number.format(poll.candidate_support)}% ±{number.format(poll.margin_of_error)} · n={number.format(poll.sample_size)}</span></li>)}</ol></details>
      </section>}
      {section === 'Campanha' && overview.phase === 'pre_campaign' && <div className="career-columns">
        <form className="panel career-action" onSubmit={prepareCampaign}>
          <div className="career-section-heading"><div><span className="eyebrow">PREPARAÇÃO INTERNA</span><h3>Monte a estrutura antes da campanha</h3><p>Essas atividades organizam a equipe. Não pedem votos, não publicam propaganda e não alteram a pesquisa.</p></div><span className="career-cooldown">{overview.can_prepare ? 'DISPONÍVEL' : overview.preparation_wait_days ? `EM ${overview.preparation_wait_days} DIAS` : 'BASE COMPLETA'}</span></div>
          <div className="career-preparation-meter"><div><b>Organização da equipe</b><strong>{number.format(overview.pre_campaign_organization)} / {number.format(overview.pre_campaign_organization_cap)}</strong></div><i><em style={{ width: `${Math.min(100, overview.pre_campaign_organization / overview.pre_campaign_organization_cap * 100)}%` }}/></i><small>Este componente só entra no cálculo do resultado eleitoral; não é intenção de voto.</small></div>
          {overview.can_prepare ? <>
            <label className="career-message-label">Atividade<select value={preparationAction} onChange={(event) => setPreparationAction(event.target.value)}>{overview.preparation_options.map((item) => <option value={item.key} key={item.key} disabled={!item.affordable}>{item.label} · {item.days} dia(s) · R$ {number.format(item.cost)} mi{item.affordable ? '' : ' · saldo insuficiente'}</option>)}</select></label>
            {chosenPreparation && <div className="career-action-preview"><b>{chosenPreparation.label}</b><p>{chosenPreparation.summary}</p><small>Organização: +{number.format(chosenPreparation.organization)} · Fundo da candidatura: R$ {number.format(chosenPreparation.cost)} mi · calendário: {chosenPreparation.days} dia(s). A próxima atividade interna libera 30 dias depois.</small></div>}
            <div className="career-form-footer"><small>O custo sai do fundo privado simulado da candidatura, não do orçamento público. A campanha oficial abre em {dateLabel(overview.campaign_start_date)}.</small><button className="primary-button" disabled={busy || !chosenPreparation?.affordable}>{busy ? 'Registrando…' : 'Realizar preparação'}</button></div>
          </> : <p className="empty-state">{overview.pre_campaign_organization >= overview.pre_campaign_organization_cap ? 'A equipe já chegou ao limite de preparação desta disputa.' : overview.preparation_wait_days ? `A próxima atividade interna pode ser feita em ${overview.preparation_wait_days} dia(s). O calendário continua avançando durante a pré-campanha.` : 'O fundo da candidatura não cobre as atividades de preparação disponíveis.'}</p>}
          {preparationResult && <div className="career-result-box"><div><span>EFEITO REGISTRADO</span><b>{number.format(preparationResult.organization)} / {number.format(overview.pre_campaign_organization_cap)}</b></div><p>{preparationResult.message}</p><small>{preparationResult.preparation.label} · R$ {number.format(preparationResult.preparation.cost_mi)} mi · {preparationResult.days_cost} dia(s) · a pesquisa não mudou.</small></div>}
        </form>
        <aside className="panel career-rules"><span className="eyebrow">ANTES DA JANELA ELEITORAL</span><h3>O que dá para fazer</h3><ol><li>Preparação interna: voluntariado, organização partidária ou diagnóstico territorial.</li><li>Uma atividade a cada 30 dias simulados; cada uma consome dias e fundo privado.</li><li>O bônus de organização é limitado e só entra no cálculo eleitoral.</li><li>Comícios, debates, entrevistas e mensagens públicas só aparecem na janela de 90 dias antes da eleição.</li></ol><div className="career-fund"><span>FUNDO DA CANDIDATURA</span><b>R$ {number.format(overview.campaign_fund_mi)} mi</b><small>Preparação e campanha usam este fundo separado do Tesouro.</small></div></aside>
      </div>}
      {section === 'Campanha' && overview.phase !== 'pre_campaign' && preparationResult && <div className="panel career-result-box"><div><span>PREPARAÇÃO PRÉ-CAMPANHA REGISTRADA</span><b>{number.format(preparationResult.organization)} / {number.format(overview.pre_campaign_organization_cap)}</b></div><p>{preparationResult.message}</p><small>Consulte o Histórico para ver todas as atividades internas.</small></div>}
      {section === 'Campanha' && overview.phase !== 'pre_campaign' && <div className="career-columns">
        <form className="panel career-action" onSubmit={act}><div className="career-section-heading"><div><span className="eyebrow">UMA AÇÃO DE CADA VEZ</span><h3>{overview.phase === 'runoff_observer' ? 'Você não avançou ao segundo turno' : overview.phase === 'runoff_campaign' ? 'Conquiste os votos restantes' : overview.campaign_active ? 'Fale com o eleitorado' : overview.phase === 'pre_campaign' ? 'A campanha ainda não abriu' : overview.phase === 'office' ? 'A eleição está fora da janela de campanha' : 'Campanha encerrada'}</h3></div><span className="career-cooldown">{overview.campaign_active ? overview.days_until_action ? `EM ${overview.days_until_action} DIAS` : 'DISPONÍVEL' : overview.phase === 'pre_campaign' ? `EM ${overview.days_until_campaign} DIAS` : overview.phase}</span></div>
          {overview.campaign_active ? <><div className="career-form-grid"><label>Atividade<select value={activity} onChange={(event) => setActivity(event.target.value)}>{overview.activity_options.map((item) => <option value={item.key} key={item.key}>{item.label} · {item.days} dia(s) · R$ {number.format(item.cost_mi)} mi</option>)}</select></label><label>Tema<select value={issue} onChange={(event) => setIssue(event.target.value)}>{overview.issue_options.map((item) => <option value={item.key} key={item.key}>{item.label}</option>)}</select></label></div>
            {overview.scope === 'municipal'
              ? <p className="career-territory-note"><b>Atividade em {overview.municipality || 'município da candidatura'}</b><small>A campanha municipal fica dentro do território em que a candidatura disputa votos.</small></p>
              : <div className="career-form-grid campaign-location-fields">
                {overview.office === 'presidente'
                  ? <label>Estado da agenda<select value={activityStateCode} onChange={(event) => { setActivityStateCode(event.target.value); setActivityMunicipality(''); setActivityMunicipalityId(''); setActivityMunicipalityProfile(null); }}>{options.states.map((item) => <option value={item.code} key={item.code}>{item.name}</option>)}</select></label>
                  : <p className="career-territory-note"><b>Estado da campanha: {overview.state_name}</b><small>Escolha em qual município desse estado acontecerá a atividade.</small></p>}
                <MunicipalityPicker request={request} stateCode={activityStateCode} value={activityMunicipality} selectedId={activityMunicipalityId} required label="Cidade da atividade" onSelect={(item) => { setActivityMunicipality(item.name); setActivityMunicipalityId(item.id); setActivityMunicipalityProfile(item.profile); }} />
              </div>}
            {activity === 'debate' && <div className="career-debate-prompt"><span>{overview.debate_prompts?.[issue]?.moderator || 'Mediação simulada'} · pergunta para {overview.debate_prompts?.[issue]?.scope || 'o território'}</span><b>{overview.debate_prompts?.[issue]?.question}</b><small>{overview.debate_prompts?.[issue]?.instruction}</small></div>}{chosenActivity?.requires_travel && campaignActivityLocation && <div className="career-action-preview"><b>Deslocamento da equipe</b><p>{overview.campaign_team_location?.name || 'Base da campanha'} &rarr; {campaignActivityLocation.name}/{campaignActivityLocation.state_code}</p><small>{travelDays ? `A viagem acrescenta ${travelDays} dia(s) ao calend\u00e1rio. Regra simulada: 1 dia dentro da UF ou macroregi\u00e3o; 2 dias entre macroregi\u00f5es.` : 'Sem deslocamento adicional para esta atividade.'}</small></div>}<details className="career-conduct"><summary>Conduta eleitoral · padrão dentro das regras</summary><label>Forma de conduzir a atividade<select value={conduct} onChange={(event) => setConduct(event.target.value)}><option value="regular">Dentro das regras</option><option value="irregular">Atalho irregular (simulação)</option></select></label><p>{conduct === 'irregular' ? `Detecção: ${number.format(overview.conduct_preview?.detection_pct || 0)}%. Revisão final após esta ação: ${number.format(overview.conduct_preview?.review_if_not_detected_pct || 0)}% a ${number.format(overview.conduct_preview?.review_if_detected_pct || 0)}%. Efeito agora: +0,6 p.p. se não detectada ou −3 p.p. se detectada.` : 'Sem risco adicional de sanção eleitoral.'} {overview.conduct_preview?.notice}</p></details><label className="career-message-label">Fala, proposta ou resposta<textarea value={message} onChange={(event) => setMessage(event.target.value)} maxLength={600} minLength={12} placeholder={activity === 'debate' ? 'Responda diretamente à pergunta: diga a ação, o prazo e como será fiscalizada.' : 'Diga qual problema você quer resolver, como vai agir e que resultado o eleitor poderá cobrar.'} required /></label><div className="career-form-footer"><small>{message.length}/600 · {campaignActivityDays} dia(s) de calendário{chosenActivity?.requires_travel ? ` (inclui ${travelDays} de viagem)` : ''} e R$ {number.format(chosenActivity?.cost_mi || 0)} mi do fundo de campanha.</small><button className="primary-button" disabled={busy || !overview.can_act || message.trim().length < 12 || (overview.scope !== 'municipal' && !activityMunicipalityId)}>{busy ? 'Calculando…' : overview.can_act ? 'Realizar atividade' : overview.days_until_action ? `Agenda em ${overview.days_until_action} dia(s)` : 'Ação indisponível'}</button></div></> : <p className="empty-state">{overview.phase === 'pre_campaign' ? `A campanha oficial abre em ${dateLabel(overview.campaign_start_date)}. Avance os dias para acompanhar eventos, governo e formação da base até a janela eleitoral.` : overview.phase === 'runoff_observer' ? 'Você não está entre os finalistas e não pode fazer campanha neste turno. Se ocupa um cargo, continua governando até o fim do mandato.' : overview.phase === 'runoff_campaign' ? 'A rodada final acontece em breve. Escolha uma atividade que caiba nos dias e no fundo restantes.' : 'O calendário da campanha e do mandato continua avançando dia a dia. Novas atividades abrem no período eleitoral.'}</p>}
          {result && <div className="career-result-box"><div><span>NOTA DA ATIVIDADE</span><b>{result.score}/100</b></div><p>Pesquisa: {number.format(result.poll_support)}% · apoio local: {number.format(result.local_support)}% · apoio estadual: {number.format(result.state_support)}%.</p>{result.activity?.travel_days > 0 && <p>Deslocamento: <b>{result.activity.travel_from_municipality_name} &rarr; {result.activity.municipality_name}</b> +{result.activity.travel_days} dia(s); total da atividade: {result.activity.days_cost} dia(s).</p>}{result.activity?.municipality_name && <p>Local da atividade: <b>{result.activity.municipality_name}/{result.activity.municipality_state_code}</b>{result.municipality_support != null ? ` · apoio simulado na cidade: ${number.format(result.municipality_support)}%` : ''} · alcance ×{number.format(result.activity.city_reach_multiplier || 1)}.</p>}{result.debate && <div className={`career-debate-result ${result.debate.outcome}`}><span>DEBATE SIMULADO · {result.debate.outcome === 'won' ? 'VOCÊ FOI MELHOR' : result.debate.outcome === 'lost' ? 'RÉPLICA ADVERSÁRIA MELHOR' : 'EMPATE TÉCNICO'}</span><b>{result.debate.player_score} × {result.debate.opponent_score}</b><p><strong>Réplica adversária simulada:</strong> {result.debate.opponent_reply}</p><p>{result.debate.explanation} Pesquisa: {result.debate.support_delta > 0 ? '+' : ''}{number.format(result.debate.support_delta)} p.p.</p><small>{result.debate.question}</small></div>}{result.activity?.conduct && <p className="career-conduct-result">{result.activity.conduct.summary}</p>}<div>{result.forecast?.map((item) => <article key={item.horizon}><b>{item.horizon}</b><span>{item.effect}</span></article>)}</div><details><summary>Ver os critérios da nota</summary><ul>{Object.entries(result.rubric).map(([key, value]) => <li key={key}>{key}: {value > 0 ? '+' : ''}{value}</li>)}</ul></details></div>}
          {result?.social_result && <div className={`career-social-result ${result.social_result.group_effect < 0 ? 'negative' : ''}`}><span>CANAL SIMULADO · {result.social_result.platform}</span><b>{result.social_result.event}</b><p>Chance estimada de alcance: {result.social_result.virality_pct}% · efeito de {result.social_result.group_effect > 0 ? '+' : ''}{number.format(result.social_result.group_effect)} p.p. entre {result.social_result.audience.join(' e ')}.</p><small>{result.social_result.explanation}</small></div>}
          {result?.campaign_promise && <div className="career-promise-result"><span>{result.campaign_promise.status === 'not_recorded' ? 'COMPROMISSO NÃO REGISTRADO' : 'COMPROMISSO REGISTRADO'} · {result.campaign_promise.issue_label}</span><p>“{result.campaign_promise.statement}”</p><small>{result.campaign_promise.evidence_rule}{result.campaign_promise.status !== 'not_recorded' ? ` Revisão prevista: ${dateLabel(result.campaign_promise.review_date) === '—' ? 'quando você assumir um cargo e completar o primeiro ciclo anual' : dateLabel(result.campaign_promise.review_date)}. A cobrança é gerada por regras do simulador.` : ''}</small></div>}
        </form>
        <aside className="panel career-rules"><span className="eyebrow">COMO A CAMPANHA FUNCIONA</span><ol><li>Uma ação a cada sete dias simulados.</li><li>Comícios e visitas consomem mais dias e alcançam mais eleitores.</li><li>Propostas com prazo, equipe, recurso e resultado verificável recebem melhor nota.</li><li>Promessas vagas e ataques pessoais reduzem credibilidade.</li><li>A votação considera apoio, organização, fadiga, dificuldade e variação eleitoral.</li></ol><div className="career-fund"><span>FUNDO RESTANTE</span><b>R$ {number.format(overview.campaign_fund_mi)} mi</b><small>Gasto registrado: R$ {number.format(overview.spent_mi)} mi</small></div></aside>
      </div>}

      {section === 'Mandato' && <div className="career-columns">
        <form className="panel career-action" onSubmit={govern}><div className="career-section-heading"><div><span className="eyebrow">DECISÕES DO CARGO</span><h3>{overview.phase === 'outgoing' ? 'Governo de saída' : 'Transforme autoridade em entrega'}</h3><p>As ações disponíveis dependem do cargo. A agenda libera uma decisão a cada 30 dias simulados.</p></div><span className="career-cooldown">{overview.governance_wait_days ? `EM ${overview.governance_wait_days} DIAS` : 'AGENDA ABERTA'}</span></div>
          {overview.governance_actions?.length ? <><label className="career-message-label">Ação<select value={governmentAction} onChange={(event) => setGovernmentAction(event.target.value)}>{overview.governance_actions.map((item) => <option value={item.key} key={item.key}>{item.label}{item.cost_mi ? ` · R$ ${number.format(item.cost_mi)} mi` : ''}</option>)}</select></label>{chosenGovernmentAction && <div className="career-action-preview"><b>{chosenGovernmentAction.label}</b><p>{chosenGovernmentAction.summary}</p><small>{chosenGovernmentAction.cost_mi ? `Custo previsto: R$ ${number.format(chosenGovernmentAction.cost_mi)} milhões · previsão de entrega: ${chosenGovernmentAction.days} dias.` : chosenGovernmentAction.capital ? `Capital político: ${number.format(chosenGovernmentAction.capital)} pontos · ` : ''}{!chosenGovernmentAction.cost_mi && !chosenGovernmentAction.capital ? `Conclusão prevista em ${chosenGovernmentAction.days ?? 1} dia(s).` : ''}</small></div>}<label className="career-message-label">Assunto, política ou objeto da decisão<input value={governmentIssue} onChange={(event) => setGovernmentIssue(event.target.value)} maxLength={160} placeholder="Ex.: manutenção de escolas municipais" /></label><div className="career-form-footer"><small>{overview.governance_annual_budget_mi ? overview.governance_budget_source === 'federal_investment' ? `Investimentos federais: R$ ${number.format(overview.governance_budget_mi)} mi disponíveis de R$ ${number.format(overview.governance_annual_budget_mi)} mi · R$ ${number.format(overview.governance_investment_commitment_mi)} mi comprometidos. ` : `Reserva anual: R$ ${number.format(overview.governance_budget_mi)} de R$ ${number.format(overview.governance_annual_budget_mi)} mi · preços ×${number.format(overview.governance_budget_price_index)}. ` : `Capital político: ${number.format(overview.political_capital)} pontos. `}{overview.governance_wait_days ? `Próxima decisão em ${overview.governance_wait_days} dias.` : 'A ação pode ser tomada agora.'}</small><button className="primary-button" disabled={busy || Boolean(overview.governance_wait_days)}>{busy ? 'Processando…' : 'Executar decisão'}</button></div></> : <div className="empty-state">Este cargo não tem uma ação de mandato disponível nesta etapa. A administração do Executivo e a atividade legislativa seguem atribuições diferentes.</div>}
          {governmentResult && <div className="career-result-box"><div><span>EFEITO REGISTRADO</span><b>{governmentResult.action?.status || 'ativo'}</b></div><p>{governmentResult.summary}</p>{governmentResult.governance?.outcomes && <div className="career-outcomes">{Object.entries(governmentResult.governance.outcomes).map(([key, value]) => <article key={key}><b>{outcomeLabels[key] || key}</b><span>{number.format(value)}/100</span></article>)}</div>}</div>}
        </form>
        <aside className="panel career-rules"><span className="eyebrow">MANDATO EM CURSO</span><div className="career-countdown career-mandate-metrics"><div><span>FIM DO MANDATO</span><b>{dateLabel(overview.term_end)}</b></div><div><span>CONFIANÇA</span><b>{number.format(overview.governance?.trust ?? 50)}/100</b></div><div><span>ENTREGAS</span><b>{overview.governance?.delivery ?? 0}</b></div></div><div className="career-area-card"><span>TERRITÓRIO ADMINISTRADO · {overview.governance_territory?.scope}</span><b>{overview.governance_territory?.name}</b></div><h4>Indicadores acumulados</h4><div className="career-territory-outcomes">{Object.entries(overview.governance?.outcomes || {}).map(([key, value]) => <article key={key}><b>{outcomeLabels[key] || key}</b><span>{number.format(value)}/100</span></article>)}</div><h4>Programas e votações em curso</h4>{overview.governance?.pipeline?.length ? overview.governance.pipeline.map((item) => <article className="career-pipeline" key={item.id}><b>{item.title}</b><small>{item.territory ? `${item.territory_scope} · ${item.territory} · ` : ''}{item.kind === 'bill' ? 'Votação prevista' : 'Conclusão prevista'} · {dateLabel(item.due_date)}</small></article>) : <p className="empty-state">Nenhum programa ou proposta pendente.</p>}<p className="career-scope-note">Orçamento e resultados do cargo são estimativas do simulador. A reserva não representa o orçamento oficial de uma prefeitura, estado ou da União.</p></aside>
      </div>}

      {section === 'Mandato' && overview.public_reports?.length > 0 && <section className="panel career-history career-public-reports"><span className="eyebrow">TRANSPARÊNCIA DO MANDATO</span><h3>Prestações de contas publicadas</h3><p>Snapshots simulados dos registros do jogo; valores não representam execução oficial.</p>{overview.public_reports.map((report) => <article key={report.id}><div><b>{report.office} · {report.territory}</b><span>SIMULADO</span></div><small>Período {dateLabel(report.period_start)} a {dateLabel(report.period_end)} · R$ {number.format(report.programs_reserved_mi)} mi reservados de R$ {number.format(report.annual_budget_mi)} mi no orçamento anual</small><small>Disponível: R$ {number.format(report.budget_available_mi)} mi · {report.budget_committed_label}: R$ {number.format(report.budget_committed_mi)} mi</small><small>{report.programs_started} iniciado(s) · {report.programs_completed} concluído(s) · {report.programs_in_progress} em andamento</small>{Object.keys(report.outcomes || {}).length > 0 && <small>Indicadores no fechamento: {Object.entries(report.outcomes).map(([key, value]) => `${outcomeLabels[key] || key} ${number.format(value)}/100`).join(' · ')}</small>}</article>)}</section>}
      {section === 'Histórico' && overview.campaign_promises?.length > 0 && <section className="panel career-history career-promises"><span className="eyebrow">PROMESSAS E COBRANÇAS SIMULADAS</span><h3>O que a campanha deixou em aberto</h3><p>O jogo registra falas com compromisso explícito. Após um ano no cargo, confere indicadores e entregas do próprio save e publica uma notícia simulada.</p>{overview.campaign_promises.map((promise) => <article key={promise.id}><div><b>{promise.issue_label}</b><span>{promiseStatus[promise.status] || promise.status}</span></div><p>“{promise.statement}”</p><small>{promise.evidence_rule}{promise.review_date ? ` · revisão em ${dateLabel(promise.review_date)}` : ' · aguarda o primeiro mandato do personagem'}{promise.reviewed_on ? ` · variação observada: ${promise.observed_change > 0 ? '+' : ''}${number.format(promise.observed_change)} ${promise.metric_label}` : ''}</small></article>)}</section>}

      {section === 'Apoio' && <section className="panel career-support"><div className="career-section-heading"><div><span className="eyebrow">PESQUISA SIMULADA</span><h3>Quem e onde está com a candidatura</h3><p>Apoio de grupos e território muda com cada atividade e com a passagem do tempo.</p></div><span className="career-support-total">{number.format(overview.poll_support)}%</span></div><div className="career-bars">{overview.groups.map((item) => <article key={item.key}><div><span>{item.label}</span><b>{number.format(item.support)}%</b></div><i><em style={{ width: `${item.support}%` }}/></i></article>)}</div><div className="career-area-card"><span>BASE ELEITORAL</span><b>{overview.campaign_territory || overview.state_name}</b><small>{municipalityProfile ? `${number.format(municipalityProfile.population_estimate)} habitantes · estimativa IBGE ${municipalityProfile.population_reference_year} · ` : ''}{overview.electorate}. Candidatura e pesquisa inteiramente simuladas.</small>{overview.scope === 'municipal' && municipalityProfile && <small>Regra do jogo: o porte altera o alcance simulado de cada ação para ×{number.format(municipalityProfile.municipal_campaign_reach_multiplier)}. Não representa uma estimativa eleitoral oficial.</small>}</div>{overview.campaign_city_support?.length > 0 && <div><span className="eyebrow">CIDADES ONDE A CAMPANHA ATUOU</span><div className="career-territory-outcomes">{overview.campaign_city_support.map((item) => <article key={item.municipality_id}><b>{item.municipality_name}/{item.state_code}</b><span>{number.format(item.support)}%</span></article>)}</div></div>}</section>}

      {section === 'Histórico' && <section className="panel career-history"><span className="eyebrow">LINHA DO TEMPO</span><h3>Atividades, eleições e partidas arquivadas</h3>{overview.history?.map((item, index) => <article key={`${item.date}-${item.office}-${index}`}><div><b>{item.office} · {item.territory || `${item.municipality || item.state_code}`}</b><span>{item.result === 'won' ? 'ELEITO' : item.result === 'lost' ? 'NÃO ELEITO' : 'MANDATO CONCLUÍDO'}</span></div><small>{dateLabel(item.date)} · {item.vote_share == null ? `${item.term_years} anos de mandato` : `${number.format(item.vote_share)}% dos votos`} · reputação ${number.format(item.reputation)}/100</small></article>)}{overview.activities.length ? (historyExpanded ? overview.activities : overview.activities.slice(0, 8)).map((item) => <article key={item.id}><div><b>{item.label} · {item.issue_label}</b><span>{item.score}/100</span></div><p>{item.message}</p><small>{dateLabel(item.date)} · {item.days_cost} dia(s) · R$ {number.format(item.cost_mi)} mi · apoio local {item.local_change > 0 ? '+' : ''}{number.format(item.local_change)} p.p.{item.municipality_name ? ` · ${item.municipality_name}/${item.municipality_state_code}` : ''}{item.travel_days > 0 ? ` - viagem ${item.travel_from_municipality_name || 'base'} -> ${item.municipality_name} (+${item.travel_days} dias)` : ''}{item.municipality_id ? ` · alcance simulado ×${number.format(item.city_reach_multiplier || 1)}` : ''}{item.social_result ? ` · ${item.social_result.platform}: ${item.social_result.event}` : ''}</small></article>) : <p className="empty-state">As atividades registradas durante a campanha aparecem aqui.</p>}{overview.activities.length > 8 && <button className="secondary-button career-history-more" onClick={() => setHistoryExpanded(!historyExpanded)}>{historyExpanded ? 'Mostrar menos atividades' : `Ver mais ${overview.activities.length - 8} atividades`}</button>}
        <div className="career-archives"><div><b>Partidas arquivadas</b><small>A partida atual foi guardada quando você iniciou uma nova carreira.</small></div><select value={selectedArchive} onChange={(event) => setSelectedArchive(event.target.value)}><option value="">Escolher partida para restaurar</option>{archives.map((item) => <option value={item.id} key={item.id}>{item.title} · {dateLabel(item.archived_at?.slice(0, 10))}</option>)}</select><button className="secondary-button" disabled={busy || !selectedArchive} onClick={restore}>Restaurar partida</button></div>
      </section>}
      {section.startsWith('Hist') && overview.pre_campaign_preparations?.length > 0 && <section className="panel career-history"><span className="eyebrow">ORGANIZAÇÃO PRÉ-CAMPANHA</span><h3>Preparação da equipe</h3>{overview.pre_campaign_preparations.map((item) => <article key={item.id}><div><b>{item.label}</b><span>+{number.format(item.organization_gain)} organização</span></div><p>{item.summary}</p><small>{dateLabel(item.date)} · {item.days_cost} dia(s) · R$ {number.format(item.cost_mi)} mi · sem mudança imediata na pesquisa</small></article>)}</section>}
      {section === 'Dados do TSE' && <TSEArchivePanel request={request} stateCode={overview.state_code} />}
    </>}
    {!overview && archives.length > 0 && <section className="panel career-archive-shortcut"><b>Partidas arquivadas</b><select value={selectedArchive} onChange={(event) => setSelectedArchive(event.target.value)}><option value="">Restaurar uma partida anterior</option>{archives.map((item) => <option value={item.id} key={item.id}>{item.title}</option>)}</select><button className="secondary-button" disabled={busy || !selectedArchive} onClick={restore}>Restaurar</button></section>}
  </section>;
}
