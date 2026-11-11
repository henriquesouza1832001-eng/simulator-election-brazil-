# Partidos, Congresso e ideologia

## Dados reais
- **Composição do Congresso:** 513 deputados e 81 senadores em exercício, com nome parlamentar, partido e UF, obtidos das APIs de dados abertos da Câmara dos Deputados e do Senado Federal (`python -m app.data.parliament`, saída em `backend/data/parliament.json`, com data de coleta e fontes). E-mails e contatos não são copiados.
- **Partidos:** siglas e nomes do cadastro do TSE (`app/data/parties.json`). Candidaturas oficiais 2014–2026 vêm do importador do TSE.

## O que é simulação
- O **voto de cada parlamentar** é simulado por regras e semente da partida. Não representa nem prevê o voto de pessoas reais.
- Os atributos internos (disciplina, fisiologismo, imprevisibilidade, bancadas) são sorteados pelo jogo.
- **Adversários e colegas de lista** nas eleições simuladas usam partidos reais, mas as candidaturas são genéricas ("Candidato(a) simulado(a) do PL"); não há pessoas inventadas com nome.
- 2028 e 2030 não têm registro oficial: o elenco continua rotulado como cenário simulado.

## Posição ideológica (escolha editorial, de −1 esquerda a +1 direita)
| Posição | Partidos |
| --- | --- |
| Extrema-esquerda (≈ −0,95) | PSOL |
| Esquerda (−0,85 a −0,6) | PCdoB, PT, REDE |
| Centro-esquerda (−0,5 a −0,45) | PSB, PV, PDT |
| Centro (−0,1 a +0,15) | CIDADANIA, PSDB, SOLIDARIEDADE, MDB, PSD, AVANTE, PODE |
| Centro-direita (+0,4 a +0,55) | UNIÃO, PRD, PP |
| Direita (+0,6 a +0,85) | REPUBLICANOS, PL, NOVO, MISSÃO |

A classificação segue o consenso aproximado da literatura (pesquisas de survey com parlamentares e análises de votação), mas partidos mudam; é uma simplificação revisável em `PARTY_PROFILE` (`engine/legislature.py`). A adesão inicial ao governo é um parâmetro de design.

## Limites conhecidos
- O roster é a legislatura atual na data da coleta; trocas de partido e suplentes exigem nova importação.
- Partidos sem representação no Congresso (PSTU, PCB, UP etc.) existem no cadastro do TSE, mas não têm cadeiras na simulação do plenário.
