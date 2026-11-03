# Dados públicos, nomes e sátira

Revisado em 3 de novembro de 2026. Este documento define cuidados de produto e
proveniência; não é parecer jurídico nem garantia de que todo uso esteja livre
de contestação.

## Regra de produto

Podemos usar nomes de partidos e registros eleitorais como dados factuais,
guardando a fonte, a data de consulta e a licença. O portal do TSE identifica o
conjunto de candidaturas de 2026 como **Creative Commons Attribution** e lista
arquivos de candidaturas, histórico e fotos como recursos. Na tela de dados e
no catálogo, atribuir ao Tribunal Superior Eleitoral, ligar ao conjunto usado e
indicar eventuais alterações de formato.

O rótulo **Sátira · cenário fictício** é necessário, mas não transforma uma
afirmação falsa sobre pessoa real em fato protegido por si só. A Constituição
protege a expressão artística e também a honra e a imagem. O Código Civil
prevê proteção quando uso de imagem atinge honra, reputação ou finalidade
comercial. A decisão do STF na ADI 4815 afastou autorização prévia para
biografias, mas não é uma imunidade geral para caricaturas, jogos, alegações
inventadas ou uso comercial.

Por isso, o jogo separa duas camadas:

- **Registro público factual:** nome tal como consta na eleição, sigla do
  partido, cargo disputado, território, situação registrada e resultado, sempre
  com ano, fonte e data de extração. Não presumir que uma candidatura prova o
  cargo atual, uma ideologia ou uma conduta.
- **Narrativa simulada:** falas, pesquisas, escândalos, decisões, alianças,
  acusações e eventos do jogo pertencem a personagens fictícios. Não atribuir
  crime, propina ou outra acusação factual inventada a uma pessoa real. Se uma
  partida usar nomes reais, limitar o material associado a eles a informação
  verificável e manter o aviso de ficção junto da narrativa.

## Retratos e marcas

O portal do TSE oferece fotos como recursos separados do conjunto de dados. A
licença indicada no nível do conjunto não substitui o registro de proveniência
de cada arquivo. Para cada retrato usado, guardar URL, titular/crédito conforme
publicado, licença mostrada para o recurso, data de obtenção e transformações.
Só gerar uma caricatura depois dessa checagem; registrar também o artista ou
ferramenta, a imagem de referência e a versão resultante. Se a licença do
arquivo não estiver clara, usar avatar original que não reproduza a fotografia
e manter personagem fictício até revisão.

Usar nomes e siglas partidárias como informação identificadora não exige que o
jogo use logotipos. Preferir texto simples e deixar explícito que o partido não
patrocina nem endossa o jogo. O mesmo vale para nomes de empresas em notícias
simuladas: preferir empresas fictícias; quando uma empresa real for necessária
para contextualizar um fato verdadeiro, identificá-lo com fonte e não sugerir
endosso ou envolvimento em fato fictício.

## Importação mínima

Para o catálogo jogável, importar somente o necessário para identificar o
registro eleitoral: nome público, ano, cargo, UF/município, sigla partidária,
status registrado e votação/resultado quando a base correspondente existir.
Não importar CPF, endereço, bens, certidões, raça, religião, saúde ou dados de
familiares para construir personagens. A LGPD diz que até dados pessoais de
acesso público devem ser tratados considerando finalidade, boa-fé e interesse
público; opiniões e filiação política são dados sensíveis quando vinculadas a
uma pessoa. O eixo ideológico de uma partida é uma escolha fictícia e nunca
deve ser inferido de uma sigla real.

Formato mínimo de proveniência no catálogo:

```json
{
  "source_name": "Tribunal Superior Eleitoral — Candidatos 2026",
  "source_url": "https://dadosabertos.tse.jus.br/pt_BR/dataset/candidatos-2026",
  "retrieved_at": "YYYY-MM-DD",
  "dataset_year": 2026,
  "license": "Creative Commons Attribution",
  "modified": false
}
```

## Antes de publicar ou vender

- Revisar o aviso de sátira no menu, nas notícias e nos retratos, sem esconder
  a fonte dos dados factuais.
- Conferir cada alegação associada a pessoa ou empresa real; ficção não deve
  aparecer como notícia verdadeira.
- Revisar a licença e a atribuição de cada foto e caricatura, e remover a arte
  quando a proveniência não puder ser comprovada.
- Fazer busca de disponibilidade do nome Civiciclo e da marca gráfica no INPI;
  o nome continua provisório até essa busca.
- Submeter o catálogo e as peças promocionais a revisão jurídica antes de uma
  distribuição comercial ampla.

## Fontes oficiais consultadas

- [TSE — Candidatos 2026 e licença do conjunto](https://dadosabertos.tse.jus.br/pt_BR/dataset/candidatos-2026)
- [Constituição Federal — art. 5º, IX e X](https://www4.planalto.gov.br/legislacao/legis-federal/constituicao)
- [Código Civil — arts. 16 a 21](https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm)
- [Lei de Direitos Autorais — art. 47](https://www.planalto.gov.br/ccivil_03/leis/l9610.htm)
- [STF — ADI 4815](https://portal.stf.jus.br/peticaoInicial/verPeticaoInicial.asp?base=ADI&numProcesso=4815)
- [LGPD — Lei 13.709/2018](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm)
