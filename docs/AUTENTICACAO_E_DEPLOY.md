# Contas, privacidade e publicação

## Situação publicada — 3 nov. 2026

- URL HTTPS: `https://d2dpmk0vrt66wn.cloudfront.net`.
- Versão em produção: commit `8d9effba7a0a10af03e97ae652081507a31823ce`, publicado via Systems Manager após backup consistente do SQLite em `/opt/mandato/backups/predeploy-1ef5e76e955f2ade55d0124c4b713fbfea360e0c.sqlite3`. API e web ficaram em execução; o endpoint público `/api/health` respondeu HTTP 200.
- CloudFront termina TLS e encaminha ao EC2 por HTTP com segredo de origem. A porta 80 do EC2 aceita tráfego do CloudFront; o Nginx bloqueia requisições sem o cabeçalho secreto. O IP antigo responde 403.
- Amazon Cognito User Pool ativo. Cadastro por e-mail verificado e login pelo fluxo OAuth authorization code + PKCE, sem segredo no cliente público.
- A API valida a assinatura/issuer/expiração do access token e exige `token_use=access` e o `client_id` configurado. O `sub` verificado identifica o jogador; não é aceito um identificador escolhido pelo navegador.
- Campanhas, histórico de ações, prévias e correções de interpretação são filtrados por jogador no SQLite persistente do EC2. Cada campanha tem ID próprio; o servidor valida que ela pertence ao jogador autenticado. Saves antigos migram para a campanha inicial `default`. O texto da proposta e o resultado da interpretação ficam no `interpretation_log`; saídas sem correção humana não são rótulos de treino.
- A interface guarda os tokens com `CookieStorage` Secure e SameSite=Lax; são cookies acessíveis ao JavaScript, não cookies HttpOnly. O backend continua exigindo bearer token validado.
- A sessão HTTPS e as rotas protegidas foram verificadas: páginas e configuração respondem; `/api/game` sem token retorna 401; acesso direto ao IP retorna 403.

## Deploy automático via GitHub Actions

O workflow `aws-deploy.yml` faz build e roda a suíte do backend em cada atualização relevante na `main`. Para publicar, o GitHub assume por OIDC a role `mandato-github-deploy` e envia o script de deploy para uma instância EC2 específica via Systems Manager; não há chaves AWS permanentes no GitHub.

A role ainda não está conectada: a validação do commit publicado passou, mas o job de deploy foi pulado porque a variável de repositório `AWS_DEPLOY_ROLE_ARN` não existe. A tentativa de configuração pela CLI foi bloqueada pela SCP da AWS Organizations ao consultar o provedor IAM OIDC; a role e a stack CloudFormation ainda não existem. Até essa permissão ser liberada, publique com `deploy/aws/remote-deploy.sh` via SSM. O repositório já tem o subject OIDC imutável habilitado.

Para concluir a configuração uma vez, autentique o AWS CLI e o GitHub CLI na conta correta e execute `./deploy/aws/setup-github-deploy.ps1` no PowerShell. O helper valida o repositório e a OIDC, cria/atualiza a stack CloudFormation `mandato-github-deploy`, restringe a role ao branch `main` e à instância do jogo, grava o ARN como `AWS_DEPLOY_ROLE_ARN` e dispara um deploy. Depois disso, pushes relevantes publicam automaticamente.
## Limites que ainda faltam antes de abrir amplamente

1. Aplicar a configuração de backup semanal S3 em `deploy/aws/template.yaml` e validar um envio e uma restauração reais. A cópia manual pré-deploy fica no mesmo volume e não substitui o backup externo.
2. Configurar alarmes de custo e de falha, política de retenção de logs e limite de tentativas de autenticação.
3. Considerar MFA e recuperação de conta, testar cadastro, confirmação de e-mail, troca de senha e encerramento global de sessão.
4. Substituir o domínio CloudFront aleatório por domínio próprio somente se a experiência exigir um endereço permanente e memorável.

## Separação dos dados

`game_campaigns` guarda várias linhas por `player_id`, cada uma com `campaign_id`, nome e estado. O identificador de jogador vem do JWT validado, e o servidor confere a propriedade da campanha escolhida no cabeçalho. Ações e snapshots de recuperação são filtrados por jogador e campanha; interpretações e correções são filtradas por jogador. `game_saves` é mantida apenas para migrar saves antigos. Catálogos eleitorais e trechos de conhecimento são dados compartilhados somente de leitura.

## Recursos AWS

- Stack principal `mandato-simulator`: EC2 e volume persistente com o jogo e SQLite.
- Stack separada `mandato-edge-auth`: distribuição CloudFront, regra de entrada do origin e recursos Cognito. A distribuição pode ser atualizada sem recriar a instância principal.
- Arquivo `deploy/aws/.origin-secret`: segredo local da origem, ignorado pelo Git. Não publicar nem copiar para o frontend.
- Configuração de produção aplicada pelo SSM; `.env` remoto fica com permissão `600`.

## Referências

- [Amazon Cognito: authorization code grant e PKCE](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-settings-client-apps.html)
- [Amazon Cognito: callback HTTPS e endpoint de autorização](https://docs.aws.amazon.com/cognito/latest/developerguide/authorization-endpoint.html)
- [Amplify: opções de armazenamento dos tokens](https://docs.amplify.aws/react/build-a-backend/auth/concepts/tokens-and-credentials/)
