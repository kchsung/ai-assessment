// Edge Function: structured-problems/index.ts
// structured_problems 테이블 전용 Edge Function
import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type'
};

// JSONB 필드 파싱 헬퍼 함수
function passJson<T = unknown>(v: any, fallback: T): T {
  if (v === null || v === undefined) {
    return fallback as any;
  }
  
  if (typeof v === 'object') {
    return v as T;       // jsonb → 그대로
  }
  
  if (typeof v === 'string') {
    const s = v.trim();
    if (!s || s.toLowerCase() === 'null') {
      return fallback as any;
    }
    try { 
      const parsed = JSON.parse(s) as T;
      return parsed; 
    } catch (e) { 
      return fallback as any; 
    }
  }
  
  return fallback as any;
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', {
      headers: corsHeaders
    });
  }

  try {
    const { action, params } = await req.json();
    const supabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_ANON_KEY') ?? ''
    );

    switch (action) {
      case 'save_structured_problem':
        return await saveStructuredProblem(supabaseClient, params);
      case 'get_structured_problems':
        return await getStructuredProblems(supabaseClient, params);
      case 'update_structured_problem':
        return await updateStructuredProblem(supabaseClient, params);
      default:
        return new Response(JSON.stringify({
          ok: false,
          error: 'Unknown action'
        }), {
          status: 400,
          headers: {
            ...corsHeaders,
            'Content-Type': 'application/json'
          }
        });
    }
  } catch (error) {
    console.error('Edge Function Error:', error);
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
});

// structured_problems 테이블에 문제 저장
async function saveStructuredProblem(supabaseClient, params) {
  try {
    console.log('Saving structured_problem (ID will be auto-generated)');
    console.log('Received params keys:', Object.keys(params));
    
    // 빈 문자열이나 null 값들을 필터링하는 함수
    const cleanValue = (value) => {
      if (value === null || value === undefined || value === '') {
        return null;
      }
      if (typeof value === 'string' && value.trim() === '') {
        return null;
      }
      return value;
    };

    // 날짜 형식 변환 함수 (PostgreSQL timestamp 형식을 ISO 형식으로 변환)
    const formatTimestamp = (dateValue) => {
      if (!dateValue) {
        return new Date().toISOString();
      }
      
      if (typeof dateValue === 'string') {
        // PostgreSQL timestamp 형식 (예: "2025-10-23 08:50:14.242741+00")을 ISO로 변환
        if (dateValue.includes(' ') && !dateValue.includes('T')) {
          // 공백이 있고 T가 없으면 PostgreSQL 형식으로 간주
          let isoString = dateValue.replace(' ', 'T');
          
          // 시간대 형식 정리 (+00 -> +00:00, -00 -> -00:00)
          // 정규식으로 시간대 부분 찾기: 끝에 있는 +HH 또는 -HH 형식
          const tzMatch = isoString.match(/([+-])(\d{2})$/);
          if (tzMatch) {
            // +00 또는 -00 형식을 +00:00 또는 -00:00로 변환
            const sign = tzMatch[1];
            const hours = tzMatch[2];
            isoString = isoString.replace(/([+-])(\d{2})$/, `${sign}${hours}:00`);
          } else if (!isoString.includes('+') && !isoString.includes('-') && !isoString.endsWith('Z')) {
            // 시간대가 없으면 UTC로 가정
            isoString += '+00:00';
          }
          
          try {
            const date = new Date(isoString);
            if (!isNaN(date.getTime())) {
              return date.toISOString();
            }
          } catch (e) {
            console.warn(`날짜 파싱 실패, 기본값 사용: ${dateValue}`);
          }
        } else {
          // 이미 ISO 형식이거나 다른 형식이면 파싱 시도
          try {
            const date = new Date(dateValue);
            if (!isNaN(date.getTime())) {
              return date.toISOString();
            }
          } catch (e) {
            // 파싱 실패 시 기본값 사용
          }
        }
      }
      
      return new Date().toISOString();
    };

    // 필수 필드 검증
    if (!params.lang || !params.category || !params.difficulty || !params.problem_type || !params.target_template_code) {
      return new Response(JSON.stringify({
        ok: false,
        error: "필수 필드가 누락되었습니다: lang, category, difficulty, problem_type, target_template_code"
      }), {
        status: 400,
        headers: {
          ...corsHeaders,
          'Content-Type': 'application/json'
        }
      });
    }

    // topic 배열 처리 (빈 배열이면 null로 변환)
    let topicValue = params.topic;
    if (Array.isArray(topicValue)) {
      if (topicValue.length === 0) {
        topicValue = null;
      }
    } else if (!topicValue) {
      topicValue = null;
    }

    const problemData = {
      // idx는 자동 증가 컬럼이므로 제외
      lang: params.lang,
      category: params.category,
      topic: topicValue,  // text[] 배열 (빈 배열이면 null)
      difficulty: params.difficulty,
      time_limit: cleanValue(params.time_limit),
      problem_type: params.problem_type,
      target_template_code: params.target_template_code,
      created_by: cleanValue(params.created_by),
      created_at: formatTimestamp(params.created_at),
      updated_at: formatTimestamp(params.updated_at),
      active: params.active !== undefined ? params.active : true,
      // JSONB 필드들
      user_view_layer: passJson(params.user_view_layer, {}),
      system_view_layer: passJson(params.system_view_layer, {}),
      evaluation_layer: passJson(params.evaluation_layer, {}),
    };
    
    // 최종 데이터에서 null 값들 제거 (선택적 필드만)
    // idx는 자동 증가 컬럼이므로 제외
    const optionalFields = ['topic', 'time_limit', 'created_by'];
    optionalFields.forEach(key => {
      if (problemData[key] === null || problemData[key] === undefined) {
        delete problemData[key];
        console.log(`🗑️ null/undefined 값 제거: ${key}`);
      }
    });
    
    // idx가 params에 포함되어 있으면 제거 (자동 증가 컬럼이므로)
    if ('idx' in problemData) {
      delete problemData.idx;
      console.log(`🗑️ idx 필드 제거 (자동 증가 컬럼)`);
    }

    // UUID 필드 중 id만 제거 (Supabase에서 자동 생성되도록)
    // problemData에는 id가 없지만, 혹시 모를 경우를 대비해 체크
    if ('id' in problemData) {
      delete problemData.id;
      console.log(`🗑️ UUID 필드 제거: id`);
    }
    
    // params에 id가 직접 있는 경우도 제거 (혹시 모를 경우를 대비)
    if (params.id !== undefined) {
      console.log(`🗑️ params.id 필드 제거: ${params.id}`);
    }

    console.log('Final problemData keys:', Object.keys(problemData));
    console.log('Final problemData:', JSON.stringify(problemData, null, 2));
    
    console.log('🔧 [saveStructuredProblem] Supabase 삽입 시작...');
    const { data, error } = await supabaseClient
      .from('structured_problems')
      .insert(problemData)
      .select();

    if (error) {
      console.error('❌ [saveStructuredProblem] Supabase insert error:', error);
      console.error('❌ [saveStructuredProblem] Error details:', {
        message: error.message,
        details: error.details,
        hint: error.hint,
        code: error.code
      });
      throw error;
    }
    
    console.log('✅ [saveStructuredProblem] Supabase 삽입 성공!');
    console.log('✅ [saveStructuredProblem] 삽입된 데이터:', JSON.stringify(data, null, 2));

    return new Response(JSON.stringify({
      ok: true,
      data
    }), {
      headers: {
        ...corsHeaders,
        'Content-Type': 'application/json'
      }
    });
  } catch (error) {
    console.error('Save structured_problem error:', error);
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

// structured_problems 테이블에서 문제 조회
async function getStructuredProblems(supabaseClient, filters = {}) {
  try {
    console.log('Getting structured_problems with filters:', filters);
    
    let query = supabaseClient.from('structured_problems').select('*');
    
    // 필터 적용
    if (filters.id) query = query.eq('id', filters.id);
    if (filters.category) query = query.eq('category', filters.category);
    if (filters.difficulty) query = query.eq('difficulty', filters.difficulty);
    if (filters.lang) query = query.eq('lang', filters.lang);
    if (filters.problem_type) query = query.eq('problem_type', filters.problem_type);
    if (filters.target_template_code) query = query.eq('target_template_code', filters.target_template_code);
    if (filters.active !== undefined) query = query.eq('active', filters.active);

    const { data, error } = await query.order('created_at', {
      ascending: false
    });

    if (error) {
      console.error('Supabase select error:', error);
      throw error;
    }

    // 데이터 변환
    const transformedData = (data || []).map((r) => {
      return {
        id: r.id,
        idx: r.idx,
        lang: r.lang,
        category: r.category,
        topic: r.topic,
        difficulty: r.difficulty,
        time_limit: r.time_limit,
        problem_type: r.problem_type,
        target_template_code: r.target_template_code,
        created_by: r.created_by,
        created_at: r.created_at,
        updated_at: r.updated_at,
        active: r.active,
        user_view_layer: passJson(r.user_view_layer, {}),
        system_view_layer: passJson(r.system_view_layer, {}),
        evaluation_layer: passJson(r.evaluation_layer, {}),
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
    console.error('Get structured_problems error:', error);
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

// structured_problems 테이블의 문제 업데이트
async function updateStructuredProblem(supabaseClient, params) {
  try {
    const { problem_id, updates } = params;
    
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

    const updateData = { ...updates };
    updateData.updated_at = new Date().toISOString();

    const { data, error } = await supabaseClient
      .from('structured_problems')
      .update(updateData)
      .eq('id', problem_id)
      .select();

    if (error) {
      console.error('Supabase update error:', error);
      throw error;
    }

    return new Response(JSON.stringify({
      ok: true,
      data
    }), {
      headers: {
        ...corsHeaders,
        'Content-Type': 'application/json'
      }
    });
  } catch (error) {
    console.error('Update structured_problem error:', error);
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

