import { useEffect, useMemo, useState } from 'react';
import MunicipalityPicker from './MunicipalityPicker';
import Brand from './Brand';

const difficultyOptions = [
  ['tranquilo', 'Tranquilo'], ['normal', 'Normal'], ['dificil', 'Difícil'],
  ['complicado', 'Complicado'], ['realismo_puro', 'Realismo puro'],
];
const difficultyDescriptions = {
  tranquilo: 'Mais margem para recuperar apoio e orçamento; eventos dão avisos claros.',
  normal: 'Pressão equilibrada, com consequências graduais e tempo para reagir.',
  dificil: 'Menos folga política e fiscal; oposição e choques aparecem com mais frequência.',
  complicado: 'Pouca margem para erro; efeitos acumulados exigem planejamento.',
  realismo_puro: 'Parâmetros mais voláteis e consequências persistentes; continua sendo um cenário fictício.',
};
const spectra = [
  ['esquerda', 'Esquerda'], ['centro_esquerda', 'Centro-esquerda'], ['centro', 'Centro'],
  ['centro_direita', 'Centro-direita'], ['direita', 'Direita'],
];
const familyOptions = [
  ['trabalhadora', 'Família trabalhadora'], ['classe_media', 'Classe média'],
  ['empreendedora', 'Pequeno negócio'], ['rural', 'Origem rural'],
  ['servidora_publica', 'Serviço público'], ['politica', 'Família ligada à política'],
  ['educadora', 'Educação e cuidado'], ['oficios', 'Ofícios e comércio'], ['lideranca_comunitaria', 'Liderança comunitária'],
];
const customOptions = [
  ['vida_comunitaria', 'Vida comunitária'], ['vida_urbana', 'Cotidiano urbano'],
  ['vida_rural', 'Cotidiano rural'], ['fe_presente', 'Fé presente na comunidade'],
  ['cultura_popular', 'Cultura popular'], ['vida_sindical', 'Participação sindical'],
  ['voluntariado', 'Voluntariado'], ['esporte_local', 'Esporte local'], ['migracao', 'História de migração'],
];
const axisOptions = {
  economic_axis: [['estado_social', 'Mais presença do Estado'], ['equilibrio', 'Equilíbrio'], ['mercado', 'Mais espaço ao mercado']],
  social_axis: [['liberdades', 'Liberdades individuais'], ['comunidade', 'Valores comunitários'], ['tradicao', 'Tradição']],
  territorial_axis: [['municipalista', 'Decisões mais locais'], ['federativa', 'Equilíbrio entre entes'], ['nacional', 'Coordenação nacional']],
};
const axisLabels = { economic_axis: 'Economia', social_axis: 'Costumes e direitos', territorial_axis: 'Organização do país' };
const spectrumIndex = { esquerda: 0, centro_esquerda: 1, centro: 2, centro_direita: 3, direita: 4 };
const ideologyToSpectrum = { Esquerda: 'esquerda', 'Centro-esquerda': 'centro_esquerda', Centro: 'centro', 'Centro-direita': 'centro_direita', Direita: 'direita' };
const bannedPartyTerms = ['nazista', 'nazismo', 'fascista', 'fascismo', 'nsdap'];
const tutorialSteps = [
  ['Escolha o caminho', 'Posse direta começa no governo. Carreira política começa numa eleição e pode seguir por outros cargos.'],
  ['Monte seu personagem', 'A cidade natal é opcional e diferente do território da candidatura. Município de campanha só é obrigatório para vereador e prefeito.'],
  ['Leia antes de decidir', 'O painel mostra indicadores essenciais. As outras áreas ficam agrupadas nas abas temáticas.'],
  ['Avance o calendário', 'Uma ação pode gastar dias. Veja o efeito imediato e os riscos futuros antes de confirmar medidas.'],
];
const traitOptions = [
  ['carismatica', 'Carismática', '+1 ponto de aprovação na posse; +0,5 de apoio inicial e +0,15 ponto local por ação na campanha.'],
  ['tecnica', 'Técnica', '+1 de confiança institucional na posse; até +3 pontos em falas concretas.'],
  ['conciliadora', 'Conciliadora', '+1 de apoio no Congresso na posse; pequeno ganho entre grupos alcançados.'],
  ['combativa', 'Combativa', '+0,5 de aprovação e −0,5 de confiança na posse; mais alcance e desgaste.'],
  ['gestora', 'Gestora', '+1 de capacidade de governar na posse; ações de campanha custam 10% menos.'],
  ['comunitaria', 'Comunitária', '+0,5 de aprovação na posse; pequeno ganho entre grupos alcançados.'],
];
const blankCharacter = { name: '', political_spectrum: 'centro', family_background: 'classe_media', customs: [], traits: [], biography: '', economic_axis: 'equilibrio', social_axis: 'liberdades', territorial_axis: 'federativa', birth_state_code: '', birth_municipality_id: null };
const spectrumSupport = {
  esquerda: { trabalhadores: 2, servidores: 1, negocios: -1 }, centro_esquerda: { trabalhadores: 1.2, familias: .7 },
  centro: { familias: .4 }, centro_direita: { negocios: 1, rural: .6 }, direita: { negocios: 1.8, rural: 1, servidores: -.6 },
};
const familySupport = {
  trabalhadora: { trabalhadores: 1.2, familias: .5 }, classe_media: { familias: .6, negocios: .4 },
  empreendedora: { negocios: 1.2 }, rural: { rural: 1.4, trabalhadores: .3 },
  servidora_publica: { servidores: 1.2, familias: .3 }, politica: { servidores: .3, negocios: .3 },
  educadora: { familias: .7, servidores: .6 }, oficios: { trabalhadores: .8, negocios: .4 }, lideranca_comunitaria: { familias: .5, trabalhadores: .5 },
};
const supportLabels = { trabalhadores: 'Trabalhadores', negocios: 'Pequenos negócios', familias: 'Famílias', servidores: 'Servidores', rural: 'População rural' };

function toggleLimited(items, value, limit) {
  if (items.includes(value)) return items.filter((item) => item !== value);
  return items.length < limit ? [...items, value] : items;
}

export default function GameSetupPanel({ state, request, onState, onContinue, busy, setBusy, authConfig, authUser, onSignIn, onAccount }) {
  const [catalog, setCatalog] = useState(null);
  const [archives, setArchives] = useState([]);
  const [campaigns, setCampaigns] = useState([]);
  const [mode, setMode] = useState('');
  const [office, setOffice] = useState('vereador');
  const [stateCode, setStateCode] = useState('SP');
  const [municipality, setMunicipality] = useState('');
  const [municipalityId, setMunicipalityId] = useState('');
  const [party, setParty] = useState('');
  const [customParty, setCustomParty] = useState('');
  const [ideology, setIdeology] = useState('Centro');
  const [alignmentConfirmed, setAlignmentConfirmed] = useState(false);
  const [character, setCharacter] = useState(blankCharacter);
  const [difficulty, setDifficulty] = useState(state.difficulty || 'normal');
  const [selectedArchive, setSelectedArchive] = useState('');
  const [campaignName, setCampaignName] = useState('');
  const [notice, setNotice] = useState('');
  const [tutorialStep, setTutorialStep] = useState(-1);

  useEffect(() => {
    let mounted = true;
    Promise.all([request('/api/career/options?fresh=true'), request('/api/game/archives'), request('/api/campaigns')])
      .then(([career, saved, savedCampaigns]) => {
        if (!mounted) return;
        setCatalog(career);
        setArchives(saved.items || []);
        setCampaigns(savedCampaigns.items || []);
        setParty(career.parties?.[0] || 'MDB — Movimento Democrático Brasileiro');
      })
      .catch((error) => { if (mounted) setNotice(error.message); });
    return () => { mounted = false; };
  }, []);

  const chosenOffice = useMemo(() => catalog?.offices.find((item) => item.key === office), [catalog, office]);
  const isPresidentialCampaign = office === 'presidente';
  const requiresCampaignCity = chosenOffice?.scope === 'municipal';
  const selectedParty = party === '__custom__' ? customParty.trim() : party;
  const candidateSpectrum = character.political_spectrum || 'centro';
  const alignmentGap = Math.abs((spectrumIndex[candidateSpectrum] ?? 2) - (spectrumIndex[ideologyToSpectrum[ideology]] ?? 2));
  const customPartyNormalized = customParty.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  const invalidCustomParty = party === '__custom__' && bannedPartyTerms.some((term) => customPartyNormalized.includes(term));
  const partyReady = Boolean(selectedParty && selectedParty.length >= 3 && !invalidCustomParty);
  const preview = catalog?.calendar_previews?.[office];
  const hasSavedGame = Boolean(state && !state.setup_pending);
  const heroImage = mode === 'career' && ['AC', 'AP', 'AM', 'PA', 'RO', 'RR', 'TO'].includes(stateCode)
    ? 'porto-amazonico.jpg' : mode === 'career' ? 'praca-campanha.jpg' : 'brasilia-amanhecer.jpg';
  const initialSupport = { ...spectrumSupport[character.political_spectrum], ...{} };
  Object.entries(familySupport[character.family_background] || {}).forEach(([group, amount]) => { initialSupport[group] = (initialSupport[group] || 0) + amount; });
  const setCharacterField = (key, value) => setCharacter((current) => ({ ...current, [key]: value }));
  const updateMode = (next) => setMode((current) => current === next ? '' : next);
  const characterForRequest = () => ({ ...character,
    birth_state_code: character.birth_municipality_id ? character.birth_state_code : '',
    birth_municipality_id: character.birth_municipality_id || null,
  });

  async function startPresidency(event) {
    event.preventDefault();
    setBusy(true); setNotice('');
    try {
      const data = await request('/api/game/new', { method: 'POST', body: JSON.stringify({ difficulty, character: characterForRequest(), campaign_name: campaignName }) });
      onState(data);
      onContinue();
    } catch (error) { setNotice(error.message); }
    finally { setBusy(false); }
  }

  async function startCareer(event) {
    event.preventDefault();
    if (alignmentGap > 0 && !alignmentConfirmed) {
      setNotice('A linha escolhida para o partido diverge do espectro do personagem. Confirme para iniciar com esse atrito simulado.');
      return;
    }
    if (!partyReady) {
      setNotice(invalidCustomParty ? 'Esse nome não está disponível para partidos personalizados.' : 'Informe um nome para o partido da simulação.');
      return;
    }
    setBusy(true); setNotice('');
    try {
      const data = await request('/api/career/start', {
        method: 'POST',
        body: JSON.stringify({ office, state_code: isPresidentialCampaign ? 'DF' : stateCode, municipality: requiresCampaignCity || municipalityId ? municipality : '', municipality_id: requiresCampaignCity || municipalityId ? municipalityId : null, party: selectedParty, ideology, candidate_name: character.name, character: characterForRequest(), difficulty, new_game: true, campaign_name: campaignName }),
      });
      onState(data.state);
      onContinue();
    } catch (error) { setNotice(error.message); }
    finally { setBusy(false); }
  }

  async function restore() {
    if (!selectedArchive) return;
    if (!window.confirm('A partida ativa será arquivada; a partida escolhida voltará a ser a ativa. Continuar?')) return;
    setBusy(true); setNotice('');
    try {
      const data = await request(`/api/game/archives/${selectedArchive}/restore`, { method: 'POST', body: '{}' });
      onState(data.state);
      onContinue();
    } catch (error) { setNotice(error.message); }
    finally { setBusy(false); }
  }

  async function activateCampaign(campaignId) {
    setBusy(true); setNotice('');
    try {
      const data = await request(`/api/campaigns/${campaignId}/activate`, { method: 'POST', body: '{}' });
      onState(data.state);
      onContinue();
    } catch (error) { setNotice(error.message); }
    finally { setBusy(false); }
  }

  const characterFields = <section className="character-creator" aria-labelledby="character-creator-title">
    <div className="character-creator-heading">
      <div><span className="eyebrow">PERSONAGEM FICTÍCIO</span><h3 id="character-creator-title">Quem você será nesta partida?</h3>
        <p>Perfil, origem e costumes dão contexto ao personagem. A cidade natal não define onde ele concorre.</p></div>
      <span className="character-avatar" aria-hidden="true">{character.name.trim().slice(0, 1).toUpperCase() || 'C'}</span>
    </div>
    <div className="character-fields">
      <label className="character-name">Nome público<input value={character.name} onChange={(event) => setCharacterField('name', event.target.value)} minLength={2} maxLength={80} required placeholder="Nome do personagem" /></label>
      <label>Origem familiar<select value={character.family_background} onChange={(event) => setCharacterField('family_background', event.target.value)}>{familyOptions.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
      <label>Espectro político<select value={character.political_spectrum} onChange={(event) => { setCharacterField('political_spectrum', event.target.value); setAlignmentConfirmed(false); }}>{spectra.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
    </div>
    {mode === 'career' && <p className="character-support-preview">Efeito inicial estimado na base eleitoral: {Object.entries(initialSupport).filter(([, value]) => value !== 0).map(([group, value]) => `${supportLabels[group]} ${value > 0 ? '+' : ''}${value.toLocaleString('pt-BR')} p.p.`).join(' · ') || 'sem alteração'}.</p>}
    <fieldset className="character-choice-group"><legend>Costumes e vínculos <small>escolha até 3</small></legend><div className="character-chip-grid">{customOptions.map(([value, label]) => <label className={character.customs.includes(value) ? 'chosen' : ''} key={value}><input type="checkbox" checked={character.customs.includes(value)} onChange={() => setCharacterField('customs', toggleLimited(character.customs, value, 3))} />{label}</label>)}</div></fieldset>
    <details className="character-more"><summary>Origem e características detalhadas <small>opcionais</small></summary>
      <div className="character-fields character-birthplace-fields">
        <label>Estado onde nasceu<select value={character.birth_state_code || ''} onChange={(event) => setCharacter((current) => ({ ...current, birth_state_code: event.target.value, birth_municipality_id: null }))}><option value="">Não informar</option>{catalog?.states.map((item) => <option key={item.code} value={item.code}>{item.name}</option>)}</select></label>
        <MunicipalityPicker request={request} stateCode={character.birth_state_code || ''} value={character.birth_municipality_name || ''} selectedId={character.birth_municipality_id || ''} required={false} disabled={!character.birth_state_code} label="Cidade natal (opcional)" onSelect={(item) => setCharacter((current) => ({ ...current, birth_municipality_id: item.id || null, birth_municipality_name: item.id ? item.name : '' }))} />
      </div>
      <p className="character-field-note">A origem é opcional e só é salva quando UF e cidade do catálogo do IBGE foram escolhidas.</p>
      <div className="character-axis-grid">{Object.entries(axisOptions).map(([key, values]) => <label key={key}>{axisLabels[key]}<select value={character[key]} onChange={(event) => setCharacterField(key, event.target.value)}>{values.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>)}</div>
    </details>
    <details className="character-more"><summary>Traços e descrição <small>opcionais</small></summary>
      <fieldset className="character-choice-group"><legend>Traços de atuação <small>escolha até 2</small></legend><div className="character-trait-grid">{traitOptions.map(([value, label, effect]) => <label className={character.traits.includes(value) ? 'chosen' : ''} key={value}><input type="checkbox" checked={character.traits.includes(value)} onChange={() => setCharacterField('traits', toggleLimited(character.traits, value, 2))} /><span><b>{label}</b><small>{effect}</small></span></label>)}</div></fieldset>
      <label className="character-biography">Como é esse personagem? <small>até 400 caracteres · não inclua dados pessoais reais</small><textarea value={character.biography} onChange={(event) => setCharacterField('biography', event.target.value.slice(0, 400))} maxLength={400} rows={3} placeholder="Conte de onde veio, o que valoriza e como costuma tomar decisões." /></label>
    </details>
  </section>;

  return <main className="game-setup-screen">
    <header className="game-setup-header">
      <Brand />
      <span className="game-setup-caption">ESCOLHA UMA PARTIDA</span>
      {authConfig?.enabled && (authUser?.isGuest
        ? <button className="secondary-button" onClick={onSignIn}>Entrar ou criar conta</button>
        : <button className="secondary-button" onClick={onAccount}>Minha conta</button>)}
    </header>
    <div className="game-setup-content">
      <section className="game-setup-hero" style={{ backgroundImage: `linear-gradient(90deg, rgba(9,24,21,.84), rgba(9,24,21,.22)), url('/assets/backgrounds/${heroImage}')` }}>
        <span className="eyebrow">UM BRASIL, VÁRIOS CAMINHOS</span><h1>Onde começa sua história?</h1>
        <p>Escolha o ponto de partida. Você pode entrar direto no governo ou construir uma carreira desde a campanha.</p>
      </section>

      <section className="setup-tutorial" aria-label="Guia de início">
        {tutorialStep < 0 ? <><div><b>Primeira vez?</b><span>Veja um guia curto sobre os modos, o calendário e as decisões.</span></div><button className="secondary-button" type="button" onClick={() => setTutorialStep(0)}>Abrir guia rápido</button></> : <>
          <div className="setup-tutorial-step"><span>GUIA · {tutorialStep + 1} DE {tutorialSteps.length}</span><b>{tutorialSteps[tutorialStep][0]}</b><p>{tutorialSteps[tutorialStep][1]}</p></div>
          <div className="setup-tutorial-actions"><button className="secondary-button" type="button" disabled={tutorialStep === 0} onClick={() => setTutorialStep((step) => step - 1)}>Anterior</button><button className="secondary-button" type="button" onClick={() => setTutorialStep(-1)}>Pular guia</button>{tutorialStep < tutorialSteps.length - 1 ? <button className="primary-button" type="button" onClick={() => setTutorialStep((step) => step + 1)}>Próximo</button> : <button className="primary-button" type="button" onClick={() => setTutorialStep(-1)}>Concluir</button>}</div>
        </>}
      </section>

      <div className="game-setup-toolbar">
        {hasSavedGame ? <button className="primary-button" onClick={onContinue}>Continuar partida salva <b>→</b></button> : <span className="setup-new-label">Nenhuma partida ativa. Escolha um modo para começar.</span>}
        <label className="setup-difficulty">Dificuldade<select value={difficulty} onChange={(event) => setDifficulty(event.target.value)}>{difficultyOptions.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select><small>{difficultyDescriptions[difficulty]}</small></label>
      </div>

      {campaigns.length > 0 && <details className="saved-campaign-list"><summary>Minhas partidas salvas ({campaigns.length})</summary><div className="saved-campaign-grid">{campaigns.map((item) => <article className={item.active ? 'active' : ''} key={item.campaign_id}><div><b>{item.name}</b><small>{item.office} · {item.phase.replaceAll('_', ' ')} · {item.date ? new Date(`${item.date}T12:00:00`).toLocaleDateString('pt-BR') : 'sem data'} · {difficultyOptions.find(([value]) => value === item.difficulty)?.[1] || item.difficulty}</small></div><button className="secondary-button" disabled={busy || item.active} onClick={() => activateCampaign(item.campaign_id)}>{item.active ? 'Em andamento' : 'Abrir'}</button></article>)}</div></details>}

      <section className="game-mode-grid" aria-label="Modos de jogo">
        <article className={`game-mode-card presidency-mode ${mode === 'presidency' ? 'selected' : ''}`}>
          <div className="game-mode-art" aria-hidden="true" style={{ backgroundImage: "url('/assets/backgrounds/brasilia-amanhecer.jpg')" }} />
          <span className="game-mode-kicker">GOVERNO FEDERAL · 48 MESES</span><h2>Tomar posse no primeiro dia</h2>
          <p>Comece em 1º de janeiro de 2027 como presidente e conduza o governo pelos quatro anos.</p>
          <ul><li>Sem etapa de campanha</li><li>Pronunciamento de posse obrigatório</li><li>Orçamento, Congresso e agenda nacional</li></ul>
          <button className="secondary-button" disabled={busy} onClick={() => updateMode('presidency')}>{mode === 'presidency' ? 'Fechar configuração' : 'Configurar posse direta'}</button>
        </article>
        <article className={`game-mode-card career-mode ${mode === 'career' ? 'selected' : ''}`}>
          <div className="game-mode-art" aria-hidden="true" style={{ backgroundImage: "url('/assets/backgrounds/praca-campanha.jpg')" }} />
          <span className="game-mode-kicker">CAMPANHA E CARREIRA</span><h2>Disputar uma eleição</h2>
          <p>Escolha cargo e território. Faça campanha, dispute a eleição e exerça o mandato se vencer.</p>
          <ul><li>De vereador a presidente</li><li>Calendário e poderes próprios de cada cargo</li><li>Estado e município definem o cenário local</li></ul>
          <button className="secondary-button" disabled={!catalog || busy} onClick={() => updateMode('career')}>{mode === 'career' ? 'Fechar configuração' : 'Escolher cargo e lugar'}</button>
        </article>
      </section>

      {mode === 'presidency' && <form className="career-start-form" onSubmit={startPresidency}>
        <div className="career-start-heading"><div><span className="eyebrow">POSSE DIRETA</span><h2>Configure sua personagem</h2></div><span className="career-start-date">Brasília · 1º de janeiro de 2027</span></div>
        <label className="campaign-name-field">Nome desta partida<input value={campaignName} onChange={(event) => setCampaignName(event.target.value.slice(0, 80))} maxLength={80} placeholder={`Mandato de ${character.name || 'seu personagem'}`} /></label>
        {characterFields}
        <button className="primary-button" disabled={busy || character.name.trim().length < 2}>Assumir a Presidência no primeiro dia <b>→</b></button>
      </form>}

      {mode === 'career' && <form className="career-start-form" onSubmit={startCareer}>
        <div className="career-start-heading"><div><span className="eyebrow">CAMINHO ELEITORAL</span><h2>Escolha cargo e território</h2></div><span className="career-start-date">Calendário eleitoral simulado</span></div>
        <label className="campaign-name-field">Nome desta partida<input value={campaignName} onChange={(event) => setCampaignName(event.target.value.slice(0, 80))} maxLength={80} placeholder={`Campanha de ${character.name || 'seu personagem'}`} /></label>
        {!catalog ? <p>Carregando cargos e estados…</p> : <>
          <div className="career-start-fields">
            <label>Cargo<select value={office} onChange={(event) => setOffice(event.target.value)}>{catalog.offices.map((item) => <option key={item.key} value={item.key}>{item.label}</option>)}</select></label>
            {!isPresidentialCampaign && <label>Estado da candidatura<select value={stateCode} onChange={(event) => { setStateCode(event.target.value); setMunicipality(''); setMunicipalityId(''); }}>{catalog.states.map((item) => <option key={item.code} value={item.code}>{item.name}</option>)}</select></label>}
            {isPresidentialCampaign ? <p className="career-territory-note"><b>Território da eleição: Brasil</b><small>Presidência é uma disputa nacional. A cidade natal, se informada, fica apenas no perfil.</small></p>
              : <MunicipalityPicker request={request} stateCode={stateCode} value={municipality} selectedId={municipalityId} required={requiresCampaignCity} onSelect={(item) => { setMunicipality(item.name); setMunicipalityId(item.id); }} label={requiresCampaignCity ? 'Cidade da candidatura' : 'Cidade de referência (opcional)'} />}
            <label>Partido da simulação<select value={party} onChange={(event) => { setParty(event.target.value); setAlignmentConfirmed(false); }}>{catalog.parties.map((item) => <option key={item} value={item}>{item}</option>)}<option value="__custom__">Criar partido fictício…</option></select></label>
            <label>Linha do partido na simulação<select value={ideology} onChange={(event) => { setIdeology(event.target.value); setAlignmentConfirmed(false); }}>{catalog.ideologies.map((item) => <option key={item}>{item}</option>)}</select></label>
            {party === '__custom__' && <label>Nome do partido fictício<input value={customParty} onChange={(event) => setCustomParty(event.target.value.slice(0, 60))} minLength={3} maxLength={60} placeholder="Ex.: Movimento Cívico" /><small className={invalidCustomParty ? 'field-error' : ''}>{invalidCustomParty ? 'Esse nome não está disponível.' : 'Evite nomes de ideologias extremistas ou ataques a grupos.'}</small></label>}
          </div>
          <p className="party-data-note">Partidos reais aparecem apenas como referência factual, conforme a lista do TSE ({catalog.party_source?.checked_on || 'data não informada'}). A linha ideológica é uma escolha da simulação e não descreve oficialmente o partido. {catalog.party_source?.url && <a href={catalog.party_source.url} target="_blank" rel="noreferrer">Fonte TSE</a>}</p>
          {alignmentGap > 0 && <label className="party-alignment-warning"><span>O personagem está {alignmentGap} posição(ões) distante da linha escolhida para a legenda. Isso reduz levemente o apoio inicial e cria atrito interno fictício; o jogo não afirma que essa seja a posição real do partido.</span><input type="checkbox" checked={alignmentConfirmed} onChange={(event) => setAlignmentConfirmed(event.target.checked)} /> Confirmo essa divergência para a simulação</label>}
          {chosenOffice && <div className="career-start-preview"><b>{chosenOffice.label} · mandato de {chosenOffice.term_years} anos</b><span>{chosenOffice.powers.join(' · ')}</span>{preview && <small>Eleição prevista: {new Date(`${preview.election_date}T12:00:00`).toLocaleDateString('pt-BR')} · campanha abre em {new Date(`${preview.campaign_start}T12:00:00`).toLocaleDateString('pt-BR')} · posse prevista em {new Date(`${preview.inauguration_date}T12:00:00`).toLocaleDateString('pt-BR')}</small>}</div>}
          {characterFields}
          <button className="primary-button" disabled={busy || (requiresCampaignCity && !municipalityId) || character.name.trim().length < 2 || !partyReady || (alignmentGap > 0 && !alignmentConfirmed)}>Criar personagem e iniciar campanha <b>→</b></button>
        </>}
      </form>}

      {archives.length > 0 && <details className="game-archives"><summary>Restaurar uma partida arquivada ({archives.length})</summary><div><select value={selectedArchive} onChange={(event) => setSelectedArchive(event.target.value)}><option value="">Escolha uma partida salva</option>{archives.map((item) => <option key={item.id} value={item.id}>{item.title} · {new Date(`${item.archived_at.slice(0, 10)}T12:00:00`).toLocaleDateString('pt-BR')}</option>)}</select><button className="secondary-button" disabled={busy || !selectedArchive} onClick={restore}>Restaurar</button></div></details>}
      {notice && <p className="game-setup-notice" role="status">{notice}</p>}
    </div>
    <footer className="game-setup-footer">Civiciclo é um simulador fictício e satírico, sem afiliação ou endosso de partidos, pessoas ou instituições. A referência a nomes partidários não transforma resultados simulados em fatos. Não use dados pessoais reais no perfil livre.</footer>
  </main>;
}
