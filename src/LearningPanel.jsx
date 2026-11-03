import { useState } from 'react';
import './learning-panel.css';

const fieldLabel = { category: 'Categoria', instrument: 'Instrumento' };

export default function LearningPanel({ state, request }) {
  const [training, setTraining] = useState(false);
  const [report, setReport] = useState(null);
  const [error, setError] = useState('');

  async function evaluate() {
    setTraining(true);
    setError('');
    try {
      setReport(await request('/api/learning/train', { method: 'POST', body: JSON.stringify({}) }));
    } catch (problem) {
      setError(problem.message);
    } finally {
      setTraining(false);
    }
  }

  return <section className="panel learning-page">
    <div className="eyebrow">MEMÓRIA E AGENTE PYTHON</div>
    <h2>Treino offline com suas correções</h2>
    <p className="page-description">Cada prévia fica registrada por jogador. Você pode revisar categoria e instrumento; um classificador local avalia esses rótulos fora da partida. O motor Python continua decidindo custos e efeitos.</p>
    <div className="learning-cards">
      <article><span>PRÉVIAS REGISTRADAS</span><strong>{state.learning?.interpretations_logged ?? 0}</strong><small>Histórico isolado deste jogador</small></article>
      <article><span>CORREÇÕES SALVAS</span><strong>{state.learning?.corrections_saved ?? 0}</strong><small>Texto livre e rótulos revisados</small></article>
      <article><span>POLÍTICA DO AGENTE</span><strong>Python</strong><small>Treino com estados e efeitos sintéticos</small></article>
      <article><span>IA DE TEXTO</span><strong>Gemini</strong><small>Ajuda a classificar; não decide efeitos numéricos</small></article>
    </div>
    <div className="learning-note">
      <b>Treinar a política de governo</b>
      <code>python -m app.bot.trainer --episodes 3000</code>
      <span>Execute em <code>backend</code>. Usa cenários sintéticos e não chama APIs externas.</span>
    </div>
    <div className="learning-note interpreter-training-note">
      <b>Avaliar o classificador local de interpretações</b>
      <span>Usa apenas as categorias e os instrumentos corrigidos nesta conta. O candidato exige cinco exemplos por classe e acurácia mínima de 75% em dados reservados; não altera interpretações nem resultados da partida.</span>
      <button className="secondary-button" onClick={evaluate} disabled={training}>
        {training ? 'Avaliando exemplos…' : 'Treinar e avaliar agora'}
      </button>
      {error && <p className="training-error" role="alert">{error}</p>}
      {report && <div className="training-result" role="status">
        <b>{report.status === 'no_structured_labels' ? 'Ainda não há rótulos de treino.' : `${report.reviewed_proposals} proposta(s) revisada(s)`}</b>
        {Object.entries(report.fields || {}).map(([field, result]) => <div key={field}>
          <strong>{fieldLabel[field] || field}</strong>
          <span>{result.accuracy === null ? 'Amostra insuficiente' : `${Math.round(result.accuracy * 100)}% de acurácia`}</span>
          <small>{Object.entries(result.classes || {}).map(([name, count]) => `${name}: ${count}`).join(' · ')}</small>
          <small>{result.candidate_saved ? 'Candidato salvo para revisão, ainda inativo.' : result.reason}</small>
        </div>)}
        {report.live_interpreter_changed === false && report.status !== 'no_structured_labels' && <small>O modelo usado durante as partidas não foi alterado.</small>}
      </div>}
    </div>
  </section>;
}
