#!/bin/bash
set -e

echo "🚀 RAGbot 인프라 설정 시작..."

# Docker가 실행 중인지 확인
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker가 실행되지 않았습니다. Docker를 시작해주세요."
    exit 1
fi

# Docker Compose 파일 확인
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ docker-compose.yml 파일을 찾을 수 없습니다."
    exit 1
fi

# 환경 변수 파일 확인
if [ ! -f ".env" ]; then
    echo "⚠️  .env 파일이 없습니다. .env.example을 복사합니다."
    cp .env.example .env
    echo "📝 .env 파일을 확인하고 필요한 API 키를 설정해주세요."
fi

# Docker 컨테이너 빌드 및 시작
echo "📦 Docker 컨테이너 빌드 중..."
docker-compose build

echo "🔄 서비스 시작 중..."
docker-compose up -d

# 서비스 상태 확인
echo "⏳ 서비스 시작 대기 중..."
sleep 30

# 헬스체크
echo "🏥 서비스 상태 확인 중..."
echo "  - PostgreSQL: $(docker-compose exec -T postgres pg_isready -U ragbot_user -d ragbot && echo '✅' || echo '❌')"
echo "  - Redis: $(docker-compose exec -T redis redis-cli ping && echo '✅' || echo '❌')"
echo "  - MinIO: $(curl -f http://localhost:9000/minio/health/live > /dev/null 2>&1 && echo '✅' || echo '❌')"

echo ""
echo "✅ 인프라 설정 완료!"
echo "📊 서비스 접속 정보:"
echo "  - 프론트엔드: http://localhost:3000"
echo "  - 백엔드 API: http://localhost:8000"
echo "  - MinIO 콘솔: http://localhost:9001 (minioadmin/minioadmin123)"
echo "  - 데이터베이스: localhost:5432 (ragbot_user/ragbot_password)"
echo ""
echo "🔧 유용한 명령어:"
echo "  - 서비스 상태 확인: docker-compose ps"
echo "  - 로그 확인: docker-compose logs [service_name]"
echo "  - 서비스 재시작: docker-compose restart [service_name]"
echo "  - 서비스 중지: docker-compose down"

