import './start.css';
import Hero from './Hero';
import { Icon } from './Shell';
import { NOVIDADES, EM_BREVE, VERSAO } from './novidades';

const MODES = [
  { key: 'presidency', icon: 'Governo', kicker: 'Governo federal · 48 meses', title: 'Tomar posse no primeiro dia', text: 'Comece em 1º de janeiro de 2027 como presidente e conduza o governo pelos quatro anos.', bullets: ['Sem etapa de campanha', 'Orçamento, Congresso e agenda nacional'], cta: 'Configurar posse' },
  { key: 'career', icon: 'Politica', kicker: 'Campanha e carreira', title: 'Disputar uma eleição', text: 'Escolha cargo e território. Faça campanha, dispute a eleição e exerça o mandato se vencer.', bullets: ['De vereador a presidente', 'Poderes próprios de cada cargo'], cta: 'Escolher cargo e lugar', needsCatalog: true },
  { key: 'party', icon: 'Agenda', kicker: 'Militância e partido', title: 'Começar como militante', text: 'Comece como eleitor engajado, ganhe espaço no partido e chegue à candidatura a vereador.', bullets: ['Filiação e vida partidária', 'Pré-candidatura leva à campanha'], cta: 'Começar trajetória' },
  { key: 'elector', icon: 'Partidas', kicker: 'Modo eleitor · 2014 a 2030', title: 'Consultar e votar em simulação', text: 'Veja os candidatos oficiais de um pleito e escolha seu voto simulado, sem criar partida.', bullets: ['Dados oficiais do TSE com fonte', 'Nunca envia voto a eleição real'], cta: 'Abrir Modo Eleitor' },
];

const PHASE = { pre_campaign: 'pré-campanha', campaign: 'campanha', transition: 'transição', office: 'no mandato', opposition: 'fora do cargo', term_complete: 'mandato concluído', runoff_campaign: 'segundo turno' };

export default function StartMenu({ active, hasSavedGame, onContinue, onPick, busy, catalogReady, tutorial }) {
  const when = active?.date ? new Date(`${active.date}T12:00:00`).toLocaleDateString('pt-BR') : null;
  return <>
    <Hero name="inicio" mood="calmo" label="Um Brasil, vários caminhos" title="Onde começa sua história?" text="Entre direto no governo ou construa uma carreira desde a campanha. Cada decisão tem consequência." />
    {hasSavedGame && <section className="ds-start-continue" aria-label="Partida em andamento">
      <div>
        <span className="ds-label">Partida em andamento</span>
        <h2>{active?.name || 'Sua partida salva'}</h2>
        <p>{[active?.office, PHASE[active?.phase] || active?.phase?.replaceAll('_', ' '), when].filter(Boolean).join(' · ') || 'Continue de onde parou.'}</p>
      </div>
      <button type="button" className="ds-btn primary" onClick={onContinue}>Continuar →</button>
    </section>}
    <section className="ds-start-section" aria-label="Modos de jogo">
      <h2>{hasSavedGame ? 'Ou comece uma nova partida' : 'Escolha como jogar'}</h2>
      <div className="ds-start-modes">
        {MODES.map((m) => <article key={m.key} className="ds-card ds-start-mode">
          <div className="ds-start-icon"><Icon name={m.icon} /></div>
          <span className="ds-label">{m.kicker}</span>
          <h3>{m.title}</h3>
          <p>{m.text}</p>
          <ul>{m.bullets.map((b) => <li key={b}>{b}</li>)}</ul>
          <button type="button" className="ds-btn" disabled={busy || (m.needsCatalog && !catalogReady)} onClick={() => onPick(m.key)}>{m.cta} →</button>
        </article>)}
      </div>
    </section>
    <section className="ds-start-info">
      <article className="ds-card">
        <h3>Novidades da versão {VERSAO}</h3>
        <ul className="ds-start-news">{NOVIDADES.map(([t, d]) => <li key={t}><b>{t}</b><span>{d}</span></li>)}</ul>
      </article>
      <article className="ds-card">
        <h3>O que vem por aí</h3>
        <ul className="ds-start-news">{EM_BREVE.map(([v, t, d]) => <li key={v}><b>{v} · {t}</b><span>{d}</span></li>)}</ul>
      </article>
    </section>
    {tutorial}
  </>;
}
