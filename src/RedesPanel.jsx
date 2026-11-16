import { useEffect, useState } from 'react';
import { Page, Empty, Badge } from './ui.jsx';

const KIND = { apoio: 'Apoiadores', oposicao: 'Oposição', humor: 'Humor', imprensa: 'Imprensa' };
const short = (n) => (n >= 1e6 ? `${(n / 1e6).toLocaleString('pt-BR', { maximumFractionDigits: 1 })} mi` : n >= 1e3 ? `${(n / 1e3).toLocaleString('pt-BR', { maximumFractionDigits: 1 })} mil` : String(n));
const day = (iso) => iso.split('-').reverse().join('/');

export default function RedesPanel({ request, state, go }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [kind, setKind] = useState('todos');
  const [platform, setPlatform] = useState('todas');
  const [shown, setShown] = useState(10);
  useEffect(() => { request('/api/social/feed').then(setData).catch((e) => setError(e.message)); }, [state?.date]);
  if (error) return <Page title="Redes"><p className="meta-status meta-error" role="alert">{error}</p></Page>;
  if (!data) return <Page title="Redes"><Empty title="Carregando…" /></Page>;
  const list = data.posts.filter((p) => (kind === 'todos' || p.kind === kind) && (platform === 'todas' || p.platform === platform));
  return <Page title="Redes" lead="O que as redes estão dizendo sobre o que aconteceu. Perfis e frases são fictícios e satíricos.">
    <div className="ds-seg" role="group" aria-label="Tipo de perfil">{[['todos', 'Todos'], ...Object.entries(KIND)].map(([k, l]) => <button key={k} type="button" aria-pressed={kind === k} onClick={() => setKind(k)}>{l}</button>)}</div>
    {data.platforms && <div className="ds-seg" role="group" aria-label="Plataforma">{[{ key: 'todas', label: 'Todas as redes' }, ...data.platforms].map((pl) => <button key={pl.key} type="button" aria-pressed={platform === pl.key} title={pl.about} onClick={() => setPlatform(pl.key)}>{pl.label}</button>)}</div>}
    {list.length === 0 ? <Empty title="Nada nas redes ainda">As publicações aparecem quando há decisões, crises, pesquisas ou resultado de eleição.</Empty>
      : <ul className="ds-feed">{list.slice(0, shown).map((p) => <li key={p.id} className={`ds-post ${p.kind}`}>
        <header><b>{p.name}</b><span className="ds-muted">{p.handle} · {p.platform_label} · {day(p.date)}</span>{p.rumor && <Badge tone="bad">Boato</Badge>}</header>
        <p>{p.text}</p>
        <footer><span>Alcance {short(p.reach)}</span><span>{short(p.likes)} curtidas</span>{p.tab && <button type="button" className="ds-link" onClick={() => go(p.tab)}>{p.origin}</button>}</footer>
      </li>)}</ul>}
    {list.length > shown && <button type="button" className="secondary-button" onClick={() => setShown(shown + 10)}>Mostrar mais ({list.length - shown})</button>}
    <p className="ds-muted">{data.note}</p>
  </Page>;
}
