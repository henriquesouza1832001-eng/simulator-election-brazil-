import Brand from './Brand';

export default function WelcomePanel({ onGuest, onSignIn, busy, notice }) {
  return <main className="welcome-screen">
    <header className="welcome-header">
      <Brand />
      <button className="quiet-button" onClick={onSignIn}>Entrar / criar conta</button>
    </header>
    <section className="welcome-stage">
      <div className="welcome-copy">
        <div className="eyebrow">UMA SIMULAÇÃO POLÍTICA DO BRASIL</div>
        <h1>Governe o país.<br />Comece quando quiser.</h1>
        <p>Faça escolhas, acompanhe os efeitos e avance um dia de cada vez. Você pode jogar sem cadastro; a conta é opcional.</p>
        <button className="primary-button welcome-play" onClick={onGuest} disabled={busy}>{busy ? 'Preparando sua partida…' : 'Jogar sem conta'} <b>→</b></button>
        <small className="welcome-save-note">A partida fica salva neste navegador. Entre ou crie uma conta para acessar partidas salvas na conta em outros dispositivos.</small>
        {notice && <p className="auth-notice" role="status">{notice}</p>}
      </div>
      <aside className="welcome-account-card">
        <div className="eyebrow">SUA CONTA É OPCIONAL</div>
        <h2>Já tem uma conta?</h2>
        <p>Entre para continuar suas partidas salvas na conta.</p>
        <button className="secondary-button" onClick={onSignIn}>Entrar ou criar conta <b>→</b></button>
      </aside>
    </section>
    <footer className="welcome-footer">Simulador político satírico. Pessoas, falas, pesquisas e acontecimentos das partidas são ficção, salvo quando aparecerem identificados como dados públicos com fonte e data. As partidas sem conta ficam vinculadas a este navegador.</footer>
  </main>;
}
