"""
제미나이 수동 검토 탭
"""
import streamlit as st
import json
import re
from src.constants import ASSESSMENT_AREAS
try:
    from src.services.gemini_client import GeminiClient
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    GeminiClient = None
from src.prompts.ai_review_template import DEFAULT_AI_REVIEW_PROMPT

def render(st):
    st.header("🔍 제미나이 수동 검토")
    st.caption("qlearn_problems 테이블의 문제를 제미나이 API로 수동 검토하고 active 필드를 true로 업데이트합니다.")
    
    # DB 연결 체크
    if st.session_state.db is None:
        st.error("데이터베이스 연결이 초기화되지 않았습니다.")
        return
    
    # 제미나이 API 연결 체크
    gemini_available = False
    gemini_client = None
    
    if GEMINI_AVAILABLE:
        try:
            # Streamlit Cloud에서는 st.secrets 사용, 로컬에서는 환경변수 사용
            api_key = None
            
            # 1순위: st.secrets 직접 접근
            try:
                api_key = st.secrets["GEMINI_API_KEY"]
            except:
                pass
            
            # 2순위: st.secrets.get() 방식
            if not api_key:
                try:
                    api_key = st.secrets.get("GEMINI_API_KEY")
                except:
                    pass
            
            # 3순위: 환경변수 fallback
            if not api_key:
                import os
                api_key = os.getenv("GEMINI_API_KEY")
            
            # API 키가 존재하고 빈 문자열이 아닌지 확인
            if api_key and len(api_key.strip()) > 0:
                gemini_client = GeminiClient()
                gemini_available = True
        except Exception as e:
            gemini_available = False
    
    if not gemini_available:
        if not GEMINI_AVAILABLE:
            st.warning("⚠️ google-generativeai 패키지가 설치되지 않았습니다. 내용 검토 기능을 사용할 수 없습니다.")
        else:
            st.warning("⚠️ 제미나이 API 키가 설정되지 않았습니다. 내용 검토 기능을 사용할 수 없습니다.")
            
    
    # 1단계: qlearn_problems 테이블에서 문제 가져오기
    st.markdown("### 1단계: qlearn_problems 테이블에서 문제 가져오기")
    
    # 필터링 옵션
    col1, col2 = st.columns(2)
    
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
            key="gemini_manual_review_area_filter_v2"
        )
    
    with col2:
        # active 상태 필터
        active_filter = st.selectbox(
            "활성 상태 필터", 
            options=["전체", "비활성", "활성"],
            key="gemini_manual_review_active_filter_v2"
        )
    
    # 필터 적용하여 문제 가져오기
    if st.button("🔍 문제 조회", type="primary", key="gemini_manual_review_search_v2"):
        filters = {}
        if area_filter != "전체":
            # 한국어 키를 영어 값으로 변환
            filters["category"] = ASSESSMENT_AREAS[area_filter]
        
        # active 상태 필터 적용
        if active_filter == "비활성":
            filters["active"] = False
        elif active_filter == "활성":
            filters["active"] = True
            
        problems = st.session_state.db.get_qlearn_problems(filters)
        st.session_state.gemini_manual_review_problems = problems
        st.success(f"총 {len(problems)}개의 문제를 찾았습니다.")
        
        # 기존 선택된 문제 정보 초기화
        if "selected_gemini_manual_review_problem" in st.session_state:
            del st.session_state.selected_gemini_manual_review_problem
        if "gemini_manual_review_result" in st.session_state:
            del st.session_state.gemini_manual_review_result
        if "used_gemini_manual_review_prompt" in st.session_state:
            del st.session_state.used_gemini_manual_review_prompt
        if "gemini_manual_review_prompt_source" in st.session_state:
            del st.session_state.gemini_manual_review_prompt_source
    
    # 조회된 문제 표시
    if "gemini_manual_review_problems" in st.session_state and st.session_state.gemini_manual_review_problems:
        problems = st.session_state.gemini_manual_review_problems
        
        st.markdown("### 조회된 문제 목록")
        
        # 문제 선택
        problem_options = {}
        for i, problem in enumerate(problems):
            title = problem.get("title", "제목 없음")
            active_status = "활성" if problem.get("active", False) else "비활성"
            display_text = f"{i+1}. {title[:50]}{'...' if len(title) > 50 else ''} [{problem.get('category', 'N/A')}] [{active_status}]"
            problem_options[display_text] = problem
        
        selected_display = st.selectbox(
            "검토할 문제 선택",
            options=list(problem_options.keys()),
            key="gemini_manual_review_problem_selector_v2"
        )
        
        if selected_display:
            selected_problem = problem_options[selected_display]
            st.session_state.selected_gemini_manual_review_problem = selected_problem
            
            # 선택된 문제 상세 정보 표시
            with st.expander("선택된 문제 상세 정보", expanded=True):
                st.json(selected_problem)
    
    # 2단계: 제미나이 API 내용 검토
    if "selected_gemini_manual_review_problem" in st.session_state and gemini_available:
        st.markdown("### 2단계: 제미나이 API 내용 검토")
        
        # 세션 상태 초기화 버튼 (디버깅용)
        if st.button("🔄 세션 상태 초기화 (디버깅)", type="secondary", key="gemini_manual_review_session_reset_v2"):
            # 모든 관련 세션 상태 초기화
            keys_to_clear = [
                "gemini_manual_review_result", "gemini_manual_review_corrected_data", 
                "used_gemini_manual_review_prompt", "gemini_manual_review_prompt_source",
                "selected_gemini_manual_review_problem"
            ]
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            st.success("세션 상태가 초기화되었습니다.")
            st.rerun()
        
        selected_problem = st.session_state.selected_gemini_manual_review_problem
        
        if st.button("🤖 제미나이로 내용 검토", type="primary", key="gemini_manual_review_gemini_v2"):
            with st.spinner("제미나이 API로 내용을 검토 중..."):
                try:
                    # 검토할 내용 구성
                    review_content = f"""
문제 제목: {selected_problem.get('title', '')}
역할: {selected_problem.get('role', '')}
난이도: {selected_problem.get('difficulty', '')}
시나리오: {selected_problem.get('scenario', '')}
목표: {selected_problem.get('goal', [])}
과제: {selected_problem.get('task', '')}
요구사항: {selected_problem.get('requirements', [])}
제약사항: {selected_problem.get('constraints', [])}
가이드: {selected_problem.get('guide', {})}
평가 기준: {selected_problem.get('evaluation', [])}
"""
                    
                    # 프롬프트를 DB에서 가져오기
                    system_prompt = DEFAULT_AI_REVIEW_PROMPT
                    prompt_source = "기본 프롬프트"
                    try:
                        # Supabase에서 프롬프트 조회 (QLearn 검토용 프롬프트 ID 사용)
                        print(f"🔍 QLearn 검토용 프롬프트 ID 조회: 9e55115e-0198-401d-8633-075bc8a25201")
                        db_prompt = st.session_state.db.get_prompt_by_id("9e55115e-0198-401d-8633-075bc8a25201")
                        if db_prompt:
                            system_prompt = db_prompt
                            prompt_source = "데이터베이스 프롬프트 (ID: 9e55115e-0198-401d-8633-075bc8a25201)"
                            print(f"✅ QLearn 검토 프롬프트 조회 성공: {len(db_prompt)} 문자")
                            st.info("📋 데이터베이스에서 QLearn 검토 프롬프트를 가져왔습니다.")
                        else:
                            print(f"❌ QLearn 검토 프롬프트 조회 실패 - None 반환")
                            st.info("📝 기본 검토 프롬프트를 사용합니다.")
                    except Exception as e:
                        print(f"❌ QLearn 검토 프롬프트 조회 예외: {e}")
                        st.warning(f"프롬프트 조회 실패: {e}. 기본 프롬프트를 사용합니다.")
                    
                    # 사용된 프롬프트 정보 저장
                    st.session_state.used_gemini_manual_review_prompt = system_prompt
                    st.session_state.gemini_manual_review_prompt_source = prompt_source
                    
                    # 제미나이 API 호출
                    review_result = gemini_client.review_content(
                        system_prompt=system_prompt,
                        user_prompt=review_content
                    )
                    
                    st.session_state.gemini_manual_review_result = review_result
                    st.success("제미나이 API 검토가 완료되었습니다.")
                    
                    # 검토 결과에서 JSON 추출 시도
                    corrected_data = {}
                    try:
                        # 직접 JSON 파싱 시도
                        corrected_data = json.loads(review_result)
                    except json.JSONDecodeError:
                        # JSON 파싱 실패 시 텍스트에서 JSON 추출 시도
                        corrected_data = extract_json_from_text(review_result)
                    
                    # 검토된 데이터 저장
                    if corrected_data:
                        st.session_state.gemini_manual_review_corrected_data = corrected_data
                    
                except Exception as e:
                    st.error(f"제미나이 API 검토 실패: {str(e)}")
        
        # 검토 결과 표시
        if "gemini_manual_review_result" in st.session_state:
            st.markdown("**제미나이 API 검토 결과**")
            
            # 응답 길이 정보 표시
            result_length = len(st.session_state.gemini_manual_review_result)
            st.caption(f"응답 길이: {result_length} 문자")
            
            # 검토 내용 표시
            st.text_area("검토 내용", st.session_state.gemini_manual_review_result, height=300)
            
            # JSON 비교 기능
            if "gemini_manual_review_corrected_data" in st.session_state:
                st.markdown("---")
                st.markdown("### 🔍 검토 전후 JSON 비교")
                
                original_data = st.session_state.selected_gemini_manual_review_problem
                corrected_data = st.session_state.gemini_manual_review_corrected_data
                
                # 두 컬럼으로 나누어 비교 표시
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**📋 원본 문제 데이터**")
                    st.json(original_data)
                
                with col2:
                    st.markdown("**✨ 제미나이 검토 후 데이터**")
                    st.json(corrected_data)
                
                # 변경사항 하이라이트
                st.markdown("#### 🔄 주요 변경사항")
                changes_found = False
                
                # 주요 필드들 비교
                key_fields = ['title', 'role', 'difficulty', 'scenario', 'goal', 'task', 'requirements', 'constraints', 'guide', 'evaluation']
                
                for field in key_fields:
                    original_value = original_data.get(field, "")
                    corrected_value = corrected_data.get(field, "")
                    
                    if original_value != corrected_value:
                        changes_found = True
                        st.markdown(f"**{field}**:")
                        st.markdown(f"- **원본**: `{str(original_value)[:100]}{'...' if len(str(original_value)) > 100 else ''}`")
                        st.markdown(f"- **수정**: `{str(corrected_value)[:100]}{'...' if len(str(corrected_value)) > 100 else ''}`")
                        st.markdown("---")
                
                if not changes_found:
                    st.info("🔍 검토 결과에서 주요 변경사항이 발견되지 않았습니다.")
                
                # 업데이트할 최종 데이터 미리보기
                st.markdown("#### 📝 업데이트될 최종 데이터")
                final_data = original_data.copy()
                final_data.update(corrected_data)
                final_data["active"] = True  # 활성화 상태로 설정
                
                with st.expander("🔍 최종 업데이트 데이터 미리보기", expanded=False):
                    st.json(final_data)
            
            # 사용된 프롬프트 정보 표시
            if "used_gemini_manual_review_prompt" in st.session_state and "gemini_manual_review_prompt_source" in st.session_state:
                st.markdown("---")
                st.markdown("### 📋 사용된 프롬프트 정보")
                
                # 프롬프트 소스 정보
                st.info(f"**프롬프트 소스**: {st.session_state.gemini_manual_review_prompt_source}")
                
                # 프롬프트 내용 표시
                with st.expander("🔍 사용된 프롬프트 전체 내용", expanded=False):
                    st.text_area(
                        "프롬프트 내용", 
                        st.session_state.used_gemini_manual_review_prompt, 
                        height=400,
                        help="제미나이 API에 전달된 시스템 프롬프트의 전체 내용입니다."
                    )
                    st.caption(f"프롬프트 길이: {len(st.session_state.used_gemini_manual_review_prompt)} 문자")
            
            # 원시 응답 정보 (디버깅용)
            with st.expander("🔍 응답 디버깅 정보"):
                st.code(f"응답 타입: {type(st.session_state.gemini_manual_review_result)}")
                st.code(f"응답 길이: {result_length}")
                if result_length > 0:
                    st.code(f"첫 100자: {st.session_state.gemini_manual_review_result[:100]}...")
                else:
                    st.warning("응답이 비어있습니다.")
    
    # 3단계: 문제 업데이트 (active 필드 true로 변경)
    if "selected_gemini_manual_review_problem" in st.session_state:
        st.markdown("### 3단계: 문제 업데이트 (active 필드 true로 변경)")
        
        selected_problem = st.session_state.selected_gemini_manual_review_problem
        
        # 검토 완료 여부 확인
        review_completed = "gemini_manual_review_result" in st.session_state
        
        if review_completed:
            st.success("✅ 내용 검토가 완료되었습니다.")
        else:
            st.warning("⚠️ 내용 검토를 건너뛰고 업데이트하시겠습니까?")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✅ 문제 활성화 (active=true)", type="primary", disabled=not review_completed, key="gemini_manual_review_activate_v2"):
                try:
                    # 선택된 문제 정보 확인
                    if not selected_problem or not selected_problem.get("id"):
                        st.error("선택된 문제 정보가 없습니다.")
                        return
                    
                    problem_id = selected_problem.get("id")
                    st.info(f"🔍 문제 활성화 시작 - 문제 ID: {problem_id}")
                    
                    # 업데이트할 데이터 준비
                    update_data = {"active": True}
                    
                    # 검토된 데이터가 있으면 함께 업데이트
                    if "gemini_manual_review_corrected_data" in st.session_state:
                        corrected_data = st.session_state.gemini_manual_review_corrected_data
                        update_data.update(corrected_data)
                        st.info(f"📝 검토된 데이터와 함께 업데이트: {list(corrected_data.keys())}")
                    else:
                        st.info("📝 active 필드만 업데이트")
                    
                    # qlearn_problems 테이블 업데이트
                    st.info("📝 qlearn_problems 테이블 업데이트 중...")
                    success = st.session_state.db.update_qlearn_problem(problem_id, update_data)
                    
                    if success:
                        st.success("✅ 문제가 성공적으로 활성화되었습니다!")
                        
                        # 업데이트 후 실제로 DB에서 조회되는지 확인
                        st.info("📝 업데이트 검증 중...")
                        try:
                            # 업데이트된 문제 조회
                            updated_problems = st.session_state.db.get_qlearn_problems({"id": problem_id})
                            if updated_problems and len(updated_problems) > 0:
                                updated_problem = updated_problems[0]
                                active_status = updated_problem.get("active", False)
                                if active_status:
                                    st.success("✅ 검증 완료: 문제가 정상적으로 활성화되었습니다")
                                    
                                    # 검토된 데이터가 반영되었는지 확인
                                    if "gemini_manual_review_corrected_data" in st.session_state:
                                        st.info("🔍 검토된 데이터 반영 확인 중...")
                                        corrected_data = st.session_state.gemini_manual_review_corrected_data
                                        data_updated = True
                                        for key, value in corrected_data.items():
                                            if updated_problem.get(key) != value:
                                                st.warning(f"⚠️ {key} 필드가 예상과 다르게 업데이트되었습니다")
                                                data_updated = False
                                        
                                        if data_updated:
                                            st.success("✅ 검토된 데이터가 정상적으로 반영되었습니다")
                                else:
                                    st.warning("⚠️ 경고: 문제가 여전히 비활성 상태입니다")
                            else:
                                st.warning("⚠️ 경고: 업데이트된 문제를 DB에서 찾을 수 없습니다")
                        except Exception as verify_error:
                            st.warning(f"⚠️ 검증 오류: {str(verify_error)}")
                        
                        # 세션 상태 정리
                        if "selected_gemini_manual_review_problem" in st.session_state:
                            del st.session_state.selected_gemini_manual_review_problem
                        if "gemini_manual_review_result" in st.session_state:
                            del st.session_state.gemini_manual_review_result
                        if "gemini_manual_review_corrected_data" in st.session_state:
                            del st.session_state.gemini_manual_review_corrected_data
                        if "used_gemini_manual_review_prompt" in st.session_state:
                            del st.session_state.used_gemini_manual_review_prompt
                        if "gemini_manual_review_prompt_source" in st.session_state:
                            del st.session_state.gemini_manual_review_prompt_source
                        
                        st.rerun()
                    else:
                        st.error("❌ 문제 활성화에 실패했습니다.")
                        
                except Exception as e:
                    st.error(f"❌ 업데이트 중 오류가 발생했습니다: {str(e)}")
                    st.exception(e)  # 상세한 오류 정보 표시
        
        with col2:
            # 새로 시작 버튼
            if st.button("🔄 새로 시작", type="secondary", key="gemini_manual_review_restart_v2"):
                # 세션 상태 정리
                if "selected_gemini_manual_review_problem" in st.session_state:
                    del st.session_state.selected_gemini_manual_review_problem
                if "gemini_manual_review_result" in st.session_state:
                    del st.session_state.gemini_manual_review_result
                if "gemini_manual_review_corrected_data" in st.session_state:
                    del st.session_state.gemini_manual_review_corrected_data
                if "used_gemini_manual_review_prompt" in st.session_state:
                    del st.session_state.used_gemini_manual_review_prompt
                if "gemini_manual_review_prompt_source" in st.session_state:
                    del st.session_state.gemini_manual_review_prompt_source
                st.rerun()

def extract_json_from_text(text: str) -> dict:
    """
    텍스트에서 JSON 부분을 추출합니다.
    """
    if not text:
        return {}
    
    # 1. 먼저 전체 텍스트가 JSON인지 확인
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass
    
    # 2. 코드 블록(```json ... ```) 내부의 JSON 추출
    code_block_pattern = r'```(?:json)?\s*\n?(\{.*?\})\s*\n?```'
    code_matches = re.findall(code_block_pattern, text, re.DOTALL)
    for match in code_matches:
        try:
            cleaned_match = match.strip()
            return json.loads(cleaned_match)
        except json.JSONDecodeError:
            continue
    
    # 3. 첫 번째 중괄호부터 마지막 중괄호까지 추출
    first_brace = text.find('{')
    last_brace = text.rfind('}')
    
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        json_candidate = text[first_brace:last_brace + 1]
        try:
            return json.loads(json_candidate)
        except json.JSONDecodeError:
            pass
    
    # 4. 여러 JSON 객체가 있는 경우 가장 긴 것 선택
    json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
    matches = re.findall(json_pattern, text, re.DOTALL)
    
    longest_match = ""
    for match in matches:
        if len(match) > len(longest_match):
            longest_match = match
    
    if longest_match:
        try:
            return json.loads(longest_match)
        except json.JSONDecodeError:
            pass
    
    return {}
