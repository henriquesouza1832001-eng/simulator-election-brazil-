import { useEffect, useRef, useState } from 'react';
import './municipality-picker.css';

const population = new Intl.NumberFormat('pt-BR');

export default function MunicipalityPicker({ request, stateCode, value = '', selectedId = '', onSelect, label = 'Município' }) {
  const [query, setQuery] = useState(value);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const [referenceYear, setReferenceYear] = useState(null);
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
          onSelect({ id: '', name: next, profile: null });
        }}
        onFocus={() => setOpen(true)}
        onBlur={() => setTimeout(() => setOpen(false), 120)}
        autoComplete="off"
        minLength={2}
        maxLength={80}
        required
        placeholder="Digite duas letras e escolha uma cidade"
        aria-autocomplete="list"
        aria-expanded={open && query.trim().length >= 2}
      />
    </label>
    {open && query.trim().length >= 2 && <div className="municipality-results" role="listbox" aria-label="Municípios encontrados">
      {loading ? <span className="municipality-result-note">Buscando municípios…</span>
        : items.length ? items.map((item) => <button type="button" role="option" key={item.ibge_code} onMouseDown={(event) => event.preventDefault()} onClick={() => choose(item)}>
          <span><b>{item.name}</b><small>{item.state_code} · {item.city_size_label}</small></span>
          <small>{population.format(item.population_estimate)} hab.</small>
        </button>)
          : <span className="municipality-result-note">Nenhum município encontrado nesta UF.</span>}
    </div>}
    {selectedId && <small className="municipality-selection">Código IBGE {selectedId} · população estimada em {referenceYear || 2026}</small>}
  </div>;
}
