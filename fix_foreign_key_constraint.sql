-- qlearn_problems_i18n 테이블 완전 재생성
-- 기존 테이블 삭제 후 외래 키 제약 조건 없이 새로 생성

-- 1. 기존 테이블 완전 삭제 (모든 데이터와 제약 조건 포함)
DROP TABLE IF EXISTS public.qlearn_problems_i18n CASCADE;

-- 2. 새로운 독립적인 i18n 테이블 생성 (외래 키 제약 조건 없음)
CREATE TABLE public.qlearn_problems_i18n (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  source_problem_id uuid NOT NULL,  -- 외래 키 제약 조건 없음
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
  CONSTRAINT qlearn_problems_i18n_pkey PRIMARY KEY (id),
  CONSTRAINT uq_qlearn_problems_i18n_source_lang UNIQUE (source_problem_id, lang),
  CONSTRAINT chk_i18n_topic_summary_nonempty CHECK ((length(btrim(topic_summary)) > 0))
) TABLESPACE pg_default;

-- 4. 인덱스 생성 (성능 향상)
CREATE INDEX idx_qlearn_problems_i18n_source ON public.qlearn_problems_i18n USING btree (source_problem_id) TABLESPACE pg_default;
CREATE INDEX idx_qlearn_problems_i18n_lang ON public.qlearn_problems_i18n USING btree (lang) TABLESPACE pg_default;
CREATE INDEX idx_qlearn_problems_i18n_category ON public.qlearn_problems_i18n USING btree (category) TABLESPACE pg_default;
CREATE INDEX idx_qlearn_problems_i18n_difficulty ON public.qlearn_problems_i18n USING btree (difficulty) TABLESPACE pg_default;
CREATE INDEX idx_qlearn_problems_i18n_active ON public.qlearn_problems_i18n USING btree (active) TABLESPACE pg_default;

-- 5. RLS (Row Level Security) 정책 설정
ALTER TABLE public.qlearn_problems_i18n ENABLE ROW LEVEL SECURITY;

CREATE POLICY "qlearn_problems_i18n_select_policy" ON public.qlearn_problems_i18n
FOR SELECT USING (true);

CREATE POLICY "qlearn_problems_i18n_insert_policy" ON public.qlearn_problems_i18n
FOR INSERT WITH CHECK (true);

CREATE POLICY "qlearn_problems_i18n_update_policy" ON public.qlearn_problems_i18n
FOR UPDATE USING (true);

CREATE POLICY "qlearn_problems_i18n_delete_policy" ON public.qlearn_problems_i18n
FOR DELETE USING (true);

-- 6. 업데이트 트리거 추가
CREATE TRIGGER trg_qlearn_problems_i18n_touch_updated_at 
BEFORE UPDATE ON qlearn_problems_i18n 
FOR EACH ROW 
EXECUTE FUNCTION _qlearn_touch_updated_at();

-- 7. 테이블 통계 업데이트
ANALYZE public.qlearn_problems_i18n;
