import random
from datetime import datetime
import streamlit as st
from src.constants import ASSESSMENT_AREAS, ASSESSMENT_AREAS_DISPLAY, DIFFICULTY_LEVELS, QUESTION_TYPES


def render(st):
    # 좌우 컬럼으로 나누기
    col1, col2 = st.columns([1, 2])
    
    # 좌측: 문제 생성 설정
    with col1:
        area = st.selectbox("평가 영역", options=list(ASSESSMENT_AREAS_DISPLAY.keys()), format_func=lambda k: ASSESSMENT_AREAS_DISPLAY[k])
        difficulty = st.selectbox("난이도", options=list(DIFFICULTY_LEVELS.keys()), format_func=lambda k: DIFFICULTY_LEVELS[k])
        qtype = st.selectbox("문제 유형", options=list(QUESTION_TYPES.keys()), format_func=lambda k: QUESTION_TYPES[k])
        
        # 사용자 추가 요구사항 (항상 표시)
        context = st.text_area("사용자 추가 요구사항", placeholder="예: 이커머스 마케팅팀, 금융 리스크 관리, 특정 도구 사용 등...", help="문제 생성 시 반영할 추가적인 요구사항이나 맥락을 입력하세요")

        if st.button("🎯 문제 생성", type="primary", use_container_width=True):
            with st.spinner("생성 중..."):
                if st.session_state.generator is None:
                    st.error("AI 생성기가 초기화되지 않았습니다. API 키를 확인하세요.")
                    return
                q = st.session_state.generator.generate_with_ai(area, difficulty, qtype, context)
                if q and st.session_state.db.save_question(q):
                    st.success("문제가 저장되었습니다!")
                    st.session_state.last_generated = q
                elif q:
                    st.error("문제 저장 실패")

    # 우측: 생성된 문제 미리보기
    with col2:
        st.markdown("#### 생성된 문제 보기")
        q = st.session_state.get("last_generated")
        if q:
            st.info(f"**문제 ID**: {q['id']}  \n**평가 영역**: {q['area']}  \n**난이도**: {q['difficulty']}  \n**유형**: {q['type']}")
            
            meta = q.get("metadata", {})
            
            # 객관식 문제 표시
            if q.get("type") == "multiple_choice" and meta.get("steps"):
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
            
            # 주관식 문제 표시
            elif q.get("type") == "subjective":
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
            
            # 기존 방식으로 fallback (새로운 구조가 아닌 경우)
            else:
                st.markdown("### 문제")
                st.markdown(q.get("question","(없음)"))
                if meta.get("scenario"):
                    st.markdown("### 상황 설명")
                    st.markdown(meta["scenario"])
            
            # 디버깅용 원문 표시
            if q.get("ai_generated") and st.session_state.get("last_raw_content"):
                st.markdown("### 🔍 원문 모델 응답 (디버깅)")
                st.code(st.session_state.last_raw_content)
        else:
            st.info("문제를 생성하면 여기에 미리보기가 표시됩니다.")
