import random
from datetime import datetime
import streamlit as st
from src.constants import ASSESSMENT_AREAS, DIFFICULTY_LEVELS, QUESTION_TYPES


def render(st):
    # 좌우 컬럼으로 나누기
    col1, col2 = st.columns([1, 2])
    
    # 좌측: 문제 생성 설정
    with col1:
        st.header("문제 생성 설정")
        method = st.radio("생성 방식", ["AI 자동 생성", "템플릿 기반 생성"], help="AI 자동 생성은 OpenAI API 사용")
        area = st.selectbox("평가 영역", options=list(ASSESSMENT_AREAS.keys()), format_func=lambda k: ASSESSMENT_AREAS[k])
        difficulty = st.selectbox("난이도", options=list(DIFFICULTY_LEVELS.keys()), format_func=lambda k: DIFFICULTY_LEVELS[k])
        qtype = st.selectbox("문제 유형", options=list(QUESTION_TYPES.keys()), format_func=lambda k: QUESTION_TYPES[k])

        context = ""
        if method == "AI 자동 생성":
            context = st.text_area("추가 컨텍스트 (선택)", placeholder="예: 이커머스 마케팅팀, 금융 리스크 관리...")

        if st.button("🎯 문제 생성", type="primary", use_container_width=True):
            with st.spinner("생성 중..."):
                if method == "AI 자동 생성":
                    if st.session_state.generator is None:
                        st.error("AI 생성기가 초기화되지 않았습니다. API 키를 확인하세요.")
                        return
                    q = st.session_state.generator.generate_with_ai(area, difficulty, qtype, context)
                else:
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    q = {
                        "id": f"Q_TPL_{ts}_{random.randint(1000, 9999)}",
                        "area": ASSESSMENT_AREAS[area],
                        "difficulty": DIFFICULTY_LEVELS[difficulty],
                        "type": QUESTION_TYPES[qtype],
                        "question": f"{ASSESSMENT_AREAS[area]} 영역 / {DIFFICULTY_LEVELS[difficulty]} / {QUESTION_TYPES[qtype]} 문제",
                        "ai_generated": False,
                        "metadata": {"generated_at": ts, "template_based": True}
                    }
                if q and st.session_state.db.save_question(q):
                    st.success("문제가 저장되었습니다!")
                    st.session_state.last_generated = q
                elif q:
                    st.error("문제 저장 실패")

    # 우측: 생성된 문제 미리보기
    with col2:
        st.header("생성된 문제 미리보기")
        q = st.session_state.get("last_generated")
        if q:
            st.info(f"**문제 ID**: {q['id']}  \n**평가 영역**: {q['area']}  \n**난이도**: {q['difficulty']}  \n**유형**: {q['type']}")
            st.markdown("### 문제")
            st.markdown(q.get("question","(없음)"))
            meta = q.get("metadata", {})
            if meta.get("scenario"):
                st.markdown("### 상황 설명"); st.markdown(meta["scenario"])
            if q.get("options"):
                st.markdown("### 선택지")
                for i, opt in enumerate(q["options"], 1):
                    st.markdown(f"{i}. {opt}")
                if q.get("correct_answer"):
                    with st.expander("정답 확인"):
                        st.success(f"정답: {q['correct_answer']}번")
            if q.get("requirements"):
                st.markdown("### 요구사항"); [st.markdown(f"- {r}") for r in q["requirements"]]
            if q.get("evaluation_criteria"):
                st.markdown("### 평가 기준"); [st.markdown(f"- {c}") for c in q["evaluation_criteria"]]
            if q.get("ai_generated") and st.session_state.get("last_raw_content"):
                with st.expander("원문 모델 응답 (디버깅)"):
                    st.code(st.session_state.last_raw_content)
        else:
            st.info("문제를 생성하면 여기에 미리보기가 표시됩니다.")
