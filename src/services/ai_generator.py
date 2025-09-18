import json, random, re
from datetime import datetime
import streamlit as st
from openai import OpenAI
from src.config import get_secret
from src.constants import ASSESSMENT_AREAS, ASSESSMENT_AREAS_DISPLAY, DIFFICULTY_LEVELS
from src.prompts.default_prompts import DEFAULT_SYSTEM_PROMPT, DEFAULT_DIFFICULTY_GUIDES, DIFFICULTY_TIME_MAPPING
from src.prompts.multiple_choice_template import get_multiple_choice_prompt
from src.prompts.subjective_template import get_subjective_prompt

class AIQuestionGenerator:
    def __init__(self):
        api_key = get_secret("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is missing")
        self.client = OpenAI(api_key=api_key)
        self.assessment_areas = ASSESSMENT_AREAS_DISPLAY
        self.difficulty_levels = DIFFICULTY_LEVELS
        
        # 기본 프롬프트 템플릿 (외부 파일에서 import)
        self.default_system_prompt = DEFAULT_SYSTEM_PROMPT
        self.default_difficulty_guides = DEFAULT_DIFFICULTY_GUIDES
        self.difficulty_time_mapping = DIFFICULTY_TIME_MAPPING

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
            
            # pharma_distribution의 경우 특정 ID의 프롬프트 사용
            if area == "pharma_distribution":
                try:
                    pharma_prompt = db.get_prompt_by_id("2731d7c8-32d5-45d2-bef9-52ad68510bb8")
                    if pharma_prompt:
                        system_prompt = pharma_prompt  # 기본 프롬프트 대신 특정 프롬프트 사용
                    else:
                        st.warning("태전제약유통 전용 프롬프트를 찾을 수 없습니다. 기본 프롬프트를 사용합니다.")
                except Exception as e:
                    st.warning(f"태전제약유통 전용 프롬프트 조회 실패: {e}. 기본 프롬프트를 사용합니다.")
            elif area_prompts:
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
        guide = self.default_difficulty_guides[difficulty]
        time_limit = self.difficulty_time_mapping[difficulty]
        
        if question_type == "multiple_choice":
            return self._build_multiple_choice_prompt(area, difficulty, guide, time_limit, context)
        else:  # subjective
            return self._build_subjective_prompt(area, difficulty, guide, time_limit, context)
    
    def _build_multiple_choice_prompt(self, area: str, difficulty: str, guide: str, time_limit: str, context: str):
        """객관식 문제 생성 프롬프트"""
        # work_application, daily_problem_solving, pharma_distribution의 경우 topic을 동적으로 설정
        if area in ["work_application", "daily_problem_solving", "pharma_distribution"]:
            topic_instruction = f"topic 필드에는 {self.assessment_areas[area]}와 관련된 구체적인 직무나 상황을 설정해주세요 (예: '마케팅 담당자', '고객 서비스', '일상 업무 효율화', '제약회사 영업팀', '유통업체 물류팀' 등)"
            area_display = f"{self.assessment_areas[area]} (구체적인 직무/상황으로 설정)"
        else:
            topic_instruction = f"topic 필드에는 '{self.assessment_areas[area]}'를 그대로 사용해주세요"
            area_display = self.assessment_areas[area]
        
        return get_multiple_choice_prompt(
            area_display=area_display,
            difficulty_display=self.difficulty_levels[difficulty],
            guide=guide,
            time_limit=time_limit,
            context=context,
            assessment_area=self.assessment_areas[area],
            topic_instruction=topic_instruction,
            difficulty=difficulty
        )

    def _build_subjective_prompt(self, area: str, difficulty: str, guide: str, time_limit: str, context: str):
        """주관식 문제 생성 프롬프트"""
        # work_application, daily_problem_solving, pharma_distribution의 경우 topic을 동적으로 설정
        if area in ["work_application", "daily_problem_solving", "pharma_distribution"]:
            topic_instruction = f"topic 필드에는 {self.assessment_areas[area]}와 관련된 구체적인 직무나 상황을 설정해주세요 (예: '마케팅 담당자', '고객 서비스', '일상 업무 효율화', '제약회사 영업팀', '유통업체 물류팀' 등)"
            area_display = f"{self.assessment_areas[area]} (구체적인 직무/상황으로 설정)"
            task_template = "나는 현재 [구체적인 직무/상황] 상황에 있다. 다음 상황에서..."
        else:
            topic_instruction = f"topic 필드에는 '{self.assessment_areas[area]}'를 그대로 사용해주세요"
            area_display = self.assessment_areas[area]
            task_template = f"나는 현재 {self.assessment_areas[area]} 상황에 있다. 다음 상황에서..."
        
        return get_subjective_prompt(
            area_display=area_display,
            difficulty_display=self.difficulty_levels[difficulty],
            guide=guide,
            time_limit=time_limit,
            context=context,
            assessment_area=self.assessment_areas[area],
            topic_instruction=topic_instruction,
            task_template=task_template,
            difficulty=difficulty
        )

    def generate_with_ai(self, area: str, difficulty: str, question_type: str, context: str = ""):
        # 데이터베이스에서 프롬프트 조회 시도
        db_system_prompt, db_user_prompt = self._get_prompts_from_db(area, difficulty, question_type)
        
        # 데이터베이스 프롬프트가 있으면 사용, 없으면 기본 프롬프트 사용
        if db_system_prompt and db_user_prompt:
            system_prompt = db_system_prompt
            user_prompt = db_user_prompt
            if context:
                user_prompt = user_prompt.replace("추가 맥락: 없음", f"추가 맥락: {context}")
            st.info("📋 데이터베이스 프롬프트 사용 중")
        else:
            # 기본 프롬프트 사용
            system_prompt = self.default_system_prompt
            user_prompt = self._build_user_prompt(area, difficulty, question_type, context)
            st.info("📝 기본 프롬프트 사용 중")
            
        try:
            # 세션 상태에서 선택된 모델 가져오기 (기본값: gpt-5)
            model = st.session_state.get("selected_model", "gpt-5")
            
            resp = self.client.chat.completions.create(
                model=model,
                messages=[{"role":"system","content":system_prompt},
                          {"role":"user","content":user_prompt}]
            )
            content = resp.choices[0].message.content
            m = re.search(r"\{[\s\S]*\}", content or "")
            if m:
                # JSON에서 trailing comma 제거
                json_str = m.group()
                # 배열과 객체의 trailing comma 제거
                json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
                qdata = json.loads(json_str)
            else:
                qdata = {"title": content or ""}
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
