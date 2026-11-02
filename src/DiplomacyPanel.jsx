import { useEffect, useState } from 'react';
import { fetchAuthSession } from 'aws-amplify/auth';

async function api(path, options, authEnabled) {
  const headers = { 'Content-Type': 'application/json', ...(options?.headers || {}) };
  if (authEnabled) {
    const session = await fetchAuthSession();
    const token = session.tokens?.accessToken?.toString();
    if (!token) throw new Error('Sua sessão expirou. Entre novamente.');
    headers.Authorization = `Bearer ${token}`;
  }
  const response = await fetch(path, { ...options, headers });
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || 'Falha na solicitacao');
  return data;
}

export default function DiplomacyPanel({ date, authEnabled, onState, onNotice, busy, setBusy }) {
  const [view, setView] = useState(null);
  const [country, setCountry] = useState('ARG');
  const [agenda, setAgenda] = useState('trade');
  useEffect(() => { api('/api/diplomacy', undefined, authEnabled).then(setView).catch((error) => onNotice(error.message)); }, [date, authEnabled]);

  async function act(path, body) {
    setBusy(true);
    try {
      const data = await api(path, { method: 'POST', body: JSON.stringify(body) }, authEnabled);
      onState(data.state); setView(data.diplomacy); onNotice(data.result.message);
    } catch (error) { onNotice(error.message); } finally { setBusy(false); }
  }

  return <section className="panel agenda-page diplomacy-page">
    <div className="eyebrow">RELACOES EXTERIORES · AGENDA SIMULADA</div>
    <h2>Diplomacia e visitas oficiais</h2>
    <p className="page-description">Prepare missões, acompanhe o deslocamento no calendário e participe de cúpulas. O tempo fora de Brasília e os custos de viagem entram na simulação; relações e resultados mudam quando a missão termina.</p>
    {!view ? <div className="empty-state">Carregando agenda diplomatica...</div> : <>
      {view.active_trip && <section className="flight-card" aria-live="polite">
        <div className="flight-heading"><div><span className="eyebrow">MISSÃO EM ANDAMENTO · SIMULAÇÃO</span><h3>{view.active_trip.type === 'bilateral' ? `Visita oficial a ${view.active_trip.destination}` : view.active_trip.destination}</h3><p>{view.active_trip.agenda}</p></div><strong>{view.active_trip.days_remaining} dia(s)<small>até o retorno</small></strong></div>
        <div className="flight-route"><span>{view.active_trip.route_from.toUpperCase()}</span><div className="flight-track"><i style={{ width: `${view.active_trip.route_progress}%` }}/><b style={{ left: `${view.active_trip.route_progress}%` }} aria-label={view.active_trip.phase}>✈</b></div><span>{view.active_trip.route_to.toUpperCase()}</span></div>
        <small className="flight-phase">{view.active_trip.phase}</small>
        <div className="flight-footer"><span>Retorno previsto: {new Date(`${view.active_trip.arrival_date}T12:00:00`).toLocaleDateString('pt-BR')}</span><b>R$ {(view.active_trip.cost_bi * 1000).toFixed(0)} mi registrados</b></div>
      </section>}
      <div className="diplomacy-summary">
        <article><span>Relacao bilateral media</span><b>{view.average_relation}/100</b></article>
        <article><span>Influencia multilateral</span><b>{view.multilateral_influence}/100</b></article>
        <article><span>Intervalo para nova missão</span><b>{view.active_trip ? 'Em andamento' : view.days_until_visit ? `${view.days_until_visit} dias` : 'Disponível'}</b></article>
        <article><span>Verba anual de viagens</span><b>R$ {view.travel_remaining_bi.toFixed(3)} bi livres</b><small>R$ {view.travel_spent_bi.toFixed(3)} bi usados neste ano</small></article>
      </div>
      {(() => { const selected = view.countries.find((item) => item.code === country) || view.countries[0]; return <div className="diplomacy-trip-quote">A missão para <b>{selected.name}</b> ocupa <b>{selected.trip_days} dias</b> no calendário, ida, agenda e retorno. Custo estimado: <b>R$ {(selected.travel_cost_bi * 1000).toFixed(0)} milhões</b>. O efeito diplomático só entra ao concluir a missão.</div>; })()}
      <div className="diplomacy-form">
        <label>Pais<select value={country} onChange={(event) => setCountry(event.target.value)}>{view.countries.map((item) => <option key={item.code} value={item.code}>{item.name} · {item.region}</option>)}</select></label>
        <label>Pauta<select value={agenda} onChange={(event) => setAgenda(event.target.value)}>{Object.entries(view.agendas).map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select></label>
        <button className="primary-button" disabled={busy || Boolean(view.active_trip) || view.days_until_visit > 0} onClick={() => act('/api/diplomacy/visit', { country_code: country, agenda })}>{view.active_trip ? 'Em missão' : view.days_until_visit ? `Nova visita em ${view.days_until_visit} dias` : 'Iniciar missão oficial'}</button>
      </div>
      <h3 className="subheading">Relacoes bilaterais</h3>
      <div className="country-grid">{view.countries.map((item) => <article key={item.code}><div><b>{item.name}</b><span>{item.region}</span></div><strong>{item.relation}/100</strong><small>{item.focus}</small><div className="bar"><i style={{ width: `${item.relation}%` }}/></div></article>)}</div>
      <h3 className="subheading">Cupulas e compromissos multilaterais</h3>
      {view.events.length ? view.events.map((event) => <div className="agenda-event" key={event.id}><div className="agenda-count">{event.days_until === 0 ? 'HOJE' : `EM ${event.days_until} DIAS`}<small>{event.place}</small></div><div><h3>{event.name}</h3><p>{event.description}</p><button className="secondary-button" disabled={busy || Boolean(view.active_trip) || event.days_until > 30} onClick={() => act('/api/diplomacy/events/attend', { event_id: event.id })}>{event.days_until > 30 ? 'Confirmação abre 30 dias antes' : `Iniciar missão · ${event.trip_days} dias · R$ ${(event.cost_bi * 1000).toFixed(0)} mi`}</button></div></div>) : <div className="empty-state">Nenhum evento com tempo suficiente para a viagem.</div>}
      <h3 className="subheading">Visitas recentes</h3>
      {view.visit_log.length ? view.visit_log.slice(0, 6).map((visit, index) => <div className="fiscal-line" key={`${visit.date}-${index}`}><span>{visit.date} · {visit.country} · {visit.agenda}</span><b>R$ {visit.cost_bi.toFixed(3)} bi</b></div>) : <div className="empty-state">Nenhuma visita oficial registrada.</div>}
    </>}
  </section>;
}
