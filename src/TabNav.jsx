

/** Parte de App.jsx: linha:410. Recebe do App o estado e as ações de que precisa. */
export default function TabNav({ activeTab, baseGroups, pins, selectedTabGroup, setActiveTab, togglePin }) {
  return (
    <nav className="ds-tabs" aria-label={`Seções de ${selectedTabGroup.label}`}>{selectedTabGroup.hidden && <button type="button" className="ds-tab back" onClick={() => setActiveTab(baseGroups[0].items[0])}>← Voltar ao jogo</button>}{selectedTabGroup.items.map((tab) => <button key={tab} className="ds-tab" aria-selected={activeTab === tab} onClick={() => setActiveTab(tab)}>{tab}</button>)}<button type="button" className="ds-tab-pin" aria-pressed={pins.includes(activeTab)} title={pins.includes(activeTab) ? 'Tirar do menu lateral' : 'Fixar no menu lateral'} onClick={() => togglePin(activeTab)}>{pins.includes(activeTab) ? '★ Fixada' : '☆ Fixar'}</button></nav>
  );
}
