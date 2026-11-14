#!/usr/bin/env bash
# Prepara a VM do Google uma única vez: baixa o código, cria os arquivos de configuração,
# instala os timers (deploy automático e backup diário) e sobe a API e o site.
# Uso (na VM):  sudo bash bootstrap.sh [branch]      # branch padrão: main
set -Eeuo pipefail

if [[ $EUID -ne 0 ]]; then
  echo "Rode com sudo." >&2
  exit 1
fi
branch="${1:-main}"
repo_url="https://github.com/henriquesouza1832001-eng/simulator-election-brazil-.git"
base="/opt/quatroanos"
app_dir="$base/app"

mkdir -p "$base/backups" /var/lib/quatroanos
chmod 700 "$base/backups"
printf '%s\n' "$branch" > "$base/branch"

if [[ ! -d "$app_dir/.git" ]]; then
  git clone --branch "$branch" "$repo_url" "$app_dir"
else
  git -C "$app_dir" fetch origin "$branch"
  git -C "$app_dir" checkout -B "$branch" "origin/$branch"
fi

if [[ ! -f "$base/.env" ]]; then
  cat > "$base/.env" <<'EOF'
# Configuração do Quatro Anos nesta VM. NUNCA suba este arquivo para o GitHub.
# Token do túnel da Cloudflare (painel Zero Trust > Networks > Tunnels). Deixe em branco até criar o túnel.
TUNNEL_TOKEN=
# Troque por COMPOSE_PROFILES=tunnel depois de colar o token acima.
COMPOSE_PROFILES=
# Endereço público (só informativo para a API).
PUBLIC_URL=
# Gemini (opcional): use a chave direta OU o gateway da Cloudflare.
GEMINI_API_KEY=
GEMINI_MODEL=
GEMINI_GATEWAY_URL=
GEMINI_GATEWAY_TOKEN=
# Deixe vazio: quem protege o acesso é o Cloudflare Access.
ORIGIN_SECRET=
EOF
  chmod 600 "$base/.env"
fi

cat > /usr/local/bin/quatro-dc <<'EOF'
#!/usr/bin/env bash
# O .env guarda segredos (permissão 600, só root); por isso o atalho se reexecuta com sudo.
if [[ $EUID -ne 0 ]]; then exec sudo "$0" "$@"; fi
exec docker compose -f /opt/quatroanos/app/deploy/gcp/compose.yaml --env-file /opt/quatroanos/.env "$@"
EOF
chmod 755 /usr/local/bin/quatro-dc

chmod 755 "$app_dir"/deploy/gcp/*.sh
cp "$app_dir"/deploy/gcp/quatroanos-*.service "$app_dir"/deploy/gcp/quatroanos-*.timer /etc/systemd/system/
systemctl daemon-reload

(cd "$app_dir" && quatro-dc build api && quatro-dc build web && quatro-dc up -d --remove-orphans)

# Registra o commit atual como ponto de partida do deploy automático.
git -C "$app_dir" rev-parse HEAD > /var/lib/quatroanos/auto-deploy-last-checked
chmod 600 /var/lib/quatroanos/auto-deploy-last-checked
systemctl enable --now quatroanos-auto-deploy.timer quatroanos-backup.timer

echo
echo "Pronto. Confira:  quatro-dc ps"
echo "Health da API:    quatro-dc exec -T api python -c 'from urllib.request import urlopen; print(urlopen(\"http://127.0.0.1:8000/api/health\").read())'"
echo "Próximo passo:    criar o túnel na Cloudflare e colar o token em $base/.env (veja deploy/gcp/README.md)."
