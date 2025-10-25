-- qlearn_problem_translations 테이블 생성 및 설정
-- 번역 완료 상태를 추적하기 위한 테이블

-- qlearn_problem_translations 테이블이 이미 존재하는지 확인
DO $$ 
BEGIN
    -- 테이블이 존재하지 않는 경우에만 생성
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.tables 
        WHERE table_name = 'qlearn_problem_translations'
    ) THEN
        -- 테이블 생성
        CREATE TABLE public.qlearn_problem_translations (
            id uuid NOT NULL DEFAULT gen_random_uuid(),
            problem_id uuid NOT NULL,
            en boolean NOT NULL DEFAULT false,
            jp boolean NOT NULL DEFAULT false,
            cn boolean NOT NULL DEFAULT false,
            created_by uuid NULL DEFAULT auth.uid(),
            created_at timestamp with time zone NOT NULL DEFAULT now(),
            updated_at timestamp with time zone NOT NULL DEFAULT now(),
            CONSTRAINT qlearn_problem_translations_pkey PRIMARY KEY (id),
            CONSTRAINT qlearn_problem_translations_problem_id_unique UNIQUE (problem_id),
            CONSTRAINT qlearn_problem_translations_problem_id_fk FOREIGN KEY (problem_id) REFERENCES qlearn_problems (id) ON DELETE CASCADE
        ) TABLESPACE pg_default;
        
        RAISE NOTICE 'qlearn_problem_translations 테이블이 성공적으로 생성되었습니다.';
    ELSE
        RAISE NOTICE 'qlearn_problem_translations 테이블이 이미 존재합니다.';
    END IF;
END $$;

-- 인덱스 생성 (성능 향상을 위해)
CREATE INDEX IF NOT EXISTS idx_qpt_problem_id 
ON public.qlearn_problem_translations USING btree (problem_id) TABLESPACE pg_default;

CREATE INDEX IF NOT EXISTS idx_qpt_pending_en 
ON public.qlearn_problem_translations USING btree (problem_id) TABLESPACE pg_default
WHERE (en = false);

CREATE INDEX IF NOT EXISTS idx_qpt_pending_jp 
ON public.qlearn_problem_translations USING btree (problem_id) TABLESPACE pg_default
WHERE (jp = false);

CREATE INDEX IF NOT EXISTS idx_qpt_pending_cn 
ON public.qlearn_problem_translations USING btree (problem_id) TABLESPACE pg_default
WHERE (cn = false);

CREATE INDEX IF NOT EXISTS idx_qpt_updated_at_desc 
ON public.qlearn_problem_translations USING btree (updated_at DESC) TABLESPACE pg_default;

-- updated_at 자동 업데이트 트리거 생성
CREATE OR REPLACE FUNCTION _touch_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 트리거 생성
DROP TRIGGER IF EXISTS trg_qpt_touch_updated_at ON qlearn_problem_translations;
CREATE TRIGGER trg_qpt_touch_updated_at 
    BEFORE UPDATE ON qlearn_problem_translations 
    FOR EACH ROW 
    EXECUTE FUNCTION _touch_updated_at();

-- 테이블 구조 확인
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns 
WHERE table_name = 'qlearn_problem_translations' 
ORDER BY ordinal_position;
