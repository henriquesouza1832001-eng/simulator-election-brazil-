#!/usr/bin/env bash
# Roda a cada 5 minutos (timer do systemd). Só implanta commits cujos testes passaram no GitHub Actions.
set -Eeuo pipefail

base="/opt/quatroanos"
app_dir="$base/app"
repo="henriquesouza1832001-eng/simulator-election-brazil-"
workflow="ci.yml"
state_file="/var/lib/quatroanos/auto-deploy-last-checked"
branch="$(cat "$base/branch" 2>/dev/null || echo main)"

mkdir -p /run/lock /var/lib/quatroanos
exec 9>/run/lock/quatroanos-deploy.lock
flock 9

git -C "$app_dir" config core.fileMode false
git -C "$app_dir" fetch --quiet --prune origin "$branch"
deployed_sha="$(git -C "$app_dir" rev-parse HEAD)"
target_sha="$(git -C "$app_dir" rev-parse "origin/$branch")"

if [[ ! -s "$state_file" ]]; then
  printf '%s\n' "$deployed_sha" > "$state_file"
  chmod 600 "$state_file"
fi
checked_sha="$(cat "$state_file")"
if [[ "$checked_sha" == "$target_sha" ]]; then
  exit 0
fi
if ! git -C "$app_dir" merge-base --is-ancestor "$checked_sha" "$target_sha"; then
  echo "Recuso implantar sozinho: a branch ${branch} foi reescrita depois de ${checked_sha}. Veja o README (deploy/gcp)." >&2
  exit 1
fi

needs_deploy=0
while IFS= read -r path; do
  case "$path" in
    backend/*|src/*|public/*|data/*|deploy/nginx.conf|deploy/gcp/*|web.Dockerfile|package.json|package-lock.json|index.html|vite.config.js)
      needs_deploy=1
      break
      ;;
  esac
done < <(git -C "$app_dir" diff --name-only "$checked_sha" "$target_sha")

if [[ "$needs_deploy" == "0" ]]; then
  printf '%s\n' "$target_sha" > "${state_file}.tmp"
  chmod 600 "${state_file}.tmp"
  mv "${state_file}.tmp" "$state_file"
  echo "Verifiquei ${target_sha}; nenhum arquivo que exija implantação mudou."
  exit 0
fi

api_url="https://api.github.com/repos/${repo}/actions/workflows/${workflow}/runs?head_sha=${target_sha}&per_page=1"
workflow_json="$(curl --fail --silent --show-error --retry 3 --retry-delay 5 "$api_url")"
ci_result="$(python3 -c 'import json,sys; data=json.load(sys.stdin); runs=data.get("workflow_runs", []); run=next((r for r in runs if r.get("head_sha")==sys.argv[1]), None); print(((run or {}).get("status") or "pending")+":"+((run or {}).get("conclusion") or ""))' "$target_sha" <<<"$workflow_json")"
if [[ "$ci_result" != "completed:success" ]]; then
  echo "Aguardando testes verdes de ${target_sha}; situação atual: ${ci_result}."
  exit 0
fi

echo "Implantando o commit aprovado ${target_sha} da branch ${branch}."
QUATRO_DEPLOY_LOCK_HELD=1 bash "$app_dir/deploy/gcp/remote-deploy.sh" "$target_sha"
deployed_sha="$(git -C "$app_dir" rev-parse HEAD)"
printf '%s\n' "$deployed_sha" > "${state_file}.tmp"
chmod 600 "${state_file}.tmp"
mv "${state_file}.tmp" "$state_file"
