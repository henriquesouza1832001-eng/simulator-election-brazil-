# Fontes e atribuição

## Tribunal Superior Eleitoral

Portal consultado: [dadosabertos.tse.jus.br](https://dadosabertos.tse.jus.br/). O catálogo atual lista conjuntos por eleição para candidaturas, resultados, eleitorado, comparecimento/abstenção, prestação de contas, pesquisas e processos. Cada conjunto informa sua própria atualização, formatos, recursos e licença. O importador inicial usa a API CKAN do portal para encontrar a planilha principal de candidaturas; ele não baixa nem copia fotos ou certidões em massa.

O conjunto **Candidatos - 2024** identifica o TSE/AGEL como fonte, informa licença Creative Commons Atribuição, atualização diária e contém recursos de candidaturas, informações complementares, bens, coligações, vagas, motivo de cassação, redes sociais, fotos e propostas. A atribuição será mantida junto aos registros importados. A licença e a data de cada pacote devem ser relidas no momento da ingestão, pois podem variar por dataset.

## Instituto Brasileiro de Geografia e Estatística

O catálogo municipal registra código, nome, UF e região pela API de Localidades do IBGE. A população usa as estimativas municipais da tabela SIDRA 6579, variável 9324; o ano de referência é guardado por registro e a data populacional é 1º de julho do respectivo ano. A importação atual usa 2026 e cobre 5.571 municípios. As URLs e a nota de licença acompanham o arquivo `backend/app/data/municipalities.json`; a API consultada não declara licença por registro, então o jogo preserva atribuição e proveniência.

Porte e multiplicador de alcance sao regras ficticias do simulador, nao uma classificacao oficial do IBGE nem uma previsao eleitoral. O catalogo tambem mostra perfil economico municipal, com PIB e PIB por pessoa de 2023 e composicao setorial de 2021 quando comparavel. Ausencias e limites estao em [PERFIL_ECONOMICO_MUNICIPAL.md](PERFIL_ECONOMICO_MUNICIPAL.md). Eleitorado, IDHM e temas-ancora nao estao incluidos como preferencias locais.

- [IBGE SIDRA, tabela 6579, vari?vel 9324](https://servicodados.ibge.gov.br/api/v3/agregados/6579/periodos/2026/variaveis/9324?localidades=N6%5Ball%5D)
- [IBGE API de Localidades](https://servicodados.ibge.gov.br/api/v1/localidades/municipios?orderBy=nome)
- [Estimativas da população do IBGE](https://www.ibge.gov.br/estatisticas/sociais/populacao/9103)

## Uso dentro do jogo

Armazenar: identificador eleitoral, nome público/urna, partido, cargo disputado, UF/município, status do resultado e alguns dados de perfil estritamente úteis ao jogo. Para calcular desempenho, associar o identificador ao conjunto oficial de votação nominal. Para valores de campanha, consultar prestação de contas. Não copiar CPF, título, endereço residencial, dados bancários ou certificados criminais para o perfil lúdico.

Fotos e caricaturas são ativos diferentes. A foto oficial será vinculada à página/conjunto do TSE. Uma caricatura original não substitui a foto, não deve fingir ser imagem documental e será rotulada como sátira.

## Verificação de fonte

- [Portal de Dados Abertos do TSE](https://dadosabertos.tse.jus.br/)
- [Página institucional do Portal de Dados Abertos](https://www.tse.jus.br/administracao/painel/portal-de-dados-abertos-do-tse)
- [Candidatos - 2024: conjunto, recursos e licença](https://dadosabertos.tse.jus.br/dataset/candidatos-2024)
- [CKAN: API documentada](https://docs.ckan.org/en/2.11/api/)
