-- Questions 테이블 분리: 객관식과 주관식으로 분리

-- 필요한 확장 활성화
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Enum 타입 정의 (이미 존재하는 경우 무시됨)
DO $$ BEGIN
    CREATE TYPE public.q_lang AS ENUM ('kr', 'en', 'jp');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE public.q_domain AS ENUM ('life', 'news', 'interview', 'learning_concept', 'pharma_distribution', 'job_practice');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN

    CREATE TYPE public.q_difficulty AS ENUM ('very easy', 'easy', 'normal', 'hard', 'very hard');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- 1. 객관식 문제 테이블 (questions_multiple_choice)
-- onboarding_problems 테이블 구조를 참조하여 생성
CREATE TABLE public.questions_multiple_choice (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  lang public.q_lang NOT NULL,
  category public.q_domain NOT NULL,
  problem_title text NOT NULL,
  difficulty public.q_difficulty NOT NULL,
  estimated_time text NOT NULL DEFAULT '3분 이내'::text,
  scenario text NOT NULL,
  steps jsonb NOT NULL,
  created_by uuid NULL DEFAULT auth.uid(),
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  updated_at timestamp with time zone NOT NULL DEFAULT now(),
  image_url text NULL,
  active boolean NOT NULL DEFAULT true,
  topic_summary text NULL,
  CONSTRAINT questions_multiple_choice_pkey PRIMARY KEY (id)
) TABLESPACE pg_default;

-- 객관식 테이블 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_questions_multiple_choice_lang 
ON public.questions_multiple_choice USING btree (lang) TABLESPACE pg_default;

CREATE INDEX IF NOT EXISTS idx_questions_multiple_choice_category 
ON public.questions_multiple_choice USING btree (category) TABLESPACE pg_default;

CREATE INDEX IF NOT EXISTS idx_questions_multiple_choice_difficulty 
ON public.questions_multiple_choice USING btree (difficulty) TABLESPACE pg_default;

CREATE INDEX IF NOT EXISTS idx_questions_multiple_choice_created_at 
ON public.questions_multiple_choice USING btree (created_at DESC) TABLESPACE pg_default;

-- 텍스트 검색을 위한 인덱스 (pg_trgm 확장이 필요한 경우)
-- CREATE INDEX IF NOT EXISTS idx_questions_multiple_choice_title_trgm 
-- ON public.questions_multiple_choice USING gin (problem_title gin_trgm_ops) TABLESPACE pg_default;

-- 대안: 일반적인 텍스트 인덱스
CREATE INDEX IF NOT EXISTS idx_questions_multiple_choice_title_text 
ON public.questions_multiple_choice USING btree (problem_title) TABLESPACE pg_default;

CREATE INDEX IF NOT EXISTS idx_questions_multiple_choice_lang_cat_diff_created 
ON public.questions_multiple_choice USING btree (lang, category, difficulty, created_at DESC) TABLESPACE pg_default;

-- review_done은 question_status 테이블에 있으므로 제거
-- CREATE INDEX IF NOT EXISTS idx_questions_multiple_choice_review_done 
-- ON public.questions_multiple_choice USING btree (review_done) TABLESPACE pg_default;

CREATE INDEX IF NOT EXISTS idx_questions_multiple_choice_active 
ON public.questions_multiple_choice USING btree (active) TABLESPACE pg_default;

-- 객관식 테이블 업데이트 트리거
CREATE TRIGGER trg_questions_multiple_choice_touch_updated_at 
BEFORE UPDATE ON questions_multiple_choice 
FOR EACH ROW 
EXECUTE FUNCTION _qlearn_touch_updated_at();

-- 2. 주관식 문제 테이블 (questions_subjective)
-- qlearn_problems 테이블 구조와 동일하게 생성
CREATE TABLE public.questions_subjective (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  lang public.q_lang NOT NULL,
  category public.q_domain NOT NULL,
  topic text NOT NULL,
  difficulty public.q_difficulty NOT NULL,
  time_limit text NOT NULL,
  topic_summary text NOT NULL,
  title text NOT NULL,
  scenario text NOT NULL,
  goal jsonb NOT NULL,
  first_question jsonb NOT NULL,
  requirements jsonb NOT NULL,
  constraints jsonb NOT NULL,
  guide jsonb NOT NULL,
  evaluation jsonb NOT NULL,
  task text NOT NULL,
  created_by uuid NULL DEFAULT auth.uid(),
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  updated_at timestamp with time zone NOT NULL DEFAULT now(),
  reference jsonb NULL,
  active boolean NOT NULL DEFAULT true,
  CONSTRAINT questions_subjective_pkey PRIMARY KEY (id),
  CONSTRAINT chk_questions_subjective_topic_summary_nonempty CHECK ((length(btrim(topic_summary)) > 0))
) TABLESPACE pg_default;

-- 주관식 테이블 인덱스 생성
CREATE INDEX IF NOT EXISTS questions_subjective_lang_idx 
ON public.questions_subjective USING btree (lang) TABLESPACE pg_default;

CREATE INDEX IF NOT EXISTS questions_subjective_domain_idx 
ON public.questions_subjective USING btree (category) TABLESPACE pg_default;

CREATE INDEX IF NOT EXISTS questions_subjective_difficulty_idx 
ON public.questions_subjective USING btree (difficulty) TABLESPACE pg_default;

CREATE INDEX IF NOT EXISTS questions_subjective_created_at_idx 
ON public.questions_subjective USING btree (created_at DESC) TABLESPACE pg_default;

-- review_done은 question_status 테이블에 있으므로 제거
-- CREATE INDEX IF NOT EXISTS questions_subjective_review_done_idx 
-- ON public.questions_subjective USING btree (review_done) TABLESPACE pg_default;

CREATE INDEX IF NOT EXISTS questions_subjective_active_idx 
ON public.questions_subjective USING btree (active) TABLESPACE pg_default;

-- is_en 필드가 제거되어 인덱스도 제거
-- CREATE INDEX IF NOT EXISTS questions_subjective_is_en_idx 
-- ON public.questions_subjective USING btree (is_en) TABLESPACE pg_default;

-- 주관식 테이블 업데이트 트리거
CREATE TRIGGER trg_questions_subjective_touch_updated_at 
BEFORE UPDATE ON questions_subjective 
FOR EACH ROW 
EXECUTE FUNCTION _qlearn_touch_updated_at();

-- 3. 문제 상태 추적 테이블 (question_status)
-- 문제 ID 기준으로 리뷰 완료 여부, 번역 여부 등을 추적
CREATE TABLE public.question_status (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  question_id uuid NOT NULL,
  question_type text NOT NULL CHECK (question_type IN ('multiple_choice', 'subjective')),
  review_done boolean NOT NULL DEFAULT false,
  translation_done boolean NOT NULL DEFAULT false,
  ai_generated boolean NOT NULL DEFAULT false,
  template_id uuid NULL,
  created_by uuid NULL DEFAULT auth.uid(),
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  updated_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT question_status_pkey PRIMARY KEY (id),
  CONSTRAINT question_status_question_id_unique UNIQUE (question_id)
) TABLESPACE pg_default;

-- 문제 상태 테이블 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_question_status_question_id 
ON public.question_status USING btree (question_id) TABLESPACE pg_default;

CREATE INDEX IF NOT EXISTS idx_question_status_question_type 
ON public.question_status USING btree (question_type) TABLESPACE pg_default;

CREATE INDEX IF NOT EXISTS idx_question_status_review_done 
ON public.question_status USING btree (review_done) TABLESPACE pg_default;

CREATE INDEX IF NOT EXISTS idx_question_status_translation_done 
ON public.question_status USING btree (translation_done) TABLESPACE pg_default;

-- 문제 상태 테이블 업데이트 트리거
CREATE TRIGGER trg_question_status_touch_updated_at 
BEFORE UPDATE ON question_status 
FOR EACH ROW 
EXECUTE FUNCTION _qlearn_touch_updated_at();

-- 4. RLS (Row Level Security) 정책 설정
-- 객관식 테이블 RLS
ALTER TABLE public.questions_multiple_choice ENABLE ROW LEVEL SECURITY;

CREATE POLICY "questions_multiple_choice_select_policy" ON public.questions_multiple_choice
FOR SELECT USING (true);

CREATE POLICY "questions_multiple_choice_insert_policy" ON public.questions_multiple_choice
FOR INSERT WITH CHECK (true);

CREATE POLICY "questions_multiple_choice_update_policy" ON public.questions_multiple_choice
FOR UPDATE USING (true);

CREATE POLICY "questions_multiple_choice_delete_policy" ON public.questions_multiple_choice
FOR DELETE USING (true);

-- 주관식 테이블 RLS
ALTER TABLE public.questions_subjective ENABLE ROW LEVEL SECURITY;

CREATE POLICY "questions_subjective_select_policy" ON public.questions_subjective
FOR SELECT USING (true);

CREATE POLICY "questions_subjective_insert_policy" ON public.questions_subjective
FOR INSERT WITH CHECK (true);

CREATE POLICY "questions_subjective_update_policy" ON public.questions_subjective
FOR UPDATE USING (true);

CREATE POLICY "questions_subjective_delete_policy" ON public.questions_subjective
FOR DELETE USING (true);

-- 5. 문제 상태 테이블 RLS 정책 설정
ALTER TABLE public.question_status ENABLE ROW LEVEL SECURITY;

CREATE POLICY "question_status_select_policy" ON public.question_status
FOR SELECT USING (true);

CREATE POLICY "question_status_insert_policy" ON public.question_status
FOR INSERT WITH CHECK (true);

CREATE POLICY "question_status_update_policy" ON public.question_status
FOR UPDATE USING (true);

CREATE POLICY "question_status_delete_policy" ON public.question_status
FOR DELETE USING (true);

-- 6. 새로운 테이블들에 대한 통계 정보 업데이트
ANALYZE public.questions_multiple_choice;
ANALYZE public.questions_subjective;
ANALYZE public.question_status;
