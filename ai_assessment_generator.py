# ai_assessment_generator.py (Edge Function 버전)
import os
import json
import random
from datetime import datetime
from typing import Dict, List, Optional
import sqlite3

import requests
import pandas as pd
import streamlit as st

import plotly.express as px
import plotly.graph_objects as go

from openai import OpenAI

# ===== 환경 변수 로드 =====

# 1) 로컬 개발 환경일 수 있으니 .env를 "가능하면" 읽어둡니다.
try:
    from dotenv import load_dotenv 
    load_dotenv(override=False)   # 이미 설정된 환경변수는 덮어쓰지 않음
except Exception:
    pass  # 클라우드나 미설치 환경에서도 문제없이 통과

def get_secret(name: str, default=None) -> str:
    """
    우선순위:
    1) Streamlit Cloud Secrets (st.secrets)
    2) 환경변수 (os.environ)
    3) 기본값(default) or 에러
    """
    # 1) Streamlit Secrets
    try:
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass

    # 2) OS 환경변수 (로컬 .env 로드 포함)
    val = os.getenv(name)
    if val is not None and val != "":
        return val

    # 3) Default or Error
    if default is not None:
        return default
    raise RuntimeError(f"Missing required secret: {name}")


# ===== OpenAI 설정 (키 하드코딩 금지) =====
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ===== UI 상수 =====
ASSESSMENT_AREAS = {
    "ai_basics": "AI 기초 이해도",
    "prompt_engineering": "프롬프트 엔지니어링",
    "tool_utilization": "AI 도구 활용능력",
    "ethics_security": "AI 윤리/보안 인식",
    "work_application": "업무 적용 능력",
}

DIFFICULTY_LEVELS = {
    "basic": "초급",
    "intermediate": "중급",
    "advanced": "고급",
}

QUESTION_TYPES = {
    "multiple_choice": "객관식",
    "scenario": "시나리오 기반",
    "practical": "실습형",
    "project": "프로젝트형",
}

# ===== Edge Function Client =====
class EdgeDBClient:
    def __init__(self, base_url: Optional[str] = None, token: Optional[str] = None):
        self.base_url = base_url or os.getenv("EDGE_FUNCTION_URL")
        self.token = token or os.getenv("EDGE_SHARED_TOKEN")
        if not self.base_url:
            raise RuntimeError("EDGE_FUNCTION_URL not set in environment (.env)")
        if not self.token:
            raise RuntimeError("EDGE_SHARED_TOKEN not set in environment (.env)")

    def _call(self, action: str, params: Optional[dict] = None):
        headers = {
            "content-type": "application/json",
            "x-edge-token": self.token,
            "authorization": f"Bearer {os.getenv('SUPABASE_ANON_KEY')}"  # <-- 추가

        }
        resp = requests.post(self.base_url, headers=headers, json={"action": action, "params": params or {}})
        if resp.status_code >= 400:
            raise RuntimeError(f"Edge error {resp.status_code}: {resp.text}")
        data = resp.json()
        if not data.get("ok"):
            raise RuntimeError(f"Edge failure: {data.get('error')}")
        return data.get("data")

    # === methods used by app ===
    def save_question(self, q: Dict) -> bool:
        self._call("save_question", q)
        return True

    def get_questions(self, filters: Dict = None) -> List[Dict]:
        return self._call("get_questions", filters or {}) or []

    def save_feedback(self, feedback: Dict) -> bool:
        self._call("save_feedback", feedback)
        return True

    def get_feedback_stats(self, question_id: str) -> Optional[Dict]:
        return self._call("get_feedback_stats", {"question_id": question_id})

    def adjust_difficulty(self, question_id: str, new_difficulty: str, reason: str, adjusted_by: str = "system"):
        self._call("adjust_difficulty", {
            "question_id": question_id,
            "new_difficulty": new_difficulty,
            "reason": reason,
            "adjusted_by": adjusted_by,
        })

    def count_feedback(self) -> int:
        return int(self._call("count_feedback") or 0)

    def count_adjustments(self) -> int:
        return int(self._call("count_adjustments") or 0)

    def reset_database(self):
        self._call("reset_database")

# ===== Local SQLite Fallback Client =====
class LocalDBClient:
    def __init__(self, db_path: str = "ai_assessment_bank.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS questions (
                id TEXT PRIMARY KEY,
                area TEXT NOT NULL,
                difficulty TEXT NOT NULL,
                type TEXT NOT NULL,
                question_text TEXT NOT NULL,
                options TEXT,
                correct_answer INTEGER,
                requirements TEXT,
                evaluation_criteria TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ai_generated BOOLEAN DEFAULT FALSE,
                template_id TEXT,
                metadata TEXT
            )
            '''
        )
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id TEXT NOT NULL,
                user_id TEXT,
                difficulty_rating INTEGER CHECK(difficulty_rating BETWEEN 1 AND 5),
                relevance_rating INTEGER CHECK(relevance_rating BETWEEN 1 AND 5),
                clarity_rating INTEGER CHECK(clarity_rating BETWEEN 1 AND 5),
                comments TEXT,
                actual_difficulty TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            '''
        )
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS difficulty_adjustments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id TEXT NOT NULL,
                original_difficulty TEXT,
                adjusted_difficulty TEXT,
                adjustment_reason TEXT,
                adjusted_by TEXT,
                adjusted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            '''
        )
        conn.commit()
        conn.close()

    def save_question(self, q: Dict) -> bool:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                '''
                INSERT INTO questions (
                    id, area, difficulty, type, question_text,
                    options, correct_answer, requirements,
                    evaluation_criteria, ai_generated, template_id, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    q['id'],
                    q['area'],
                    q['difficulty'],
                    q.get('type', 'general'),
                    q['question'],
                    json.dumps(q.get('options', [])),
                    q.get('correct_answer'),
                    json.dumps(q.get('requirements', [])),
                    json.dumps(q.get('evaluation_criteria', [])),
                    q.get('ai_generated', False),
                    q.get('template_id'),
                    json.dumps(q.get('metadata', {})),
                ),
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            st.error(f"문제 저장 실패: {e}")
            return False

    def get_questions(self, filters: Dict = None) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        query = "SELECT * FROM questions"
        params: List = []
        if filters:
            conds = []
            if 'id' in filters:
                conds.append("id = ?")
                params.append(filters['id'])
            if 'area' in filters:
                conds.append("area = ?")
                params.append(filters['area'])
            if 'difficulty' in filters:
                conds.append("difficulty = ?")
                params.append(filters['difficulty'])
            if 'type' in filters:
                conds.append("type = ?")
                params.append(filters['type'])
            if conds:
                query += " WHERE " + " AND ".join(conds)
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        questions: List[Dict] = []
        for _, row in df.iterrows():
            questions.append(
                {
                    'id': row['id'],
                    'area': row['area'],
                    'difficulty': row['difficulty'],
                    'type': row['type'],
                    'question': row['question_text'],
                    'options': json.loads(row['options']) if row['options'] else None,
                    'correct_answer': row['correct_answer'],
                    'requirements': json.loads(row['requirements']) if row['requirements'] else None,
                    'evaluation_criteria': json.loads(row['evaluation_criteria']) if row['evaluation_criteria'] else None,
                    'ai_generated': row['ai_generated'],
                    'metadata': json.loads(row['metadata']) if row['metadata'] else {},
                }
            )
        return questions

    def save_feedback(self, feedback: Dict) -> bool:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                '''
                INSERT INTO feedback (
                    question_id, user_id, difficulty_rating,
                    relevance_rating, clarity_rating, comments,
                    actual_difficulty
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    feedback['question_id'],
                    feedback.get('user_id', 'anonymous'),
                    feedback['difficulty_rating'],
                    feedback['relevance_rating'],
                    feedback['clarity_rating'],
                    feedback.get('comments', ''),
                    feedback.get('actual_difficulty'),
                ),
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            st.error(f"피드백 저장 실패: {e}")
            return False

    def get_feedback_stats(self, question_id: str) -> Optional[Dict]:
        conn = sqlite3.connect(self.db_path)
        query = (
            'SELECT '
            'AVG(difficulty_rating) as avg_difficulty, '
            'AVG(relevance_rating) as avg_relevance, '
            'AVG(clarity_rating) as avg_clarity, '
            'COUNT(*) as feedback_count, '
            'GROUP_CONCAT(actual_difficulty) as difficulty_votes '
            'FROM feedback WHERE question_id = ?'
        )
        df = pd.read_sql_query(query, conn, params=[question_id])
        conn.close()
        if df.empty or df.iloc[0]['feedback_count'] == 0:
            return None
        votes_raw = df.iloc[0]['difficulty_votes']
        votes: Dict[str, int] = {}
        if votes_raw:
            for v in str(votes_raw).split(','):
                vv = v.strip()
                votes[vv] = votes.get(vv, 0) + 1
        return {
            'avg_difficulty': df.iloc[0]['avg_difficulty'],
            'avg_relevance': df.iloc[0]['avg_relevance'],
            'avg_clarity': df.iloc[0]['avg_clarity'],
            'feedback_count': df.iloc[0]['feedback_count'],
            'difficulty_votes': votes,
        }

    def adjust_difficulty(self, question_id: str, new_difficulty: str, reason: str, adjusted_by: str = 'system'):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT difficulty FROM questions WHERE id = ?", (question_id,))
        row = cursor.fetchone()
        original = row[0] if row else None
        cursor.execute("UPDATE questions SET difficulty = ? WHERE id = ?", (new_difficulty, question_id))
        cursor.execute(
            '''
            INSERT INTO difficulty_adjustments (
                question_id, original_difficulty, adjusted_difficulty,
                adjustment_reason, adjusted_by
            ) VALUES (?, ?, ?, ?, ?)
            ''',
            (question_id, original, new_difficulty, reason, adjusted_by),
        )
        conn.commit()
        conn.close()

    def count_feedback(self) -> int:
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query("SELECT COUNT(*) as cnt FROM feedback", conn)
        conn.close()
        return int(df.iloc[0]['cnt']) if not df.empty else 0

    def count_adjustments(self) -> int:
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query("SELECT COUNT(*) as cnt FROM difficulty_adjustments", conn)
        conn.close()
        return int(df.iloc[0]['cnt']) if not df.empty else 0

    def reset_database(self):
        try:
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
        finally:
            self._init_db()

# ===== AI 문제 생성기 =====
class AIQuestionGenerator:
    def __init__(self, db_client: EdgeDBClient):
        self.db = db_client
        self.assessment_areas = ASSESSMENT_AREAS
        self.difficulty_levels = DIFFICULTY_LEVELS

    def generate_with_ai(self, area: str, difficulty: str, question_type: str, context: str = "") -> Optional[Dict]:
        system_prompt = (
            "당신은 AI 활용능력평가 전문가입니다. 실무에서 AI를 효과적으로 활용하는 능력을 평가하는 문제를 생성해주세요. "
            "문제는 단순히 AI로 해결할 수 있는 것이 아니라, 인간의 판단력과 창의성이 필요한 것이어야 합니다."
        )
        difficulty_guide = {
            "basic": "기본 개념 이해와 단순 도구 사용 능력을 평가. 명확한 정답이 있는 문제.",
            "intermediate": "복합적 문제 해결과 도구 조합 활용 능력을 평가. 여러 접근법이 가능한 문제.",
            "advanced": "전략적 사고와 시스템 설계 능력을 평가. 비즈니스 임팩트를 고려한 종합적 문제.",
        }

        user_prompt = f"""
다음 조건에 맞는 AI 활용능력평가 문제를 생성해주세요:

평가 영역: {self.assessment_areas[area]}
난이도: {self.difficulty_levels[difficulty]} - {difficulty_guide[difficulty]}
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
            resp = client.chat.completions.create(
                model="gpt-5-nano",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            content = resp.choices[0].message.content

            import re
            try:
                m = re.search(r"\{[\s\S]*\}", content)
                qdata = json.loads(m.group() if m else content)
            except Exception:
                qdata = {"question": content, "evaluation_criteria": ["내용의 적절성 (100점)"]}

            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            q = {
                "id": f"Q_AI_{ts}_{random.randint(1000, 9999)}",
                "area": self.assessment_areas[area],
                "difficulty": self.difficulty_levels[difficulty],
                "type": question_type,
                "question": qdata.get("question", content or ""),
                "ai_generated": True,
                "metadata": {
                    "generated_at": ts,
                    "model": "gpt-5-nano",
                    "scenario": qdata.get("scenario", ""),
                    "sample_solution": qdata.get("sample_solution"),
                    "key_points": qdata.get("key_points"),
                },
            }
            if qdata.get("options"):
                q["options"] = qdata.get("options")
                q["correct_answer"] = qdata.get("correct_answer")
            if qdata.get("requirements"):
                q["requirements"] = qdata.get("requirements")
            if qdata.get("evaluation_criteria"):
                q["evaluation_criteria"] = qdata.get("evaluation_criteria")

            st.session_state.last_raw_content = content
            return q
        except Exception as e:
            st.error(f"AI 문제 생성 실패: {e}")
            return None

# ===== HITL =====
class HITLManager:
    def __init__(self, db_client: EdgeDBClient):
        self.db = db_client
        self.difficulty_thresholds = {
            "basic": {"min": 1.0, "max": 2.5},
            "intermediate": {"min": 2.5, "max": 4.0},
            "advanced": {"min": 4.0, "max": 5.0},
        }

    def analyze_difficulty_alignment(self, question_id: str) -> Dict:
        stats = self.db.get_feedback_stats(question_id)
        if not stats or stats.get("feedback_count", 0) < 3:
            return {"status": "insufficient_data", "message": "피드백이 부족합니다 (최소 3개 필요)"}

        questions = self.db.get_questions({"id": question_id})
        if not questions:
            return {"status": "error", "message": "문제를 찾을 수 없습니다"}
        current = questions[0]
        current_difficulty = current["difficulty"]

        avg_difficulty = stats["avg_difficulty"]
        votes = stats.get("difficulty_votes") or {}
        if votes:
            most_voted_difficulty, mv_count = max(votes.items(), key=lambda x: x[1])
            vote_pct = mv_count / max(sum(votes.values()), 1) * 100
        else:
            most_voted_difficulty, vote_pct = current_difficulty, 0

        needs_adjustment = False
        recommended = current_difficulty
        for k, th in self.difficulty_thresholds.items():
            if th["min"] <= avg_difficulty < th["max"]:
                if k != current_difficulty:
                    needs_adjustment = True
                    recommended = k
                break
        if vote_pct > 50 and most_voted_difficulty != current_difficulty:
            needs_adjustment = True
            recommended = most_voted_difficulty

        return {
            "status": "analyzed",
            "current_difficulty": current_difficulty,
            "avg_difficulty_rating": avg_difficulty,
            "recommended_difficulty": recommended,
            "needs_adjustment": needs_adjustment,
            "confidence": vote_pct,
            "feedback_count": stats["feedback_count"],
            "difficulty_votes": votes,
            "stats": stats,
        }

    def auto_adjust_difficulties(self) -> List[Dict]:
        all_q = self.db.get_questions()
        adjustments = []
        for q in all_q:
            a = self.analyze_difficulty_alignment(q["id"])
            if a.get("status") == "analyzed" and a.get("needs_adjustment"):
                reason = (
                    f"자동 조정: 평균 난이도 평가 {a['avg_difficulty_rating']:.1f}, "
                    f"{a['confidence']:.0f}%가 {a['recommended_difficulty']}로 평가"
                )
                self.db.adjust_difficulty(q["id"], a["recommended_difficulty"], reason, "auto_system")
                adjustments.append({
                    "question_id": q["id"],
                    "from": a["current_difficulty"],
                    "to": a["recommended_difficulty"],
                    "reason": reason,
                })
        return adjustments

# ===== Streamlit App =====

def main():
    st.set_page_config(page_title="AI 활용능력평가 문제생성 에이전트 v2.0", page_icon="🤖", layout="wide")

    # 세션 초기화
    if "db" not in st.session_state:
        st.session_state.db = EdgeDBClient()
    if "generator" not in st.session_state:
        st.session_state.generator = AIQuestionGenerator(st.session_state.db)
    if "hitl" not in st.session_state:
        st.session_state.hitl = HITLManager(st.session_state.db)

    st.title("🤖 AI 활용능력평가 문제생성 에이전트 v2.0")
    st.markdown("OpenAI API + Supabase Edge Function 기반")

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📝 문제 생성", "📚 문제 은행", "💬 피드백 & HITL", "📊 분석 대시보드", "⚙️ 설정"])

    # === Tab 1: 문제 생성 ===
    with tab1:
        col1, col2 = st.columns([1, 2])
        with col1:
            st.header("문제 생성 설정")
            generation_method = st.radio("생성 방식", ["AI 자동 생성", "템플릿 기반 생성"], help="AI 자동 생성은 OpenAI API 사용")
            area = st.selectbox("평가 영역", options=list(ASSESSMENT_AREAS.keys()), format_func=lambda k: ASSESSMENT_AREAS[k])
            difficulty = st.selectbox("난이도", options=list(DIFFICULTY_LEVELS.keys()), format_func=lambda k: DIFFICULTY_LEVELS[k])
            question_type = st.selectbox("문제 유형", options=list(QUESTION_TYPES.keys()), format_func=lambda k: QUESTION_TYPES[k])
            context = ""
            if generation_method == "AI 자동 생성":
                context = st.text_area("추가 컨텍스트 (선택)", placeholder="예: 이커머스 마케팅팀, 금융 리스크 관리, 제조업 품질관리 등")

            if st.button("🎯 문제 생성", type="primary", use_container_width=True):
                with st.spinner("생성 중..."):
                    if generation_method == "AI 자동 생성":
                        q = st.session_state.generator.generate_with_ai(area, difficulty, question_type, context)
                    else:
                        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                        q = {
                            "id": f"Q_TPL_{ts}_{random.randint(1000, 9999)}",
                            "area": ASSESSMENT_AREAS[area],
                            "difficulty": DIFFICULTY_LEVELS[difficulty],
                            "type": question_type,
                            "question": f"{area} 영역의 {difficulty} 수준 문제입니다.",
                            "ai_generated": False,
                        }
                    if q:
                        if st.session_state.db.save_question(q):
                            st.success("문제가 성공적으로 저장되었습니다!")
                            st.session_state.last_generated = q
                        else:
                            st.error("문제 저장 실패")

        with col2:
            st.header("생성된 문제 미리보기")
            if "last_generated" in st.session_state:
                q = st.session_state.last_generated
                st.info(f"**문제 ID**: {q['id']}  \n**평가 영역**: {q['area']}  \n**난이도**: {q['difficulty']}  \n**유형**: {q['type']}")
                st.markdown("### 문제")
                st.markdown(q["question"])
                if (q.get("metadata") or {}).get("scenario"):
                    st.markdown("### 상황 설명")
                    st.markdown(q["metadata"]["scenario"])
                if q.get("options"):
                    st.markdown("### 선택지")
                    for i, opt in enumerate(q["options"], 1):
                        st.markdown(f"{i}. {opt}")
                    if q.get("correct_answer"):
                        with st.expander("정답 확인"):
                            st.success(f"정답: {q['correct_answer']}번")
                if q.get("requirements"):
                    st.markdown("### 요구사항")
                    for r in q["requirements"]:
                        st.markdown(f"- {r}")
                if q.get("evaluation_criteria"):
                    st.markdown("### 평가 기준")
                    for c in q["evaluation_criteria"]:
                        st.markdown(f"- {c}")
                if q.get("ai_generated"):
                    with st.expander("AI 생성 정보"):
                        meta = q.get("metadata", {})
                        if meta.get("sample_solution"):
                            st.markdown("**모범 답안/해결 방향**")
                            st.markdown(meta["sample_solution"])
                        if meta.get("key_points"):
                            st.markdown("**핵심 평가 포인트**")
                            for p in meta["key_points"]:
                                st.markdown(f"- {p}")
                        if st.session_state.get("last_raw_content"):
                            with st.expander("원문 모델 응답 (디버깅)"):
                                st.code(st.session_state.last_raw_content)

    # === Tab 2: 문제 은행 ===
    with tab2:
        st.header("📚 문제 은행")
        fc1, fc2, fc3, fc4 = st.columns(4)
        with fc1:
            filter_area = st.selectbox("평가 영역 필터", options=["전체"] + list(ASSESSMENT_AREAS.keys()), format_func=lambda v: "전체" if v == "전체" else ASSESSMENT_AREAS[v])
        with fc2:
            filter_difficulty = st.selectbox("난이도 필터", options=["전체"] + list(DIFFICULTY_LEVELS.keys()), format_func=lambda v: "전체" if v == "전체" else DIFFICULTY_LEVELS[v])
        with fc3:
            filter_type = st.selectbox("문제 유형 필터", options=["전체"] + list(QUESTION_TYPES.keys()), format_func=lambda v: "전체" if v == "전체" else QUESTION_TYPES[v])
        with fc4:
            if st.button("🔍 검색", use_container_width=True):
                filters = {}
                if filter_area != "전체":
                    filters["area"] = ASSESSMENT_AREAS[filter_area]
                if filter_difficulty != "전체":
                    filters["difficulty"] = DIFFICULTY_LEVELS[filter_difficulty]
                if filter_type != "전체":
                    filters["type"] = filter_type
                st.session_state.filtered_questions = st.session_state.db.get_questions(filters)

        if "filtered_questions" in st.session_state:
            st.markdown(f"### 검색 결과: {len(st.session_state.filtered_questions)}개")
            for idx, q in enumerate(st.session_state.filtered_questions):
                with st.expander(f"{idx+1}. [{q['difficulty']}] {q['area']} - {q['id'][:15]}..."):
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        st.markdown(f"**문제**: {q['question'][:200]}...")
                        stats = st.session_state.db.get_feedback_stats(q["id"])
                        if stats:
                            st.markdown(
                                f"""
📊 **피드백 통계** (응답 수: {stats['feedback_count']})
- 난이도: {stats['avg_difficulty']:.1f}/5.0
- 관련성: {stats['avg_relevance']:.1f}/5.0
- 명확성: {stats['avg_clarity']:.1f}/5.0
"""
                            )
                    with c2:
                        if st.button("📋 상세보기", key=f"view_{q['id']}"):
                            st.session_state.selected_question = q
                        if st.button("💬 피드백", key=f"feedback_{q['id']}"):
                            st.session_state.feedback_question = q

    # === Tab 3: 피드백 & HITL ===
    with tab3:
        st.header("💬 피드백 & Human-in-the-Loop")
        c1, c2 = st.columns([1, 1])
        with c1:
            st.subheader("피드백 입력")
            if st.session_state.get("feedback_question"):
                q = st.session_state.feedback_question
                st.info(f"문제 ID: {q['id']}")
                st.markdown(f"**문제**: {q['question'][:200]}...")
                d = st.slider("난이도 평가", 1, 5, 3)
                r = st.slider("관련성 평가", 1, 5, 3)
                c = st.slider("명확성 평가", 1, 5, 3)
                actual = st.radio("실제 체감 난이도", options=list(DIFFICULTY_LEVELS.values()))
                comments = st.text_area("추가 의견 (선택)")
                if st.button("피드백 제출", type="primary"):
                    fb = {
                        "question_id": q["id"],
                        "difficulty_rating": d,
                        "relevance_rating": r,
                        "clarity_rating": c,
                        "actual_difficulty": actual,
                        "comments": comments,
                    }
                    if st.session_state.db.save_feedback(fb):
                        st.success("피드백이 저장되었습니다!")
                        a = st.session_state.hitl.analyze_difficulty_alignment(q["id"])
                        if a.get("needs_adjustment"):
                            st.warning(f"난이도 조정 필요: {a['current_difficulty']} → {a['recommended_difficulty']}")
            else:
                st.info("문제 은행에서 피드백을 남길 문제를 선택해주세요.")

        with c2:
            st.subheader("난이도 자동 조정")
            if st.button("🔄 전체 문제 난이도 분석 실행"):
                with st.spinner("분석 중..."):
                    adjs = st.session_state.hitl.auto_adjust_difficulties()
                    if adjs:
                        st.success(f"{len(adjs)}개 문제의 난이도가 조정되었습니다.")
                        for a in adjs:
                            st.write(f"- {a['question_id']}: {a['from']} → {a['to']}")
                    else:
                        st.info("난이도 조정이 필요한 문제가 없습니다.")

            st.markdown("### 수동 난이도 조정")
            all_q = st.session_state.db.get_questions()
            qids = [q["id"] for q in all_q]
            sel = st.selectbox("문제 선택", qids)
            if sel:
                a = st.session_state.hitl.analyze_difficulty_alignment(sel)
                if a.get("status") == "analyzed":
                    st.info(f"현재 난이도: {a['current_difficulty']}")
                    st.info(f"권장 난이도: {a['recommended_difficulty']}")
                    new_d = st.selectbox("새 난이도", options=list(DIFFICULTY_LEVELS.values()))
                    reason = st.text_input("조정 사유")
                    if st.button("난이도 조정 실행"):
                        st.session_state.db.adjust_difficulty(sel, new_d, reason, "manual_admin")
                        st.success("난이도가 조정되었습니다!")

    # === Tab 4: 분석 대시보드 ===
    with tab4:
        st.header("📊 분석 대시보드")
        all_q = st.session_state.db.get_questions()
        if all_q:
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("전체 문제 수", len(all_q))
            with c2:
                ai_cnt = sum(1 for q in all_q if q.get("ai_generated", False))
                st.metric("AI 생성 문제", ai_cnt)
            with c3:
                st.metric("총 피드백 수", st.session_state.db.count_feedback())
            with c4:
                st.metric("난이도 조정 횟수", st.session_state.db.count_adjustments())

            st.markdown("### 문제 분포")
            area_dist = pd.DataFrame(all_q)["area"].value_counts()
            st.plotly_chart(px.pie(values=area_dist.values, names=area_dist.index, title="평가 영역별 분포"), use_container_width=True)
            diff_dist = pd.DataFrame(all_q)["difficulty"].value_counts()
            st.plotly_chart(px.bar(x=diff_dist.index, y=diff_dist.values, title="난이도별 분포"), use_container_width=True)

            st.markdown("### 피드백 분석")
            feedback_rows = []
            for q in all_q[:20]:
                s = st.session_state.db.get_feedback_stats(q["id"])
                if s:
                    feedback_rows.append({
                        "question_id": q["id"][:10] + "...",
                        "difficulty": s["avg_difficulty"],
                        "relevance": s["avg_relevance"],
                        "clarity": s["avg_clarity"],
                    })
            if feedback_rows:
                df = pd.DataFrame(feedback_rows)
                fig = go.Figure()
                fig.add_trace(go.Bar(name="난이도", x=df["question_id"], y=df["difficulty"]))
                fig.add_trace(go.Bar(name="관련성", x=df["question_id"], y=df["relevance"]))
                fig.add_trace(go.Bar(name="명확성", x=df["question_id"], y=df["clarity"]))
                fig.update_layout(title="문제별 평가 점수", barmode="group", yaxis_title="평균 점수", xaxis_title="문제 ID")
                st.plotly_chart(fig, use_container_width=True)

    # === Tab 5: 설정 ===
    with tab5:
        st.header("⚙️ 설정")
        st.subheader("API 설정")
        if os.getenv("OPENAI_API_KEY"):
            st.success("✅ OpenAI API 키가 설정되어 있습니다.")
        else:
            st.warning("⚠️ OpenAI API 키가 설정되지 않았습니다. .env 파일을 확인하세요.")

        st.subheader("데이터베이스 관리")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("📥 데이터 내보내기"):
                all_q = st.session_state.db.get_questions()
                df = pd.DataFrame(all_q)
                csv = df.to_csv(index=False, encoding="utf-8-sig")
                st.download_button(
                    label="CSV 다운로드",
                    data=csv,
                    file_name=f"ai_assessment_questions_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                )
        with c2:
            if st.button("🗑️ 데이터베이스 초기화", type="secondary"):
                if st.checkbox("정말로 모든 데이터를 삭제하시겠습니까?"):
                    st.session_state.db.reset_database()
                    st.success("데이터베이스가 초기화되었습니다.")
                    st.rerun()

if __name__ == "__main__":
    main()

