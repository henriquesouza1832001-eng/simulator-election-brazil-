# Contas, privacidade e publicação

## Situação publicada — 2 nov. 2026

- URL HTTPS: `https://d2dpmk0vrt66wn.cloudfront.net`.
- CloudFront termina TLS e encaminha ao EC2 por HTTP com segredo de origem. A porta 80 do EC2 aceita tráfego do CloudFront; o Nginx bloqueia requisições sem o cabeçalho secreto. O IP antigo responde 403.
- Amazon Cognito User Pool ativo. Cadastro por e-mail verificado e login pelo fluxo OAuth authorization code + PKCE, sem segredo no cliente público.
- A API valida a assinatura/issuer/expiração do access token e exige `token_use=access` e o `client_id` configurado. O `sub` verificado identifica o jogador; não é aceito um identificador escolhido pelo navegador.
- Partida, histórico de ações, prévias e correções de interpretação são filtrados por jogador no SQLite persistente do EC2. O texto da proposta e o resultado da interpretação ficam no `interpretation_log`; saídas sem correção humana não são rótulos de treino. O estado legado `local` foi preservado como jogador local; uma conta Cognito inicia um estado separado.
- A interface guarda os tokens com `CookieStorage` Secure e SameSite=Lax; são cookies acessíveis ao JavaScript, não cookies HttpOnly. O backend continua exigindo bearer token validado.
- A sessão HTTPS e as rotas protegidas foram verificadas: páginas e configuração respondem; `/api/game` sem token retorna 401; acesso direto ao IP retorna 403.

## Limites que ainda faltam antes de abrir amplamente

1. Criar várias campanhas independentes por jogador, com nome, cargo inicial, dificuldade e retomada. Hoje há um estado de jogo por conta.
2. Configurar cópia automática semanal para armazenamento fora da EC2 e testar restauração. A cópia manual pré-deploy está no mesmo volume e não substitui backup externo.
3. Configurar alarmes de custo e de falha, política de retenção de logs e limite de tentativas de autenticação.
4. Considerar MFA e recuperação de conta, testar cadastro, confirmação de e-mail, troca de senha e encerramento global de sessão.
5. Substituir o domínio CloudFront aleatório por domínio próprio somente se a experiência exigir um endereço permanente e memorável.

## Separação dos dados

`game_saves` tem uma linha por `player_id`; `actions`, `interpretation_log` e `interpretation_corrections` também registram `player_id`. O identificador vem do JWT validado. Catálogos eleitorais e trechos de conhecimento são dados compartilhados somente de leitura, sem saves pessoais.

## Recursos AWS

- Stack principal `mandato-simulator`: EC2 e volume persistente com o jogo e SQLite.
- Stack separada `mandato-edge-auth`: distribuição CloudFront, regra de entrada do origin e recursos Cognito. A distribuição pode ser atualizada sem recriar a instância principal.
- Arquivo `deploy/aws/.origin-secret`: segredo local da origem, ignorado pelo Git. Não publicar nem copiar para o frontend.
- Configuração de produção aplicada pelo SSM; `.env` remoto fica com permissão `600`.

## Referências

- [Amazon Cognito: authorization code grant e PKCE](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-settings-client-apps.html)
- [Amazon Cognito: callback HTTPS e endpoint de autorização](https://docs.aws.amazon.com/cognito/latest/developerguide/authorization-endpoint.html)
- [Amplify: opções de armazenamento dos tokens](https://docs.amplify.aws/react/build-a-backend/auth/concepts/tokens-and-credentials/)
