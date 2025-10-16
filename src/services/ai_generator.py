import json, random, re
from datetime import datetime
import streamlit as st
from openai import OpenAI
from src.config import get_secret
from src.constants import ASSESSMENT_AREAS, DIFFICULTY_LEVELS
from src.prompts.default_prompts import DEFAULT_SYSTEM_PROMPT, DEFAULT_DIFFICULTY_GUIDES, DIFFICULTY_TIME_MAPPING
from src.prompts.multiple_choice_template import get_multiple_choice_prompt
from src.prompts.subjective_template import get_subjective_prompt

class AIQuestionGenerator:
    def __init__(self):
        api_key = get_secret("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is missing")
        self.client = OpenAI(api_key=api_key)
        self.assessment_areas = ASSESSMENT_AREAS
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
                    # subjective 문제 유형일 때는 특정 프롬프트 ID 사용
                    if question_type == "subjective":
                        pharma_prompt = db.get_prompt_by_id("1b89bce9-1916-4677-b520-87c7ec532524")
                    else:
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

    def _build_system_prompt(self):
        """시스템 프롬프트를 동적으로 구성"""
        base_prompt = self.default_system_prompt
        
        # 난이도별 평가 기준 추가
        difficulty_guides = "\n\n난이도별 평가 기준:\n"
        for key, guide in self.default_difficulty_guides.items():
            difficulty_guides += f"- {key}: {guide}\n"
        
        # 난이도별 시간 제한 추가
        time_mapping = "\n난이도별 시간 제한:\n"
        for key, time_limit in self.difficulty_time_mapping.items():
            time_mapping += f"- {key}: {time_limit}\n"
        
        # 스텝 구성 규칙 추가
        step_rules = "\n스텝 구성 규칙:\n"
        step_rules += "- very easy: 1~2 스텝\n"
        step_rules += "- easy: 2~3 스텝\n"
        step_rules += "- normal: 3~5 스텝\n"
        step_rules += "- hard: 5~7 스텝\n"
        step_rules += "- very hard: 7~9 스텝"
        
        return base_prompt + difficulty_guides + time_mapping + step_rules

    def _build_user_prompt(self, area: str, difficulty: str, question_type: str, context: str = ""):
        """기본 user 프롬프트 구성 - 새로운 JSON 포맷 지원"""
        guide = self.default_difficulty_guides[difficulty]
        time_limit = self.difficulty_time_mapping[difficulty]
        
        if question_type == "multiple_choice":
            return self._build_multiple_choice_prompt(area, difficulty, guide, time_limit, context)
        else:  # subjective
            return self._build_subjective_prompt(area, difficulty, guide, time_limit, context)
    
    def _build_multiple_choice_prompt(self, area: str, difficulty: str, guide: str, time_limit: str, context: str):
        """Multiple choice problem generation prompt"""
        # work_application, daily_problem_solving, pharma_distribution, learning_concept의 경우 topic을 동적으로 설정
        if area in ["work_application", "daily_problem_solving", "pharma_distribution", "learning_concept"]:
            topic_instruction = f"topic 필드에는 {self.assessment_areas[area]}와 관련된 구체적인 직무나 상황을 설정해주세요 (예: '마케팅 담당자', '고객 서비스', '일상 업무 효율화', '제약회사 영업팀', '유통업체 물류팀', '학습자', '교육과정' 등)"
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
        """Subjective problem generation prompt"""
        # work_application, daily_problem_solving, pharma_distribution, learning_concept의 경우 topic을 동적으로 설정
        if area in ["work_application", "daily_problem_solving", "pharma_distribution", "learning_concept"]:
            topic_instruction = f"topic 필드에는 {self.assessment_areas[area]}와 관련된 구체적인 직무나 상황을 설정해주세요 (예: '마케팅 담당자', '고객 서비스', '일상 업무 효율화', '제약회사 영업팀', '유통업체 물류팀', '학습자', '교육과정' 등)"
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

    def generate_with_ai(self, area: str, difficulty: str, question_type: str, user_prompt_extra: str = "", system_prompt_extra: str = ""):
        # 데이터베이스에서 프롬프트 조회 시도
        db_system_prompt, db_user_prompt = self._get_prompts_from_db(area, difficulty, question_type)
        
        # 기본 시스템 프롬프트 구성
        if db_system_prompt and db_user_prompt:
            # 데이터베이스 시스템 프롬프트에 난이도 기준 추가
            base_system_prompt = db_system_prompt + "\n\n" + self._build_system_prompt().split("난이도별 평가 기준:")[1]
            # 데이터베이스 user 프롬프트에 사용자 시스템 프롬프트를 context로 추가
            if system_prompt_extra.strip():
                base_user_prompt = db_user_prompt + f"\n\n사용자 추가 요구사항: {system_prompt_extra}"
            else:
                base_user_prompt = db_user_prompt
            st.info("📋 데이터베이스 프롬프트 사용 중")
        else:
            # 기본 프롬프트 사용 - 사용자 시스템 프롬프트를 context로 전달
            base_system_prompt = self._build_system_prompt()
            base_user_prompt = self._build_user_prompt(area, difficulty, question_type, system_prompt_extra)
            st.info("📝 기본 프롬프트 사용 중")
        
        # 시스템 프롬프트 구성: 기본 프롬프트 + 사용자 프롬프트 (사용자 프롬프트가 있으면)
        if system_prompt_extra.strip():
            system_prompt = base_system_prompt + "\n\n[사용자 추가 시스템 요구사항]\n" + system_prompt_extra
            st.info("🎯 기본 프롬프트 + 사용자 시스템 프롬프트 적용 중")
        else:
            system_prompt = base_system_prompt
        
        # User 프롬프트 구성: 기본 프롬프트 + 사용자 프롬프트 (사용자 프롬프트가 있으면)
        if user_prompt_extra.strip():
            user_prompt = base_user_prompt + "\n\n[사용자 추가 요구사항]\n" + user_prompt_extra
        else:
            user_prompt = base_user_prompt
            
        try:
            # 세션 상태에서 선택된 모델 가져오기 (기본값: gpt-5)
            model = st.session_state.get("selected_model", "gpt-5")
            
            resp = self.client.chat.completions.create(
                model=model,
                messages=[{"role":"system","content":system_prompt},
                          {"role":"user","content":user_prompt}]
            )
            content = resp.choices[0].message.content
            # Streamlit 상태값 제거 (key로 시작하는 패턴 제거)
            if content:
                content = re.sub(r'key\w+\s*', '', content)
            
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
                    "area": area,  # 원본 area 값 저장
                    "category": ASSESSMENT_AREAS[area],  # 영어 버전으로 DB 저장
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
                    "area": area,  # 원본 area 값 저장
                    "category": ASSESSMENT_AREAS[area],  # 영어 버전으로 DB 저장
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
