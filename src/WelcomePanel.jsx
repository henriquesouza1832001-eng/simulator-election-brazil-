import './start.css';
import Brand from './Brand';
import Hero from './Hero';
import { NOVIDADES, VERSAO } from './novidades';

export default function WelcomePanel({ onGuest, onSignIn, busy, notice }) {
  return <main className="welcome-screen ds-welcome">
    <header className="welcome-header">
      <Brand />
      <button className="quiet-button" onClick={onSignIn}>Entrar / criar conta</button>
    </header>
    <div className="ds-welcome-body">
      <Hero name="inicio" mood="calmo" label="Uma simulação política do Brasil" title="Governe o país. Comece quando quiser." text="Faça escolhas, acompanhe os efeitos e avance um dia de cada vez. Você pode jogar sem cadastro; a conta é opcional." />
      <section className="ds-start-continue">
        <div>
          <span className="ds-label">Sem cadastro</span>
          <h2>Comece agora</h2>
          <p>A partida fica salva neste navegador. Com uma conta, você acessa suas partidas em outros dispositivos.</p>
        </div>
        <div className="ds-welcome-actions">
          <button type="button" className="ds-btn primary" onClick={onGuest} disabled={busy}>{busy ? 'Preparando sua partida…' : 'Jogar sem conta →'}</button>
          <button type="button" className="ds-btn" onClick={onSignIn}>Já tenho conta</button>
        </div>
      </section>
      {notice && <p className="auth-notice" role="status">{notice}</p>}
      <section className="ds-start-info">
        <article className="ds-card">
          <h3>Novidades da versão {VERSAO}</h3>
          <ul className="ds-start-news">{NOVIDADES.map(([t, d]) => <li key={t}><b>{t}</b><span>{d}</span></li>)}</ul>
        </article>
      </section>
    </div>
    <footer className="welcome-footer">Simulador político satírico. Pessoas, falas, pesquisas e acontecimentos das partidas são ficção, salvo quando aparecerem identificados como dados públicos com fonte e data. As partidas sem conta ficam vinculadas a este navegador.</footer>
  </main>;
}
