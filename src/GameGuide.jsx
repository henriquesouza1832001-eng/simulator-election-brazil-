import { useEffect } from 'react';

export default function GameGuide({ steps, stepIndex, onStepChange, onClose }) {
  const step = steps[stepIndex];

  useEffect(() => {
    function closeOnEscape(event) {
      if (event.key === 'Escape') onClose();
    }
    window.addEventListener('keydown', closeOnEscape);
    return () => window.removeEventListener('keydown', closeOnEscape);
  }, [onClose]);

  if (!step) return null;

  return <div className="game-guide-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}>
    <section className="game-guide-dialog" role="dialog" aria-modal="true" aria-labelledby="game-guide-title">
      <div className="game-guide-topline"><span>GUIA RÁPIDO · {stepIndex + 1} DE {steps.length}</span><button type="button" className="game-guide-close" aria-label="Fechar guia" onClick={onClose}>×</button></div>
      <h2 id="game-guide-title">{step.title}</h2>
      <p>{step.description}</p>
      <div className="game-guide-progress" aria-label={`Etapa ${stepIndex + 1} de ${steps.length}`}><i style={{ width: `${((stepIndex + 1) / steps.length) * 100}%` }} /></div>
      <div className="game-guide-actions">
        <button type="button" className="secondary-button" disabled={stepIndex === 0} onClick={() => onStepChange(stepIndex - 1)}>Anterior</button>
        <button type="button" className="game-guide-skip" onClick={onClose}>Pular guia</button>
        {stepIndex < steps.length - 1
          ? <button type="button" className="primary-button" onClick={() => onStepChange(stepIndex + 1)}>Próximo <span aria-hidden="true">→</span></button>
          : <button type="button" className="primary-button" onClick={onClose}>Concluir</button>}
      </div>
    </section>
  </div>;
}
