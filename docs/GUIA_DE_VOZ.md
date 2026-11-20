# Guia de voz de Quatro Anos

A sátira é o que separa o jogo de um relatório. Este guia diz como o jogo fala. O código está em `backend/app/engine/voice.py`; qualquer texto novo de notícia, crise ou rede social deve seguir estas regras.

## 1. O que é a voz
Um jornal brasileiro de política escrito por quem já viu muita coisa: seco, irônico, observador. Ri do sistema e dos hábitos políticos (promessa, emenda, comissão, nota de repúdio), nunca de pessoas, minorias ou tragédias.

## 2. Regras fixas
1. **Número é do motor.** Todo valor aparece inteiro e igual ao do jogo (dólar −1,2%, bolsa +6,2%). O humor fica na frase ao redor.
2. **Zero "simulação" na narrativa.** A palavra "simulação", "simulada" ou "fictício" não aparece dentro da notícia. O aviso de ficção fica no rodapé, na tela inicial e no aviso de paródia do Congresso.
3. **Variantes, não repetição.** Cada tipo de notícia tem 3 ou mais frases e a escolha é estável pela semente da partida (`voice.pick`). A mesma partida conta sempre a mesma história.
4. **Frase curta.** Uma ideia por frase. Piada em, no máximo, uma oração; o resto é informação.
5. **Tom pelo peso do fato.** Mercado em pânico e crise grave pedem ironia seca, não graça. Gafe, boato e rotina pedem mais leveza.
6. **Veículos e perfis inventados.** Jornal da Manhã, Rádio Notícia, Faria Lima, Tia do Zap: arquétipos, não marcas ou pessoas reais.
7. **Pessoas reais só como elenco do plenário**, com o aviso de paródia visível; nenhuma fala, ato ou escândalo é atribuído a elas como fato.

## 3. Exemplos
| Em vez de | Escreva |
|---|---|
| Reação simulada do mercado financeiro. | Os operadores comentam o dia; nenhum previu, todos explicam. |
| Mercado em movimento: dólar −1,2%, bolsa +6,2% … | A Faria Lima acordou otimista: dólar −3,4%, bolsa +6,2%, risco-país −40 pontos no período. |
| O PSB anuncia oposição à medida, na simulação. | A bancada do PSB sobe à tribuna contra a medida; o plenário esvazia, mas a ata registra. |
| O prazo passou e a crise se agravou, na simulação. | O prazo passou, ninguém respondeu e a crise tomou a vaga do governo na pauta. |

## 4. O que já usa a voz
Notícias de mercado (`macro.py`), reações de imprensa e bancadas (`consequences.py`) e rotina das redes (`social_feed.py`).

## 5. O que falta reescrever (por ordem de frequência)
1. Eventos de crise e acontecimentos (`event_templates.py`, `data/events/`).
2. Entrevistas e perguntas de repórter (`interviews.py`, `ai/question_ai.py`).
3. Textos de campanha e debate (`campaign_debate.py`, `career_action.py`).
4. Rodapés dos painéis ("Eventos e projeções são ficção…" fica; as demais frases explicativas ficam, mas sem a palavra "simulado" na narrativa).

Critério de pronto para cada lote: nenhuma ocorrência de "simula" nas strings narrativas e uma revisão de leitura em voz alta (a piada precisa funcionar sem explicar).
