# 파티셔닝 확장 방안

## 🎯 **파티셔닝 적용 시점**

### **현재 상태 (MVP)**
- 파티셔닝 미적용
- 단순한 테이블 구조
- 개발 및 유지보수 용이성 우선

### **파티셔닝 적용 필요 시점**
```
다음 상황에서 파티셔닝 고려:
1. 채팅 메시지가 100만 건 이상
2. 검색 응답 시간이 1초 이상
3. 데이터베이스 크기가 10GB 이상
4. 월별 데이터 증가량이 10만 건 이상
```

---

## 📊 **파티셔닝 전략**

### **1. 시간 기반 파티셔닝 (추천)**

#### **월별 파티셔닝**
```sql
-- 메인 테이블 (파티션 테이블)
CREATE TABLE chat_messages (
    id BIGSERIAL,
    session_id BIGINT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);

-- 월별 파티션 생성
CREATE TABLE chat_messages_2024_01 PARTITION OF chat_messages
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE chat_messages_2024_02 PARTITION OF chat_messages
FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

-- 자동 파티션 생성 함수
CREATE OR REPLACE FUNCTION create_monthly_partition(table_name text, start_date date)
RETURNS void AS $$
DECLARE
    partition_name text;
    end_date date;
BEGIN
    partition_name := table_name || '_' || to_char(start_date, 'YYYY_MM');
    end_date := start_date + interval '1 month';
    
    EXECUTE format('CREATE TABLE %I PARTITION OF %I FOR VALUES FROM (%L) TO (%L)',
                   partition_name, table_name, start_date, end_date);
END;
$$ LANGUAGE plpgsql;
```

#### **세션 테이블 파티셔닝**
```sql
-- 세션 테이블도 시간 기반 파티셔닝
CREATE TABLE chat_sessions (
    id BIGSERIAL,
    client_id UUID NOT NULL,
    title TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);

-- 월별 파티션 생성
CREATE TABLE chat_sessions_2024_01 PARTITION OF chat_sessions
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

### **2. 사용자 기반 파티셔닝 (대안)**

#### **Client ID 기반 파티셔닝**
```sql
-- 해시 기반 파티셔닝
CREATE TABLE chat_sessions (
    id BIGSERIAL,
    client_id UUID NOT NULL,
    title TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (id, client_id)
) PARTITION BY HASH (client_id);

-- 파티션 생성 (4개 파티션)
CREATE TABLE chat_sessions_p0 PARTITION OF chat_sessions
FOR VALUES WITH (modulus 4, remainder 0);

CREATE TABLE chat_sessions_p1 PARTITION OF chat_sessions
FOR VALUES WITH (modulus 4, remainder 1);

CREATE TABLE chat_sessions_p2 PARTITION OF chat_sessions
FOR VALUES WITH (modulus 4, remainder 2);

CREATE TABLE chat_sessions_p3 PARTITION OF chat_sessions
FOR VALUES WITH (modulus 4, remainder 3);
```

---

## 🔧 **파티셔닝 구현 단계**

### **1단계: 기존 테이블 백업**
```sql
-- 기존 데이터 백업
CREATE TABLE chat_messages_backup AS SELECT * FROM chat_messages;
CREATE TABLE chat_sessions_backup AS SELECT * FROM chat_sessions;
```

### **2단계: 파티션 테이블 생성**
```sql
-- 파티션 테이블로 재생성
DROP TABLE chat_messages CASCADE;
CREATE TABLE chat_messages (
    id BIGSERIAL,
    session_id BIGINT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);
```

### **3단계: 데이터 마이그레이션**
```sql
-- 백업 데이터를 파티션 테이블로 이동
INSERT INTO chat_messages SELECT * FROM chat_messages_backup;
```

### **4단계: 인덱스 재생성**
```sql
-- 파티션별 인덱스 생성
CREATE INDEX ON chat_messages_2024_01 (session_id, role, created_at);
CREATE INDEX ON chat_messages_2024_02 (session_id, role, created_at);
```

---

## 📈 **성능 모니터링**

### **파티셔닝 효과 측정**
```sql
-- 쿼리 성능 비교
EXPLAIN (ANALYZE, BUFFERS) 
SELECT * FROM chat_messages 
WHERE created_at >= '2024-01-01' 
AND created_at < '2024-02-01';

-- 파티션별 통계
SELECT 
    schemaname,
    tablename,
    n_tup_ins,
    n_tup_upd,
    n_tup_del,
    n_live_tup,
    n_dead_tup
FROM pg_stat_user_tables 
WHERE tablename LIKE 'chat_messages_%';
```

### **자동 파티션 관리**
```sql
-- 월별 파티션 자동 생성 스크립트
CREATE OR REPLACE FUNCTION auto_create_partitions()
RETURNS void AS $$
DECLARE
    current_month date;
    next_month date;
    partition_name text;
BEGIN
    current_month := date_trunc('month', CURRENT_DATE);
    next_month := current_month + interval '1 month';
    partition_name := 'chat_messages_' || to_char(current_month, 'YYYY_MM');
    
    -- 파티션이 없으면 생성
    IF NOT EXISTS (
        SELECT 1 FROM pg_tables 
        WHERE tablename = partition_name
    ) THEN
        EXECUTE format('CREATE TABLE %I PARTITION OF chat_messages FOR VALUES FROM (%L) TO (%L)',
                       partition_name, current_month, next_month);
    END IF;
END;
$$ LANGUAGE plpgsql;
```

---

## 🚀 **확장 시나리오**

### **시나리오 1: 대용량 데이터**
```
상황: 월별 100만 건 이상 메시지
해결: 월별 파티셔닝 + 인덱스 최적화
```

### **시나리오 2: 다중 사용자**
```
상황: 수천 명의 동시 사용자
해결: Client ID 기반 파티셔닝
```

### **시나리오 3: 장기 보관**
```
상황: 1년 이상 데이터 보관
해결: 연도별 파티셔닝 + 아카이브
```

---

## 📋 **구현 체크리스트**

### **파티셔닝 적용 전**
- [ ] 현재 테이블 크기 측정
- [ ] 쿼리 성능 분석
- [ ] 백업 전략 수립
- [ ] 롤백 계획 준비

### **파티셔닝 적용 중**
- [ ] 기존 데이터 백업
- [ ] 파티션 테이블 생성
- [ ] 데이터 마이그레이션
- [ ] 인덱스 재생성
- [ ] 애플리케이션 코드 수정

### **파티셔닝 적용 후**
- [ ] 성능 모니터링
- [ ] 자동 파티션 관리 설정
- [ ] 백업/복구 테스트
- [ ] 문서화 업데이트

---

## 💡 **주의사항**

1. **데이터 손실 위험**: 마이그레이션 중 데이터 손실 가능성
2. **애플리케이션 수정**: 파티션 키 관련 쿼리 수정 필요
3. **관리 복잡도**: 파티션별 인덱스, 통계 관리 필요
4. **백업 복잡도**: 파티션별 백업 전략 필요

**파티셔닝은 성능 문제가 명확히 발생했을 때 신중하게 적용하는 것이 좋습니다.**
