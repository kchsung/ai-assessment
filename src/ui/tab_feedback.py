import streamlit as st
from src.constants import DIFFICULTY_LEVELS

def render(st):
    st.header("💬 피드백 & Human-in-the-Loop")

    # 문제 선택 (통합된 인터페이스)
    all_q = st.session_state.db.get_questions()
    if not all_q:
        st.info("문제가 없습니다. 먼저 문제를 생성해주세요.")
        return
    
    # 문제 선택 옵션을 question_text로 표시
    question_options = {}
    for question in all_q:
        qt = question.get("question") or question.get("question_text","(없음)")
        display_text = f"{qt[:60]}{'...' if len(qt) > 60 else ''} [{question['id'][:8]}...]"
        question_options[display_text] = question
    
    selected_display = st.selectbox(
        "📋 피드백할 문제 선택", 
        options=list(question_options.keys()),
        help="문제를 선택하면 피드백을 입력하고 기존 피드백을 조회할 수 있습니다."
    )
    
    if selected_display:
        selected_question = question_options[selected_display]
        selected_id = selected_question["id"]
        
        # 선택된 문제 정보 표시
        qt = selected_question.get("question") or selected_question.get("question_text","(없음)")
        st.markdown(f"**선택된 문제**: {qt}")
        st.caption(f"문제 ID: {selected_id} | 영역: {selected_question.get('area', 'N/A')} | 난이도: {selected_question.get('difficulty', 'N/A')}")
        
        # 좌우 분할: 피드백 입력 vs 기존 피드백 조회
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("📝 새 피드백 입력")
            
            # 피드백 입력 폼
            with st.form("feedback_form"):
                st.markdown("**평가 항목**")
                col1_1, col1_2, col1_3 = st.columns(3)
                with col1_1:
                    d = st.slider("난이도 평가", 1, 5, 3, help="1: 매우 쉬움, 5: 매우 어려움")
                with col1_2:
                    r = st.slider("관련성 평가", 1, 5, 3, help="1: 관련성 낮음, 5: 관련성 높음")
                with col1_3:
                    c = st.slider("명확성 평가", 1, 5, 3, help="1: 불명확, 5: 매우 명확")
                
                actual = st.radio("실제 체감 난이도", options=list(DIFFICULTY_LEVELS.values()))
                
                # 텍스트 입력창
                comments = st.text_area(
                    "💬 피드백 내용", 
                    placeholder="문제에 대한 의견, 개선사항, 오류 발견 등을 자유롭게 작성해주세요...",
                    height=100
                )
                
                submitted = st.form_submit_button("💾 피드백 저장", type="primary")
                
                if submitted:
                    if comments.strip():  # 텍스트 입력이 있는 경우에만 저장
                        ok = st.session_state.db.save_feedback({
                            "question_id": selected_id, 
                            "difficulty_rating": d,
                            "relevance_rating": r, 
                            "clarity_rating": c,
                            "actual_difficulty": actual, 
                            "comments": comments
                        })
                        if ok:
                            st.success("✅ 피드백이 성공적으로 저장되었습니다!")
                            st.rerun()  # 페이지 새로고침하여 새 피드백 표시
                        else:
                            st.error("❌ 피드백 저장에 실패했습니다.")
                    else:
                        st.warning("⚠️ 피드백 내용을 입력해주세요.")

        with col2:
            st.subheader("📊 기존 피드백 조회")
            
            # 선택된 문제의 피드백 조회
            feedbacks = st.session_state.db.get_feedback(selected_id)
            
            if feedbacks:
                st.markdown(f"**📋 총 {len(feedbacks)}개의 피드백**")
                
                for idx, feedback in enumerate(feedbacks, 1):
                    with st.expander(f"피드백 #{idx} - {feedback.get('created_at', '날짜 미상')}"):
                        col_f1, col_f2, col_f3 = st.columns(3)
                        with col_f1:
                            st.metric("난이도", f"{feedback.get('difficulty_rating', 0)}/5")
                        with col_f2:
                            st.metric("관련성", f"{feedback.get('relevance_rating', 0)}/5")
                        with col_f3:
                            st.metric("명확성", f"{feedback.get('clarity_rating', 0)}/5")
                        
                        st.markdown(f"**실제 체감 난이도**: {feedback.get('actual_difficulty', '미설정')}")
                        
                        if feedback.get('comments'):
                            st.markdown("**💬 피드백 내용**:")
                            st.markdown(feedback['comments'])
                        else:
                            st.markdown("*피드백 내용 없음*")
            else:
                st.info("이 문제에 대한 피드백이 아직 없습니다. 왼쪽에서 첫 번째 피드백을 작성해보세요!")
        
        # 난이도 조정 섹션 (하단에 배치)
        st.markdown("---")
        st.subheader("🔧 난이도 자동/수동 조정")
        
        col_adj1, col_adj2 = st.columns(2)
        
        with col_adj1:
            if st.button("🔄 전체 자동 분석"):
                with st.spinner("분석 중..."):
                    adjs = st.session_state.hitl.auto_adjust_difficulties()
                    if adjs:
                        st.success(f"{len(adjs)}건 조정")
                        for a in adjs:
                            st.write(f"- {a['question_id']}: {a['from']} → {a['to']} ({a['reason']})")
                    else:
                        st.info("조정 필요 없음")

        with col_adj2:
            a = st.session_state.hitl.analyze_difficulty_alignment(selected_id)
            if a.get("status")=="analyzed":
                st.info(f"현재: {a['current_difficulty']} / 권장: {a['recommended_difficulty']}")
                new_d = st.selectbox("새 난이도", options=list(DIFFICULTY_LEVELS.values()))
                reason = st.text_input("조정 사유")
                if st.button("난이도 조정"):
                    st.session_state.db.adjust_difficulty(selected_id, new_d, reason, "manual_admin")
                    st.success("조정 완료")
                    st.rerun()
