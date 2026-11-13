# Eleições, cenários e Modo Eleitor

Data desta revisão: 9 nov. 2026.

## O que existe agora

- **Calendário de cenários:** 2014, 2016, 2018, 2020, 2022, 2024, 2026, 2028 e 2030, com tipo (geral ou municipal), datas de 1º e 2º turno e regras por ano. Código: [`backend/app/engine/election_rules.py`](../backend/app/engine/election_rules.py).
- **Validação de cargo e território:** o cargo precisa existir no tipo de eleição do ano; UF válida para cargos estaduais e federais; município validado pelo **código IBGE** (catálogo do projeto) para prefeito e vereador, e conferido contra a UF.
- **Importação oficial de candidaturas do TSE** com proveniência: [`backend/app/data/tse_candidacies.py`](../backend/app/data/tse_candidacies.py).
- **Modo Eleitor** (tela inicial → terceiro cartão): escolher o pleito, cargo e território, ver os candidatos oficiais com fonte e dar um **voto simulado**. Código: [`engine/elector.py`](../backend/app/engine/elector.py), [`scenario_routes.py`](../backend/app/scenario_routes.py), [`src/ElectorPanel.jsx`](../src/ElectorPanel.jsx).
- O aviso **"Voto simulado: não é enviado à Justiça Eleitoral e não altera uma eleição real."** aparece na urna, no resultado e na resposta da API.
- O visitante usa tudo **sem conta**. A trava de pronunciamento de posse não se aplica a `/api/elector/*` e `/api/scenarios*`.

## Fonte dos dados

| Item | Valor |
| --- | --- |
| Catálogo | Portal de Dados Abertos do TSE (CKAN), conjuntos `candidatos-AAAA` (2020 usa `candidatos-2020-subtemas`) |
| Recurso usado | Somente o recurso chamado **"Candidatos"** (`consulta_cand_AAAA.zip`, arquivo `consulta_cand_AAAA_BRASIL.csv`) |
| Licença registrada | Creative Commons Attribution (conforme o catálogo no momento da coleta; conferir por ano antes de publicar) |
| Campos guardados | ano, turno, cargo, UF, município (nome e código do TSE), número, nome, nome de urna, partido, situação da candidatura, situação de totalização, URL da fonte, licença, arquivo, **SHA-256 do ZIP**, data de geração do arquivo e data da coleta |
| Campos **não** guardados | CPF, e-mail, endereço, data de nascimento, bens, redes sociais |

Resultado da importação (tabela `tse_candidacies`, 9 nov. 2026; linhas lidas = mantidas, 0 descartadas):

| Ano | Linhas lidas | Registros únicos |
| --- | ---: | ---: |
| 2014 | 26.263 | 26.195 |
| 2016 | 498.391 | 498.163 |
| 2018 | 29.287 | 29.227 |
| 2020 | 558.804 | 558.572 |
| 2022 | 29.322 | 29.270 |
| 2024 | 463.932 | 463.728 |
| 2026 | 21.017 | 20.989 |

Para reproduzir: `cd backend && python -m app.data.tse_candidacies --years 2014 2016 2018 2020 2022 2024 2026`. Cada execução registra uma linha em `tse_import_runs` com checksum.

### Defeito encontrado no importador antigo

O importador antigo (`app/data/tse_import.py`) selecionava **todo** recurso cujo nome contivesse "candidato", incluindo "Bens de candidatos" e "Redes sociais de candidatos", e usava `ON CONFLICT DO UPDATE`. As linhas vazias desses recursos **sobrescreveram** as completas: na tabela antiga `tse_candidates`, 78% dos registros de 2024 e 93% dos de 2026 ficaram sem nome, partido e cargo. A tabela antiga **não foi apagada nem usada** pelo fluxo novo. Os endpoints antigos (`/api/data/tse/*`) ainda leem a tabela antiga e devem ser migrados ou descontinuados.

## Conferência dos dados (o que foi e o que não foi validado)

Conferido por amostragem, em 9 nov. 2026:

- Presidência: 2014 (12 candidaturas), 2018 (14), 2022 (13) e 2026 (14, uma delas com marcador `#NULO`). O cargo eleito em 2014, 2018 e 2022 aparece como `ELEITO`; em 2026 só uma candidatura consta como `2º TURNO`.
- Prefeitura de São Paulo em 2024: 10 candidaturas, uma `ELEITO`.

**Ainda pendente:** conferência detalhada contra os relatórios oficiais do TSE por cargo/UF. Há indício de contagem inflada de `ELEITO` para prefeitos (2016: 5.649 `ELEITO` contra 5.570 municípios), provavelmente por substituições ou renovação de eleição; precisa ser investigado antes de publicar números agregados. **Votos por candidato não foram importados**: o comparativo do Modo Eleitor usa apenas a situação de totalização do cadastro (`ELEITO`, `NÃO ELEITO`, `2º TURNO`) e avisa isso na tela. Para 2026, o cadastro só diz quem foi ao 2º turno; o vencedor final exige o conjunto de resultados/votação do TSE.

## 2028 e 2030

Não existem candidaturas oficiais. O jogo gera elencos **fictícios**, determinísticos por ano/cargo/território, com nomes inventados e siglas de partidos fictícios, e marca tudo como "Cenário futuro simulado". Nenhum nome de pessoa real aparece. A importação oficial desses anos segue o mesmo comando quando o TSE publicar os registros, sem mudar o motor.

## Regras por ano (`ElectionRuleset`)

Entram apenas regras com base normativa citada na própria estrutura (Constituição Federal, Lei nº 9.504/1997, EC nº 16/1997, EC nº 97/2017, EC nº 107/2020, EC nº 111/2021, Lei nº 13.487/2017, Lei nº 14.208/2021, ADI 4650/STF):

- datas de 1º e 2º turno (2020 adiada pela EC 107/2020; 2028 e 2030 **calculadas** pela regra constitucional e marcadas como derivadas);
- duração de mandato por cargo (senador, 8 anos) e renovação alternada do Senado (2/3 em 2018 e 2026; 1/3 em 2014, 2022 e 2030);
- idade mínima por cargo, critério de 2º turno, reeleição, coligações proporcionais (vedadas a partir de 2020), federações (a partir de 2022), doação de empresas (vedada a partir de 2016), fundo público de campanha (a partir de 2018) e data de posse (EC 111/2021, a partir de 2027).

**Pendente e exposto na tela, sem uso como fato:** prazos de filiação e domicílio por ciclo, limites de gastos e prestação de contas, datas de convenção/registro/propaganda por ciclo e cálculo de vagas/sobras do proporcional. O jogo ainda inicia a partida de posse em 1º de janeiro de 2027; a EC 111/2021 prevê 5 de janeiro de 2027 para a Presidência — ajuste pendente no motor.

## Limitações abertas desta fatia

1. **Campanha/Carreira por ano:** a carreira e a posse direta continuam no calendário de 2027 em diante. Escolher um ano do passado para jogar como candidato ainda não existe; os anos 2014–2024 estão disponíveis no Modo Eleitor.
2. Votos por candidato e resultados agregados oficiais não importados.
3. Fotos oficiais do TSE e caricaturas por candidatura: não ligadas à tela; ver [Personagem e retratos](PERSONAGEM_E_RETRATOS.md).
4. Endpoints e tabela antiga do TSE a migrar.
5. Multiplayer: apenas documentado (ver [Multiplayer](MULTIPLAYER_ARQUITETURA.md)).


## Votos por candidato (12 nov. 2026)

`python -m app.data.tse_votes --years 2016 2020 2024` importa o recurso "Votação nominal por município e zona" do TSE (licença Creative Commons Attribution, SHA-256 e data de coleta registrados em `tse_import_runs`). Guarda votos nominais por candidato e município (prefeito, vereador, presidente, governador e senador) ou por candidato e UF (deputados). Anos gerais (2014, 2018, 2022) têm arquivos de 400 a 600 MB: rode no servidor.

- API: `GET /api/elector/results?year=&office=&uf=&municipality_id=` (votos, participação sobre os votos nominais e situação, por turno). Aparece no Modo Eleitor.
- Conferência: São Paulo 2024, prefeito: Ricardo Nunes 1.801.139 (29,49%) no 1º turno e 59,35% no 2º; vereador mais votado, Lucas Pavanato, 161.386 votos.
- A carreira mostra uma "referência real": para vereador, quantos votos teve o último eleito no município na eleição anterior; para prefeito, quanto teve o vencedor. A simulação não usa esses números para decidir o resultado.
- Votos em branco e nulos não entram. Sem a importação, as telas explicam como importar e o jogo segue sem a referência.
- Produção: o banco de produção precisa rodar os dois importadores (`tse_candidacies` e `tse_votes`); o banco local não vai para o repositório.
