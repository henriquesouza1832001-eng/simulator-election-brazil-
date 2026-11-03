#!/usr/bin/env bash
set -Eeuo pipefail

backup_uri="${1:?Use s3://BUCKET/weekly/game-TIMESTAMP.sqlite3}"
if [[ "$backup_uri" != s3://*/weekly/game-*.sqlite3 ]]; then
  echo "Expected a weekly game database backup in S3." >&2
  exit 2
fi

app_dir="/opt/mandato/app"
backup_dir="/opt/mandato/backups"
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
restore_file="$backup_dir/restore-$stamp.sqlite3"
pre_restore_file="$backup_dir/pre-restore-$stamp.sqlite3"
api_stopped=0

restart_api() {
  status=$?
  if [[ "$api_stopped" == "1" ]]; then
    (cd "$app_dir" && docker compose up -d api) || true
  fi
  exit "$status"
}
trap restart_api EXIT

mkdir -p "$backup_dir"
chmod 700 "$backup_dir"
api_container="$(cd "$app_dir" && docker compose ps -q api)"
if [[ -z "$api_container" ]]; then
  echo "The API container is not running; refusing to replace the game database." >&2
  exit 1
fi

aws s3 cp "$backup_uri" "$restore_file" --only-show-errors --region "${AWS_REGION:-us-east-2}"
chmod 600 "$restore_file"
test -s "$restore_file"

docker exec "$api_container" python -c 'import sqlite3; d=sqlite3.connect("/data/game.sqlite3"); s=sqlite3.connect("/tmp/mandato-pre-restore.sqlite3"); d.backup(s); s.close(); d.close()'
docker cp "$api_container:/tmp/mandato-pre-restore.sqlite3" "$pre_restore_file"
chmod 600 "$pre_restore_file"
docker exec "$api_container" rm -f /tmp/mandato-pre-restore.sqlite3

(cd "$app_dir" && docker compose run --rm --no-deps -v "$restore_file:/tmp/restore.sqlite3:ro" api python -c 'import sqlite3; d=sqlite3.connect("file:/tmp/restore.sqlite3?mode=ro", uri=True); assert d.execute("PRAGMA integrity_check").fetchone()[0] == "ok"; d.close()')
(cd "$app_dir" && docker compose stop api)
api_stopped=1
(cd "$app_dir" && docker compose run --rm --no-deps -v "$restore_file:/tmp/restore.sqlite3:ro" api python -c 'import os, shutil, sqlite3; s=sqlite3.connect("file:/tmp/restore.sqlite3?mode=ro", uri=True); assert s.execute("PRAGMA integrity_check").fetchone()[0] == "ok"; s.close(); p="/data/game.sqlite3"; shutil.copyfile("/tmp/restore.sqlite3", p+".restore"); os.replace(p+".restore", p); [os.remove(p+x) for x in ("-wal", "-shm") if os.path.exists(p+x)]')
(cd "$app_dir" && docker compose up -d api)
api_stopped=0
echo "Restored $backup_uri. Previous database kept at $pre_restore_file."
