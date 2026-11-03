# Perfil economico municipal

O seletor de municipios pode mostrar um retrato economico curto da cidade escolhida. O painel e descritivo: esses numeros ainda nao alteram o resultado de campanhas nem representam preferencia politica dos moradores.

## Fontes e referencias

- PIB municipal e PIB por pessoa: IBGE, Produto Interno Bruto dos Municipios, ano de referencia 2023. Os valores estao sujeitos a revisao. O PIB por pessoa de 2023 usa a populacao do Censo 2022, conforme a nota metodologica do IBGE.
- Valor adicionado por atividade: ultima composicao setorial disponivel nesta serie, ano de referencia 2021. O arquivo separa agropecuaria, industria, servicos privados e servicos publicos.
- A populacao municipal segue a estimativa do IBGE de 2026; o eleitorado segue o TSE de 2026. Sao referencias diferentes e nao devem ser somadas nem tratadas como medidas simultaneas.
- A importacao e offline e reproduzivel por `python -m app.data.economic_import --zip <arquivo-do-IBGE>` dentro de `backend`. O jogo nao consulta o IBGE durante a partida.

## Cobertura e ausencias

A serie importada cobre 5.570 dos 5.571 municipios do catalogo atual. O codigo `5101837` (Boa Esperanca do Norte) nao tem registro nesta edicao. O perfil permanece `null`; o jogo nao estima um valor substituto.

A composicao setorial so e exibida quando os componentes e o total permitem calcular participacoes comparaveis. Uma linha oficial com componentes negativos ou valor adicionado total nao positivo continua preservada como dado de contexto, mas nao vira percentuais nem um setor lider. Isso ocorre em Cachoeira Dourada (GO) na referencia de 2021.

## Como aparece no jogo

Depois de escolher uma cidade validada pelo codigo IBGE, a tela mostra PIB por pessoa e, quando houver calculo comparavel, o maior setor no valor adicionado. A cidade de nascimento do personagem e um campo separado do territorio da candidatura e das cidades visitadas em campanha.

O jogo ainda nao usa o perfil economico para conceder bonus eleitorais ou prever comportamento. Uma futura regra precisara de calibracao propria, fontes e explicacao visivel antes de mudar efeitos de jogo.

## Fontes oficiais

- [IBGE: PIB dos Municipios](https://www.ibge.gov.br/estatisticas/economicas/contas-nacionais/9088-produto-interno-bruto-dos-municipios.html)
- [Serie TXT 2010-2023 do IBGE](https://ftp.ibge.gov.br/Pib_Municipios/2022_2023/base/base_de_dados_2010_2023_txt.zip)
