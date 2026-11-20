# Revisão geral do jogo — 19 nov. 2026

Origem: o jogador (você) disse que "nada faz sentido, está confuso". Percorri o jogo rodando (partida de prefeito em campanha, partida de presidente no mês 48 e a tela inicial) e conferi as telas e os textos. Esta página junta o que achei e o que falta, em ordem de prioridade.

## O que está bom (não mexer)
- Tela inicial, criação de partida (3 etapas) e casca visual: legíveis, com identidade.
- Motor macro (mercado, indicadores), poderes do cargo, projetos, Congresso, mapa, Gemini em produção: funcionam e têm teste.

## O que está confuso — achados concretos

### A. Números que se contradizem (campanha)
Na mesma partida de prefeito, quatro números diferentes para "quanto apoio eu tenho":
- Carreira: "Última pesquisa **32,6%**"
- Painel: "Intenção de voto **42%**"
- Painel: "Apoio local **39%**" e Carreira: "Apoio no território **39%**"
- Apoio por grupo: todos entre 42% e 46% (os seis grupos quase iguais, então não dizem nada).

Também apareciam rivais com o mesmo partido do jogador (MDB contra MDB). Isso já foi corrigido no motor (commit `9f09a99`), mas partidas salvas só mudam na próxima pesquisa.

### B. Telas que não são do cargo
- Painel de **prefeito** mostra "O país agora" (mapa do Brasil), dólar, bolsa, Selic e risco-país. O prefeito de São Paulo não decide nada disso.
- **Redes** e **Imprensa** do prefeito mostram crises nacionais ("Enchentes no Sul", "Falha em serviço digital") e "governo avalia opções de resposta".
- **Instituições** do prefeito mostra "Lealdade militar à Constituição".
- Reguladores aparece para todos os cargos.
- Regra já escrita no seu pedido: "país OU cidade, nunca tudo junto". Não está sendo cumprida nessas telas.

### C. Não diz o que fazer agora
- **Agenda** da campanha tem um único item (a eleição). Não há metas ("chegar a X% até Y", "fazer um debate", "prestar contas").
- **Imprensa** rotula como "Crise" um projeto que "aguarda sanção" e depois como "sem resposta do governo… a crise se agravou". Para quem lê, é prazo normal virando drama.
- Texto de fim de mandato (presidente, mês 48/48): "Seca pressiona a produção" com "decisão esperando resposta", sem dizer que o mandato acabou e o que vem depois.
- Cartão "Poderes do cargo" na Carreira tem um vão em branco no topo.

### D. Motor eleitoral — o que ainda falta
Entregue: rivais reais (TSE), leitura do discurso pelo Gemini com nota decidida pelo motor, tela da leitura.
Falta:
1. Ligar a leitura à campanha presidencial (`/api/campaign/action`).
2. Um só número de apoio por tela, e nomes dos rivais com força real e foco.
3. Apoio diferente por grupo (hoje quase igual).
4. Pesquisas por instituto, com margem e viés de cada um.
5. Ações dos rivais e eventos de campanha (escândalo, debate, apoio, decisão do TSE).
6. Coalizões, convenção, tempo de TV.
7. Entregar o resultado em Carreira, Apoio, Apuração, Redes e Imprensa (hoje cada tela conta uma história).

### E. Conteúdo e testes humanos
- Nenhuma jogada humana completa de ponta a ponta com a interface atual; só bots e testes automáticos.
- Textos de eventos e tom (sátira sem pessoa real) precisam de leitura sua.
- 53 imagens reais por fazer (lista em `docs/IMAGENS_RESTANTES.md`, 37 nomes exatos dos projetos).

### F. Limpeza técnica
- CSS legado (`editorial.css`, `views.css` e outros) ainda brigando com o sistema novo.
- Telas "reescrever com componentes novos" que sobraram da 0.4/0.5.
- Banco local com 72 partidas de teste (só no PC; não afeta produção).
- Gemini em produção só com `interpretar` e `mapear`; `narrar` e `perguntar` seguem desligados por decisão.
- Backend de produção na Oracle ainda sem o commit do motor eleitoral (falta deploy).

### G. Fora do jogo
- Robô da Oracle A1: ~5 mil tentativas, só "sem vaga"; cartão ainda recusado no upgrade.
- Ranking aprendido (bandit) e calibração histórica: não iniciados.
- Dados sintéticos com GPT-6 Luna: só testado em simulação; falta chave da OpenAI.

## Ordem proposta

1. **Um número por conceito + telas por cargo** (A e B). É o que mais passa a sensação de "não faz sentido". Regra: cada tela mostra só o que o cargo do jogador controla ou sofre; "país" só para presidente (e mercado, só quando a decisão mexe nele).
2. **"O que fazer agora"** (C): metas por fase na Agenda, texto de fim de mandato, Imprensa sem drama falso, cartão sem vão.
3. **Motor eleitoral completo** (D), na ordem 1 → 7.
4. **Partida de teste sua** (E), com lista de incômodos, e correções.
5. **Limpeza de CSS e telas antigas** (F).

Cada item entra com teste e captura de tela antes de seguir para o próximo.
