import './learning-panel.css';

export default function LearningPanel({ state }) {
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
      <code>python -m app.ai.trainer</code>
      <span>Execute em <code>backend</code>. Usa apenas categoria e instrumento que você corrigiu nos menus da prévia. Treina um candidato separado para cada jogador; exige cinco exemplos por classe e acurácia mínima de 75% em dados reservados. Os arquivos ficam junto ao banco local e ainda não são usados nas partidas.</span>
    </div>
  </section>;
}
