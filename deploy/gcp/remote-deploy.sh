#!/usr/bin/env bash
# Implanta um commit já aprovado pelos testes. Faz backup antes e volta ao commit anterior se algo falhar.
set -Eeuo pipefail

requested_sha="${1:?Informe o SHA do commit}"
base="/opt/quatroanos"
app_dir="$base/app"
backup_dir="$base/backups"
branch="$(cat "$base/branch" 2>/dev/null || echo main)"
dc() { docker compose -f "$app_dir/deploy/gcp/compose.yaml" --env-file "$base/.env" "$@"; }

mkdir -p /run/lock
if [[ "${QUATRO_DEPLOY_LOCK_HELD:-0}" != "1" ]]; then
  exec 9>/run/lock/quatroanos-deploy.lock
  flock 9
fi
previous_sha="$(git -C "$app_dir" rev-parse HEAD)"
deployment_started=0

rollback() {
  exit_code=$?
  if [[ "$deployment_started" == "1" ]]; then
    echo "A implantação falhou; voltando para ${previous_sha}." >&2
    git -C "$app_dir" reset --hard "$previous_sha" || true
    (cd "$app_dir" && dc build api && dc build web && dc up -d --remove-orphans) || true
  fi
  exit "$exit_code"
}
trap rollback ERR

git -C "$app_dir" fetch --prune origin "$branch"
branch_sha="$(git -C "$app_dir" rev-parse "origin/$branch")"
if ! git -C "$app_dir" cat-file -e "${requested_sha}^{commit}"; then
  echo "Commit não encontrado: ${requested_sha}" >&2
  exit 1
fi
if [[ "$requested_sha" != "$branch_sha" ]]; then
  echo "Ignorando ${requested_sha}: a branch ${branch} já está em ${branch_sha}; só implanto depois que esse commit passar nos testes."
  exit 0
fi
if [[ "$previous_sha" == "$requested_sha" ]]; then
  echo "A VM já está em ${requested_sha}."
  exit 0
fi

mkdir -p "$backup_dir"
chmod 700 "$backup_dir"
api_container="$(dc ps -q api)"
if [[ -z "$api_container" ]]; then
  echo "O container da API não está rodando; não implanto sem backup do banco." >&2
  exit 1
fi
backup_name="predeploy-${previous_sha}.sqlite3"
dc exec -T api python - "/tmp/$backup_name" < "$app_dir/deploy/gcp/slim_backup.py"
docker cp "$api_container:/tmp/$backup_name" "$backup_dir/$backup_name"
dc exec -T api rm -f "/tmp/$backup_name"
chmod 600 "$backup_dir/$backup_name"
echo "Backup: $backup_dir/$backup_name"

deployment_started=1
git -C "$app_dir" checkout -B "$branch" "$requested_sha"
cd "$app_dir"
dc build api
dc build web
dc up -d --remove-orphans

for attempt in $(seq 1 40); do
  if dc exec -T api python -c 'from urllib.request import urlopen; r = urlopen("http://127.0.0.1:8000/api/health", timeout=3); assert r.status == 200; print(r.read().decode())'; then
    deployment_started=0
    find "$backup_dir" -maxdepth 1 -type f -name 'predeploy-*.sqlite3' -printf '%T@ %p\n' | sort -nr | tail -n +31 | cut -d' ' -f2- | xargs -r rm -f --
    docker image prune -f >/dev/null 2>&1 || true
    echo "Implantação saudável em $(date -u +%Y-%m-%dT%H:%M:%SZ); commit ${requested_sha}"
    exit 0
  fi
  sleep 3
done

echo "A API não respondeu ao health check depois da implantação." >&2
exit 1
