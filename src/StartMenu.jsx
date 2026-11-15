import { useState } from 'react';
import './start.css';
import { Icon } from './Shell';
import Tour, { tourSeen, markTour } from './Tour';
import { NOVIDADES, EM_BREVE, VERSAO } from './novidades';

const MODES = [
  { key: 'presidency', icon: 'Governo', kicker: 'Governo federal · 48 meses', title: 'Tomar posse no primeiro dia', text: 'Comece em 1º de janeiro de 2027 como presidente e conduza o governo pelos quatro anos.', cta: 'Assumir o governo' },
  { key: 'career', icon: 'Politica', kicker: 'Campanha e carreira', title: 'Disputar uma eleição', text: 'De vereador a presidente: faça campanha, dispute a eleição e exerça o mandato se vencer.', cta: 'Montar candidatura', needsCatalog: true },
  { key: 'party', icon: 'Agenda', kicker: 'Militância e partido', title: 'Começar como militante', text: 'Ganhe espaço no partido e chegue à candidatura a vereador.', cta: 'Entrar no partido', needsCatalog: true },
  { key: 'elector', icon: 'Partidas', kicker: 'Modo eleitor · 2014 a 2030', title: 'Consultar e votar em simulação', text: 'Veja os candidatos oficiais de um pleito e registre um voto simulado, sem criar partida.', cta: 'Consultar eleição', needsCatalog: true },
];
const PHASE = { pre_campaign: 'pré-campanha', campaign: 'campanha', transition: 'transição', office: 'no mandato', opposition: 'fora do cargo', term_complete: 'mandato concluído', runoff_campaign: 'segundo turno' };
const STEPS = [
  { target: 'modos', title: 'Escolha o caminho', text: 'Posse direta começa no governo. Carreira começa numa eleição. Militante começa pela vida partidária. Eleitor só consulta e vota em simulação.' },
  { target: 'partidas', title: 'Suas partidas', text: 'Aqui ficam as partidas salvas. Abra qualquer uma para continuar de onde parou.' },
  { target: 'novidades', title: 'O que mudou', text: 'Novidades da versão e o que vem nas próximas. Sem sair do jogo.' },
  { title: 'Dentro do jogo', text: 'Depois de começar, a barra lateral leva a cada área. O botão Avançar passa o tempo, e os Indicadores mostram o efeito das suas decisões.' },
];
const fmtDate = (d) => (d ? new Date(`${d}T12:00:00`).toLocaleDateString('pt-BR') : 'sem data');
const phaseName = (p) => PHASE[p] || String(p || '').replaceAll('_', ' ');

/** Menu inicial em formato de página de jornal: manchete à esquerda, serviço (partidas, novidades) à direita. */
export default function StartMenu({ active, hasSavedGame, onContinue, onPick, busy, catalogReady, campaigns = [], onActivate, difficultyLabel = (d) => d }) {
  const [tour, setTour] = useState(false);
  const today = new Date().toLocaleDateString('pt-BR', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
  const close = () => { markTour('inicio'); setTour(false); };

  return <div className="np">
    <header className="np-mast">
      <div className="np-rule"><span>Edição {VERSAO}</span><span>{today}</span><span>Simulação política · ficção</span></div>
      <h1>Quatro Anos</h1>
      <p className="np-tag">O jornal do seu mandato. Decida, acompanhe as consequências, preste contas.</p>
      <button type="button" className="ds-btn np-tour" onClick={() => setTour(true)}>{tourSeen('inicio') ? 'Rever o guia' : 'Guia rápido'}</button>
    </header>

    <div className="np-grid">
      <main className="np-main">
        {hasSavedGame
          ? <section className="np-lead" aria-label="Partida em andamento">
            <span className="ds-label">Em andamento</span>
            <h2>{active?.name || 'Sua partida salva'}</h2>
            <p>{[active?.office, phaseName(active?.phase), fmtDate(active?.date)].filter(Boolean).join(' · ')}</p>
            <button type="button" className="ds-btn primary" onClick={onContinue}>Continuar →</button>
          </section>
          : <section className="np-lead" aria-label="Boas-vindas">
            <span className="ds-label">Comece por aqui</span>
            <h2>Quatro anos para governar. Uma decisão por vez.</h2>
            <p>Escolha abaixo como quer jogar. Você pode rever o guia rápido a qualquer momento.</p>
          </section>}
        <section data-tour="modos" aria-label="Modos de jogo">
          <h3 className="np-sec">{hasSavedGame ? 'Nova partida' : 'Como jogar'}</h3>
          <div className="np-modes">
            {MODES.map((m) => <article key={m.key} className="np-mode">
              <div className="np-ico"><Icon name={m.icon} /></div>
              <div>
                <span className="ds-label">{m.kicker}</span>
                <h4>{m.title}</h4>
                <p>{m.text}</p>
                <button type="button" className="np-link" disabled={busy || (m.needsCatalog && !catalogReady)} onClick={() => onPick(m.key)}>{m.cta} →</button>
              </div>
            </article>)}
          </div>
        </section>
      </main>

      <aside className="np-side">
        <section data-tour="partidas" aria-label="Partidas salvas">
          <h3 className="np-sec">Partidas salvas ({campaigns.length})</h3>
          {campaigns.length === 0 ? <p className="ds-muted">Nenhuma ainda.</p>
            : <ul className="np-saved">{campaigns.slice(0, 6).map((c) => <li key={c.campaign_id} className={c.active ? 'on' : ''}>
              <div><b>{c.name}</b><small>{c.office} · {phaseName(c.phase)} · {fmtDate(c.date)} · {difficultyLabel(c.difficulty)}</small></div>
              <button type="button" className="np-link" disabled={busy || c.active} onClick={() => onActivate(c.campaign_id)}>{c.active ? 'Atual' : 'Abrir'}</button>
            </li>)}</ul>}
          {campaigns.length > 6 && <details className="np-more"><summary>Ver as outras {campaigns.length - 6}</summary>
            <ul className="np-saved">{campaigns.slice(6).map((c) => <li key={c.campaign_id}><div><b>{c.name}</b><small>{c.office} · {fmtDate(c.date)}</small></div><button type="button" className="np-link" disabled={busy} onClick={() => onActivate(c.campaign_id)}>Abrir</button></li>)}</ul></details>}
        </section>
        <section data-tour="novidades" aria-label="Novidades">
          <h3 className="np-sec">Novidades da {VERSAO}</h3>
          <ul className="ds-start-news">{NOVIDADES.map(([t, d]) => <li key={t}><b>{t}</b><span>{d}</span></li>)}</ul>
          <details className="np-more"><summary>O que vem por aí</summary>
            <ul className="ds-start-news">{EM_BREVE.map(([v, t, d]) => <li key={v}><b>{v} · {t}</b><span>{d}</span></li>)}</ul></details>
        </section>
      </aside>
    </div>
    {tour && <Tour steps={STEPS} onClose={close} />}
  </div>;
}
