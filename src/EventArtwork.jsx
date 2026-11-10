import { useId } from 'react';

const SCENES = [
  ['flood', /enchent|alag|inunda|chuva|ressaca|tempestad/, 'ÁGUA E CLIMA', '#193c50', '#5bb5c3'],
  ['drought', /seca|estiagem|reservat|geada|calor/, 'CLIMA E TERRITÓRIO', '#4b3827', '#d4a663'],
  ['landslide', /desliz|encosta|soterr/, 'DEFESA CIVIL', '#463b32', '#c4af8d'],
  ['fire', /queimad|incend|fogo|fumaca/, 'EMERGÊNCIA', '#4a2c30', '#e69365'],
  ['health', /saude|hospital|vacina|epidemi|atendimento|medic/, 'SAÚDE PÚBLICA', '#24414a', '#7ac4b5'],
  ['power', /apagao|energia|eletric|internet|servico digital|infraestrutura|barragem/, 'INFRAESTRUTURA', '#263c50', '#8cacd4'],
  ['transport', /rodovia|ferrovia|transporte|cargas|porto|aeroporto|logistica/, 'MOBILIDADE', '#263d43', '#85b7a7'],
  ['justice', /justica|tribunal|liminar|contrato|denuncia|corrup|cpi|investig|integridade/, 'INSTITUIÇÕES', '#34344b', '#b3a3cb'],
  ['security', /seguranca|crime|policia|violencia|milicia/, 'SEGURANÇA', '#273c46', '#8ab8c8'],
  ['economy', /economia|mercado|preco|credito|juros|cambio|bolsa|abastec|inflacao|orcamento|fiscal|divida|investimento|balanco/, 'ECONOMIA', '#3d392c', '#c5b271'],
  ['labor', /greve|paralis|trabalho|sindica|servidor|salario/, 'TRABALHO', '#3d3540', '#c6a2ad'],
  ['diplomacy', /diplomacia|exterior|internacion|fronteira|embaix/, 'RELAÇÕES EXTERIORES', '#244251', '#88bed4'],
  ['education', /educac|escola|professor|universid/, 'EDUCAÇÃO', '#304044', '#b7c895'],
  ['culture', /cultura|arte|musica|festival|esporte/, 'CULTURA', '#443344', '#d2a4c4'],
  ['politics', /congresso|senado|camara|eleic|partido|militan|govern|mandato/, 'VIDA POLÍTICA', '#243e39', '#8bc2a1'],
];

function hashEvent(value) {
  let hash = 2166136261;
  for (const character of String(value)) hash = Math.imul(hash ^ character.charCodeAt(0), 16777619);
  return hash >>> 0;
}

function describe(event) {
  const text = [event?.id, event?.def, event?.kind, event?.title, ...(event?.tags || [])]
    .join(' ').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  return SCENES.find(([, expression]) => expression.test(text)) || ['politics', null, 'ACONTECIMENTO', '#263c3e', '#91b9a9'];
}

function titleLines(value) {
  const words = String(value || 'Acontecimento').split(/\s+/);
  const lines = [''];
  for (const word of words) {
    const current = lines.length - 1;
    if (lines[current] && (lines[current] + ' ' + word).trim().length > 33 && lines.length < 2) lines.push(word);
    else lines[current] = `${lines[current]} ${word}`.trim();
  }
  if (lines[1]?.length > 36) lines[1] = `${lines[1].slice(0, 35).trimEnd()}…`;
  return lines;
}

function SceneSymbol({ name }) {
  const common = { fill: 'none', stroke: 'currentColor', strokeWidth: 8, strokeLinecap: 'round', strokeLinejoin: 'round' };
  switch (name) {
    case 'flood': return <g {...common}><path d="M460 197l68-56 68 56M478 188v-37h22v19M477 198v42h103v-42" /><path d="M436 251c20-14 41-14 61 0s41 14 61 0 41-14 61 0M436 278c20-14 41-14 61 0s41 14 61 0 41-14 61 0" /></g>;
    case 'drought': return <g {...common}><circle cx="550" cy="139" r="38" /><path d="M443 251h60l26 23 21-21h78M479 219l38 20-18 27M568 220l-14 31 34 16" /></g>;
    case 'landslide': return <g {...common}><path d="M441 249l87-131 45 70 26-35 55 96H441Z" /><path d="M528 118l19 93 30 18M599 153l-21 70M480 249l22-26M616 249l16-20" /></g>;
    case 'fire': return <g {...common}><path d="M529 256c-28-19-33-46-8-75 2 20 17 21 17 21-5-37 10-51 23-67-2 38 36 43 36 80 0 24-18 44-44 44-13 0-23-9-24-21 0-12 12-20 17-29 11 11 21 19 18 34" /></g>;
    case 'health': return <g {...common}><rect x="482" y="145" width="132" height="112" rx="9" /><path d="M548 170v61M518 200h60M469 130h157M517 130V99h62v31" /></g>;
    case 'power': return <g {...common}><path d="M516 117h65l-12 140h-41l-12-140ZM508 146h81M502 181h92M521 217h57M548 94v-26M480 111l-29-20M610 111l29-20" /></g>;
    case 'transport': return <g {...common}><path d="M489 116h110l44 137H446l43-137ZM511 116l-14 137M577 116l14 137M543 141h28M538 187h38M530 236h53" /></g>;
    case 'justice': return <g {...common}><path d="M465 145l84-41 84 41M479 156h140M482 254h134M470 267h158M495 161v87M526 161v87M557 161v87M588 161v87" /></g>;
    case 'security': return <g {...common}><path d="M548 99l74 31v54c0 44-25 72-74 94-49-22-74-50-74-94v-54l74-31Z" /><path d="M515 187l23 24 48-51" /></g>;
    case 'economy': return <g {...common}><path d="M462 256h173M484 221v35M515 200v56M546 166v90M577 185v71M609 135v121" /><path d="M474 155l51-32 37 24 56-52" /></g>;
    case 'labor': return <g {...common}><circle cx="505" cy="173" r="18" /><circle cx="552" cy="157" r="21" /><circle cx="598" cy="173" r="18" /><path d="M477 247v-25c0-19 10-29 28-29s27 10 27 29M520 250v-32c0-24 10-39 32-39s32 15 32 39v32M576 222c0-19 9-29 22-29 19 0 28 10 28 29v25" /></g>;
    case 'diplomacy': return <g {...common}><circle cx="550" cy="182" r="76" /><path d="M475 182h150M550 106c25 23 40 47 40 76s-15 53-40 76M550 106c-25 23-40 47-40 76s15 53 40 76M493 139h114M493 225h114" /></g>;
    case 'education': return <g {...common}><path d="M548 134c-28-18-53-24-86-18v112c34-5 59 0 86 17 27-17 52-22 86-17V116c-33-6-58 0-86 18ZM548 134v111M478 143c19-1 37 3 54 11M565 154c18-8 36-12 54-11" /></g>;
    case 'culture': return <g {...common}><path d="M547 116v104c0 22-16 38-37 38-20 0-32-11-32-25s12-25 32-25c10 0 20 3 27 9V141l73-17v91c0 22-16 38-37 38-20 0-32-11-32-25s12-25 32-25c10 0 20 3 27 9v-88l-63 17" /></g>;
    default: return <g {...common}><path d="M466 140h164M483 145v105M520 145v105M557 145v105M594 145v105M458 264h180M548 97l-91 42h182l-91-42Z" /></g>;
  }
}

export default function EventArtwork({ event, compact = false }) {
  const reactId = useId().replace(/:/g, '');
  const [scene, , sceneLabel, base, accent] = describe(event);
  const hash = hashEvent(`${event?.id || ''}|${event?.title || ''}`);
  const lines = titleLines(event?.title);
  const serial = String(hash % 10000).padStart(4, '0');
  const topography = Array.from({ length: 6 }, (_, index) => ({
    x: 100 + ((hash >> (index % 4) * 5) + index * 109) % 690,
    y: 35 + ((hash >> (index % 5) * 4) + index * 39) % 250,
    r: 24 + ((hash >> (index % 3) * 7) + index * 17) % 90,
  }));
  return <svg className={`event-art${compact ? ' compact' : ''}`} viewBox={compact ? '390 70 300 220' : '0 0 800 320'} preserveAspectRatio="xMidYMid slice" role="img" aria-label={`Ilustração de ${event?.title || 'acontecimento'}`}>
    <defs><linearGradient id={reactId} x1="0" y1="0" x2="1" y2="1"><stop stopColor={base} /><stop offset="1" stopColor="#0b191e" /></linearGradient><clipPath id={`${reactId}-text`}><rect x="0" y="0" width="390" height="320" /></clipPath></defs>
    <rect width="800" height="320" fill={`url(#${reactId})`} />
    <path d="M0 257C173 231 250 292 391 256c134-35 262-4 409-39v103H0Z" fill={accent} opacity=".12" />
    {topography.map(({ x, y, r }, index) => <circle key={index} cx={x} cy={y} r={r} fill="none" stroke={accent} strokeWidth="1" opacity=".12" />)}
    <path d="M390 0v320" stroke={accent} strokeWidth="1" opacity=".3" />
    <g color={accent} opacity=".96"><SceneSymbol name={scene} /></g>
    <text x="660" y="276" textAnchor="end" fill={accent} fontSize="12" fontFamily="system-ui, sans-serif" letterSpacing="1" opacity=".8">{serial}</text>
    <g clipPath={`url(#${reactId}-text)`}>
      <text x="31" y="46" fill={accent} fontSize="15" fontFamily="system-ui, sans-serif" fontWeight="700" letterSpacing="2">CIVICICLO  /  {sceneLabel}</text>
      <text x="31" y="104" fill="#f1f5ee" fontSize="24" fontFamily="Georgia, serif" fontWeight="700">{lines.map((line, index) => <tspan key={index} x="31" dy={index ? 31 : 0}>{line}</tspan>)}</text>
      <path d="M31 267h205" stroke={accent} strokeWidth="2" opacity=".8" />
      <text x="31" y="291" fill="#bbcfca" fontSize="13" fontFamily="system-ui, sans-serif" letterSpacing="1">ARQUIVO DE EVENTOS  /  Nº {serial}</text>
    </g>
  </svg>;
}
