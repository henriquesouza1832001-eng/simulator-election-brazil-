import { useEffect, useState } from 'react';
import MunicipalityPicker from './MunicipalityPicker';
import './meta.css';
import './party.css';

const UFS = ['AC', 'AL', 'AM', 'AP', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MG', 'MS', 'MT', 'PA', 'PB', 'PE', 'PI', 'PR', 'RJ', 'RN', 'RO', 'RR', 'RS', 'SC', 'SE', 'SP', 'TO'];
const SPECTRUMS = [['esquerda', 'Esquerda'], ['centro_esquerda', 'Centro-esquerda'], ['centro', 'Centro'], ['centro_direita', 'Centro-direita'], ['direita', 'Direita']];
const CAUSES = [['moradia', 'Moradia'], ['saude', 'Saúde'], ['educacao', 'Educação'], ['transporte', 'Transporte'], ['seguranca', 'Segurança'], ['ambiente', 'Meio ambiente'],
  ['cultura', 'Cultura'], ['esporte', 'Esporte'], ['trabalho', 'Trabalho e renda'], ['mulheres', 'Direitos das mulheres'], ['juventude', 'Juventude'], ['idosos', 'Pessoas idosas']];
const STAGES = [['eleitor', 'Eleitor engajado'], ['militante', 'Militante'], ['filiado', 'Filiado(a)'], ['quadro', 'Quadro do partido'], ['pre_candidato', 'Pré-candidato(a)']];

/* Formulário de início: cartão "Militante e partidário" da tela inicial. */
export function PartyStartForm({ request, onState, onContinue, busy, setBusy, setNotice }) {
  const [name, setName] = useState('');
  const [uf, setUf] = useState('');
  const [city, setCity] = useState({ id: '', name: '' });
  const [spectrum, setSpectrum] = useState('centro');
  const [cause, setCause] = useState('educacao');
  const ready = name.trim().length >= 2 && uf && city.id;
  async function submit(event) {
    event.preventDefault();
    setBusy(true); setNotice('');
    try {
      const data = await request('/api/party-path/start', { method: 'POST', body: JSON.stringify({ name: name.trim(), state_code: uf, municipality_id: city.id, spectrum, cause }) });
      onState(data); onContinue();
    } catch (e) { setNotice(e.message); } finally { setBusy(false); }
  }
  return <form className="career-start-form party-start" onSubmit={submit}>
    <div className="career-start-heading"><div><span className="eyebrow">MILITÂNCIA E PARTIDO</span><h2>Comece como eleitor engajado</h2></div><span className="career-start-date">Rumo à eleição municipal de 2028</span></div>
    <p className="meta-count">Você começa sem partido e sem mandato. Faça militância, filie-se, ganhe espaço no diretório e lance a pré-candidatura a vereador na sua cidade. O personagem é fictício.</p>
    <div className="career-start-fields">
      <label>Nome público<input value={name} onChange={(e) => setName(e.target.value.slice(0, 80))} maxLength={80} placeholder="Seu nome" required /></label>
      <label>UF<select value={uf} onChange={(e) => { setUf(e.target.value); setCity({ id: '', name: '' }); }} required><option value="">Escolha…</option>{UFS.map((u) => <option key={u} value={u}>{u}</option>)}</select></label>
      <MunicipalityPicker request={request} stateCode={uf} value={city.name} selectedId={city.id} required disabled={!uf} label="Sua cidade (código oficial do IBGE)" onSelect={(item) => setCity({ id: item.id, name: item.name })} />
      <label>Posição política (sua, não do partido)<select value={spectrum} onChange={(e) => setSpectrum(e.target.value)}>{SPECTRUMS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}</select></label>
      <label>Causa que move você<select value={cause} onChange={(e) => setCause(e.target.value)}>{CAUSES.map(([v, l]) => <option key={v} value={v}>{l}</option>)}</select></label>
    </div>
    <button className="primary-button" disabled={busy || !ready}>Começar a trajetória <b>→</b></button>
  </form>;
}

function Meter({ label, value, max = 100, tone }) {
  return <div className={`pp-meter ${tone || ''}`}><div className="pp-meter-head"><span>{label}</span><b>{value}</b></div>
    <div className="bar" role="progressbar" aria-label={label} aria-valuenow={Math.round(value)} aria-valuemin={0} aria-valuemax={max}><i style={{ width: `${Math.min(100, (value / max) * 100)}%` }} /></div></div>;
}

export default function PartyPathPanel({ request, state, onNotice, onLaunched }) {
  const [ov, setOv] = useState(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [last, setLast] = useState(null);
  const [catalog, setCatalog] = useState(null);
  const [party, setParty] = useState('');
  const [custom, setCustom] = useState('');
  const [ideology, setIdeology] = useState('Centro');

  const load = () => request('/api/party-path').then(setOv).catch((e) => setError(e.message));
  useEffect(() => { load(); }, [state?.date]); // eslint-disable-line
  useEffect(() => { request('/api/career/options').then((c) => { setCatalog(c); setParty(c.parties?.[0] || ''); }).catch(() => {}); }, []); // eslint-disable-line

  async function call(path, body, okMessage) {
    setBusy(true); setError('');
    try {
      const out = await request(path, { method: 'POST', body: JSON.stringify(body || {}) });
      if (out.overview) setOv(out.overview); else if (out.stage) setOv(out); else await load();
      if (out.result) setLast(out.result);
      if (okMessage) onNotice?.(typeof okMessage === 'function' ? okMessage(out) : okMessage);
      return out;
    } catch (e) { setError(e.message); onNotice?.(e.message); } finally { setBusy(false); }
  }

  async function launch(office) {
    const out = await call('/api/party-path/launch', { office }, 'Pré-candidatura lançada! A campanha segue no módulo de carreira.');
    if (out?.state) onLaunched?.(out.state);
  }

  if (error && !ov) return <section className="panel meta-page"><p className="meta-status meta-error" role="alert">{error}</p></section>;
  if (!ov) return <section className="panel meta-page"><p className="meta-status" role="status">Carregando trajetória…</p></section>;
  if (!ov.active) return <section className="panel meta-page"><p className="meta-status">A trajetória partidária terminou. Siga pela aba Carreira.</p></section>;

  const stageIndex = STAGES.findIndex(([k]) => k === ov.stage);
  const m = ov.meters;
  const partyName = party === '__custom__' ? custom.trim() : party;
  const canAffiliate = ov.stage === 'militante' && ov.next.ready && ov.affiliation.status !== 'analise';

  return <section className="panel meta-page party-path">
    <h2>{ov.name} · {ov.stage_label}</h2>
    <p className="page-description">{ov.municipality} ({ov.state_code}) · causa: {ov.cause}. {ov.party ? `Filiado(a) a ${ov.party}${ov.post ? `, ${ov.post}` : ''}.` : 'Sem partido.'} Próximas eleições: municipal em {new Date(`${ov.next_municipal_election}T12:00:00`).toLocaleDateString('pt-BR')} ({ov.days_to_municipal_election} dias) e geral em {new Date(`${ov.next_general_election}T12:00:00`).toLocaleDateString('pt-BR')} ({ov.days_to_general_election} dias).</p>

    <ol className="pp-stages" aria-label="Etapas da trajetória">{STAGES.map(([k, l], i) => <li key={k} className={i < stageIndex ? 'done' : i === stageIndex ? 'current' : ''} aria-current={i === stageIndex ? 'step' : undefined}><span>{i + 1}</span>{l}</li>)}</ol>

    <div className="pp-meters">
      <Meter label="Energia" value={m.energy} tone={ov.low_energy ? 'low' : ''} />
      <Meter label="Reputação" value={m.reputation} />
      <Meter label="Contatos" value={m.network} />
      <Meter label="Militância" value={m.militancy} />
      {(ov.party || m.standing > 0) && <Meter label="Prestígio no partido" value={m.standing} />}
    </div>
    {ov.low_energy && <p className="meta-status" role="alert">Energia baixa: tudo rende 60%. Descanse ou deixe o tempo passar.</p>}

    <h3 className="subheading">Próxima etapa: {ov.next.goal}</h3>
    <ul className="pp-goals">{ov.next.items.map((it) => <li key={it.label} className={it.value >= it.need ? 'ok' : ''}>{it.label}: <b>{it.value}</b> / {it.need}</li>)}</ul>
    <p className="meta-count">{ov.next.how}</p>

    {ov.affiliation.status === 'analise' && <p className="meta-status" role="status">Pedido de filiação a <b>{ov.affiliation.party}</b> em análise até {new Date(`${ov.affiliation.decision_date}T12:00:00`).toLocaleDateString('pt-BR')}. Avance o tempo para saber a resposta.</p>}
    {ov.affiliation.status === 'recusado' && <p className="meta-status" role="alert">Pedido recusado por {ov.affiliation.party}. Novo pedido a partir de {new Date(`${ov.affiliation.refused_until}T12:00:00`).toLocaleDateString('pt-BR')}.</p>}

    {ov.stage === 'militante' && <section aria-label="Pedir filiação" className="pp-box">
      <h3 className="subheading">Filiação</h3>
      <div className="elector-filters">
        <label>Partido<select value={party} onChange={(e) => setParty(e.target.value)}>{(catalog?.parties || []).map((p) => <option key={p} value={p}>{p}</option>)}<option value="__custom__">Criar partido fictício…</option></select></label>
        {party === '__custom__' && <label>Nome do partido fictício<input value={custom} onChange={(e) => setCustom(e.target.value)} maxLength={80} placeholder="Nome plausível e original" /></label>}
        <label>Linha do partido (separada da sua posição)<select value={ideology} onChange={(e) => setIdeology(e.target.value)}>{(catalog?.ideologies || SPECTRUMS.map(([, l]) => l)).map((i) => <option key={i} value={i}>{i}</option>)}</select></label>
      </div>
      <p className="meta-count">O partido analisa por 14 dias e pode recusar: pesam afinidade com a sua posição, militância, contatos e reputação. Prazos aqui são simplificações do jogo.</p>
      <button className="primary-button" disabled={busy || !canAffiliate || !partyName} onClick={() => call('/api/party-path/affiliate', { party: partyName, ideology }, 'Pedido de filiação enviado.')}>Pedir filiação</button>
      {!ov.next.ready && <p className="meta-count">Complete as metas acima para poder pedir a filiação.</p>}
    </section>}

    {ov.stage === 'filiado' && <section className="pp-box"><h3 className="subheading">Cargo no diretório</h3>
      <p className="meta-count">Disputar a secretaria do diretório municipal. Se perder, perde prestígio, mas segue filiado(a).</p>
      <button className="primary-button" disabled={busy || !ov.next.ready} onClick={() => call('/api/party-path/run-post', {}, (o) => (o.won ? 'Você foi eleito(a) para o diretório!' : 'Você perdeu a eleição do diretório.'))}>Disputar cargo no diretório</button></section>}

    {ov.stage === 'quadro' && <section className="pp-box" aria-label="Pré-candidatura"><h3 className="subheading">Pré-candidatura</h3>
      {ov.returns > 0 && <p className="meta-status" role="status">Você voltou ao diretório depois da última disputa. O resultado está na aba Carreira; aqui você reconstrói prestígio e escolhe a próxima eleição.</p>}
      <p className="meta-count">Ao lançar, a campanha começa no módulo de carreira, levando a reputação que você construiu. Cargos maiores exigem mais do partido.</p>
      <ul className="launch-offices">{(ov.next.offices || []).map((o) => <li key={o.key} className={o.ready ? 'ready' : ''}>
        <div><b>{o.label}</b><small>Eleição {o.cycle === 'municipal' ? 'municipal' : 'geral'} · exige prestígio {o.needs.standing}, contatos {o.needs.network}, reputação {o.needs.reputation}</small></div>
        <button className={o.ready ? 'primary-button' : 'secondary-button'} disabled={busy || !o.ready} onClick={() => launch(o.key)}>{o.ready ? 'Lançar' : 'Ainda não'}</button></li>)}</ul></section>}

    {last && <p className="meta-status" role="status">{last.label}: {Object.entries(last.applied).map(([k, v]) => `${v > 0 ? '+' : ''}${v} ${({ reputation: 'reputação', network: 'contatos', militancy: 'militância', standing: 'prestígio' })[k] || k}`).join(' · ') || 'recuperou energia'}{last.gaffe ? ' · deu errado' : ''}{last.repeat_factor < 1 ? ` · repetição ×${last.repeat_factor}` : ''}.</p>}

    <h3 className="subheading">O que fazer hoje</h3>
    <ul className="week-actions">{ov.actions.map((a) => <li key={a.key} className={a.available ? '' : 'blocked'}>
      <div><b>{a.label}</b><small>{a.energy < 0 ? `+${-a.energy} energia` : `${a.energy} energia`}</small><small>{a.text}</small>{!a.available && <small className="neg">{a.reason}</small>}</div>
      <button className="secondary-button" disabled={busy || !a.available} onClick={() => call('/api/party-path/act', { action: a.key })}>Fazer</button></li>)}</ul>
    <p className="meta-count">A energia volta com o tempo. Use “Próximo dia” ou “Avançar 7 dias” no topo. Acontecimentos aparecem na aba Acontecimentos.</p>

    <h3 className="subheading">Diário da trajetória</h3>
    {ov.log.length === 0 ? <p className="meta-status">Nada registrado ainda.</p> : <ul className="meta-notes">{ov.log.map((l, i) => <li key={i}>{new Date(`${l.date}T12:00:00`).toLocaleDateString('pt-BR')} — {l.text}</li>)}</ul>}
    <p className="meta-count">{ov.note}</p>
  </section>;
}
