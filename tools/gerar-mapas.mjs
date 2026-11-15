// Gera src/mapData.js (Brasil por estado e América do Sul por país) a partir de dois GeoJSON públicos.
// Uso: node tools/gerar-mapas.mjs <ibge-uf.geojson> <paises-mundo.geojson>
//   IBGE: https://servicodados.ibge.gov.br/api/v3/malhas/paises/BR?intrarregiao=UF&formato=application/vnd.geo+json&qualidade=minima
//   Países: https://github.com/datasets/geo-countries (Natural Earth, domínio público)
import fs from 'node:fs';

const [, , brPath, worldPath] = process.argv;
const UF = { 11: 'RO', 12: 'AC', 13: 'AM', 14: 'RR', 15: 'PA', 16: 'AP', 17: 'TO', 21: 'MA', 22: 'PI', 23: 'CE', 24: 'RN', 25: 'PB', 26: 'PE', 27: 'AL', 28: 'SE', 29: 'BA', 31: 'MG', 32: 'ES', 33: 'RJ', 35: 'SP', 41: 'PR', 42: 'SC', 43: 'RS', 50: 'MS', 51: 'MT', 52: 'GO', 53: 'DF' };
const SUL = { ARG: 'Argentina', BOL: 'Bolívia', BRA: 'Brasil', CHL: 'Chile', COL: 'Colômbia', ECU: 'Equador', GUY: 'Guiana', PRY: 'Paraguai', PER: 'Peru', SUR: 'Suriname', URY: 'Uruguai', VEN: 'Venezuela' };

const rings = (geom) => (geom.type === 'Polygon' ? [geom.coordinates] : geom.coordinates).flat();

function simplify(pts, tol) {
  if (pts.length < 3) return pts;
  const [fx, fy] = pts[0], [lx, ly] = pts[pts.length - 1];
  if (fx === lx && fy === ly) { const m = pts.length >> 1; return [...simplify(pts.slice(0, m + 1), tol), ...simplify(pts.slice(m), tol).slice(1)]; }
  const keep = new Array(pts.length).fill(false); keep[0] = keep[pts.length - 1] = true;
  const stack = [[0, pts.length - 1]];
  while (stack.length) {
    const [a, b] = stack.pop(); let max = 0, idx = -1;
    const [ax, ay] = pts[a], [bx, by] = pts[b]; const dx = bx - ax, dy = by - ay, len = Math.hypot(dx, dy) || 1e-9;
    for (let i = a + 1; i < b; i++) { const d = Math.abs(dy * pts[i][0] - dx * pts[i][1] + bx * ay - by * ax) / len; if (d > max) { max = d; idx = i; } }
    if (max > tol && idx > 0) { keep[idx] = true; stack.push([a, idx], [idx, b]); }
  }
  return pts.filter((_, i) => keep[i]);
}

function build(features, idOf, tol, width) {
  const all = features.flatMap((f) => rings(f.geometry).flat());
  const lats = all.map((p) => p[1]); const midLat = (Math.min(...lats) + Math.max(...lats)) / 2;
  const k = Math.cos((midLat * Math.PI) / 180);
  const proj = (p) => [p[0] * k, -p[1]];
  const xs = all.map((p) => proj(p)[0]), ys = all.map((p) => proj(p)[1]);
  const minX = Math.min(...xs), minY = Math.min(...ys), scale = width / (Math.max(...xs) - minX);
  const height = Math.ceil((Math.max(...ys) - minY) * scale);
  const items = features.map((f) => {
    const d = rings(f.geometry).map((ring) => {
      const pts = simplify(ring.map(proj), tol / scale).map(([x, y]) => [(x - minX) * scale, (y - minY) * scale]);
      if (pts.length < 4) return '';
      return 'M' + pts.map(([x, y]) => `${x.toFixed(1)} ${y.toFixed(1)}`).join('L') + 'Z';
    }).join('');
    return { id: idOf(f), d };
  });
  return { viewBox: `0 0 ${width} ${height}`, items: items.filter((i) => i.id && i.d) };
}

const br = JSON.parse(fs.readFileSync(brPath, 'utf8'));
const world = JSON.parse(fs.readFileSync(worldPath, 'utf8'));
const brasil = build(br.features, (f) => UF[f.properties.codarea], 0.6, 600);
const sul = build(world.features.filter((f) => SUL[f.properties['ISO3166-1-Alpha-3']]), (f) => f.properties['ISO3166-1-Alpha-3'], 0.9, 600);
sul.names = SUL;
const out = `// Gerado por tools/gerar-mapas.mjs. Fontes: IBGE (malha de UFs) e Natural Earth (domínio público). Não edite à mão.\nexport const BRASIL = ${JSON.stringify(brasil)};\nexport const AMSUL = ${JSON.stringify(sul)};\n`;
fs.writeFileSync('src/mapData.js', out);
console.log('BRASIL', brasil.items.length, brasil.viewBox, 'AMSUL', sul.items.length, sul.viewBox, (out.length / 1024).toFixed(0) + ' KB');
