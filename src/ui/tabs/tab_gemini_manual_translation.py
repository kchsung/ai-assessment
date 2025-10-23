"""
제미나이 수동 번역 탭
"""
from src.services.translation_service import TranslationService
from src.services.gemini_client import GeminiClient

def render(st):
    """제미나이 수동 번역 탭 렌더링"""
    st.header("🌐 제미나이 수동 번역")
    st.markdown("### 하나의 문제를 선택하여 영어로 번역합니다")
    
    # 세션 상태 초기화
    if "manual_translation_problems" not in st.session_state:
        st.session_state.manual_translation_problems = []
    if "manual_translation_result" not in st.session_state:
        st.session_state.manual_translation_result = None
    
    # 세션 상태에서 DB 클라이언트 가져오기
    db = st.session_state.get("db")
    
    if not db:
        st.error("❌ 데이터베이스 연결이 필요합니다")
        return
    
    # 제미나이 API 사용 가능 여부 확인
    try:
        gemini_client = GeminiClient()
        if not gemini_client.is_available():
            st.error("❌ 제미나이 API 키가 설정되지 않았습니다")
            return
    except Exception as e:
        st.error(f"❌ 제미나이 클라이언트 초기화 실패: {str(e)}")
        return
    
    # 번역 서비스 초기화
    try:
        translation_service = TranslationService()
        if not translation_service.is_available():
            st.error("❌ 번역 서비스가 사용할 수 없습니다")
            return
    except Exception as e:
        st.error(f"❌ 번역 서비스 초기화 실패: {str(e)}")
        return
    
    # 문제 검색 섹션
    st.markdown("---")
    st.subheader("📋 문제 검색")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # 평가 영역 필터
        domains = ["전체", "life", "news", "interview", "learning_concept", "pharma_distribution", "job_practice"]
        selected_domain = st.selectbox(
            "평가 영역",
            domains,
            key="manual_translation_domain"
        )
    
    with col2:
        # 난이도 필터
        difficulties = ["전체", "very easy", "easy", "normal", "hard", "very hard"]
        selected_difficulty = st.selectbox(
            "난이도",
            difficulties,
            key="manual_translation_difficulty"
        )
    
    with col3:
        # 영문 번역 필터 (is_en 필드 제거로 인해 기능 비활성화)
        st.selectbox(
            "영문 번역 (기능 비활성화)",
            ["전체"],
            key="manual_translation_is_en",
            disabled=True
        )
    
    # 검색 버튼
    if st.button("🔍 문제 검색", key="search_problems_for_translation"):
        filters = {}
        
        if selected_domain != "전체":
            filters["domain"] = selected_domain
        
        if selected_difficulty != "전체":
            filters["difficulty"] = selected_difficulty
        
        # is_en 필터 제거됨 (필드 삭제로 인해)
        
        try:
            # translation_done = False인 문제들만 조회
            problems = db.get_problems_for_translation(filters)
            st.session_state.manual_translation_problems = problems
            st.success(f"✅ {len(problems)}개의 번역이 필요한 문제를 찾았습니다")
        except Exception as e:
            st.error(f"❌ 문제 검색 실패: {str(e)}")
    
    # 문제 목록 표시
    if "manual_translation_problems" in st.session_state and st.session_state.manual_translation_problems:
        st.markdown("---")
        st.subheader("📚 문제 목록")
        
        problems = st.session_state.manual_translation_problems
        
        # 문제 선택
        problem_options = [
            f"{i+1}. [{p.get('domain', 'N/A')}] {p.get('title', 'No Title')[:50]}..."
            for i, p in enumerate(problems)
        ]
        
        selected_problem_index = st.selectbox(
            "번역할 문제 선택",
            range(len(problem_options)),
            format_func=lambda i: problem_options[i],
            key="selected_manual_translation_problem_index"
        )
        
        if selected_problem_index is not None:
            selected_problem = problems[selected_problem_index]
            
            # 문제 상세 정보 표시
            st.markdown("---")
            st.subheader("📝 선택된 문제")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("평가 영역", selected_problem.get("domain", "N/A"))
            
            with col2:
                st.metric("난이도", selected_problem.get("difficulty", "N/A"))
            
            with col3:
                st.metric("시간 제한", selected_problem.get("time_limit", "N/A"))
            
            with col4:
                st.metric("영문 번역 상태", "확인 불가")
            
            # 원본 문제 내용 표시
            with st.expander("🔍 원본 문제 내용 보기", expanded=True):
                st.markdown("**제목:**")
                st.write(selected_problem.get("title", ""))
                
                st.markdown("**시나리오:**")
                st.write(selected_problem.get("scenario", ""))
                
                st.markdown("**목표:**")
                goals = selected_problem.get("goal", [])
                if isinstance(goals, list):
                    for i, goal in enumerate(goals, 1):
                        st.write(f"{i}. {goal}")
                else:
                    st.write(goals)
                
                st.markdown("**요구사항:**")
                requirements = selected_problem.get("requirements", [])
                if isinstance(requirements, list):
                    for i, req in enumerate(requirements, 1):
                        st.write(f"{i}. {req}")
                else:
                    st.write(requirements)
            
            # 번역 버튼
            st.markdown("---")
            
            # is_en 필드가 제거되어 번역 상태 확인 불가
            
            if st.button("🌐 번역 시작", key="start_manual_translation", type="primary"):
                with st.spinner("번역 중... 잠시만 기다려주세요 ⏳"):
                    try:
                        # 문제 번역 및 저장 (i18n 테이블에 저장하고 상태 업데이트)
                        translated_problem = translation_service.translate_and_save_problem(selected_problem)
                        
                        if translated_problem and isinstance(translated_problem, dict):
                            # 세션 상태에 번역 결과 저장
                            st.session_state.manual_translation_result = translated_problem
                            st.success("✅ 번역이 완료되었습니다!")
                        else:
                            st.error("❌ 번역 결과가 유효하지 않습니다.")
                            # 실패 시 결과 초기화
                            if "manual_translation_result" in st.session_state:
                                del st.session_state.manual_translation_result
                        
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ 번역 실패: {str(e)}")
                        # 실패 시 결과 초기화
                        if "manual_translation_result" in st.session_state:
                            del st.session_state.manual_translation_result
            
            # 번역 결과 표시
            if "manual_translation_result" in st.session_state and st.session_state.manual_translation_result:
                st.markdown("---")
                st.subheader("✨ 번역 결과")
                
                translated = st.session_state.manual_translation_result
                
                if translated is None:
                    st.error("❌ 번역 결과가 없습니다.")
                else:
                    with st.expander("🔍 번역된 문제 내용 보기", expanded=True):
                        st.markdown("**Title:**")
                        st.write(translated.get("title", ""))
                        
                        st.markdown("**Scenario:**")
                        st.write(translated.get("scenario", ""))
                        
                        st.markdown("**Time Limit:**")
                        st.write(translated.get("time_limit", ""))
                        
                        st.markdown("**Goals:**")
                        goals = translated.get("goal", [])
                        if isinstance(goals, list):
                            for i, goal in enumerate(goals, 1):
                                st.write(f"{i}. {goal}")
                        else:
                            st.write(goals)
                        
                        st.markdown("**Requirements:**")
                        requirements = translated.get("requirements", [])
                        if isinstance(requirements, list):
                            for i, req in enumerate(requirements, 1):
                                st.write(f"{i}. {req}")
                        else:
                            st.write(requirements)
                
                # 초기화 버튼
                if st.button("🔄 새로운 문제 번역하기", key="reset_manual_translation"):
                    if "manual_translation_result" in st.session_state:
                        del st.session_state.manual_translation_result
                    st.rerun()
    
    else:
        st.info("💡 문제를 검색하여 번역할 문제를 선택해주세요")

