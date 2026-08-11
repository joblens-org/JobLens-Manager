#!/bin/bash
# 触发下游 GitLab CI 部署流水线
#
# 用法:
#   export GITLAB_URL=https://gitlab.example.com
#   export GITLAB_TOKEN=xxx              # 触发令牌 (trigger token)
#   export GITLAB_PROJECT_ID=123         # 部署项目 ID
#   # 需要透传给部署流水线的 CI/CD 变量, 每行一个 KEY=VALUE:
#   export TRIGGER_VARS=$'DEPLOY_ENV=dev\nSTACK=management'
#   ./scripts/trigger-gitlab.sh [ref]
#
# 兼容旧用法: 若设置了 LABELS 且未设置 TRIGGER_VARS, 则等价于 TRIGGER_VARS="LABELS=<值>"

set -euo pipefail

REF="${1:-main}"
GITLAB_URL="${GITLAB_URL:?请设置 GITLAB_URL 环境变量}"
GITLAB_TOKEN="${GITLAB_TOKEN:?请设置 GITLAB_TOKEN 环境变量}"
GITLAB_PROJECT_ID="${GITLAB_PROJECT_ID:?请设置 GITLAB_PROJECT_ID 环境变量}"

TRIGGER_VARS="${TRIGGER_VARS:-}"
if [ -z "${TRIGGER_VARS}" ] && [ -n "${LABELS:-}" ]; then
  TRIGGER_VARS="LABELS=${LABELS}"
fi

curl_args=(
  -X POST
  --fail
  --silent
  -F "token=${GITLAB_TOKEN}"
  -F "ref=${REF}"
)

if [ -n "${TRIGGER_VARS}" ]; then
  while IFS= read -r line || [ -n "${line}" ]; do
    line="${line#"${line%%[![:space:]]*}"}"
    line="${line%"${line##*[![:space:]]}"}"
    [ -z "${line}" ] && continue
    case "${line}" in \#*) continue ;; esac

    key="${line%%=*}"
    value="${line#*=}"
    if [ "${key}" = "${line}" ]; then
      continue
    fi
    if [ "${key}" = "DEPLOY_ENV" ] || [ "${key}" = "STACK" ]; then
      echo "${key}=${value}"
    fi
    curl_args+=(-F "variables[${key}]=${value}")
  done <<< "${TRIGGER_VARS}"
fi

curl "${curl_args[@]}" \
  "${GITLAB_URL}/api/v4/projects/${GITLAB_PROJECT_ID}/trigger/pipeline" \
  >/dev/null
