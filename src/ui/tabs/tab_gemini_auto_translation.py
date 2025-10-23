"""
제미나이 자동 번역 탭
"""
from src.services.translation_service import TranslationService
from src.services.gemini_client import GeminiClient
import time

def render(st):
    """제미나이 자동 번역 탭 렌더링"""
    st.header("🤖 제미나이 자동 번역")
    st.markdown("### 여러 문제를 선택하여 일괄 번역합니다")
    
    # 세션 상태 초기화
    if "auto_translation_running" not in st.session_state:
        st.session_state.auto_translation_running = False
    if "auto_translation_selected" not in st.session_state:
        st.session_state.auto_translation_selected = []
    if "auto_translation_results" not in st.session_state:
        st.session_state.auto_translation_results = []
    if "auto_translation_errors" not in st.session_state:
        st.session_state.auto_translation_errors = []
    if "auto_translation_current" not in st.session_state:
        st.session_state.auto_translation_current = 0
    
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
    
    # 필터 섹션
    st.markdown("---")
    st.subheader("🔍 문제 필터링")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # 평가 영역 필터
        domains = ["전체", "life", "news", "interview", "learning_concept", "pharma_distribution", "job_practice"]
        selected_domain = st.selectbox(
            "평가 영역",
            domains,
            key="auto_translation_domain"
        )
    
    with col2:
        # 난이도 필터
        difficulties = ["전체", "very easy", "easy", "normal", "hard", "very hard"]
        selected_difficulty = st.selectbox(
            "난이도",
            difficulties,
            key="auto_translation_difficulty"
        )
    
    with col3:
        # 영문 번역 필터 (is_en 필드 제거로 인해 기능 비활성화)
        st.selectbox(
            "영문 번역 (기능 비활성화)",
            ["전체"],
            key="auto_translation_is_en",
            disabled=True
        )
    
    # 검색 버튼 (Subjective 타입만)
    st.info("💡 현재는 주관식 문제(Subjective)만 번역 가능합니다. 객관식 문제 번역은 추후 지원 예정입니다.")
    if st.button("🔍 문제 검색 (Subjective만)", key="search_problems_for_auto_translation"):
        filters = {}
        
        if selected_domain != "전체":
            filters["domain"] = selected_domain
        
        if selected_difficulty != "전체":
            filters["difficulty"] = selected_difficulty
        
        # is_en 필터 제거됨 (필드 삭제로 인해)
        
        try:
            # translation_done = False인 문제들만 조회
            problems = db.get_problems_for_translation(filters)
            st.session_state.auto_translation_problems = problems
            st.session_state.auto_translation_selected = []
            st.success(f"✅ {len(problems)}개의 번역이 필요한 문제를 찾았습니다")
        except Exception as e:
            st.error(f"❌ 문제 검색 실패: {str(e)}")
    
    # 문제 목록 표시 및 선택
    if "auto_translation_problems" in st.session_state and st.session_state.auto_translation_problems:
        st.markdown("---")
        st.subheader("📚 문제 목록")
        
        problems = st.session_state.auto_translation_problems
        
        # 전체 선택/해제 버튼
        col1, col2, col3 = st.columns([1, 1, 4])
        
        with col1:
            if st.button("✅ 전체 선택", key="select_all_problems"):
                st.session_state.auto_translation_selected = list(range(len(problems)))
                st.rerun()
        
        with col2:
            if st.button("❌ 전체 해제", key="deselect_all_problems"):
                st.session_state.auto_translation_selected = []
                st.rerun()
        
        # 선택된 문제 수 표시
        selected_count = len(st.session_state.get('auto_translation_selected', []))
        st.markdown(f"**선택된 문제: {selected_count}개**")
        
        # 번역 시작 버튼 (상단으로 이동)
        if selected_count > 0:
            st.info(f"📌 {selected_count}개의 문제가 선택되었습니다")
            
            if not st.session_state.auto_translation_running:
                if st.button(
                    f"🚀 선택한 {selected_count}개 문제 번역 시작",
                    key="start_auto_translation",
                    type="primary"
                ):
                    st.session_state.auto_translation_running = True
                    st.session_state.auto_translation_results = []
                    st.session_state.auto_translation_errors = []
                    st.session_state.auto_translation_current = 0
                    st.rerun()
        
        st.markdown("---")
        
        # 문제 목록 표시 (체크박스)
        
        for i, problem in enumerate(problems):
            col1, col2 = st.columns([0.5, 9.5])
            
            with col1:
                is_selected = i in st.session_state.auto_translation_selected
                checkbox_key = f"problem_select_{i}"
                
                # 체크박스 상태 변경 감지
                new_selected_state = st.checkbox("", value=is_selected, key=checkbox_key)
                
                # 상태가 변경된 경우에만 업데이트
                if new_selected_state != is_selected:
                    if new_selected_state:
                        if i not in st.session_state.auto_translation_selected:
                            st.session_state.auto_translation_selected.append(i)
                    else:
                        if i in st.session_state.auto_translation_selected:
                            st.session_state.auto_translation_selected.remove(i)
                    # 상태 변경 시 즉시 리렌더링
                    st.rerun()
            
            with col2:
                st.markdown(
                    f"**{i+1}. [{problem.get('category', problem.get('domain', 'N/A'))}] {problem.get('title', 'No Title')[:70]}...** "
                    f"({problem.get('difficulty', 'N/A')})"
                )
        
        # 번역 진행 중
        if st.session_state.auto_translation_running:
            st.markdown("---")
            st.subheader("⚙️ 번역 진행 중...")
            
            # 진행 상태 표시
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # 선택된 문제들 필터링 (유효한 인덱스만)
            valid_indices = [i for i in st.session_state.auto_translation_selected if i < len(problems)]
            selected_problems = [problems[i] for i in valid_indices]
            total_count = len(selected_problems)
            current_index = st.session_state.get("auto_translation_current", 0)
            
            # 진행 상태 정보 표시
            st.info(f"📊 총 {total_count}개 문제 중 {current_index + 1}번째 번역 중...")
            
            # 번역 진행
            if current_index < total_count:
                problem = selected_problems[current_index]
                
                try:
                    # 진행 상태 업데이트
                    progress = (current_index) / total_count
                    progress_bar.progress(progress)
                    status_text.markdown(
                        f"**번역 중: {current_index + 1}/{total_count}** - "
                        f"{problem.get('title', 'Unknown')[:50]}..."
                    )
                    
                    # 문제 번역 및 저장 (i18n 테이블에 저장하고 상태 업데이트)
                    try:
                        # 디버깅 콜백 함수 정의
                        def debug_callback(debug_info):
                            # 현재 문제의 디버깅 정보를 상태에 저장
                            if "auto_translation_debug" not in st.session_state:
                                st.session_state.auto_translation_debug = {}
                            st.session_state.auto_translation_debug[problem.get("id")] = debug_info
                        
                        translated_problem = translation_service.translate_and_save_problem(problem, debug_callback)
                        
                        if translated_problem:
                            # 성공 결과 저장
                            st.session_state.auto_translation_results.append({
                                "problem_id": problem.get("id"),
                                "title": problem.get("title"),
                                "translated_title": translated_problem.get("title", ""),
                                "status": "success"
                            })
                        else:
                            # 번역 실패
                            st.session_state.auto_translation_errors.append({
                                "problem_id": problem.get("id"),
                                "title": problem.get("title"),
                                "error": "번역 결과가 유효하지 않음"
                            })
                    except Exception as e:
                        # 번역 중 예외 발생
                        st.session_state.auto_translation_errors.append({
                            "problem_id": problem.get("id"),
                            "title": problem.get("title"),
                            "error": f"번역 중 오류: {str(e)}"
                        })
                    
                    # API 호출 제한을 위한 대기
                    # time.sleep(1) 제거 - 성능 개선
                    
                except Exception as e:
                    # 실패 결과 저장
                    st.session_state.auto_translation_errors.append({
                        "problem_id": problem.get("id"),
                        "title": problem.get("title"),
                        "error": str(e)
                    })
                
                # 다음 문제로 진행
                st.session_state.auto_translation_current = current_index + 1
                st.rerun()
            
            else:
                # 번역 완료
                progress_bar.progress(1.0)
                status_text.markdown("**✅ 번역 완료!**")
                
                st.session_state.auto_translation_running = False
                
                st.success(
                    f"✅ 번역이 완료되었습니다! "
                    f"(성공: {len(st.session_state.auto_translation_results)}개, "
                    f"실패: {len(st.session_state.auto_translation_errors)}개)"
                )
                
                # 결과 표시
                if st.session_state.auto_translation_results:
                    with st.expander("✅ 성공한 번역", expanded=True):
                        for result in st.session_state.auto_translation_results:
                            st.markdown(f"- {result['title'][:70]}...")
                
                if st.session_state.auto_translation_errors:
                    with st.expander("❌ 실패한 번역", expanded=True):
                        for error in st.session_state.auto_translation_errors:
                            st.markdown(f"- {error['title'][:70]}...")
                            st.caption(f"  오류: {error['error']}")
                            
                            # 디버깅 정보 표시
                            if "auto_translation_debug" in st.session_state and error['problem_id'] in st.session_state.auto_translation_debug:
                                debug_info = st.session_state.auto_translation_debug[error['problem_id']]
                                with st.expander(f"🔍 {error['title'][:30]}... 디버깅 정보", expanded=False):
                                    if debug_info.get("steps"):
                                        st.write("**진행 단계:**")
                                        for step in debug_info["steps"]:
                                            st.write(f"• {step}")
                                    if debug_info.get("errors"):
                                        st.write("**오류:**")
                                        for err in debug_info["errors"]:
                                            st.error(f"• {err}")
                
                # 초기화 버튼
                if st.button("🔄 새로운 번역 시작", key="reset_auto_translation"):
                    st.session_state.auto_translation_selected = []
                    st.session_state.auto_translation_results = []
                    st.session_state.auto_translation_errors = []
                    st.session_state.auto_translation_current = 0
                    if "auto_translation_debug" in st.session_state:
                        del st.session_state.auto_translation_debug
                    st.rerun()
        
        else:
            st.warning("⚠️ 번역할 문제를 선택해주세요")
    
    else:
        st.info("💡 문제를 검색하여 번역할 문제를 선택해주세요")

