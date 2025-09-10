#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

# 0) Check prerequisites
command -v docker >/dev/null 2>&1 || { echo "Docker is required"; exit 1; }
command -v docker compose >/dev/null 2>&1 || { echo "Docker Compose v2 is required"; exit 1; }

# 1) Infra up (postgres, redis, minio)
echo "[1/5] Bringing up infra (postgres, redis, minio)"
docker compose up -d postgres redis minio

# 2) Backend up
echo "[2/5] Bringing up backend (api, workers)"
docker compose up -d backend celery-worker celery-beat celery-flower

# 3) DB migration
echo "[3/5] Running alembic upgrade"
docker compose exec -T backend alembic upgrade head

# 4) Print service URLs
echo "[4/5] Services"
echo "- API:         http://localhost:8000"
echo "- Docs:        http://localhost:8000/docs"
echo "- Flower:      http://localhost:5555"
echo "- MinIO:       http://localhost:9001"

# 5) Frontend hint
echo "[5/5] Start frontend locally:"
echo "    cd frontend && npm install && npm run dev"
echo "Then open http://localhost:3000"
