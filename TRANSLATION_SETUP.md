# 제미나이 번역 기능 설정 가이드

## 개요
제미나이를 사용하여 QLearn 문제를 한국어에서 영어로 자동 번역하는 기능입니다.

## 설정 단계

### 1. Supabase 데이터베이스 설정

먼저 `qlearn_problems_en` 테이블을 생성해야 합니다. Supabase SQL Editor에서 다음 SQL을 실행하세요:

```sql
-- qlearn_problems_en 테이블 생성 (번역된 문제 저장)
CREATE TABLE IF NOT EXISTS qlearn_problems_en (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lang TEXT NOT NULL DEFAULT 'en',
    category TEXT,
    topic TEXT,
    difficulty q_difficulty,
    time_limit TEXT,
    topic_summary TEXT,
    title TEXT NOT NULL,
    scenario TEXT,
    goal JSONB,
    first_question JSONB,
    requirements JSONB,
    constraints JSONB,
    guide JSONB,
    evaluation JSONB,
    task TEXT,
    created_by TEXT DEFAULT 'translation_service',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    reference JSONB,
    active BOOLEAN DEFAULT TRUE,
    is_en BOOLEAN DEFAULT TRUE,
    original_problem_id UUID REFERENCES qlearn_problems(id)
);

-- qlearn_problems 테이블에 is_en 컬럼 추가 (이미 없는 경우)
ALTER TABLE qlearn_problems 
ADD COLUMN IF NOT EXISTS is_en BOOLEAN DEFAULT FALSE;

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_qlearn_problems_en_category ON qlearn_problems_en(category);
CREATE INDEX IF NOT EXISTS idx_qlearn_problems_en_difficulty ON qlearn_problems_en(difficulty);
CREATE INDEX IF NOT EXISTS idx_qlearn_problems_en_original_id ON qlearn_problems_en(original_problem_id);
CREATE INDEX IF NOT EXISTS idx_qlearn_problems_is_en ON qlearn_problems(is_en);
```

### 2. Edge Function 업데이트

`edge_function_updated.ts` 파일을 다음과 같이 수정하세요:

#### 2-1. Action 케이스 추가

파일의 `switch (action)` 블록 안에 다음 케이스들을 추가하세요 (약 54-56번째 줄 근처):

```typescript
      case 'update_question_review_done':
        return await updateQuestionReviewDone(supabaseClient, params);
      // 번역 관련 액션들 추가
      case 'save_qlearn_problem_en':
        return await saveQlearnProblemEn(supabaseClient, params);
      case 'get_qlearn_problems_en':
        return await getQlearnProblemsEn(supabaseClient, params);
      case 'update_qlearn_problem_is_en':
        return await updateQlearnProblemIsEn(supabaseClient, params);
      default:
```

#### 2-2. 기존 getQlearnProblems 함수 수정

`getQlearnProblems` 함수의 필터 적용 부분에 `is_en` 필터를 추가하세요 (약 232-238번째 줄 근처):

```typescript
    // 필터 적용
    if (filters.id) query = query.eq('id', filters.id);
    if (filters.domain) query = query.eq('domain', filters.domain);  // category에서 domain으로 변경
    if (filters.difficulty) query = query.eq('difficulty', filters.difficulty);
    if (filters.topic) query = query.eq('topic', filters.topic);
    if (filters.active !== undefined) query = query.eq('active', filters.active);
    if (filters.lang) query = query.eq('lang', filters.lang);
    if (filters.is_en !== undefined) {
      if (filters.is_en === false) {
        // false인 경우: is_en이 false이거나 null인 경우 모두 포함
        query = query.or('is_en.is.null,is_en.eq.false');
      } else if (filters.is_en === true) {
        // true인 경우: is_en이 정확히 true인 경우만
        query = query.eq('is_en', true);
      } else {
        query = query.eq('is_en', filters.is_en);
      }
    }
```

#### 2-3. 번역 함수들 추가

파일의 끝 부분 (약 988번째 줄 이후)에 다음 함수들을 추가하세요:

```typescript
// 번역 관련 함수들

// qlearn_problems_en 테이블에 번역된 문제 저장
async function saveQlearnProblemEn(supabaseClient, params) {
  try {
    console.log('Saving translated qlearn_problem to qlearn_problems_en table');
    console.log('Received params keys:', Object.keys(params));
    
    const cleanValue = (value) => {
      if (value === null || value === undefined || value === '') {
        return null;
      }
      if (typeof value === 'string' && value.trim() === '') {
        return null;
      }
      return value;
    };
    
    const problemData = {
      lang: cleanValue(params.lang) || 'en',
      category: cleanValue(params.category),
      topic: cleanValue(params.topic),
      difficulty: cleanValue(params.difficulty),
      time_limit: cleanValue(params.time_limit),
      topic_summary: cleanValue(params.topic_summary),
      title: cleanValue(params.title),
      scenario: cleanValue(params.scenario),
      goal: params.goal,
      first_question: params.first_question,
      requirements: params.requirements,
      constraints: params.constraints,
      guide: params.guide,
      evaluation: params.evaluation,
      task: cleanValue(params.task),
      created_by: cleanValue(params.created_by) || 'translation_service',
      reference: params.reference,
      active: params.active !== undefined ? params.active : true,
      is_en: true,
      original_problem_id: cleanValue(params.original_problem_id)
    };

    const { data, error } = await supabaseClient
      .from('qlearn_problems_en')
      .insert([problemData])
      .select();

    if (error) {
      console.error('Supabase insert error:', error);
      throw error;
    }

    return new Response(JSON.stringify({
      ok: true,
      data: data
    }), {
      headers: {
        ...corsHeaders,
        'Content-Type': 'application/json'
      }
    });
  } catch (error) {
    console.error('Error saving translated problem:', error);
    return new Response(JSON.stringify({
      ok: false,
      error: error.message
    }), {
      status: 500,
      headers: {
        ...corsHeaders,
        'Content-Type': 'application/json'
      }
    });
  }
}

// qlearn_problems_en 테이블에서 번역된 문제 조회
async function getQlearnProblemsEn(supabaseClient, filters = {}) {
  try {
    console.log('Getting qlearn_problems_en with filters:', filters);
    
    let query = supabaseClient.from('qlearn_problems_en').select('*');
    
    if (filters.id) query = query.eq('id', filters.id);
    if (filters.category) query = query.eq('category', filters.category);
    if (filters.difficulty) query = query.eq('difficulty', filters.difficulty);
    if (filters.topic) query = query.eq('topic', filters.topic);
    if (filters.active !== undefined) query = query.eq('active', filters.active);
    if (filters.lang) query = query.eq('lang', filters.lang);
    if (filters.original_problem_id) query = query.eq('original_problem_id', filters.original_problem_id);

    const { data, error } = await query.order('created_at', {
      ascending: false
    });

    if (error) {
      console.error('Supabase select error:', error);
      throw error;
    }

    const transformedData = (data || []).map(r => {
      const safeJsonParse = (jsonString, defaultValue) => {
        if (!jsonString) return defaultValue;
        try {
          return JSON.parse(jsonString);
        } catch (error) {
          const preview = typeof jsonString === 'string' ? jsonString.substring(0, 50) : String(jsonString).substring(0, 50);
          console.warn(`JSON 파싱 오류 (${preview}...):`, error.message);
          if (Array.isArray(defaultValue)) {
            return [jsonString];
          } else if (typeof defaultValue === 'object' && defaultValue !== null) {
            return { raw: jsonString };
          }
          return jsonString;
        }
      };

      return {
        id: r.id,
        lang: r.lang,
        category: r.category,
        topic: r.topic,
        difficulty: r.difficulty,
        time_limit: r.time_limit,
        topic_summary: r.topic_summary,
        title: r.title,
        scenario: r.scenario,
        goal: safeJsonParse(r.goal, []),
        first_question: safeJsonParse(r.first_question, []),
        requirements: safeJsonParse(r.requirements, []),
        constraints: safeJsonParse(r.constraints, []),
        guide: safeJsonParse(r.guide, {}),
        evaluation: safeJsonParse(r.evaluation, []),
        task: r.task,
        created_by: r.created_by,
        created_at: r.created_at,
        updated_at: r.updated_at,
        reference: safeJsonParse(r.reference, {}),
        active: r.active,
        is_en: r.is_en,
        original_problem_id: r.original_problem_id
      };
    });

    return new Response(JSON.stringify({
      ok: true,
      data: transformedData
    }), {
      headers: {
        ...corsHeaders,
        'Content-Type': 'application/json'
      }
    });
  } catch (error) {
    console.error('Error getting translated problems:', error);
    return new Response(JSON.stringify({
      ok: false,
      error: error.message
    }), {
      status: 500,
      headers: {
        ...corsHeaders,
        'Content-Type': 'application/json'
      }
    });
  }
}

// qlearn_problems 테이블의 is_en 필드 업데이트
async function updateQlearnProblemIsEn(supabaseClient, params) {
  try {
    const { problem_id, is_en } = params;
    
    if (!problem_id) {
      return new Response(JSON.stringify({
        ok: false,
        error: "problem_id is required"
      }), {
        status: 400,
        headers: {
          ...corsHeaders,
          'Content-Type': 'application/json'
        }
      });
    }

    const updateData = {
      is_en: is_en,
      updated_at: new Date().toISOString()
    };

    const { data, error } = await supabaseClient
      .from('qlearn_problems')
      .update(updateData)
      .eq('id', problem_id)
      .select();

    if (error) {
      console.error('Supabase update error:', error);
      throw error;
    }

    return new Response(JSON.stringify({
      ok: true,
      data: data
    }), {
      headers: {
        ...corsHeaders,
        'Content-Type': 'application/json'
      }
    });
  } catch (error) {
    console.error('Error updating is_en field:', error);
    return new Response(JSON.stringify({
      ok: false,
      error: error.message
    }), {
      status: 500,
      headers: {
        ...corsHeaders,
        'Content-Type': 'application/json'
      }
    });
  }
}
```

### 3. 환경 변수 설정

`.env` 파일에 제미나이 API 키가 설정되어 있는지 확인하세요:

```
GEMINI_API_KEY=your_gemini_api_key_here
```

Streamlit Cloud를 사용하는 경우, Secrets 설정에 추가하세요.

## 사용 방법

### 수동 번역

1. "🌐 제미나이 수동 번역" 탭으로 이동
2. 카테고리, 난이도, 번역 여부로 문제 필터링
3. "🔍 문제 검색" 버튼 클릭
4. 번역할 문제 선택
5. "🌐 번역 시작" 버튼 클릭
6. 번역 결과 확인

### 자동 번역

1. "🤖 제미나이 자동 번역" 탭으로 이동
2. 카테고리, 난이도, 번역 여부로 문제 필터링
3. "🔍 문제 검색" 버튼 클릭
4. 번역할 문제들을 체크박스로 선택 (또는 "✅ 전체 선택")
5. "🚀 선택한 N개 문제 번역 시작" 버튼 클릭
6. 번역 진행 상황 모니터링
7. 번역 완료 후 성공/실패 결과 확인

## 번역 기능 상세

### 번역되는 필드

- **텍스트 필드**: title, scenario, task, topic_summary
- **JSON 배열 필드**: goal, first_question, requirements, constraints, evaluation
- **JSON 객체 필드**: guide, reference
- **특수 처리**: time_limit (숫자는 그대로, 형식만 변경. 예: "5분 이내" → "within 5 minutes")

### 데이터 흐름

1. `qlearn_problems` 테이블에서 `is_en=false`인 문제 조회
2. 제미나이 API로 문제 번역
3. 번역된 문제를 `qlearn_problems_en` 테이블에 저장
4. 원본 문제의 `is_en` 필드를 `true`로 업데이트

## 주의사항

- 제미나이 API 호출 제한을 고려하여 자동 번역 시 1초 간격으로 번역 진행
- 번역 실패 시 원본 문제는 유지되며, `is_en` 필드는 업데이트되지 않음
- 이미 번역된 문제(`is_en=true`)도 재번역 가능

