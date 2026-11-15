import { useEffect, useMemo, useState } from 'react';
import { Page, Section, Empty, Badge } from './ui.jsx';
import { BRASIL } from './mapData.js';

const NAMES = BRASIL.names || {};
const pct = (v) => (Number.isFinite(Number(v)) ? Number(v).toLocaleString('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 }) : '—');
// Cor por UF: dourado quando o jogador lidera, azul-acinzentado quando o adversário lidera; mais forte quanto maior a margem.
const colorOf = (player) => {
  if (player == null) return '#1e2733';
  const m = Math.min(1, Math.abs(player - 50) / 30);
  const a = 0.35 + 0.65 * m;
  return player >= 50 ? `rgba(217,180,74,${a})` : `rgba(111,143,201,${a})`;
};

export default function ApuracaoPanel({ request, state }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [i, setI] = useState(0);
  const [uf, setUf] = useState(null);
  const [auto, setAuto] = useState(false);
  useEffect(() => { request('/api/election/tally').then((d) => { setData(d); setI(0); setAuto(false); }).catch((e) => setError(e.message)); }, [state?.date]);
  useEffect(() => {
    if (!auto || !data?.steps) return undefined;
    if (i >= data.steps.length - 1) { setAuto(false); return undefined; }
    const t = setTimeout(() => setI((n) => n + 1), 1400);
    return () => clearTimeout(t);
  }, [auto, i, data]);

  const step = data?.steps?.[i];
  const closed = step ? step.closed.length : 0;
  const rows = useMemo(() => (step ? Object.entries(step.ufs).filter(([, v]) => v.player != null).sort((a, b) => b[1].counted - a[1].counted) : []), [step]);
  if (error) return <Page title="Apuração"><p className="meta-status meta-error" role="alert">{error}</p></Page>;
  if (!data) return <Page title="Apuração"><Empty title="Carregando…" /></Page>;
  if (!data.available) return <Page title="Apuração" lead="Acompanhe a contagem dos votos, estado por estado."><Empty title="Ainda não há apuração">{data.reason}</Empty></Page>;
  if (data.kind === 'resumo') return <Page title="Apuração" lead={data.note}>
    <Section title="Resultado"><p><b>{data.result === 'won' ? 'Eleito(a)' : 'Não eleito(a)'}</b>{data.vote_share != null && <> · {pct(data.vote_share)}% dos votos</>}</p></Section>
  </Page>;

  const sel = uf && step?.ufs[uf];
  const player = step.national_player;
  return <Page title="Apuração" lead="A contagem avança por boletins: os estados fecham aos poucos e o placar pode mudar até a última urna.">
    <div className="ds-apu">
      <section className="ds-card ds-apu-map" aria-label="Mapa da apuração">
        <div className="ds-seg" role="group" aria-label="Boletim">{data.steps.map((s, k) => <button key={s.time} type="button" aria-pressed={i === k} onClick={() => { setI(k); setAuto(false); }}>{s.time}</button>)}</div>
        <svg viewBox={BRASIL.viewBox} role="group" aria-label="Estados na apuração">
          {BRASIL.items.map((it) => {
            const v = step.ufs[it.id];
            return <path key={it.id} d={it.d} fill={colorOf(v?.player)} stroke={uf === it.id ? '#eef1f5' : '#0e1319'} strokeWidth={uf === it.id ? 1.6 : 0.6}
              opacity={v && v.counted < 100 && v.counted > 0 ? 0.78 : 1} tabIndex={0} role="button"
              aria-label={`${NAMES[it.id] || it.id}: ${v?.player != null ? `${pct(v.player)}% para você, ${pct(v.counted)}% apurado` : 'sem urnas apuradas'}`}
              onClick={() => setUf(it.id)} onKeyDown={(e) => { if (e.key === 'Enter') setUf(it.id); }} />;
          })}
        </svg>
        <ul className="ds-geomap-legend"><li><i style={{ background: 'rgba(217,180,74,.9)' }} />Você lidera</li><li><i style={{ background: 'rgba(111,143,201,.9)' }} />Adversário lidera</li><li><i style={{ background: '#1e2733' }} />Sem urnas apuradas</li></ul>
        <div className="ds-apu-ctl">
          <button type="button" className="secondary-button" disabled={i === 0} onClick={() => { setI(0); setAuto(false); }}>Reiniciar</button>
          <button type="button" className="primary-button" disabled={i >= data.steps.length - 1} onClick={() => setAuto(!auto)}>{auto ? 'Pausar' : i === 0 ? 'Começar a apuração' : 'Continuar'}</button>
        </div>
      </section>
      <aside className="ds-apu-side">
        <section className="ds-card">
          <h4>Placar nacional <small className="ds-muted">boletim das {step.time}</small></h4>
          {player == null ? <p className="ds-muted">As urnas ainda não começaram a ser apuradas.</p> : <>
            <div className="ds-apu-bar" role="img" aria-label={`Você ${pct(player)}%, adversário ${pct(100 - player)}%`}><i style={{ width: `${player}%` }} /></div>
            <dl className="ds-kv"><dt>Você</dt><dd>{pct(player)}%</dd><dt>Adversário</dt><dd>{pct(100 - player)}%</dd><dt>Urnas apuradas</dt><dd>{pct(step.counted)}%</dd><dt>Estados fechados</dt><dd>{closed}/27</dd></dl></>}
          {i === data.steps.length - 1 && <p><Badge tone={data.result === 'won' ? 'good' : 'bad'}>{data.result === 'won' ? 'Vitória' : 'Derrota'}</Badge> {data.turning_point ? `A virada aconteceu no boletim das ${data.turning_point}.` : 'Sem virada: o líder do início manteve a frente.'}</p>}
        </section>
        <section className="ds-card">
          <h4>{uf ? `${NAMES[uf] || uf}` : 'Estados'}</h4>
          {sel ? <dl className="ds-kv"><dt>Você</dt><dd>{sel.player != null ? `${pct(sel.player)}%` : '—'}</dd><dt>Apurado</dt><dd>{pct(sel.counted)}%</dd><dt>Região</dt><dd>{data.regions[uf]}</dd><dt>Peso no eleitorado</dt><dd>{pct(data.weights[uf])}%</dd></dl>
            : <p className="ds-muted">Toque em um estado para ver a contagem dele.</p>}
          <ul className="ds-list ds-apu-list">{rows.slice(0, 8).map(([k, v]) => <li key={k}><button type="button" className="ds-link" onClick={() => setUf(k)}>{NAMES[k] || k}</button><span className="ds-muted">{pct(v.player)}% · {pct(v.counted)}% apurado</span></li>)}</ul>
        </section>
        <p className="ds-muted">{data.note}</p>
      </aside>
    </div>
  </Page>;
}
