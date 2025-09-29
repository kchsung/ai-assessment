// Edge Function: ai-bank/index.ts (save_qlearn_problem 액션 추가된 버전)
import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type'
};

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
    console.log('Params with empty values:', Object.entries(params).filter(([k, v]) => v === ''));
    
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
    
    // 모든 NOT NULL 필드에 기본값 제공
    const problemData = {
      lang: cleanValue(params.lang) || 'kr',
      category: cleanValue(params.category) || 'life',
      topic: cleanValue(params.topic) || '기본 주제',
      difficulty: cleanValue(params.difficulty) || '보통',
      time_limit: cleanValue(params.time_limit) || '5분',
      topic_summary: cleanValue(params.topic_summary) || '기본 주제 요약',
      title: cleanValue(params.title) || '기본 제목',
      scenario: cleanValue(params.scenario) || '기본 시나리오',
      goal: params.goal || [],
      first_question: params.first_question || [],
      requirements: params.requirements || [],
      constraints: params.constraints || [],
      guide: params.guide || {},
      evaluation: params.evaluation || [],
      task: cleanValue(params.task) || '기본 과제',
      active: params.active !== undefined ? params.active : false,
      created_at: cleanValue(params.created_at) || new Date().toISOString(),
      updated_at: cleanValue(params.updated_at) || new Date().toISOString()
    };
    
    // 선택적 필드들 추가
    if (params.reference && Object.keys(params.reference).length > 0) {
      problemData.reference = params.reference;
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
    
    // UUID 필드들을 완전히 제거 (Supabase에서 자동 생성되도록)
    const uuidFields = ['id', 'created_by'];
    uuidFields.forEach(field => {
      if (problemData[field] !== undefined) {
        delete problemData[field];
        console.log(`🗑️ UUID 필드 제거: ${field}`);
      }
    });

    console.log('Final problemData keys:', Object.keys(problemData));
    console.log('Final problemData:', JSON.stringify(problemData, null, 2));

    const { data, error } = await supabaseClient
      .from('qlearn_problems')
      .insert(problemData)
      .select();

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
    if (filters.category) query = query.eq('category', filters.category);
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
        goal: r.goal ? JSON.parse(r.goal) : [],
        first_question: r.first_question ? JSON.parse(r.first_question) : [],
        requirements: r.requirements ? JSON.parse(r.requirements) : [],
        constraints: r.constraints ? JSON.parse(r.constraints) : [],
        guide: r.guide ? JSON.parse(r.guide) : {},
        evaluation: r.evaluation ? JSON.parse(r.evaluation) : [],
        task: r.task,
        created_by: r.created_by,
        created_at: r.created_at,
        updated_at: r.updated_at,
        reference: r.reference ? JSON.parse(r.reference) : {},
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

    // JSON 필드들은 그대로 유지 (Supabase가 자동으로 JSONB로 처리)
    const updateData = { ...updates };
    
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
      // 새로운 필드들
      lang: metadata.lang || 'kr',
      category: metadata.category || 'interview',
      topic: metadata.topic || null,
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
      // review_done 필드 추가
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
    if (filters.topic) query = query.eq('topic', filters.topic);
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
      const metadata = r.metadata ? JSON.parse(r.metadata) : {};
      // 새로운 필드들을 메타데이터에 병합
      const newFields = {
        lang: r.lang || 'kr',
        category: r.category || 'interview',
        topic: r.topic,
        time_limit: r.time_limit,
        topic_summary: r.topic_summary,
        scenario: r.scenario,
        goal: r.goal ? JSON.parse(r.goal) : [],
        task: r.task,
        reference: r.reference ? JSON.parse(r.reference) : {},
        first_question: r.first_question ? JSON.parse(r.first_question) : [],
        constraints: r.constraints ? JSON.parse(r.constraints) : [],
        guide: r.guide ? JSON.parse(r.guide) : {},
        evaluation: r.evaluation ? JSON.parse(r.evaluation) : [],
        steps: r.steps ? JSON.parse(r.steps) : []
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
        options: r.options ? JSON.parse(r.options) : null,
        correct_answer: r.correct_answer,
        requirements: r.requirements ? JSON.parse(r.requirements) : null,
        evaluation_criteria: r.evaluation_criteria ? JSON.parse(r.evaluation_criteria) : null,
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
