import { useEffect, useRef } from 'react';

// Endereço por tela (#/orcamento): botão voltar do navegador e links diretos funcionam. Não desenha nada.
export const slugOf = (tab) => tab.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');

export default function HashRoute({ tab, tabs, go }) {
  const started = useRef(false);
  const key = tabs.join('|');
  useEffect(() => {
    const apply = () => {
      const wanted = decodeURIComponent(window.location.hash.replace(/^#\/?/, ''));
      if (!wanted) return;
      const found = tabs.find((t) => slugOf(t) === wanted);
      if (found && found !== tab) go(found);
    };
    apply();
    window.addEventListener('popstate', apply);
    window.addEventListener('hashchange', apply);
    return () => { window.removeEventListener('popstate', apply); window.removeEventListener('hashchange', apply); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);
  useEffect(() => {
    if (!started.current) { started.current = true; return; }
    const hash = `#/${slugOf(tab)}`;
    if (window.location.hash !== hash) window.history.pushState(null, '', hash);
  }, [tab]);
  return null;
}
