import { useState } from 'react';

// Arte dos cartões em SVG, no mesmo estilo editorial plano das imagens de cabeçalho (azul-marinho, ouro, verde).
// Se existir public/assets/cards/<grupo>-<id>.webp, a imagem real substitui a arte, sem mexer em código.
const C = { navy: '#0d1a2c', mid: '#15253d', sky: '#2a6fa8', gold: '#ffd23f', gold2: '#f5b800', green: '#1f7a4a', ice: '#f3f6fb', red: '#e2554a', wine: '#4a1d3a' };

const hash = (text) => [...String(text)].reduce((h, ch) => (h * 31 + ch.charCodeAt(0)) >>> 0, 7);

function Sky({ id, night, children }) {
  const h = hash(id);
  const sunX = 60 + (h % 200);
  return <>
    <rect width="320" height="200" fill={night ? C.navy : C.sky} />
    {!night && <rect y="90" width="320" height="110" fill={C.mid} opacity=".35" />}
    {night
      ? [...Array(18)].map((_, i) => <circle key={i} cx={(h * (i + 3)) % 320} cy={(h * (i + 7)) % 120} r={i % 4 === 0 ? 1.6 : 1} fill={C.ice} opacity=".8" />)
      : <><circle cx={sunX} cy="60" r="22" fill={C.gold} opacity=".95" /><ellipse cx={sunX + 60} cy="48" rx="46" ry="7" fill={C.gold2} opacity=".35" /></>}
    {children}
  </>;
}

const TRANSPORT = {
  ponte: (id) => <Sky id={id}>
    <rect y="150" width="320" height="50" fill={C.green} />
    <rect y="132" width="320" height="10" fill={C.ice} /><rect y="142" width="320" height="8" fill={C.mid} />
    {[60, 160, 260].map((x) => <g key={x}><rect x={x} y="80" width="7" height="62" fill={C.ice} /><path d={`M${x + 3} 82 L${x - 55} 132 M${x + 3} 82 L${x + 61} 132`} stroke={C.gold} strokeWidth="1.6" fill="none" /></g>)}
  </Sky>,
  estrada: (id) => <Sky id={id}>
    <path d="M0 150 q90 -40 180 -8 t140 -14 V200 H0 Z" fill={C.green} />
    <path d="M-10 196 Q150 120 330 130 L330 150 Q160 140 10 200 Z" fill={C.mid} /><path d="M10 192 Q160 134 330 140" stroke={C.gold} strokeWidth="3" strokeDasharray="14 10" fill="none" />
  </Sky>,
  trilho: (id) => <Sky id={id}>
    <path d="M0 140 q90 -24 180 -4 t140 -6 V200 H0 Z" fill={C.green} />
    <path d="M140 200 L150 120 M200 200 L170 120" stroke={C.ice} strokeWidth="4" />
    {[196, 178, 162, 148, 136].map((y, i) => <path key={y} d={`M${150 - (y - 120) * 0.12 - 20 + i} ${y} H${190 + (y - 120) * 0.1 + 12 - i}`} stroke={C.gold2} strokeWidth="3" />)}
  </Sky>,
  pista: (id) => <Sky id={id}>
    <rect y="140" width="320" height="60" fill={C.green} />
    <path d="M40 200 L130 138 H230 L300 200 Z" fill={C.mid} /><path d="M165 196 L170 142" stroke={C.ice} strokeWidth="3" strokeDasharray="8 6" />
    <rect x="236" y="96" width="10" height="46" fill={C.ice} /><rect x="228" y="84" width="26" height="14" fill={C.gold2} />
    <path d="M60 80 l40 8 l-6 6 Z" fill={C.ice} />
  </Sky>,
  agua: (id) => <Sky id={id}>
    <rect y="130" width="320" height="70" fill={C.sky} /><path d="M0 150 q20 -8 40 0 t40 0 t40 0 t40 0 t40 0 t40 0 t40 0 t40 0" stroke={C.ice} strokeWidth="1.6" fill="none" opacity=".6" />
    <rect x="30" y="138" width="130" height="14" fill={C.mid} /><rect x="60" y="120" width="70" height="18" fill={C.gold2} />
    <rect x="220" y="70" width="8" height="70" fill={C.ice} /><path d="M224 74 H290 V90" stroke={C.ice} strokeWidth="5" fill="none" /><rect x="224" y="140" width="80" height="60" fill={C.green} />
  </Sky>,
};
const TRANSPORT_OF = { Ponte: 'ponte', Viaduto: 'ponte', Rodovia: 'estrada', BRT: 'estrada', Ferrovia: 'trilho', 'Porto e ferrovia': 'trilho', Metrô: 'trilho', Aeroporto: 'pista', Porto: 'agua', Hidrovia: 'agua' };

const SCENES = {
  Transportes: (id, kind) => (TRANSPORT[TRANSPORT_OF[kind]] || TRANSPORT.ponte)(id),
  'Espaço e ciência': (id) => <Sky id={id} night>
    <circle cx="255" cy="55" r="26" fill={C.ice} opacity=".92" /><circle cx="246" cy="48" r="5" fill={C.mid} opacity=".25" /><circle cx="262" cy="64" r="7" fill={C.mid} opacity=".2" />
    <rect y="168" width="320" height="32" fill={C.green} opacity=".85" />
    <rect x="96" y="64" width="6" height="104" fill={C.ice} opacity=".5" /><path d="M96 80 h-14 M96 110 h-14 M96 140 h-14" stroke={C.ice} strokeWidth="2" opacity=".5" />
    <path d="M150 168 V92 q12 -34 24 0 V168 Z" fill={C.ice} /><path d="M150 108 q12 -42 24 0 Z" fill={C.red} /><path d="M150 158 l-10 14 h10 Z M174 158 l10 14 h-10 Z" fill={C.gold2} />
    <path d="M156 168 q6 26 12 0 Z" fill={C.gold} />
  </Sky>,
  'Energia e campo': (id) => <Sky id={id}>
    <path d="M0 150 q80 -34 160 -4 t160 -8 V200 H0 Z" fill={C.green} />
    {[70, 150, 235].map((x, i) => <g key={x} transform={`translate(${x} ${96 + (i % 2) * 8})`}><rect x="-2" y="0" width="4" height="58" fill={C.ice} />{[0, 120, 240].map((a) => <rect key={a} x="-1.6" y="-26" width="3.2" height="26" fill={C.ice} transform={`rotate(${a + 20 * i} 0 0)`} />)}<circle r="3.6" fill={C.gold} /></g>)}
  </Sky>,
  'Cidades e saneamento': (id) => <Sky id={id}>
    <rect y="156" width="320" height="44" fill={C.green} />
    {[[40, 110, 38], [86, 90, 44], [140, 122, 34], [188, 84, 46], [240, 108, 40]].map(([x, y, w]) => <g key={x}><rect x={x} y={y} width={w} height={156 - y} fill={C.ice} /><rect x={x + 6} y={y + 8} width="7" height="9" fill={C.sky} /><rect x={x + w - 14} y={y + 8} width="7" height="9" fill={C.sky} /></g>)}
    <path d="M0 176 q80 -10 160 0 t160 0" stroke={C.sky} strokeWidth="6" fill="none" opacity=".9" />
  </Sky>,
  Reformas: (id) => <Sky id={id}>
    <rect y="156" width="320" height="44" fill={C.green} />
    <rect x="70" y="100" width="180" height="56" fill={C.ice} /><path d="M60 100 L160 58 L260 100 Z" fill={C.gold2} />
    {[96, 140, 184, 214].map((x) => <rect key={x} x={x} y="116" width="14" height="40" fill={C.sky} />)}
    <path d="M40 156 L70 80 M70 156 L40 80 M40 118 h30" stroke={C.gold} strokeWidth="2.4" />
  </Sky>,
  Saúde: (id) => <Sky id={id}>
    <rect y="158" width="320" height="42" fill={C.green} />
    <rect x="90" y="76" width="140" height="82" fill={C.ice} /><rect x="146" y="58" width="28" height="18" fill={C.ice} />
    <rect x="155" y="92" width="10" height="34" fill={C.red} /><rect x="143" y="104" width="34" height="10" fill={C.red} />
    {[104, 124, 188, 208].map((x) => <rect key={x} x={x} y="130" width="10" height="28" fill={C.sky} />)}
  </Sky>,
  Educação: (id) => <Sky id={id}>
    <rect y="158" width="320" height="42" fill={C.green} />
    <rect x="80" y="104" width="160" height="54" fill={C.ice} /><path d="M70 104 L160 62 L250 104 Z" fill={C.red} opacity=".9" />
    {[100, 130, 190, 220].map((x) => <rect key={x} x={x} y="120" width="12" height="38" fill={C.sky} />)}
    <rect x="156" y="124" width="10" height="34" fill={C.mid} /><rect x="160" y="40" width="2" height="26" fill={C.ice} /><path d="M162 40 h18 l-5 5 5 5 h-18 Z" fill={C.gold} />
  </Sky>,
  'Segurança e defesa': (id) => <Sky id={id}>
    <rect y="160" width="320" height="40" fill={C.green} />
    <rect x="150" y="84" width="14" height="76" fill={C.ice} /><path d="M120 84 q37 -44 74 0 Z" fill={C.ice} /><circle cx="157" cy="68" r="4" fill={C.gold} />
    <path d="M200 70 q22 10 22 34 M208 56 q36 14 36 52" stroke={C.gold} strokeWidth="2" fill="none" opacity=".8" />
    <rect x="60" y="130" width="50" height="30" fill={C.mid} /><rect x="230" y="136" width="46" height="24" fill={C.mid} />
  </Sky>,
  Crise: (id) => <Sky id={id} night>
    <rect width="320" height="200" fill={C.wine} opacity=".5" />
    <circle cx="240" cy="96" r="34" fill={C.red} opacity=".85" />
    <path d="M0 150 q60 -30 120 -4 t120 -6 t80 6 V200 H0 Z" fill={C.navy} />
  </Sky>,
};

export const categoryOf = (category) => (SCENES[category] ? category : 'Transportes');

export default function CardArt({ group = 'obra', id, category, kind, className = '' }) {
  const [imageOk, setImageOk] = useState(false);
  const scene = SCENES[categoryOf(category)](id || category, kind);
  return <div className={`ds-cardart ${className}`} aria-hidden="true">
    <svg viewBox="0 0 320 200" preserveAspectRatio="xMidYMid slice">{scene}</svg>
    <img hidden={!imageOk} alt="" loading="lazy" src={`/assets/cards/${group}-${id}.webp`} onLoad={() => setImageOk(true)} onError={() => setImageOk(false)} />
  </div>;
}
