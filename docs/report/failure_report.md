- MinIO 인증 문제에서 Cursor AI가 무한 루프를 돌았음 (20분 소요)
    - MinIO 인증 과정에 대한 코드 위치와 MInIO에 대한 기본적 지식을 md파일로 작성하게 함
    - 해당 부분을 읽고 문제가 되는 것 같은 부분 판단(환경 변수가 변경되지 않는 문제)
    - 코드 내 잘못된 비밀번호(e.g. "minadmin123")를 찾아 위치들을 찾고 해당 부분이 잘못된 것 아닌지 다시 질의
    - 해당 부분을 수정하고 코드 정상화

- SSE Redis 구독 문제로 백엔드 시작 지연 (15분 소요)
    - Redis 연결은 정상이지만 SSE 서비스의 비동기 처리에서 무한 루프 발생
    - `_handle_redis_messages()` 함수에 `await asyncio.sleep(0.1)` 추가로 해결
    - 백엔드 시작 시 Redis 구독이 블로킹하는 문제 해결

- Celery 워커 예외 처리 문제 (10분 소요)
    - Redis 백엔드에서 `exc_type` 키 누락으로 인한 `ValueError` 발생
    - `task_ignore_result=True` 설정으로 결과 저장 비활성화하여 해결
    - 비동기 함수 호출 문제도 함께 해결