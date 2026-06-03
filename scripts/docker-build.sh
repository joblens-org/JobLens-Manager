#!/bin/bash
# 构建 JobLens Web Manager Docker 镜像
# 用法: ./scripts/docker-build.sh [tag] [registry]
# 示例: ./scripts/docker-build.sh latest
#       ./scripts/docker-build.sh v1.0.0 ghcr.io/joblens-org/joblens-manager

set -euo pipefail

TAG="${1:-latest}"
REGISTRY="${2:-ghcr.io/joblens-org/joblens-manager}"

BACKEND_IMAGE="${REGISTRY}/backend:${TAG}"
FRONTEND_IMAGE="${REGISTRY}/frontend:${TAG}"

echo "=== 构建后端镜像: ${BACKEND_IMAGE} ==="
docker build -t "${BACKEND_IMAGE}" ./backend

echo "=== 构建前端镜像: ${FRONTEND_IMAGE} ==="
docker build -t "${FRONTEND_IMAGE}" ./frontend

echo "=== 构建完成 ==="
docker images | grep joblens
