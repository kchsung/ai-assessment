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
    if "manual_translation_processing" not in st.session_state:
        st.session_state.manual_translation_processing = False
    
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
        gemini_client = GeminiClient()
        translation_service = TranslationService(gemini_client, st.session_state.db)
    except Exception as e:
        st.error(f"❌ 번역 서비스 초기화 실패: {str(e)}")
        return
    
    # 문제 검색 섹션
    st.markdown("---")
    st.subheader("📋 문제 검색 (Subjective 타입만)")
    st.info("💡 현재는 주관식 문제(Subjective)만 번역 가능합니다. 객관식 문제 번역은 추후 지원 예정입니다.")
    
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
            f"{i+1}. [{p.get('category', p.get('domain', 'N/A'))}] {p.get('title', 'No Title')[:50]}..."
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
                # category 필드 사용 (domain이 아닌)
                category = selected_problem.get("category", selected_problem.get("domain", "N/A"))
                st.metric("평가 영역", category)
            
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
            
            # 번역 처리 중이 아닐 때만 버튼 활성화
            if not st.session_state.manual_translation_processing:
                if st.button("🌐 번역 시작", key="start_manual_translation", type="primary"):
                    st.session_state.manual_translation_processing = True
                    st.rerun()
            else:
                # 번역 처리 중일 때는 스피너 표시
                with st.spinner("번역 중... 잠시만 기다려주세요 ⏳"):
                    try:
                        # 진행 상태 표시
                        st.info("🔄 번역을 시작합니다...")
                        
                        # 디버깅 정보 표시 영역
                        debug_container = st.container()
                        with debug_container:
                            st.subheader("🔍 번역 진행 상황")
                            debug_placeholder = st.empty()
                            
                            # 초기 디버깅 정보 표시
                            debug_placeholder.info("🔄 번역 프로세스를 시작합니다...")
                        
                        # 디버깅 콜백 함수 정의
                        def debug_callback(debug_info):
                            with debug_placeholder.container():
                                st.write("**진행 단계:**")
                                for step in debug_info["steps"]:
                                    st.write(f"• {step}")
                                
                                if debug_info["errors"]:
                                    st.write("**오류:**")
                                    for error in debug_info["errors"]:
                                        st.error(f"• {error}")
                        
                        # 문제 번역 및 저장 (i18n 테이블에 저장하고 상태 업데이트)
                        translated_problem = translation_service.translate_and_save_problem(selected_problem, debug_callback)
                        
                        if translated_problem and isinstance(translated_problem, dict):
                            # 세션 상태에 번역 결과 저장
                            st.session_state.manual_translation_result = translated_problem
                            st.success("✅ 번역이 완료되었습니다!")
                            
                            # 번역 결과 요약 표시
                            with st.expander("📋 번역 결과 요약", expanded=True):
                                st.write(f"**원본 제목**: {selected_problem.get('title', 'N/A')}")
                                st.write(f"**번역된 제목**: {translated_problem.get('title', 'N/A')}")
                                st.write(f"**카테고리**: {translated_problem.get('category', 'N/A')}")
                                st.write(f"**난이도**: {translated_problem.get('difficulty', 'N/A')}")
                                st.write(f"**저장된 ID**: {translated_problem.get('source_problem_id', 'N/A')}")
                            
                            # 성공 시에만 처리 상태 초기화 및 화면 갱신
                            st.session_state.manual_translation_processing = False
                            st.rerun()
                        else:
                            st.error("❌ 번역 결과가 유효하지 않습니다.")
                            # 실패 시 결과 초기화
                            if "manual_translation_result" in st.session_state:
                                del st.session_state.manual_translation_result
                            
                            # 실패 시에도 처리 상태 초기화 (화면 갱신하지 않음)
                            st.session_state.manual_translation_processing = False
                                
                    except Exception as e:
                        error_msg = str(e)
                        st.error(f"❌ 번역 중 오류가 발생했습니다: {error_msg}")
                        
                        # 에러 메시지를 복사할 수 있도록 코드 블록으로 표시
                        with st.expander("🔍 에러 상세 정보 (복사 가능)", expanded=True):
                            st.code(error_msg, language="text")
                            
                            # 에러 메시지 복사 버튼
                            if st.button("📋 에러 메시지 복사", key="copy_error_msg"):
                                st.write("에러 메시지를 위의 코드 블록에서 복사하세요")
                        
                        st.error("💡 가능한 해결 방법:")
                        st.write("1. 네트워크 연결을 확인해주세요")
                        st.write("2. 제미나이 API 키가 올바른지 확인해주세요")
                        st.write("3. Edge Function이 정상적으로 배포되었는지 확인해주세요")
                        st.write("4. 잠시 후 다시 시도해주세요")
                        
                        # 실패 시 결과 초기화
                        if "manual_translation_result" in st.session_state:
                            del st.session_state.manual_translation_result
                        
                        # 번역 완료 후 처리 상태 초기화
                        st.session_state.manual_translation_processing = False
                        # 에러 발생 시 화면 갱신하지 않음 (에러 메시지 유지)
                        
                        
                        # 번역 실패 후 처리 상태 초기화
                        st.session_state.manual_translation_processing = False
                        st.rerun()
            
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
                    if "manual_translation_processing" in st.session_state:
                        st.session_state.manual_translation_processing = False
                    st.rerun()
    
    else:
        st.info("💡 문제를 검색하여 번역할 문제를 선택해주세요")

