import streamlit as st
from src.constants import ASSESSMENT_AREAS, DIFFICULTY_LEVELS, QUESTION_TYPES

def render(st):
    st.header("📚 문제 은행")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        f_area = st.selectbox("평가 영역", ["전체"] + list(ASSESSMENT_AREAS.keys()), format_func=lambda v: "전체" if v=="전체" else ASSESSMENT_AREAS[v])
    with c2:
        f_diff = st.selectbox("난이도", ["전체"] + list(DIFFICULTY_LEVELS.keys()), format_func=lambda v: "전체" if v=="전체" else DIFFICULTY_LEVELS[v])
    with c3:
        f_type = st.selectbox("유형", ["전체"] + list(QUESTION_TYPES.keys()), format_func=lambda v: "전체" if v=="전체" else QUESTION_TYPES[v])
    with c4:
        if st.button("🔍 검색", use_container_width=True):
            filters={}
            if f_area!="전체": filters["area"]=ASSESSMENT_AREAS[f_area]
            if f_diff!="전체": filters["difficulty"]=DIFFICULTY_LEVELS[f_diff]
            if f_type!="전체": filters["type"]=f_type
            st.session_state.filtered_questions = st.session_state.db.get_questions(filters)

    qs = st.session_state.get("filtered_questions", [])
    if qs:
        st.markdown(f"### 검색 결과: {len(qs)}개")
        for idx, q in enumerate(qs):
            with st.expander(f"{idx+1}. [{q['difficulty']}] {q['area']} - {q['id'][:15]}..."):
                question_text = q.get("question") or q.get("question_text","(없음)")
                st.markdown(f"**문제**: {question_text[:200]}...")
                stats = st.session_state.db.get_feedback_stats(q["id"])
                if stats:
                    st.markdown(
                        f"📊 **피드백**: n={stats['feedback_count']} / "
                        f"난이도 {stats['avg_difficulty']:.1f}, 관련성 {stats['avg_relevance']:.1f}, 명확성 {stats['avg_clarity']:.1f}"
                    )
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("📋 상세보기", key=f"view_{q['id']}"):
                        st.session_state.selected_question = q
                with c2:
                    if st.button("💬 피드백", key=f"fb_{q['id']}"):
                        st.session_state.feedback_question = q
