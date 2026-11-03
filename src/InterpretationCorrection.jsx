import { useState } from 'react';
import './interpretation-correction.css';

const categories = [
  ['fiscal_efficiency', 'Eficiência fiscal'],
  ['business_formalization', 'Formalização de empresas'],
  ['public_investment', 'Investimento público'],
  ['tax_change', 'Mudança tributária'],
  ['social_policy', 'Política social'],
  ['security', 'Segurança'],
  ['communication', 'Comunicação'],
  ['other', 'Outro'],
];

const instruments = [
  'Ato do Executivo', 'Projeto de Lei', 'Projeto de Lei Complementar',
  'PEC', 'Decreto', 'Medida Provisória', 'Indefinido',
];

export default function InterpretationCorrection({ preview, measure, request, onSaved, onNotice, busy, setBusy }) {
  const [note, setNote] = useState('');
  const [category, setCategory] = useState('');
  const [instrument, setInstrument] = useState('');
  const hasCorrection = Boolean(note.trim() || category || instrument);

  async function save() {
    if (!preview || !hasCorrection) return;
    const labels = Object.fromEntries(Object.entries({ category, instrument }).filter(([, value]) => value));
    setBusy(true);
    try {
      const data = await request('/api/learning/corrections', {
        method: 'POST',
        body: JSON.stringify({
          original_text: measure,
          corrected_interpretation: note.trim() || 'Rótulos estruturados confirmados pelo jogador.',
          labels,
        }),
      });
      onSaved(data);
      setNote('');
      setCategory('');
      setInstrument('');
      onNotice(data.training_labels_saved
        ? 'Correção salva como exemplo supervisionado. O modelo local ainda não foi ativado.'
        : 'Correção textual salva para orientar leituras futuras.');
    } catch (error) {
      onNotice(error.message);
    } finally {
      setBusy(false);
    }
  }

  return <details className="correction">
    <summary>Revisar esta interpretação para o treino offline</summary>
    <p>Os campos escolhidos viram rótulos de treino. Eles não alteram o custo nem o efeito calculado pelo jogo.</p>
    <div className="correction-label-grid">
      <label>Categoria correta<select value={category} onChange={(event) => setCategory(event.target.value)}>
        <option value="">Não revisar</option>
        {categories.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
      </select></label>
      <label>Instrumento correto<select value={instrument} onChange={(event) => setInstrument(event.target.value)}>
        <option value="">Não revisar</option>
        {instruments.map((value) => <option key={value} value={value}>{value}</option>)}
      </select></label>
    </div>
    <label className="correction-note">Observação opcional<textarea value={note} onChange={(event) => setNote(event.target.value)} placeholder="Explique em poucas palavras o que a leitura entendeu errado." /></label>
    <button className="secondary-button" onClick={save} disabled={busy || !hasCorrection}>Guardar correção</button>
  </details>;
}
