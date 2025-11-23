"""
자동 문제 검토 탭
"""
import streamlit as st
import json
import uuid
import re
from datetime import datetime
from src.constants import ASSESSMENT_AREAS, QUESTION_TYPES, VALID_DIFFICULTIES, DEFAULT_DIFFICULTY, DEFAULT_DOMAIN

def update_selection(question_index):
    """체크박스 선택 상태를 업데이트하는 함수"""
    if "selected_questions" not in st.session_state:
        st.session_state.selected_questions = []
    
    # 현재 문제 목록의 길이 확인 (auto_review_questions가 있는 경우)
    if "auto_review_questions" in st.session_state and st.session_state.auto_review_questions:
        max_index = len(st.session_state.auto_review_questions) - 1
        if question_index > max_index:
            # 유효하지 않은 인덱스는 무시
            return
    
    if question_index in st.session_state.selected_questions:
        st.session_state.selected_questions.remove(question_index)
    else:
        st.session_state.selected_questions.append(question_index)


def render(st):
    st.header("🤖 자동 문제 교정")
    st.caption("questions_multiple_choice/questions_subjective 테이블의 문제를 교정하여 structured_problems 테이블에 저장합니다.")
    
    # DB 연결 체크
    if st.session_state.db is None:
        st.error("❌ 데이터베이스 연결이 초기화되지 않았습니다.")
        st.info("💡 **해결 방법**:")
        st.write("1. ⚙️ **설정** 탭으로 이동하세요.")
        st.write("2. **Edge Function URL**과 **Edge Shared Token**이 올바르게 설정되어 있는지 확인하세요.")
        st.write("3. Streamlit Cloud를 사용하는 경우 `.streamlit/secrets.toml` 파일에 다음 값들이 설정되어 있어야 합니다:")
        st.code("""
EDGE_FUNCTION_URL = "your-edge-function-url"
EDGE_SHARED_TOKEN = "your-edge-shared-token"
SUPABASE_ANON_KEY = "your-supabase-anon-key"
        """)
        st.write("4. 로컬 환경을 사용하는 경우 `.env` 파일에 다음 값들이 설정되어 있어야 합니다:")
        st.code("""
EDGE_FUNCTION_URL=your-edge-function-url
EDGE_SHARED_TOKEN=your-edge-shared-token
SUPABASE_ANON_KEY=your-supabase-anon-key
        """)
        
        # 디버깅 정보 표시
        with st.expander("🔍 디버깅 정보", expanded=False):
            from src.config import get_secret
            import os
            edge_url = get_secret("EDGE_FUNCTION_URL") or os.getenv("EDGE_FUNCTION_URL")
            edge_token = get_secret("EDGE_SHARED_TOKEN") or os.getenv("EDGE_SHARED_TOKEN")
            supabase_key = get_secret("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_ANON_KEY")
            
            st.write("**환경 변수 확인:**")
            st.write(f"- EDGE_FUNCTION_URL: {'✅ 설정됨' if edge_url else '❌ 설정되지 않음'}")
            st.write(f"- EDGE_SHARED_TOKEN: {'✅ 설정됨' if edge_token else '❌ 설정되지 않음'}")
            st.write(f"- SUPABASE_ANON_KEY: {'✅ 설정됨' if supabase_key else '❌ 설정되지 않음'}")
            
            if st.session_state.get("_edge_init_ok") is False:
                st.error("Edge Function 초기화 실패")
            elif st.session_state.get("_edge_init_ok") is True:
                st.success("Edge Function 초기화 완료")
            else:
                st.warning("Edge Function 초기화 상태 확인 불가")
        
        return
    
    # 디버깅 정보 표시 섹션 (고정)
    st.markdown("---")
    st.markdown("### 🔧 AI 교정 디버깅 정보")
    
    # 메서드 사용 정보 표시 (항상 표시)
    if "correction_method_debug" in st.session_state and st.session_state.correction_method_debug:
        latest_method_debug = st.session_state.correction_method_debug[-1]
        use_new = latest_method_debug.get("use_new_method", False)
        debug_info = latest_method_debug.get("debug_info", {})
        
        # 항상 표시되는 경고 박스
        if not use_new:
            st.error("⚠️ **중요**: `review_content` 메서드가 사용되었습니다. 레이어 구조가 아닌 일반 형식으로 응답됩니다.")
            st.write("**상세 정보:**")
            st.json(debug_info)
            if debug_info.get("reason"):
                st.write(f"**이유**: {debug_info.get('reason')}")
            if debug_info.get("import_error"):
                st.write(f"**Import 오류**: {debug_info.get('import_error')}")
            st.info("💡 **해결 방법**: `pip install google-genai`를 실행하세요.")
        else:
            st.success("✅ `correct_problem` 메서드가 사용되었습니다 (레이어 구조)")
        
        with st.expander("🔍 최근 API 메서드 선택 정보", expanded=False):
            st.write("**사용된 메서드**:", "✅ `correct_problem`" if use_new else "⚠️ `review_content`")
            st.json(debug_info)
    
    if "correction_method_used" in st.session_state and st.session_state.correction_method_used:
        with st.expander("📋 메서드 사용 이력", expanded=False):
            for i, method_info in enumerate(st.session_state.correction_method_used[-5:], 1):  # 최근 5개만
                st.write(f"{i}. **{method_info.get('method')}** - {method_info.get('timestamp', 'N/A')}")
                if method_info.get('error'):
                    st.write(f"   오류: {method_info.get('error')}")
                if method_info.get('reason'):
                    st.write(f"   이유: {method_info.get('reason')}")
    
    # 디버깅 정보 상태 확인
    debug_count = len(st.session_state.get("correction_debug_info", []))
    st.info(f"현재 저장된 디버깅 정보: {debug_count}개")
    
    if debug_count > 0:
        # 최신 디버깅 정보 표시
        latest_debug = st.session_state.correction_debug_info[-1]
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info(f"**최신 교정 결과**: {latest_debug.get('question_title', 'N/A')[:50]}...")
        with col2:
            if st.button("🗑️ 디버깅 정보 초기화", key="clear_debug_info"):
                st.session_state.correction_debug_info = []
                st.rerun()
        
        # 디버깅 정보 상세 표시
        with st.expander("📊 상세 디버깅 정보", expanded=True):
            # 상태 표시
            if latest_debug.get("status") == "success":
                st.success("✅ 교정 성공")
            else:
                st.error(f"❌ 교정 실패: {latest_debug.get('status', 'unknown')}")
            
            # 저장 상태 표시
            if latest_debug.get("save_success"):
                st.success("✅ 저장 성공")
            else:
                st.error(f"❌ 저장 실패")
                if latest_debug.get("save_error"):
                    st.error(f"오류: {latest_debug.get('save_error')}")
            
            # 탭으로 구분
            tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["원본 데이터", "AI 응답", "교정 데이터", "매핑 데이터", "저장 오류", "🔧 API 설정"])
            
            with tab1:
                st.json(latest_debug.get("original_data", {}))
            
            with tab2:
                ai_response = latest_debug.get("ai_response", "")
                if ai_response:
                    st.text(ai_response[:2000] + "..." if len(ai_response) > 2000 else ai_response)
                else:
                    st.warning("AI 응답이 없습니다.")
            
            with tab3:
                if latest_debug.get("corrected_data"):
                    st.json(latest_debug.get("corrected_data"))
                else:
                    st.warning("교정 데이터가 없습니다.")
            
            with tab4:
                if latest_debug.get("mapped_data"):
                    st.json(latest_debug.get("mapped_data"))
                    st.info(f"저장 대상: {latest_debug.get('target_table', 'N/A')}")
                else:
                    st.warning("매핑 데이터가 없습니다.")
            
            with tab5:
                if latest_debug.get("save_error"):
                    st.error(latest_debug.get("save_error"))
                else:
                    st.info("저장 오류 정보가 없습니다.")
            
            with tab6:
                # 최신 API 호출 정보 표시
                if "gemini_api_debug" in st.session_state and st.session_state.gemini_api_debug:
                    latest_api_debug = st.session_state.gemini_api_debug[-1]
                    
                    st.markdown("### 🤖 제미나이 모델 정보")
                    st.write(f"**모델**: `{latest_api_debug.get('model', 'N/A')}`")
                    st.write(f"**사용된 메서드**: `{latest_api_debug.get('method', 'N/A')}`")
                    st.write(f"**호출 시간**: {latest_api_debug.get('timestamp', 'N/A')}")
                    
                    st.markdown("### ⚙️ API 파라미터")
                    params = latest_api_debug.get("parameters", {})
                    param_col1, param_col2 = st.columns(2)
                    with param_col1:
                        st.write(f"**Temperature**: {params.get('temperature', 'N/A')}")
                        st.write(f"**Thinking Level**: {params.get('thinking_level', 'N/A')}")
                    with param_col2:
                        st.write(f"**Media Resolution**: {params.get('media_resolution', 'N/A')}")
                        st.write(f"**Response MIME Type**: {params.get('response_mime_type', 'N/A')}")
                    st.write(f"**Response Schema**: {params.get('response_schema', 'N/A')}")
                    
                    st.markdown("### 📝 사용된 프롬프트")
                    prompts = latest_api_debug.get("prompts", {})
                    
                    # System Prompt
                    with st.expander("📋 System Prompt (시스템 프롬프트)", expanded=False):
                        system_prompt = prompts.get("system_prompt", "")
                        if system_prompt:
                            st.write(f"**길이**: {prompts.get('system_prompt_length', 0)} 문자")
                            st.code(system_prompt, language="text")
                        else:
                            st.warning("System Prompt가 없습니다.")
                    
                    # User Prompt
                    with st.expander("💬 User Prompt (사용자 프롬프트)", expanded=False):
                        user_prompt = prompts.get("user_prompt", "")
                        if user_prompt:
                            st.write(f"**길이**: {prompts.get('user_prompt_length', 0)} 문자")
                            st.code(user_prompt[:5000] + "..." if len(user_prompt) > 5000 else user_prompt, language="text")
                        else:
                            st.warning("User Prompt가 없습니다.")
                    
                    # Combined Prompt (review_content의 경우)
                    if "combined_prompt" in prompts:
                        with st.expander("🔗 Combined Prompt (통합 프롬프트)", expanded=False):
                            combined_prompt = prompts.get("combined_prompt", "")
                            if combined_prompt:
                                st.write(f"**길이**: {prompts.get('combined_prompt_length', 0)} 문자")
                                st.code(combined_prompt[:5000] + "..." if len(combined_prompt) > 5000 else combined_prompt, language="text")
                    
                    # 전체 디버깅 정보 (JSON)
                    with st.expander("🔍 전체 API 디버깅 정보 (JSON)", expanded=False):
                        st.json(latest_api_debug)
                    
                    # 이전 호출 이력
                    if len(st.session_state.gemini_api_debug) > 1:
                        st.markdown("### 📚 이전 API 호출 이력")
                        for i, api_info in enumerate(st.session_state.gemini_api_debug[-5:-1], 1):  # 최근 5개 중 마지막 4개
                            with st.expander(f"호출 #{len(st.session_state.gemini_api_debug) - i} - {api_info.get('timestamp', 'N/A')}", expanded=False):
                                st.write(f"**모델**: {api_info.get('model', 'N/A')}")
                                st.write(f"**메서드**: {api_info.get('method', 'N/A')}")
                                st.json(api_info.get("parameters", {}))
                else:
                    st.warning("API 호출 정보가 없습니다. 문제 교정을 실행하면 여기에 정보가 표시됩니다.")
    else:
        st.warning("디버깅 정보가 없습니다. 문제 교정을 실행하면 여기에 정보가 표시됩니다.")
    
    st.markdown("---")
    
    
    # 1단계: 문제 가져오기 및 필터링
    st.markdown("### 문제 가져오기 및 필터링")
    
    # 필터링 옵션
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # 평가 영역 필터
        def format_review_area(x):
            if x == "전체":
                return "전체"
            return x
        
        area_filter = st.selectbox(
            "평가 영역 필터",
            options=["전체"] + list(ASSESSMENT_AREAS.keys()),
            format_func=format_review_area,
            key="auto_review_area_filter_v3",
            index=0
        )
    
    with col2:
        # 문제 유형 필터
        type_filter = st.selectbox(
            "문제 유형 필터", 
            options=["전체", "multiple_choice", "subjective"],
            format_func=lambda x: "전체" if x == "전체" else ("객관식" if x == "multiple_choice" else "주관식"),
            key="auto_review_type_filter_v3",
            index=0
        )
    
    with col3:
        # 교정 상태 필터 (현재 비활성화)
        correction_status = st.selectbox(
            "교정 상태 필터", 
            options=["전체", "미교정", "교정완료"],
            format_func=lambda x: "전체" if x == "전체" else ("미교정" if x == "미교정" else "교정완료"),
            key="auto_review_correction_filter_v3",
            index=0
        )
    
    # 필터 적용하여 문제 가져오기
    if st.button("🔍 문제 조회", type="primary", key="auto_review_search_v3"):
        questions = []
        
        # 교정 상태 필터 설정
        review_done_filter = None
        if correction_status == "미교정":
            review_done_filter = False
        elif correction_status == "교정완료":
            review_done_filter = True
        
        # 문제 유형에 따라 다른 테이블에서 조회
        if type_filter == "전체":
            # 객관식과 주관식 모두 조회
            mc_filters = {}
            sub_filters = {}
            
            if area_filter != "전체":
                mc_filters["category"] = ASSESSMENT_AREAS[area_filter]
                sub_filters["category"] = ASSESSMENT_AREAS[area_filter]
            
            if review_done_filter is not None:
                mc_filters["review_done"] = review_done_filter
                sub_filters["review_done"] = review_done_filter
            
            # 객관식 문제 조회
            mc_questions = st.session_state.db.get_multiple_choice_questions(mc_filters)
            for q in mc_questions:
                q["question_type"] = "multiple_choice"
            questions.extend(mc_questions)
            
            # 주관식 문제 조회
            sub_questions = st.session_state.db.get_subjective_questions(sub_filters)
            for q in sub_questions:
                q["question_type"] = "subjective"
            questions.extend(sub_questions)
            
        elif type_filter == "multiple_choice":
            filters = {}
            if area_filter != "전체":
                filters["category"] = ASSESSMENT_AREAS[area_filter]
            if review_done_filter is not None:
                filters["review_done"] = review_done_filter
            
            questions = st.session_state.db.get_multiple_choice_questions(filters)
            for q in questions:
                q["question_type"] = "multiple_choice"
                
        elif type_filter == "subjective":
            filters = {}
            if area_filter != "전체":
                filters["category"] = ASSESSMENT_AREAS[area_filter]
            if review_done_filter is not None:
                filters["review_done"] = review_done_filter
            
            questions = st.session_state.db.get_subjective_questions(filters)
            for q in questions:
                q["question_type"] = "subjective"
        
        st.session_state.auto_review_questions = questions
        st.success(f"총 {len(questions)}개의 문제를 찾았습니다.")
        
        # 기존 선택된 문제 정보 초기화
        if "selected_auto_review_question" in st.session_state:
            del st.session_state.selected_auto_review_question
        if "mapped_auto_review_data" in st.session_state:
            del st.session_state.mapped_auto_review_data
        # 선택 상태를 안전하게 초기화
        st.session_state.selected_questions = []
    
    # 조회된 문제 표시 및 자동 처리
    if "auto_review_questions" in st.session_state and st.session_state.auto_review_questions:
        questions = st.session_state.auto_review_questions
        
        st.markdown("### 조회된 문제 목록")
        st.info(f"📊 총 {len(questions)}개의 문제가 조회되었습니다. 원하는 문제를 선택하여 교정할 수 있습니다.")
        
        # 조회된 문제 목록을 테이블 형태로 표시 (선택 기능 포함)
        with st.expander("조회된 문제 목록", expanded=True):
            # 선택 상태 초기화 및 유효성 검사
            if "selected_questions" not in st.session_state:
                st.session_state.selected_questions = []
            else:
                # 기존 선택 상태에서 유효하지 않은 인덱스 제거
                valid_indices = [i for i in st.session_state.selected_questions if 0 <= i < len(questions)]
                if len(valid_indices) != len(st.session_state.selected_questions):
                    st.session_state.selected_questions = valid_indices
            
            # 전체 선택/해제 버튼
            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                if st.button("✅ 전체 선택", key="select_all_questions"):
                    if "selected_questions" not in st.session_state:
                        st.session_state.selected_questions = []
                    st.session_state.selected_questions = list(range(len(questions)))
                    st.rerun()
            with col2:
                if st.button("❌ 전체 해제", key="deselect_all_questions"):
                    st.session_state.selected_questions = []
                    st.rerun()
            with col3:
                selected_count = len(st.session_state.selected_questions)
                st.info(f"선택된 문제: {selected_count}개 / 전체 {len(questions)}개")
            
            st.markdown("---")
            
            # 체크박스와 테이블을 함께 표시
            st.markdown("**문제 목록 (체크박스로 선택):**")
            
            # 각 문제별로 체크박스와 정보를 행으로 표시
            for i, question in enumerate(questions):
                # 문제 유형에 따라 다른 필드에서 제목 가져오기
                if question.get("question_type") == "multiple_choice":
                    question_text = question.get("problem_title", "제목 없음")
                else:
                    question_text = question.get("title", "제목 없음")
                
                # question_status 정보 가져오기
                question_status = question.get("question_status", {})
                review_done = question_status.get("review_done", False) if question_status else False
                translation_done = question_status.get("translation_done", False) if question_status else False
                
                # 컬럼으로 나누기 (체크박스 + 문제 정보)
                col1, col2, col3, col4, col5, col6, col7 = st.columns([0.1, 0.1, 0.15, 0.4, 0.1, 0.1, 0.1])
                
                with col1:
                    # 체크박스
                    if "selected_questions" not in st.session_state:
                        st.session_state.selected_questions = []
                    
                    # 현재 인덱스가 유효한 범위 내에 있는지 확인
                    is_valid_index = 0 <= i < len(questions)
                    is_currently_selected = i in st.session_state.selected_questions and is_valid_index
                    
                    is_selected = st.checkbox(
                        "", 
                        value=is_currently_selected,
                        key=f"question_checkbox_{i}",
                        on_change=lambda idx=i: update_selection(idx)
                    )
                
                with col2:
                    st.write(f"**{i+1}**")
                
                with col3:
                    question_type_text = "객관식" if question.get("question_type") == "multiple_choice" else "주관식"
                    st.write(question_type_text)
                
                with col4:
                    st.write(f"{question_text[:60]}{'...' if len(question_text) > 60 else ''}")
                
                with col5:
                    review_status = "✅완료" if review_done else "❌미완료"
                    st.write(review_status)
                
                with col6:
                    translation_status = "✅완료" if translation_done else "❌미완료"
                    st.write(translation_status)
                
                with col7:
                    st.write(question.get("difficulty", ""))
                
                # 구분선 (마지막 문제 제외)
                if i < len(questions) - 1:
                    st.markdown("---")
            
            # 테이블 헤더 표시 (참고용)
            st.markdown("**컬럼 설명:**")
            st.caption("체크박스 | 번호 | 유형 | 제목 | 교정여부 | 번역여부 | 난이도")
            
            st.markdown("---")
            
            # 선택된 문제 요약
            if "selected_questions" in st.session_state and st.session_state.selected_questions:
                # 유효한 인덱스만 필터링하고 세션 상태 업데이트
                valid_selected = [i for i in st.session_state.selected_questions if 0 <= i < len(questions)]
                if len(valid_selected) != len(st.session_state.selected_questions):
                    # 유효하지 않은 인덱스가 있으면 세션 상태 업데이트
                    st.session_state.selected_questions = valid_selected
                
                if valid_selected:
                    selected_indices = sorted(valid_selected)
                    st.success(f"✅ {len(selected_indices)}개 문제가 선택되었습니다: {[i+1 for i in selected_indices]}번")
                else:
                    st.warning("⚠️ 교정할 문제를 선택해주세요.")
            else:
                st.warning("⚠️ 교정할 문제를 선택해주세요.")
        
        # 자동 처리 시작 버튼
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # 선택된 문제만 처리
            if st.button("🚀 선택된 문제 교정 시작", type="primary", key="auto_review_selected_start"):
                if not st.session_state.selected_questions:
                    st.error("교정할 문제를 선택해주세요.")
                else:
                    # 선택된 인덱스가 유효한지 검증
                    valid_indices = [i for i in st.session_state.selected_questions if 0 <= i < len(questions)]
                    if not valid_indices:
                        st.error("선택된 문제 인덱스가 유효하지 않습니다. 다시 선택해주세요.")
                        st.session_state.selected_questions = []
                        st.rerun()
                    else:
                        selected_questions = [questions[i] for i in valid_indices]
                        # 유효하지 않은 인덱스가 있었다면 선택 상태 업데이트
                        if len(valid_indices) != len(st.session_state.selected_questions):
                            st.session_state.selected_questions = valid_indices
                            st.warning(f"유효하지 않은 선택이 제거되었습니다. {len(valid_indices)}개 문제가 선택되었습니다.")
                    st.session_state.auto_review_batch_processing = True
                    st.session_state.auto_review_batch_progress = {
                        "total": len(selected_questions),
                        "completed": 0,
                        "success": 0,
                        "failed": 0,
                        "results": [],
                        "start_time": datetime.now()
                    }
                    st.session_state.auto_review_questions = selected_questions  # 선택된 문제만 저장
                    st.rerun()
        
        with col2:
            # 모든 문제 처리 (기존 기능 유지)
            if st.button("🚀 모든 문제 교정 시작", key="auto_review_all_start"):
                st.session_state.auto_review_batch_processing = True
                st.session_state.auto_review_batch_progress = {
                    "total": len(questions),
                    "completed": 0,
                    "success": 0,
                    "failed": 0,
                    "results": [],
                    "start_time": datetime.now()
                }
                st.rerun()
        
        # 자동 배치 처리 실행
        if st.session_state.get("auto_review_batch_processing", False):
            auto_process_all_questions(st, questions)
            return
    


def extract_json_from_text(text: str) -> dict:
    """
    텍스트에서 JSON 부분을 추출합니다.
    """
    if not text:
        return {}
    
    # 1. 먼저 전체 텍스트가 JSON인지 확인
    try:
        result = json.loads(text.strip())
        return result
    except json.JSONDecodeError:
        pass
    
    # 2. 코드 블록(```json ... ```) 내부의 JSON 추출
    code_block_pattern = r'```(?:json)?\s*\n?(\{.*?\})\s*\n?```'
    code_matches = re.findall(code_block_pattern, text, re.DOTALL)
    
    for match in code_matches:
        try:
            cleaned_match = match.strip()
            result = json.loads(cleaned_match)
            return result
        except json.JSONDecodeError:
            continue
    
    # 3. 더 간단한 코드 블록 패턴도 시도
    simple_code_pattern = r'```json\s*(\{.*?\})\s*```'
    simple_matches = re.findall(simple_code_pattern, text, re.DOTALL)
    for match in simple_matches:
        try:
            cleaned_match = match.strip()
            return json.loads(cleaned_match)
        except json.JSONDecodeError:
            continue
    
    # 4. 첫 번째 중괄호부터 마지막 중괄호까지 추출
    first_brace = text.find('{')
    last_brace = text.rfind('}')
    
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        json_candidate = text[first_brace:last_brace + 1]
        try:
            result = json.loads(json_candidate)
            return result
        except json.JSONDecodeError:
            pass
    
    # 5. 여러 JSON 객체가 있는 경우 가장 긴 것 선택
    json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
    matches = re.findall(json_pattern, text, re.DOTALL)
    
    # 가장 긴 JSON 후보를 선택
    longest_match = ""
    for match in matches:
        if len(match) > len(longest_match):
            longest_match = match
    
    if longest_match:
        try:
            return json.loads(longest_match)
        except json.JSONDecodeError:
            pass
    
    # 6. 중괄호 개수를 맞춰서 JSON 추출 시도
    brace_count = 0
    start_idx = -1
    
    for i, char in enumerate(text):
        if char == '{':
            if brace_count == 0:
                start_idx = i
            brace_count += 1
        elif char == '}':
            brace_count -= 1
            if brace_count == 0 and start_idx != -1:
                json_candidate = text[start_idx:i + 1]
                try:
                    return json.loads(json_candidate)
                except json.JSONDecodeError:
                    continue
    
    # 7. 플레이스홀더가 있는 JSON 처리 (예: {time_limit})
    if '{' in text and '}' in text:
        # 플레이스홀더를 기본값으로 대체하여 JSON 파싱 시도
        placeholder_replacements = {
            '{time_limit}': '"5분"',
            '{difficulty}': f'"{DEFAULT_DIFFICULTY}"',
            '{category}': f'"{DEFAULT_DOMAIN}"',
            '{lang}': '"kr"'
        }
        
        # 첫 번째 중괄호부터 마지막 중괄호까지 추출
        first_brace = text.find('{')
        last_brace = text.rfind('}')
        
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            json_candidate = text[first_brace:last_brace + 1]
            
            # 플레이스홀더 대체
            for placeholder, replacement in placeholder_replacements.items():
                json_candidate = json_candidate.replace(placeholder, replacement)
            
            try:
                result = json.loads(json_candidate)
                return result
            except json.JSONDecodeError:
                pass
    
    # 8. 주관식 문제의 특수한 경우 처리
    # 주관식 문제는 때때로 여러 줄에 걸쳐 JSON이 작성될 수 있음
    lines = text.split('\n')
    json_lines = []
    in_json = False
    brace_count = 0
    
    for line in lines:
        line = line.strip()
        if line.startswith('{'):
            in_json = True
            json_lines = [line]
            brace_count = line.count('{') - line.count('}')
        elif in_json:
            json_lines.append(line)
            brace_count += line.count('{') - line.count('}')
            if brace_count == 0:
                # 중괄호가 균형을 이룰 때까지 수집
                json_candidate = '\n'.join(json_lines)
                try:
                    result = json.loads(json_candidate)
                    return result
                except json.JSONDecodeError:
                    continue
    
    # 9. 마지막 시도: 텍스트에서 모든 중괄호 쌍을 찾아서 가장 완전한 JSON 추출
    if '{' in text and '}' in text:
        # 중괄호의 위치를 찾아서 가장 완전한 JSON 구조 추출
        start_pos = text.find('{')
        if start_pos != -1:
            # 시작 중괄호부터 끝까지 스캔하여 완전한 JSON 구조 찾기
            brace_count = 0
            end_pos = -1
            
            for i in range(start_pos, len(text)):
                if text[i] == '{':
                    brace_count += 1
                elif text[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_pos = i
                        break
            
            if end_pos != -1:
                json_candidate = text[start_pos:end_pos + 1]
                try:
                    result = json.loads(json_candidate)
                    return result
                except json.JSONDecodeError:
                    pass
    
    # 10. 주관식 문제의 특수한 경우: 텍스트에서 JSON 구조를 더 유연하게 추출
    # 예: "다음은 문제입니다: { ... } 이것이 문제입니다" 같은 형태
    if '{' in text and '}' in text:
        # 텍스트를 줄 단위로 분할하여 JSON 구조 찾기
        lines = text.split('\n')
        json_candidates = []
        
        for i, line in enumerate(lines):
            if '{' in line:
                # 이 줄부터 시작하여 JSON 구조 완성 시도
                json_lines = []
                brace_count = 0
                
                for j in range(i, len(lines)):
                    current_line = lines[j]
                    json_lines.append(current_line)
                    
                    # 중괄호 개수 계산
                    brace_count += current_line.count('{') - current_line.count('}')
                    
                    if brace_count == 0:
                        # 중괄호가 균형을 이룰 때까지 수집
                        json_candidate = '\n'.join(json_lines)
                        json_candidates.append(json_candidate)
                        break
        
        # 가장 긴 JSON 후보를 선택하여 파싱 시도
        if json_candidates:
            longest_candidate = max(json_candidates, key=len)
            try:
                result = json.loads(longest_candidate)
                return result
            except json.JSONDecodeError:
                pass
    
    # 11. 마지막 시도: 주관식 문제의 특수한 경우 처리
    # 예: "문제: { ... } 답안: { ... }" 같은 형태에서 첫 번째 JSON만 추출
    if '{' in text and '}' in text:
        # 첫 번째 완전한 JSON 구조만 추출
        start_pos = text.find('{')
        if start_pos != -1:
            brace_count = 0
            end_pos = -1
            
            for i in range(start_pos, len(text)):
                if text[i] == '{':
                    brace_count += 1
                elif text[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_pos = i
                        break
            
            if end_pos != -1:
                json_candidate = text[start_pos:end_pos + 1]
                try:
                    result = json.loads(json_candidate)
                    return result
                except json.JSONDecodeError:
                    pass
    
    return {}

def ensure_array_format(data) -> list:
    """데이터를 올바른 배열 형식으로 변환 (JSONB 호환)"""
    if data is None:
        return []
    
    if isinstance(data, list):
        # 이미 배열인 경우, 각 요소를 그대로 유지 (이스케이프 방지)
        result = [item for item in data if item is not None and str(item).strip()]
        return result
    
    if isinstance(data, str):
        # 문자열인 경우, JSON 파싱 시도 후 실패하면 단일 요소 배열로 변환
        try:
            parsed = json.loads(data)
            if isinstance(parsed, list):
                # 파싱된 배열의 각 요소를 그대로 유지
                result = [item for item in parsed if item is not None and str(item).strip()]
                return result
            else:
                # 단일 값인 경우 그대로 반환
                result = [parsed] if str(parsed).strip() else []
                return result
        except (json.JSONDecodeError, TypeError):
            # JSON 파싱 실패 시 원본 문자열을 그대로 반환
            result = [data] if data.strip() else []
            return result
    
    # 기타 타입인 경우 그대로 단일 요소 배열로 반환
    result = [data] if str(data).strip() else []
    return result

def map_question_to_qlearn_format(question: dict) -> dict:
    """questions 테이블 데이터를 qlearn_problems 형식으로 매핑"""
    
    # UUID 생성
    problem_id = str(uuid.uuid4())
    
    # 현재 시간
    now = datetime.now()
    
    # 메타데이터 추출
    metadata = question.get("metadata", {})
    
    # difficulty 값 변환 (Supabase q_difficulty enum에 맞게) - 허용된 값만 사용
    difficulty_mapping = {
        "very_easy": "very easy",
        "easy": "easy",
        "medium": "normal",  # medium을 normal로 변환
        "normal": "normal",
        "hard": "hard",
        "very_hard": "very hard",
        "보통": "normal",  # 한국어 "보통"을 "normal"로 변환
        "쉬움": "easy",
        "어려움": "hard",
        "아주 쉬움": "very easy",
        "아주 어려움": "very hard",
        "매우 어려움": "very hard",
        "": "normal",  # 기본값
        None: "normal"
    }
    
    # Supabase q_difficulty enum 값만 허용
    original_difficulty = question.get("difficulty", "")
    valid_difficulty = difficulty_mapping.get(original_difficulty, DEFAULT_DIFFICULTY)
    
    # 최종 검증: 허용된 enum 값이 아니면 기본값으로 설정
    if valid_difficulty not in VALID_DIFFICULTIES:
        valid_difficulty = DEFAULT_DIFFICULTY
    
    # 난이도별 time_limit 기본값 설정
    time_limit_defaults = {
        "very easy": "3분 이내",
        "easy": "4분 이내", 
        "normal": "5분 이내",
        "hard": "7분 이내",
        "very hard": "10분 이내"
    }
    time_limit = metadata.get("time_limit", "")
    if not time_limit or time_limit == "":
        time_limit = time_limit_defaults.get(valid_difficulty, "5분 이내")
    
    # 매핑된 데이터 구성
    # JSON 필드들을 올바른 형식으로 변환
    
    # 주관식 문제의 특수한 필드들 처리
    # question 필드가 없으면 title이나 다른 필드에서 가져오기
    question_title = question.get("question", question.get("title", question.get("problem_title", "")))
    if not question_title:
        question_title = metadata.get("topic", question.get("topic", "제목 없음"))
    
    # scenario 필드 처리 (여러 소스에서 가져오기)
    scenario = metadata.get("scenario", question.get("scenario", ""))
    
    # task 필드 처리
    task = metadata.get("task", question.get("task", ""))
    
    # JSON 필드들을 직접 question에서 가져오기 (metadata가 아닌)
    goal_data = question.get("goal", metadata.get("goal", []))
    first_question_data = question.get("first_question", metadata.get("first_question", []))
    requirements_data = question.get("requirements", metadata.get("requirements", []))
    constraints_data = question.get("constraints", metadata.get("constraints", []))
    guide_data = question.get("guide", metadata.get("guide", {}))
    evaluation_data = question.get("evaluation", metadata.get("evaluation", []))
    
    # ensure_array_format 함수 적용
    processed_goal = ensure_array_format(goal_data)
    processed_first_question = ensure_array_format(first_question_data)
    processed_requirements = ensure_array_format(requirements_data)
    processed_constraints = ensure_array_format(constraints_data)
    processed_evaluation = ensure_array_format(evaluation_data)
    
    mapped_data = {
        "id": problem_id,
        "area": question.get("area", ""),  # area 필드 추가
        "lang": metadata.get("lang", question.get("lang", "kr")),
        "category": metadata.get("category", question.get("category", "")),
        "topic": metadata.get("topic", question.get("topic", "")),
        "difficulty": valid_difficulty,  # 변환된 difficulty 사용
        "time_limit": time_limit,
        "topic_summary": question.get("topic_summary", metadata.get("topic_summary", metadata.get("topic", question.get("topic", "")))),
        "title": question_title,
        "scenario": scenario,
        "goal": processed_goal,
        "first_question": processed_first_question,
        "requirements": processed_requirements,
        "constraints": processed_constraints,
        "guide": guide_data if isinstance(guide_data, dict) else {},
        "evaluation": processed_evaluation,
        "task": task,
        # created_by 필드는 제외 (UUID 오류 방지)
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
        "reference": metadata.get("reference", question.get("reference", {})),
        "active": False  # 기본값
    }
    
    # 매핑 완료
    
    return mapped_data

def map_to_structured_problem_format(corrected_data: dict) -> dict:
    """교정된 데이터를 structured_problems 테이블 형식으로 매핑"""
    
    # 교정된 데이터는 4개 레이어 구조로 반환됨
    meta_layer = corrected_data.get("meta_layer", {})
    user_view_layer = corrected_data.get("user_view_layer", {})
    system_view_layer = corrected_data.get("system_view_layer", {})
    evaluation_layer = corrected_data.get("evaluation_layer", {})
    
    # 현재 시간
    now = datetime.now()
    
    # 날짜 형식 변환 함수
    def format_timestamp(date_value):
        """날짜 문자열을 ISO 형식으로 변환"""
        if not date_value:
            return now.isoformat()
        
        if isinstance(date_value, str):
            # PostgreSQL timestamp 형식 (예: "2025-10-23 08:50:14.242741+00")을 ISO로 변환
            if ' ' in date_value and 'T' not in date_value:
                # 공백이 있고 T가 없으면 PostgreSQL 형식으로 간주
                try:
                    # 공백을 T로 변환
                    iso_string = date_value.replace(' ', 'T')
                    
                    # 시간대 형식 정리 (+00 -> +00:00, -00 -> -00:00)
                    import re
                    # 끝에 있는 +HH 또는 -HH 형식을 찾아서 +HH:00 또는 -HH:00로 변환
                    tz_pattern = r'([+-])(\d{2})$'
                    match = re.search(tz_pattern, iso_string)
                    if match:
                        sign = match.group(1)
                        hours = match.group(2)
                        iso_string = re.sub(tz_pattern, f'{sign}{hours}:00', iso_string)
                    elif not ('+' in iso_string or '-' in iso_string[-6:] or iso_string.endswith('Z')):
                        # 시간대가 없으면 UTC로 가정
                        iso_string += '+00:00'
                    
                    # datetime.fromisoformat으로 파싱 (Python 3.7+)
                    try:
                        from datetime import datetime
                        parsed_date = datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
                        return parsed_date.isoformat()
                    except ValueError:
                        # fromisoformat 실패 시 기본값 사용
                        return now.isoformat()
                except Exception as e:
                    # 파싱 실패 시 기본값 사용
                    return now.isoformat()
            else:
                # 이미 ISO 형식이면 그대로 사용 (파싱 시도)
                try:
                    from datetime import datetime
                    # Z를 +00:00로 변환 후 파싱
                    iso_value = date_value.replace('Z', '+00:00')
                    parsed_date = datetime.fromisoformat(iso_value)
                    return parsed_date.isoformat()
                except (ValueError, AttributeError):
                    return now.isoformat()
        
        return now.isoformat()
    
    # meta_layer에서 필드 추출
    # meta_layer에 id와 idx가 있으면 제거 (테이블에서 자동 생성)
    meta_layer_clean = {k: v for k, v in meta_layer.items() if k not in ['id', 'idx']}
    
    mapped_data = {
        # idx는 자동 증가 컬럼이므로 제외
        "lang": meta_layer_clean.get("lang", "kr"),
        "category": meta_layer_clean.get("category", ""),
        "topic": meta_layer_clean.get("topic", []),  # text[] 배열
        "difficulty": meta_layer_clean.get("difficulty", "normal"),
        "time_limit": meta_layer_clean.get("time_limit", ""),
        "problem_type": meta_layer_clean.get("problem_type", ""),
        "target_template_code": meta_layer_clean.get("target_template_code", ""),
        "created_by": meta_layer_clean.get("created_by"),
        "created_at": format_timestamp(meta_layer_clean.get("created_at")),
        "updated_at": format_timestamp(meta_layer_clean.get("updated_at")),
        "active": meta_layer_clean.get("active", True),
        # JSONB 필드들
        "user_view_layer": user_view_layer,
        "system_view_layer": system_view_layer,
        "evaluation_layer": evaluation_layer,
    }
    
    return mapped_data

def map_multiple_choice_to_qlearn_format(question: dict) -> dict:
    """객관식 문제를 qlearn_problems_multiple 형식으로 매핑"""
    
    # UUID 생성
    problem_id = str(uuid.uuid4())
    
    # 현재 시간
    now = datetime.now()
    
    # 메타데이터 추출
    metadata = question.get("metadata", {})
    
    # difficulty 값 변환 (Supabase q_difficulty enum에 맞게)
    difficulty_mapping = {
        "very_easy": "very easy",
        "easy": "easy",
        "medium": "normal",
        "normal": "normal",
        "hard": "hard",
        "very_hard": "very hard",
        "보통": "normal",
        "쉬움": "easy",
        "어려움": "hard",
        "아주 쉬움": "very easy",
        "아주 어려움": "very hard",
        "매우 어려움": "very hard",
        "": "normal",
        None: "normal"
    }
    
    original_difficulty = question.get("difficulty", "")
    valid_difficulty = difficulty_mapping.get(original_difficulty, DEFAULT_DIFFICULTY)
    
    if valid_difficulty not in VALID_DIFFICULTIES:
        valid_difficulty = DEFAULT_DIFFICULTY
    
    # 난이도별 estimated_time 기본값 설정
    time_limit_defaults = {
        "very easy": "3분 이내",
        "easy": "4분 이내", 
        "normal": "5분 이내",
        "hard": "7분 이내",
        "very hard": "10분 이내"
    }
    estimated_time = question.get("estimated_time", "")
    if not estimated_time or estimated_time == "":
        estimated_time = time_limit_defaults.get(valid_difficulty, "5분 이내")
    
    # 매핑된 데이터 구성
    mapped_data = {
        "id": problem_id,
        "lang": metadata.get("lang", question.get("lang", "kr")),
        "category": metadata.get("category", question.get("category", "")),
        "problem_title": question.get("problem_title", question.get("title", "")),
        "difficulty": valid_difficulty,
        "estimated_time": estimated_time,
        "scenario": question.get("scenario", ""),
        "steps": ensure_array_format(question.get("steps", [])),
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
        "image_url": question.get("image_url"),
        "active": False,  # 기본값
        "topic_summary": question.get("topic_summary", metadata.get("topic_summary", metadata.get("topic", question.get("topic", ""))))
    }
    
    # 매핑 완료
    
    return mapped_data

def auto_process_all_questions(st, questions):
    """모든 문제를 자동으로 처리하는 함수"""
    
    progress = st.session_state.auto_review_batch_progress
    
    # 진행률 표시
    if progress["completed"] < progress["total"]:
        progress_bar = st.progress(progress["completed"] / progress["total"])
        elapsed_time = datetime.now() - progress["start_time"]
        st.caption(f"진행률: {progress['completed']}/{progress['total']} (성공: {progress['success']}, 실패: {progress['failed']}) - 경과시간: {elapsed_time}")
        
        # 현재 처리 중인 문제 표시
        current_question = questions[progress["completed"]]
        question_title = current_question.get('problem_title', current_question.get('title', '제목 없음'))
        st.info(f"🔄 현재 처리 중: {question_title[:100]}...")
        
        # 배치 처리 실행
        with st.spinner(f"자동 처리 중... ({progress['completed'] + 1}/{progress['total']})"):
            try:
                # 현재 처리할 문제
                current_question = questions[progress["completed"]]
                current_index = progress["completed"]
                question_type = current_question.get("question_type", "subjective")
                
                # 1. 문제 교정 (AI를 통한 교정)
                from src.services.problem_correction_service import ProblemCorrectionService
                correction_service = ProblemCorrectionService()
                
                if correction_service.is_available():
                    # 문제를 JSON으로 변환
                    question_json = json.dumps(current_question, ensure_ascii=False, indent=2)
                    
                    # 디버깅: 교정 서비스 상태 확인
                    st.write("🔍 **교정 서비스 상태 확인**")
                    with st.expander("📊 교정 서비스 정보", expanded=True):
                        st.write(f"**서비스 사용 가능**: {correction_service.is_available()}")
                        st.write(f"**Gemini Client 존재**: {correction_service.gemini_client is not None}")
                        
                        # NEW_GENAI_AVAILABLE 확인
                        try:
                            from src.services.gemini_client import NEW_GENAI_AVAILABLE
                            st.write(f"**NEW_GENAI_AVAILABLE**: {NEW_GENAI_AVAILABLE}")
                            st.write(f"**correct_problem 메서드 존재**: {hasattr(correction_service.gemini_client, 'correct_problem') if correction_service.gemini_client else False}")
                            
                            if not NEW_GENAI_AVAILABLE:
                                st.error("❌ `google-genai` 패키지가 설치되지 않았습니다!")
                                st.info("💡 해결 방법: `pip install google-genai`를 실행하세요.")
                            elif not hasattr(correction_service.gemini_client, 'correct_problem'):
                                st.error("❌ `correct_problem` 메서드가 없습니다!")
                            else:
                                st.success("✅ 새로운 `correct_problem` 메서드를 사용할 수 있습니다.")
                        except Exception as e:
                            st.error(f"❌ 상태 확인 중 오류: {str(e)}")
                    
                    # 교정 실행
                    st.write("🚀 **교정 실행 중...**")
                    corrected_result = correction_service.correct_problem(question_json, question_type)
                    
                    # 디버깅: 어떤 메서드가 사용되었는지 확인
                    st.write("📋 **교정 결과 요약**")
                    with st.expander("🔍 교정 메서드 사용 확인", expanded=True):
                        # 응답이 레이어 구조인지 확인
                        import json as json_lib
                        try:
                            parsed = json_lib.loads(corrected_result) if isinstance(corrected_result, str) else corrected_result
                            if isinstance(parsed, dict):
                                has_layers = "meta_layer" in parsed and "user_view_layer" in parsed
                                st.write(f"**레이어 구조 포함**: {'✅ 예' if has_layers else '❌ 아니오'}")
                                if has_layers:
                                    st.success("✅ `correct_problem` 메서드가 사용되었습니다 (레이어 구조)")
                                else:
                                    st.warning("⚠️ `review_content` 메서드가 사용되었습니다 (일반 형식)")
                                    st.write("**응답 키**:", list(parsed.keys())[:10])
                                    st.error("❌ **문제**: `google-genai` 패키지가 설치되지 않았거나 `correct_problem` 메서드가 호출되지 않았습니다.")
                                    st.info("💡 **해결 방법**: `pip install google-genai`를 실행하세요.")
                        except:
                            st.warning("⚠️ 응답 파싱 실패 - 메서드 확인 불가")
                    
                    # 디버깅 정보를 세션 상태에 저장
                    debug_info = {
                        "question_id": current_question.get("id", "unknown"),
                        "question_title": current_question.get("title", current_question.get("problem_title", "제목 없음")),
                        "original_data": current_question,
                        "ai_response": corrected_result,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    # 교정 결과에서 JSON 추출
                    corrected_data = extract_json_from_text(corrected_result)
                    if not corrected_data:
                        # 교정 실패 시 교정 결과를 UI에 표시
                        debug_info["status"] = "parsing_failed"
                        debug_info["corrected_data"] = None
                        debug_info["parsing_error"] = "JSON 추출 실패"
                        corrected_data = current_question  # 교정 실패 시 원본 사용
                        
                        # 디버깅: JSON 파싱 실패 상세 정보
                        st.error("❌ JSON 파싱 실패")
                        with st.expander("🔍 JSON 파싱 실패 상세 정보", expanded=True):
                            st.write("**AI 응답 원본 (처음 1000자):**")
                            st.code(corrected_result[:1000] if corrected_result else "응답 없음")
                            st.write("**AI 응답 전체 길이:**", len(corrected_result) if corrected_result else 0)
                    else:
                        # 교정 성공 시 결과를 UI에 표시
                        debug_info["status"] = "success"
                        debug_info["corrected_data"] = corrected_data
                        
                        # 디버깅: 교정된 데이터 구조 분석
                        st.write("🔍 **교정 결과 분석**")
                        with st.expander("📊 교정된 데이터 구조 분석", expanded=True):
                            # 데이터 타입 확인
                            st.write(f"**데이터 타입**: {type(corrected_data).__name__}")
                            
                            # 모든 키 확인
                            if isinstance(corrected_data, dict):
                                all_keys = list(corrected_data.keys())
                                st.write(f"**전체 키 목록 ({len(all_keys)}개)**: {all_keys}")
                                
                                # 레이어 구조 확인
                                required_layers = ["meta_layer", "user_view_layer", "system_view_layer", "evaluation_layer"]
                                st.write("**레이어 구조 확인:**")
                                for layer in required_layers:
                                    if layer in corrected_data:
                                        layer_data = corrected_data[layer]
                                        layer_type = type(layer_data).__name__
                                        if isinstance(layer_data, dict):
                                            layer_keys = list(layer_data.keys())
                                            st.write(f"  ✅ {layer}: {layer_type} (키: {len(layer_keys)}개) - {layer_keys[:10]}")
                                        else:
                                            st.write(f"  ✅ {layer}: {layer_type}")
                                    else:
                                        st.write(f"  ❌ {layer}: 없음")
                                
                                # 예상치 못한 키 확인
                                unexpected_keys = [k for k in all_keys if k not in required_layers]
                                if unexpected_keys:
                                    st.write(f"**예상치 못한 키**: {unexpected_keys}")
                            else:
                                st.error(f"❌ 교정된 데이터가 딕셔너리가 아닙니다: {type(corrected_data)}")
                    
                    # 디버깅 정보를 세션 상태에 저장
                    if "correction_debug_info" not in st.session_state:
                        st.session_state.correction_debug_info = []
                    st.session_state.correction_debug_info.append(debug_info)
                else:
                    st.warning("⚠️ 교정 서비스 사용 불가 - 원본 데이터 사용")
                    corrected_data = current_question  # 교정 서비스 사용 불가 시 원본 사용
                
                # 2. 교정된 데이터를 structured_problems 테이블에 저장
                save_success = False
                target_table = "structured_problems"
                mapped_data = None
                save_error = None
                
                # 교정된 데이터가 레이어 구조인지 확인
                if "meta_layer" in corrected_data and "user_view_layer" in corrected_data:
                    # 레이어 구조로 교정된 경우
                    try:
                        mapped_data = map_to_structured_problem_format(corrected_data)
                        
                        # 디버깅: 매핑된 데이터 확인
                        st.write("🔍 **디버깅 정보**")
                        with st.expander("📋 매핑된 데이터 미리보기", expanded=False):
                            st.json(mapped_data)
                        
                        # 필수 필드 확인
                        required_fields = ["lang", "category", "difficulty", "problem_type", "target_template_code"]
                        missing_fields = [field for field in required_fields if not mapped_data.get(field)]
                        if missing_fields:
                            st.error(f"❌ 필수 필드 누락: {missing_fields}")
                            save_error = f"필수 필드 누락: {missing_fields}"
                        else:
                            # 저장 시도
                            try:
                                st.write(f"💾 저장 시도 중... (Edge Function: {st.session_state.db.structured_problems_url})")
                                save_success = st.session_state.db.save_structured_problem(mapped_data)
                                if save_success:
                                    st.success("✅ 저장 성공!")
                                else:
                                    st.error("❌ 저장 실패 (응답 없음)")
                                    save_error = "저장 실패 (응답 없음)"
                            except Exception as save_ex:
                                st.error(f"❌ 저장 중 오류 발생: {str(save_ex)}")
                                save_error = str(save_ex)
                                save_success = False
                    except Exception as map_ex:
                        st.error(f"❌ 데이터 매핑 중 오류: {str(map_ex)}")
                        save_error = f"매핑 오류: {str(map_ex)}"
                        save_success = False
                else:
                    # 교정 실패 또는 레이어 구조가 아닌 경우
                    st.error("❌ **레이어 구조 검증 실패**")
                    
                    # 상세 분석
                    with st.expander("🔍 레이어 구조 검증 상세 분석", expanded=True):
                        # 데이터 타입 확인
                        st.write(f"**교정된 데이터 타입**: {type(corrected_data).__name__}")
                        
                        if isinstance(corrected_data, dict):
                            # 모든 키 확인
                            all_keys = list(corrected_data.keys())
                            st.write(f"**전체 키 목록 ({len(all_keys)}개)**:")
                            for key in all_keys:
                                value = corrected_data[key]
                                value_type = type(value).__name__
                                if isinstance(value, dict):
                                    value_keys = list(value.keys())[:5]
                                    st.write(f"  - `{key}`: {value_type} (키: {list(value.keys())[:10]})")
                                elif isinstance(value, (list, str)):
                                    preview = str(value)[:100] + "..." if len(str(value)) > 100 else str(value)
                                    st.write(f"  - `{key}`: {value_type} (미리보기: {preview})")
                                else:
                                    st.write(f"  - `{key}`: {value_type} = {value}")
                            
                            # 레이어 구조 확인
                            required_layers = {
                                "meta_layer": "필수",
                                "user_view_layer": "필수",
                                "system_view_layer": "선택",
                                "evaluation_layer": "선택"
                            }
                            
                            st.write("**레이어 구조 검증 결과:**")
                            missing_layers = []
                            present_layers = []
                            
                            for layer, required in required_layers.items():
                                if layer in corrected_data:
                                    present_layers.append(layer)
                                    layer_data = corrected_data[layer]
                                    if isinstance(layer_data, dict):
                                        layer_keys = list(layer_data.keys())
                                        st.write(f"  ✅ {layer} ({required}): 있음 - 키 {len(layer_keys)}개")
                                        if len(layer_keys) > 0:
                                            st.write(f"     키 목록: {layer_keys[:15]}")
                                    else:
                                        st.write(f"  ⚠️ {layer} ({required}): 있음 (하지만 딕셔너리가 아님: {type(layer_data).__name__})")
                                else:
                                    missing_layers.append(layer)
                                    st.write(f"  ❌ {layer} ({required}): 없음")
                            
                            # 원인 분석
                            st.write("**원인 분석:**")
                            if not present_layers:
                                st.error("  - 교정된 데이터에 레이어가 전혀 없습니다.")
                                st.write("  - 가능한 원인:")
                                st.write("    1. AI가 레이어 구조로 교정하지 않았을 수 있습니다.")
                                st.write("    2. JSON 파싱이 잘못되었을 수 있습니다.")
                                st.write("    3. AI 응답 형식이 예상과 다를 수 있습니다.")
                            elif len(present_layers) < 2:
                                st.warning(f"  - 필수 레이어가 부족합니다. (현재: {present_layers}, 필요: meta_layer, user_view_layer)")
                                st.write("  - 가능한 원인:")
                                st.write("    1. AI가 일부 레이어만 생성했을 수 있습니다.")
                                st.write("    2. JSON 파싱 중 일부 데이터가 손실되었을 수 있습니다.")
                            else:
                                st.info(f"  - 일부 레이어는 있지만 필수 레이어가 누락되었습니다.")
                            
                            # AI 응답 원본 확인
                            st.write("**AI 응답 원본 확인:**")
                            if "ai_response" in debug_info:
                                ai_response = debug_info.get("ai_response", "")
                                st.code(ai_response[:2000] + "..." if len(ai_response) > 2000 else ai_response)
                            
                            # 교정된 데이터 전체 확인
                            st.write("**교정된 데이터 전체:**")
                            st.json(corrected_data)
                        else:
                            st.error(f"❌ 교정된 데이터가 딕셔너리가 아닙니다: {type(corrected_data)}")
                            st.write(f"**데이터 값**: {str(corrected_data)[:500]}")
                    
                    # 요약
                    if isinstance(corrected_data, dict):
                        missing_layers = []
                        if "meta_layer" not in corrected_data:
                            missing_layers.append("meta_layer")
                        if "user_view_layer" not in corrected_data:
                            missing_layers.append("user_view_layer")
                        st.warning(f"⚠️ 교정된 데이터가 레이어 구조가 아닙니다. 누락된 레이어: {missing_layers}")
                        save_error = f"레이어 구조 불일치: 누락된 레이어 {missing_layers}"
                    else:
                        st.error(f"⚠️ 교정된 데이터가 딕셔너리가 아닙니다: {type(corrected_data)}")
                        save_error = f"데이터 타입 오류: {type(corrected_data)}"
                    save_success = False
                
                # 저장 정보를 디버깅 정보에 추가
                if "correction_debug_info" in st.session_state and st.session_state.correction_debug_info:
                    latest_debug = st.session_state.correction_debug_info[-1]
                    latest_debug["mapped_data"] = mapped_data
                    latest_debug["save_success"] = save_success
                    latest_debug["save_error"] = save_error
                    latest_debug["target_table"] = target_table
                
                if save_success:
                    # 저장 성공 시 question_status 테이블의 review_done 상태를 True로 업데이트
                    try:
                        update_success = st.session_state.db.update_question_status(
                            question_id=current_question["id"],
                            updates={"review_done": True}
                        )
                        if update_success:
                            progress["success"] += 1
                            progress["results"].append({
                                "question_id": current_question["id"],
                                "status": "success",
                                "message": f"교정 및 {target_table} 테이블 저장 완료, 상태 업데이트 완료"
                            })
                        else:
                            progress["success"] += 1
                            progress["results"].append({
                                "question_id": current_question["id"],
                                "status": "partial_success",
                                "message": f"교정 및 {target_table} 테이블 저장 완료, 상태 업데이트 실패"
                            })
                    except Exception as update_error:
                        progress["success"] += 1
                        progress["results"].append({
                            "question_id": current_question["id"],
                            "status": "partial_success",
                            "message": f"교정 및 {target_table} 테이블 저장 완료, 상태 업데이트 오류: {str(update_error)}"
                        })
                else:
                    progress["failed"] += 1
                    progress["results"].append({
                        "question_id": current_question["id"],
                        "status": "failed",
                        "message": f"{target_table} 테이블 저장 실패"
                    })
                
                # 완료 카운트 증가
                progress["completed"] += 1
                
                # 다음 문제 처리 또는 완료
                if progress["completed"] < progress["total"]:
                    st.rerun()  # 다음 문제 처리
                else:
                    # 모든 처리 완료
                    st.session_state.auto_review_batch_processing = False
                    st.rerun()
                    
            except Exception as e:
                progress["failed"] += 1
                progress["results"].append({
                    "question_id": current_question["id"],
                    "status": "error",
                    "message": f"처리 중 오류 발생: {str(e)}"
                })
                progress["completed"] += 1
                
                if progress["completed"] < progress["total"]:
                    st.rerun()  # 다음 문제 처리
                else:
                    st.session_state.auto_review_batch_processing = False
                    st.rerun()
    
    else:
        # 모든 처리 완료
        st.session_state.auto_review_batch_processing = False
        elapsed_time = datetime.now() - progress["start_time"]
        
        st.success(f"✅ 모든 문제 자동 처리 완료!")
        st.info(f"📊 처리 결과: 성공 {progress['success']}개, 실패 {progress['failed']}개")
        st.info(f"⏱️ 총 소요시간: {elapsed_time}")
        
        # 결과 상세 표시
        if progress["results"]:
            with st.expander("📋 처리 결과 상세"):
                for i, result in enumerate(progress["results"], 1):
                    status_emoji = {
                        "success": "✅",
                        "partial_success": "⚠️",
                        "failed": "❌",
                        "error": "💥"
                    }.get(result["status"], "❓")
                    
                    st.write(f"{i}. {status_emoji} {result['question_id']}: {result['message']}")
        
        # 초기화 버튼
        if st.button("🔄 새로 시작", key="auto_review_batch_reset_v3"):
            # 배치 처리 상태 초기화
            if "auto_review_batch_progress" in st.session_state:
                del st.session_state.auto_review_batch_progress
            if "auto_review_batch_processing" in st.session_state:
                del st.session_state.auto_review_batch_processing
            if "auto_review_questions" in st.session_state:
                del st.session_state.auto_review_questions
            st.rerun()