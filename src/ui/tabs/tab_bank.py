import streamlit as st
from src.constants import ASSESSMENT_AREAS, ASSESSMENT_AREAS_DISPLAY, DIFFICULTY_LEVELS, QUESTION_TYPES

def render(st):
    
    # 검색 필터
    c1, c2, c3, c4, c5 = st.columns([1, 1, 1, 2, 1])
    with c1:
        f_area = st.selectbox("평가 영역", ["전체"] + list(ASSESSMENT_AREAS_DISPLAY.keys()), 
                             format_func=lambda v: "전체" if v=="전체" else ASSESSMENT_AREAS_DISPLAY[v])
    with c2:
        f_diff = st.selectbox("난이도", ["전체"] + list(DIFFICULTY_LEVELS.keys()), 
                             format_func=lambda v: "전체" if v=="전체" else DIFFICULTY_LEVELS[v])
    with c3:
        f_type = st.selectbox("유형", ["전체"] + list(QUESTION_TYPES.keys()), 
                             format_func=lambda v: "전체" if v=="전체" else QUESTION_TYPES[v])
    with c4:
        search_text = st.text_input("검색어", placeholder="문제 내용으로 검색...", key="question_search_input")
    with c5:
        st.markdown("<br>", unsafe_allow_html=True)  # 공간 추가
        if st.button("🔍 검색", use_container_width=True):
            filters = {}
            if f_area != "전체": 
                filters["area"] = ASSESSMENT_AREAS[f_area]
            if f_diff != "전체": 
                filters["difficulty"] = DIFFICULTY_LEVELS[f_diff]
            if f_type != "전체": 
                filters["type"] = f_type
            
            # 데이터베이스에서 필터링된 결과 가져오기
            questions = st.session_state.db.get_questions(filters)
            
            # 검색어가 있으면 클라이언트 측에서 추가 필터링
            if search_text.strip():
                search_term = search_text.strip().lower()
                questions = [
                    q for q in questions 
                    if search_term in (q.get("question") or q.get("question_text", "")).lower()
                ]
            
            st.session_state.filtered_questions = questions
            st.session_state.current_filters = filters
            st.session_state.current_page = 1  # 검색 시 첫 페이지로 리셋
            st.session_state.selected_question_id = None  # 검색 시 선택 초기화
            st.rerun()
    
    # 초기 로드 시 전체 문제 표시
    if not st.session_state.get("filtered_questions"):
        st.session_state.filtered_questions = st.session_state.db.get_questions({})

    # 좌우 분할 레이아웃
    col_left, col_right = st.columns([1, 2])
    
    # 좌측: 검색 결과 카드뷰
    with col_left:
        st.markdown("### 📋 검색 결과")
        qs = st.session_state.get("filtered_questions", [])
        
        if qs:
            st.markdown(f"**총 {len(qs)}개 문제**")
            
            # 문제 선택을 위한 selectbox 사용 (페이지 새로고침 없음)
            question_options = {}
            for q in qs:
                question_text = q.get("question") or q.get("question_text","(없음)")
                display_text = f"[{q['difficulty']}] {q['area']} - {question_text[:100]}{'...' if len(question_text) > 100 else ''}"
                question_options[display_text] = q
            
            # 현재 선택된 문제 찾기
            current_selection = None
            if st.session_state.get("selected_question_id"):
                for display_text, q in question_options.items():
                    if q["id"] == st.session_state.selected_question_id:
                        current_selection = display_text
                        break
            
            # 문제 선택 드롭다운
            selected_display = st.selectbox(
                "문제를 선택하세요:",
                options=list(question_options.keys()),
                index=list(question_options.keys()).index(current_selection) if current_selection else 0,
                key="question_selector"
            )
            
            # 선택된 문제를 세션 상태에 저장
            if selected_display and selected_display in question_options:
                selected_q = question_options[selected_display]
                st.session_state.selected_question_id = selected_q["id"]
                st.session_state.selected_question = selected_q
        else:
            st.info("검색 결과가 없습니다.")
    
    # 우측: 선택된 문제 상세보기
    with col_right:
        st.markdown("### 📖 문제 상세보기")
        
        selected_q = st.session_state.get("selected_question")
        if selected_q:
            # 문제 기본 정보
            st.info(f"**문제 ID**: {selected_q['id']}  \n**평가 영역**: {selected_q['area']}  \n**난이도**: {selected_q['difficulty']}  \n**유형**: {selected_q['type']}")
            
            meta = selected_q.get("metadata", {})
            
            # 객관식 문제 상세 표시
            if selected_q.get("type") == "multiple_choice" and meta.get("steps"):
                st.markdown("### 📋 객관식 문제")
                
                # 시나리오를 마크다운으로 표시
                if meta.get("scenario"):
                    st.markdown("**📖 문제 상황**")
                    st.markdown(meta["scenario"])
                
                steps = meta["steps"]
                
                # 스텝별 탭으로 표시
                if len(steps) > 1:
                    step_tabs = st.tabs([f"Step {step['step']}" for step in steps])
                    for i, step in enumerate(steps):
                        with step_tabs[i]:
                            st.markdown(f"**{step.get('title', '문제')}**")
                            st.markdown(step.get('question', ''))
                            
                            # 선택지 표시
                            if step.get('options'):
                                st.markdown("**선택지:**")
                                for opt in step['options']:
                                    st.markdown(f"• {opt['text']}")
                                    if opt.get('feedback'):
                                        st.caption(f"💡 {opt['feedback']}")
                            
                            # 정답 표시
                            if step.get('answer'):
                                st.markdown(f"**정답: {step['answer']}**")
                else:
                    # 단일 스텝인 경우
                    step = steps[0]
                    st.markdown(f"**{step.get('title', '문제')}**")
                    st.markdown(step.get('question', ''))
                    
                    # 선택지 표시
                    if step.get('options'):
                        st.markdown("**선택지:**")
                        for opt in step['options']:
                            st.markdown(f"• {opt['text']}")
                            if opt.get('feedback'):
                                st.caption(f"💡 {opt['feedback']}")
                    
                    # 정답 표시
                    if step.get('answer'):
                        st.markdown(f"**정답: {step['answer']}**")
            
            # 주관식 문제 상세 표시
            elif selected_q.get("type") == "subjective":
                st.markdown("### 📝 주관식 문제")
                
                # 시나리오를 마크다운으로 표시
                if meta.get("scenario"):
                    st.markdown("**📖 문제 상황**")
                    st.markdown(meta["scenario"])
                
                # 목표 표시
                if meta.get("goal"):
                    st.markdown("**🎯 목표**")
                    for goal in meta["goal"]:
                        st.markdown(f"- {goal}")
            
            # 기존 방식으로 fallback
            else:
                st.markdown("### 문제")
                st.markdown(selected_q.get("question","(없음)"))
                if meta.get("scenario"):
                    st.markdown("**📖 문제 상황**")
                    st.markdown(meta["scenario"])
                if meta.get("goal"):
                    st.markdown("**🎯 목표**")
                    for goal in meta["goal"]:
                        st.markdown(f"- {goal}")
            
            
            # 피드백 통계 표시
            stats = st.session_state.db.get_feedback_stats(selected_q["id"])
            if stats:
                st.markdown("### 📊 피드백 통계")
                col_stat1, col_stat2, col_stat3 = st.columns(3)
                with col_stat1:
                    st.metric("피드백 수", stats['feedback_count'])
                with col_stat2:
                    st.metric("평균 난이도", f"{stats['avg_difficulty']:.1f}")
                with col_stat3:
                    st.metric("평균 관련성", f"{stats['avg_relevance']:.1f}")
        else:
            st.info("좌측에서 문제를 선택하면 상세 내용이 여기에 표시됩니다.")