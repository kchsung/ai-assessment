import streamlit as st
from src.constants import ASSESSMENT_AREAS, ASSESSMENT_AREAS_DISPLAY, DIFFICULTY_LEVELS, QUESTION_TYPES

def render(st):
    
    # 검색 필터
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        f_area = st.selectbox("평가 영역", ["전체"] + list(ASSESSMENT_AREAS_DISPLAY.keys()), format_func=lambda v: "전체" if v=="전체" else ASSESSMENT_AREAS_DISPLAY[v])
    with c2:
        f_diff = st.selectbox("난이도", ["전체"] + list(DIFFICULTY_LEVELS.keys()), format_func=lambda v: "전체" if v=="전체" else DIFFICULTY_LEVELS[v])
    with c3:
        f_type = st.selectbox("유형", ["전체"] + list(QUESTION_TYPES.keys()), format_func=lambda v: "전체" if v=="전체" else QUESTION_TYPES[v])
    with c4:
        # 검색 버튼을 아래쪽 정렬로 맞춤
        st.markdown("<br>", unsafe_allow_html=True)  # 공간 추가
        if st.button("🔍 검색", use_container_width=True):
            filters={}
            if f_area!="전체": filters["area"]=ASSESSMENT_AREAS[f_area]
            if f_diff!="전체": filters["difficulty"]=DIFFICULTY_LEVELS[f_diff]
            if f_type!="전체": filters["type"]=f_type
            st.session_state.filtered_questions = st.session_state.db.get_questions(filters)
            st.session_state.current_page = 1  # 검색 시 첫 페이지로 리셋

    # 좌우 분할 레이아웃
    col_left, col_right = st.columns([1, 2])
    
    # 좌측: 검색 결과 카드뷰
    with col_left:
        st.markdown("### 📋 검색 결과")
        qs = st.session_state.get("filtered_questions", [])
        
        if qs:
            st.markdown(f"**총 {len(qs)}개 문제**")
            
            # 페이징 설정
            items_per_page = 10
            total_pages = (len(qs) + items_per_page - 1) // items_per_page
            current_page = st.session_state.get("current_page", 1)
            
            # 페이지네이션 컨트롤
            if total_pages > 1:
                col_prev, col_info, col_next = st.columns([1, 2, 1])
                with col_prev:
                    if st.button("◀️ 이전", disabled=(current_page <= 1)):
                        st.session_state.current_page = current_page - 1
                        st.rerun()
                with col_info:
                    st.markdown(f"**{current_page} / {total_pages} 페이지**")
                with col_next:
                    if st.button("다음 ▶️", disabled=(current_page >= total_pages)):
                        st.session_state.current_page = current_page + 1
                        st.rerun()
            
            # 현재 페이지의 문제들 표시
            start_idx = (current_page - 1) * items_per_page
            end_idx = min(start_idx + items_per_page, len(qs))
            current_questions = qs[start_idx:end_idx]
            
            # 카드뷰로 문제 표시
            for idx, q in enumerate(current_questions):
                question_text = q.get("question") or q.get("question_text","(없음)")
                is_selected = st.session_state.get("selected_question_id") == q["id"]
                meta = q.get("metadata", {})
                
                # 난이도별 색상 설정
                difficulty_colors = {
                    "아주 쉬움": "#4CAF50",  # 초록
                    "쉬움": "#8BC34A",       # 연한 초록
                    "보통": "#FF9800",       # 주황
                    "어려움": "#F44336",     # 빨강
                    "아주 어려움": "#9C27B0" # 보라
                }
                
                difficulty_color = difficulty_colors.get(q['difficulty'], "#757575")
                
                # 카드 컨테이너
                with st.container():
                    # 상단 태그 영역 (한 줄 형태)
                    col_tag1, col_tag2, col_time, col_feedback = st.columns([1, 1, 1, 1])
                    
                    with col_tag1:
                        st.markdown(f"""
                        <span style="
                            background-color: {difficulty_color};
                            color: white;
                            padding: 4px 8px;
                            border-radius: 6px;
                            font-size: 12px;
                            font-weight: bold;
                        ">{q['difficulty']}</span>
                        """, unsafe_allow_html=True)
                    
                    with col_tag2:
                        st.markdown(f"""
                        <span style="
                            background-color: {difficulty_color};
                            color: white;
                            padding: 4px 8px;
                            border-radius: 6px;
                            font-size: 12px;
                            font-weight: bold;
                        ">{q['area']}</span>
                        """, unsafe_allow_html=True)
                    
                    with col_time:
                        estimated_time = meta.get('estimatedTime', '3분 이내')
                        st.markdown(f"""
                        <div style="color: #666; font-size: 12px;">
                            ⏱️ {estimated_time}
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col_feedback:
                        stats = st.session_state.db.get_feedback_stats(q['id'])
                        feedback_count = stats['feedback_count'] if stats else 0
                        st.markdown(f"""
                        <div style="color: #666; font-size: 12px;">
                            💬 {feedback_count}
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # 카드 클릭 버튼 (question_text 포함, 높이 증가)
                    display_text = question_text[:200] + ('...' if len(question_text) > 200 else '')
                    
                    # 버튼 높이를 3줄 고정 크기로 설정
                    st.markdown(f"""
                    <style>
                    div[data-testid="column"] button[kind="secondary"][data-testid="baseButton-secondary"]:has-text("{display_text[:50]}") {{
                        height: 90px !important;
                        min-height: 90px !important;
                        max-height: 90px !important;
                        line-height: 1.3 !important;
                        white-space: normal !important;
                        text-align: left !important;
                        padding: 12px !important;
                        overflow: hidden !important;
                        display: -webkit-box !important;
                        -webkit-line-clamp: 3 !important;
                        -webkit-box-orient: vertical !important;
                    }}
                    </style>
                    """, unsafe_allow_html=True)
                    
                    if st.button(
                        f"📋 {display_text}",
                        key=f"card_{q['id']}",
                        use_container_width=True,
                        help=f"클릭하여 상세보기"
                    ):
                        st.session_state.selected_question_id = q["id"]
                        st.session_state.selected_question = q
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
                                show_answer = st.toggle("정답 보기", key=f"bank_answer_toggle_{step.get('step', 1)}")
                                if show_answer:
                                    st.success(f"정답: {step['answer']}")
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
                        show_answer = st.toggle("정답 보기", key="bank_answer_toggle_single")
                        if show_answer:
                            st.success(f"정답: {step['answer']}")
            
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
            
            # 피드백 버튼 (우측에 배치)
            st.markdown("---")
            if st.button("💬 피드백 작성", key=f"feedback_{selected_q['id']}", use_container_width=True):
                st.session_state.feedback_question = selected_q
            
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