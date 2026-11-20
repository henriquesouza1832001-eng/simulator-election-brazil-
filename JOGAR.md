# Como jogar agora

1. Dê dois cliques em `JOGAR.bat` (na pasta `game`). Ele sobe o motor (porta 8000) e a tela (porta 5179) e abre o navegador em `http://localhost:5179/`.
2. Na primeira vez, a lista de **Partidas salvas** vem vazia: o jogo usa uma lista própria (`LOCAL_PLAYER_ID=jogador`), sem as partidas de teste do desenvolvimento.
3. Para começar rápido, escolha **Os primeiros 100 dias → Jogar agora** (15 minutos). Para o mandato completo, **Tomar posse no primeiro dia**.
4. Anote o que incomodar na tabela de `docs/ROTEIRO_PLAYTEST.md`.
5. Para encerrar, feche as duas janelas minimizadas "Quatro Anos".

**Se algo não abrir:** confirme que existem `backend\.venv` e `node_modules` (rode `npm install` uma vez na pasta `game` e, em `backend`, `python -m venv .venv` seguido de `.venv\Scripts\pip install -r requirements.txt`).

**Gemini:** com a chave em `backend\.env`, a leitura de discursos e a interpretação de medidas usam o Gemini; sem a chave, o jogo usa a leitura local e continua jogável.

**Voltar a ver as partidas de desenvolvimento:** inicie sem `LOCAL_PLAYER_ID` (por exemplo, rodando os comandos à mão).
