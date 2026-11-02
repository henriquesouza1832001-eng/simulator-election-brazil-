# Direção do jogo

## Fantasia e estrutura

Um simulador de carreira política e governo brasileiro, jogável no navegador e baseado em calendário diário. A campanha pode começar na política municipal, crescer por eleições e nomeações, e continuar por mandatos sucessivos. A jornada não será uma escada automática: cada cargo abre caminhos diferentes, e perder uma eleição muda o percurso sem encerrar necessariamente a carreira.

### Caminhos de carreira

- Entrada: liderança comunitária, assessor ou candidatura a vereador.
- Cargos eletivos: vereador, prefeito, deputado estadual, deputado federal, senador, governador e presidente.
- Nomeações: secretarias, ministérios e outros postos administrativos, com indicação, audiência/avaliação e coalizão.
- STF: rota separada de nomeação; o motor cria candidatos fictícios elegíveis quando o conjunto público não oferece perfis adequados. Requisitos legais e etapas serão mantidos num catálogo datado e revisado.
- Cada cargo define território, mandato, orçamento, equipe, atribuições, calendário eleitoral, indicadores próprios e relações políticas.

O primeiro ciclo pode ser uma campanha municipal seguida do mandato conquistado. Para quem prefere começar no Planalto, o jogo também poderá oferecer cenário de governo pronto.

## Dificuldade

Os cinco níveis reutilizam as mesmas regras centrais; mudam pressão, margem de erro, recursos e frequência de eventos. Assim, um evento não se contradiz entre modos.

| Modo | O que muda |
| --- | --- |
| Tranquilo | Mais caixa e apoio inicial, aviso antecipado e recuperação mais rápida. |
| Normal | Equilíbrio padrão, consequências graduais e eventos previsíveis. |
| Difícil | Coalizões menores, oposição mais ativa e choques mais frequentes. |
| Complicado | Pouca folga fiscal e política; efeitos acumulados pesam mais. |
| Realismo Puro | Parâmetros calibrados por dados históricos, restrições institucionais explícitas e sem bônus de ajuda. Eventos continuam ficcionais quando ocorrerem dentro da partida. |

## Indicadores e impostos

- A tela inicial mostra poucos cartões escolhidos pelo jogador. O painel de configurações permite fixar, remover e ordenar indicadores; detalhes ficam em páginas temáticas.
- O núcleo usa cinco dimensões resumidas: economia, contas públicas, apoio, governabilidade e integridade. Indicadores locais (saúde, educação, segurança, serviços, votos e popularidade territorial) aparecem de acordo com o cargo.
- Impostos começam com alavancas legíveis: famílias de baixa, média e alta renda; agro, indústria, serviços, bancos e digital. A tela mostra quem paga, receita aproximada, prazo e risco para atividade.
- Cada opção tributária representa uma posição no espectro econômico. As escolhas são combinações, não estereótipos de partido. O jogador pode montar sua própria linha.

## Dados de pessoas e partidos

O importador iniciado nesta base busca candidaturas no CKAN do TSE e guarda campos minimizados com ano, cargo, partido, município/UF, resultado declarado e proveniência. A próxima camada agrega votos por candidatura a partir dos conjuntos de resultados e contas de campanha por CNPJ/candidato.

Dados eleitorais são fatos de uma eleição, não cadastro completo de quem ocupa hoje cada cargo. Trajetória em governos, mandatos atuais, votações legislativas, biografia e indicações exigem fontes oficiais adicionais. Cada fato terá URL, instituição, data de referência e nível de confiança. O jogo não inferirá culpa, ideologia ou caráter a partir de uma candidatura ou dado cadastral.

## Eventos e RAG

1. Um motor de regras determina se uma situação ocorre e seus efeitos de jogo, usando cargo, território, estado, alianças, dificuldade, orçamento e histórico.
2. O recuperador procura fatos e documentos oficiais pertinentes (TSE, Câmara, Senado, governos, legislação e estatísticas públicas) com fonte e data.
3. A IA escreve o texto e as opções em JSON, citando os trechos usados. Ela não inventa placares nem altera indicadores diretamente.
4. A notícia recebe um rótulo explícito: registro público, dado histórico ou ficção do jogo. Uma crise aleatória pode ser fictícia, mas não será apresentada como notícia real.

Oracle hospeda o backend, banco e índice de busca. Para uma pessoa, começar com SQLite para jogo e busca textual é simples; a camada vetorial poderá usar Qdrant ou pgvector quando o volume documental justificar. RAG não é treinamento de modelo: recupera trechos antes de cada geração. As correções do jogador viram exemplos de interpretação; elas não reescrevem as regras econômicas.

## Retratos

Fotos eleitorais vêm do recurso de fotos do TSE quando necessário e com atribuição. Caricaturas originais serão apenas para um conjunto curto de figuras de alto reconhecimento, escolhido depois de importar e classificar os dados; cada asset terá registro da pessoa, fonte da imagem de referência, arquivo, criador/modelo e nota de sátira. As demais pessoas usam avatares gerados por iniciais ou retratos fictícios. A separação por pastas já está planejada em `public/assets/portraits/{official,caricatures,fictional}`.

## Etapas de desenvolvimento

1. **Agora:** estrutura de dados e regras para carreira/dificuldade; importação TSE com proveniência; especificação de telas e fontes.
2. Criar campanha municipal inicial e eleição funcional, popularidade territorial e avanço entre cargos.
3. Implementar perfis de cada cargo, partidos/blocos e nomeações; depois adicionar legislativo e Supremo.
4. Dar ao jogador controles de indicadores, tributos e orçamento; calibrar efeitos e cinco dificuldades.
5. Construir RAG com fontes oficiais, indexação e eventos com rótulos claros.
6. Selecionar elenco principal e produzir caricaturas originais; preservar fotos oficiais e atribuições separadamente.
7. Calibrar o agente Python por episódios sintéticos, depois comparar com campanhas históricas agregadas sem copiar resultados individuais como destino obrigatório.

## Limites importantes

- O TSE cobre candidaturas, eleições, contas, bens declarados, propostas, fotos e dados eleitorais conforme cada conjunto/ano; não entrega uma enciclopédia unificada de políticos.
- Resultados de eleição e cargos atuais são entidades distintas e precisam de importadores próprios.
- Dados pessoais sensíveis e endereços serão excluídos do catálogo de jogo. Informações públicas não são automaticamente necessárias para a simulação.
- Valores do modo Realismo Puro serão rastreáveis e calibrados; enquanto não houver evidência suficiente, serão apresentados como hipótese de jogo, não como previsão real.
