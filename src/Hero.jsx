import { useState } from 'react';
import { fmt } from './ui';

const PALETTE = {
  calmo: { top: '#0b1a1c', mid: '#1c3a33', low: '#8a7a3f', sun: '#d8b25a', sunOpacity: 0.85 },
  tenso: { top: '#0b1518', mid: '#2a3033', low: '#6b5a36', sun: '#c79a4a', sunOpacity: 0.5 },
  crise: { top: '#0a0f12', mid: '#2b1d1f', low: '#5a2e2a', sun: '#e5776c', sunOpacity: 0.55 },
};

/** Esplanada em duas cores. É a arte padrão: se existir public/assets/hero/<nome>.webp, a imagem real a substitui. */
function HeroArt({ mood }) {
  const c = PALETTE[mood] || PALETTE.calmo;
  const id = `hero-${mood}`;
  return <svg className="ds-hero-art" viewBox="0 0 1200 420" preserveAspectRatio="xMidYMax slice" aria-hidden="true">
    <defs>
      <linearGradient id={`${id}-ceu`} x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor={c.top} /><stop offset=".55" stopColor={c.mid} /><stop offset="1" stopColor={c.low} /></linearGradient>
      <linearGradient id={`${id}-chao`} x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#26332a" /><stop offset="1" stopColor="#0b1216" /></linearGradient>
    </defs>
    <rect width="1200" height="420" fill={`url(#${id}-ceu)`} />
    <circle cx="930" cy="250" r="64" fill={c.sun} opacity={c.sunOpacity} />
    {mood === 'crise' && <path d="M760 30l-34 86h30l-26 84 78-110h-34l30-60z" fill="#f4d9a0" opacity=".28" />}
    <g fill="#0b1216" opacity=".92">
      <rect x="420" y="120" width="26" height="170" /><rect x="470" y="120" width="26" height="170" /><rect x="380" y="270" width="150" height="26" />
      <path d="M230 296a90 38 0 01180 0z" /><path d="M560 296a76 52 0 01152 0z" />
      <rect x="120" y="190" width="70" height="106" /><rect x="200" y="210" width="70" height="86" /><rect x="760" y="200" width="70" height="96" /><rect x="840" y="220" width="70" height="76" />
    </g>
    <rect y="296" width="1200" height="124" fill={`url(#${id}-chao)`} />
  </svg>;
}

/** Faixa de abertura de uma seção: imagem (ou arte padrão), rótulo, manchete e uma frase. */
export default function Hero({ name = 'painel', mood = 'calmo', badge, label, title, text }) {
  const [imageOk, setImageOk] = useState(false);
  return <header className="ds-hero">
    <HeroArt mood={mood} />
    <img className="ds-hero-img" hidden={!imageOk} alt="" src={`/assets/hero/hero-${name}-${mood}.webp`} onLoad={() => setImageOk(true)} onError={() => setImageOk(false)} />
    {badge && <div className="ds-hero-badge"><span>{badge}</span></div>}
    <div className="ds-hero-text">
      {label && <div className="ds-label">{label}</div>}
      <h1>{title}</h1>
      {text && <p>{text}</p>}
    </div>
  </header>;
}

const BETTER = { approval: 'up', congress_support: 'up', institutional_trust: 'up', integrity: 'up', gdp_growth: 'up', inflation: 'down', unemployment: 'down', debt_gdp: 'down' };
const PHRASE = {
  approval: [(m) => `A aprovação do governo cai para ${fmt(m.now)}%`, (m) => `A aprovação do governo sobe para ${fmt(m.now)}%`],
  inflation: [(m) => `A inflação sobe para ${fmt(m.now)}% ao ano`, (m) => `A inflação recua para ${fmt(m.now)}% ao ano`],
  unemployment: [(m) => `O desemprego sobe para ${fmt(m.now)}%`, (m) => `O desemprego cai para ${fmt(m.now)}%`],
  debt_gdp: [(m) => `A dívida pública chega a ${fmt(m.now)}% do PIB`, (m) => `A dívida pública cai para ${fmt(m.now)}% do PIB`],
  integrity: [(m) => `A integridade do governo cai para ${fmt(m.now, 0)}/100`, (m) => `A integridade do governo sobe para ${fmt(m.now, 0)}/100`],
  congress_support: [(m) => `A base no Congresso encolhe para ${fmt(m.now)}%`, (m) => `A base no Congresso cresce para ${fmt(m.now)}%`],
  institutional_trust: [(m) => `A confiança nas instituições cai para ${fmt(m.now, 0)}/100`, (m) => `A confiança nas instituições sobe para ${fmt(m.now, 0)}/100`],
};

/** Manchete do dia, escrita só com os números do motor (sem IA): pega a mudança mais forte desde o início da partida. */
export function headline(review, crisis) {
  if (crisis) return { mood: 'crise', title: crisis.title, text: 'Há uma decisão esperando resposta. Se o prazo acabar, vale a opção padrão.' };
  const rows = (review?.metrics || []).filter((m) => Number.isFinite(m.delta));
  if (!rows.length) return { mood: 'calmo', title: 'O mandato está começando.', text: 'Avance o tempo para ver como o país reage às suas decisões.' };
  const scale = { approval: 5, congress_support: 5, institutional_trust: 5, integrity: 5, gdp_growth: 1, inflation: 1, unemployment: 1, debt_gdp: 4 };
  const scored = rows.map((m) => ({ m, force: Math.abs(m.delta) / (scale[m.key] || 1), worse: (m.delta > 0) !== (BETTER[m.key] === 'up') })).sort((a, b) => b.force - a.force);
  const top = scored[0];
  if (top.force < 0.4) return { mood: 'calmo', title: 'O país segue estável.', text: 'Nenhum indicador mudou de forma relevante desde o início da partida.' };
  const text = PHRASE[top.m.key]?.[top.worse ? 0 : 1]?.(top.m);
  const approval = rows.find((m) => m.key === 'approval');
  const worseCount = scored.filter((s) => s.force >= 0.4 && s.worse).length;
  const mood = worseCount >= 3 || (approval && approval.now < 35) ? 'tenso' : 'calmo';
  const second = scored.slice(1).find((s) => s.force >= 0.4);
  return { mood, title: `${text}.`, text: second ? `${PHRASE[second.m.key]?.[second.worse ? 0 : 1]?.(second.m)}.` : 'Os demais indicadores mudaram pouco desde o início.' };
}
