#!/bin/bash
# 触发 GitLab CI 流水线
# 用法: export GITLAB_TOKEN=xxx GITLAB_PROJECT_ID=xxx
#       ./scripts/trigger-gitlab.sh [ref] [gitlab_url]
# 示例: ./scripts/trigger-gitlab.sh main

set -euo pipefail

REF="${1:-main}"
GITLAB_URL="${GITLAB_URL}"
GITLAB_TOKEN="${GITLAB_TOKEN:?请设置 GITLAB_TOKEN 环境变量}"
GITLAB_PROJECT_ID="${GITLAB_PROJECT_ID:?请设置 GITLAB_PROJECT_ID 环境变量}"

echo "=== 触发 GitLab CI 流水线 ==="
echo "GitLab: ${GITLAB_URL}"
echo "项目 ID: ${GITLAB_PROJECT_ID}"
echo "分支: ${REF}"

curl -X POST \
    --fail \
    --silent \
    --show-error \
    -F "token=${GITLAB_TOKEN}" \
    -F "ref=${REF}" \
    "${GITLAB_URL}/api/v4/projects/${GITLAB_PROJECT_ID}/trigger/pipeline"

echo ""
echo "=== GitLab 流水线已触发 ==="
