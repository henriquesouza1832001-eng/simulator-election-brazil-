# Workflows automáticos e AWS

Revisão de 9 nov. 2026. **Nada aqui faz deploy nem cria recurso na AWS.**

## O que já existia: `aws-deploy.yml` (somente `main`)

Fluxo: push em `main` → build do front-end + testes da API → deploy. O deploy tem **duas vias**:

1. **Host consulta `main`** (a via em uso): `deploy/aws/auto-deploy-check.sh` roda por timer a cada 5 minutos na instância, confere o resultado público do workflow, faz **backup do SQLite antes do deploy**, executa `docker compose build/up`, confere `/api/health` e reverte se falhar (`remote-deploy.sh`).
2. **GitHub → AWS por OIDC + SSM** (preparada, **inativa**): a role `AWS_DEPLOY_ROLE_ARN` não existe porque a SCP da conta impede criá-la.

Mudanças de `docs/` não disparam rebuild (só `backend/`, `src/`, `public/`, `data/`, `deploy/aws/` e arquivos de build).

## O que foi adicionado

| Workflow | Quando roda | O que faz | Segredos/AWS |
| --- | --- | --- | --- |
| `ci.yml` | pull requests para `main` e push em qualquer outra branch | build do front-end, **validação da biblioteca de eventos** (`python -m app.engine.event_library`) e todos os testes da API | nenhum |
| `events-generate.yml` | só manual (`workflow_dispatch`) | importa candidatos do TSE (para a trava de nomes reais), gera eventos a partir do corpus, **abre um PR** com eventos `pendente` | `GEMINI_API_KEY` opcional; sem ela usa adaptação local |

`ci.yml` fecha a lacuna principal: antes, o CI só rodava **depois** do merge em `main`.

Para `events-generate.yml` funcionar: criar o segredo `GEMINI_API_KEY` (opcional) e habilitar em *Settings → Actions → General* a opção "Allow GitHub Actions to create and approve pull requests". Com o Gemini ligado, os resumos do corpus são enviados à API do Google.

## Segurança do gerador

- Recusa rodar se a trava de nomes reais estiver vazia (sem candidatos do TSE no banco). `--no-guard` existe, por conta e risco de quem usa.
- Nada gerado entra no jogo sem aprovação explícita; quem aprovou fica gravado em `reviewed_by`. Os 124 eventos históricos atuais foram aprovados por **validação automática, sem revisão editorial humana**, e as fontes do corpus estão marcadas `source_verified: false`.

## O que continua manual e por quê

- **Dados do TSE em produção.** O banco do servidor não tem a tabela `tse_candidacies`; sem ela o Modo Eleitor mostra "dados oficiais ainda não importados". Rodar no servidor (com suas credenciais, via sessão SSM ou console):

  ```bash
  cd /opt/mandato/app && docker compose exec -T api python -m app.data.tse_candidacies --years 2014 2018 2022 2026
  # anos municipais (2016, 2020, 2024) têm ~500 mil linhas cada; conferir o espaço em disco antes
  ```

  O importador confirma por lote, então o jogo continua gravando saves durante a importação. Não automatizei isso: exigiria alterar `remote-deploy.sh` (código de produção que não dá para testar daqui) ou uma role SSM que a SCP bloqueia.
- **Trava de nomes reais no servidor** depende dessa mesma importação (anos gerais).
- **Merge e deploy** continuam a decisão de quem mescla o PR em `main`.

## Pendências

- Alerta quando o deploy falhar (hoje só o log do workflow e o health check).
- Se a SCP for liberada: ativar a rota OIDC/SSM e um job manual de importação do TSE.
