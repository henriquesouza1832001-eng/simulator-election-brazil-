# Contas, privacidade e publicação

## Estado atual

- O protótipo publicado ainda está em HTTP, protegido por regra de IP da EC2. Não colocar formulário de senha nesse endereço.
- O backend agora tem armazenamento de partida, ações e exemplos de aprendizado por `player_id`. O registro antigo migra para o jogador local sem apagar a base anterior.
- Quando Cognito estiver configurado, o backend aceita apenas access tokens válidos do User Pool e usa o `sub` verificado no servidor como dono dos dados. O navegador não escolhe o `player_id`.
- O cliente de login existe de forma opcional. Sem os valores Cognito, o app segue no modo local de um jogador.

## Requisitos para habilitar contas

1. Publicar o jogo em um endereço HTTPS estável. O IP atual não é callback HTTPS e não deve receber senha. Cognito aceita `http://localhost` para desenvolvimento, mas exige HTTPS para callbacks de produção.
2. Criar um Cognito User Pool, domínio gerenciado e app client público, sem client secret. Habilitar somente Authorization Code Grant com PKCE e escopos `openid` e `email`.
3. Cadastrar o endereço exato do jogo como callback e logout URL.
4. Definir no backend `COGNITO_REGION`, `COGNITO_USER_POOL_ID`, `COGNITO_CLIENT_ID` e `COGNITO_DOMAIN` (host Cognito sem `https://`). Não colocar segredos AWS no frontend.
5. Ativar inscrição/verificação de email e política de senha no User Pool. Considerar MFA antes de abrir acesso público.
6. Abrir a aplicação pelo domínio HTTPS; conferir que API rejeita chamadas sem token e que dois usuários recebem estados vazios e independentes.
7. Configurar backup externo semanal e realizar uma restauração de ensaio antes de usar contas reais.

## Dados separados hoje

`game_saves` tem uma linha por identidade. `actions` e `interpretation_corrections` também têm `player_id`. O banco de dados de fatos TSE e trechos de conhecimento continua compartilhado e somente de leitura: não contém saves pessoais. A próxima migração adicionará `campaign_id` para cada pessoa poder guardar várias campanhas, exportar e apagar uma campanha sem afetar as demais.

## Rede e operação

Manter a EC2 sem porta SSH e restringir o origin ao proxy TLS escolhido antes de remover a lista de IPs atual. Não expor diretamente a porta da API. Incluir logs de autenticação sem tokens, limite de tentativas, monitoramento de erro, orçamento AWS e rotação/expiração de sessões. HSTS deve ser ativado somente quando todo o domínio operar corretamente em HTTPS.

## Referências

- Amazon Cognito recomenda authorization code + PKCE para aplicativos públicos e SPAs: https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-settings-client-apps.html
- Cognito exige HTTPS para callback, exceto localhost de desenvolvimento: https://docs.aws.amazon.com/cognito/latest/developerguide/authorization-endpoint.html
