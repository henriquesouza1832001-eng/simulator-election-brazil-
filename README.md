# Mandato — simulador de governo

Protótipo local de um jogo de governo no navegador. React/JSX cuida da interface; FastAPI e Python guardam o estado, calendário, regras e memória de correções. As medidas são fictícias.

## Rodar localmente

Requisitos: Node.js 20+ e Python 3.11+.

1. Instale o front-end: `npm install`
2. Inicie a API em outro terminal:

   ```powershell
   cd backend
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   uvicorn app.main:app --reload --port 8000
   ```

3. Em `game/`, rode `npm run dev` e abra o endereço mostrado pelo Vite.

O jogo começa em 1º de janeiro de 2027. O salvamento e as correções ficam em `game/data/game.sqlite3`.

## Gemini

Copie `backend/.env.example` para `backend/.env` e preencha `GEMINI_API_KEY` e, se quiser, `GEMINI_MODEL`. A API carrega esse arquivo ao iniciar.

```powershell
Copy-Item backend/.env.example backend/.env
# Depois edite backend/.env e insira a chave criada no Google AI Studio.
```

Sem chave, a API usa um interpretador local simples. A chave nunca vai para o navegador. A disponibilidade e o custo do modelo dependem do projeto e do crédito Google ligado à conta.

## Arquitetura inicial

- `src/`: interface JSX responsiva e prévia de medida.
- `backend/app/engine/`: estado, calendário e cálculo determinístico dos efeitos.
- `backend/app/ai/`: extração estruturada da intenção via Gemini, com fallback local.
- `backend/app/db.py`: estado persistido e memória SQLite de correções.
- `backend/app/bot/agent.py`: política de decisão inicial e função de recompensa transparente.
- `backend/app/bot/trainer.py`: treinamento tabular opcional com episódios sintéticos, sem chamadas de IA.
- `backend/app/data/tse_import.py`: importador seletivo de candidaturas do Portal de Dados Abertos do TSE, guardando fonte e licença por ano.
- `backend/app/ai/rag.py`: indexação e recuperação local de trechos com fonte, data e licença para eventos fundamentados.
- `backend/app/engine/career.py`, `difficulty.py`, `tax_policy.py`: esqueleto para progressão de carreira, perfis de dificuldade e alavancas tributárias.
- `docs/PROJETO_DO_JOGO.md`: carreira, dificuldades, dados, retratos, eventos, impostos e etapas planejadas.

O modelo de linguagem interpreta o texto e identifica parâmetros; não escolhe os efeitos numéricos. Esses efeitos ficam em `engine/rules.py`, para a simulação ser reproduzível. Correções do jogador entram como exemplos para interpretações futuras. O agente Python não chama IA durante episódios de treino; primeiro aprende com estados e ações gerados pelo próprio motor.

## Próximos passos

1. Cobrir as ações centrais com regras e custos explícitos.
2. Implementar eventos noticiosos, grupos sociais e aprovação por segmento.
3. Adicionar exportação/importação de campanha e tela de histórico.
4. Gerar episódios sintéticos e comparar políticas do agente com cenários de referência.
5. Preparar deploy da API no Oracle Cloud e hospedar o front-end como estático.

Para treinar a política de referência, estando em `game/backend/`: `python -m app.bot.trainer --episodes 3000`. O arquivo de política sai em `game/data/policy.json` e pode ser usado pelo endpoint de recomendação.

Para carregar perfis eleitorais minimizados, estando em `game/backend/`: `python -m app.data.tse_import --years 2022 2024 2026`. O comando busca apenas os CSVs principais de candidaturas; votos, contas, fotos e propostas serão importadores separados. A licença é lida do catálogo de cada ano e armazenada com os registros.

A API de consulta do catálogo carregado é `GET /api/data/tse/candidates?year=2024&state_code=SP&office=VEREADOR&search=nome`.

Para indexar uma fonte oficial já revisada como texto, use `python -m app.data.ingest_source --title "Título" --url "https://..." --kind legislacao --license "CC BY" --file .\fonte.txt`. O RAG inicial usa recuperação lexical leve no SQLite; depois pode ser trocado por busca vetorial no Oracle sem misturar essa camada às regras do jogo.

## Deploy inicial com Docker

O projeto inclui `compose.yaml`, uma imagem FastAPI e Nginx para servir o JSX e encaminhar `/api` à API. Na VM Oracle, instale Docker Engine e Docker Compose, copie o projeto e crie `backend/.env`; depois rode `docker compose up -d --build`. Libere a porta TCP 80 na lista de segurança da VCN e no firewall da VM. O SQLite fica em volume persistente. Para HTTPS e domínio, coloque Caddy ou Nginx TLS à frente antes de abrir o serviço ao público.
