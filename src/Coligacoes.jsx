import { useState } from 'react';
import { br } from './format';

/** Coligação (eleições majoritárias): quem já está na chapa, o tempo de TV somado e os convites possíveis, com a chance de aceitação de cada oferta. */
export default function Coligacoes({ view, tv, busy, onInvite }) {
  const [open, setOpen] = useState(false);
  const [answer, setAnswer] = useState('');   // resposta do último convite, mostrada aqui mesmo (o aviso geral não aparece nesta tela)
  if (!view) return null;
  return <section className="coalition" aria-label="Coligações">
    <div className="coalition-head"><div><span className="eyebrow">CHAPA E TEMPO DE TV</span><h4>Coligações</h4></div>
      {view.bonus_pp > 0 && <strong className="coalition-bonus">+{br(view.bonus_pp, 1)} p.p.<small>votos dos aliados</small></strong>}</div>
    <p className="coalition-tv">{tv?.text}</p>
    {view.partners.length > 0 && <ul className="coalition-partners">{view.partners.map((p) => <li key={p.party}><b>{p.party}</b><span>{p.offer === 'vice' ? 'vice da chapa' : p.offer === 'secretarias' ? 'secretarias prometidas' : 'pontos do programa'} · +{br(p.transfer_pp, 1)} p.p.{p.distance_pct > 40 ? ' · aliança distante do seu campo' : ''}</span></li>)}</ul>}
    {answer && <p className="coalition-answer" role="status">{answer}</p>}
    {view.log?.length > 0 && <ul className="coalition-log">{view.log.slice().reverse().slice(0, 4).map((l, i) => <li key={i}>{l.text}</li>)}</ul>}
    {view.obligations.length > 0 && <p className="coalition-note">Compromissos assumidos: {view.obligations.map((o) => `${o.party} (${o.what})`).join(', ')}.</p>}
    {view.can_invite
      ? <>
        <button type="button" className="quiet-button" onClick={() => setOpen(!open)}>{open ? 'Ocultar partidos' : `Convidar partidos (${view.partners.length}/${view.max_partners} na chapa)`}</button>
        {open && <div className="territory-table-wrap"><table className="territory-table"><thead><tr><th>Partido</th><th>Cadeiras</th><th>TV</th><th>Distância</th><th>Proposta (chance de aceitar)</th></tr></thead>
          <tbody>{view.candidates.map((c) => <tr key={c.party}><td>{c.party}<small> {c.spectrum}</small></td><td>{c.seats}</td><td>{br(c.tv_pct, 1)}%</td><td>{c.distance_pct}%</td>
            <td>{c.offers.map((o) => <button key={o.id} type="button" className="quiet-button" disabled={busy || !o.available} title={o.text} onClick={async () => setAnswer((await onInvite(c.party, o.id)) || '')}>{o.short} ({o.chance_pct}%)</button>)}</td></tr>)}</tbody></table></div>}
      </>
      : <p className="coalition-note">{view.partners.length >= view.max_partners ? 'A chapa está completa.' : 'Coligações só podem ser formadas antes do fim da campanha.'}</p>}
  </section>;
}
