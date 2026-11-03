#!/usr/bin/env bash
set -Eeuo pipefail

requested_sha="${1:?Expected commit SHA is required}"
app_dir="/opt/mandato/app"
backup_dir="/opt/mandato/backups"
mkdir -p /run/lock
if [[ "${MANDATO_DEPLOY_LOCK_HELD:-0}" != "1" ]]; then
  exec 9>/run/lock/mandato-deploy.lock
  flock 9
fi
previous_sha="$(git -C "$app_dir" rev-parse HEAD)"
deployment_started=0

rollback() {
  exit_code=$?
  if [[ "$deployment_started" == "1" ]]; then
    echo "Deployment failed; restoring ${previous_sha}." >&2
    git -C "$app_dir" reset --hard "$previous_sha" || true
    (cd "$app_dir" && docker compose build api && docker compose build web && docker compose up -d) || true
  fi
  exit "$exit_code"
}
trap rollback ERR

git -C "$app_dir" fetch --prune origin main
main_sha="$(git -C "$app_dir" rev-parse origin/main)"
if ! git -C "$app_dir" cat-file -e "${requested_sha}^{commit}"; then
  echo "Requested commit is not available locally: ${requested_sha}" >&2
  exit 1
fi
if [[ "$requested_sha" != "$main_sha" ]]; then
  echo "Skipping ${requested_sha}: main is now ${main_sha}; deploy only after that commit passes CI."
  exit 0
fi
deployed_sha="$requested_sha"
echo "CI-approved commit: ${deployed_sha}"
if [[ "$previous_sha" == "$deployed_sha" ]]; then
  echo "Game host is already at ${deployed_sha}; no deployment needed."
  exit 0
fi

mkdir -p "$backup_dir"
api_container="$(cd "$app_dir" && docker compose ps -q api)"
if [[ -z "$api_container" ]]; then
  echo "The API container is not running; refusing to deploy without a database backup." >&2
  exit 1
fi
backup_name="predeploy-${previous_sha}.sqlite3"
docker exec "$api_container" python -c 'import sqlite3; source = sqlite3.connect("/data/game.sqlite3"); target = sqlite3.connect("/tmp/mandato-predeploy.sqlite3"); source.backup(target); target.close(); source.close()'
docker cp "$api_container:/tmp/mandato-predeploy.sqlite3" "$backup_dir/$backup_name"
chmod 600 "$backup_dir/$backup_name"
docker exec "$api_container" rm -f /tmp/mandato-predeploy.sqlite3
echo "SQLite backup: $backup_dir/$backup_name"

deployment_started=1
git -C "$app_dir" checkout main
git -C "$app_dir" reset --hard "$deployed_sha"
cd "$app_dir"
docker compose build api
docker compose build web
docker compose up -d --remove-orphans

for attempt in $(seq 1 40); do
  if docker compose exec -T api python -c 'from urllib.request import urlopen; response = urlopen("http://127.0.0.1:8000/api/health", timeout=3); assert response.status == 200; print(response.read().decode())'; then
    deployment_started=0
    find "$backup_dir" -maxdepth 1 -type f -name 'predeploy-*.sqlite3' -printf '%T@ %p\n' | sort -nr | tail -n +31 | cut -d' ' -f2- | xargs -r rm -f --
    echo "Deploy healthy at $(date -u +%Y-%m-%dT%H:%M:%SZ); commit $deployed_sha"
    exit 0
  fi
  sleep 3
done

echo "API health check failed after deployment." >&2
exit 1
