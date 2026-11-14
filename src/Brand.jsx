export default function Brand({ compact = false }) {
  return <a className={`brand ${compact ? 'brand-compact' : ''}`} href="#" aria-label="Quatro Anos — simulador político do Brasil">
    <img className="brand-mark" src="/assets/brand/civiciclo-marca.png" alt="" aria-hidden="true" />
    {!compact && <span>QUATRO ANOS<small>SIMULADOR POLÍTICO DO BRASIL</small></span>}
  </a>;
}
