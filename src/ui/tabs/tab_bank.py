import streamlit as st
from src.constants import ASSESSMENT_AREAS, ASSESSMENT_AREAS_DISPLAY, DIFFICULTY_LEVELS, QUESTION_TYPES

def render(st):
    st.header("📚 문제 은행")
    
    # 검색 필터
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        f_area = st.selectbox("평가 영역", ["전체"] + list(ASSESSMENT_AREAS_DISPLAY.keys()), format_func=lambda v: "전체" if v=="전체" else ASSESSMENT_AREAS_DISPLAY[v])
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

    # 좌우 분할 레이아웃
    col_left, col_right = st.columns([1, 2])
    
    # 좌측: 검색 결과 리스트
    with col_left:
        st.markdown("### 📋 검색 결과")
        qs = st.session_state.get("filtered_questions", [])
        
        if qs:
            st.markdown(f"**총 {len(qs)}개 문제**")
            
            # 문제 리스트 (간단한 형태)
            for idx, q in enumerate(qs):
                question_text = q.get("question") or q.get("question_text","(없음)")
                is_selected = st.session_state.get("selected_question_id") == q["id"]
                
                # 선택된 문제는 다른 스타일로 표시
                if is_selected:
                    st.markdown(f"**▶️ {idx+1}. [{q['difficulty']}] {q['area']}**")
                    st.caption(f"{question_text[:50]}...")
                else:
                    if st.button(f"{idx+1}. [{q['difficulty']}] {q['area']}", key=f"select_{q['id']}", use_container_width=True):
                        st.session_state.selected_question_id = q["id"]
                        st.session_state.selected_question = q
                        st.rerun()
                    st.caption(f"{question_text[:50]}...")
                
                # 피드백 통계
                stats = st.session_state.db.get_feedback_stats(q["id"])
                if stats:
                    st.caption(f"📊 n={stats['feedback_count']} | 난이도 {stats['avg_difficulty']:.1f}")
                
                st.markdown("---")
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
                                    col_a, col_b = st.columns([1, 4])
                                    with col_a:
                                        st.markdown(f"**{opt['id']}**")
                                    with col_b:
                                        st.markdown(opt['text'])
                                        if opt.get('feedback'):
                                            st.caption(f"💡 {opt['feedback']}")
                            
                            # 정답 표시
                            if step.get('answer'):
                                with st.expander("정답 확인"):
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
                            col_a, col_b = st.columns([1, 4])
                            with col_a:
                                st.markdown(f"**{opt['id']}**")
                            with col_b:
                                st.markdown(opt['text'])
                                if opt.get('feedback'):
                                    st.caption(f"💡 {opt['feedback']}")
                    
                    # 정답 표시
                    if step.get('answer'):
                        with st.expander("정답 확인"):
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
                
                # 과제 표시
                if meta.get("task"):
                    st.markdown("**📋 과제**")
                    st.markdown(meta["task"])
                
                # 첫 번째 질문들
                if meta.get("first_question"):
                    st.markdown("**❓ 질문**")
                    for question in meta["first_question"]:
                        st.markdown(f"- {question}")
                
                # 요구사항
                if meta.get("requirements"):
                    st.markdown("**📌 요구사항**")
                    for req in meta["requirements"]:
                        st.markdown(f"- {req}")
                
                # 제약사항
                if meta.get("constraints"):
                    st.markdown("**⚠️ 제약사항**")
                    for constraint in meta["constraints"]:
                        st.markdown(f"- {constraint}")
                
                # 평가 기준
                if meta.get("evaluation"):
                    st.markdown("**📊 평가 기준**")
                    for eval_criteria in meta["evaluation"]:
                        st.markdown(f"- {eval_criteria}")
            
            # 기존 방식으로 fallback
            else:
                st.markdown("### 문제")
                st.markdown(selected_q.get("question","(없음)"))
                if meta.get("scenario"):
                    st.markdown("### 상황 설명")
                    st.markdown(meta["scenario"])
            
            # 피드백 버튼 (우측에 배치)
            st.markdown("---")
            col_fb1, col_fb2 = st.columns(2)
            with col_fb1:
                if st.button("💬 피드백 작성", key=f"feedback_{selected_q['id']}", use_container_width=True):
                    st.session_state.feedback_question = selected_q
            with col_fb2:
                if st.button("🔄 다른 문제 선택", key=f"clear_{selected_q['id']}", use_container_width=True):
                    st.session_state.selected_question_id = None
                    st.session_state.selected_question = None
                    st.rerun()
            
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