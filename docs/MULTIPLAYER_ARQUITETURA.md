# Multiplayer: arquitetura planejada (não implementada)

**Estado: não existe multiplayer no Civiciclo.** Este documento define contratos e migrações para depois da base solo. Nada aqui está ativo; ao implementar, tudo fica atrás da flag `MULTIPLAYER_ENABLED=false` (padrão), sem alterar a partida solo nem exigir login.

Regra central: **votação entre jogadores dentro da partida não é voto real** e nunca se conecta a urna, pesquisa ou coleta de voto reais. A tela deve repetir o aviso do Modo Eleitor.

## Entidades

| Entidade | Campos principais |
| --- | --- |
| `rooms` | `id`, `scenario_year`, `difficulty`, `seed`, `clock_mode`, `status` (`lobby`, `ativa`, `encerrada`), `owner_player_id`, `max_players`, `created_at` |
| `room_players` | `room_id`, `player_id`, `role`, `party_id`, `joined_at`, `status` (`ativo`, `ausente`, `removido`), `last_seen_at` |
| `room_roles` | `room_id`, `role` (`candidato`, `equipe`, `partido`, `governo`, `oposicao`, `observador`), `permissions[]` |
| `room_state` | `room_id`, `day`, `version`, `state_json` — **autoritativo no servidor** |
| `action_log` | `room_id`, `seq`, `player_id`, `day`, `type`, `payload`, `state_before_hash`, `state_after_hash`, `created_at` — **append-only** |
| `internal_ballots` | `id`, `room_id`, `kind` (`candidato`, `alianca`, `prioridade`, `decisao_governo`), `question`, `options[]`, `opens_at`, `closes_at`, `quorum`, `tie_rule`, `secret` (bool), `status` |
| `internal_votes` | `ballot_id`, `player_id`, `choice` (`opcao`, `abstencao`), `cast_at` — único por (`ballot_id`, `player_id`) |
| `invites` | `id`, `room_id`, `token_hash`, `expires_at`, `uses_left` |
| `moderation_events` | `room_id`, `player_id`, `kind`, `reason`, `by_player_id`, `created_at` |

## Regras de estado e sincronização

- O servidor é a única fonte de verdade. O cliente envia **intenções**; o motor valida, aplica e grava no `action_log`.
- Toda escrita confere `room_state.version` esperada (controle otimista). Divergência retorna `409` com o estado atual; nunca sobrescreve silenciosamente.
- Relógio compartilhado: o dia da sala avança por regra de sala (por exemplo, só quando todos os jogadores ativos marcam "pronto" ou por prazo). O avanço para antes de prazos obrigatórios (convenção, registro, turnos) e registra quem avançou.
- Reconexão: o cliente pede `GET /api/rooms/{id}/state?since=seq` e recebe o delta do `action_log`.
- Determinismo: sorteios por hash de (semente da sala, dia, chave), como no solo; o mesmo log reproduz o mesmo estado.

## Votação interna

- Abertura: quem tem a permissão `criar_votacao` (por papel) informa pergunta, opções, prazo, quórum e regra de empate.
- **Quórum:** mínimo de votos (incluindo abstenções) para valer. **Maioria:** simples sobre votos válidos (sem abstenções). **Empate:** `desempate_por: presidente_do_partido | sorteio_deterministico | repetir`, definido na abertura.
- **Privacidade:** se `secret=true`, o servidor guarda quem votou, mas **só divulga o agregado** ao fechar; nunca expõe voto individual a outros jogadores.
- Resultado e trilha: `closed_at`, contagem, quórum atingido, regra aplicada e hash do log. O efeito da decisão entra no `action_log` como ação do sistema.
- Jogador ausente: não vota; conta para quórum só se a sala definir "ausência conta como abstenção".

## API planejada (contrato)

| Método e rota | Função |
| --- | --- |
| `POST /api/rooms` | cria sala (cenário, dificuldade, limites) |
| `POST /api/rooms/{id}/invites` · `POST /api/rooms/join` | convite e entrada por token |
| `GET /api/rooms/{id}` · `GET /api/rooms/{id}/state?since=` | metadados e delta de estado |
| `POST /api/rooms/{id}/actions` | envia intenção (com `expected_version`) |
| `POST /api/rooms/{id}/ballots` · `POST /api/rooms/{id}/ballots/{bid}/vote` · `GET …/results` | votação interna |
| `POST /api/rooms/{id}/moderation` | expulsar, silenciar, bloquear (somente dono/moderador) |

Autenticação: exige conta (Cognito) apenas para multiplayer; o modo solo permanece anônimo.

## Moderação e limites

Limite de jogadores e de salas por conta, rate limit por jogador e por sala, nomes e mensagens passam pelo mesmo filtro de termos barrados do nome de partido, bloqueio e denúncia, convite com expiração e uso limitado, remoção de jogador pelo dono com registro em `moderation_events`.

## Migração e ordem de entrega

1. Persistência solo por partida (já existe) e estados versionados (`version`) — pré-requisito.
2. Tabelas `rooms`, `room_players`, `action_log` (somente leitura no cliente).
3. Salas de 2 jogadores com relógio compartilhado e ações validadas.
4. Papéis e permissões.
5. Votação interna com resultado auditável.
6. Moderação, convites e limites.

Cada etapa só entra com testes de concorrência (duas ações simultâneas, reconexão, replay do log).
