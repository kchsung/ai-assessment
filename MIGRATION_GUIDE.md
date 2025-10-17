# Questions 테이블 분리 가이드

## 개요
기존 `questions` 테이블을 `questions_multiple_choice` (객관식)와 `questions_subjective` (주관식)로 분리하여 각 문제 타입에 최적화된 구조로 변경합니다. 기존 데이터는 삭제하고 새로운 구조로 시작합니다.

## 1. 데이터베이스 스키마 변경

### 1.1 새로운 테이블 생성
`database_schema_update.sql` 파일의 SQL을 Supabase Cloud에서 실행하세요:

```sql
-- 1. 새로운 테이블들 생성
-- 2. 인덱스 생성
-- 3. RLS 정책 설정
-- 4. 문제 상태 추적 테이블 생성
```

### 1.2 기존 테이블 정리 (선택사항)
기존 questions 테이블이 있다면 삭제:

```sql
-- 기존 테이블 삭제 (주의: 데이터 손실 위험)
DROP TABLE IF EXISTS public.questions CASCADE;
```

## 2. Edge Function 배포

### 2.1 Edge Function 업데이트
`edge_function_updated.ts` 파일을 Supabase Edge Function으로 배포하세요.

### 2.2 새로운 액션들
- `save_multiple_choice_question`: 객관식 문제 저장
- `save_subjective_question`: 주관식 문제 저장
- `get_multiple_choice_questions`: 객관식 문제 조회
- `get_subjective_questions`: 주관식 문제 조회
- `update_multiple_choice_question`: 객관식 문제 업데이트
- `update_subjective_question`: 주관식 문제 업데이트
- `get_question_status`: 문제 상태 조회
- `update_question_status`: 문제 상태 업데이트

## 3. 애플리케이션 코드 변경사항

### 3.1 Edge Client (`src/services/edge_client.py`)
새로운 메서드들이 추가되었습니다:
- `save_multiple_choice_question()`
- `save_subjective_question()`
- `get_multiple_choice_questions()`
- `get_subjective_questions()`
- `update_multiple_choice_question()`
- `update_subjective_question()`
- `get_question_status()`
- `update_question_status()`

### 3.2 AI Generator (`src/services/ai_generator.py`)
문제 생성 시 객관식/주관식에 맞는 필드들이 추가되었습니다.

### 3.3 UI 탭들
- `tab_auto_generate.py`: 문제 타입에 따라 적절한 테이블에 저장
- `tab_create.py`: 문제 타입에 따라 적절한 테이블에 저장
- `tab_bank.py`: 새로운 테이블들에서 통합 조회
- `tab_review.py`: 새로운 테이블들에서 통합 조회
- `tab_dashboard.py`: 새로운 테이블들에서 통합 조회

## 4. 테이블 구조 비교

### 4.1 객관식 테이블 (`questions_multiple_choice`)
```sql
- id (uuid, PK)
- lang (q_lang)
- category (q_domain)
- problem_title (text)
- difficulty (q_difficulty)
- estimated_time (text)
- scenario (text)
- steps (jsonb)
- created_by, created_at, updated_at, image_url, active, topic_summary
```

### 4.2 주관식 테이블 (`questions_subjective`)
```sql
- id (uuid, PK)
- lang (q_lang)
- category (q_domain)
- topic (text)
- difficulty (q_difficulty)
- time_limit (text)
- topic_summary (text)
- title (text)
- scenario (text)
- goal (jsonb)
- first_question (jsonb)
- requirements (jsonb)
- constraints (jsonb)
- guide (jsonb)
- evaluation (jsonb)
- task (text)
- created_by, created_at, updated_at, reference, active
```

### 4.3 문제 상태 테이블 (`question_status`)
```sql
- id (uuid, PK)
- question_id (uuid, UNIQUE)
- question_type (text) -- 'multiple_choice' or 'subjective'
- review_done (boolean)
- translation_done (boolean)
- ai_generated (boolean)
- template_id (uuid)
- created_by, created_at, updated_at
```

## 5. 테스트 방법

### 5.1 데이터베이스 테스트
```sql
-- 객관식 문제 조회 테스트
SELECT * FROM questions_multiple_choice LIMIT 5;

-- 주관식 문제 조회 테스트
SELECT * FROM questions_subjective LIMIT 5;

-- 문제 상태 조회 테스트
SELECT * FROM question_status LIMIT 5;

-- 데이터 개수 확인
SELECT 
  (SELECT COUNT(*) FROM questions_multiple_choice) as multiple_choice_count,
  (SELECT COUNT(*) FROM questions_subjective) as subjective_count,
  (SELECT COUNT(*) FROM question_status) as status_count;
```

### 5.2 Edge Function 테스트
```bash
# 객관식 문제 저장 테스트
curl -X POST "YOUR_EDGE_FUNCTION_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "save_multiple_choice_question",
    "params": {
      "id": "test_mc_001",
      "lang": "kr",
      "category": "interview",
      "problem_title": "테스트 객관식 문제",
      "difficulty": "normal",
      "question_text": "다음 중 올바른 것은?",
      "options": ["선택지1", "선택지2", "선택지3", "선택지4"],
      "correct_answer": "선택지1"
    }
  }'

# 주관식 문제 저장 테스트
curl -X POST "YOUR_EDGE_FUNCTION_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "save_subjective_question",
    "params": {
      "id": "test_sub_001",
      "lang": "kr",
      "category": "interview",
      "topic": "테스트 주제",
      "difficulty": "normal",
      "title": "테스트 주관식 문제",
      "scenario": "테스트 시나리오",
      "goal": ["목표1", "목표2"],
      "task": "테스트 과제"
    }
  }'

# 문제 상태 조회 테스트
curl -X POST "YOUR_EDGE_FUNCTION_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "get_question_status",
    "params": {
      "question_id": "test_mc_001"
    }
  }'
```

### 5.3 애플리케이션 테스트
1. **문제 생성 테스트**: 자동 생성 탭에서 객관식/주관식 문제 생성
2. **문제 조회 테스트**: 문제 은행 탭에서 문제 목록 확인
3. **문제 검토 테스트**: 검토 탭에서 문제 상세 확인
4. **대시보드 테스트**: 대시보드에서 통계 확인

## 6. 롤백 계획

문제가 발생할 경우 롤백 방법:

### 6.1 데이터베이스 롤백
```sql
-- 기존 테이블 복원 (백업이 있는 경우)
DROP TABLE IF EXISTS questions_multiple_choice CASCADE;
DROP TABLE IF EXISTS questions_subjective CASCADE;
-- 백업에서 복원
```

### 6.2 코드 롤백
- 기존 Edge Function으로 되돌리기
- 기존 애플리케이션 코드로 되돌리기

## 7. 주의사항

1. **데이터 백업**: 마이그레이션 전 반드시 기존 데이터를 백업하세요.
2. **단계적 배포**: 개발 환경에서 먼저 테스트한 후 프로덕션에 배포하세요.
3. **모니터링**: 배포 후 데이터 무결성과 애플리케이션 동작을 모니터링하세요.
4. **성능 테스트**: 새로운 테이블 구조의 성능을 테스트하세요.

## 8. 문제 해결

### 8.1 일반적인 문제들
- **JSON 파싱 오류**: Edge Function에서 JSON 필드 처리 확인
- **권한 오류**: RLS 정책 설정 확인
- **인덱스 오류**: 인덱스 생성 상태 확인

### 8.2 로그 확인
- Supabase Edge Function 로그
- 애플리케이션 콘솔 로그
- 데이터베이스 쿼리 로그

## 9. 성능 최적화

### 9.1 인덱스 최적화
- 자주 사용되는 필터 조건에 대한 인덱스 추가
- 복합 인덱스 활용

### 9.2 쿼리 최적화
- 불필요한 데이터 조회 최소화
- 페이지네이션 구현

## 10. 향후 개선사항

1. **통합 뷰**: 두 테이블을 통합하는 뷰 생성
2. **자동 마이그레이션**: 스크립트를 통한 자동 마이그레이션
3. **모니터링**: 테이블 분리 효과 모니터링
4. **성능 튜닝**: 사용 패턴에 따른 성능 최적화
