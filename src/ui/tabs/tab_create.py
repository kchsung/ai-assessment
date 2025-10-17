import random
from datetime import datetime
import streamlit as st
from src.constants import ASSESSMENT_AREAS, DIFFICULTY_LEVELS, QUESTION_TYPES
# 탭 상태 관리 코드 제거


def render(st):
    # 좌우 컬럼으로 나누기
    col1, col2 = st.columns([1, 2])
    
    # 좌측: 문제 생성 설정
    with col1:
        def format_create_area(k):
            return k
        
        area = st.selectbox("평가 영역", options=list(ASSESSMENT_AREAS.keys()), format_func=format_create_area, key="create_area", index=0)
        difficulty = st.selectbox("난이도", options=list(DIFFICULTY_LEVELS.keys()), format_func=lambda k: DIFFICULTY_LEVELS[k], key="create_difficulty", index=0)
        qtype = st.selectbox("문제 유형", options=list(QUESTION_TYPES.keys()), format_func=lambda k: k, key="create_type", index=0)
        
        # System 프롬프트 입력
        system_prompt = st.text_area("System 프롬프트", placeholder="시스템 프롬프트에 추가할 내용을 입력하세요...", help="AI에게 역할이나 행동 방식을 지시하는 시스템 프롬프트를 입력하세요")
        
        # User 프롬프트 입력
        user_prompt = st.text_area("User 프롬프트", placeholder="사용자 프롬프트에 추가할 내용을 입력하세요...", help="문제 생성 요청에 추가할 구체적인 요구사항이나 맥락을 입력하세요")

        if st.button("🎯 문제 생성", type="primary", use_container_width=True, key="create_generate"):
            with st.spinner("생성 중..."):
                if st.session_state.generator is None:
                    st.error("AI 생성기가 초기화되지 않았습니다. API 키를 확인하세요.")
                    return
                if st.session_state.db is None:
                    st.error("데이터베이스 연결이 초기화되지 않았습니다. Edge Function 설정을 확인하세요.")
                    return
                q = st.session_state.generator.generate_with_ai(area, difficulty, qtype, user_prompt, system_prompt)
                if q:
                    # 문제 타입에 따라 적절한 테이블에 저장
                    question_type = q.get("type", "subjective")
                    try:
                        if question_type == "multiple_choice":
                            if st.session_state.db.save_multiple_choice_question(q):
                                st.success("✅ 객관식 문제가 questions_multiple_choice 테이블에 저장되었습니다!")
                            else:
                                st.error("❌ 객관식 문제 저장 실패")
                        else:
                            if st.session_state.db.save_subjective_question(q):
                                st.success("✅ 주관식 문제가 questions_subjective 테이블에 저장되었습니다!")
                            else:
                                st.error("❌ 주관식 문제 저장 실패")
                        st.session_state.last_generated = q
                    except Exception as e:
                        st.error(f"❌ 문제 저장 실패: {str(e)}")
                else:
                    st.error("❌ 문제 생성 실패")
        
        # 프롬프트 보기 버튼
        if st.button("📋 프롬프트 보기", use_container_width=True):
            # 프롬프트를 세션 상태에 저장
            st.session_state.show_prompts = True
            st.session_state.current_system_prompt = system_prompt
            st.session_state.current_user_prompt = user_prompt
            st.session_state.current_area = area
            st.session_state.current_difficulty = difficulty
            st.session_state.current_qtype = qtype

    # 우측: 생성된 문제 미리보기 또는 프롬프트 보기
    with col2:
        # 프롬프트 보기 모드
        if st.session_state.get("show_prompts", False):
            st.markdown("#### 📋 프롬프트 미리보기")
            
            # 닫기 버튼
            if st.button("❌ 닫기", key="close_prompts"):
                st.session_state.show_prompts = False
                st.rerun()
            
            # 현재 설정 정보
            area_display = st.session_state.current_area
            difficulty_display = DIFFICULTY_LEVELS.get(st.session_state.current_difficulty, st.session_state.current_difficulty)
            qtype_display = st.session_state.current_qtype
            
            st.info(f"**평가 영역**: {area_display} | **난이도**: {difficulty_display} | **유형**: {qtype_display}")
            
            # System 프롬프트 표시
            st.markdown("### 🤖 System 프롬프트")
            # 기존 시스템 프롬프트 가져오기
            from src.services.ai_generator import AIQuestionGenerator
            generator = AIQuestionGenerator()
            db_system_prompt, db_user_prompt = generator._get_prompts_from_db(
                st.session_state.current_area, 
                st.session_state.current_difficulty, 
                st.session_state.current_qtype
            )
            
            if db_system_prompt:
                # 데이터베이스 시스템 프롬프트에 난이도 기준 추가
                base_system_prompt = db_system_prompt + "\n\n" + generator._build_system_prompt().split("난이도별 평가 기준:")[1]
                st.caption("📋 데이터베이스 프롬프트 사용")
            else:
                base_system_prompt = generator._build_system_prompt()
                st.caption("📝 기본 프롬프트 사용")
            
            # 시스템 프롬프트 구성: 기본 프롬프트 + 사용자 프롬프트 (사용자 프롬프트가 있으면)
            if st.session_state.current_system_prompt:
                full_system_prompt = base_system_prompt + "\n\n[사용자 추가 시스템 요구사항]\n" + st.session_state.current_system_prompt
                st.caption("🎯 기본 프롬프트 + 사용자 시스템 프롬프트 적용")
            else:
                full_system_prompt = base_system_prompt
            
            # 프롬프트 표시용 CSS 추가
            st.markdown("""
            <style>
            .prompt-code {
                white-space: pre-wrap !important;
                word-wrap: break-word !important;
                overflow-x: hidden !important;
                max-width: 100% !important;
            }
            .prompt-code pre {
                white-space: pre-wrap !important;
                word-wrap: break-word !important;
                overflow-x: hidden !important;
                max-width: 100% !important;
            }
            </style>
            """, unsafe_allow_html=True)
            
            st.code(full_system_prompt, language="text")
            
            # User 프롬프트 표시
            st.markdown("### 👤 User 프롬프트")
            if db_user_prompt:
                # 데이터베이스 user 프롬프트에 사용자 시스템 프롬프트를 context로 추가
                if st.session_state.current_system_prompt:
                    base_user_prompt = db_user_prompt + f"\n\n사용자 추가 요구사항: {st.session_state.current_system_prompt}"
                else:
                    base_user_prompt = db_user_prompt
            else:
                base_user_prompt = generator._build_user_prompt(
                    st.session_state.current_area, 
                    st.session_state.current_difficulty, 
                    st.session_state.current_qtype, 
                    st.session_state.current_system_prompt
                )
            
            # 사용자 추가 입력이 있으면 붙여서 표시
            if st.session_state.current_user_prompt:
                full_user_prompt = base_user_prompt + "\n\n[사용자 추가 요구사항]\n" + st.session_state.current_user_prompt
            else:
                full_user_prompt = base_user_prompt
            
            st.code(full_user_prompt, language="text")
        
        # 일반 문제 미리보기 모드
        else:
            st.markdown("#### 생성된 문제 보기")
            q = st.session_state.get("last_generated")
            
            if q:
                st.info(f"**문제 ID**: {q.get('id', 'N/A')}  \n**평가 영역**: {q.get('category', 'N/A')}  \n**난이도**: {q['difficulty']}  \n**유형**: {q['type']}")
                
                meta = q.get("metadata", {})
                
                # 객관식 문제 표시
                if q.get("type") == "multiple_choice" and meta.get("steps"):
                    st.markdown("### 📋 Multiple Choice Problem")
                    
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
                    st.markdown("### 📝 Subjective Problem")
                    
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