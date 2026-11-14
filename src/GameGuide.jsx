import { useEffect, useMemo, useState } from 'react';
import { GLOSSARY, HOW, TAB_HELP } from './guideContent';

/** Guia do jogo: painel lateral com o que cada aba faz e o significado dos termos. Fecha com Esc ou clicando fora. */
export default function GameGuide({ groups, activeTab, onGo, onClose }) {
  const [q, setQ] = useState('');
  useEffect(() => {
    const onKey = (e) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);

  const needle = q.trim().toLowerCase();
  const match = (...parts) => !needle || parts.some((p) => String(p).toLowerCase().includes(needle));
  const tabs = useMemo(() => groups.filter((g) => g.items.length).map((g) => ({ label: g.label, items: g.items.filter((t) => match(t, TAB_HELP[t] || '', g.label)) })).filter((g) => g.items.length), [groups, needle]);
  const terms = GLOSSARY.filter(([t, d]) => match(t, d));

  return <div className="ds-guide-backdrop" onMouseDown={(e) => { if (e.target === e.currentTarget) onClose(); }}>
    <aside className="ds-guide" role="dialog" aria-modal="true" aria-labelledby="ds-guide-title">
      <div className="ds-guide-top">
        <div><h2 id="ds-guide-title">Guia do jogo</h2><button type="button" aria-label="Fechar guia" onClick={onClose}>×</button></div>
        <input type="search" aria-label="Buscar no guia" placeholder="Buscar uma aba ou um termo (ex.: PEC, Selic, CPI)" value={q} onChange={(e) => setQ(e.target.value)} />
      </div>

      {!needle && <><h3>Como o jogo funciona</h3><ol>{HOW.map((t) => <li key={t}>{t}</li>)}</ol></>}

      {tabs.length > 0 && <h3>O que cada aba faz</h3>}
      {tabs.map((g) => <div key={g.label}>
        <div className="ds-guide-group">{g.label}</div>
        {g.items.map((t) => <div className="ds-guide-item" key={t}>
          <b>{t}{t === activeTab ? ' · você está aqui' : ''}</b>
          <p>{TAB_HELP[t] || 'Sem descrição ainda.'}</p>
          <button type="button" className="secondary-button" onClick={() => { onGo(t); onClose(); }}>Abrir</button>
        </div>)}
      </div>)}

      {terms.length > 0 && <h3>Termos do jogo</h3>}
      {terms.map(([t, d]) => <div className="ds-gloss" key={t}><b>{t}</b><p>{d}</p></div>)}
      {!tabs.length && !terms.length && <p className="ds-muted" style={{ marginTop: 24 }}>Nada encontrado para “{q}”.</p>}
    </aside>
  </div>;
}
