import { useEffect, useState } from 'react';
import './tse-archive.css';

const dateLabel = (value) => value ? new Date(value).toLocaleDateString('pt-BR') : '—';

export default function TSEArchivePanel({ request, stateCode = '' }) {
  const [status, setStatus] = useState(null);
  const [year, setYear] = useState('');
  const [query, setQuery] = useState('');
  const [office, setOffice] = useState('');
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [notice, setNotice] = useState('');

  useEffect(() => {
    let alive = true;
    request('/api/data/tse/status').then((data) => {
      if (!alive) return;
      setStatus(data);
      if (data.years?.length) setYear(String(data.years[0].election_year));
    }).catch((error) => { if (alive) setNotice(error.message); });
    return () => { alive = false; };
  }, []);

  useEffect(() => {
    if (!status?.ready || !year) return undefined;
    let alive = true;
    const timer = setTimeout(() => {
      const params = new URLSearchParams({ year, limit: '30' });
      if (stateCode) params.set('state_code', stateCode);
      if (office.trim()) params.set('office', office.trim());
      if (query.trim()) params.set('search', query.trim());
      request(`/api/data/tse/candidates?${params.toString()}`)
        .then((data) => { if (alive) { setItems(data.items || []); setTotal(data.total || 0); setNotice(''); } })
        .catch((error) => { if (alive) setNotice(error.message); });
    }, 220);
    return () => { alive = false; clearTimeout(timer); };
  }, [request, status?.ready, year, query, office, stateCode]);

  return <section className="panel tse-archive">
    <header><div><span className="eyebrow">DADOS ELEITORAIS · FONTE PÚBLICA</span><h3>Arquivo de candidaturas do TSE</h3><p>Consulte registros históricos para dar contexto ao cenário. Candidatura não comprova mandato atual, posição política ou conduta.</p></div><a href={status?.source_url || 'https://dadosabertos.tse.jus.br/group/candidatos'} target="_blank" rel="noreferrer">Portal oficial ↗</a></header>
    {!status?.ready ? <div className="tse-empty"><b>Os dados ainda não foram importados para esta instalação.</b><p>Importe somente os anos necessários. O pacote do TSE é baixado pelo servidor e os campos pessoais desnecessários são descartados.</p><code>cd backend<br/>python -m app.data.tse_import --years 2024</code><a href="https://dadosabertos.tse.jus.br/group/candidatos" target="_blank" rel="noreferrer">Ver conjuntos e licença no TSE ↗</a></div> : <>
      <div className="tse-import-status"><span>{total.toLocaleString('pt-BR')} resultado(s) nesta busca · máximo de 30 exibidos</span><small>{status.years.map((item) => `${item.election_year}: ${Number(item.candidate_count).toLocaleString('pt-BR')} candidaturas`).join(' · ')}</small></div>
      <div className="tse-filters"><label>Ano da eleição<select value={year} onChange={(event) => setYear(event.target.value)}>{status.years.map((item) => <option key={item.election_year} value={item.election_year}>{item.election_year}</option>)}</select></label><label>Cargo contém<input value={office} onChange={(event) => setOffice(event.target.value)} placeholder="Ex.: Vereador, Governador" /></label><label>Buscar nome<input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Nome de urna ou nome civil" /></label><span>UF: {stateCode || 'Todas'}</span></div>
      {items.length ? <div className="tse-results">{items.map((item) => <article key={`${item.election_year}-${item.candidate_id}`}><div><b>{item.display_name || 'Nome não informado'}</b><span>{item.office} · {item.municipality}/{item.state}</span></div><strong>{item.party || 'Sem partido'}</strong><small>Eleição {item.election_year} · {item.result_status || 'situação não informada'}</small><a href={item.source_url} target="_blank" rel="noreferrer">Fonte · licença {item.license_name || 'TSE'} ↗</a></article>)}</div> : <div className="empty-state">Nenhuma candidatura encontrada com esses filtros. Tente outro ano, cargo ou nome.</div>}
    </>}
    {notice && <p className="notice">{notice}</p>}
    <small className="tse-disclaimer">Fonte: Tribunal Superior Eleitoral. Registros eleitorais públicos usados como referência histórica. Fotos, endereços e dados pessoais sensíveis não são copiados por este importador.</small>
  </section>;
}
