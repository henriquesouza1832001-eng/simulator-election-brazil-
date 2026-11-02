import { useEffect, useState } from 'react';

async function api(path, options) {
  const response = await fetch(path, { headers: { 'Content-Type': 'application/json' }, ...options });
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || 'Falha na solicitacao');
  return data;
}

export default function DiplomacyPanel({ onState, onNotice, busy, setBusy }) {
  const [view, setView] = useState(null);
  const [country, setCountry] = useState('ARG');
  const [agenda, setAgenda] = useState('trade');
  useEffect(() => { api('/api/diplomacy').then(setView).catch((error) => onNotice(error.message)); }, []);

  async function act(path, body) {
    setBusy(true);
    try {
      const data = await api(path, { method: 'POST', body: JSON.stringify(body) });
      onState(data.state); setView(data.diplomacy); onNotice(data.result.message);
    } catch (error) { onNotice(error.message); } finally { setBusy(false); }
  }

  return <section className="panel agenda-page diplomacy-page">
    <div className="eyebrow">RELACOES EXTERIORES · AGENDA SIMULADA</div>
    <h2>Diplomacia e visitas oficiais</h2>
    <p className="page-description">Receba paises, agende visitas e participe de cupulas. As viagens usam a verba anual de deslocamentos ja contabilizada no orcamento; eventos e resultados sao simulados.</p>
    {!view ? <div className="empty-state">Carregando agenda diplomatica...</div> : <>
      <div className="diplomacy-summary">
        <article><span>Relacao bilateral media</span><b>{view.average_relation}/100</b></article>
        <article><span>Influencia multilateral</span><b>{view.multilateral_influence}/100</b></article>
        <article><span>Proxima visita</span><b>{view.days_until_visit ? `${view.days_until_visit} dias` : 'Disponivel'}</b></article>
        <article><span>Verba anual de viagens</span><b>R$ {view.travel_remaining_bi.toFixed(3)} bi livres</b><small>R$ {view.travel_spent_bi.toFixed(3)} bi usados neste ano</small></article>
      </div>
      <div className="diplomacy-form">
        <label>Pais<select value={country} onChange={(event) => setCountry(event.target.value)}>{view.countries.map((item) => <option key={item.code} value={item.code}>{item.name} · {item.region}</option>)}</select></label>
        <label>Pauta<select value={agenda} onChange={(event) => setAgenda(event.target.value)}>{Object.entries(view.agendas).map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select></label>
        <button className="primary-button" disabled={busy || view.days_until_visit > 0} onClick={() => act('/api/diplomacy/visit', { country_code: country, agenda })}>Agendar visita oficial</button>
      </div>
      <h3 className="subheading">Relacoes bilaterais</h3>
      <div className="country-grid">{view.countries.map((item) => <article key={item.code}><div><b>{item.name}</b><span>{item.region}</span></div><strong>{item.relation}/100</strong><small>{item.focus}</small><div className="bar"><i style={{ width: `${item.relation}%` }}/></div></article>)}</div>
      <h3 className="subheading">Cupulas e compromissos multilaterais</h3>
      {view.events.length ? view.events.map((event) => <div className="agenda-event" key={event.id}><div className="agenda-count">{event.days_until < 0 ? `${Math.abs(event.days_until)} DIAS APOS` : event.days_until === 0 ? 'HOJE' : `EM ${event.days_until} DIAS`}<small>{event.place}</small></div><div><h3>{event.name}</h3><p>{event.description}</p><button className="secondary-button" disabled={busy || event.days_until < -30 || event.days_until > 30} onClick={() => act('/api/diplomacy/events/attend', { event_id: event.id })}>{event.days_until > 30 ? 'Confirmacao abre 30 dias antes' : event.days_until < -30 ? 'Prazo encerrado' : 'Confirmar participacao'}</button></div></div>) : <div className="empty-state">Nenhum evento multilateral proximo.</div>}
      <h3 className="subheading">Visitas recentes</h3>
      {view.visit_log.length ? view.visit_log.slice(0, 6).map((visit, index) => <div className="fiscal-line" key={`${visit.date}-${index}`}><span>{visit.date} · {visit.country} · {visit.agenda}</span><b>R$ {visit.cost_bi.toFixed(3)} bi</b></div>) : <div className="empty-state">Nenhuma visita oficial registrada.</div>}
    </>}
  </section>;
}
