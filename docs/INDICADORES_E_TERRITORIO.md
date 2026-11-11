# Indicadores, território e obras

## Dados reais
- **Atlas do Desenvolvimento Humano (Censo 2010)**, via Ipeadata: 35 séries municipais (IDHM e dimensões, Gini, Theil, pobreza, extrema pobreza, esperança de vida, mortalidade infantil, analfabetismo, frequência escolar, água, esgoto, lixo, energia, formalização, estrutura do emprego, renda, desocupação). Importador: `python -m app.data.atlas_import` -> `backend/data/atlas_municipal.json`.
- **IBGE:** população, PIB e setores (`data/municipalities.json`).
- É a base municipal mais recente com esse conjunto; o Censo 2022 ainda não tem todas essas séries por município. As séries são de 2010, e o jogo mostra isso.

## O que é estimativa do jogo
Mobilidade, segurança, atenção básica de saúde, conectividade e o índice de saneamento (combinação de água, esgoto e lixo). Cada linha mostra a fonte (Atlas, IBGE ou estimativa).
As médias por estado e região são ponderadas pela população municipal; o Gini nacional aparece menor que o oficial (0,53 contra ≈0,60) porque é a média dos Ginis municipais, que não captam a desigualdade entre municípios.

## Registro de indicadores (`engine/indicator_registry.py`)
Cada um dos ~65 indicadores declara domínio, escopo (país, região, UF, município), fonte, sentido (mais é melhor?), o que o influencia (`drivers`, com sinal e força) e quais cargos agem sobre ele e como (`levers`). `propagate()` espalha uma mudança pelos dependentes (efeitos de segunda ordem). Os pesos são escolhas de design.
API: `GET /api/indicators/registry?domain=&office=`, `GET /api/indicators/office/{cargo}`.

## Território e obras (`engine/territory.py`)
- `GET /api/territory` (país, regiões e 27 estados), `/api/territory/search`, `/api/territory/city/{ibge}` (36 indicadores por município).
- Projetos de transporte e urbanismo (Rodoanel de BH e de SP, Metrô, BRT, VLT, trem intercidades, tarifa zero, saneamento, habitação, segurança, polo industrial): custo pelo índice de preços, prazo em meses e competência por cargo. Ao concluir, mudam os indicadores do município ou do estado e, em menor grau, os indicadores ligados.
- Interface: aba Território (estados e regiões, cidades, obras, mapa de influências).

## Limites
Custos, prazos e efeitos são parâmetros de design; os valores reais de obras variam muito. Séries de 2010 não evoluem sozinhas ao longo da partida, só pelas ações do jogador. Faltam séries anuais (RAIS/Caged, Sinan, SIM, Siconfi) por município, a fazer em importadores próprios.
