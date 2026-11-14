#!/usr/bin/env bash
# Backup diário das partidas (sem as tabelas do TSE, que se recriam). Guarda os últimos 14.
set -Eeuo pipefail

base="/opt/quatroanos"
app_dir="$base/app"
backup_dir="$base/backups"
dc() { docker compose -f "$app_dir/deploy/gcp/compose.yaml" --env-file "$base/.env" "$@"; }

mkdir -p "$backup_dir"
chmod 700 "$backup_dir"
api_container="$(dc ps -q api)"
if [[ -z "$api_container" ]]; then
  echo "A API não está rodando; sem backup." >&2
  exit 1
fi
name="daily-$(date -u +%Y%m%d).sqlite3"
dc exec -T api python - "/tmp/$name" < "$app_dir/deploy/gcp/slim_backup.py"
docker cp "$api_container:/tmp/$name" "$backup_dir/$name"
dc exec -T api rm -f "/tmp/$name"
gzip -f "$backup_dir/$name"
chmod 600 "$backup_dir/$name.gz"
find "$backup_dir" -maxdepth 1 -type f -name 'daily-*.sqlite3.gz' -printf '%T@ %p\n' | sort -nr | tail -n +15 | cut -d' ' -f2- | xargs -r rm -f --
echo "Backup salvo: $backup_dir/$name.gz"
