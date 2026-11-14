import { Page, Section } from './ui';

const TODAY = [
  ['Sete cargos, cada um com os poderes da Constituição', 'De vereador a presidente. Cada ação mostra a base legal, o custo e o risco de ser barrada.'],
  ['Congresso e reguladores', 'Bancadas dos partidos reais, comissões, relatores, urgência, sanção e veto; STF, AGU, tribunais de contas, PF e Ministério Público e TSE respondem às suas decisões.'],
  ['Indicadores do país e das cidades', 'Mais de sessenta indicadores ligados entre si, com dados de partida do Atlas do Desenvolvimento Humano e do IBGE.'],
  ['Eleições', 'Campanha, debates e apuração; e as eleições de 2014 a 2024 podem ser jogadas com os candidatos oficiais do TSE e comparadas com o resultado real.'],
  ['Contas públicas', 'Orçamento, LRF para estados e municípios, empresas estatais, obras e CPIs.'],
  ['Balanço do mandato', 'No fim dos 48 meses, o que mudou indicador por indicador e uma nota calculada por regra fixa.'],
];
const ROADMAP = [
  ['0.4', 'Base de interface e informação (concluída)'],
  ['0.5', 'Direção visual: identidade, navegação e desempenho (próxima)'],
  ['0.6', 'Motor: economia e Estado, empresas, Banco Central e Selic'],
  ['0.7', 'Gemini conectado ao jogo'],
  ['0.8', 'Congresso, eleições, contas e nuvem'],
  ['0.9', 'Balanceamento e acabamento'],
  ['1.0', 'Jogo completo'],
];
const SOURCES = [
  ['TSE (dados abertos)', 'Partidos, candidaturas e votos de eleições passadas, com fonte e licença registradas.'],
  ['IBGE', 'Municípios, população e PIB.'],
  ['Atlas do Desenvolvimento Humano (via Ipeadata)', 'Indicadores municipais do Censo 2010: IDHM, Gini, pobreza, saneamento e outros.'],
  ['Câmara dos Deputados e Senado Federal (dados abertos)', 'Composição do Congresso.'],
];

function Item({ title, children }) { return <div className="ds-gloss"><b>{title}</b><p>{children}</p></div>; }

export default function AboutPanel({ section }) {
  if (section === 'Termos') return <Page title="Termos e avisos" lead="O que você precisa saber antes de jogar.">
    <Section>
      <Item title="É uma obra de ficção satírica">Candidatos, pesquisas, empresas e acontecimentos criados pelo jogo são inventados. Nenhuma pessoa real participa e nenhum fato atual é afirmado pelos indicadores.</Item>
      <Item title="Dados reais só como ponto de partida">Partidos, parlamentares, cidades e resultados de eleições passadas vêm de fontes públicas e servem de cenário, não de acusação ou elogio a ninguém.</Item>
      <Item title="Inteligência artificial">O jogo funciona sem IA. Quando o Gemini for conectado (versão 0.7), ele só interpreta texto e narra fatos que o motor já decidiu; o motor continua decidindo todos os números.</Item>
      <Item title="Seus dados">As partidas ficam no servidor do jogo, ligadas à sua conta ou ao seu navegador. Nada é vendido nem enviado a terceiros.</Item>
      <Item title="Independência">É uma criação independente, com regras próprias, sem vínculo com partidos, órgãos públicos ou outros jogos.</Item>
    </Section>
  </Page>;

  if (section === 'Créditos') return <Page title="Créditos" lead="De onde vêm os dados e o que o jogo usa.">
    <Section title="Fontes de dados">{SOURCES.map(([t, d]) => <Item key={t} title={t}>{d}</Item>)}</Section>
    <Section title="Sobre o projeto"><Item title="Quatro Anos">Simulador político do Brasil em desenvolvimento. O motor de regras é determinístico: o mesmo cenário produz o mesmo resultado.</Item></Section>
  </Page>;

  return <Page title="O jogo" lead="Quatro Anos é um simulador político do Brasil: você conduz um mandato de 48 meses ou constrói uma carreira de vereador a presidente.">
    <Section title="O que já funciona">{TODAY.map(([t, d]) => <Item key={t} title={t}>{d}</Item>)}</Section>
    <Section title="Para onde vai" hint="A versão atual é a 0.4. O roteiro completo está em docs/ROADMAP_VERSOES.md.">
      <ul className="ds-list">{ROADMAP.map(([v, t]) => <li key={v}><span className="ds-muted">versão {v}</span><b>{t}</b></li>)}</ul>
    </Section>
  </Page>;
}
