import json, random, re
from datetime import datetime
import streamlit as st
from openai import OpenAI
from src.config import get_secret
from src.constants import ASSESSMENT_AREAS, ASSESSMENT_AREAS_DISPLAY, DIFFICULTY_LEVELS

class AIQuestionGenerator:
    def __init__(self):
        api_key = get_secret("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is missing")
        self.client = OpenAI(api_key=api_key)
        self.assessment_areas = ASSESSMENT_AREAS_DISPLAY
        self.difficulty_levels = DIFFICULTY_LEVELS
        
        # 기본 프롬프트 템플릿
        self.default_system_prompt = (
            "당신은 AI 활용능력평가 전문가입니다. 실무에서 AI를 효과적으로 활용하는 능력을 평가하는 문제를 생성해주세요. "
            "문제는 단순히 AI로 해결할 수 있는 것이 아니라, 인간의 판단력과 창의성이 필요한 것이어야 합니다."
        )
        
        self.default_difficulty_guides = {
            "very_easy": "기본 개념 이해와 단순 도구 사용 능력을 평가. 명확한 정답이 있는 문제.",
            "easy": "기본 도구 활용과 간단한 문제 해결 능력을 평가. 단계별 접근이 가능한 문제.",
            "medium": "복합적 문제 해결과 도구 조합 활용 능력을 평가. 여러 접근법이 가능한 문제.",
            "hard": "전략적 사고와 시스템 설계 능력을 평가. 비즈니스 임팩트를 고려한 종합적 문제.",
            "very_hard": "혁신적 사고와 복잡한 시스템 통합 능력을 평가. 창의적 해결책이 필요한 고도화된 문제.",
        }
        
        # 난이도별 시간 제한 매핑
        self.difficulty_time_mapping = {
            "very_easy": "3분 이내",
            "easy": "4분 이내", 
            "medium": "5분 이내",
            "hard": "7분 이내",
            "very_hard": "10분 이내"
        }

    def _get_prompts_from_db(self, area: str, difficulty: str, question_type: str):
        """데이터베이스에서 프롬프트 조회"""
        try:
            db = st.session_state.get("db")
            if not db:
                return None, None
            
            # 평가 영역별 프롬프트 조회
            area_prompts = db.get_prompts(category=f"area_{area}")
            difficulty_prompts = db.get_prompts(category=f"difficulty_{difficulty}")
            type_prompts = db.get_prompts(category=f"type_{question_type}")
            
            # system 프롬프트 조합
            system_prompt = self.default_system_prompt
            if area_prompts:
                system_prompt += f"\n\n평가 영역 특화 지침:\n{area_prompts[0]['prompt_text']}"
            
            # user 프롬프트 조합
            user_prompt = self._build_user_prompt(area, difficulty, question_type)
            if difficulty_prompts:
                user_prompt += f"\n\n난이도별 특화 요구사항:\n{difficulty_prompts[0]['prompt_text']}"
            if type_prompts:
                user_prompt += f"\n\n문제 유형별 특화 지침:\n{type_prompts[0]['prompt_text']}"
            
            return system_prompt, user_prompt
            
        except Exception as e:
            st.warning(f"프롬프트 조회 실패, 기본 프롬프트 사용: {e}")
            return None, None

    def _build_user_prompt(self, area: str, difficulty: str, question_type: str, context: str = ""):
        """기본 user 프롬프트 구성 - 새로운 JSON 포맷 지원"""
        guide = self.default_difficulty_guides.get(difficulty, "적절한 난이도의 문제")
        time_limit = self.difficulty_time_mapping.get(difficulty, "5분 이내")
        
        if question_type == "multiple_choice":
            return self._build_multiple_choice_prompt(area, difficulty, guide, time_limit, context)
        else:  # subjective
            return self._build_subjective_prompt(area, difficulty, guide, time_limit, context)
    
    def _build_multiple_choice_prompt(self, area: str, difficulty: str, guide: str, time_limit: str, context: str):
        """객관식 문제 생성 프롬프트"""
        # work_application과 daily_problem_solving의 경우 topic을 동적으로 설정
        if area in ["work_application", "daily_problem_solving"]:
            topic_instruction = f"topic 필드에는 {self.assessment_areas[area]}와 관련된 구체적인 직무나 상황을 설정해주세요 (예: '마케팅 담당자', '고객 서비스', '일상 업무 효율화' 등)"
            area_display = f"{self.assessment_areas[area]} (구체적인 직무/상황으로 설정)"
        else:
            topic_instruction = f"topic 필드에는 '{self.assessment_areas[area]}'를 그대로 사용해주세요"
            area_display = self.assessment_areas[area]
        
        return f"""
다음 조건에 맞는 AI 활용능력평가 객관식 문제를 생성해주세요:

평가 영역: {area_display}
난이도: {self.difficulty_levels[difficulty]} - {guide}
시간 제한: {time_limit}
사용자 추가 요구사항: {context if context else '없음'}

요구사항:
1. 실무 상황을 반영한 현실적인 문제
2. AI를 도구로 활용하는 능력을 평가
3. 단계별 접근이 필요한 문제
4. {difficulty} 수준에 맞는 복잡도

다음 JSON 형식으로 응답해주세요:
{{
  "lang": "kr",
  "category": "{self.assessment_areas[area]}",
  "problemTitle": "문제 제목",
  "topic": "{self.assessment_areas[area] if area not in ['work_application', 'daily_problem_solving'] else '구체적인 직무/상황'}",
  "difficulty": "{difficulty}",
  "estimatedTime": "{time_limit}",
  "scenario": "면접 시뮬레이션 배경 상황 설명",
  "reference": {{
    "metrics": {{"paid_conv_rate": "유료 전환율 2.3%", "retention_d7": "7일 리텐션 45%"}},
    "funnel": {{"signup": "회원가입 단계별 데이터"}},
    "user_feedback": [{{"tag": "사용자 피드백 태그", "content": "피드백 내용"}}],
    "competitor_strategy": {{"campaign": {{"A": "경쟁사 A 전략", "B": "경쟁사 B 전략"}}}}
  }},
  "steps": [
    {{
      "step": 1,
      "title": "맥락 파악",
      "question": "핵심 질문 내용",
      "ref_paths": ["ref.metrics.paid_conv_rate"],
      "options": [
        {{"id":"A","text":"선택지 A","feedback":"피드백 A","weight":0.85,"ref_paths":["ref.funnel.signup"]}},
        {{"id":"B","text":"선택지 B","feedback":"피드백 B","weight":0.75,"ref_paths":["ref.user_feedback[0].tag"]}},
        {{"id":"C","text":"선택지 C","feedback":"피드백 C","weight":1.0,"ref_paths":["ref.metrics.retention_d7"]}},
        {{"id":"D","text":"선택지 D","feedback":"피드백 D","weight":0.65,"ref_paths":["ref.competitor_strategy.campaign.B"]}}
      ],
      "answer":"C"
    }}
  ]
}}

중요: {topic_instruction}
"""

    def _build_subjective_prompt(self, area: str, difficulty: str, guide: str, time_limit: str, context: str):
        """주관식 문제 생성 프롬프트"""
        # work_application과 daily_problem_solving의 경우 topic을 동적으로 설정
        if area in ["work_application", "daily_problem_solving"]:
            topic_instruction = f"topic 필드에는 {self.assessment_areas[area]}와 관련된 구체적인 직무나 상황을 설정해주세요 (예: '마케팅 담당자', '고객 서비스', '일상 업무 효율화' 등)"
            area_display = f"{self.assessment_areas[area]} (구체적인 직무/상황으로 설정)"
            task_template = "나는 현재 [구체적인 직무/상황] 면접에 참여하고 있다. 다음 상황에서..."
        else:
            topic_instruction = f"topic 필드에는 '{self.assessment_areas[area]}'를 그대로 사용해주세요"
            area_display = self.assessment_areas[area]
            task_template = f"나는 현재 {self.assessment_areas[area]} 면접에 참여하고 있다. 다음 상황에서..."
        
        return f"""
다음 조건에 맞는 AI 활용능력평가 주관식 문제를 생성해주세요:

평가 영역: {area_display}
난이도: {self.difficulty_levels[difficulty]} - {guide}
시간 제한: {time_limit}
사용자 추가 요구사항: {context if context else '없음'}

요구사항:
1. 실무 상황을 반영한 현실적인 문제
2. AI를 도구로 활용하는 능력을 평가
3. 창의적 사고와 종합적 문제 해결 능력 평가
4. {difficulty} 수준에 맞는 복잡도

다음 JSON 형식으로 응답해주세요:
{{
  "lang": "kr",
  "category": "{self.assessment_areas[area]}",
  "topic": "{self.assessment_areas[area] if area not in ['work_application', 'daily_problem_solving'] else '구체적인 직무/상황'}",
  "difficulty": "{difficulty}",
  "time_limit": "{time_limit}",
  "topic_summary": "주제 요약 설명",
  "title": "문제 제목",
  "scenario": "면접 시뮬레이션 배경 + 출처",
  "goal": ["1단계: 첫 번째 목표", "2단계: 두 번째 목표"],
  "task": "{task_template}",
  "reference": {{
    "metrics": {{"key_metric": "핵심 지표 설명"}},
    "funnel": {{"stage": "단계별 데이터"}},
    "user_feedback": [{{"type": "피드백 유형", "content": "피드백 내용"}}],
    "competitor_strategy": {{"approach": "경쟁사 접근법"}}
  }},
  "first_question": ["첫 번째 질문", "두 번째 질문", "세 번째 질문"],
  "requirements": ["요구사항 1", "요구사항 2"],
  "constraints": ["개인정보 포함 금지", "금칙어 사용 금지"],
  "guide": {{
    "method": "Search–Compare–Choose–Verify",
    "alternatives": [
      "Rapid Research & Snapshot",
      "Iterative Q-A Refinement", 
      "Decompose-Solve-Recombine"
    ]
  }},
  "evaluation": [
    "목표 적합성·정확성 30%",
    "근거·출처 신뢰도 25%",
    "실행 가능성·구체성 25%",
    "명료성·형식 준수 20%"
  ]
}}

중요: {topic_instruction}
"""

    def generate_with_ai(self, area: str, difficulty: str, question_type: str, context: str = ""):
        # 데이터베이스에서 프롬프트 조회 시도
        db_system_prompt, db_user_prompt = self._get_prompts_from_db(area, difficulty, question_type)
        
        # 데이터베이스 프롬프트가 있으면 사용, 없으면 기본 프롬프트 사용
        if db_system_prompt and db_user_prompt:
            system_prompt = db_system_prompt
            user_prompt = db_user_prompt
            if context:
                user_prompt = user_prompt.replace("추가 맥락: 없음", f"추가 맥락: {context}")
        else:
            # 기본 프롬프트 사용
            system_prompt = self.default_system_prompt
            user_prompt = self._build_user_prompt(area, difficulty, question_type, context)
        try:
            # 세션 상태에서 선택된 모델 가져오기 (기본값: gpt-5-nano)
            model = st.session_state.get("selected_model", "gpt-5-nano")
            
            resp = self.client.chat.completions.create(
                model=model,
                messages=[{"role":"system","content":system_prompt},
                          {"role":"user","content":user_prompt}]
            )
            content = resp.choices[0].message.content
            m = re.search(r"\{[\s\S]*\}", content or "")
            qdata = json.loads(m.group()) if m else {"title": content or ""}
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 새로운 JSON 포맷에 맞게 데이터 구조 변환
            if question_type == "multiple_choice":
                q = {
                    "id": f"Q_AI_{ts}_{random.randint(1000,9999)}",
                    "area": ASSESSMENT_AREAS[area],  # 영어 버전으로 DB 저장
                    "difficulty": DIFFICULTY_LEVELS[difficulty],
                    "type": question_type,
                    "question": qdata.get("problemTitle", ""),
                    "ai_generated": True,
                    "metadata": {
                        "generated_at": ts,
                        "model": model,
                        "lang": qdata.get("lang", "kr"),
                        "category": ASSESSMENT_AREAS[area],  # 영어 버전으로 DB 저장
                        "topic": qdata.get("topic", ""),
                        "estimatedTime": qdata.get("estimatedTime", ""),
                        "scenario": qdata.get("scenario", ""),
                        "reference": qdata.get("reference", {}),
                        "steps": qdata.get("steps", [])
                    },
                }
            else:  # subjective
                q = {
                    "id": f"Q_AI_{ts}_{random.randint(1000,9999)}",
                    "area": ASSESSMENT_AREAS[area],  # 영어 버전으로 DB 저장
                    "difficulty": DIFFICULTY_LEVELS[difficulty],
                    "type": question_type,
                    "question": qdata.get("title", ""),
                    "ai_generated": True,
                    "metadata": {
                        "generated_at": ts,
                        "model": model,
                        "lang": qdata.get("lang", "kr"),
                        "category": ASSESSMENT_AREAS[area],  # 영어 버전으로 DB 저장
                        "topic": qdata.get("topic", ""),
                        "time_limit": qdata.get("time_limit", ""),
                        "topic_summary": qdata.get("topic_summary", ""),
                        "scenario": qdata.get("scenario", ""),
                        "goal": qdata.get("goal", []),
                        "task": qdata.get("task", ""),
                        "reference": qdata.get("reference", {}),
                        "first_question": qdata.get("first_question", []),
                        "requirements": qdata.get("requirements", []),
                        "constraints": qdata.get("constraints", []),
                        "guide": qdata.get("guide", {}),
                        "evaluation": qdata.get("evaluation", [])
                    },
                }
            st.session_state.last_raw_content = content
            return q
        except Exception as e:
            st.error(f"AI 문제 생성 실패: {e}")
            return None
