// Ligações entre telas (árvore do guia de interface): cada tela aponta para onde o assunto continua.
const RELATED = {
  'Visão geral': [['Indicadores', 'cada número tem origem e o que o move'], ['Crises', 'o que está pedindo resposta'], ['Imprensa', 'como a notícia do dia foi contada'], ['Agenda', 'prazos e compromissos']],
  Indicadores: [['Orçamento', 'onde o dinheiro público muda estes números'], ['Obras e mapa', 'obras que mexem nos indicadores'], ['Histórico', 'a evolução desde o primeiro dia']],
  Histórico: [['Indicadores', 'estado atual de cada número'], ['Competências', 'decisões que podem mudar a trajetória']],
  Medidas: [['Competências', 'o que o seu cargo permite fazer'], ['Tramitação', 'projetos que dependem do Congresso'], ['Orçamento', 'custo e espaço fiscal da medida']],
  Competências: [['Empresas', 'participação e controle de estatais'], ['Orçamento', 'efeito nas contas'], ['Tramitação', 'leis que dependem de votação']],
  Empresas: [['Orçamento', 'juros e dividendos entram nas contas'], ['Competências', 'privatizar e estatizar exige lei'], ['Indicadores', 'inflação, emprego e atividade']],
  Orçamento: [['Obras e mapa', 'onde o investimento vira obra'], ['Indicadores', 'resultado fiscal e dívida'], ['Empresas', 'dividendos e Selic']],
  'Obras e mapa': [['Orçamento', 'de onde vem o dinheiro das obras'], ['Indicadores', 'efeito nos indicadores locais'], ['Crises', 'problemas que as obras podem evitar']],
  Crises: [['Agenda', 'prazo para responder'], ['Imprensa', 'repercussão da crise'], ['Redes', 'o que se diz nas redes'], ['Orçamento', 'custo das respostas']],
  Carreira: [['Eleição', 'campanha e pesquisa'], ['Apuração', 'resultado urna a urna'], ['Congresso', 'base e votos']],
  Eleição: [['Apuração', 'dia da votação'], ['Redes', 'publicações e humor sobre a campanha'], ['Entrevistas', 'debates e sabatinas'], ['Semana', 'atividades de campanha']],
  Apuração: [['Eleição', 'o que levou a este resultado'], ['Redes', 'a reação nas redes'], ['Imprensa', 'a manchete da noite']],
  Redes: [['Imprensa', 'a versão dos jornais'], ['Eleição', 'pesquisa e campanha'], ['Crises', 'fatos que geram publicação']],
  Congresso: [['Tramitação', 'projetos em andamento'], ['Nomeações', 'cargos que movem a base'], ['Instituições', 'estabilidade e confiança']],
  Tramitação: [['Congresso', 'quem vota e quem apoia'], ['Medidas', 'novas propostas'], ['Nomeações', 'negociar apoio']],
  Nomeações: [['Congresso', 'efeito na base'], ['Instituições', 'confiança e estabilidade']],
  Instituições: [['Reguladores', 'agências e decisões técnicas'], ['Nomeações', 'indicações ao STF e ao gabinete']],
  Reguladores: [['Instituições', 'estabilidade geral'], ['Competências', 'estrutura do Banco Central e agências']],
  Diplomacia: [['Indicadores', 'câmbio e comércio'], ['Imprensa', 'repercussão externa']],
  Imprensa: [['Redes', 'o que as redes dizem'], ['Crises', 'crises ativas'], ['Entrevistas', 'responder à imprensa']],
  Entrevistas: [['Imprensa', 'repercussão da entrevista'], ['Eleição', 'efeito nas pesquisas']],
  Acontecimentos: [['Crises', 'crises em andamento'], ['Agenda', 'prazos das decisões']],
  Agenda: [['Crises', 'o que pede resposta agora'], ['Tramitação', 'votações marcadas']],
};

export default function Related({ tab, exists, go }) {
  const links = (RELATED[tab] || []).filter(([t]) => exists.has(t) && t !== tab);
  if (!links.length) return null;
  return <nav className="ds-related" aria-label="Telas ligadas a esta">
    <span>Ligado a esta tela</span>
    <ul>{links.map(([t, why]) => <li key={t}><button type="button" onClick={() => go(t)}><b>{t}</b><small>{why}</small></button></li>)}</ul>
  </nav>;
}
