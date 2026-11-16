import { useEffect, useMemo, useState } from 'react';
import { Section, Badge, Empty } from './ui.jsx';
import Select from './Choice.jsx';
import { br } from './format';

const NAMES = { AC: 'Acre', AL: 'Alagoas', AP: 'Amapá', AM: 'Amazonas', BA: 'Bahia', CE: 'Ceará', DF: 'Distrito Federal', ES: 'Espírito Santo', GO: 'Goiás', MA: 'Maranhão', MT: 'Mato Grosso', MS: 'Mato Grosso do Sul', MG: 'Minas Gerais', PA: 'Pará', PB: 'Paraíba', PR: 'Paraná', PE: 'Pernambuco', PI: 'Piauí', RJ: 'Rio de Janeiro', RN: 'Rio Grande do Norte', RS: 'Rio Grande do Sul', RO: 'Rondônia', RR: 'Roraima', SC: 'Santa Catarina', SP: 'São Paulo', SE: 'Sergipe', TO: 'Tocantins' };

// Cartograma em mosaico: cada quadrado é um município, com tamanho pelo eleitorado e cor pelo vencedor.
function sizeClass(rank, total) {
  const p = rank / total;
  return p < 0.005 ? 'xl' : p < 0.03 ? 'l' : p < 0.13 ? 'm' : 's';
}
function colorOf(share) {
  const strength = Math.min(1, Math.abs(share - 50) / 25);
  const alpha = (0.35 + 0.6 * strength).toFixed(2);
  return share >= 50 ? `rgba(217,180,74,${alpha})` : `rgba(111,143,201,${alpha})`;
}

export default function MunicipiosMapa({ request, state, uf: wanted }) {
  const [data, setData] = useState(null);
  const [uf, setUf] = useState(wanted || '');
  const [error, setError] = useState('');
  const [pick, setPick] = useState(null);
  useEffect(() => { if (wanted) setUf(wanted); }, [wanted]);
  useEffect(() => {
    setPick(null);
    request(`/api/election/tally/municipal${uf ? `?uf=${uf}` : ''}`).then((d) => { setData(d); setError(''); if (!uf && d.uf) setUf(d.uf); }).catch((e) => setError(e.message));
  }, [uf, state?.date]);

  const tiles = data?.tiles || [];
  const top = useMemo(() => tiles.slice(0, 8), [tiles]);
  if (error) return <Section title="Mapa por município"><p className="meta-status meta-error" role="alert">{error}</p></Section>;
  if (!data) return <Section title="Mapa por município"><Empty title="Carregando…" /></Section>;
  if (!data.available) return <Section title="Mapa por município"><Empty title="Ainda não há mapa">{data.reason}</Empty></Section>;

  const sel = pick && tiles.find((t) => t.id === pick);
  return <Section title="Mapa por município" hint="Cada quadrado é um município, do maior eleitorado ao menor. Dourado: você ganhou. Azul: o adversário ganhou. Quanto mais forte a cor, maior a margem.">
    <div className="ds-mm-head">
      {data.ufs.length > 1
        ? <label className="ds-mm-pick">Estado<Select value={data.uf} onChange={(e) => setUf(e.target.value)}>{data.ufs.map((u) => <option key={u} value={u}>{NAMES[u] || u}</option>)}</Select></label>
        : <b>{NAMES[data.uf] || data.uf}</b>}
      <div className="ds-mm-stats">
        <span>Seu total no estado <b>{br(data.state_share, 1)}%</b></span>
        <span>Municípios ganhos <b>{br(data.won, 0)}</b> de {br(data.municipalities, 0)}</span>
        <span>Eleitorado desses municípios <b>{br(data.won_electorate_pct, 1)}%</b></span>
      </div>
    </div>
    <div className="ds-mm">
      <div className="ds-mm-grid" role="group" aria-label={`Municípios de ${NAMES[data.uf] || data.uf}`}>
        {tiles.map((t, i) => <button key={t.id} type="button" className={`ds-mm-tile ${sizeClass(i, tiles.length)} ${pick === t.id ? 'on' : ''}`} style={{ background: colorOf(t.share) }}
          title={`${t.name}: ${br(t.share, 1)}% para você`} aria-label={`${t.name}: ${br(t.share, 1)}% para você, ${t.winner === 'player' ? 'você ganhou' : 'adversário ganhou'}`} onClick={() => setPick(t.id)} />)}
      </div>
      <aside className="ds-card ds-mm-side">
        {sel ? <>
          <h4>{sel.name}</h4>
          <dl className="pj-facts">
            <dt>Você</dt><dd>{br(sel.share, 1)}%</dd>
            <dt>Adversário</dt><dd>{br(100 - sel.share, 1)}%</dd>
            <dt>Eleitorado</dt><dd>{br(sel.electorate, 0)} eleitores</dd>
            <dt>Resultado</dt><dd><Badge tone={sel.winner === 'player' ? 'good' : 'bad'}>{sel.winner === 'player' ? 'Você ganhou' : 'Adversário ganhou'}</Badge></dd>
          </dl>
        </> : <p className="ds-muted">Toque em um quadrado para ver o município.</p>}
        <h4>Maiores colégios</h4>
        <ul className="ds-list ds-mm-top">{top.map((t) => <li key={t.id}><button type="button" className="ds-link" onClick={() => setPick(t.id)}>{t.name}</button><span className="ds-muted">{br(t.share, 1)}%</span></li>)}</ul>
        <p className="ds-muted">{data.note}</p>
      </aside>
    </div>
  </Section>;
}
