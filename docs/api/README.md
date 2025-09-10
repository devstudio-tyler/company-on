# API 문서

Company-on API의 사용법 및 개발자 가이드입니다.

## 📋 문서 목록

### [api.md](./api.md)
- **목적**: REST API 엔드포인트의 완전한 사용법 가이드
- **내용**:
  - 문서 관리 API (8개 엔드포인트)
  - 업로드 상태 추적 API (6개 엔드포인트)
  - SSE 실시간 스트리밍 사용법
  - 상태별 시각화 가이드
  - JavaScript 클라이언트 예제
  - 에러 처리 및 상태 코드

## 🔗 주요 API 그룹

### 문서 관리
- `POST /documents/upload` - 업로드 시작
- `PUT /documents/upload/{upload_id}` - 업로드 완료
- `GET /documents` - 문서 목록 조회
- `GET /documents/{id}` - 문서 상세 조회
- `GET /documents/{id}/download` - 문서 다운로드
- `POST /documents/{id}/reprocess` - 문서 재처리
- `DELETE /documents/{id}` - 문서 삭제
- `GET /documents/{id}/chunks` - 청크 목록 조회

### 업로드 상태 추적
- `GET /uploads/sessions` - 세션 목록
- `GET /uploads/sessions/{upload_id}` - 세션 조회
- `GET /uploads/sessions/{upload_id}/progress` - 진행률 조회
- `GET /uploads/sessions/{upload_id}/stream` - SSE 스트리밍
- `PUT /uploads/sessions/{upload_id}/status` - 상태 업데이트
- `DELETE /uploads/sessions/{upload_id}` - 세션 삭제

## 🚀 빠른 시작

```bash
# Base URL
http://localhost:8000/api/v1

# 헬스 체크
curl http://localhost:8000/health

# 문서 목록 조회
curl http://localhost:8000/api/v1/documents
```
