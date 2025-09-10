# Redis 학습 노트

## 개요
- 역할: 메시지 브로커(Celery), 캐시, Pub/Sub 기반 SSE 중계
- 장점: 초고속 인메모리, 다양한 자료구조, 간단한 운영

## 주요 개념
- Key-Value, TTL, Eviction(메모리 정책)
- Pub/Sub: 채널 기반 브로드캐스트
- Streams: 로그형 데이터 구조(필요 시 도입)

## Company-on 적용
- Celery Broker/Backend로 사용
- SSE Redis Service: 업로드 상태 등 실시간 이벤트 중계
- 캐싱 후보: 문서 메타/검색 결과(추후)

## 운영 팁
- persistence: AOF + RDB 혼합
- 모니터링: INFO, slowlog, keyspace hits/misses
- 보안: 비밀번호 설정, 네트워크 접근 제어

## 문제 해결
- 연결 지연/초기 실패: 컨테이너 기동 순서/재시도 로직
- 메모리 부족: maxmemory + eviction 정책 설정
- Pub/Sub 누락: 구독자 연결 상태/타임아웃 확인
