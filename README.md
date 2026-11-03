# Civiciclo 0.1 — simulador político

Civiciclo é o nome de trabalho do jogo fictício de política brasileira, jogado no navegador. O símbolo vetorial está em `public/assets/brand/civiciclo.svg`; a busca de disponibilidade da marca no INPI ainda não foi feita. O tempo avança por dia; decisões, campanhas, eleições, crises e projetos alteram uma simulação determinística. O projeto não representa previsões oficiais nem atribui fatos inventados a pessoas ou empresas reais.

## Estado da versão

O 0.1 reúne uma partida presidencial e uma carreira eleitoral com sete cargos, calendário diário, campanha, transição e exercício do mandato. Orçamento, indicadores, obras, diplomacia, nomeações e eventos estão conectados ao mesmo estado salvo. Cada conta Cognito pode manter várias partidas nomeadas, alternar entre elas e continuar do ponto salvo.

As regras são uma abstração de jogo, não um modelo econômico ou jurídico preditivo. Candidatos, pesquisas, contratos, empresas, falas e acontecimentos gerados são fictícios. Nomes e siglas partidárias podem vir do cadastro público do TSE; sua posição ideológica no jogo é configurada para a simulação e não descreve oficialmente o partido. Cada conta pode manter várias partidas nomeadas. A carreira ainda tem ações de mandato mais simples que o módulo presidencial; também faltam retratos próprios para o elenco, importação automática contínua do TSE, mensageria multijogador e backup externo automático.

## Jogar na web

A instalação de protótipo está em [Civiciclo](https://d2dpmk0vrt66wn.cloudfront.net). O endereço usa Cognito para cadastro e login e pode exigir confirmação de e-mail. A branch `main` é validada pelo GitHub Actions e publicada automaticamente pelo servidor após aprovação; a instância verifica atualizações a cada cinco minutos. Os arquivos e limites da infraestrutura estão em [`deploy/aws/README.md`](deploy/aws/README.md) e [`docs/AUTENTICACAO_E_DEPLOY.md`](docs/AUTENTICACAO_E_DEPLOY.md).

## Executar localmente

Requisitos: Node.js 20+ e Python 3.11+.

1. Na pasta `game`, instale e inicie o frontend:

   ```powershell
   npm install
   npm run dev
   ```

2. Em outro terminal, inicie a API:

   ```powershell
   cd backend
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   uvicorn app.main:app --reload --port 8000
   ```

O Vite encaminha `/api` para `http://localhost:8000`. Sem Cognito configurado, o modo local usa uma única partida local. O banco padrão é `data/game.sqlite3`; defina `DATABASE_PATH` para usar outro arquivo.

## Fluxo principal

1. Escolha entre seguir a posse presidencial ou iniciar uma carreira eleitoral em outro cargo.
2. Faça o pronunciamento de posse quando assumir o Executivo.
3. Leia o briefing diário e escolha uma ação; cada ação informa custo, tempo e efeitos previstos.
4. Avance um dia, uma semana ou até 30 dias. Viagens e campanhas consomem dias no calendário.
5. Acompanhe crises, obras, orçamento, apoio regional, votação e transição eleitoral. Uma derrota não encerra a carreira.

O painel inicial limita a vista a seis indicadores escolhidos. Indicadores detalhados e históricos ficam em telas separadas; grupos secundários e registros extensos abrem sob demanda.

## Interpretação de medidas com Gemini

Copie `backend/.env.example` para `backend/.env` e adicione `GEMINI_API_KEY`. A chave fica apenas no backend. `GEMINI_MODEL` pode selecionar o modelo. Sem chave, a interpretação local oferece uma leitura básica. Se o provedor falhar, a API usa o fallback; exceções inesperadas retornam erro controlado.

O Gemini sugere intenção, categoria e outros campos para a prévia; o jogo registra cada leitura no SQLite por jogador e permite corrigir categoria e instrumento. A aba **Aprendizado** avalia os rótulos e grava candidatos separados por jogador; o mesmo processo pode ser executado com `python -m app.ai.trainer` em `backend`. Os candidatos ainda não são usados nas partidas e as saídas sem revisão não viram rótulos de treino. Somente o motor Python valida ações e calcula efeitos. Valores fiscais são extraídos no servidor a partir do texto original, nunca aceitos da resposta da IA ou do navegador; quando não há valor explícito, a prévia avisa que R$ 0 no cálculo não confirma neutralidade fiscal. Veja a [fronteira IA/motor e a validação cruzada](docs/VALIDACAO_CRUZADA_PROPOSTAS.md).

## Testes e build

Na pasta `game/backend`:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Na pasta `game`:

```powershell
npm run build
```

Os testes de API usam banco temporário e cobrem inicialização, fala de posse, progressão diária, início de carreira, telas centrais, falha do interpretador e isolamento de saves.

## Mapa do código

- `src/`: React/JSX, telas de decisão, campanha, orçamento, diplomacia, carreira e indicadores.
- `backend/app/engine/`: estado, calendários, regras, eventos, finanças, carreira, obras e instituições.
- `backend/app/ai/`: interpretação via Gemini e recuperação lexical local.
- `backend/app/db.py`: saves por jogador, arquivos, histórico e correções.
- `backend/app/data/`: importação seletiva do catálogo público do TSE e ingestão de fontes documentais.
- `backend/app/bot/`: agente de referência e treinamento tabular sintético, sem chamadas de IA.
- `docs/`: regras, fontes, comparativo e plano de evolução.

Para treinar a política de referência, execute em `game/backend`: `python -m app.bot.trainer --episodes 3000`. Para importar candidaturas disponíveis no Portal de Dados Abertos do TSE, execute: `python -m app.data.tse_import --years 2022 2024 2026`. A importação é manual e os registros guardam fonte/licença. A consulta local usa `GET /api/data/tse/candidates?year=2024&state_code=SP&office=VEREADOR&search=nome`.

As mecânicas de irregularidade eleitoral e ruptura institucional são abstratas, restritas ao cenário fictício e resolvidas pelo motor; não fornecem instruções aplicáveis fora do jogo.
