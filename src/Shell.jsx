import { useEffect, useRef } from 'react';

// Ícones de linha (1,6 px), um conjunto só. Chave = rótulo do grupo de abas.
const PATHS = {
  Painel: <><rect x="3" y="3" width="7" height="9" rx="1.5" /><rect x="14" y="3" width="7" height="5" rx="1.5" /><rect x="14" y="12" width="7" height="9" rx="1.5" /><rect x="3" y="16" width="7" height="5" rx="1.5" /></>,
  Governo: <path d="M3 21h18M5 21V10M19 21V10M9 21V10M15 21V10M2 10l10-6 10 6" />,
  Politica: <path d="M4 20c0-4 3-6 8-6s8 2 8 6M12 4a4 4 0 100 8 4 4 0 000-8z" />,
  Agenda: <><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M8 3v4M16 3v4M3 10h18" /></>,
  Mais: <><circle cx="5" cy="12" r="1.4" /><circle cx="12" cy="12" r="1.4" /><circle cx="19" cy="12" r="1.4" /></>,
  Mundo: <><circle cx="12" cy="12" r="9" /><path d="M3 12h18M12 3a14 14 0 010 18M12 3a14 14 0 000 18" /></>,
  Perfil: <path d="M4 20c0-4 3-6 8-6s8 2 8 6M12 4a4 4 0 100 8 4 4 0 000-8z" />,
  Guia: <><circle cx="12" cy="12" r="9" /><path d="M9.5 9.5a2.5 2.5 0 114 2c-.9.6-1.5 1.1-1.5 2.2M12 17.2v.1" /></>,
  Sobre: <><circle cx="12" cy="12" r="9" /><path d="M12 11v6M12 7.5v.1" /></>,
  Fixar: <path d="M9 4h6l-1 6 3 3v2H7v-2l3-3-1-6zM12 15v5" />,
  Partidas: <><rect x="4" y="3" width="16" height="18" rx="2" /><path d="M8 8h8M8 12h8M8 16h5" /></>,
};
const keyOf = (label) => (label === 'Política' ? 'Politica' : label);

export function Icon({ name }) {
  const body = PATHS[keyOf(name)] || PATHS.Painel;
  return <svg viewBox="0 0 24 24" aria-hidden="true" className="ds-icon">{body}</svg>;
}

/** Trilho lateral (computador e tablet) e barra inferior (celular): os mesmos cinco destinos. */
export function Nav({ items, current, moreActive, onGo, onMore, expanded, onToggle, pins = [], activePin, onPin }) {
  const all = [...items.map((g) => ({ key: g.label, label: g.rail || g.label, icon: g.icon || g.label, badge: g.badge || 0, active: current === g.label, go: () => onGo(g) })), { key: 'Mais', label: 'Mais', icon: 'Mais', active: moreActive, go: onMore }];
  return <>
    <aside className="ds-rail" aria-label="Seções do jogo">
      {all.map((i) => <button key={i.key} type="button" className="ds-nav" title={i.label} aria-current={i.active ? 'page' : undefined} onClick={i.go}><Icon name={i.icon} /><span>{i.label}</span>{i.badge > 0 && <i className="ds-count" aria-label={`${i.badge} ${i.badge === 1 ? "pendência" : "pendências"}`}>{i.badge}</i>}</button>)}
      {pins.length > 0 && <div className="ds-pins" role="group" aria-label="Atalhos fixados"><small>Fixados</small>{pins.map((tab) => <button key={tab} type="button" className="ds-nav ds-pin" title={tab} aria-current={activePin === tab ? 'page' : undefined} onClick={() => onPin(tab)}><Icon name="Fixar" /><span>{tab}</span></button>)}</div>}
      <button type="button" className="ds-nav ds-rail-toggle" aria-expanded={expanded} title={expanded ? 'Recolher menu' : 'Expandir menu'} onClick={onToggle}><svg viewBox="0 0 24 24" aria-hidden="true" className="ds-icon"><path d={expanded ? 'M14 6l-6 6 6 6M19 4v16' : 'M10 6l6 6-6 6M5 4v16'} /></svg><span>{expanded ? 'Recolher menu' : 'Abrir'}</span></button>
    </aside>
    <nav className="ds-bottom" aria-label="Seções do jogo">
      {all.map((i) => <button key={i.key} type="button" className="ds-nav" aria-current={i.active ? 'page' : undefined} onClick={i.go}><Icon name={i.icon} /><span>{i.label}</span>{i.badge > 0 && <i className="ds-count" aria-label={`${i.badge} ${i.badge === 1 ? "pendência" : "pendências"}`}>{i.badge}</i>}</button>)}
    </nav>
  </>;
}

function useClose(open, onClose, ref) {
  useEffect(() => {
    if (!open) return undefined;
    const onKey = (e) => { if (e.key === 'Escape') onClose(); };
    const onDown = (e) => { if (ref.current && !ref.current.contains(e.target) && !e.target.closest('[data-keep-open]')) onClose(); };
    window.addEventListener('keydown', onKey);
    window.addEventListener('pointerdown', onDown);
    return () => { window.removeEventListener('keydown', onKey); window.removeEventListener('pointerdown', onDown); };
  }, [open, onClose, ref]);
}

/** Avançar o tempo: um dia, sete dias ou um mês. No celular é um botão flutuante; no computador, o botão do topo. */
export function AdvanceMenu({ open, setOpen, busy, advance, floating }) {
  const ref = useRef(null);
  useClose(open, () => setOpen(false), ref);
  const options = [['Próximo dia', 1], ['7 dias', 7], ['1 mês', 30]];
  return <div className={`ds-advance ${floating ? 'floating' : ''}`} ref={ref}>
    <button type="button" data-keep-open className={floating ? 'ds-fab' : 'ds-btn primary'} aria-haspopup="menu" aria-expanded={open} disabled={busy} onClick={() => setOpen(!open)}>Avançar ▾</button>
    {open && <div className="ds-menu" role="menu">{options.map(([label, days]) => <button key={days} type="button" role="menuitem" onClick={() => { setOpen(false); advance(days); }}>{label}</button>)}</div>}
  </div>;
}

/** Folha "Mais": o que não cabe nos cinco destinos (Mundo, Perfil, Guia, Sobre, Partidas, conta). */
export function MoreSheet({ open, onClose, entries }) {
  const ref = useRef(null);
  useClose(open, onClose, ref);
  if (!open) return null;
  return <div className="ds-sheet-backdrop">
    <section className="ds-sheet" ref={ref} role="dialog" aria-modal="true" aria-label="Mais opções">
      <header><b>Mais</b><button type="button" aria-label="Fechar" onClick={onClose}>×</button></header>
      <ul>{entries.map((e) => <li key={e.label}><button type="button" onClick={() => { onClose(); e.go(); }}><Icon name={e.icon || e.label} /><span><b>{e.label}</b>{e.hint && <small>{e.hint}</small>}</span></button></li>)}</ul>
    </section>
  </div>;
}
