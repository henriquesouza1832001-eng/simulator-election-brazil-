import { useEffect, useState } from 'react';
import { effectText } from './format';
import './gabinete.css';

const dayName = (iso) => (iso ? new Date(`${iso}T12:00:00`).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' }) : '');

/** Decidir: uma decisão por vez, com a prévia das consequências de cada opção antes de confirmar. */
export default function Decidir({ request, state, onState, onNotice, go }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [chosen, setChosen] = useState({});
  const [sending, setSending] = useState(false);
  useEffect(() => { request('/api/consequences').then(setData).catch((e) => setError(e.message)); }, [state?.date]);

  if (error) return <section className="gb"><p role="alert">{error}</p></section>;
  if (!data) return <section className="gb"><p role="status">Carregando…</p></section>;
  const item = data.pending[0];
  if (!item) return <section className="gb" aria-label="Decidir">
    <header className="gb-head"><div className="gb-eyebrow">Mesa de despacho</div><h1>Decidir</h1></header>
    <div className="gb-panel"><h2>Nenhuma decisão espera resposta</h2><p className="gb-note">Quando uma crise ou um projeto aprovado exigir resposta, ele aparece aqui com a prévia dos efeitos.</p>
      <div className="gb-actions"><span /><button type="button" className="gb-btn primary" onClick={() => go('Visão geral')}>Voltar ao gabinete</button></div></div>
  </section>;

  const idx = chosen[item.id] ?? 0;
  const opt = item.options[idx];
  const effects = Object.entries(opt.effects || {});
  const goodWhenUp = { inflation: false, unemployment: false, divida_pib: false, homicidios: false };
  async function confirm() {
    setSending(true);
    try {
      const r = await request(`/api/consequences/${encodeURIComponent(item.id)}/respond?option=${encodeURIComponent(opt.id)}`, { method: 'POST', body: '{}' });
      setData(r.overview);
      if (r.state) onState?.(r.state);
      onNotice?.(`Resposta registrada: ${opt.label}. Efeitos: ${effectText(r.effects) || 'sem efeito direto'}.`);
    } catch (e) { onNotice?.(e.message); } finally { setSending(false); }
  }

  return <section className="gb" aria-label="Decidir">
    <header className="gb-head"><div className="gb-eyebrow">Mesa de despacho · prazo {dayName(item.deadline)}{data.pending.length > 1 ? ` · ${data.pending.length} decisões na fila` : ''}</div><h1>Decidir</h1><p className="gb-lead">Veja a prévia antes de confirmar.</p></header>
    <div className="gb-panel crisis"><div className="gb-eyebrow">Crise</div><h2 style={{ marginTop: 6 }}>{item.title}</h2><p className="gb-note">{item.text}</p></div>
    <div className="gb-panel"><div className="gb-panel-title"><h2>Escolha uma resposta</h2><span className="gb-meta">Uma opção</span></div>
      <div className="gb-options">{item.options.map((o, i) => <button key={o.id} type="button" className={`gb-option ${i === idx ? 'selected' : ''}`} aria-pressed={i === idx} onClick={() => setChosen({ ...chosen, [item.id]: i })}>
        <span className="gb-radio" /><span className="gb-option-text">{o.label}</span>{i === item.options.length - 1 && <span className="gb-option-note">Vale se o prazo vencer</span>}</button>)}</div></div>
    <div className="gb-panel"><div className="gb-panel-title"><h2>Prévia das consequências</h2><span className="gb-meta">Antes de confirmar</span></div>
      {effects.length ? <div className="gb-preview">{effects.map(([k, v]) => { const up = Number(v) > 0; const good = up === (goodWhenUp[k] ?? true); return <div key={k}><span>{effectText({ [k]: v }).replace(/^\S+ /, '')}</span><strong className={good ? 'good' : 'bad'}>{effectText({ [k]: v }).split(' ')[0]}</strong></div>; })}</div>
        : <p className="gb-note">Esta resposta não tem efeito direto nos indicadores.</p>}
      <div className="gb-actions"><span className="gb-meta">A escolha fica registrada depois da confirmação.</span>
        <button type="button" className="gb-btn primary" disabled={sending} onClick={confirm}>{sending ? 'Enviando…' : 'Confirmar resposta ✓'}</button></div></div>
  </section>;
}
