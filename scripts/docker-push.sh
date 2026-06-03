#!/bin/bash
# 推送镜像到 GitHub Container Registry
# 用法: ./scripts/docker-push.sh [tag] [registry]
# 前置: 需先执行 docker login ghcr.io

set -euo pipefail

TAG="${1:-latest}"
REGISTRY="${2:-ghcr.io/joblens-org/joblens-manager}"

BACKEND_IMAGE="${REGISTRY}/backend:${TAG}"
FRONTEND_IMAGE="${REGISTRY}/frontend:${TAG}"

echo "=== 推送后端镜像: ${BACKEND_IMAGE} ==="
docker push "${BACKEND_IMAGE}"

echo "=== 推送前端镜像: ${FRONTEND_IMAGE} ==="
docker push "${FRONTEND_IMAGE}"

echo "=== 推送完成 ==="
