# Company-on API 문서

## 📋 개요

Company-on은 RAG 기반 AI 챗봇을 위한 문서 관리 및 채팅 시스템입니다. 이 문서는 모든 API 엔드포인트의 사용법과 예제를 제공합니다.

**Base URL**: `http://localhost:8000/api/v1`

---

## 🔧 문서 관리 API

### 1. 문서 업로드 시작

**POST** `/documents/upload`

문서 업로드를 위한 사전 서명된 URL을 생성합니다.

#### 요청 본문
```json
{
  "filename": "example.pdf",
  "size": 1024000,
  "content_type": "application/pdf"
}
```

#### 응답
```json
{
  "upload_id": "550e8400-e29b-41d4-a716-446655440000",
  "upload_url": "http://localhost:9000/company-on-documents/uploads/550e8400-e29b-41d4-a716-446655440000/example.pdf?X-Amz-Algorithm=...",
  "expires_at": "2024-01-15T10:30:00Z"
}
```

#### 사용 예제
```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "example.pdf",
    "size": 1024000,
    "content_type": "application/pdf"
  }'
```

---

### 2. 문서 업로드 완료

**PUT** `/documents/upload/{upload_id}`

업로드된 파일을 데이터베이스에 등록하고 처리 작업을 시작합니다.

#### 경로 매개변수
- `upload_id`: 업로드 ID (문자열)

#### 요청 본문
```json
{
  "metadata": {
    "filename": "example.pdf",
    "size": 1024000,
    "content_type": "application/pdf",
    "author": "John Doe",
    "description": "Sample document"
  }
}
```

#### 응답
```json
{
  "document_id": 1,
  "status": "processing"
}
```

#### 사용 예제
```bash
curl -X PUT "http://localhost:8000/api/v1/documents/upload/550e8400-e29b-41d4-a716-446655440000" \
  -H "Content-Type: application/json" \
  -d '{
    "metadata": {
      "filename": "example.pdf",
      "size": 1024000,
      "content_type": "application/pdf"
    }
  }'
```

---

### 3. 문서 목록 조회

**GET** `/documents`

문서 목록을 페이지네이션으로 조회합니다.

#### 쿼리 매개변수
- `page`: 페이지 번호 (기본값: 1)
- `limit`: 페이지당 항목 수 (기본값: 20, 최대: 100)
- `status`: 문서 상태 필터 (`processing`, `completed`, `failed`)
- `search`: 검색어 (파일명 또는 제목)

#### 응답
```json
{
  "documents": [
    {
      "id": 1,
      "title": "example",
      "filename": "example.pdf",
      "file_size": 1024000,
      "content_type": "application/pdf",
      "status": "completed",
      "document_metadata": {
        "author": "John Doe",
        "description": "Sample document"
      },
      "created_at": "2024-01-15T10:00:00Z",
      "updated_at": "2024-01-15T10:05:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "limit": 20
}
```

#### 사용 예제
```bash
# 모든 문서 조회
curl "http://localhost:8000/api/v1/documents"

# 상태별 필터링
curl "http://localhost:8000/api/v1/documents?status=completed"

# 검색
curl "http://localhost:8000/api/v1/documents?search=example"

# 페이지네이션
curl "http://localhost:8000/api/v1/documents?page=2&limit=10"
```

---

### 4. 문서 상세 조회

**GET** `/documents/{document_id}`

특정 문서의 상세 정보를 조회합니다.

#### 경로 매개변수
- `document_id`: 문서 ID (정수)

#### 응답
```json
{
  "id": 1,
  "title": "example",
  "filename": "example.pdf",
  "file_size": 1024000,
  "content_type": "application/pdf",
  "status": "completed",
  "document_metadata": {
    "author": "John Doe",
    "description": "Sample document"
  },
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T10:05:00Z"
}
```

#### 사용 예제
```bash
curl "http://localhost:8000/api/v1/documents/1"
```

---

### 5. 문서 다운로드

**GET** `/documents/{document_id}/download`

문서 다운로드를 위한 사전 서명된 URL을 생성합니다.

#### 경로 매개변수
- `document_id`: 문서 ID (정수)

#### 응답
```json
{
  "download_url": "http://localhost:9000/company-on-documents/uploads/550e8400-e29b-41d4-a716-446655440000/example.pdf?X-Amz-Algorithm=..."
}
```

#### 사용 예제
```bash
curl "http://localhost:8000/api/v1/documents/1/download"
```

---

### 6. 문서 재처리

**POST** `/documents/{document_id}/reprocess`

문서를 다시 처리합니다.

#### 경로 매개변수
- `document_id`: 문서 ID (정수)

#### 요청 본문
```json
{
  "options": {
    "chunk_size": 512,
    "overlap": 50,
    "force_reprocess": true
  }
}
```

#### 응답
```json
{
  "task_id": "reprocess_1_1705312800.123",
  "status": "queued"
}
```

#### 사용 예제
```bash
curl -X POST "http://localhost:8000/api/v1/documents/1/reprocess" \
  -H "Content-Type: application/json" \
  -d '{
    "options": {
      "chunk_size": 512,
      "overlap": 50
    }
  }'
```

---

### 7. 문서 삭제

**DELETE** `/documents/{document_id}`

문서를 삭제합니다.

#### 경로 매개변수
- `document_id`: 문서 ID (정수)

#### 응답
```json
{
  "success": true,
  "deleted_at": "2024-01-15T10:30:00Z"
}
```

#### 사용 예제
```bash
curl -X DELETE "http://localhost:8000/api/v1/documents/1"
```

---

### 8. 문서 청크 목록 조회

**GET** `/documents/{document_id}/chunks`

문서의 청크 목록을 조회합니다.

#### 경로 매개변수
- `document_id`: 문서 ID (정수)

#### 쿼리 매개변수
- `page`: 페이지 번호 (기본값: 1)
- `limit`: 페이지당 항목 수 (기본값: 20, 최대: 100)
- `search`: 검색어 (청크 내용)

#### 응답
```json
{
  "chunks": [
    {
      "id": 1,
      "document_id": 1,
      "chunk_index": 0,
      "content": "This is the first chunk of the document...",
      "chunk_metadata": {
        "page_number": 1,
        "word_count": 150
      },
      "created_at": "2024-01-15T10:05:00Z"
    }
  ],
  "total": 1
}
```

#### 사용 예제
```bash
curl "http://localhost:8000/api/v1/documents/1/chunks"
```

---

## 📊 업로드 상태 추적 API

### 1. 업로드 세션 목록 조회

**GET** `/uploads/sessions`

업로드 세션 목록을 조회합니다.

#### 쿼리 매개변수
- `page`: 페이지 번호 (기본값: 1)
- `limit`: 페이지당 항목 수 (기본값: 20, 최대: 100)
- `status`: 상태 필터 (`init`, `uploading`, `pending`, `processing`, `completed`, `failed`)

#### 응답
```json
{
  "sessions": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "filename": "example.pdf",
      "file_size": 1024000,
      "uploaded_size": 1024000,
      "content_type": "application/pdf",
      "status": "completed",
      "document_id": 1,
      "error_message": null,
      "created_at": "2024-01-15T10:00:00Z",
      "updated_at": "2024-01-15T10:05:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "limit": 20
}
```

#### 사용 예제
```bash
# 모든 세션 조회
curl "http://localhost:8000/api/v1/uploads/sessions"

# 상태별 필터링
curl "http://localhost:8000/api/v1/uploads/sessions?status=processing"
```

---

### 2. 업로드 세션 조회

**GET** `/uploads/sessions/{upload_id}`

특정 업로드 세션의 정보를 조회합니다.

#### 경로 매개변수
- `upload_id`: 업로드 ID (문자열)

#### 응답
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "example.pdf",
  "file_size": 1024000,
  "uploaded_size": 1024000,
  "content_type": "application/pdf",
  "status": "completed",
  "document_id": 1,
  "error_message": null,
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T10:05:00Z"
}
```

#### 사용 예제
```bash
curl "http://localhost:8000/api/v1/uploads/sessions/550e8400-e29b-41d4-a716-446655440000"
```

---

### 3. 업로드 진행률 조회

**GET** `/uploads/sessions/{upload_id}/progress`

업로드 진행률을 조회합니다.

#### 경로 매개변수
- `upload_id`: 업로드 ID (문자열)

#### 응답
```json
{
  "upload_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "example.pdf",
  "status": "uploading",
  "progress_percentage": 75.5,
  "uploaded_size": 773120,
  "file_size": 1024000,
  "document_id": null,
  "error_message": null,
  "updated_at": "2024-01-15T10:02:30Z"
}
```

#### 사용 예제
```bash
curl "http://localhost:8000/api/v1/uploads/sessions/550e8400-e29b-41d4-a716-446655440000/progress"
```

---

### 4. 실시간 상태 스트리밍 (SSE)

**GET** `/uploads/sessions/{upload_id}/stream`

Server-Sent Events를 통해 실시간으로 업로드 상태를 스트리밍합니다.

#### 경로 매개변수
- `upload_id`: 업로드 ID (문자열)

#### 응답 헤더
```
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
```

#### 응답 형식
```
data: {"upload_id": "550e8400-e29b-41d4-a716-446655440000", "filename": "example.pdf", "status": "uploading", "progress_percentage": 75.5, "uploaded_size": 773120, "file_size": 1024000, "document_id": null, "error_message": null, "updated_at": "2024-01-15T10:02:30Z"}

data: {"upload_id": "550e8400-e29b-41d4-a716-446655440000", "filename": "example.pdf", "status": "completed", "progress_percentage": 100.0, "uploaded_size": 1024000, "file_size": 1024000, "document_id": 1, "error_message": null, "updated_at": "2024-01-15T10:05:00Z"}

```

#### JavaScript 사용 예제
```javascript
const eventSource = new EventSource('/api/v1/uploads/sessions/550e8400-e29b-41d4-a716-446655440000/stream');

eventSource.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Status:', data.status);
    console.log('Progress:', data.progress_percentage + '%');
    
    // 상태별 시각적 표시
    switch(data.status) {
        case 'init':
            showStatus('초기화 중...', 'info');
            break;
        case 'uploading':
            showProgress(data.progress_percentage);
            break;
        case 'pending':
            showStatus('처리 대기 중...', 'warning');
            break;
        case 'processing':
            showStatus('처리 중...', 'info');
            break;
        case 'completed':
            showStatus('완료', 'success');
            break;
        case 'failed':
            showStatus('실패: ' + data.error_message, 'error');
            break;
    }
};

eventSource.onerror = function(event) {
    console.error('SSE connection error:', event);
    eventSource.close();
};
```

---

### 5. 업로드 상태 업데이트 (내부 API)

**PUT** `/uploads/sessions/{upload_id}/status`

업로드 상태를 업데이트합니다. (주로 내부 시스템에서 사용)

#### 경로 매개변수
- `upload_id`: 업로드 ID (문자열)

#### 요청 본문
```json
{
  "status": "processing",
  "uploaded_size": 1024000,
  "document_id": 1,
  "error_message": null
}
```

#### 응답
```json
{
  "success": true,
  "updated_at": "2024-01-15T10:05:00Z"
}
```

#### 사용 예제
```bash
curl -X PUT "http://localhost:8000/api/v1/uploads/sessions/550e8400-e29b-41d4-a716-446655440000/status" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "processing",
    "uploaded_size": 1024000,
    "document_id": 1
  }'
```

---

### 6. 업로드 세션 삭제

**DELETE** `/uploads/sessions/{upload_id}`

업로드 세션을 삭제합니다.

#### 경로 매개변수
- `upload_id`: 업로드 ID (문자열)

#### 응답
```json
{
  "success": true,
  "deleted_at": "2024-01-15T10:30:00Z"
}
```

#### 사용 예제
```bash
curl -X DELETE "http://localhost:8000/api/v1/uploads/sessions/550e8400-e29b-41d4-a716-446655440000"
```

---

## 🔍 상태 코드 및 에러 처리

### HTTP 상태 코드

- `200 OK`: 요청 성공
- `201 Created`: 리소스 생성 성공
- `400 Bad Request`: 잘못된 요청
- `404 Not Found`: 리소스를 찾을 수 없음
- `422 Unprocessable Entity`: 요청 데이터 검증 실패
- `500 Internal Server Error`: 서버 내부 오류

### 에러 응답 형식

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "field": "filename",
      "reason": "Field is required"
    }
  }
}
```

---

## 📝 업로드 상태 설명

### 상태 흐름

1. **init**: 업로드 세션 초기화
2. **uploading**: 파일 업로드 중
3. **pending**: 업로드 완료, 처리 대기
4. **processing**: 문서 처리 중 (파싱, 청킹, 임베딩)
5. **completed**: 처리 완료
6. **failed**: 처리 실패

### 상태별 시각화 가이드

- **init**: 회색 점 또는 "초기화 중..." 텍스트
- **uploading**: 진행률 바 (0-100%)
- **pending**: 노란색 점 또는 "대기 중..." 텍스트
- **processing**: 파란색 점 또는 "처리 중..." 텍스트
- **completed**: 녹색 점 또는 "완료" 텍스트
- **failed**: 빨간색 점 또는 "실패" 텍스트

---

## 🚀 빠른 시작 예제

### 전체 업로드 플로우

```bash
# 1. 업로드 시작
UPLOAD_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/documents/upload" \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "example.pdf",
    "size": 1024000,
    "content_type": "application/pdf"
  }')

# 2. 업로드 ID 추출
UPLOAD_ID=$(echo $UPLOAD_RESPONSE | jq -r '.upload_id')
UPLOAD_URL=$(echo $UPLOAD_RESPONSE | jq -r '.upload_url')

# 3. 파일 업로드 (MinIO)
curl -X PUT "$UPLOAD_URL" \
  -H "Content-Type: application/pdf" \
  --data-binary @example.pdf

# 4. 업로드 완료 처리
curl -X PUT "http://localhost:8000/api/v1/documents/upload/$UPLOAD_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "metadata": {
      "filename": "example.pdf",
      "size": 1024000,
      "content_type": "application/pdf"
    }
  }'

# 5. 상태 확인
curl "http://localhost:8000/api/v1/uploads/sessions/$UPLOAD_ID/progress"
```

---

## 📚 추가 리소스

- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [Server-Sent Events (SSE) 가이드](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
- [MinIO 클라이언트 가이드](https://docs.min.io/docs/minio-client-quickstart-guide.html)
