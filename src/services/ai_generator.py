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

    def generate_with_ai(self, area: str, difficulty: str, question_type: str, context: str = ""):
        system_prompt = (
            "당신은 AI 활용능력평가 전문가입니다. 실무에서 AI를 효과적으로 활용하는 능력을 평가하는 문제를 생성해주세요. "
            "문제는 단순히 AI로 해결할 수 있는 것이 아니라, 인간의 판단력과 창의성이 필요한 것이어야 합니다."
        )
        guide = {
            "basic": "기본 개념 이해와 단순 도구 사용 능력을 평가. 명확한 정답이 있는 문제.",
            "intermediate": "복합적 문제 해결과 도구 조합 활용 능력을 평가. 여러 접근법이 가능한 문제.",
            "advanced": "전략적 사고와 시스템 설계 능력을 평가. 비즈니스 임팩트를 고려한 종합적 문제.",
        }
        user_prompt = f"""
다음 조건에 맞는 AI 활용능력평가 문제를 생성해주세요:

평가 영역: {self.assessment_areas[area]}
난이도: {self.difficulty_levels[difficulty]} - {guide[difficulty]}
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
