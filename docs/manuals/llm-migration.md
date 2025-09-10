# LLM 마이그레이션 가이드 (OpenRouter ↔ Vertex, 로컬)

## 개요
- 현재 기본: OpenRouter를 통한 Google Gemma 3 12B 실시간 스트리밍
- 목표: 프로바이더 전환이 쉬운 추상화와 환경 구성 제공

## 사전 준비
- 환경변수(.env)
  - OPENROUTER_API_KEY
  - LLM_PROVIDER=openrouter|vertex|local
  - NEXT_PUBLIC_API_URL (프론트엔드에서 백엔드 접속 시)
- 네트워크
  - CORS, 프록시(Next.js rewrites), 방화벽/사설망 확인

## 전환 절차
1) 코드 레벨 추상화 확인
- backend/app/services/llm_service.py에서 프로바이더별 호출 분기
- 공통 인터페이스: generate_answer / generate_streaming_answer

2) OpenRouter → Vertex
- 환경변경: LLM_PROVIDER=vertex, Vertex 자격증명 설정(GCP SA JSON 또는 ADC)
- 엔드포인트/모델명 매핑: Gemma 계열 또는 등가 모델 선택
- 응답 포맷 차이 조정: 스트리밍 청크 구조 통일

3) OpenRouter → 로컬(Ollama 등)
- 로컬 엔진 설치 및 모델 pull
- 백엔드 네트워크 접근 허용(docker-compose 네트워크에서 접근)
- LLM_PROVIDER=local, 엔드포인트 URL 설정

## 점진적 전환 전략
- 카나리 릴리즈: 트래픽 일부(예: 5%)를 신규 프로바이더로 라우팅
- A/B 실험: 품질/지연/비용 수집 후 가중치 조정
- 롤백: 환경변수만 되돌려도 복구되도록 유지

## 체크리스트
- [ ] .env 적용 및 재시작 완료
- [ ] SSE 스트리밍 정상 (첫 청크/완료 이벤트 포함)
- [ ] 에러/타임아웃 처리
- [ ] 비용/지연/품질 로그 수집

## 트러블슈팅
- 401 Unauthorized: API Key/ADC 확인
- CORS: 프론트 도메인/포트와 백엔드 CORS 허용
- 스트리밍 끊김: 프록시/로드밸런서 타임아웃, 헤더 설정(Cache-Control, no-buffer)
