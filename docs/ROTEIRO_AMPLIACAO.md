# Roteiro de ampliação do Civiciclo

Objetivo: um jogo **autoral**, bem mais completo, que sustente uma campanha longa (como a descrita em `plano-transicao-governo.md` e `campanha-modo-facil.md`) com ritmo de decisões mensais, acontecimentos, Congresso nominal e consequências.

## Fontes e regras de uso

| Fonte | Como usamos |
| --- | --- |
| **PLANALTO** (observado em sessão do usuário, via REA, só leitura) | Mecânicas e experiência: campanha semanal, Congresso, ranking, coleção. Ver `extrato/MAPA_TELAS.md`. Não copiamos textos, arte nem código. |
| **dominio-politico** (repositório público **sem licença**) | Estudo de conceitos; **reescrevemos** em Python com conteúdo próprio. Sem licença não copiamos código. Se o autor publicar uma licença permissiva, reavaliar. Clone de estudo fora do projeto: `C:\projetos\referencias\dominio-politico`. |
| **Civiciclo atual** | Base: motor Python determinístico, FastAPI, React, Gemini opcional. |
| **Ideias do autor deste projeto** | Prioridade máxima. Ver seção "Suas ideias" abaixo. |

Regra de conteúdo (adotada do que há de melhor nas duas referências): **o motor decide, o texto narra.** Pessoas reais nunca recebem crimes, falas, saúde nem atitudes inventadas; eventos negativos só com personagens fictícios. Tudo simulado é marcado como tal.

## Pilares do jogo autoral

1. **Governo mês a mês**: medidas em linguagem natural → instrumento → custo → votação nominal → consequências (existe; ampliar).
2. **Acontecimentos**: decisões com prazo, oportunidades e informativos, com ritmo e histórias encadeadas (iniciado em `engine/story.py`).
3. **Congresso vivo**: parlamentares com eixos, disciplina, relação, frentes, compromissos (iniciado em `engine/legislature.py`).
4. **Campanha**: semanal, com energia, caixa, debate e apoios (iniciado em `engine/campaign_week.py`).
5. **Meta-jogo**: placar, coleção, histórico (iniciado em `engine/meta.py`).
6. **IA assistente (Gemini) + ML local**: o Gemini narra e interpreta texto; o ML local classifica e aprende com correções; o motor continua dono dos números.

## Backlog priorizado

Legenda de origem: **P** = observado no Planalto · **D** = conceito do dominio-politico · **A** = autoral/seu · Estado: ✅ feito · 🟡 parcial · ⬜ pendente

### Núcleo de governo
| Item | Origem | Estado |
| --- | --- | --- |
| Congresso nominal 513 + 81, eixos, disciplina, relação | P + D | ✅ |
| Compromissos de campanha e penalidade de relação | P | ✅ |
| Acontecimentos (decisão/oportunidade/info, prazo, padrão, encadeamento) | D | ✅ (14 eventos) |
| Mais acontecimentos (meta: 60+), por área e fase do mandato | A | ⬜ |
| Fechamento mensal com extrato (receitas, gastos, juros, dívida) | D | ⬜ |
| Emendas, comissões, CPIs completas com investigação em etapas | P + D | ⬜ |
| Ministérios com titulares, partido e cobrança | P | 🟡 (existe nomeação) |
| Política monetária (Selic/regra tipo Taylor) e choques externos | D | ⬜ |
| Crises encadeadas e memória de crises | P + D | 🟡 |
| Impeachment/pressão e sucessão | P | 🟡 |

### Campanha e eleição
| Item | Origem | Estado |
| --- | --- | --- |
| Campanha semanal, 17 ações, viagem, energia | P | ✅ |
| Debate (participar/recusar/casa) | P | ✅ |
| Apoios de governadores e senadores com prazo | P | ⬜ |
| Mapa por 27 estados, margem e indecisos | P | ⬜ |
| Pesquisas com margem de erro e efeito de instituto | D | ⬜ |
| Apuração com 2º turno; proporcionais D'Hondt (modo carreira) | D | ⬜ |
| Calendário cívico semanal | P | ⬜ |

### Carreira e mundo
| Item | Origem | Estado |
| --- | --- | --- |
| Carreira em etapas (cidadão → … → mandato) | D | 🟡 (existe carreira por cargo) |
| Regras por época (filiação, fundo, coligações) | D | ⬜ |
| Partido próprio (fundação, apoiamento, registro) | D | ⬜ |
| Finanças pessoais e mensais | D | ⬜ |
| Mundo determinístico e relógio | D | ✅ (semente) |

### IA e ML
| Item | Origem | Estado |
| --- | --- | --- |
| Interpretação de medidas (Gemini + local) | existente | ✅ |
| Narrador de acontecimentos (Gemini opcional, fallback local) | A | ⬜ próximo |
| Avaliação de falas em debate com Gemini (nota + leitura) | P | ⬜ |
| Réplica do rival gerada por IA com custo/tokens registrados | P | ⬜ |
| ML local: classificar medidas e prever aprovação com histórico do jogador | A | 🟡 (trainer existe) |

### Meta-jogo e plataforma
| Item | Origem | Estado |
| --- | --- | --- |
| Placar S–F, coleção, diário | P | ✅ |
| Conquistas ligadas a eventos e ao Congresso | P + D | 🟡 |
| Resumo do período (antes/depois, manchetes) | D | ⬜ |
| Glossário com dicas nos termos | D | ⬜ |
| Exportação de dados e exclusão (LGPD) | D | ⬜ |

## Suas ideias (preencha aqui)

> Escreva abaixo o que você quer de diferente, a identidade do jogo, mecânicas favoritas da sua campanha, regras que mudaria. Esta seção tem prioridade sobre todo o resto.

- [ ] …
- [ ] …
