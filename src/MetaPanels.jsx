import { useEffect, useMemo, useState } from 'react';
import './meta.css';

function useLoad(request, path, deps = []) {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    let live = true;
    setLoading(true); setError('');
    request(path).then((d) => { if (live) setData(d); }).catch((e) => { if (live) setError(e.message); }).finally(() => { if (live) setLoading(false); });
    return () => { live = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [path, ...deps]);
  return { data, error, loading, setData };
}

function Status({ loading, error, empty, children }) {
  if (loading) return <p className="meta-status" role="status">Carregando…</p>;
  if (error) return <p className="meta-status meta-error" role="alert">{error}</p>;
  if (empty) return <p className="meta-status">Nada para mostrar ainda.</p>;
  return children;
}

const GRADE_CLASS = { S: 'g-s', A: 'g-a', B: 'g-b', C: 'g-c', D: 'g-d', F: 'g-f' };
const PART_LABELS = { pais: 'O país que você entrega', popularidade: 'Popularidade', governar: 'Capacidade de governar', mundo: 'Posição no mundo', integridade: 'Integridade', promessas: 'Promessas e programas', preco: 'O preço do mandato' };

/* ---------- Congresso ---------- */
export function CongressPanel({ request, state }) {
  const { data, error, loading } = useLoad(request, '/api/legislature', [state?.date]);
  const [house, setHouse] = useState('camara');
  const [party, setParty] = useState('todos');
  const [query, setQuery] = useState('');
  const [open, setOpen] = useState(null);
  const [shown, setShown] = useState(20);
  useEffect(() => { setShown(20); }, [house, party, query]);
  const members = useMemo(() => {
    if (!data) return [];
    const list = house === 'camara' ? data.parlamentares : data.senadores;
    return list.filter((m) => (party === 'todos' || m.party === party) && m.name.toLowerCase().includes(query.toLowerCase()));
  }, [data, house, party, query]);
  const maxSeats = data ? Math.max(...data.partidos.map((p) => p[house])) : 1;
  return <section className="panel meta-page">
    <h2>Câmara e Senado</h2>
    <p className="page-description">513 deputados e 81 senadores inventados, gerados pela semente da partida. Projetos de lei e PECs enviados na aba Medidas são votados um a um quando chega a data da decisão.</p>
    <Status loading={loading} error={error}>{data && <>
      <div className="meta-tabs" role="tablist" aria-label="Casa legislativa">
        {[['camara', `Câmara · ${data.camara_total}`], ['senado', `Senado · ${data.senado_total}`], ['votacoes', 'Votações']].map(([id, label]) =>
          <button key={id} role="tab" aria-selected={house === id} className={house === id ? 'meta-tab active' : 'meta-tab'} onClick={() => setHouse(id)}>{label}</button>)}
      </div>
      <div className="meta-cards">
        <article><span>APOIO AGREGADO</span><strong>{Math.round(data.apoio_agregado)}</strong><small>Base da disposição de voto</small></article>
        <article><span>LEIS APROVADAS</span><strong>{data.leis_aprovadas}</strong><small>Neste mandato</small></article>
        <article><span>REJEITADAS</span><strong>{data.leis_rejeitadas}</strong><small>Derrotas no plenário</small></article>
        <article><span>EM TRAMITAÇÃO</span><strong>{data.em_tramitacao.length}</strong><small>Aguardando votação</small></article>
      </div>
      {house !== 'votacoes' && <>
        <h3 className="subheading">Bancadas</h3>
        <ul className="party-bars">{data.partidos.map((p) => <li key={p.id}>
          <button className={party === p.id ? 'party-row active' : 'party-row'} onClick={() => setParty(party === p.id ? 'todos' : p.id)} aria-pressed={party === p.id} title={p.name}>
            <b>{p.id}</b><span className="bar"><i style={{ width: `${(p[house] / maxSeats) * 100}%` }} /></span><em>{p[house]}</em><small>adesão {p.adesao_media}%</small>
          </button></li>)}</ul>
        <div className="meta-filter"><label>Buscar parlamentar <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Nome" /></label>
          {party !== 'todos' && <button className="quiet-button" onClick={() => setParty('todos')}>Limpar partido {party}</button>}</div>
        <p className="meta-count">{members.length} parlamentar(es)</p>
        {members.length === 0 ? <p className="meta-status">Nenhum parlamentar com esse filtro.</p> :
          <ul className="member-list">{members.slice(0, shown).map((m) => <li key={m.id}><b>{m.name}</b><span>{m.party} · {m.state}</span><small>adesão {Math.round(m.loyalty * 100)}% · {m.ideology > 0.2 ? 'direita' : m.ideology < -0.2 ? 'esquerda' : 'centro'}</small></li>)}</ul>}
        {members.length > shown && <button className="secondary-button" onClick={() => setShown(shown + 20)}>Mostrar mais ({members.length - shown} restantes)</button>}
      </>}
      {house === 'votacoes' && <>
        <h3 className="subheading">Em tramitação</h3>
        {data.em_tramitacao.length === 0 ? <p className="meta-status">Nenhum projeto aguardando votação. Envie um projeto de lei ou PEC na aba Medidas.</p> :
          <ul className="vote-list">{data.em_tramitacao.map((b) => <li key={b.id}><b>{b.title}</b><span>{b.instrument} · decisão em {new Date(`${b.decision_date}T12:00:00`).toLocaleDateString('pt-BR')}</span></li>)}</ul>}
        <h3 className="subheading">Votações realizadas</h3>
        {data.votacoes.length === 0 ? <p className="meta-status">Ainda não houve votação.</p> :
          <ul className="vote-list">{data.votacoes.map((v) => {
            const c = v.resultado.camara;
            return <li key={v.bill_id}>
              <button className="vote-head" onClick={() => setOpen(open === v.bill_id ? null : v.bill_id)} aria-expanded={open === v.bill_id}>
                <b>{v.title}</b><span className={v.aprovado ? 'vote-ok' : 'vote-no'}>{v.aprovado ? 'Aprovado' : 'Rejeitado'}</span>
                <small>{v.instrument} · Câmara {c.sim} sim / {c.nao} não / {c.abstencao} abst. (precisava {c.necessarios}){v.resultado.senado ? ` · Senado ${v.resultado.senado.sim} sim` : ''}</small>
              </button>
              {open === v.bill_id && <div className="vote-detail">
                <table><caption>Voto por partido na Câmara</caption><thead><tr><th>Partido</th><th>Sim</th><th>Não</th><th>Abst.</th></tr></thead>
                  <tbody>{Object.entries(c.por_partido || {}).map(([p, r]) => <tr key={p}><td>{p}</td><td>{r.sim}</td><td>{r.nao}</td><td>{r.abstencao}</td></tr>)}</tbody></table>
              </div>}
            </li>; })}</ul>}
      </>}
    </>}</Status>
  </section>;
}

function DebateBlock({ request, version, onNotice, onWeek }) {
  const { data, error, loading, setData } = useLoad(request, '/api/campaign-debate', [version]);
  const [choice, setChoice] = useState('');
  const [issue, setIssue] = useState('');
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null);
  async function go(picked) {
    setBusy(true);
    try {
      const out = await request('/api/campaign-debate/attend', { method: 'POST', body: JSON.stringify({ choice: picked, issue, message }) });
      setResult(out.result); setData(out.overview); onWeek?.(out.week); setChoice('');
      onNotice?.(out.result.score == null ? 'Você recusou o debate: −1 de momentum e uma ação de rua extra.' : `Debate: nota ${out.result.score}, momentum ${out.result.momentum_delta >= 0 ? '+' : ''}${out.result.momentum_delta}.`);
    } catch (e) { onNotice?.(e.message); } finally { setBusy(false); }
  }
  if (loading || error || !data) return null;
  if (!data.scheduled && !result) return null;
  return <section className="meta-status" aria-label="Debate da semana"><h3 className="subheading">Debate desta semana</h3>
    {data.scheduled ? <>
      <p>Um debate acontece nesta semana. Escolha como participar.</p>
      <div className="meta-tabs">{data.choices.map((c) => <button key={c.key} className={choice === c.key ? 'meta-tab active' : 'meta-tab'} aria-pressed={choice === c.key} onClick={() => setChoice(c.key)} title={c.text}>{c.label}</button>)}</div>
      {choice && <p className="meta-count">{data.choices.find((c) => c.key === choice).text}</p>}
      {choice === 'participar' && <div className="week-region">
        <label>Tema <select value={issue} onChange={(e) => setIssue(e.target.value)}><option value="">Escolha…</option>{data.issues.map((i) => <option key={i.key} value={i.key}>{i.label}</option>)}</select></label>
        <label>Sua resposta (mínimo 40 caracteres)<textarea rows={4} value={message} onChange={(e) => setMessage(e.target.value)} maxLength={1200} /></label></div>}
      {choice && <button className="primary-button" disabled={busy || (choice === 'participar' && (!issue || message.trim().length < 40))} onClick={() => go(choice)}>{busy ? 'Enviando…' : 'Confirmar'}</button>}
    </> : <p>Debate desta semana resolvido.</p>}
    {result && <p role="status">Resultado: {result.score == null ? 'recusado' : `nota ${result.score}`} · momentum {result.momentum_delta >= 0 ? '+' : ''}{result.momentum_delta}{result.low_energy_penalty ? ` · energia baixa (−${result.low_energy_penalty})` : ''}.</p>}
  </section>;
}

function Commitments({ request, version, onNotice }) {
  const [tick, setTick] = useState(0);
  const { data, error, loading } = useLoad(request, '/api/commitments', [version, tick]);
  async function resolve(id, fulfilled) {
    try { await request(`/api/commitments/${id}/resolve`, { method: 'POST', body: JSON.stringify({ fulfilled }) }); setTick((t) => t + 1);
      onNotice?.(fulfilled ? 'Compromisso cumprido: a bancada gostou.' : 'Compromisso descumprido: a bancada perdeu 20 de relação com você.'); }
    catch (e) { onNotice?.(e.message); }
  }
  return <section aria-label="Compromissos de campanha"><h3 className="subheading">O que você já prometeu</h3>
    <Status loading={loading} error={error} empty={data && data.compromissos.length === 0}>{data && <ul className="meta-notes">{data.compromissos.map((c) => <li key={c.id}>
      Um ministério para o {c.party}, pelo apoio na região {c.region} (semana {c.week}) — <b>{c.status}</b>
      {c.status === 'pendente' && <> <button className="quiet-button" onClick={() => resolve(c.id, true)}>Cumprir</button> <button className="quiet-button" onClick={() => resolve(c.id, false)}>Descumprir</button></>}
    </li>)}</ul>}</Status></section>;
}

/* ---------- Acontecimentos ---------- */
const TONE_LABEL = { dialogo: 'Diálogo', dura: 'Linha dura', etica: 'Ética', passiva: 'Omissão', neutra: 'Neutra', fisiologica: 'Fisiologismo' };

export function StoryPanel({ request, state, onNotice }) {
  const [tick, setTick] = useState(0);
  const { data, error, loading, setData } = useLoad(request, '/api/story', [state?.date, tick]);
  const [busy, setBusy] = useState(false);
  const [last, setLast] = useState(null);
  async function choose(event, choice) {
    setBusy(true);
    try {
      const out = await request(`/api/story/${event.id}/respond`, { method: 'POST', body: JSON.stringify({ choice }) });
      setData(out.overview); setLast(out.entry); setTick((t) => t + 1);
      onNotice?.(`${event.title}: ${out.entry.outcome}`);
    } catch (e) { onNotice?.(e.message); } finally { setBusy(false); }
  }
  const fmt = (d) => `${d.delta > 0 ? '+' : ''}${d.delta} ${d.label}`;
  return <section className="panel meta-page">
    <h2>O que está acontecendo</h2>
    <p className="page-description">Decisões têm prazo: se você não responder, vale a opção padrão. Oportunidades esperam mais. Tudo é fictício e as consequências são calculadas pelo motor.</p>
    <Status loading={loading} error={error}>{data && <>
      <h3 className="subheading">Pedem resposta ({data.pending.length})</h3>
      {data.pending.length === 0 ? <p className="meta-status">Nenhum acontecimento pendente. Avance o tempo para ver novidades.</p> :
        data.pending.map((ev) => <article className="story-card" key={ev.id}>
          <div className="story-head"><span className={`tag t-${ev.kind === 'decisao' ? 'correcao' : ev.kind === 'oportunidade' ? 'melhor' : 'novo'}`}>{ev.kind === 'decisao' ? 'Decisão' : 'Oportunidade'}</span>
            {ev.days_left != null && <small>{ev.days_left <= 0 ? 'Último dia' : `${ev.days_left} dia(s) para responder`}</small>}</div>
          <h3>{ev.title}</h3>{ev.inspired_by_real_event && <p className="meta-count">Versão fictícia inspirada em um episódio real{ev.remix?.label ? ` · intensidade ${ev.remix.label}` : ''}.</p>}<p>{ev.text}</p>
          <div className="story-choices">{ev.choices.map((c) => <button key={c.id} className="secondary-button" disabled={busy} onClick={() => choose(ev, c.id)}>
            <b>{c.label}</b><small>{c.hint}{c.cost_bi ? ` · R$ ${c.cost_bi} bi` : ''} · {TONE_LABEL[c.tone] || c.tone}</small></button>)}</div>
        </article>)}
      {last && <p className="meta-status" role="status"><b>{last.title}:</b> {last.outcome} <small>({last.deltas.map(fmt).join(' · ') || 'sem efeito numérico'})</small></p>}
      {Object.keys(data.profile).length > 0 && <><h3 className="subheading">Seu estilo de governo</h3>
        <ul className="meta-notes">{Object.entries(data.profile).map(([k, v]) => <li key={k}>{TONE_LABEL[k] || k}: {v}</li>)}{data.unanswered > 0 && <li>Sem resposta no prazo: {data.unanswered}</li>}</ul></>}
      <details className="agenda-more" open={data.pending.length === 0}><summary>Histórico ({data.history.length})</summary>
      {data.history.length === 0 ? <p className="meta-status">Ainda não há histórico.</p> :
        <ul className="vote-list">{data.history.map((h) => <li key={h.id}><b>{h.title}</b>
          <span>{new Date(`${h.on}T12:00:00`).toLocaleDateString('pt-BR')} · {h.choice_label}{h.auto ? ' (opção padrão)' : ''}</span>
          <small>{h.outcome} {h.deltas.length > 0 && `(${h.deltas.map(fmt).join(' · ')})`}</small></li>)}</ul>}</details>
    </>}</Status>
  </section>;
}

/* ---------- Semana de campanha ---------- */
export function CampaignWeekPanel({ request, onNotice }) {
  const [version, setVersion] = useState(0);
  const { data, error, loading, setData } = useLoad(request, '/api/campaign-week', [version]);
  const [region, setRegion] = useState('sudeste');
  const [busy, setBusy] = useState(false);
  const [jet, setJet] = useState(false);
  const [last, setLast] = useState(null);
  async function act(key) {
    setBusy(true);
    try {
      const out = await request('/api/campaign-week/act', { method: 'POST', body: JSON.stringify({ action: key, region, jet }) });
      setData(out.overview); setLast(out.result);
      onNotice?.(out.result.refused
        ? `${out.result.label}: o governador recusou por ora (faltaram ${out.result.shortfall} pontos de disposição), mas ficou mais receptivo.`
        : `${out.result.label}: +${out.result.gain} ponto(s) de apoio.`);
    } catch (e) { onNotice?.(e.message); } finally { setBusy(false); }
  }
  async function close() {
    setBusy(true);
    try {
      const out = await request('/api/campaign-week/close', { method: 'POST', body: '{}' });
      setData(out.overview); setLast(null);
      onNotice?.(`Semana fechada: +${out.points_gained} ponto(s) no total.`);
    } catch (e) { onNotice?.(e.message); } finally { setBusy(false); }
  }
  return <section className="panel meta-page">
    <h2>Palanque</h2>
    <p className="page-description">Cada semana você tem algumas ações livres. Ações gastam energia e caixa; repetir a mesma ação no mesmo lugar rende menos, e abaixo de 35 de energia tudo rende 60%.</p>
    <Status loading={loading} error={error}>{data && <>
      <div className="meta-cards">
        <article><span>SEMANA</span><strong>{data.week}</strong><small>{data.remaining_actions} de {data.free_actions} ações livres</small></article>
        <article><span>ENERGIA</span><strong>{data.energy}/{data.energy_max}</strong><div className="bar" role="progressbar" aria-valuenow={data.energy} aria-valuemin={0} aria-valuemax={data.energy_max} aria-label="Energia"><i style={{ width: `${data.energy}%` }} /></div>{data.low_energy && <small className="neg">Energia baixa: rendimento reduzido.</small>}</article>
        <article><span>CAIXA</span><strong>R$ {data.funds_mi.toLocaleString('pt-BR')} mi</strong><small>Promessas para gastar: {data.promises}</small></article>
        <article><span>APOIO NACIONAL</span><strong>{data.national_support ?? '—'}</strong><small>Média ponderada das regiões</small></article>
      </div>
      <label className="week-region">Região da ação <select value={region} onChange={(e) => setRegion(e.target.value)}>
        {data.regions.map((r) => <option key={r.key} value={r.key}>{r.label} · apoio {r.support}</option>)}</select></label>
      <p className="meta-count">{data.location ? `Você está em: ${data.regions.find((r) => r.key === data.location)?.label}. ` : 'Você ainda não saiu da capital. '}Mudar de região custa {data.travel.other_region_energy} de energia; de jatinho, {data.travel.jet_energy} de energia e R$ {data.travel.jet_mi} mi.</p>
      <label className="week-region"><input type="checkbox" checked={jet} onChange={(e) => setJet(e.target.checked)} /> Ir de jatinho quando mudar de região</label>
      {last && <p className="meta-status" role="status">Último resultado: {last.label} em {last.region}, {last.refused ? `recusado (faltaram ${last.shortfall} pontos)` : `+${last.gain}`}{last.travel_energy ? ` · viagem −${last.travel_energy} energia` : ''}{last.low_energy_penalty ? ' (energia baixa)' : ''}{last.repeat_factor < 1 ? ` · repetição ×${last.repeat_factor}` : ''}{last.raised_mi ? ` · arrecadou R$ ${last.raised_mi} mi` : ''}.</p>}
      <ul className="week-actions">{data.catalog.filter((a) => a.available).map((a) => <li key={a.key}>
        <div><b>{a.label}</b><small>{a.money_mi ? `R$ ${a.money_mi} mi` : 'sem custo'} · {a.energy < 0 ? `+${-a.energy} energia` : `${a.energy} energia`}{a.scope === 'regiao' ? ' · região' : ' · nacional'}</small><small>{a.text}</small>{!a.available && <small className="neg">{a.reason}</small>}</div>
        <button className="secondary-button" disabled={busy} onClick={() => act(a.key)}>Fazer</button></li>)}</ul>
      {data.catalog.some((a) => !a.available) && <details className="agenda-more"><summary>Indisponíveis agora ({data.catalog.filter((a) => !a.available).length})</summary>
        <ul className="week-actions">{data.catalog.filter((a) => !a.available).map((a) => <li key={a.key} className="blocked"><div><b>{a.label}</b><small>{a.reason}</small></div></li>)}</ul></details>}
      {data.this_week.length > 0 && <><h3 className="subheading">Nesta semana</h3><ul className="meta-notes">{data.this_week.map((u, i) => <li key={i}>{u.label} · {u.region} · +{u.gain}</li>)}</ul></>}
      <DebateBlock request={request} version={data.week} onNotice={onNotice} onWeek={setData} />
      <Commitments request={request} version={`${data.week}-${data.used_actions}`} onNotice={onNotice} />
      <button className="primary-button" onClick={close} disabled={busy || data.used_actions === 0}>Fechar a semana</button>
      {data.used_actions === 0 && <p className="meta-count">Use ao menos uma ação antes de fechar a semana.</p>}
    </>}</Status>
  </section>;
}

/* ---------- Placar ---------- */
const QUADROS = [['geral', 'Todos os tempos'], ['aprovacao', 'Aprovação'], ['economia', 'Economia'], ['campanhas', 'Campanhas']];

export function RankingPanel({ request, state, onNotice }) {
  const [rankShown, setRankShown] = useState(10);
  const [quadro, setQuadro] = useState('geral');
  const [nota, setNota] = useState('todas');
  const [version, setVersion] = useState(0);
  const { data, error, loading } = useLoad(request, `/api/ranking?quadro=${quadro}&nota=${nota}`, [version]);
  const score = useLoad(request, '/api/score', [state?.date]);
  const [busy, setBusy] = useState(false);
  async function submit() {
    setBusy(true);
    try { await request('/api/ranking/submit', { method: 'POST', body: '{}' }); onNotice?.('Mandato registrado no Placar da História.'); setVersion((v) => v + 1); }
    catch (e) { onNotice?.(e.message); } finally { setBusy(false); }
  }
  return <section className="panel meta-page">
    <h2>Ranking de mandatos</h2>
    <p className="page-description">Entradas marcadas como <em>simulado</em> são exemplos fictícios. O placar mostra só o presidente da ficção, nunca quem joga.</p>
    <Status loading={score.loading} error={score.error}>{score.data && <div className="score-box">
      <div className={`grade ${GRADE_CLASS[score.data.grade]}`} aria-label={`Nota ${score.data.grade}`}>{score.data.grade}</div>
      <div><b>{score.data.points} pontos · {score.data.title}</b>
        <small>{score.data.ranked ? `Multiplicador de dificuldade ×${score.data.multiplier}` : 'A dificuldade Tranquilo não conta para o ranking.'}</small>
        <ul className="parts">{Object.entries(score.data.parts).map(([k, v]) => <li key={k}><span>{PART_LABELS[k]}</span><b className={v < 0 ? 'neg' : ''}>{v > 0 ? '+' : ''}{v}</b></li>)}</ul></div>
      <button className="primary-button" onClick={submit} disabled={busy || !score.data.ranked}>{busy ? 'Registrando…' : 'Registrar mandato no placar'}</button>
    </div>}</Status>
    <div className="meta-filter" role="group" aria-label="Filtros">
      <div className="meta-tabs">{QUADROS.map(([id, label]) => <button key={id} className={quadro === id ? 'meta-tab active' : 'meta-tab'} aria-pressed={quadro === id} onClick={() => setQuadro(id)}>{label}</button>)}</div>
      <div className="meta-tabs">{['todas', 'S', 'A', 'B', 'C', 'D', 'F'].map((n) => <button key={n} className={nota === n ? 'meta-tab active' : 'meta-tab'} aria-pressed={nota === n} onClick={() => setNota(n)}>{n === 'todas' ? 'Todas' : n}</button>)}</div>
    </div>
    <Status loading={loading} error={error} empty={data && data.linhas.length === 0}>{data && <>
      <ol className="rank-list">{data.linhas.slice(0, rankShown).map((l) => <li key={l.chave}>
        <span className="pos">{l.posicao}</span>
        <span className={`grade small ${GRADE_CLASS[l.nota]}`}>{l.nota}</span>
        <div><b>{l.presidente} <small>({l.partido})</small></b><small>{l.desfechoTitulo} · aprovação {l.aprovacao}% · {l.dificuldade}{l.simulado ? ' · simulado' : ` · jogador ${l.jogador}`}</small></div>
        <strong>{l.pontos}</strong></li>)}</ol>
      {data.linhas.length > rankShown && <button className="secondary-button" onClick={() => setRankShown(rankShown + 10)}>Mostrar mais ({data.linhas.length - rankShown})</button>}
      <details className="agenda-more"><summary>Como a nota é calculada e regras do placar</summary><ul className="meta-notes">{data.regras.map((r) => <li key={r}>{r}</li>)}</ul></details></>}</Status>
  </section>;
}

/* ---------- Coleção ---------- */
export function CollectionPanel({ request, state }) {
  const { data, error, loading } = useLoad(request, '/api/collection', [state?.date]);
  const [filter, setFilter] = useState('todos');
  const list = data ? data.carimbos.filter((c) => filter === 'todos' || (filter === 'obtidos' ? c.obtido : !c.obtido)) : [];
  return <section className="panel meta-page">
    <h2>Carimbos do mandato</h2>
    <p className="page-description">Cada mandato carimba o que você fez, inclusive o absurdo. Os carimbos são desbloqueados pelo estado da partida e ficam guardados na sua conta.</p>
    <Status loading={loading} error={error}>{data && <>
      <p className="meta-count" role="status">{data.obtidos} de {data.total} carimbos{data.novos.length ? ` · ${data.novos.length} novo(s) agora!` : ''}</p>
      <div className="meta-tabs">{[['todos', 'Todos'], ['obtidos', 'Obtidos'], ['faltam', 'Faltam']].map(([id, l]) => <button key={id} className={filter === id ? 'meta-tab active' : 'meta-tab'} aria-pressed={filter === id} onClick={() => setFilter(id)}>{l}</button>)}</div>
      {list.length === 0 ? <p className="meta-status">Nenhum carimbo neste filtro.</p> :
        <ul className="stamp-grid">{list.map((c) => <li key={c.id} className={c.obtido ? `stamp got r-${c.raridade}` : 'stamp'}>
          <span className="stamp-mark" aria-hidden="true">{c.obtido ? '★' : '?'}</span><b>{c.obtido ? c.titulo : 'Carimbo oculto'}</b>
          <small>{c.obtido ? c.descricao : 'Continue governando para descobrir.'}</small><em>{c.raridade}</em></li>)}</ul>}
    </>}</Status>
  </section>;
}

/* ---------- Diário ---------- */
export function DiaryPanel({ request }) {
  const { data, error, loading } = useLoad(request, '/api/diary');
  const TAG = { novo: 'Novo', melhor: 'Melhor', correcao: 'Correção' };
  return <section className="panel meta-page">
    <h2>Diário de atualizações</h2>
    <Status loading={loading} error={error} empty={data && !data.edicoes.length}>{data && data.edicoes.map((e) => <article className="diary-edition" key={e.versao}>
      <h3>Versão {e.versao} <small>{new Date(`${e.data}T12:00:00`).toLocaleDateString('pt-BR', { day: 'numeric', month: 'long', year: 'numeric' })}</small></h3>
      <ul>{e.notas.map((n) => <li key={n.texto}><span className={`tag t-${n.tipo}`}>{TAG[n.tipo] || n.tipo}</span>{n.texto}</li>)}</ul></article>)}</Status>
  </section>;
}

/* ---------- Planos, Legado, Termos e Créditos (informativo) ---------- */
export function InfoPanel({ section }) {
  const content = {
    Planos: <>
      <h2>Modos e limites</h2>
      <p className="page-description">Esta reconstrução roda localmente e não cobra nada. A tabela abaixo descreve os planos observados no site de referência, apenas como informação; nenhuma compra é feita aqui.</p>
      <div className="meta-cards plans">
        <article><span>LIVRE · referência</span><strong>R$ 0</strong><small>Primeiro ano de mandato, um mandato guardado.</small></article>
        <article><span>PRO · referência</span><strong>R$ 19,99/30 dias</strong><small>Meses 13 a 48 do mandato (valor observado no site público).</small></article>
        <article><span>ESTADISTA · referência</span><strong>R$ 49,99/30 dias</strong><small>Sandbox fora do ranking, chave própria de IA e 10 mandatos guardados.</small></article>
        <article><span>NESTA VERSÃO LOCAL</span><strong>Tudo liberado</strong><small>Sem limite de meses. A chave de IA (Gemini) é sua, no arquivo backend/.env.</small></article>
      </div></>,
    Legado: <>
      <h2>Legado</h2>
      <p className="page-description">O site de referência tem um segundo jogo, o Legado: temporadas de 90 dias, eleições a cada temporada com apuração ao vivo e quatro classes (Político, Jornalista, Advogado, Empresário), com conta separada.</p>
      <p className="meta-status">O multiplayer exige servidor compartilhado e contas, o que está fora desta versão local. A <b>Carreira</b> do jogo cobre o percurso de político em modo solo; as outras classes e as temporadas ao vivo continuam pendentes.</p></>,
    Termos: <>
      <h2>Termos e avisos</h2>
      <ul className="meta-notes">
        <li>Este jogo é uma obra de ficção satírica. Candidatos, parlamentares, pesquisas, empresas e acontecimentos são inventados.</li>
        <li>Nenhuma pessoa real participa do jogo; nenhum fato real atual é afirmado pelos indicadores.</li>
        <li>Os textos podem ser gerados por IA se você configurar uma chave; sem chave, o modo local é determinístico e nada sai do seu computador.</li>
        <li>Os dados do jogo ficam no seu navegador/servidor local (SQLite). Nada é enviado a terceiros sem a sua configuração.</li>
        <li>Esta é uma reconstrução independente, baseada em observação pública; não é afiliada ao produto de referência.</li>
      </ul></>,
    Créditos: <>
      <h2>Créditos</h2>
      <ul className="meta-notes">
        <li>Reconstrução independente construída sobre o Civiciclo, com regras próprias.</li>
        <li>Dados públicos de partidos podem vir do cadastro do TSE (importação manual, com fonte e licença registradas).</li>
        <li>Observação do site de referência feita com o REA (Reverse Engineer Anything) sobre páginas públicas.</li>
      </ul></>,
  }[section];
  return <section className="panel meta-page"><div className="eyebrow">{section.toUpperCase()}</div>{content}</section>;
}
