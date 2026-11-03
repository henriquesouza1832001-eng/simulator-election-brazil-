export default function Brand({ compact = false }) {
  return <a className={`brand ${compact ? 'brand-compact' : ''}`} href="#" aria-label="Civiciclo — simulador político do Brasil">
    <svg className="brand-mark" viewBox="0 0 40 40" role="img" aria-hidden="true">
      <rect x="1" y="1" width="38" height="38" rx="11" fill="currentColor" opacity=".12" />
      <path d="M27.5 12.8a11.2 11.2 0 1 0 1.1 13.7" fill="none" stroke="currentColor" strokeWidth="3.2" strokeLinecap="round" />
      <path d="m25.1 10.1 5.4 2-2.2 5.3" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx="20" cy="20" r="3.1" fill="#d1a94f" />
    </svg>
    {!compact && <span>CIVICICLO<small>SIMULADOR POLÍTICO DO BRASIL</small></span>}
  </a>;
}
