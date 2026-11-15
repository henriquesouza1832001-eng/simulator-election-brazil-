import { Children, isValidElement, useMemo, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { Drawer } from './ui.jsx';

// Substitui o <select> nativo: mostra a escolha atual e abre uma lista num painel lateral à direita.
// Mesma interface do <select> (value, onChange com event.target.value, <option> como filhos), então a troca é direta.

const textOf = (node) => Children.toArray(node).map((n) => (isValidElement(n) ? textOf(n.props.children) : String(n))).join('');

function readOptions(children) {
  return Children.toArray(children).filter((c) => isValidElement(c) && c.type === 'option').map((c) => {
    const label = textOf(c.props.children).trim();
    const value = c.props.value !== undefined ? String(c.props.value) : label;
    return { value, label, disabled: Boolean(c.props.disabled) };
  });
}

function labelTextOf(el) {
  const lab = el?.closest('label');
  if (!lab) return '';
  return [...lab.childNodes].filter((n) => n.nodeType === 3).map((n) => n.textContent).join(' ').replace(/\s+/g, ' ').trim();
}

export default function Select({ value, onChange, children, disabled, required, className = '', 'aria-label': ariaLabel, title }) {
  const options = useMemo(() => readOptions(children), [children]);
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const btn = useRef(null);
  const current = options.find((o) => o.value === String(value ?? ''));
  const shown = current && current.value !== '' ? current.label : (options.find((o) => o.value === '')?.label || 'Escolher…');
  const filtered = query.trim() ? options.filter((o) => o.label.toLowerCase().includes(query.trim().toLowerCase())) : options;
  const drawerTitle = title || ariaLabel || labelTextOf(btn.current) || 'Escolher';

  const pick = (o) => { onChange?.({ target: { value: o.value } }); setOpen(false); setQuery(''); };
  return <>
    <button ref={btn} type="button" className={`ds-choice ${className}`} disabled={disabled} aria-haspopup="dialog" aria-label={ariaLabel ? `${ariaLabel}: ${shown}` : undefined}
      onClick={() => setOpen(true)}>
      <span className={current && current.value !== '' ? '' : 'ds-muted'}>{shown}</span><i aria-hidden="true">›</i>
    </button>
    {required && <input className="ds-choice-required" required value={current && current.value !== '' ? current.value : ''} onChange={() => {}} tabIndex={-1} aria-hidden="true" />}
    {open && createPortal(<Drawer title={drawerTitle} onClose={() => { setOpen(false); setQuery(''); }}>
      {options.length > 10 && <input type="search" aria-label="Buscar na lista" placeholder="Buscar" value={query} onChange={(e) => setQuery(e.target.value)} autoFocus />}
      <div className="ds-pick-list" role="listbox" aria-label={drawerTitle}>
        {filtered.map((o) => <button key={o.value + o.label} type="button" role="option" aria-selected={current?.value === o.value} aria-pressed={current?.value === o.value}
          disabled={o.disabled} onClick={() => pick(o)}><span>{o.label || 'Nenhum'}</span></button>)}
        {filtered.length === 0 && <p className="ds-muted">Nada encontrado.</p>}
      </div>
    </Drawer>, document.body)}
  </>;
}
