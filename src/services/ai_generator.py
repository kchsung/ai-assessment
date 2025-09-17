import json, random, re
from datetime import datetime
import streamlit as st
from openai import OpenAI
from src.config import get_secret
from src.constants import ASSESSMENT_AREAS, DIFFICULTY_LEVELS

class AIQuestionGenerator:
    def __init__(self):
        api_key = get_secret("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is missing")
        self.client = OpenAI(api_key=api_key)
        self.assessment_areas = ASSESSMENT_AREAS
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
        """기본 user 프롬프트 구성"""
        guide = self.default_difficulty_guides.get(difficulty, "적절한 난이도의 문제")
        
        return f"""
다음 조건에 맞는 AI 활용능력평가 문제를 생성해주세요:

평가 영역: {self.assessment_areas[area]}
난이도: {self.difficulty_levels[difficulty]} - {guide}
문제 유형: {question_type}
추가 맥락: {context if context else '없음'}

요구사항:
1. 실무 상황을 반영한 현실적인 문제
2. AI를 도구로 활용하는 능력을 평가
3. 단순 암기가 아닌 응용력 평가
4. {difficulty} 수준에 맞는 복잡도

다음 형식으로 응답해주세요:
{{
    "question": "문제 내용",
    "scenario": "상황 설명 (있는 경우)",
    "options": ["선택지1", "선택지2", "선택지3", "선택지4"],
    "correct_answer": 1,
    "requirements": ["요구사항1", "요구사항2"],
    "evaluation_criteria": ["평가기준1 (배점)", "평가기준2 (배점)"],
    "sample_solution": "모범 답안 또는 해결 방향",
    "key_points": ["핵심 평가 포인트1", "핵심 평가 포인트2"]
}}
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
            qdata = json.loads(m.group()) if m else {"question": content or ""}
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            q = {
                "id": f"Q_AI_{ts}_{random.randint(1000,9999)}",
                "area": ASSESSMENT_AREAS[area],
                "difficulty": DIFFICULTY_LEVELS[difficulty],
                "type": question_type,
                "question": qdata.get("question",""),
                "ai_generated": True,
                "metadata": {
                    "generated_at": ts,
                    "model": model,
                    "scenario": qdata.get("scenario",""),
                    "sample_solution": qdata.get("sample_solution"),
                    "key_points": qdata.get("key_points"),
                },
            }
            if qdata.get("options"): q["options"]=qdata["options"]; q["correct_answer"]=qdata.get("correct_answer")
            if qdata.get("requirements"): q["requirements"]=qdata["requirements"]
            if qdata.get("evaluation_criteria"): q["evaluation_criteria"]=qdata["evaluation_criteria"]
            st.session_state.last_raw_content = content
            return q
        except Exception as e:
            st.error(f"AI 문제 생성 실패: {e}")
            return None
