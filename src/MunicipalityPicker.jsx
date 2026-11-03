import { useEffect, useRef, useState } from 'react';
import './municipality-picker.css';

const population = new Intl.NumberFormat('pt-BR');
const electorate = new Intl.NumberFormat('pt-BR');
const multiplier = new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

export default function MunicipalityPicker({ request, stateCode, value = '', selectedId = '', onSelect, label = 'Município', required = true, disabled = false }) {
  const [query, setQuery] = useState(value);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const [referenceYear, setReferenceYear] = useState(null);
  const [electorateYear, setElectorateYear] = useState(null);
  const [reachMultiplier, setReachMultiplier] = useState(null);
  const [electorateSource, setElectorateSource] = useState(null);
  const requestRef = useRef(request);
  requestRef.current = request;

  useEffect(() => { setQuery(value); }, [value]);
  useEffect(() => {
    let active = true;
    const term = query.trim();
    if (term.length < 2 || !stateCode) {
      setItems([]);
      setLoading(false);
      return () => { active = false; };
    }
    setLoading(true);
    const timer = setTimeout(() => {
      const params = new URLSearchParams({ state_code: stateCode, q: term, limit: '12' });
      requestRef.current(`/api/geography/municipalities?${params.toString()}`)
        .then((data) => { if (active) setItems(data.items || []); })
        .catch(() => { if (active) setItems([]); })
        .finally(() => { if (active) setLoading(false); });
    }, 220);
    return () => { active = false; clearTimeout(timer); };
  }, [stateCode, query]);

  function choose(item) {
    setQuery(item.name);
    setReferenceYear(item.population_reference_year);
    setElectorateYear(item.electorate_reference_year || null);
    setReachMultiplier(item.municipal_campaign_reach_multiplier || null);
    setElectorateSource(item.electorate_source_url || null);
    setItems([]);
    setOpen(false);
    onSelect({ id: item.ibge_code, name: item.name, profile: item });
  }

  return <div className="municipality-picker">
    <label>{label}
      <input
        type="search"
        value={query}
        onChange={(event) => {
          const next = event.target.value;
          setQuery(next);
          setOpen(true);
          setReferenceYear(null);
          setElectorateYear(null);
          setReachMultiplier(null);
          setElectorateSource(null);
          onSelect({ id: '', name: next, profile: null });
        }}
        onFocus={() => setOpen(true)}
        onBlur={() => setTimeout(() => setOpen(false), 120)}
        autoComplete="off"
        minLength={2}
        maxLength={80}
        required={required}
        disabled={disabled}
        placeholder="Digite duas letras e escolha uma cidade"
        aria-autocomplete="list"
        aria-expanded={open && query.trim().length >= 2}
      />
    </label>
    {open && query.trim().length >= 2 && <div className="municipality-results" role="listbox" aria-label="Municípios encontrados">
      {loading ? <span className="municipality-result-note">Buscando municípios…</span>
        : items.length ? items.map((item) => <button type="button" role="option" key={item.ibge_code} onMouseDown={(event) => event.preventDefault()} onClick={() => choose(item)}>
          <span><b>{item.name}</b><small>{item.state_code} · {item.city_size_label}</small></span>
          <span className="municipality-result-population"><small>{population.format(item.population_estimate)} hab.</small>{item.electorate_count && <small>{electorate.format(item.electorate_count)} eleitores aptos</small>}</span>
        </button>)
          : <span className="municipality-result-note">Nenhum município encontrado nesta UF.</span>}
    </div>}
    {selectedId && <small className="municipality-selection">Código IBGE {selectedId} · população estimada em {referenceYear || 2026}{electorateYear ? <> · eleitorado TSE {electorateYear}{electorateSource && <> · <a href={electorateSource} target="_blank" rel="noreferrer">fonte CC BY ↗</a></>}</> : ''}</small>}
    {selectedId && electorateYear && reachMultiplier && <small className="municipality-selection">Alcance local estimado ×{multiplier.format(reachMultiplier)} conforme o tamanho do eleitorado.</small>}
  </div>;
}
