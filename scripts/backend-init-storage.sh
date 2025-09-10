#!/usr/bin/env bash
set -euo pipefail

# Project root detection
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

echo "[1/4] Bring up core infra (postgres, redis, minio)"
docker compose up -d postgres redis minio

# Wait for Postgres to be healthy
echo "[2/4] Waiting for Postgres to be ready..."
for i in {1..30}; do
  if docker compose exec -T postgres pg_isready -U postgres >/dev/null 2>&1; then
    echo "Postgres is ready"
    break
  fi
  sleep 1
  if [ "$i" -eq 30 ]; then
    echo "Postgres not ready in time" >&2
    exit 1
  fi
done

# Enable pgvector extension
echo "[3/4] Enable pgvector extension (if not exists)"
docker compose exec -T postgres psql -U postgres -d ragbot -c "CREATE EXTENSION IF NOT EXISTS vector;" || true

# Initialize MinIO (if helper exists)
if [ -f "$ROOT_DIR/scripts/init-minio.sh" ]; then
  echo "[4/4] Initialize MinIO buckets (helper script)"
  bash "$ROOT_DIR/scripts/init-minio.sh"
else
  echo "[4/4] Skipping MinIO init (scripts/init-minio.sh not found)"
fi

echo "\n✅ Backend storage init done. Services:"
echo "- Postgres: localhost:5432\n- Redis: localhost:6379\n- MinIO Console: http://localhost:9001"
