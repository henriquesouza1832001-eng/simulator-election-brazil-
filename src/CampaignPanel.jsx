import { useMemo, useState } from 'react';
import './campaign.css';
import MunicipalityPicker from './MunicipalityPicker';

const number = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 1 });

export default function CampaignPanel({ state, request, onState, busy, setBusy, onNotice }) {
  const overview = state.campaign_overview;
  const [activity, setActivity] = useState('comicio');
  const [region, setRegion] = useState('sudeste');
  const [municipality, setMunicipality] = useState(null);
  const [citySearch, setCitySearch] = useState('');
  const [issue, setIssue] = useState('economia');
  const [conduct, setConduct] = useState('regular');
  const [message, setMessage] = useState('');
  const [result, setResult] = useState(null);
  const [section, setSection] = useState('Plano');
  const selectedActivity = useMemo(() => overview?.activity_options?.find((item) => item.key === activity), [overview, activity]);

  async function submit(event) {
    event.preventDefault();
    setBusy(true);
    setResult(null);
    try {
      const data = await request('/api/campaign/action', { method: 'POST', body: JSON.stringify({ activity_type: activity, region, municipality_id: municipality?.id || null, issue, message, conduct }) });
      onState(data.state);
      setResult(data.result);
      onNotice(`${data.result.activity.label} registrado. O calendário avançou ${data.result.days_cost} dia(s); ${data.calendar_message}`);
      setMessage('');
    } catch (error) {
      onNotice(error.message);
    } finally {
      setBusy(false);
    }
  }

  if (!overview) return <section className="panel campaign-page"><p>Carregando situação eleitoral…</p></section>;

  return <section className="campaign-page">
    <header className="campaign-heading panel">
      <div><span className="eyebrow">CICLO ELEITORAL SIMULADO</span><h2>{overview.finished ? 'Apuração concluída' : overview.active ? 'Campanha em andamento' : 'Próxima disputa presidencial'}</h2>
        <p>{overview.finished ? overview.result === 'reelected' ? 'Você venceu. A transição segue até a posse e o novo mandato mantém o calendário.' : overview.transition_complete ? 'A transição terminou. Você deixou a Presidência e pode seguir por outro caminho de carreira.' : 'Você perdeu. Continua no cargo durante a transição; a derrota abre outro caminho de carreira.' : overview.active ? 'A eleição está aberta. O governo continua trabalhando enquanto você faz campanha.' : `A campanha abre em ${new Date(`${overview.campaign_start}T12:00:00`).toLocaleDateString('pt-BR')}. O mandato e os eventos seguem no calendário até lá.`}</p>
      </div>
      <div className="campaign-countdown"><span>{overview.finished ? 'RESULTADO' : overview.active ? 'DIAS ATÉ A VOTAÇÃO' : 'DIAS ATÉ A CAMPANHA'}</span><strong>{overview.finished ? overview.result === 'reelected' ? 'Vitória' : 'Derrota' : overview.active ? overview.days_until_election : overview.days_until_campaign}</strong><small>Eleição simulada · {new Date(`${overview.election_date}T12:00:00`).toLocaleDateString('pt-BR')}{overview.transition_date ? ` · transição até ${new Date(`${overview.transition_date}T12:00:00`).toLocaleDateString('pt-BR')}` : ''}</small></div>
    </header>

    <div className="campaign-metrics">
      <article className="panel"><span>APOIO PROJETADO</span><strong>{number.format(overview.national_support)}<small>%</small></strong><p>Estimativa da campanha, não aprovação do governo.</p></article>
      <article className="panel"><span>MOMENTUM</span><strong>{overview.momentum > 0 ? '+' : ''}{number.format(overview.momentum)}</strong><p>Movimento recente acumulado no cenário.</p></article>
      <article className="panel"><span>FUNDO SIMULADO</span><strong>R$ {number.format(overview.funds_bi)}<small> bi</small></strong><p>Contabilidade da campanha, separada do Tesouro.</p></article>
    </div>
    {overview.finished && overview.conduct_review?.attempts > 0 && <div className="campaign-conduct-result">Revisão eleitoral simulada: {overview.conduct_review.detected} irregularidade(s) detectada(s); {overview.conduct_review.reviewed ? 'a Justiça Eleitoral abriu revisão final' : 'não houve revisão adicional na apuração'}; penalidade aplicada ao resultado: {number.format(overview.conduct_review.vote_penalty)} pontos.</div>}

    <nav className="campaign-subnav" aria-label="Seções da campanha">
      {['Plano', 'Território', 'Histórico'].map((item) => <button key={item} className={section === item ? 'active' : ''} onClick={() => setSection(item)}>{item}</button>)}
    </nav>

    {section === 'Plano' && <div className="campaign-columns">
      <section className="panel campaign-action-panel">
        <span className="eyebrow">PRÓXIMO PASSO</span><h3>{overview.active ? 'Escolha uma atividade' : 'Prepare a disputa'}</h3>
        {!overview.active ? <div className="campaign-closed"><p>{overview.finished ? 'As atividades desta campanha foram encerradas e permanecem no histórico. O resultado e a transição seguem o calendário do mandato.' : <>Faltam <b>{overview.days_until_campaign} dias</b> para a abertura da campanha simulada. Continue o mandato; acontecimentos e indicadores continuam avançando.</>}</p>{!overview.finished && <button className="secondary-button" onClick={() => onNotice('A campanha começa na data mostrada. Até lá, o governo permanece em exercício e você pode avançar o calendário.')}>Como funciona</button>}</div> : <>
          <div className="campaign-rule-note">Uma atividade a cada sete dias. Cada formato consome tempo e recursos próprios da campanha.</div>
          <form onSubmit={submit} className="campaign-form">
            <label>Formato<select value={activity} onChange={(event) => setActivity(event.target.value)}>{overview.activity_options.map((item) => <option key={item.key} value={item.key}>{item.label} · {item.days} dia(s) · R$ {number.format(item.cost_bi)} bi</option>)}</select></label>
            <div className="campaign-select-row"><label>Região<select value={region} disabled={Boolean(municipality?.id)} onChange={(event) => setRegion(event.target.value)}>{overview.region_options.map((item) => <option key={item.key} value={item.key}>{item.label}</option>)}</select></label><label>Tema<select value={issue} onChange={(event) => setIssue(event.target.value)}>{overview.issue_options.map((item) => <option key={item.key} value={item.key}>{item.label}</option>)}</select></label></div>
            <div className="campaign-city-target"><MunicipalityPicker request={request} stateCode="" value={citySearch} selectedId={municipality?.id || ''} label="Cidade da atividade (opcional)" required={false} onSelect={(selected) => { setCitySearch(selected.name); setMunicipality(selected.id ? selected : null); if (selected.profile) { const key = selected.profile.macroregion; if (key) setRegion(key); } }} />{municipality?.profile && <div className="campaign-city-target-summary"><span>{municipality.profile.state_name} · {number.format(municipality.profile.electorate_count || 0)} eleitores aptos</span><span>Referência TSE {municipality.profile.electorate_reference_year || 'indisponível'} · alcance local simulado ×{number.format(municipality.profile.municipal_campaign_reach_multiplier)}</span><span>{municipality.profile.electorate_share_of_macroregion != null ? `Representa ${number.format(municipality.profile.electorate_share_of_macroregion * 100)}% do eleitorado regional e pesa nessa proporção na projeção da região.` : ''}</span><button type="button" className="secondary-button" onClick={() => { setMunicipality(null); setCitySearch(''); }}>Usar somente a macrorregião</button></div>}</div>
            <details className="campaign-integrity-choice"><summary>Conduta eleitoral · padrão dentro das regras</summary><label>Forma de conduzir a atividade<select value={conduct} onChange={(event) => setConduct(event.target.value)}><option value="regular">Dentro das regras</option><option value="irregular">Atalho irregular (simulação)</option></select></label><p>{conduct === 'irregular' ? `Detecção: ${number.format(overview.conduct_preview?.detection_pct || 0)}%. Revisão final após esta ação: ${number.format(overview.conduct_preview?.review_if_not_detected_pct || 0)}% a ${number.format(overview.conduct_preview?.review_if_detected_pct || 0)}%. Efeito agora: +0,6 p.p. se não detectada ou −3 p.p. se detectada.` : 'Sem risco adicional de sanção eleitoral.'} {overview.conduct_preview?.notice}</p></details>
            <label>Fala ou resposta<textarea value={message} onChange={(event) => setMessage(event.target.value)} maxLength={600} rows={5} placeholder="Escreva uma resposta curta, com uma proposta que possa ser explicada ao eleitor." /></label>
            <div className="campaign-submit-row"><small>{message.length}/600 · O motor explica os critérios usados na nota.</small><button className="primary-button" disabled={busy || !overview.can_act || !selectedActivity || overview.funds_bi < selectedActivity.cost_bi || message.trim().length < 12}>{busy ? 'Registrando…' : overview.days_until_action ? `Agenda em ${overview.days_until_action} dia(s)` : overview.funds_bi < (selectedActivity?.cost_bi || 0) ? 'Fundo insuficiente' : `Realizar · ${selectedActivity?.days || 1} dia(s)`}</button></div>
          </form>
          {result && <div className="campaign-result"><div><span>AVALIAÇÃO SIMULADA</span><strong>{result.score}/100</strong></div><p>{result.activity.label} em {result.activity.municipality_name ? `${result.activity.municipality_name}/${result.activity.municipality_state_code} · ${result.activity.region_label}` : result.activity.region_label}: apoio projetado agora em {number.format(result.national_support)}%{result.activity.municipality_support != null ? ` e apoio local em ${number.format(result.activity.municipality_support)}%` : ''}.</p>{result.activity.travel_days > 0 && <p>Deslocamento de {result.activity.travel_from}: +{result.activity.travel_days} dia(s) de viagem.</p>}{result.activity?.conduct && <p className="campaign-conduct-result">{result.activity.conduct.summary}</p>}<ul>{Object.entries(result.rubric).map(([key, value]) => <li key={key}><span>{key}</span><b className={value < 0 ? 'negative' : ''}>{value > 0 ? '+' : ''}{value}</b></li>)}</ul><small>Temas alcançados: {result.activity.groups_affected.join(', ')}. Efeito eleitoral sujeito ao resultado do cenário.</small></div>}
        </>}
      </section>

      <aside className="panel campaign-side-panel">
        <span className="eyebrow">REGRAS DESTA FASE</span>
        <ul className="campaign-rules"><li>Uma atividade por semana de jogo.</li><li>Comício e viagem consomem dias; o calendário não pausa.</li><li>O fundo de campanha é separado das contas públicas.</li><li>A nota mostra pertinência, proposta, conexão humana, responsabilidade e clareza.</li><li>O apoio regional alimenta a projeção eleitoral; a eleição continua incerta.</li></ul>
        <div className="campaign-mini-bar"><span>Próxima atividade</span><b>{overview.active ? overview.days_until_action ? `em ${overview.days_until_action} dia(s)` : 'disponível' : 'na abertura'}</b></div>
      </aside>
    </div>}

    {section === 'Território' && <section className="panel campaign-territory"><div className="campaign-panel-title"><div><span className="eyebrow">APOIO POR TERRITÓRIO</span><h3>Onde a campanha está forte?</h3></div><small>Valores simulados de 0 a 100</small></div><div className="campaign-region-grid">{overview.regions.map((item) => <article key={item.key}><div><b>{item.label}</b><strong>{number.format(item.support)}%</strong></div><div className="campaign-bar"><i style={{ width: `${item.support}%` }} /></div></article>)}</div>{overview.municipalities?.length > 0 && <div className="campaign-local-support"><h4>Cidades visitadas</h4><div>{overview.municipalities.map((item) => <article key={item.municipality_id}><div><b>{item.municipality_name}/{item.state_code}</b><strong>{number.format(item.support)}%</strong></div><small>{item.electorate_count ? `${number.format(item.electorate_count)} eleitores` : 'Eleitorado indisponível'}{item.electorate_reference_year ? ` · TSE ${item.electorate_reference_year}` : ''}</small><div className="campaign-bar"><i style={{ width: `${item.support}%` }} /></div></article>)}</div></div>}<details className="campaign-groups"><summary>Ver apoio por grupo social</summary><div>{overview.groups.map((item) => <article key={item.key}><span>{item.label}</span><b>{number.format(item.support)}%</b></article>)}</div></details></section>}

    {section === 'Histórico' && <section className="panel campaign-history"><span className="eyebrow">ATIVIDADES RECENTES</span><h3>O que a campanha fez</h3>{overview.activities.length ? overview.activities.map((item) => <article key={item.id}><div><span>{item.label} · {item.municipality_name ? `${item.municipality_name}/${item.municipality_state_code} · ` : ''}{item.region_label} · {item.issue_label}</span><b>{item.score}/100</b></div><p>{item.message}</p><small>{new Date(`${item.date}T12:00:00`).toLocaleDateString('pt-BR')} · {item.days_cost} dia(s) · R$ {number.format(item.cost_bi)} bi</small></article>) : <p className="campaign-empty">As atividades aparecem aqui depois que a campanha começar.</p>}</section>}
  </section>;
}
