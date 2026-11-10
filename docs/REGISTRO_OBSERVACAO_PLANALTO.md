# Registro de observação do PLANALTO (planalto.fun)

Data: 9 nov. 2026. Somente áreas públicas, sem conta, sem compra e sem automação de jogo.

## Confirmado e observado

| Item | Evidência |
| --- | --- |
| Menu: O jogo, Ranking, Coleção, Diário, Legado; botões Entrar/Criar conta | Leitura da home |
| Dois modos de início: Disputar a eleição (13 semanas) e Tomar posse (jan. 2027); mandato de 48 meses | Leitura da home |
| 513 deputados, 27 governadores, 32 grupos sociais | Texto da home |
| Planos Livre / Pro (R$ 19,99 por 30 dias) / Estadista (R$ 49,99 por 30 dias) | Home e `/versoes` |
| Placar da História: filtros Todos os tempos, Semana, Aprovação, Economia, Campanhas, Coleção, Dinastias; notas S–F; Brutal vale 13% a mais; sem Fácil | Home e `/ranking` |
| Nota por 7 blocos (país, popularidade, governar, mundo, integridade, promessas, preço) | `/ranking` |
| Coleção de 139 carimbos | Home |
| Legado: outro jogo, temporadas de 90 dias, quatro classes | Home |
| `/diario` responde 404; o diário fica na home e o histórico em `/versoes` | Fetch |
| Páginas `/termos` e `/creditos` | Fetch |
| Front-end Next.js/React; 54 scripts analisados | REA `analyze-web-bundle` (parcial: um script estourou o prazo) |
| Endpoints públicos: `/api/ranking?quadro=…`, `/api/conta`, `/api/auth/sair`, `/api/auth/google/disponivel`, `/api/erro` | REA (candidatos estáticos) |
| Formato do ranking: `linhas[]` com chave, posicao, presidente, partido, nota, titulo, aprovacao, pib, pontos, dificuldade, inflacao, indiceEconomia, desfecho, meses, mandato | GET público `/api/ranking?quadro=geral` |

## Bloqueado

- `/entrar`, `/jogar`, `/conta`: exigem login. Os Termos (Art. 9–10) proíbem bot e automação, então não foi feito login nem jogo automatizado.
- Regras internas (custos, quóruns, efeitos, texto das medidas, eventos): não observadas.
- Pagamentos: não iniciados.
- Legado: site separado, com conta própria, não acessado.

## Reconstruído (Civiciclo)

Congresso nominal (513 + 81), Placar com nota S–F, Coleção de carimbos, Diário, Planos, Legado, Termos e Créditos informativos.

## Inferido ou simulado (sem evidência do site)

- A fórmula de pontos e os pesos dos blocos (`engine/meta.py`).
- Disposição de voto de cada parlamentar e quóruns (`engine/legislature.py`): 257 para projeto de lei, 308 para PEC; PEC com dois turnos.
- Os 33 carimbos e suas raridades.
- Entradas de exemplo no ranking (fictícias, marcadas como simuladas).
- Parlamentares, partidos e nomes: totalmente inventados.

## Pendências

- Dinastias, Semana e Coleção como quadros do ranking.
- Reeleição/sucessão ligadas ao placar automaticamente.
- Votação com emendas, comissões e negociação por cargo.
- Fidelidade de telas internas: depende de extrato fornecido pelo usuário (prints, gravações ou JSON).
- Multiplayer e Legado.
