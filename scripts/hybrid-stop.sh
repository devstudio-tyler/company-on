#!/usr/bin/env bash
set -euo pipefail

# Usage: bash scripts/hybrid-stop.sh [--all]
#  --all : 백엔드 + 인프라(postgres, redis, minio)까지 모두 중지/정리

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

ALL=${1:-}

if [ "$ALL" = "--all" ]; then
  echo "[1/2] Stopping backend & infra services"
  docker compose stop backend celery-worker celery-beat celery-flower postgres redis minio || true
  echo "[2/2] Removing containers (preserving volumes)"
  docker compose rm -f backend celery-worker celery-beat celery-flower postgres redis minio || true
  echo "✅ Stopped all services (volumes preserved)."
else
  echo "Stopping backend services only (keeping infra up)"
  docker compose stop backend celery-worker celery-beat celery-flower || true
  echo "✅ Stopped backend services. Infra is still running (postgres/redis/minio)."
  echo "  - To stop everything including infra: bash scripts/hybrid-stop.sh --all"
fi
