export default function SpeechReading({ reading }) {
  const mark = (ok, label) => <span className={ok ? 'reading-ok' : 'reading-miss'}>{ok ? '✓' : '✗'} {label}</span>
  return (
    <section className="speech-reading">
      <h4>Como o eleitorado entendeu seu discurso <small>{reading.source === 'gemini' ? 'leitura por IA' : 'leitura automática simples'}</small></h4>
      {reading.summary && <p>{reading.summary}</p>}
      <p>Temas: <b>{reading.themes.join(', ') || '—'}</b> · Tom: <b>{reading.tone}</b></p>
      {reading.promises.length > 0 && <ul>{reading.promises.map((p, i) => <li key={i}>“{p.text}” {mark(true, 'meta')} {mark(p.deadline, 'prazo')} {mark(p.funding, 'recurso')}</li>)}</ul>}
      {reading.attacks.length > 0 && <p>Ataques a: {reading.attacks.map((a) => a.target + (a.personal ? ' (pessoal)' : '')).join(', ')}</p>}
      {reading.flags.map((f, i) => <p key={i} className="reading-flag">{f}</p>)}
    </section>
  )
}
