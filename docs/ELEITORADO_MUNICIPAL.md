# Eleitorado municipal

O catálogo municipal combina códigos e nomes do IBGE, estimativas de população do IBGE e a contagem de eleitores aptos do TSE para 2026. A camada TSE usa o recurso **Eleitorado por local de votação**, publicado pela Assessoria de Gestão Eleitoral, sob licença Creative Commons Attribution (CC BY).

## Importação

Baixe o ZIP oficial do TSE e rode o importador a partir de `backend`:

```powershell
Invoke-WebRequest `
  -Uri 'https://cdn.tse.jus.br/estatistica/sead/odsele/eleitorado_locais_votacao/eleitorado_local_votacao_2026.zip' `
  -OutFile "$env:TEMP\eleitorado_local_votacao_2026.zip"
python -m app.data.electorate_import --zip "$env:TEMP\eleitorado_local_votacao_2026.zip"
```

O importador lê somente os arquivos estaduais, ignora o arquivo nacional redundante e a seção internacional, filtra o primeiro turno e seções ativas e soma `QT_ELEITOR_SECAO`. O cruzamento exige uma correspondência única entre UF e município do TSE e o código IBGE; aliases documentados cobrem grafias eleitorais antigas ou abreviadas. A rotina falha se faltar uma UF, município ou se o total nacional ficar fora de uma faixa ampla de integridade.

Fonte e licença: [conjunto Eleitorado - 2026 do TSE](https://dadosabertos.tse.jus.br/dataset/eleitorado-2026). Os dados são agregados por seção, não contêm registros individuais e não são baixados durante uma partida.

## Regra de campanha

O porte municipal continua baseado na população residente. O alcance eleitoral local usa eleitores aptos do TSE:

| Eleitorado municipal | Multiplicador simulado |
| ---: | ---: |
| Até 35 mil | 1,15× |
| 35.001 a 140 mil | 1,00× |
| 140.001 a 700 mil | 0,85× |
| Acima de 700 mil | 0,70× |

Essas faixas são regras explícitas de equilíbrio do jogo, não estimativas oficiais de impacto eleitoral. Se o catálogo ainda não tiver eleitorado, o motor mantém as faixas de alcance anteriores, baseadas na população.
