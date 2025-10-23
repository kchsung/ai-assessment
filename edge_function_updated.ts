// Edge Function: ai-bank/index.ts (save_qlearn_problem 액션 추가된 버전)
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
      case 'save_question':
        return await saveQuestion(supabaseClient, params);
      case 'get_questions':
        return await getQuestions(supabaseClient, params);
      case 'save_multiple_choice_question':
        return await saveMultipleChoiceQuestion(supabaseClient, params);
      case 'save_subjective_question':
        return await saveSubjectiveQuestion(supabaseClient, params);
      case 'get_multiple_choice_questions':
        return await getMultipleChoiceQuestions(supabaseClient, params);
      case 'get_subjective_questions':
        return await getSubjectiveQuestions(supabaseClient, params);
      case 'update_multiple_choice_question':
        return await updateMultipleChoiceQuestion(supabaseClient, params);
      case 'update_subjective_question':
        return await updateSubjectiveQuestion(supabaseClient, params);
      case 'get_question_status':
        return await getQuestionStatus(supabaseClient, params);
      case 'update_question_status':
        return await updateQuestionStatus(supabaseClient, params);
      case 'get_prompts':
        return await getPrompts(supabaseClient, params);
      case 'save_feedback':
        return await saveFeedback(supabaseClient, params);
      case 'get_feedback':
        return await getFeedback(supabaseClient, params);
      case 'get_feedback_stats':
        return await getFeedbackStats(supabaseClient, params);
      case 'adjust_difficulty':
        return await adjustDifficulty(supabaseClient, params);
      case 'count_feedback':
        return await countFeedback(supabaseClient);
      case 'count_adjustments':
        return await countAdjustments(supabaseClient);
      case 'reset_database':
        return await resetDatabase(supabaseClient);
      case 'get_prompt_by_id':
        return await getPromptById(supabaseClient, params);
      // 새로 추가된 액션들
      case 'save_qlearn_problem':
        return await saveQlearnProblem(supabaseClient, params);
      case 'get_qlearn_problems':
        return await getQlearnProblems(supabaseClient, params);
      case 'update_qlearn_problem':
        return await updateQlearnProblem(supabaseClient, params);
      case 'update_question_review_done':
        return await updateQuestionReviewDone(supabaseClient, params);
      // 번역 관련 액션들 (함수 정의 필요)
      // case 'save_qlearn_problem_en':
      //   return await saveQlearnProblemEn(supabaseClient, params);
      // case 'get_qlearn_problems_en':
      //   return await getQlearnProblemsEn(supabaseClient, params);
      // is_en 필드가 제거되어 해당 액션 제거
      // case 'update_qlearn_problem_is_en':
      //   return await updateQlearnProblemIsEn(supabaseClient, params);
      case 'get_multiple_choice_question_by_id':
        return await getMultipleChoiceQuestionById(supabaseClient, params);
      case 'get_questions_data_version':
        return await getQuestionsDataVersion(supabaseClient);
      // 번역 관련 액션들
      case 'get_problems_for_translation':
        return await getProblemsForTranslation(supabaseClient, params);
      case 'save_i18n_problem':
        return await saveI18nProblem(supabaseClient, params);
      case 'get_i18n_problems':
        return await getI18nProblems(supabaseClient, params);
      // qlearn_problems_multiple 테이블 관련 액션들
      case 'save_qlearn_problem_multiple':
        return await saveQlearnProblemMultiple(supabaseClient, params);
      case 'get_qlearn_problems_multiple':
        return await getQlearnProblemsMultiple(supabaseClient, params);
      case 'update_qlearn_problem_multiple':
        return await updateQlearnProblemMultiple(supabaseClient, params);
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

// 새로 추가된 함수들

// qlearn_problems 테이블에 문제 저장
async function saveQlearnProblem(supabaseClient, params) {
  try {
    console.log('Saving qlearn_problem (ID will be auto-generated)');
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
    
    // 난이도별 time_limit 기본값 설정 함수
    const getTimeLimitByDifficulty = (difficulty) => {
      const timeLimitDefaults = {
        "very easy": "3분 이내",
        "easy": "4분 이내", 
        "normal": "5분 이내",
        "hard": "7분 이내",
        "very hard": "10분 이내",
        "보통": "5분 이내",  // 한국어 지원
        "쉬움": "4분 이내",
        "어려움": "7분 이내",
        "아주 쉬움": "3분 이내",
        "아주 어려움": "10분 이내"
      };
      return timeLimitDefaults[difficulty] || "5분 이내";
    };

    // 모든 NOT NULL 필드에 기본값 제공
    const difficulty = cleanValue(params.difficulty) || 'normal';
    
    // JSONB 필드들을 명시적으로 처리
    
    const problemData = {
      lang: cleanValue(params.lang) || 'kr',
      category: cleanValue(params.category) || 'life',
      topic: cleanValue(params.topic) || '기본 주제',
      difficulty: difficulty,
      time_limit: cleanValue(params.time_limit) || getTimeLimitByDifficulty(difficulty),
      topic_summary: cleanValue(params.topic_summary) || '기본 주제 요약',
      title: cleanValue(params.title) || '기본 제목',
      scenario: cleanValue(params.scenario) || '기본 시나리오',
      goal: passJson(params.goal, []),
      first_question: passJson(params.first_question, []),
      requirements: passJson(params.requirements, []),
      constraints: passJson(params.constraints, []),
      guide: passJson(params.guide, {}),
      evaluation: passJson(params.evaluation, []),
      task: cleanValue(params.task) || '기본 과제',
      active: params.active !== undefined ? params.active : false,
      created_at: cleanValue(params.created_at) || new Date().toISOString(),
      updated_at: cleanValue(params.updated_at) || new Date().toISOString()
    };
    
    // JSONB 필드 처리 완료
    
    // 선택적 필드들 추가
    const referenceData = passJson(params.reference, {});
    if (referenceData && Object.keys(referenceData).length > 0) {
      problemData.reference = referenceData;
    }
    
    // created_by 필드는 유효한 UUID 값이 있는 경우에만 추가
    const createdByValue = cleanValue(params.created_by);
    if (createdByValue && createdByValue.trim() !== '' && createdByValue !== '""') {
      // UUID 형식 검증 (간단한 검증)
      const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
      if (uuidRegex.test(createdByValue.trim())) {
        problemData.created_by = createdByValue.trim();
        console.log('✅ created_by 필드 추가:', createdByValue.trim());
      } else {
        console.log('⚠️ created_by 필드가 유효한 UUID 형식이 아님, 제외:', createdByValue);
      }
    } else {
      console.log('⚠️ created_by 필드가 빈 값이거나 없음, 제외:', params.created_by);
    }
    
    // 최종 데이터에서 null 값들 제거 (Supabase에서 null 값이 문제가 될 수 있음)
    Object.keys(problemData).forEach(key => {
      if (problemData[key] === null || problemData[key] === undefined) {
        delete problemData[key];
        console.log(`🗑️ null/undefined 값 제거: ${key}`);
      }
    });
    
    // UUID 필드 중 id만 제거 (Supabase에서 자동 생성되도록)
    const uuidFields = ['id'];
    uuidFields.forEach(field => {
      if (problemData[field] !== undefined) {
        delete problemData[field];
        console.log(`🗑️ UUID 필드 제거: ${field}`);
      }
    });

    console.log('Final problemData keys:', Object.keys(problemData));
    console.log('Final problemData:', JSON.stringify(problemData, null, 2));
    
    console.log('🔧 [saveQlearnProblem] Supabase 삽입 시작...');
    const { data, error } = await supabaseClient
      .from('qlearn_problems')
      .insert(problemData)
      .select();

    if (error) {
      console.error('❌ [saveQlearnProblem] Supabase insert error:', error);
      console.error('❌ [saveQlearnProblem] Error details:', {
        message: error.message,
        details: error.details,
        hint: error.hint,
        code: error.code
      });
      throw error;
    }
    
    console.log('✅ [saveQlearnProblem] Supabase 삽입 성공!');
    console.log('✅ [saveQlearnProblem] 삽입된 데이터:', JSON.stringify(data, null, 2));

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
    console.error('Save qlearn_problem error:', error);
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

// qlearn_problems 테이블에서 문제 조회
async function getQlearnProblems(supabaseClient, filters = {}) {
  try {
    console.log('Getting qlearn_problems with filters:', filters);
    
    let query = supabaseClient.from('qlearn_problems').select('*');
    
    // 필터 적용
    if (filters.id) query = query.eq('id', filters.id);
    if (filters.domain) query = query.eq('category', filters.domain);
    if (filters.difficulty) query = query.eq('difficulty', filters.difficulty);
    if (filters.topic) query = query.eq('topic', filters.topic);
    if (filters.active !== undefined) query = query.eq('active', filters.active);
    if (filters.lang) query = query.eq('lang', filters.lang);

    const { data, error } = await query.order('created_at', {
      ascending: false
    });

    if (error) {
      console.error('Supabase select error:', error);
      throw error;
    }

    // 데이터 변환 (JSON 필드들 파싱)
    const transformedData = (data || []).map((r) => {
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
        goal: passJson(r.goal, []),
        first_question: passJson(r.first_question, []),
        requirements: passJson(r.requirements, []),
        constraints: passJson(r.constraints, []),
        guide: passJson(r.guide, {}),
        evaluation: passJson(r.evaluation, []),
        task: r.task,
        created_by: r.created_by,
        created_at: r.created_at,
        updated_at: r.updated_at,
        reference: passJson(r.reference, {}),
        active: r.active
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
    console.error('Get qlearn_problems error:', error);
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

// qlearn_problems 테이블의 문제 업데이트
async function updateQlearnProblem(supabaseClient, params) {
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

    // 난이도별 time_limit 기본값 설정 함수
    const getTimeLimitByDifficulty = (difficulty) => {
      const timeLimitDefaults = {
        "very easy": "3분 이내",
        "easy": "4분 이내", 
        "normal": "5분 이내",
        "hard": "7분 이내",
        "very hard": "10분 이내",
        "보통": "5분 이내",  // 한국어 지원
        "쉬움": "4분 이내",
        "어려움": "7분 이내",
        "아주 쉬움": "3분 이내",
        "아주 어려움": "10분 이내"
      };
      return timeLimitDefaults[difficulty] || "5분 이내";
    };

    // JSON 필드들은 그대로 유지 (Supabase가 자동으로 JSONB로 처리)
    const updateData = { ...updates };
    
    // qlearn_problems 테이블에 존재하지 않는 필드들 제거
    const invalidFields = ['role']; // questions 테이블에만 있는 필드들
    invalidFields.forEach(field => {
      if (field in updateData) {
        console.log(`⚠️ qlearn_problems 테이블에 존재하지 않는 필드 제거: ${field}`);
        delete updateData[field];
      }
    });
    
    // time_limit 필드가 null이거나 빈 값인 경우 난이도에 따른 기본값 설정
    if (!updateData.time_limit || updateData.time_limit === "" || updateData.time_limit === null) {
      // 현재 문제의 난이도를 조회하여 기본값 설정
      const { data: currentProblem, error: fetchError } = await supabaseClient
        .from('qlearn_problems')
        .select('difficulty')
        .eq('id', problem_id)
        .single();
      
      if (!fetchError && currentProblem) {
        const difficulty = currentProblem.difficulty || 'normal';
        updateData.time_limit = getTimeLimitByDifficulty(difficulty);
        console.log(`⏰ time_limit 기본값 설정: ${updateData.time_limit} (난이도: ${difficulty})`);
      } else {
        updateData.time_limit = "5분 이내"; // 기본값
        console.log(`⏰ time_limit 기본값 설정: ${updateData.time_limit} (기본값)`);
      }
    }
    
    updateData.updated_at = new Date().toISOString();

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
      data
    }), {
      headers: {
        ...corsHeaders,
        'Content-Type': 'application/json'
      }
    });
  } catch (error) {
    console.error('Update qlearn_problem error:', error);
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

// questions 테이블의 review_done 필드 업데이트
async function updateQuestionReviewDone(supabaseClient, params) {
  try {
    const { question_id, review_done } = params;
    
    if (!question_id) {
      return new Response(JSON.stringify({
        ok: false,
        error: "question_id is required"
      }), {
        status: 400,
        headers: {
          ...corsHeaders,
          'Content-Type': 'application/json'
        }
      });
    }

    const { data, error } = await supabaseClient
      .from('questions')
      .update({ 
        review_done: review_done !== undefined ? review_done : true
      })
      .eq('id', question_id)
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
    console.error('Update question review_done error:', error);
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

// qlearn_problems_multiple 테이블 관련 함수들

// qlearn_problems_multiple 테이블에 문제 저장
async function saveQlearnProblemMultiple(supabaseClient, params) {
  try {
    console.log('Saving qlearn_problem_multiple (ID will be auto-generated)');
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
    
    // 난이도별 estimated_time 기본값 설정 함수
    const getEstimatedTimeByDifficulty = (difficulty) => {
      const timeLimitDefaults = {
        "very easy": "3분 이내",
        "easy": "4분 이내", 
        "normal": "5분 이내",
        "hard": "7분 이내",
        "very hard": "10분 이내",
        "보통": "5분 이내",
        "쉬움": "4분 이내",
        "어려움": "7분 이내",
        "아주 쉬움": "3분 이내",
        "아주 어려움": "10분 이내"
      };
      return timeLimitDefaults[difficulty] || "5분 이내";
    };

    // 모든 NOT NULL 필드에 기본값 제공
    const difficulty = cleanValue(params.difficulty) || 'normal';
    
    // JSONB 필드들을 명시적으로 처리
    
    const problemData = {
      lang: cleanValue(params.lang) || 'kr',
      category: cleanValue(params.category) || 'life',
      problem_title: cleanValue(params.problem_title) || '기본 문제 제목',
      difficulty: difficulty,
      estimated_time: cleanValue(params.estimated_time) || getEstimatedTimeByDifficulty(difficulty),
      scenario: cleanValue(params.scenario) || '기본 시나리오',
      steps: passJson(params.steps, []),
      active: params.active !== undefined ? params.active : false,
      created_at: cleanValue(params.created_at) || new Date().toISOString(),
      updated_at: cleanValue(params.updated_at) || new Date().toISOString(),
      image_url: cleanValue(params.image_url),
      topic_summary: cleanValue(params.topic_summary)
    };
    
    // JSONB 필드 처리 완료
    
    // created_by 필드는 유효한 UUID 값이 있는 경우에만 추가
    const createdByValue = cleanValue(params.created_by);
    if (createdByValue && createdByValue.trim() !== '' && createdByValue !== '""') {
      const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
      if (uuidRegex.test(createdByValue.trim())) {
        problemData.created_by = createdByValue.trim();
        console.log('✅ created_by 필드 추가:', createdByValue.trim());
      } else {
        console.log('⚠️ created_by 필드가 유효한 UUID 형식이 아님, 제외:', createdByValue);
      }
    }
    
    // 최종 데이터에서 null 값들 제거
    Object.keys(problemData).forEach(key => {
      if (problemData[key] === null || problemData[key] === undefined) {
        delete problemData[key];
        console.log(`🗑️ null/undefined 값 제거: ${key}`);
      }
    });
    
    // UUID 필드 중 id만 제거 (Supabase에서 자동 생성되도록)
    const uuidFields = ['id'];
    uuidFields.forEach(field => {
      if (problemData[field] !== undefined) {
        delete problemData[field];
        console.log(`🗑️ UUID 필드 제거: ${field}`);
      }
    });

    console.log('Final problemData keys:', Object.keys(problemData));
    console.log('Final problemData:', JSON.stringify(problemData, null, 2));
    
    console.log('🔧 [saveQlearnProblemMultiple] Supabase 삽입 시작...');
    const { data, error } = await supabaseClient
      .from('qlearn_problems_multiple')
      .insert(problemData)
      .select();

    if (error) {
      console.error('❌ [saveQlearnProblemMultiple] Supabase insert error:', error);
      console.error('❌ [saveQlearnProblemMultiple] Error details:', {
        message: error.message,
        details: error.details,
        hint: error.hint,
        code: error.code
      });
      throw error;
    }
    
    console.log('✅ [saveQlearnProblemMultiple] Supabase 삽입 성공!');
    console.log('✅ [saveQlearnProblemMultiple] 삽입된 데이터:', JSON.stringify(data, null, 2));

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
    console.error('Save qlearn_problem_multiple error:', error);
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

// qlearn_problems_multiple 테이블에서 문제 조회
async function getQlearnProblemsMultiple(supabaseClient, filters = {}) {
  try {
    console.log('Getting qlearn_problems_multiple with filters:', filters);
    
    let query = supabaseClient.from('qlearn_problems_multiple').select('*');
    
    // 필터 적용
    if (filters.id) query = query.eq('id', filters.id);
    if (filters.category) query = query.eq('category', filters.category);
    if (filters.difficulty) query = query.eq('difficulty', filters.difficulty);
    if (filters.lang) query = query.eq('lang', filters.lang);
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
        lang: r.lang,
        category: r.category,
        problem_title: r.problem_title,
        difficulty: r.difficulty,
        estimated_time: r.estimated_time,
        scenario: r.scenario,
        steps: passJson(r.steps, []),
        created_by: r.created_by,
        created_at: r.created_at,
        updated_at: r.updated_at,
        image_url: r.image_url,
        active: r.active,
        topic_summary: r.topic_summary
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
    console.error('Get qlearn_problems_multiple error:', error);
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

// qlearn_problems_multiple 테이블의 문제 업데이트
async function updateQlearnProblemMultiple(supabaseClient, params) {
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
      .from('qlearn_problems_multiple')
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
    console.error('Update qlearn_problem_multiple error:', error);
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

// 새로운 테이블 분리 함수들

// 객관식 문제 저장
async function saveMultipleChoiceQuestion(supabaseClient, params) {
  try {
    console.log('🚀 saveMultipleChoiceQuestion 시작');
    console.log('🔍 받은 params 키들:', Object.keys(params));
    console.log('🔍 받은 params 전체:', JSON.stringify(params, null, 2));
    
    const questionData = {
      // id는 UUID 자동 생성되도록 제거
      lang: params.lang || 'kr',
      category: params.category || 'interview',
      problem_title: params.problem_title || params.title || '객관식 문제',
      difficulty: params.difficulty || 'normal',
      estimated_time: params.estimated_time || params.time_limit || '3분 이내',
      scenario: params.scenario || '기본 시나리오',
      steps: params.steps || [],
      created_by: params.created_by,
      image_url: params.image_url,
      active: params.active !== undefined ? params.active : true,
      topic_summary: params.topic_summary
    };
    
    console.log('🔍 구성된 questionData:', JSON.stringify(questionData, null, 2));
    console.log('🔍 steps 필드 상세:', {
      value: questionData.steps,
      type: typeof questionData.steps,
      isArray: Array.isArray(questionData.steps),
      length: Array.isArray(questionData.steps) ? questionData.steps.length : 'N/A'
    });

    console.log('📝 데이터베이스 삽입 시도 중...');
    const { data, error } = await supabaseClient
      .from('questions_multiple_choice')
      .insert(questionData)
      .select();

    if (error) {
      console.error('❌ 데이터베이스 삽입 실패:', error);
      console.error('❌ 에러 상세:', {
        message: error.message,
        details: error.details,
        hint: error.hint,
        code: error.code
      });
      throw error;
    }

    console.log('✅ 데이터베이스 삽입 성공!');
    console.log('✅ 삽입된 데이터:', JSON.stringify(data, null, 2));

    // 문제 상태 테이블에 상태 정보 저장 (생성된 UUID 사용)
    const statusData = {
      question_id: data[0].id, // 생성된 UUID 사용
      question_type: params.type || 'multiple_choice', // params에서 전달받은 type 사용
      review_done: params.review_done || false,
      translation_done: params.translation_done || false,
      ai_generated: params.ai_generated || false,
      template_id: params.template_id,
      created_by: params.created_by
    };

    await supabaseClient
      .from('question_status')
      .insert(statusData);

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
    console.error('Save multiple choice question error:', error);
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

// 주관식 문제 저장
async function saveSubjectiveQuestion(supabaseClient, params) {
  try {
    console.log('Saving subjective question:', params.id);
    
    const questionData = {
      // id는 UUID 자동 생성되도록 제거
      lang: params.lang || 'kr',
      category: params.category || 'interview',
      topic: params.topic || '기본 주제',
      difficulty: params.difficulty || 'normal',
      time_limit: params.time_limit || '5분 이내',
      topic_summary: params.topic_summary || '기본 주제 요약',
      title: params.title || '기본 제목',
      scenario: params.scenario || '기본 시나리오',
      goal: params.goal || [],
      first_question: params.first_question || [],
      requirements: params.requirements || [],
      constraints: params.constraints || [],
      guide: params.guide || {},
      evaluation: params.evaluation || [],
      task: params.task || '기본 과제',
      created_by: params.created_by,
      reference: params.reference,
      active: params.active !== undefined ? params.active : true
    };

    const { data, error } = await supabaseClient
      .from('questions_subjective')
      .insert(questionData)
      .select();

    if (error) {
      console.error('Supabase insert error:', error);
      throw error;
    }

    // 문제 상태 테이블에 상태 정보 저장 (생성된 UUID 사용)
    const statusData = {
      question_id: data[0].id, // 생성된 UUID 사용
      question_type: params.type || 'subjective', // params에서 전달받은 type 사용
      review_done: params.review_done || false,
      translation_done: params.translation_done || false,
      ai_generated: params.ai_generated || false,
      template_id: params.template_id,
      created_by: params.created_by
    };

    await supabaseClient
      .from('question_status')
      .insert(statusData);

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
    console.error('Save subjective question error:', error);
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

// 객관식 문제 조회
async function getMultipleChoiceQuestions(supabaseClient, filters = {}) {
  try {
    console.log('Getting multiple choice questions with filters:', filters);
    
    let query = supabaseClient.from('questions_multiple_choice').select('*');
    
    // 필터 적용
    if (filters.id) query = query.eq('id', filters.id);
    if (filters.category) query = query.eq('category', filters.category);
    if (filters.difficulty) query = query.eq('difficulty', filters.difficulty);
    if (filters.lang) query = query.eq('lang', filters.lang);
    if (filters.active !== undefined) query = query.eq('active', filters.active);
    // review_done, translation_done, ai_generated 필터는 question_status 테이블에서 별도로 처리

    const { data, error } = await query.order('created_at', {
      ascending: false
    });

    if (error) {
      console.error('Supabase select error:', error);
      throw error;
    }

    // question_status 정보를 별도로 조회하여 병합
    let statusMap = {};
    if (data && data.length > 0) {
      const questionIds = data.map(r => r.id);
      let statusQuery = supabaseClient
        .from('question_status')
        .select('question_id, review_done, translation_done, ai_generated, created_at, updated_at')
        .in('question_id', questionIds)
        .eq('question_type', 'multiple_choice');

      // 교정 상태 필터 적용
      if (filters.review_done !== undefined) {
        statusQuery = statusQuery.eq('review_done', filters.review_done);
      }
      if (filters.translation_done !== undefined) {
        statusQuery = statusQuery.eq('translation_done', filters.translation_done);
      }

      const { data: statusData, error: statusError } = await statusQuery;

      if (!statusError && statusData) {
        statusData.forEach(status => {
          statusMap[status.question_id] = status;
        });
      }
    }

    // 데이터 변환 및 필터링
    const transformedData = (data || [])
      .map((r) => {
        return {
          id: r.id,
          lang: r.lang,
          category: r.category,
          problem_title: r.problem_title,
          difficulty: r.difficulty,
          estimated_time: r.estimated_time,
          scenario: r.scenario,
          steps: passJson(r.steps, []),
          created_by: r.created_by,
          created_at: r.created_at,
          updated_at: r.updated_at,
          image_url: r.image_url,
          active: r.active,
          topic_summary: r.topic_summary,
          question_status: statusMap[r.id] || null
        };
      })
      .filter((item) => {
        // 교정 상태 필터가 적용된 경우, 해당 상태에 맞는 문제만 반환
        if (filters.review_done !== undefined || filters.translation_done !== undefined) {
          return statusMap[item.id] !== undefined;
        }
        return true;
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
    console.error('Get multiple choice questions error:', error);
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

// 주관식 문제 조회
async function getSubjectiveQuestions(supabaseClient, filters = {}) {
  try {
    console.log('Getting subjective questions with filters:', filters);
    
    let query = supabaseClient.from('questions_subjective').select('*');
    
    // 필터 적용
    if (filters.id) query = query.eq('id', filters.id);
    if (filters.category) query = query.eq('category', filters.category);
    if (filters.difficulty) query = query.eq('difficulty', filters.difficulty);
    if (filters.topic) query = query.eq('topic', filters.topic);
    if (filters.lang) query = query.eq('lang', filters.lang);
    if (filters.active !== undefined) query = query.eq('active', filters.active);
    // review_done, translation_done, ai_generated 필터는 question_status 테이블에서 별도로 처리
    // is_en 필드가 제거되어 필터링 로직 제거
    // if (filters.is_en !== undefined) {
    //   if (filters.is_en === false) {
    //     query = query.or('is_en.is.null,is_en.eq.false');
    //   } else if (filters.is_en === true) {
    //     query = query.eq('is_en', true);
    //   } else {
    //     query = query.eq('is_en', filters.is_en);
    //   }
    // }

    const { data, error } = await query.order('created_at', {
      ascending: false
    });

    if (error) {
      console.error('Supabase select error:', error);
      throw error;
    }

    // question_status 정보를 별도로 조회하여 병합
    let statusMap = {};
    if (data && data.length > 0) {
      const questionIds = data.map(r => r.id);
      let statusQuery = supabaseClient
        .from('question_status')
        .select('question_id, review_done, translation_done, ai_generated, created_at, updated_at')
        .in('question_id', questionIds)
        .eq('question_type', 'subjective');

      // 교정 상태 필터 적용
      if (filters.review_done !== undefined) {
        statusQuery = statusQuery.eq('review_done', filters.review_done);
      }
      if (filters.translation_done !== undefined) {
        statusQuery = statusQuery.eq('translation_done', filters.translation_done);
      }

      const { data: statusData, error: statusError } = await statusQuery;

      if (!statusError && statusData) {
        statusData.forEach(status => {
          statusMap[status.question_id] = status;
        });
      }
    }

    // 데이터 변환 및 필터링
    const transformedData = (data || [])
      .map((r) => {
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
          goal: passJson(r.goal, []),
          first_question: passJson(r.first_question, []),
          requirements: passJson(r.requirements, []),
          constraints: passJson(r.constraints, []),
          guide: passJson(r.guide, {}),
          evaluation: passJson(r.evaluation, []),
          task: r.task,
          created_by: r.created_by,
          created_at: r.created_at,
          updated_at: r.updated_at,
          reference: passJson(r.reference, {}),
          active: r.active,
          question_status: statusMap[r.id] || null
        };
      })
      .filter((item) => {
        // 교정 상태 필터가 적용된 경우, 해당 상태에 맞는 문제만 반환
        if (filters.review_done !== undefined || filters.translation_done !== undefined) {
          return statusMap[item.id] !== undefined;
        }
        return true;
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
    console.error('Get subjective questions error:', error);
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

// 객관식 문제 업데이트
async function updateMultipleChoiceQuestion(supabaseClient, params) {
  try {
    const { question_id, updates } = params;
    
    if (!question_id) {
      return new Response(JSON.stringify({
        ok: false,
        error: "question_id is required"
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
      .from('questions_multiple_choice')
      .update(updateData)
      .eq('id', question_id)
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
    console.error('Update multiple choice question error:', error);
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

// 주관식 문제 업데이트
async function updateSubjectiveQuestion(supabaseClient, params) {
  try {
    const { question_id, updates } = params;
    
    if (!question_id) {
      return new Response(JSON.stringify({
        ok: false,
        error: "question_id is required"
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
      .from('questions_subjective')
      .update(updateData)
      .eq('id', question_id)
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
    console.error('Update subjective question error:', error);
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

// 문제 상태 조회
async function getQuestionStatus(supabaseClient, filters = {}) {
  try {
    console.log('Getting question status with filters:', filters);
    
    let query = supabaseClient.from('question_status').select('*');
    
    // 필터 적용
    if (filters.question_id) query = query.eq('question_id', filters.question_id);
    if (filters.question_type) query = query.eq('question_type', filters.question_type);
    if (filters.review_done !== undefined) query = query.eq('review_done', filters.review_done);
    if (filters.translation_done !== undefined) query = query.eq('translation_done', filters.translation_done);
    if (filters.ai_generated !== undefined) query = query.eq('ai_generated', filters.ai_generated);

    const { data, error } = await query.order('created_at', {
      ascending: false
    });

    if (error) {
      console.error('Supabase select error:', error);
      throw error;
    }

    return new Response(JSON.stringify({
      ok: true,
      data: data || []
    }), {
      headers: {
        ...corsHeaders,
        'Content-Type': 'application/json'
      }
    });
  } catch (error) {
    console.error('Get question status error:', error);
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

// 문제 상태 업데이트
async function updateQuestionStatus(supabaseClient, params) {
  try {
    const { question_id, updates } = params;
    
    if (!question_id) {
      return new Response(JSON.stringify({
        ok: false,
        error: "question_id is required"
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
      .from('question_status')
      .update(updateData)
      .eq('question_id', question_id)
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
    console.error('Update question status error:', error);
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

// 기존 함수들 (변경 없음)

// get_feedback 함수 추가
async function getFeedback(supabaseClient, params) {
  try {
    const { question_id } = params;
    let query = supabaseClient.from('feedback').select('*');
    if (question_id) {
      query = query.eq('question_id', question_id);
    }
    const { data, error } = await query.order('created_at', {
      ascending: false
    });
    if (error) throw error;
    return new Response(JSON.stringify({
      ok: true,
      data: data || []
    }), {
      headers: {
        ...corsHeaders,
        'Content-Type': 'application/json'
      }
    });
  } catch (error) {
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

// get_prompt_by_id 함수
async function getPromptById(supabaseClient, params) {
  try {
    const { prompt_id } = params;
    if (!prompt_id) {
      return new Response(JSON.stringify({
        ok: false,
        error: "prompt_id is required"
      }), {
        status: 400,
        headers: {
          ...corsHeaders,
          'Content-Type': 'application/json'
        }
      });
    }
    const { data, error } = await supabaseClient.from("prompts").select("prompt_text").eq("id", prompt_id).eq("active", true).single();
    if (error) {
      console.error("Error fetching prompt:", error);
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
    if (!data) {
      return new Response(JSON.stringify({
        ok: false,
        error: "Prompt not found"
      }), {
        status: 404,
        headers: {
          ...corsHeaders,
          'Content-Type': 'application/json'
        }
      });
    }
    return new Response(JSON.stringify({
      ok: true,
      data: data.prompt_text
    }), {
      headers: {
        ...corsHeaders,
        'Content-Type': 'application/json'
      }
    });
  } catch (error) {
    console.error("get_prompt_by_id error:", error);
    return new Response(JSON.stringify({
      ok: false,
      error: String(error)
    }), {
      status: 500,
      headers: {
        ...corsHeaders,
        'Content-Type': 'application/json'
      }
    });
  }
}

async function saveQuestion(supabaseClient, q) {
  try {
    console.log('Saving question:', q.id);
    // 메타데이터에서 새로운 필드들 추출
    const metadata = q.metadata || {};
    const questionData = {
      id: q.id,
      area: q.area,
      difficulty: q.difficulty,
      type: q.type || 'general',
      question_text: q.question,
      options: q.options ? JSON.stringify(q.options) : null,
      correct_answer: q.correct_answer,
      requirements: q.requirements ? JSON.stringify(q.requirements) : null,
      evaluation_criteria: q.evaluation_criteria ? JSON.stringify(q.evaluation_criteria) : null,
      ai_generated: q.ai_generated || false,
      template_id: q.template_id,
      metadata: JSON.stringify(metadata),
      // questions 테이블에 실제 존재하는 컬럼들
      lang: metadata.lang || 'kr',
      category: metadata.category || 'interview',
      role: metadata.role || null,
      time_limit: metadata.time_limit || metadata.estimatedTime || null,
      topic_summary: metadata.topic_summary || null,
      scenario: metadata.scenario || null,
      goal: metadata.goal ? JSON.stringify(metadata.goal) : null,
      task: metadata.task || null,
      reference: metadata.reference ? JSON.stringify(metadata.reference) : null,
      first_question: metadata.first_question ? JSON.stringify(metadata.first_question) : null,
      constraints: metadata.constraints ? JSON.stringify(metadata.constraints) : null,
      guide: metadata.guide ? JSON.stringify(metadata.guide) : null,
      evaluation: metadata.evaluation ? JSON.stringify(metadata.evaluation) : null,
      steps: metadata.steps ? JSON.stringify(metadata.steps) : null,
      review_done: q.review_done || false
    };
    const { data, error } = await supabaseClient.from('questions').insert(questionData).select();
    if (error) {
      console.error('Supabase insert error:', error);
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
    console.error('Save question error:', error);
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

async function getQuestions(supabaseClient, filters = {}) {
  try {
    console.log('Getting questions with filters:', filters);
    let query = supabaseClient.from('questions').select('*');
    // 필터 적용
    if (filters.id) query = query.eq('id', filters.id);
    if (filters.area) query = query.eq('area', filters.area);
    if (filters.difficulty) query = query.eq('difficulty', filters.difficulty);
    if (filters.type) query = query.eq('type', filters.type);
    if (filters.topic) query = query.eq('role', filters.topic); // questions 테이블에는 topic 대신 role 컬럼 사용
    if (filters.category) query = query.eq('category', filters.category);
    if (filters.review_done !== undefined) {
      // boolean 값을 명시적으로 처리
      const reviewDoneValue = filters.review_done === true || filters.review_done === 'true' || filters.review_done === 'TRUE';
      query = query.eq('review_done', reviewDoneValue);
    }
    const { data, error } = await query.order('created_at', {
      ascending: false
    });
    if (error) {
      console.error('Supabase select error:', error);
      throw error;
    }
    // 데이터 변환
    const transformedData = (data || []).map((r) => {
      const metadata = passJson(r.metadata, {});
      // questions 테이블의 실제 컬럼들을 메타데이터에 병합
      const newFields = {
        lang: r.lang || 'kr',
        category: r.category || 'interview',
        role: r.role,
        time_limit: r.time_limit,
        topic_summary: r.topic_summary,
        scenario: r.scenario,
        goal: passJson(r.goal, []),
        task: r.task,
        reference: passJson(r.reference, {}),
        first_question: passJson(r.first_question, []),
        constraints: passJson(r.constraints, []),
        guide: passJson(r.guide, {}),
        evaluation: passJson(r.evaluation, []),
        steps: passJson(r.steps, [])
      };
      // None이 아닌 값들만 메타데이터에 추가
      Object.entries(newFields).forEach(([key, value]) => {
        if (value !== null && value !== '' && !(Array.isArray(value) && value.length === 0) && !(typeof value === 'object' && Object.keys(value).length === 0)) {
          metadata[key] = value;
        }
      });
      return {
        id: r.id,
        area: r.area,
        difficulty: r.difficulty,
        type: r.type,
        question: r.question_text,
        options: passJson(r.options, null),
        correct_answer: r.correct_answer,
        requirements: passJson(r.requirements, null),
        evaluation_criteria: passJson(r.evaluation_criteria, null),
        ai_generated: r.ai_generated,
        metadata: metadata,
        review_done: r.review_done || false
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
    console.error('Get questions error:', error);
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

async function getPrompts(supabaseClient, params) {
  try {
    let query = supabaseClient.from('prompts').select('*').eq('lang', params.lang || 'kr').eq('active', true);
    if (params.category) {
      query = query.eq('category', params.category);
    }
    const { data, error } = await query.order('created_at', {
      ascending: false
    });
    if (error) throw error;
    return new Response(JSON.stringify({
      ok: true,
      data: data || []
    }), {
      headers: {
        ...corsHeaders,
        'Content-Type': 'application/json'
      }
    });
  } catch (error) {
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

async function saveFeedback(supabaseClient, fb) {
  try {
    const { data, error } = await supabaseClient.from('feedback').insert({
      question_id: fb.question_id,
      user_id: fb.user_id || 'anonymous',
      difficulty_rating: fb.difficulty_rating,
      relevance_rating: fb.relevance_rating,
      clarity_rating: fb.clarity_rating,
      comments: fb.comments || '',
      actual_difficulty: fb.actual_difficulty
    }).select();
    if (error) throw error;
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

async function getFeedbackStats(supabaseClient, params) {
  try {
    const { data, error } = await supabaseClient.from('feedback').select('*').eq('question_id', params.question_id);
    if (error) throw error;
    if (!data || data.length === 0) {
      return new Response(JSON.stringify({
        ok: true,
        data: null
      }), {
        headers: {
          ...corsHeaders,
          'Content-Type': 'application/json'
        }
      });
    }
    const stats = {
      avg_difficulty: data.reduce((sum, item) => sum + item.difficulty_rating, 0) / data.length,
      avg_relevance: data.reduce((sum, item) => sum + item.relevance_rating, 0) / data.length,
      avg_clarity: data.reduce((sum, item) => sum + item.clarity_rating, 0) / data.length,
      feedback_count: data.length,
      difficulty_votes: {}
    };
    // 난이도 투표 집계
    data.forEach((item) => {
      if (item.actual_difficulty) {
        stats.difficulty_votes[item.actual_difficulty] = (stats.difficulty_votes[item.actual_difficulty] || 0) + 1;
      }
    });
    return new Response(JSON.stringify({
      ok: true,
      data: stats
    }), {
      headers: {
        ...corsHeaders,
        'Content-Type': 'application/json'
      }
    });
  } catch (error) {
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

async function adjustDifficulty(supabaseClient, params) {
  try {
    // 기존 난이도 조회
    const { data: question, error: fetchError } = await supabaseClient.from('questions').select('difficulty').eq('id', params.question_id).single();
    if (fetchError) throw fetchError;
    // 난이도 업데이트
    const { error: updateError } = await supabaseClient.from('questions').update({
      difficulty: params.new_difficulty
    }).eq('id', params.question_id);
    if (updateError) throw updateError;
    // 조정 기록 저장
    const { error: insertError } = await supabaseClient.from('difficulty_adjustments').insert({
      question_id: params.question_id,
      original_difficulty: question.difficulty,
      adjusted_difficulty: params.new_difficulty,
      adjustment_reason: params.reason,
      adjusted_by: params.adjusted_by || 'system'
    });
    if (insertError) throw insertError;
    return new Response(JSON.stringify({
      ok: true,
      data: {}
    }), {
      headers: {
        ...corsHeaders,
        'Content-Type': 'application/json'
      }
    });
  } catch (error) {
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

async function countFeedback(supabaseClient) {
  try {
    const { count, error } = await supabaseClient.from('feedback').select('*', {
      count: 'exact',
      head: true
    });
    if (error) throw error;
    return new Response(JSON.stringify({
      ok: true,
      data: count || 0
    }), {
      headers: {
        ...corsHeaders,
        'Content-Type': 'application/json'
      }
    });
  } catch (error) {
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

async function countAdjustments(supabaseClient) {
  try {
    const { count, error } = await supabaseClient.from('difficulty_adjustments').select('*', {
      count: 'exact',
      head: true
    });
    if (error) throw error;
    return new Response(JSON.stringify({
      ok: true,
      data: count || 0
    }), {
      headers: {
        ...corsHeaders,
        'Content-Type': 'application/json'
      }
    });
  } catch (error) {
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

async function resetDatabase(supabaseClient) {
  try {
    // 모든 테이블 데이터 삭제
    await supabaseClient.from('difficulty_adjustments').delete().neq('id', 0);
    await supabaseClient.from('feedback').delete().neq('id', 0);
    await supabaseClient.from('questions').delete().neq('id', '');
    return new Response(JSON.stringify({
      ok: true,
      data: {}
    }), {
      headers: {
        ...corsHeaders,
        'Content-Type': 'application/json'
      }
    });
  } catch (error) {
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

// ID�?객�???문제 ?�건 조회 (캐시 ?�회??
async function getMultipleChoiceQuestionById(supabaseClient, params) {
  try {
    const { question_id } = params;
    console.log('Getting multiple choice question by ID:', question_id);
    
    const { data, error } = await supabaseClient
      .from('questions_multiple_choice')
      .select('*')
      .eq('id', question_id)
      .single();

    if (error) {
      console.error('Supabase select error:', error);
      throw error;
    }

    if (!data) {
      return new Response(JSON.stringify({
        ok: false,
        error: 'Question not found'
      }), {
        status: 404,
        headers: {
          ...corsHeaders,
          'Content-Type': 'application/json'
        }
      });
    }

    // ?�이??변??(기존 getMultipleChoiceQuestions?� ?�일??로직)
    const safeJsonParse = (jsonString, defaultValue) => {
      if (!jsonString) return defaultValue;
      try {
        return JSON.parse(jsonString);
      } catch (error) {
        console.warn(`JSON ?�싱 ?�류:`, error.message);
        return defaultValue;
      }
    };


    const transformedData = {
      id: data.id,
      lang: data.lang,
      category: data.category,
      problem_title: data.problem_title,
      difficulty: data.difficulty,
      estimated_time: data.estimated_time,
      scenario: data.scenario,
      steps: passJson(data.steps, []),
      created_by: data.created_by,
      created_at: data.created_at,
      updated_at: data.updated_at,
      image_url: data.image_url,
      active: data.active,
      topic_summary: data.topic_summary
    };

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
    console.error('Get multiple choice question by ID error:', error);
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

// 문제 ?�이??버전 ?�큰 조회 (캐시 무효?�용)
async function getQuestionsDataVersion(supabaseClient) {
  try {
    console.log('Getting questions data version...');
    
    // ???�이블의 최신 updated_at??조회
    const [multipleChoiceResult, subjectiveResult] = await Promise.all([
      supabaseClient
        .from('questions_multiple_choice')
        .select('updated_at')
        .order('updated_at', { ascending: false })
        .limit(1),
      supabaseClient
        .from('questions_subjective')
        .select('updated_at')
        .order('updated_at', { ascending: false })
        .limit(1)
    ]);

    if (multipleChoiceResult.error) {
      console.error('Multiple choice version query error:', multipleChoiceResult.error);
      throw multipleChoiceResult.error;
    }

    if (subjectiveResult.error) {
      console.error('Subjective version query error:', subjectiveResult.error);
      throw subjectiveResult.error;
    }

    // 최신 updated_at 값들 추출
    const mcLatest = multipleChoiceResult.data?.[0]?.updated_at || '1970-01-01T00:00:00Z';
    const subLatest = subjectiveResult.data?.[0]?.updated_at || '1970-01-01T00:00:00Z';

    // ??최신 ?�간??버전?�로 ?�용
    const version = mcLatest > subLatest ? mcLatest : subLatest;

    console.log('Data version:', version);

    return new Response(JSON.stringify({
      ok: true,
      data: { version }
    }), {
      headers: {
        ...corsHeaders,
        'Content-Type': 'application/json'
      }
    });
  } catch (error) {
    console.error('Get questions data version error:', error);
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

// 번역할 문제들 조회 (subjective 타입만)
async function getProblemsForTranslation(supabaseClient, filters = {}) {
  try {
    console.log('Getting subjective problems for translation with filters:', filters);
    
    // subjective 문제만 조회 (객관식 제외)
    const subjectiveResult = await getSubjectiveQuestions(supabaseClient, filters);
    
    // 결과 파싱
    const subData = subjectiveResult.ok ? JSON.parse(await subjectiveResult.text()).data : [];
    
    console.log(`Found ${subData.length} subjective problems for translation`);
    
    return new Response(JSON.stringify({
      ok: true,
      data: subData
    }), {
      headers: {
        ...corsHeaders,
        'Content-Type': 'application/json'
      }
    });
  } catch (error) {
    console.error('Get problems for translation error:', error);
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

// i18n 문제 저장
async function saveI18nProblem(supabaseClient, params) {
  try {
    const { problem_data } = params;
    
    console.log('🔄 saveI18nProblem 함수 시작');
    console.log('📥 받은 파라미터:', JSON.stringify(params, null, 2));
    
    if (!problem_data) {
      console.log('❌ problem_data가 없습니다');
      return new Response(JSON.stringify({
        ok: false,
        error: "problem_data is required"
      }), {
        status: 400,
        headers: {
          ...corsHeaders,
          'Content-Type': 'application/json'
        }
      });
    }

    console.log('💾 i18n 테이블에 저장할 데이터:');
    console.log('   - source_problem_id:', problem_data.source_problem_id);
    console.log('   - lang:', problem_data.lang);
    console.log('   - category:', problem_data.category);
    console.log('   - title:', problem_data.title?.substring(0, 50) + '...');

    console.log('🔄 Supabase insert 시작...');
    console.log('📊 삽입할 데이터 상세 정보:');
    console.log(JSON.stringify(problem_data, null, 2));
    
    // 외래 키 제약 조건이 없으므로 source_problem_id 검증 생략
    console.log('💾 외래 키 제약 조건 없이 i18n 테이블에 저장 중...');
    console.log('   - source_problem_id:', problem_data.source_problem_id);
    
    const { data, error } = await supabaseClient
      .from('qlearn_problems_i18n')
      .insert([problem_data])
      .select()
      .single();

    if (error) {
      console.error('❌ Supabase insert 오류 상세 정보:');
      console.error('   - 오류 코드:', error.code);
      console.error('   - 오류 메시지:', error.message);
      console.error('   - 오류 세부사항:', error.details);
      console.error('   - 오류 힌트:', error.hint);
      
      return new Response(JSON.stringify({
        ok: false,
        error: error.message,
        error_code: error.code,
        error_details: error.details,
        error_hint: error.hint,
        attempted_data: problem_data
      }), {
        status: 400,
        headers: {
          ...corsHeaders,
          'Content-Type': 'application/json'
        }
      });
    }

    console.log('✅ i18n 문제 저장 성공:', data.id);

    return new Response(JSON.stringify({
      ok: true,
      data: data,
      message: 'i18n 문제 저장 성공',
      inserted_id: data.id
    }), {
      headers: {
        ...corsHeaders,
        'Content-Type': 'application/json'
      }
    });
  } catch (error) {
    console.error('❌ saveI18nProblem 오류:', error);
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

// i18n 문제 조회
async function getI18nProblems(supabaseClient, filters = {}) {
  try {
    console.log('Getting i18n problems with filters:', filters);
    
    let query = supabaseClient.from('qlearn_problems_i18n').select('*');
    
    // 필터 적용
    if (filters.source_problem_id) query = query.eq('source_problem_id', filters.source_problem_id);
    if (filters.lang) query = query.eq('lang', filters.lang);
    if (filters.category) query = query.eq('category', filters.category);
    if (filters.difficulty) query = query.eq('difficulty', filters.difficulty);
    if (filters.active !== undefined) query = query.eq('active', filters.active);

    const { data, error } = await query.order('created_at', {
      ascending: false
    });

    if (error) {
      console.error('Supabase select error:', error);
      throw error;
    }

    return new Response(JSON.stringify({
      ok: true,
      data: data || []
    }), {
      headers: {
        ...corsHeaders,
        'Content-Type': 'application/json'
      }
    });
  } catch (error) {
    console.error('Get i18n problems error:', error);
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
