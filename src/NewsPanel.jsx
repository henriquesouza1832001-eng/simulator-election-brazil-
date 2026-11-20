import { useEffect, useMemo, useState } from 'react';
import { Page, Section, Badge, Empty, Segmented } from './ui';
import { effectText } from './format';

const KIND = { imprensa: 'Imprensa', congresso: 'Congresso', mercado: 'Mercado', crise: 'Crise', regulador: 'Regulador', resposta: 'Resposta do governo' };
const TONE = { crise: 'bad', regulador: 'warn', resposta: 'good' };
const monthName = (iso) => new Date(`${iso.slice(0, 7)}-15T12:00:00`).toLocaleDateString('pt-BR', { month: 'long', year: 'numeric' });
const dayName = (iso) => new Date(`${iso}T12:00:00`).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' });
const PAGE = 12;

export default function NewsPanel({ request, state, onState, onNotice }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [shown, setShown] = useState(PAGE);
  const [kind, setKind] = useState('todas');
  const load = () => request('/api/consequences').then(setData).catch((e) => setError(e.message));
  useEffect(() => { load(); }, [state?.date]);

  async function answer(crisis, option) {
    try {
      const r = await request(`/api/consequences/${encodeURIComponent(crisis.id)}/respond?option=${encodeURIComponent(option.id)}`, { method: 'POST', body: '{}' });
      setData(r.overview);
      if (r.state) onState?.(r.state);
      onNotice?.(`Resposta registrada: ${option.label}. Efeitos: ${effectText(r.effects) || 'sem efeito direto'}.`);
    } catch (e) { onNotice?.(e.message); }
  }

  const groups = useMemo(() => {
    const out = [];
    // notícias com data própria (movimentos de rivais, pesquisas) podem chegar fora de ordem: ordena por data para não repetir o mês
    [...(data?.feed || [])].sort((x, y) => String(y.date || '').localeCompare(String(x.date || ''))).filter((n) => kind === 'todas' || n.kind === kind).slice(0, shown).forEach((n) => {
      const m = (n.date || '').slice(0, 7);
      if (!out.length || out[out.length - 1].m !== m) out.push({ m, items: [] });
      out[out.length - 1].items.push(n);
    });
    return out;
  }, [data, shown, kind]);
  const kinds = useMemo(() => { const c = {}; (data?.feed || []).forEach((n) => { c[n.kind] = (c[n.kind] || 0) + 1; }); return c; }, [data]);
  const filtered = (data?.feed || []).filter((n) => kind === 'todas' || n.kind === kind).length;

  if (error) return <Page title="Imprensa e reações"><p className="ds-empty" role="alert">{error}</p></Page>;
  if (!data) return <Page title="Imprensa e reações"><p className="ds-muted" role="status">Carregando…</p></Page>;

  return <Page title="Imprensa e reações" lead="Toda decisão importante gera notícias, reações das bancadas e do mercado, e às vezes uma crise. As reações são simuladas e usam só fatos do jogo.">
    {data.pending.length > 0 && <Section title="Decisões que esperam resposta" hint="Se o prazo acabar sem resposta, vale a última opção da lista.">
      {data.pending.map((c) => <article className="ds-card ds-decision" key={c.id}>
        <h4>{c.title} <Badge tone="warn">prazo {dayName(c.deadline)}</Badge></h4>
        <p>{c.text}</p>
        <div className="ds-options">{c.options.map((o, i) => <button key={o.id} type="button" className={i === c.options.length - 1 ? 'quiet-button' : 'secondary-button'} onClick={() => answer(c, o)}>
          <b>{o.label}</b><small>{effectText(o.effects) || 'sem efeito direto'}</small></button>)}</div>
      </article>)}
    </Section>}

    <Section title="Linha do tempo">
      {data.feed.length === 0 ? <Empty title="Nenhuma reação ainda">Tome uma decisão e acompanhe a repercussão nos dias seguintes.</Empty>
        : <><Segmented label="Tipo de notícia" value={kind} onChange={(k) => { setKind(k); setShown(PAGE); }} options={[['todas', `Todas (${data.feed.length})`], ...Object.entries(kinds).map(([k, n]) => [k, `${KIND[k] || k} (${n})`])]} />{groups.map((g) => <div key={g.m}>
          <h4 className="ds-month">{monthName(g.m + '-15')}</h4>
          <ul className="ds-timeline">{g.items.map((n, idx) => <li key={`${n.id}-${n.date}-${idx}`} className={TONE[n.kind] === 'bad' ? 'bad' : TONE[n.kind] === 'good' ? 'good' : ''}>
            <time dateTime={n.date}>{dayName(n.date)} · <Badge tone={TONE[n.kind] || ''}>{KIND[n.kind] || n.kind}</Badge></time>
            <b>{n.headline}</b>
            {n.body && n.body !== 'Simulação.' && <p>{n.body}</p>}
          </li>)}</ul>
        </div>)}
        {filtered > shown && <button className="secondary-button" onClick={() => setShown(shown + PAGE)}>Mostrar mais ({filtered - shown})</button>}</>}
      {data.scheduled > 0 && <p className="ds-muted" style={{ marginTop: 12 }}>{data.scheduled} reação(ões) ainda por vir.</p>}
    </Section>
  </Page>;
}
