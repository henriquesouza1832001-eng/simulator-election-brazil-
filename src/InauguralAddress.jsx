import { useState } from 'react';

export default function InauguralAddress({ request, onState, onNotice, onChooseCareer, busy, setBusy }) {
  const [text, setText] = useState('');
  const [error, setError] = useState('');
  const [deferred, setDeferred] = useState(false);

  async function submit(event) {
    event.preventDefault();
    setBusy(true);
    setError('');
    try {
      const data = await request('/api/game/inaugural-address', {
        method: 'POST', body: JSON.stringify({ text }),
      });
      onState(data.state);
      onNotice(data.result.message);
    } catch (exception) {
      setError(exception.message);
    } finally {
      setBusy(false);
    }
  }

  if (deferred) return null;

  return <div className="inaugural-overlay" role="dialog" aria-modal="true" aria-labelledby="inaugural-title">
    <form className="inaugural-card" onSubmit={submit}>
      <span className="eyebrow">A PRIMEIRA FALA DO MANDATO</span>
      <h2 id="inaugural-title">Pronunciamento de posse</h2>
      <p>Antes das decisões do governo, fale ao país. Apresente prioridades, um compromisso que possa ser cobrado e como pretende prestar contas. O texto é avaliado por critérios públicos do simulador.</p>
      <div className="inaugural-guide"><span>País e vida cotidiana</span><span>Proposta verificável</span><span>Instituições e direitos</span><span>Responsabilidade e clareza</span></div>
      <label htmlFor="inaugural-speech">SEU PRONUNCIAMENTO · 80 A 1.200 CARACTERES</label>
      <textarea id="inaugural-speech" value={text} onChange={(event) => setText(event.target.value)} minLength={80} maxLength={1200} placeholder="Brasileiras e brasileiros, hoje começa um mandato que será acompanhado por metas públicas…" required />
      <div className="inaugural-footer"><small>{text.length}/1.200 · A agenda só começa depois desta fala.</small><button className="primary-button" disabled={busy || text.trim().length < 80}>{busy ? 'Registrando…' : 'Pronunciar e iniciar o governo'}</button></div>
      <button className="secondary-button inaugural-career-link" type="button" onClick={() => { setDeferred(true); onChooseCareer?.(); }}>Começar uma carreira eleitoral em outro cargo</button>
      {error && <p className="notice" role="alert">{error}</p>}
    </form>
  </div>;
}
