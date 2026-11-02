# Fontes e atribuição

## Tribunal Superior Eleitoral

Portal consultado: [dadosabertos.tse.jus.br](https://dadosabertos.tse.jus.br/). O catálogo atual lista conjuntos por eleição para candidaturas, resultados, eleitorado, comparecimento/abstenção, prestação de contas, pesquisas e processos. Cada conjunto informa sua própria atualização, formatos, recursos e licença. O importador inicial usa a API CKAN do portal para encontrar a planilha principal de candidaturas; ele não baixa nem copia fotos ou certidões em massa.

O conjunto **Candidatos - 2024** identifica o TSE/AGEL como fonte, informa licença Creative Commons Atribuição, atualização diária e contém recursos de candidaturas, informações complementares, bens, coligações, vagas, motivo de cassação, redes sociais, fotos e propostas. A atribuição será mantida junto aos registros importados. A licença e a data de cada pacote devem ser relidas no momento da ingestão, pois podem variar por dataset.

## Uso dentro do jogo

Armazenar: identificador eleitoral, nome público/urna, partido, cargo disputado, UF/município, status do resultado e alguns dados de perfil estritamente úteis ao jogo. Para calcular desempenho, associar o identificador ao conjunto oficial de votação nominal. Para valores de campanha, consultar prestação de contas. Não copiar CPF, título, endereço residencial, dados bancários ou certificados criminais para o perfil lúdico.

Fotos e caricaturas são ativos diferentes. A foto oficial será vinculada à página/conjunto do TSE. Uma caricatura original não substitui a foto, não deve fingir ser imagem documental e será rotulada como sátira.

## Verificação de fonte

- [Portal de Dados Abertos do TSE](https://dadosabertos.tse.jus.br/)
- [Página institucional do Portal de Dados Abertos](https://www.tse.jus.br/administracao/painel/portal-de-dados-abertos-do-tse)
- [Candidatos - 2024: conjunto, recursos e licença](https://dadosabertos.tse.jus.br/dataset/candidatos-2024)
- [CKAN: API documentada](https://docs.ckan.org/en/2.11/api/)
