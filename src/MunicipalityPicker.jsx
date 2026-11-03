import { useEffect, useRef, useState } from 'react';
import './municipality-picker.css';

const population = new Intl.NumberFormat('pt-BR');
const electorate = new Intl.NumberFormat('pt-BR');
const multiplier = new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const money = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 2 });
const billions = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 1 });
const sectorNames = {
  agriculture: 'Agropecuária',
  industry: 'Indústria',
  services: 'Serviços privados',
  public_services: 'Serviços públicos',
};
const percent = new Intl.NumberFormat('pt-BR', { style: 'percent', maximumFractionDigits: 1 });

export default function MunicipalityPicker({ request, stateCode, value = '', selectedId = '', onSelect, label = 'Município', required = true, disabled = false }) {
  const [query, setQuery] = useState(value);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const [profile, setProfile] = useState(null);
  const [economicSeriesAvailable, setEconomicSeriesAvailable] = useState(null);
  const requestRef = useRef(request);
  requestRef.current = request;

  useEffect(() => { setQuery(value); }, [value]);

  useEffect(() => {
    let active = true;
    const term = query.trim();
    if (!selectedId && term.length < 2) {
      setItems([]);
      setLoading(false);
      return () => { active = false; };
    }

    setLoading(true);
    const timer = setTimeout(() => {
      const params = selectedId
        ? new URLSearchParams({ ibge_code: selectedId, limit: '1' })
        : new URLSearchParams({ state_code: stateCode, q: term, limit: '12' });
      requestRef.current(`/api/geography/municipalities?${params.toString()}`)
        .then((data) => {
          if (!active) return;
          setItems(selectedId ? [] : data.items || []);
          if (selectedId) {
            const item = data.items?.[0];
            setProfile(item || null);
            setEconomicSeriesAvailable(item?.economic_series_available ?? false);
          }
        })
        .catch(() => {
          if (!active) return;
          setItems([]);
          if (selectedId) {
            setProfile(null);
            setEconomicSeriesAvailable(false);
          }
        })
        .finally(() => { if (active) setLoading(false); });
    }, selectedId ? 0 : 220);
    return () => { active = false; clearTimeout(timer); };
  }, [stateCode, query, selectedId]);

  function choose(item) {
    setQuery(item.name);
    setProfile(item);
    setEconomicSeriesAvailable(item.economic_series_available ?? false);
    setItems([]);
    setOpen(false);
    onSelect({ id: item.ibge_code, name: item.name, profile: item });
  }

  const economic = profile?.economic_profile;
  const leadingSector = economic?.leading_sector_2021;
  const leadingShare = leadingSector ? economic?.sector_shares_2021?.[leadingSector] : null;

  return <div className="municipality-picker">
    <label>{label}
      <input
        type="search"
        value={query}
        onChange={(event) => {
          const next = event.target.value;
          setQuery(next);
          setOpen(true);
          setProfile(null);
          setEconomicSeriesAvailable(null);
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
    {selectedId && profile && <small className="municipality-selection">Código IBGE {selectedId} · população estimada em {profile.population_reference_year || 2026}{profile.electorate_reference_year ? <> · eleitorado TSE {profile.electorate_reference_year}{profile.electorate_source_url && <> · <a href={profile.electorate_source_url} target="_blank" rel="noreferrer">fonte CC BY ↗</a></>}</> : ''}</small>}
    {selectedId && profile?.electorate_reference_year && profile?.municipal_campaign_reach_multiplier && <small className="municipality-selection">Alcance local estimado ×{multiplier.format(profile.municipal_campaign_reach_multiplier)} conforme o tamanho do eleitorado.</small>}
    {selectedId && profile && <details className="municipality-economic" aria-label="Contexto econ?mico municipal">
      <summary>{economic?.gdp_per_capita_brl != null ? <>IBGE ? PIB por pessoa {money.format(economic.gdp_per_capita_brl)} ({economic.gdp_reference_year}){leadingSector ? ` ? ${sectorNames[leadingSector]}` : ""}</> : economicSeriesAvailable ? "Perfil econ?mico do IBGE" : "PIB municipal sem registro nesta s?rie IBGE"}</summary>
      <div className="municipality-economic-details">
      {economic?.gdp_per_capita_brl != null && <span>PIB por pessoa: {money.format(economic.gdp_per_capita_brl)} ({economic.gdp_reference_year})</span>}
      {economic?.gdp_billion_brl != null && <span>PIB municipal: R$ {billions.format(economic.gdp_billion_brl)} bi ({economic.gdp_reference_year})</span>}
      {leadingSector && <span>Maior setor no valor adicionado: {sectorNames[leadingSector] || leadingSector} ({percent.format(leadingShare || 0)}, {economic.sector_reference_year})</span>}
      {economic?.sector_profile_status === 'not_comparable' && <span>Composição setorial sem percentuais comparáveis na base de {economic.sector_reference_year}.</span>}
      {economic && !leadingSector && economic.sector_profile_status !== 'not_comparable' && <span>Composição setorial não disponível nesta série.</span>}
      {!economicSeriesAvailable && <span>O IBGE não tem registro de PIB disponível para esta cidade nesta série.</span>}
      {profile.economic_source_url && <a href={profile.economic_source_url} target="_blank" rel="noreferrer">Consultar série e notas metodológicas do IBGE ↗</a>}
      </div></details>}
  </div>;
}
