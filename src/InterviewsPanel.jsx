import { useEffect, useState } from 'react';
import './powers.css';

const CRITERIA = { tema: 'Tema', dados: 'Dados', compromisso: 'Compromisso', tom: 'Tom' };
const GRADE = { forte: 'Desempenho forte', boa: 'Boa participação', regular: 'Participação irregular', fraca: 'Desempenho fraco' };

export default function InterviewsPanel({ request, state, onState, onNotice }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [text, setText] = useState('');
  const [feedback, setFeedback] = useState(null);
  const [summary, setSummary] = useState(null);
  const [busy, setBusy] = useState(false);

  const load = () => request('/api/interviews').then(setData).catch((e) => setError(e.message));
  useEffect(() => { load(); }, [state?.date]);

  async function begin(kind) {
    setBusy(true); setSummary(null); setFeedback(null); setText('');
    try { setData(await request('/api/interviews/start', { method: 'POST', body: JSON.stringify({ kind }) })); } catch (e) { onNotice?.(e.message); } finally { setBusy(false); }
  }

  async function send(e) {
    e.preventDefault();
    setBusy(true);
    try {
      const r = await request('/api/interviews/answer', { method: 'POST', body: JSON.stringify({ text }) });
      setFeedback(r.feedback); setData(r.overview); setText('');
      if (r.done) { setSummary(r.summary); if (r.state) onState?.(r.state); }
    } catch (err) { onNotice?.(err.message); } finally { setBusy(false); }
  }

  if (error) return <section className="panel"><p className="meta-status meta-error" role="alert">{error}</p></section>;
  if (!data) return <section className="panel"><p className="meta-status" role="status">Carregando…</p></section>;
  const cur = data.current;

  return <section className="panel powers-page">
    <h2>Entrevistas, sabatinas e debates</h2>
    <p className="page-description">{data.note}</p>

    {!cur && <ul className="powers-list">{data.kinds.map((k) => <li key={k.key} className={k.available ? '' : 'blocked'}><div>
      <b>{k.label}</b> <small>({k.questions} perguntas)</small><small>{k.text}</small>{!k.available && <small className="neg">{k.reason}</small>}</div>
      {k.available && <div className="powers-actions"><button className="secondary-button" disabled={busy} onClick={() => begin(k.key)}>Começar</button></div>}</li>)}</ul>}

    {cur && cur.question && <form className="interview-box" onSubmit={send}>
      <p className="meta-count">{cur.kind} · pergunta {cur.index + 1} de {cur.questions.length}{cur.question.stage ? ` · ${cur.question.stage}` : ''}</p>
      <blockquote className="interview-question">{cur.question.prompt}</blockquote>
      <label htmlFor="answer"><b>Sua resposta</b></label>
      <textarea id="answer" rows={5} value={text} onChange={(e) => setText(e.target.value)} placeholder="Responda ao tema, cite números, dê prazo e responsável, com tom respeitoso." />
      <small className="meta-count">Mínimo de 40 caracteres ({text.trim().length}).</small>
      <button className="primary-button" type="submit" disabled={busy || text.trim().length < 40}>{busy ? 'Enviando…' : 'Responder'}</button>
    </form>}

    {feedback && <div className="interview-feedback" role="status">
      <h3 className="subheading">Avaliação da última resposta: {feedback.total} de 100</h3>
      <ul>{Object.entries(feedback.criteria).map(([k, v]) => <li key={k}><b>{CRITERIA[k]}</b> {v}/25 — {feedback.feedback[k]}</li>)}</ul>
    </div>}

    {summary && <div className="interview-summary"><h3 className="subheading">{GRADE[summary.grade]}: {summary.avg} pontos</h3>
      <p>Efeitos persistentes: {Object.entries(summary.effects).map(([k, v]) => `${v > 0 ? '+' : ''}${v} ${k === 'approval' ? 'aprovação' : k === 'trust' ? 'confiança' : 'momentum'}`).join(' · ') || 'nenhum'}. A repercussão aparece em Imprensa.</p></div>}

    {data.history.length > 0 && !cur && <><h3 className="subheading">Histórico</h3>
      <ul className="meta-notes">{data.history.map((h) => <li key={h.id}>{h.date} — {h.kind}: {h.avg} pontos ({h.grade})</li>)}</ul></>}
  </section>;
}
