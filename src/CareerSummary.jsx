

/** Parte de App.jsx: linha:275. Recebe do App o estado e as ações de que precisa. */
export default function CareerSummary({ overview, section, sections, setSection, setShowSetup }) {
  return (
    <nav className="career-subnav" aria-label="Seções da carreira">{sections.map((item) => <button key={item} className={section === item ? 'active' : ''} onClick={() => setSection(item)}>{item}</button>)}<span/>{overview.can_start_campaign && <button onClick={() => setShowSetup(true)}>Nova candidatura</button>}</nav>
  );
}
