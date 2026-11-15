import { useEffect, useLayoutEffect, useRef, useState } from 'react';

/** Guia passo a passo: escurece a tela, destaca o elemento `[data-tour="..."]` e explica o que fazer.
 *  steps: [{ target, title, text }]. Sem dependências; Esc sai, setas navegam. */
export default function Tour({ steps, onClose }) {
  const [i, setI] = useState(0);
  const [rect, setRect] = useState(null);
  const boxRef = useRef(null);
  const step = steps[i];

  useLayoutEffect(() => {
    const el = step.target ? document.querySelector(`[data-tour="${step.target}"]`) : null;
    if (!el) { setRect(null); return undefined; }
    el.scrollIntoView({ block: 'center', behavior: 'auto' });
    const measure = () => { const r = el.getBoundingClientRect(); setRect({ top: r.top, left: r.left, width: r.width, height: r.height }); };
    measure();
    window.addEventListener('resize', measure);
    return () => window.removeEventListener('resize', measure);
  }, [i, step.target]);

  useEffect(() => {
    const onKey = (e) => {
      if (e.key === 'Escape') onClose();
      if (e.key === 'ArrowRight') setI((n) => Math.min(steps.length - 1, n + 1));
      if (e.key === 'ArrowLeft') setI((n) => Math.max(0, n - 1));
    };
    window.addEventListener('keydown', onKey);
    boxRef.current?.focus();
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose, steps.length]);

  const pad = 6;
  const vw = window.innerWidth, vh = window.innerHeight;
  const boxW = Math.min(340, vw - 24);
  let style = { left: Math.max(12, (vw - boxW) / 2), top: Math.max(12, vh / 2 - 100), width: boxW };
  if (rect) {
    const below = rect.top + rect.height + 14 + 190 < vh;
    const left = Math.min(Math.max(12, rect.left + rect.width / 2 - boxW / 2), vw - boxW - 12);
    style = { left, width: boxW, top: below ? rect.top + rect.height + pad + 10 : Math.max(12, rect.top - 200) };
  }
  const last = i === steps.length - 1;

  return <div className="ds-tour" role="dialog" aria-modal="true" aria-label="Guia do jogo">
    <div className="ds-tour-shade" onClick={onClose} />
    {rect && <div className="ds-tour-spot" style={{ top: rect.top - pad, left: rect.left - pad, width: rect.width + pad * 2, height: rect.height + pad * 2 }} />}
    <div className="ds-tour-box" style={style} ref={boxRef} tabIndex={-1} aria-live="polite">
      <span className="ds-label">Passo {i + 1} de {steps.length}</span>
      <b>{step.title}</b>
      <p>{step.text}</p>
      <div className="ds-tour-actions">
        <button type="button" className="ds-btn" onClick={onClose}>Pular</button>
        <span>
          <button type="button" className="ds-btn" disabled={i === 0} onClick={() => setI(i - 1)}>Voltar</button>
          <button type="button" className="ds-btn primary" onClick={() => (last ? onClose() : setI(i + 1))}>{last ? 'Concluir' : 'Próximo'}</button>
        </span>
      </div>
    </div>
  </div>;
}

export const tourSeen = (key) => { try { return window.localStorage.getItem(`quatroanos.tour.${key}`) === '1'; } catch { return false; } };
export const markTour = (key) => { try { window.localStorage.setItem(`quatroanos.tour.${key}`, '1'); } catch { /* sem armazenamento */ } };
