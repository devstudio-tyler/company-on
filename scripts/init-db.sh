#!/bin/bash
set -e

echo "🚀 데이터베이스 초기화 시작..."

# pgvector 확장 설치
echo "📦 pgvector 확장 설치 중..."
psql -U ragbot_user -d ragbot -c "CREATE EXTENSION IF NOT EXISTS vector;"

# 초기 데이터 삽입
echo "📊 초기 데이터 삽입 중..."
psql -U ragbot_user -d ragbot -c "
-- 기본 설정만 유지 (인증 및 회사 단위 필터링 제거됨)
SELECT 'Database initialized successfully' as status;
"

echo "✅ 데이터베이스 초기화 완료!"

