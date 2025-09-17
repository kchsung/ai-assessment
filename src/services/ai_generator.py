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

    def generate_with_ai(self, area: str, difficulty: str, question_type: str, context: str = ""):
        system_prompt = (
            "당신은 AI 활용능력평가 전문가입니다. 실무에 가까운 평가 문제를 생성하세요."
        )
        guide = {
            "basic": "기본 개념과 도구 사용",
            "intermediate": "복합 문제 해결과 도구 조합",
            "advanced": "전략/시스템 설계와 비즈니스 임팩트",
        }
        user_prompt = f"""
평가 영역: {ASSESSMENT_AREAS[area]}
난이도: {DIFFICULTY_LEVELS[difficulty]} - {guide[difficulty]}
문제 유형: {question_type}
추가 맥락: {context or '없음'}

다음 JSON 형식으로만 응답:
{{
  "question": "문제 내용",
  "scenario": "상황 설명",
  "options": ["A","B","C","D"],
  "correct_answer": 1,
  "requirements": ["요구1","요구2"],
  "evaluation_criteria": ["기준1(배점)","기준2(배점)"],
  "sample_solution": "해결 방향",
  "key_points": ["핵심1","핵심2"]
}}
"""
        try:
            resp = self.client.chat.completions.create(
                model="gpt-5-nano",
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
                    "model": "gpt-5-nano",
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
