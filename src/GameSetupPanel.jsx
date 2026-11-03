import { useEffect, useMemo, useState } from 'react';

const difficultyOptions = [
  ['tranquilo', 'Tranquilo'], ['normal', 'Normal'], ['dificil', 'Difícil'],
  ['complicado', 'Complicado'], ['realismo_puro', 'Realismo puro'],
];
const spectra = [
  ['esquerda', 'Esquerda'], ['centro_esquerda', 'Centro-esquerda'], ['centro', 'Centro'],
  ['centro_direita', 'Centro-direita'], ['direita', 'Direita'],
];
const familyOptions = [
  ['trabalhadora', 'Família trabalhadora'], ['classe_media', 'Classe média'],
  ['empreendedora', 'Pequeno negócio'], ['rural', 'Origem rural'],
  ['servidora_publica', 'Serviço público'], ['politica', 'Família ligada à política'],
];
const customOptions = [
  ['vida_comunitaria', 'Vida comunitária'], ['vida_urbana', 'Cotidiano urbano'],
  ['vida_rural', 'Cotidiano rural'], ['fe_presente', 'Fé presente na comunidade'],
  ['cultura_popular', 'Cultura popular'], ['vida_sindical', 'Participação sindical'],
];
const traitOptions = [
  ['carismatica', 'Carismática', '+1 ponto de aprovação na posse; +0,5 de apoio inicial e +0,15 ponto local por ação na campanha.'],
  ['tecnica', 'Técnica', '+1 de confiança institucional na posse; até +3 pontos em falas concretas.'],
  ['conciliadora', 'Conciliadora', '+1 de apoio no Congresso na posse; pequeno ganho entre grupos alcançados.'],
  ['combativa', 'Combativa', '+0,5 de aprovação e −0,5 de confiança na posse; mais alcance e desgaste.'],
  ['gestora', 'Gestora', '+1 de capacidade de governar na posse; ações de campanha custam 10% menos.'],
  ['comunitaria', 'Comunitária', '+0,5 de aprovação na posse; pequeno ganho entre grupos alcançados.'],
];
const blankCharacter = { name: '', political_spectrum: 'centro', family_background: 'classe_media', customs: [], traits: [], biography: '' };
const spectrumSupport = {
  esquerda: { trabalhadores: 2, servidores: 1, negocios: -1 }, centro_esquerda: { trabalhadores: 1.2, familias: .7 },
  centro: { familias: .4 }, centro_direita: { negocios: 1, rural: .6 }, direita: { negocios: 1.8, rural: 1, servidores: -.6 },
};
const familySupport = {
  trabalhadora: { trabalhadores: 1.2, familias: .5 }, classe_media: { familias: .6, negocios: .4 },
  empreendedora: { negocios: 1.2 }, rural: { rural: 1.4, trabalhadores: .3 },
  servidora_publica: { servidores: 1.2, familias: .3 }, politica: { servidores: .3, negocios: .3 },
};
const supportLabels = { trabalhadores: 'Trabalhadores', negocios: 'Pequenos negócios', familias: 'Famílias', servidores: 'Servidores', rural: 'População rural' };

function toggleLimited(items, value, limit) {
  if (items.includes(value)) return items.filter((item) => item !== value);
  return items.length < limit ? [...items, value] : items;
}

export default function GameSetupPanel({ state, request, onState, onContinue, busy, setBusy, authConfig, authUser, onSignIn, onAccount }) {
  const [catalog, setCatalog] = useState(null);
  const [archives, setArchives] = useState([]);
  const [mode, setMode] = useState('');
  const [office, setOffice] = useState('vereador');
  const [stateCode, setStateCode] = useState('SP');
  const [municipality, setMunicipality] = useState('São Paulo');
  const [party, setParty] = useState('');
  const [ideology, setIdeology] = useState('Centro');
  const [character, setCharacter] = useState(blankCharacter);
  const [difficulty, setDifficulty] = useState(state.difficulty || 'normal');
  const [selectedArchive, setSelectedArchive] = useState('');
  const [notice, setNotice] = useState('');

  useEffect(() => {
    let mounted = true;
    Promise.all([request('/api/career/options?fresh=true'), request('/api/game/archives')])
      .then(([career, saved]) => {
        if (!mounted) return;
        setCatalog(career);
        setArchives(saved.items || []);
        setParty(career.parties?.[0] || 'Partido da Renovação');
      })
      .catch((error) => { if (mounted) setNotice(error.message); });
    return () => { mounted = false; };
  }, []);

  const chosenOffice = useMemo(() => catalog?.offices.find((item) => item.key === office), [catalog, office]);
  const preview = catalog?.calendar_previews?.[office];
  const hasSavedGame = Boolean(state && !state.setup_pending);
  const heroImage = mode === 'career' && ['AC', 'AP', 'AM', 'PA', 'RO', 'RR', 'TO'].includes(stateCode)
    ? 'porto-amazonico.jpg' : mode === 'career' ? 'praca-campanha.jpg' : 'brasilia-amanhecer.jpg';
  const initialSupport = { ...spectrumSupport[character.political_spectrum], ...{} };
  Object.entries(familySupport[character.family_background] || {}).forEach(([group, amount]) => { initialSupport[group] = (initialSupport[group] || 0) + amount; });
  const setCharacterField = (key, value) => setCharacter((current) => ({ ...current, [key]: value }));
  const updateMode = (next) => setMode((current) => current === next ? '' : next);

  async function startPresidency(event) {
    event.preventDefault();
    if (hasSavedGame && !window.confirm('A partida atual será arquivada e continuará disponível para restaurar. Iniciar outro governo?')) return;
    setBusy(true); setNotice('');
    try {
      const data = await request('/api/game/new', { method: 'POST', body: JSON.stringify({ difficulty, character }) });
      onState(data);
      onContinue();
    } catch (error) { setNotice(error.message); }
    finally { setBusy(false); }
  }

  async function startCareer(event) {
    event.preventDefault();
    if (hasSavedGame && !window.confirm('A partida atual será arquivada e poderá ser restaurada depois. Começar esta carreira?')) return;
    setBusy(true); setNotice('');
    try {
      const data = await request('/api/career/start', {
        method: 'POST',
        body: JSON.stringify({ office, state_code: stateCode, municipality, party, ideology, candidate_name: character.name, character, difficulty, new_game: true }),
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

  const characterFields = <section className="character-creator" aria-labelledby="character-creator-title">
    <div className="character-creator-heading">
      <div><span className="eyebrow">PERSONAGEM FICTÍCIO</span><h3 id="character-creator-title">Quem você será nesta partida?</h3>
        <p>{mode === 'career' ? 'Origem e espectro alteram levemente sua base eleitoral. Traços ajustam as ações. Costumes e descrição ficam salvos no perfil, sem bônus numéricos.' : 'Na posse direta, os traços ajustam levemente os indicadores iniciais. Origem, espectro, costumes e descrição ficam salvos no perfil; na carreira eleitoral, origem e espectro também influenciam a base.'}</p></div>
      <span className="character-avatar" aria-hidden="true">{character.name.trim().slice(0, 1).toUpperCase() || 'M'}</span>
    </div>
    <div className="character-fields">
      <label className="character-name">Nome público<input value={character.name} onChange={(event) => setCharacterField('name', event.target.value)} minLength={2} maxLength={80} required placeholder="Nome do personagem" /></label>
      <label>Origem familiar<select value={character.family_background} onChange={(event) => setCharacterField('family_background', event.target.value)}>{familyOptions.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
      <label>Espectro político<select value={character.political_spectrum} onChange={(event) => setCharacterField('political_spectrum', event.target.value)}>{spectra.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
    </div>
    {mode === 'career' && <p className="character-support-preview">Efeito inicial estimado na base eleitoral: {Object.entries(initialSupport).filter(([, value]) => value !== 0).map(([group, value]) => `${supportLabels[group]} ${value > 0 ? '+' : ''}${value.toLocaleString('pt-BR')} p.p.`).join(' · ') || 'sem alteração'}.</p>}
    <fieldset className="character-choice-group"><legend>Costumes e vínculos <small>escolha até 3</small></legend><div className="character-chip-grid">{customOptions.map(([value, label]) => <label className={character.customs.includes(value) ? 'chosen' : ''} key={value}><input type="checkbox" checked={character.customs.includes(value)} onChange={() => setCharacterField('customs', toggleLimited(character.customs, value, 3))} />{label}</label>)}</div></fieldset>
    <fieldset className="character-choice-group"><legend>Traços de atuação <small>escolha até 2; os efeitos são modestos</small></legend><div className="character-trait-grid">{traitOptions.map(([value, label, effect]) => <label className={character.traits.includes(value) ? 'chosen' : ''} key={value}><input type="checkbox" checked={character.traits.includes(value)} onChange={() => setCharacterField('traits', toggleLimited(character.traits, value, 2))} /><span><b>{label}</b><small>{effect}</small></span></label>)}</div></fieldset>
    <label className="character-biography">Como é esse personagem? <small>opcional · até 400 caracteres · não inclua dados pessoais reais</small><textarea value={character.biography} onChange={(event) => setCharacterField('biography', event.target.value.slice(0, 400))} maxLength={400} rows={3} placeholder="Conte de onde veio, o que valoriza e como costuma tomar decisões." /></label>
  </section>;

  return <main className="game-setup-screen">
    <header className="game-setup-header">
      <a className="brand" href="#"><span className="brand-mark">M</span><span>MANDATO<small>SIMULADOR POLÍTICO</small></span></a>
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

      <div className="game-setup-toolbar">
        {hasSavedGame ? <button className="primary-button" onClick={onContinue}>Continuar partida salva <b>→</b></button> : <span className="setup-new-label">Nenhuma partida ativa. Escolha um modo para começar.</span>}
        <label className="setup-difficulty">Dificuldade<select value={difficulty} onChange={(event) => setDifficulty(event.target.value)}>{difficultyOptions.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
      </div>

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
        {characterFields}
        <button className="primary-button" disabled={busy || character.name.trim().length < 2}>Assumir a Presidência no primeiro dia <b>→</b></button>
      </form>}

      {mode === 'career' && <form className="career-start-form" onSubmit={startCareer}>
        <div className="career-start-heading"><div><span className="eyebrow">CAMINHO ELEITORAL</span><h2>Escolha cargo e território</h2></div><span className="career-start-date">Calendário eleitoral simulado</span></div>
        {!catalog ? <p>Carregando cargos e estados…</p> : <>
          <div className="career-start-fields">
            <label>Cargo<select value={office} onChange={(event) => setOffice(event.target.value)}>{catalog.offices.map((item) => <option key={item.key} value={item.key}>{item.label}</option>)}</select></label>
            <label>Estado<select value={stateCode} onChange={(event) => setStateCode(event.target.value)}>{catalog.states.map((item) => <option key={item.code} value={item.code}>{item.name}</option>)}</select></label>
            <label>Cidade da campanha<input value={municipality} onChange={(event) => setMunicipality(event.target.value)} minLength={2} maxLength={80} required placeholder="Município base" /><small>Para cargos municipais, define o local da candidatura.</small></label>
            <label>Partido simulado<select value={party} onChange={(event) => setParty(event.target.value)}>{catalog.parties.map((item) => <option key={item}>{item}</option>)}</select></label>
            <label>Posicionamento do partido<select value={ideology} onChange={(event) => setIdeology(event.target.value)}>{catalog.ideologies.map((item) => <option key={item}>{item}</option>)}</select></label>
          </div>
          {chosenOffice && <div className="career-start-preview"><b>{chosenOffice.label} · mandato de {chosenOffice.term_years} anos</b><span>{chosenOffice.powers.join(' · ')}</span>{preview && <small>Eleição prevista: {new Date(`${preview.election_date}T12:00:00`).toLocaleDateString('pt-BR')} · campanha abre em {new Date(`${preview.campaign_start}T12:00:00`).toLocaleDateString('pt-BR')} · posse prevista em {new Date(`${preview.inauguration_date}T12:00:00`).toLocaleDateString('pt-BR')}</small>}</div>}
          {characterFields}
          <button className="primary-button" disabled={busy || !municipality.trim() || character.name.trim().length < 2}>Criar personagem e iniciar campanha <b>→</b></button>
        </>}
      </form>}

      {archives.length > 0 && <details className="game-archives"><summary>Restaurar uma partida arquivada ({archives.length})</summary><div><select value={selectedArchive} onChange={(event) => setSelectedArchive(event.target.value)}><option value="">Escolha uma partida salva</option>{archives.map((item) => <option key={item.id} value={item.id}>{item.title} · {new Date(`${item.archived_at.slice(0, 10)}T12:00:00`).toLocaleDateString('pt-BR')}</option>)}</select><button className="secondary-button" disabled={busy || !selectedArchive} onClick={restore}>Restaurar</button></div></details>}
      {notice && <p className="game-setup-notice" role="status">{notice}</p>}
    </div>
    <footer className="game-setup-footer">Partidas, personagens, eleições e notícias são simulações. Não use dados pessoais reais no perfil livre.</footer>
  </main>;
}
