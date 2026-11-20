# Validação automática do jogo (motor, interface e balanceamento)

Um conjunto de verificações que roda sem ninguém jogando e responde a uma pergunta: **o jogo funciona e faz sentido jogar?** Os resultados abaixo são de 20/11/2026.

## O que existe e como rodar
| Verificação | Comando | O que mede |
|---|---|---|
| Testes do motor | `cd backend && .venv/Scripts/python.exe -m unittest discover -s tests` | 418 testes: regras, API, coerência de números, causas de variação, alavancas, coligações, STF, blocos |
| Invariantes do motor | `tests/test_invariantes_motor.py` | 10 partidas aleatórias de 24 meses (5 dificuldades): nenhum indicador vira NaN ou sai da faixa; estado serializável e menor que 3 MB |
| Balanceamento por bots | `scripts/bots_balanceamento.py --partidas 20 --dificuldade normal` | Fim do mandato por estratégia; trava em `test_balanceamento_dificuldade.py` |
| Cenário "100 dias" alcançável | `tests/test_cenario_100_alcancavel.py` | Quem governa cumpre 3 ou mais das 5 metas; quem não joga, até 2 |
| Rastreador de telas | `node tools/ui-crawler.mjs <partida> <rótulo> <rotas> [saida.json]` | Todas as telas em desktop e celular: erro de console, rede 4xx/5xx, texto quebrado (`undefined`, `NaN`), tela vazia ou presa em "Carregando", rolagem lateral, botão sem nome, imagem quebrada, tempo de renderização |
| Fluxo "100 dias" | `node tools/ui-flow-100dias.mjs` | Da tela inicial ao balanço pela interface real: criar partida, posse, avançar, mesa, alavanca fiscal com confirmação, mercado, balanço |
| Fluxo de campanha | `node tools/ui-flow-campanha.mjs <partida em campanha>` | Discurso lido, intenção de voto, coligação, avanço até a apuração |
| Contraste | `CAMPAIGN_ID=<partida> node tools/contrast-audit.mjs "Visão geral" "Orçamento" …` | Contraste WCAG AA por tela |

Os scripts de interface precisam de Chrome com `--remote-debugging-port=9222`, do front em `localhost:5179` e do backend em `8000`.

## Resultados (20/11/2026)
**Rastreador, 6 partidas em fases diferentes** (governo no mês 12, no mês 48, cenário 100 dias, prefeito em campanha, prefeito no mandato, presidente e governador em campanha): 66 + 38 + 46 + 46 + 46 + 46 + 24 telas medidas, nenhuma lenta (acima de 2,5 s). Achados e correções:
- Chave duplicada na Imprensa quando notícias chegam fora de ordem de data (movimentos de rivais e pesquisas): ordenação por data e chaves únicas.
- Botões "Narrar" ocultos contavam como botão sem nome (falso positivo do medidor); medidor corrigido para olhar só o que está visível.
- Resultado final: **0 problemas** nas telas medidas, em desktop e celular (390×844).

**Fluxos de interface:** 17 de 17 passos no cenário "100 dias" e 12 de 12 na campanha, sem erro de console e sem resposta 4xx/5xx. Achados e correções: a resposta do convite de coligação não aparecia em lugar nenhum (agora aparece na própria tela, com registro); o painel de Congresso e o Mercado só eram medidos pelo título em maiúsculas (ajuste do medidor).

**Contraste:** 0 grupos abaixo do mínimo nas telas auditadas (governo e campanha), depois de atualizar a ferramenta para os endereços novos por tela.

**Balanceamento com bots** (5 a 20 partidas por estratégia): a dificuldade antes não mudava o resultado e quem jogava bem terminava com 70 a 80% de aprovação. Depois do ajuste, quem governa bem termina com 67 (tranquilo), 64 (normal), 61 (difícil) e 58 (complicado); quem não joga, com 48, 42, 37 e 31.

**Cenário "100 dias":** a meta "aprovar um projeto de lei" era impossível (a votação leva mais de 100 dias) e a de inflação não dependia do jogador. Trocadas por "enviar um projeto" e "melhorar o resultado primário em 0,1 ponto" (alavanca fiscal). Resultado com bots: quem governa bem cumpre em média 3,5 de 5 metas; quem não joga, 1,2.

## O que isto não prova
- Que o jogo é divertido: só uma pessoa jogando diz isso (ver `docs/ROTEIRO_PLAYTEST.md`).
- Que o texto é engraçado ou claro: o rastreador vê texto quebrado, não graça.
- Celular real: o rastreador usa um viewport de 390×844, não um aparelho com toque e teclado virtual.
- Desempenho sob muitos jogadores: só um jogador por vez foi medido.
