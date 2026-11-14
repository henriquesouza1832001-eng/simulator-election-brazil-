# Quatro Anos na VM do Google (com túnel da Cloudflare)

O jogo roda numa VM `e2-micro` do Google Compute Engine, sem nenhuma porta aberta para a internet.
O acesso é só pelo **Cloudflare Tunnel** (a VM faz uma conexão de saída até a Cloudflare), protegido pelo
**Cloudflare Access** (login por e-mail, só o seu). O site também avisa os buscadores para não indexar.

```
você ──HTTPS──> Cloudflare (Access: só o seu e-mail) ──túnel──> VM do Google
                                                                 ├─ web (nginx: site + proxy /api)
                                                                 └─ api (FastAPI + SQLite)
```

## Onde fica o site: tudo na VM ou o front na Cloudflare?

Decisão: **tudo na VM, atrás do túnel**.

- Uma origem só (`/` e `/api` no mesmo endereço): sem CORS, sem cookies entre domínios e uma única regra do Access protegendo tudo.
- Hospedar o front no Cloudflare Pages exigiria liberar a API a outro endereço (CORS e uma segunda política de Access para a API), e o ganho de desempenho é pequeno para uma pessoa só.
- O ponto fraco da VM é o build do front (Node) numa máquina de 1 GB. Por isso a VM tem 2 GB de swap, e o deploy faz o build uma vez por atualização. Se ficar lento, o próximo passo é construir as imagens no GitHub Actions e a VM só baixar.

## Preparar a VM (uma vez)

Pré-requisitos já cumpridos: Ubuntu 24.04, swap de 2 GB, Docker e Compose.

```bash
# dentro da VM (botão SSH do console do Google)
git clone --branch SUA_BRANCH https://github.com/henriquesouza1832001-eng/simulator-election-brazil-.git /tmp/qa
sudo bash /tmp/qa/deploy/gcp/bootstrap.sh SUA_BRANCH
```

`SUA_BRANCH` é a branch que a VM acompanha (hoje `feat/cenarios-eleitorais-modo-eleitor`; depois do merge, `main`).
Para trocar depois: `echo main | sudo tee /opt/quatroanos/branch` e `sudo rm /var/lib/quatroanos/auto-deploy-last-checked`.

O script cria `/opt/quatroanos`, instala o atalho `quatro-dc` (um `docker compose` já apontado para o arquivo certo),
sobe API e site e liga os dois timers: **deploy automático** (a cada 5 min) e **backup diário**.

## Criar o túnel e o acesso (Cloudflare)

Precisa de um domínio na sua conta Cloudflare (por exemplo `exemplo.com`).

1. Painel **Zero Trust > Networks > Tunnels > Create a tunnel > Cloudflared**. Dê o nome `quatroanos`.
2. Copie o **token** que aparece no comando de instalação (a parte depois de `--token`). Não cole o token em conversas nem no GitHub.
3. Em **Public hostnames**, adicione `quatroanos.exemplo.com` apontando para **HTTP** e `web:80`.
4. Na VM, edite o arquivo de configuração:
   ```bash
   sudo nano /opt/quatroanos/.env
   ```
   Preencha `TUNNEL_TOKEN=` com o token e troque `COMPOSE_PROFILES=` por `COMPOSE_PROFILES=tunnel`. Salve.
5. Suba o túnel: `quatro-dc up -d` e confira com `quatro-dc ps` (o `cloudflared` deve estar `Up`).
6. **Proteja o acesso** antes de divulgar o endereço: Zero Trust > **Access > Applications > Add an application > Self-hosted**,
   domínio `quatroanos.exemplo.com`, política **Allow** com **Emails** = o seu e-mail. Teste numa janela anônima:
   deve pedir o código por e-mail.
7. No console do Google, **remova as regras de firewall HTTP e HTTPS** da VM (e deixe só o SSH pelo navegador). O túnel não precisa de porta aberta.

## Dia a dia

| O que | Comando na VM |
|---|---|
| Ver os serviços | `quatro-dc ps` |
| Logs da API | `quatro-dc logs -f --tail 100 api` |
| Ver o deploy automático | `journalctl -u quatroanos-auto-deploy.service -n 30 --no-pager` |
| Forçar uma verificação agora | `sudo systemctl start quatroanos-auto-deploy.service` |
| Backup manual | `sudo systemctl start quatroanos-backup.service` |
| Backups | `ls -lh /opt/quatroanos/backups` |

## Como o deploy automático decide

1. A VM consulta a branch acompanhada no GitHub a cada 5 minutos.
2. Só implanta se o fluxo **CI** (`.github/workflows/ci.yml`: build, eventos e testes) terminou com sucesso naquele commit.
3. Antes de trocar o código, faz um **backup enxuto** do banco (`slim_backup.py`: as partidas, sem as tabelas do TSE).
4. Reconstrói as imagens, sobe e confere `/api/health`. Se falhar, **volta ao commit anterior** sozinho.
5. Se a branch for reescrita (force-push), a VM **se recusa** a implantar sozinha: veja o log e ajuste o ponto de partida com
   `git -C /opt/quatroanos/app rev-parse HEAD | sudo tee /var/lib/quatroanos/auto-deploy-last-checked`.

## Dados do TSE

O banco de produção começa sem os dados do TSE (votos e candidaturas). Para importar, dentro da VM:

```bash
quatro-dc exec api python -m app.data.tse_candidacies --years 2018 2020 2022 2024
quatro-dc exec api python -m app.data.tse_votes --years 2016 2020 2024
```

Rode um ano de cada vez se a memória apertar e acompanhe com `free -h`. Confira com `GET /api/data/tse/status`.

## Restaurar um backup

```bash
sudo systemctl stop quatroanos-auto-deploy.timer
quatro-dc stop api
gunzip -k /opt/quatroanos/backups/daily-AAAAMMDD.sqlite3.gz
docker cp /opt/quatroanos/backups/daily-AAAAMMDD.sqlite3 $(quatro-dc ps -q api):/data/game.sqlite3
quatro-dc start api
sudo systemctl start quatroanos-auto-deploy.timer
```

Depois reimporte as tabelas do TSE (seção acima), porque o backup enxuto não as inclui.

## Segurança

- Nada de segredos no repositório: o token do túnel e as chaves do Gemini ficam só em `/opt/quatroanos/.env` (permissão 600).
- O site manda `X-Robots-Tag: noindex` e `robots.txt` bloqueando tudo; o Cloudflare Access impede que alguém sem o seu e-mail chegue ao jogo.
- A VM não publica nenhuma porta. Se o túnel cair, o jogo some para todos, inclusive para você, e volta quando o `cloudflared` reconectar.
