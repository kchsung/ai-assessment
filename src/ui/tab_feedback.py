import streamlit as st
from src.constants import DIFFICULTY_LEVELS

def render(st):
    st.header("💬 피드백 & Human-in-the-Loop")

    c1, c2 = st.columns(2)

    with c1:
        st.subheader("피드백 입력")
        q = st.session_state.get("feedback_question")
        if not q:
            st.info("문제 은행에서 피드백할 문제를 선택하세요.")
        else:
            st.info(f"문제 ID: {q['id']}")
            qt = q.get("question") or q.get("question_text","(없음)")
            st.markdown(f"**문제**: {qt[:200]}...")
            d = st.slider("난이도 평가", 1, 5, 3)
            r = st.slider("관련성 평가", 1, 5, 3)
            c = st.slider("명확성 평가", 1, 5, 3)
            actual = st.radio("실제 체감 난이도", options=list(DIFFICULTY_LEVELS.values()))
            comments = st.text_area("추가 의견")
            if st.button("피드백 제출", type="primary"):
                ok = st.session_state.db.save_feedback({
                    "question_id": q["id"], "difficulty_rating": d,
                    "relevance_rating": r, "clarity_rating": c,
                    "actual_difficulty": actual, "comments": comments
                })
                if ok:
                    st.success("저장 완료")
                a = st.session_state.hitl.analyze_difficulty_alignment(q["id"])
                if a.get("needs_adjustment"):
                    st.warning(f"난이도 조정 권고: {a['current_difficulty']} → {a['recommended_difficulty']}")

    with c2:
        st.subheader("난이도 자동/수동 조정")
        if st.button("🔄 전체 자동 분석"):
            with st.spinner("분석 중..."):
                adjs = st.session_state.hitl.auto_adjust_difficulties()
                if adjs:
                    st.success(f"{len(adjs)}건 조정")
                    for a in adjs:
                        st.write(f"- {a['question_id']}: {a['from']} → {a['to']} ({a['reason']})")
                else:
                    st.info("조정 필요 없음")

        all_q = st.session_state.db.get_questions()
        if all_q:
            sel = st.selectbox("문제 선택", [q["id"] for q in all_q])
            a = st.session_state.hitl.analyze_difficulty_alignment(sel)
            if a.get("status")=="analyzed":
                st.info(f"현재: {a['current_difficulty']} / 권장: {a['recommended_difficulty']}")
                new_d = st.selectbox("새 난이도", options=list(DIFFICULTY_LEVELS.values()))
                reason = st.text_input("조정 사유")
                if st.button("난이도 조정"):
                    st.session_state.db.adjust_difficulty(sel, new_d, reason, "manual_admin")
                    st.success("조정 완료")
