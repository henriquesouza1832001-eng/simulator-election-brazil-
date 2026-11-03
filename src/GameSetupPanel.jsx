import { useEffect, useMemo, useState } from 'react';

const difficultyOptions = [
  ['tranquilo', 'Tranquilo'], ['normal', 'Normal'], ['dificil', 'Difícil'],
  ['complicado', 'Complicado'], ['realismo_puro', 'Realismo puro'],
];

export default function GameSetupPanel({ state, request, onState, onContinue, busy, setBusy, authConfig, authUser, onSignIn, onAccount }) {
  const [catalog, setCatalog] = useState(null);
  const [archives, setArchives] = useState([]);
  const [mode, setMode] = useState('');
  const [office, setOffice] = useState('vereador');
  const [stateCode, setStateCode] = useState('SP');
  const [municipality, setMunicipality] = useState('São Paulo');
  const [party, setParty] = useState('');
  const [ideology, setIdeology] = useState('Centro');
  const [candidateName, setCandidateName] = useState('');
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

  async function startPresidency() {
    if (hasSavedGame && !window.confirm('A partida atual será arquivada e continuará disponível para restaurar. Iniciar outro governo?')) return;
    setBusy(true); setNotice('');
    try {
      const data = await request('/api/game/new', {
        method: 'POST', body: JSON.stringify({ difficulty }),
      });
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
        body: JSON.stringify({ office, state_code: stateCode, municipality, party, ideology, candidate_name: candidateName, difficulty, new_game: true }),
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

  return <main className="game-setup-screen">
    <header className="game-setup-header">
      <a className="brand" href="#"><span className="brand-mark">M</span><span>MANDATO<small>SIMULADOR POLÍTICO</small></span></a>
      <span className="game-setup-caption">ESCOLHA UMA PARTIDA</span>
      {authConfig?.enabled && (authUser?.isGuest
        ? <button className="secondary-button" onClick={onSignIn}>Entrar ou criar conta</button>
        : <button className="secondary-button" onClick={onAccount}>Minha conta</button>)}
    </header>
    <div className="game-setup-content">
      <div className="game-setup-intro">
        <span className="eyebrow">UM BRASIL, VÁRIOS CAMINHOS</span>
        <h1>Onde começa sua história?</h1>
        <p>Continue uma partida ou escolha o cargo, o estado e o modo antes de entrar no jogo.</p>
      </div>

      <div className="game-setup-toolbar">
        {hasSavedGame ? <button className="primary-button" onClick={onContinue}>Continuar partida salva <b>→</b></button> : <span className="setup-new-label">Nenhuma partida ativa. Escolha um modo para começar.</span>}
        <label className="setup-difficulty">Dificuldade<select value={difficulty} onChange={(event) => setDifficulty(event.target.value)}>{difficultyOptions.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
      </div>

      <section className="game-mode-grid" aria-label="Modos de jogo">
        <article className={`game-mode-card ${mode === 'presidency' ? 'selected' : ''}`}>
          <span className="game-mode-kicker">GOVERNO FEDERAL · 48 MESES</span>
          <h2>Presidência</h2>
          <p>Comece no Planalto, conduza o governo federal e acompanhe economia, Congresso, políticas públicas e diplomacia.</p>
          <ul><li>Agenda nacional e orçamento da União</li><li>Decisões ao longo de quatro anos</li><li>Pronunciamento de posse e campanha presidencial</li></ul>
          <button className="secondary-button" disabled={busy} onClick={startPresidency}>Começar na Presidência</button>
        </article>
        <article className={`game-mode-card ${mode === 'career' ? 'selected' : ''}`}>
          <span className="game-mode-kicker">CAMPANHA E CARREIRA</span>
          <h2>Carreira política</h2>
          <p>Escolha onde concorrer. A campanha, o resultado eleitoral e o mandato seguem o calendário do cargo escolhido.</p>
          <ul><li>Vereador, prefeito, deputado e senador</li><li>Governador ou presidente</li><li>Campanha vinculada ao estado e ao município</li></ul>
          <button className="secondary-button" disabled={!catalog} onClick={() => setMode(mode === 'career' ? '' : 'career')}>{mode === 'career' ? 'Fechar escolha de cargo' : 'Escolher cargo e lugar'}</button>
        </article>
      </section>

      {mode === 'career' && <form className="career-start-form" onSubmit={startCareer}>
        <div className="career-start-heading"><div><span className="eyebrow">CONFIGURE A CAMPANHA</span><h2>Defina seu ponto de partida</h2></div><span className="career-start-date">{chosenOffice?.term_years} anos · {chosenOffice?.electorate}</span></div>
        {!catalog ? <p>Carregando cargos e estados…</p> : <>
          <div className="career-start-fields">
            <label>Cargo<select value={office} onChange={(event) => setOffice(event.target.value)}>{catalog.offices.map((item) => <option key={item.key} value={item.key}>{item.label}</option>)}</select></label>
            <label>Estado<select value={stateCode} onChange={(event) => setStateCode(event.target.value)}>{catalog.states.map((item) => <option key={item.code} value={item.code}>{item.name}</option>)}</select></label>
            <label>Cidade da campanha<input value={municipality} onChange={(event) => setMunicipality(event.target.value)} minLength={2} maxLength={80} required placeholder="Município base" /><small>Para cargos municipais, define o município da candidatura.</small></label>
            <label>Partido simulado<select value={party} onChange={(event) => setParty(event.target.value)}>{catalog.parties.map((item) => <option key={item}>{item}</option>)}</select></label>
            <label>Posicionamento<select value={ideology} onChange={(event) => setIdeology(event.target.value)}>{catalog.ideologies.map((item) => <option key={item}>{item}</option>)}</select></label>
            <label>Nome na urna<input value={candidateName} onChange={(event) => setCandidateName(event.target.value)} maxLength={80} placeholder="Seu nome ou personagem" /></label>
          </div>
          {chosenOffice && <div className="career-start-preview"><b>O que esperar</b><span>{chosenOffice.powers.join(' · ')}</span>{preview && <small>Eleição prevista: {new Date(`${preview.election_date}T12:00:00`).toLocaleDateString('pt-BR')} · campanha abre em {new Date(`${preview.campaign_start}T12:00:00`).toLocaleDateString('pt-BR')} · posse prevista em {new Date(`${preview.inauguration_date}T12:00:00`).toLocaleDateString('pt-BR')}</small>}</div>}
          <button className="primary-button" disabled={busy || !municipality.trim()}>Começar carreira neste cargo <b>→</b></button>
        </>}
      </form>}

      {archives.length > 0 && <details className="game-archives"><summary>Restaurar uma partida arquivada ({archives.length})</summary><div><select value={selectedArchive} onChange={(event) => setSelectedArchive(event.target.value)}><option value="">Escolha uma partida salva</option>{archives.map((item) => <option key={item.id} value={item.id}>{item.title} · {new Date(`${item.archived_at.slice(0, 10)}T12:00:00`).toLocaleDateString('pt-BR')}</option>)}</select><button className="secondary-button" disabled={busy || !selectedArchive} onClick={restore}>Restaurar</button></div></details>}
      {notice && <p className="game-setup-notice" role="status">{notice}</p>}
    </div>
    <footer className="game-setup-footer">Todas as partidas, eleições e personagens são cenários fictícios.</footer>
  </main>;
}
