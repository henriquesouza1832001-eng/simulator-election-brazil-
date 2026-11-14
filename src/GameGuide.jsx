import { useEffect, useMemo, useRef, useState } from 'react';
import { GLOSSARY, HOW, TAB_HELP } from './guideContent';

const KEY = 'quatroanos.guide.pos';
const readPos = () => { try { const p = JSON.parse(localStorage.getItem(KEY) || 'null'); return p && Number.isFinite(p.x) && Number.isFinite(p.y) ? p : null; } catch { return null; } };
const savePos = (p) => { try { localStorage.setItem(KEY, JSON.stringify(p)); } catch { /* sem armazenamento: só não lembra a posição */ } };

/** Guia flutuante: não bloqueia o jogo, dá para arrastar e minimizar, e começa pela ajuda da aba atual. */
export default function GameGuide({ groups, activeTab, onGo, onClose }) {
  const [q, setQ] = useState('');
  const [mini, setMini] = useState(false);
  const [pos, setPos] = useState(readPos);
  const box = useRef(null);
  const drag = useRef(null);

  useEffect(() => {
    const onKey = (e) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);

  function startDrag(e) {
    if (e.target.closest('button') || window.innerWidth < 640) return;
    const r = box.current.getBoundingClientRect();
    drag.current = { dx: e.clientX - r.left, dy: e.clientY - r.top, w: r.width, h: r.height };
    e.currentTarget.setPointerCapture(e.pointerId);
  }
  function moveDrag(e) {
    const d = drag.current;
    if (!d) return;
    const x = Math.max(8, Math.min(window.innerWidth - d.w - 8, e.clientX - d.dx));
    const y = Math.max(8, Math.min(window.innerHeight - 60, e.clientY - d.dy));
    setPos({ x, y });
  }
  function endDrag() { if (drag.current && pos) savePos(pos); drag.current = null; }

  const needle = q.trim().toLowerCase();
  const match = (...parts) => !needle || parts.some((p) => String(p).toLowerCase().includes(needle));
  const tabs = useMemo(() => groups.filter((g) => g.items.length).map((g) => ({ label: g.label, items: g.items.filter((t) => match(t, TAB_HELP[t] || '', g.label)) })).filter((g) => g.items.length), [groups, needle]);
  const terms = GLOSSARY.filter(([t, d]) => match(t, d));
  const style = pos && window.innerWidth >= 640 ? { left: pos.x, top: pos.y, right: 'auto', bottom: 'auto' } : undefined;

  return <aside ref={box} className={`ds-guide-float ${mini ? 'mini' : ''}`} style={style} role="dialog" aria-label="Guia do jogo">
    <div className="ds-guide-bar" onPointerDown={startDrag} onPointerMove={moveDrag} onPointerUp={endDrag} onPointerCancel={endDrag}>
      <b>Guia do jogo</b>
      <span>
        <button type="button" aria-label={mini ? 'Expandir guia' : 'Minimizar guia'} onClick={() => setMini(!mini)}>{mini ? '▢' : '–'}</button>
        <button type="button" aria-label="Fechar guia" onClick={onClose}>×</button>
      </span>
    </div>
    {!mini && <div className="ds-guide-body">
      <input type="search" aria-label="Buscar no guia" placeholder="Buscar: PEC, Selic, CPI…" value={q} onChange={(e) => setQ(e.target.value)} />

      {!needle && TAB_HELP[activeTab] && <div className="ds-guide-here"><small>Você está em</small><b>{activeTab}</b><p>{TAB_HELP[activeTab]}</p></div>}
      {!needle && <><h3>Como o jogo funciona</h3><ol>{HOW.map((t) => <li key={t}>{t}</li>)}</ol></>}

      {tabs.length > 0 && <h3>O que cada aba faz</h3>}
      {tabs.map((g) => <div key={g.label}>
        <div className="ds-guide-group">{g.label}</div>
        {g.items.map((t) => <div className="ds-guide-item" key={t}>
          <b>{t}{t === activeTab ? ' · aqui' : ''}</b>
          <p>{TAB_HELP[t] || 'Sem descrição ainda.'}</p>
          <button type="button" className="secondary-button" onClick={() => onGo(t)}>Abrir</button>
        </div>)}
      </div>)}

      {terms.length > 0 && <h3>Termos do jogo</h3>}
      {terms.map(([t, d]) => <div className="ds-gloss" key={t}><b>{t}</b><p>{d}</p></div>)}
      {!tabs.length && !terms.length && <p className="ds-muted" style={{ marginTop: 16 }}>Nada encontrado para “{q}”.</p>}
    </div>}
  </aside>;
}
