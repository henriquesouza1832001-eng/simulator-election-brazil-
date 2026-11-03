#!/usr/bin/env bash
set -Eeuo pipefail

app_dir="/opt/mandato/app"
repo="henriquesouza1832001-eng/simulator-election-brazil-"
workflow="aws-deploy.yml"
state_file="/var/lib/mandato/auto-deploy-last-checked"

mkdir -p /run/lock
exec 9>/run/lock/mandato-deploy.lock
flock 9

if [[ -f "$app_dir/.git/shallow" ]]; then
  git -C "$app_dir" fetch --unshallow --quiet origin main
else
  git -C "$app_dir" fetch --quiet --prune origin main
fi
deployed_sha="$(git -C "$app_dir" rev-parse HEAD)"
target_sha="$(git -C "$app_dir" rev-parse origin/main)"

if [[ ! -s "$state_file" ]]; then
  printf '%s\n' "$deployed_sha" > "$state_file"
  chmod 600 "$state_file"
fi
checked_sha="$(cat "$state_file")"
if [[ "$checked_sha" == "$target_sha" ]]; then
  exit 0
fi
if ! git -C "$app_dir" merge-base --is-ancestor "$checked_sha" "$target_sha"; then
  echo "Refusing automatic deployment: main was rewritten after ${checked_sha}." >&2
  exit 1
fi

needs_deploy=0
while IFS= read -r path; do
  case "$path" in
    backend/*|src/*|public/*|data/*|deploy/nginx.conf|deploy/aws/*|compose.yaml|web.Dockerfile|package.json|package-lock.json|index.html|vite.config.js|.github/workflows/aws-deploy.yml)
      needs_deploy=1
      break
      ;;
  esac
done < <(git -C "$app_dir" diff --name-only "$checked_sha" "$target_sha")

if [[ "$needs_deploy" == "0" ]]; then
  printf '%s\n' "$target_sha" > "${state_file}.tmp"
  chmod 600 "${state_file}.tmp"
  mv "${state_file}.tmp" "$state_file"
  echo "Checked ${target_sha}; no deployable files changed."
  exit 0
fi

api_url="https://api.github.com/repos/${repo}/actions/workflows/${workflow}/runs?head_sha=${target_sha}&per_page=1"
workflow_json="$(curl --fail --silent --show-error --retry 3 --retry-delay 5 "$api_url")"
ci_result="$(python3 -c 'import json,sys; data=json.load(sys.stdin); runs=data.get("workflow_runs", []); run=next((r for r in runs if r.get("head_sha")==sys.argv[1]), None); print((run or {}).get("status", "pending")+":"+(run or {}).get("conclusion", ""))' "$target_sha" <<<"$workflow_json")"
if [[ "$ci_result" != "completed:success" ]]; then
  echo "Waiting for successful GitHub Actions validation of ${target_sha}; current result: ${ci_result}."
  exit 0
fi

echo "Deploying CI-approved main commit ${target_sha}."
MANDATO_DEPLOY_LOCK_HELD=1 bash "$app_dir/deploy/aws/remote-deploy.sh" "$target_sha"
deployed_sha="$(git -C "$app_dir" rev-parse HEAD)"
printf '%s\n' "$deployed_sha" > "${state_file}.tmp"
chmod 600 "${state_file}.tmp"
mv "${state_file}.tmp" "$state_file"
