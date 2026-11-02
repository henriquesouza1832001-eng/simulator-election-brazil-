import { useEffect, useMemo, useState } from 'react';
import './appointments.css';

const number = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 1 });
const dateLabel = (value) => value ? new Date(`${value}T12:00:00`).toLocaleDateString('pt-BR', { day: 'numeric', month: 'long' }) : '—';

export default function GovernmentAppointments({ state, request, onState, onNotice, busy, setBusy }) {
  const [data, setData] = useState(null);
  const [section, setSection] = useState('Gabinete');
  const [ministry, setMinistry] = useState('');
  const [candidateId, setCandidateId] = useState('');

  async function reload() {
    const result = await request('/api/government/appointments');
    setData(result);
    if (!ministry && result.cabinet?.length) setMinistry(result.cabinet[0].id);
  }

  useEffect(() => { reload().catch((error) => onNotice(error.message)); }, []);

  const selectedMinistry = useMemo(() => data?.cabinet?.find((item) => item.id === ministry), [data, ministry]);
  const selectedCandidate = selectedMinistry?.candidates?.find((item) => item.id === candidateId);
  const authorized = Boolean(data?.authorized);

  useEffect(() => {
    if (selectedMinistry?.candidates?.length && !selectedMinistry.candidates.some((item) => item.id === candidateId)) {
      setCandidateId(selectedMinistry.candidates[0].id);
    }
  }, [selectedMinistry, candidateId]);

  async function appoint() {
    if (!selectedCandidate || !selectedMinistry) return;
    setBusy(true);
    try {
      const result = await request('/api/government/appointments/minister', { method: 'POST', body: JSON.stringify({ ministry_id: ministry, candidate_id: candidateId }) });
      onState(result.state);
      setData(result.appointments);
      onNotice(result.result.summary);
    } catch (error) { onNotice(error.message); }
    finally { setBusy(false); }
  }

  async function nominate(candidate) {
    setBusy(true);
    try {
      const result = await request('/api/government/appointments/stf', { method: 'POST', body: JSON.stringify({ candidate_id: candidate.id }) });
      onState(result.state);
      setData(result.appointments);
      onNotice(result.result.summary);
    } catch (error) { onNotice(error.message); }
    finally { setBusy(false); }
  }

  if (!data) return <section className="panel appointments-panel"><p>Carregando as instituições…</p></section>;
  const filled = data.cabinet.filter((item) => item.minister).length;
  const vacancy = data.judiciary.vacant;

  return <section className="appointments-panel">
    <div className="panel appointments-intro"><div><span className="eyebrow">NOMEAÇÕES E INSTITUIÇÕES</span><h2>Monte a equipe e conduza indicações</h2><p>Escolhas de gabinete afetam coordenação e confiança. Uma indicação ao STF segue para sabatina e votação simuladas no Senado.</p></div><span className="simulated-tag">CENÁRIO FICTÍCIO</span></div>
    {!authorized && <div className="appointments-locked">As nomeações federais ficam disponíveis quando você exerce a Presidência. Aqui é possível consultar a composição desta partida.</div>}
    <nav className="appointments-nav" aria-label="Nomeações"><button className={section === 'Gabinete' ? 'active' : ''} onClick={() => setSection('Gabinete')}>Gabinete <small>{filled}/{data.cabinet.length}</small></button><button className={section === 'STF' ? 'active' : ''} onClick={() => setSection('STF')}>STF <small>{vacancy ? '1 vaga' : 'sem vaga'}</small></button></nav>

    {section === 'Gabinete' && <div className="appointments-grid">
      <section className="panel cabinet-picker"><div className="panel-heading small"><div><span className="eyebrow">PASTAS FIXAS</span><h3>Escolha o ministério</h3></div><b>{filled} nomeados</b></div>
        <label>Ministério<select value={ministry} onChange={(event) => { setMinistry(event.target.value); setCandidateId(''); }}>
          {data.cabinet.map((item) => <option value={item.id} key={item.id}>{item.name}{item.minister ? ` · ${item.minister.name}` : ' · vaga aberta'}</option>)}
        </select></label>
        {selectedMinistry?.minister ? <div className="current-minister"><span>EM EXERCÍCIO</span><b>{selectedMinistry.minister.name}</b><small>{selectedMinistry.minister.background} · desde {dateLabel(selectedMinistry.minister.appointed_on)}</small></div> : <div className="current-minister empty"><span>SEM NOMEAÇÃO</span><b>Esta pasta aguarda escolha</b></div>}
        <div className="cabinet-candidate-list">{selectedMinistry?.candidates?.map((candidate) => <button key={candidate.id} className={`appointment-candidate ${candidate.id === candidateId ? 'selected' : ''}`} onClick={() => setCandidateId(candidate.id)}>
          <span className="candidate-name">{candidate.name}</span><span className="candidate-background">{candidate.background} · {candidate.experience_years} anos</span>
          <span className="candidate-stats"><i>Área <b>{candidate.technical_fit}</b></i><i>Coalizão <b>{candidate.coalition_support}</b></i><i>Integridade <b>{candidate.integrity}</b></i><i>Risco <b>{candidate.risk}</b></i></span>
        </button>)}</div>
        {selectedCandidate && <div className="appointment-preview"><b>Se nomear</b><p>Coordenação política estimada {selectedCandidate.coalition_support >= 65 ? 'melhora' : 'fica sob pressão'}; confiança institucional responde à integridade e a problemas futuros podem trazer a escolha de volta ao noticiário.</p><button className="primary-button" disabled={!authorized || busy || data.cabinet_days_until_action > 0} onClick={appoint}>{data.cabinet_days_until_action ? `Próxima escolha em ${data.cabinet_days_until_action} dias` : 'Nomear para esta pasta'}</button></div>}
      </section>
      <aside className="panel cabinet-summary"><span className="eyebrow">FORMAÇÃO DO GOVERNO</span><h3>Quadro do gabinete</h3><div className="cabinet-progress"><i style={{ width: `${filled / data.cabinet.length * 100}%` }}/></div><p>{filled} de {data.cabinet.length} pastas com titular nesta simulação.</p><details><summary>Ver titulares</summary><div className="cabinet-roster">{data.cabinet.filter((item) => item.minister).map((item) => <article key={item.id}><span>{item.name}</span><b>{item.minister.name}</b></article>)}</div></details><div className="appointment-rule"><b>Uma nomeação a cada sete dias</b><small>As pastas são as do catálogo SIORG usado pelo jogo. Os nomes e atributos são inventados; não representam pessoas reais.</small></div></aside>
    </div>}

    {section === 'STF' && <div className="appointments-grid">
      <section className="panel court-panel"><div className="panel-heading small"><div><span className="eyebrow">INDICAÇÃO PRESIDENCIAL</span><h3>Vaga e sabatina</h3></div><span className={vacancy ? 'vacancy-badge' : 'filled-badge'}>{vacancy ? 'VAGA ABERTA' : 'SEM VAGA'}</span></div>
        {vacancy ? <><p>Uma vaga fictícia está aberta desde {dateLabel(vacancy.opened_on)}. Compare cinco perfis antes de indicar; a escolha entra em pauta no Senado em 30 dias.</p>{data.judiciary.candidates.length ? <div className="judge-candidates">{data.judiciary.candidates.map((candidate) => <article className="judge-candidate" key={candidate.id}><div className="judge-candidate-head"><div><b>{candidate.name}</b><small>{candidate.specialty} · {candidate.years_experience} anos de carreira</small></div><strong>{number.format(candidate.estimated_confirmation_pct)}%<small>chance estimada</small></strong></div><div className="candidate-stats"><i>Técnica <b>{candidate.technical_record}</b></i><i>Independência <b>{candidate.independence}</b></i><i>Diálogo no Senado <b>{candidate.senate_dialogue}</b></i><i>Controvérsia <b>{candidate.controversy}</b></i></div><button className="secondary-button" disabled={!authorized || busy} onClick={() => nominate(candidate)}>Indicar este nome</button></article>)}</div> : <p>Há uma indicação aguardando votação; novas indicações ficam suspensas até o resultado.</p>}</> : <p>As onze cadeiras estão ocupadas no cenário. Uma vaga futura poderá abrir por aposentadoria ou saída simulada.</p>}
        {data.judiciary.pending.map((item) => <div className="pending-nomination" key={item.id}><span>EM SABATINA · {item.days_until_vote} DIAS</span><b>{item.name}</b><small>{item.specialty} · votação prevista para {dateLabel(item.vote_date)}</small></div>)}
      </section>
      <aside className="panel court-history"><span className="eyebrow">RESULTADOS NO SENADO</span><h3>Indicações recentes</h3>{data.judiciary.confirmed.length || data.judiciary.rejected.length ? <div className="court-results">{[...data.judiciary.confirmed, ...data.judiciary.rejected].sort((a, b) => b.resolved_on.localeCompare(a.resolved_on)).map((item) => <article key={item.id}><b>{item.name}</b><span className={item.status}>{item.status === 'confirmed' ? 'APROVADO' : 'REJEITADO'}</span><small>{dateLabel(item.resolved_on)} · probabilidade calculada {number.format(item.vote_probability)}%</small></article>)}</div> : <p className="empty-state">Os resultados aparecem após a data da votação.</p>}<div className="appointment-rule"><b>O Senado decide</b><small>O motor considera apoio parlamentar, experiência, independência, diálogo e controvérsia. A estimativa pode divergir do resultado.</small></div></aside>
    </div>}
    <p className="appointments-notice">{data.notice}</p>
  </section>;
}
