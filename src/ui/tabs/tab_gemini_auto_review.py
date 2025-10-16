"""
제미나이 자동 검토 탭
"""
import streamlit as st
import json
import re
from datetime import datetime
from src.constants import ASSESSMENT_AREAS, DEFAULT_DOMAIN
try:
    from src.services.gemini_client import GeminiClient
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    GeminiClient = None
from src.prompts.ai_review_template import DEFAULT_AI_REVIEW_PROMPT
# 탭 상태 관리 코드 제거

def render(st):
    st.header("🤖 제미나이 자동 검토")
    st.caption("qlearn_problems 테이블의 비활성 문제를 제미나이 API로 자동 검토하고 active 필드를 true로 업데이트합니다.")
    
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
            print("🔍 [DEBUG] 제미나이 API 키 감지 시작 (자동검토)")
            
            # 1순위: st.secrets 직접 접근
            try:
                api_key = st.secrets["GEMINI_API_KEY"]
                print(f"🔍 [DEBUG] st.secrets 직접 접근 성공: 길이={len(api_key) if api_key else 0}")
            except Exception as e:
                print(f"🔍 [DEBUG] st.secrets 직접 접근 실패: {e}")
                pass
            
            # 2순위: st.secrets.get() 방식
            if not api_key:
                try:
                    api_key = st.secrets.get("GEMINI_API_KEY")
                    print(f"🔍 [DEBUG] st.secrets.get() 성공: 길이={len(api_key) if api_key else 0}")
                except Exception as e:
                    print(f"🔍 [DEBUG] st.secrets.get() 실패: {e}")
                    pass
            
            # 3순위: 환경변수 fallback
            if not api_key:
                import os
                api_key = os.getenv("GEMINI_API_KEY")
                print(f"🔍 [DEBUG] 환경변수 접근: 길이={len(api_key) if api_key else 0}")
            
            # API 키가 존재하고 빈 문자열이 아닌지 확인
            print(f"🔍 [DEBUG] 최종 API 키 상태: {api_key is not None}, 길이={len(api_key) if api_key else 0}")
            if api_key and len(api_key.strip()) > 0:
                print("🔍 [DEBUG] API 키 유효성 검증 통과")
                gemini_client = GeminiClient()
                gemini_available = True
                print("🔍 [DEBUG] GeminiClient 초기화 성공")
            else:
                print("🔍 [DEBUG] API 키 유효성 검증 실패")
        except Exception as e:
            print(f"🔍 [DEBUG] 전체 예외 발생: {e}")
            gemini_available = False
    
    if not gemini_available:
        if not GEMINI_AVAILABLE:
            st.warning("⚠️ google-generativeai 패키지가 설치되지 않았습니다. 자동 검토 기능을 사용할 수 없습니다.")
        else:
            st.warning("⚠️ 제미나이 API 키가 설정되지 않았습니다. 자동 검토 기능을 사용할 수 없습니다.")
        return
    
    # 1단계: qlearn_problems 테이블에서 비활성 문제 가져오기
    st.markdown("### 1단계: qlearn_problems 테이블에서 비활성 문제 가져오기")
    st.info("💡 이 단계만 수동으로 수행합니다. 선택한 문제들은 자동으로 검토되어 활성화됩니다.")
    
    # 필터링 옵션
    col1, col2 = st.columns(2)
    
    with col1:
        # 평가 영역 필터
        area_options = [""] + list(ASSESSMENT_AREAS.keys())
        
        def format_area_display(x):
            if not x:
                return "전체"
            return x
        
        # 자동 검토가 실행 중일 때는 평가 영역 선택 비활성화
        disabled = st.session_state.get("gemini_auto_review_running", False)
        
        # 평가 영역 상태는 app.py에서 초기화됨
        
        # 현재 선택된 인덱스 계산 (안전한 방식)
        current_value = st.session_state.gemini_auto_review_selected_area
        try:
            current_index = area_options.index(current_value)
        except (ValueError, IndexError):
            # 세션 값이 옵션에 없으면 안전하게 첫 번째 옵션 사용
            current_index = 0
        
        # 평가 영역 선택 (탭 이동 방지를 위해 radio 사용)
        if len(area_options) <= 5:  # 옵션이 적을 때는 radio 사용
            selected_area = st.radio(
                "평가 영역",
                options=area_options,
                format_func=format_area_display,
                key="gemini_auto_review_area_filter_radio_v3",
                disabled=disabled,
                index=current_index,
                horizontal=True
            )
        else:  # 옵션이 많을 때는 selectbox 사용
            selected_area = st.selectbox(
                "평가 영역",
                options=area_options,
                format_func=format_area_display,
                key="gemini_auto_review_area_filter_selectbox_v3",
                disabled=disabled,
                index=current_index
            )
        
        # 선택된 값이 변경되었을 때만 세션 상태 업데이트
        if selected_area != st.session_state.gemini_auto_review_selected_area:
            st.session_state.gemini_auto_review_selected_area = selected_area
        
        if disabled:
            st.info("🔒 자동 검토가 실행 중입니다. 완료 후 다시 선택할 수 있습니다.")
    
    with col2:
        # 활성 상태 필터 (자동검토는 항상 비활성 문제만 처리)
        st.info("🔍 자동검토는 비활성 문제만 처리합니다")
        active_status = "비활성"  # 고정값으로 설정
    
    # 문제 가져오기 버튼
    if st.button("📋 문제 목록 가져오기", type="primary", key="gemini_auto_review_get_problems_v2", disabled=st.session_state.get("gemini_auto_review_running", False)):
        with st.spinner("문제 목록을 가져오는 중..."):
            try:
                # 필터 조건 구성
                filters = {}
                if selected_area:
                    # ASSESSMENT_AREAS 매핑을 통해 올바른 enum 값으로 변환
                    filters["category"] = ASSESSMENT_AREAS.get(selected_area, DEFAULT_DOMAIN)
                
                # 자동검토는 항상 비활성 문제만 처리 (active = False)
                filters["active"] = False
                
                # 디버깅: 필터 조건 출력
                st.info(f"🔍 필터 조건: {filters}")
                
                # 문제 조회
                problems = st.session_state.db.get_qlearn_problems(filters)
                
                if not problems:
                    st.warning("조건에 맞는 비활성 문제가 없습니다.")
                    st.info("💡 다른 평가 영역을 선택하거나 다른 조건으로 다시 시도해보세요.")
                else:
                    st.session_state.gemini_auto_review_problems = problems
                    st.success(f"✅ {len(problems)}개의 비활성 문제를 찾았습니다.")
                    
            except Exception as e:
                st.error(f"❌ 문제 목록 가져오기 실패: {str(e)}")
    
    # 2단계: 자동 검토 실행
    if "gemini_auto_review_problems" in st.session_state and st.session_state.gemini_auto_review_problems:
        st.markdown("### 2단계: 자동 검토 실행")
        
        problems = st.session_state.gemini_auto_review_problems
        st.info(f"📊 총 {len(problems)}개의 비활성 문제가 자동으로 검토됩니다.")
        
        # 처리 방식 선택
        st.markdown("#### 처리 방식 선택")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🚀 개별 자동 검토 시작", type="primary", key="gemini_auto_review_start_v3"):
                # 개별 자동 검토 시작 플래그 설정
                st.session_state.gemini_auto_review_running = True
                st.session_state.gemini_batch_processing = False
                # st.rerun() 제거 - 탭 이동 방지
        
        with col2:
            if st.button("⚡ 전체 배치 처리 시작", type="secondary", key="gemini_batch_processing_start_v3"):
                # 배치 처리 시작 플래그 설정
                st.session_state.gemini_batch_processing = True
                st.session_state.gemini_auto_review_running = False
                # st.rerun() 제거 - 탭 이동 방지
        
        # 배치 처리 실행
        if st.session_state.get("gemini_batch_processing", False):
            st.markdown("#### ⚡ 전체 배치 처리 진행 중...")
            batch_process_all_problems(st, problems, gemini_client)
            return
        
        # 개별 처리 진행 상황 표시 (setdefault로 '딱 한 번만' 실행)
        st.session_state.setdefault("gemini_auto_review_progress", {
            "total": len(problems),
            "completed": 0,
            "success": 0,
            "failed": 0,
            "results": []
        })
        
        progress = st.session_state.gemini_auto_review_progress
        
        # 진행률 표시
        if progress["completed"] < progress["total"]:
            progress_bar = st.progress(progress["completed"] / progress["total"])
            st.caption(f"진행률: {progress['completed']}/{progress['total']} (성공: {progress['success']}, 실패: {progress['failed']})")
        else:
            st.success(f"✅ 모든 문제 검토 완료! (성공: {progress['success']}, 실패: {progress['failed']})")
        
        # 자동 검토 실행 로직 (버튼 클릭 후 자동으로 실행)
        if st.session_state.get("gemini_auto_review_running", False) and progress["completed"] < progress["total"]:
            with st.spinner(f"자동 검토를 진행 중... ({progress['completed'] + 1}/{progress['total']})"):
                try:
                    # 현재 처리할 문제 선택
                    current_problem = problems[progress["completed"]]
                    current_index = progress["completed"]
                    
                    # 1. 제미나이로 문제 검토
                    review_content = f"""
문제 제목: {current_problem.get('title', '')}
주제: {current_problem.get('topic', '')}
난이도: {current_problem.get('difficulty', '')}
시나리오: {current_problem.get('scenario', '')}
목표: {current_problem.get('goal', [])}
과제: {current_problem.get('task', '')}
요구사항: {current_problem.get('requirements', [])}
제약사항: {current_problem.get('constraints', [])}
가이드: {current_problem.get('guide', {})}
평가 기준: {current_problem.get('evaluation', [])}
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
                        else:
                            print(f"❌ QLearn 검토 프롬프트 조회 실패 - None 반환")
                    except Exception as e:
                        print(f"❌ QLearn 검토 프롬프트 조회 예외: {e}")
                    
                    # 제미나이 API 호출
                    review_result = gemini_client.review_content(
                        system_prompt=system_prompt,
                        user_prompt=review_content
                    )
                    
                    # 검토 결과 처리
                    if not review_result or review_result.strip() == "":
                        st.error("❌ 검토 결과가 비어있습니다.")
                    elif review_result.startswith("❌"):
                        st.error(f"❌ 검토 중 오류 발생: {review_result}")
                    else:
                        st.success(f"문제 {current_index+1}: 제미나이 검토 완료")
                        st.info(f"🔍 검토 결과 길이: {len(review_result)} 문자")
                    
                    # 검토 결과에서 JSON 추출 시도
                    corrected_data = {}
                    try:
                        # 직접 JSON 파싱 시도
                        corrected_data = json.loads(review_result)
                    except json.JSONDecodeError:
                        # JSON 파싱 실패 시 텍스트에서 JSON 추출 시도
                        corrected_data = extract_json_from_text(review_result)
                    
                    # 2. qlearn_problems 테이블 업데이트 (active 필드 + 검토된 데이터)
                    problem_id = current_problem["id"]
                    update_data = {"active": True}
                    
                    # 검토된 데이터가 있으면 함께 업데이트
                    if corrected_data:
                        # qlearn_problems 테이블에 존재하지 않는 필드들 제거
                        invalid_fields = ['role']  # questions 테이블에만 있는 필드들
                        for field in invalid_fields:
                            if field in corrected_data:
                                print(f"⚠️ qlearn_problems 테이블에 존재하지 않는 필드 제거: {field}")
                                del corrected_data[field]
                        
                        update_data.update(corrected_data)
                        st.info(f"📝 검토된 데이터와 함께 업데이트: {list(corrected_data.keys())}")
                    else:
                        st.info("📝 active 필드만 업데이트")
                    
                    # time_limit 필드가 누락되거나 null인 경우 난이도에 따른 기본값 설정
                    if not update_data.get("time_limit") or update_data.get("time_limit") == "":
                        difficulty = current_problem.get("difficulty", "normal")
                        time_limit_defaults = {
                            "very easy": "3분 이내",
                            "easy": "4분 이내", 
                            "normal": "5분 이내",
                            "hard": "7분 이내",
                            "very hard": "10분 이내"
                        }
                        default_time_limit = time_limit_defaults.get(difficulty, "5분 이내")
                        update_data["time_limit"] = default_time_limit
                        st.info(f"⏰ time_limit 기본값 설정: {default_time_limit} (난이도: {difficulty})")
                    
                    update_success = st.session_state.db.update_qlearn_problem(problem_id, update_data)
                    
                    if update_success:
                        progress["success"] += 1
                        progress["results"].append({
                            "problem_id": problem_id,
                            "status": "success",
                            "message": "제미나이 검토 완료 및 문제 활성화 완료"
                        })
                    else:
                        progress["failed"] += 1
                        progress["results"].append({
                            "problem_id": problem_id,
                            "status": "failed",
                            "message": "문제 활성화 실패"
                        })
                    
                    # 진행률 업데이트
                    progress["completed"] += 1
                    
                    # 모든 문제 처리 완료 시 자동 검토 중지
                    if progress["completed"] >= progress["total"]:
                        st.session_state.gemini_auto_review_running = False
                        st.success("🎉 모든 자동 검토가 완료되었습니다!")
                    else:
                        # 다음 문제로 자동 진행을 위해 rerun 호출 (자동 검토 진행 중에만)
                        import time
                        time.sleep(1)  # 1초 대기 후 다음 문제 진행
                        st.rerun()  # 자동 검토 진행
                    
                except Exception as e:
                    progress["failed"] += 1
                    progress["results"].append({
                        "problem_id": current_problem.get("id", "unknown"),
                        "status": "error",
                        "message": f"검토 중 오류: {str(e)}"
                    })
                    progress["completed"] += 1
                    st.session_state.gemini_auto_review_running = False
                    st.error(f"❌ 자동 검토 중 오류 발생: {str(e)}")
        
        # 자동 검토 중지 버튼
        if st.session_state.get("gemini_auto_review_running", False):
            if st.button("⏹️ 자동 검토 중지", type="secondary", key="gemini_auto_review_stop_v3"):
                st.session_state.gemini_auto_review_running = False
                st.info("⏹️ 자동 검토가 중지되었습니다.")
                # st.rerun() 제거 - 탭 이동 방지
        
        # 결과 상세 보기
        if progress["results"]:
            st.markdown("### 3단계: 검토 결과")
            
            # 결과 요약
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("성공", progress["success"])
            with col2:
                st.metric("실패", progress["failed"])
            with col3:
                st.metric("진행률", f"{progress['completed']}/{progress['total']}")
            
            # 상세 결과 표시
            with st.expander("📋 상세 결과 보기"):
                for result in progress["results"]:
                    if result["status"] == "success":
                        st.success(f"✅ {result['problem_id']}: {result['message']}")
                    elif result["status"] == "partial_success":
                        st.warning(f"⚠️ {result['problem_id']}: {result['message']}")
                    else:
                        st.error(f"❌ {result['problem_id']}: {result['message']}")
        
        # 초기화 버튼
        if st.button("🔄 새로 시작", type="secondary", key="gemini_auto_review_reset_v3"):
            if "gemini_auto_review_problems" in st.session_state:
                del st.session_state.gemini_auto_review_problems
            if "gemini_auto_review_progress" in st.session_state:
                del st.session_state.gemini_auto_review_progress
            if "gemini_auto_review_running" in st.session_state:
                del st.session_state.gemini_auto_review_running
            if "gemini_auto_review_selected_area" in st.session_state:
                del st.session_state.gemini_auto_review_selected_area
            # st.rerun() 제거 - 탭 이동 방지
    
    # 사용 안내
    st.markdown("---")
    st.markdown("### ℹ️ 사용 안내")
    st.info("""
    **제미나이 자동 문제 검토 프로세스:**
    1. **1단계 (수동)**: qlearn_problems 테이블에서 비활성 문제 가져오기 및 필터링
    2. **2단계 (자동)**: 제미나이 검토 → 문제 활성화 (active=true)
    
    **지원 기능:**
    - qlearn_problems 테이블의 비활성 문제만 자동 검토 (중복 처리 방지)
    - 검토용 프롬프트 ID 사용 (9e55115e-0198-401d-8633-075bc8a25201)
    - 실시간 진행률 표시
    - 상세한 결과 로그
    - 검토된 문제는 자동으로 활성화 (active=true)
    
    **참고**: 
    - 검토된 문제는 자동으로 활성화되어 중복 처리를 방지합니다.
    - 수동 검토 탭과 동일한 검토 프로세스를 자동화한 버전입니다.
    """)

def batch_process_all_problems(st, problems, gemini_client):
    """모든 문제를 배치로 처리하는 함수"""
    
    # 배치 처리 상태 초기화 (setdefault로 '딱 한 번만' 실행)
    st.session_state.setdefault("batch_progress", {
        "total": len(problems),
        "completed": 0,
        "success": 0,
        "failed": 0,
        "results": [],
        "start_time": datetime.now()
    })
    
    progress = st.session_state.batch_progress
    
    # 진행률 표시
    if progress["completed"] < progress["total"]:
        progress_bar = st.progress(progress["completed"] / progress["total"])
        elapsed_time = datetime.now() - progress["start_time"]
        st.caption(f"진행률: {progress['completed']}/{progress['total']} (성공: {progress['success']}, 실패: {progress['failed']}) - 경과시간: {elapsed_time}")
        
        # 현재 처리 중인 문제 표시
        current_problem = problems[progress["completed"]]
        st.info(f"🔄 현재 처리 중: {current_problem.get('title', '제목 없음')[:100]}...")
        
        # 배치 처리 실행
        with st.spinner(f"배치 처리 중... ({progress['completed'] + 1}/{progress['total']})"):
            try:
                # 현재 처리할 문제
                current_problem = problems[progress["completed"]]
                current_index = progress["completed"]
                
                # 1. 제미나이로 문제 검토
                review_content = f"""
문제 제목: {current_problem.get('title', '')}
주제: {current_problem.get('topic', '')}
난이도: {current_problem.get('difficulty', '')}
시나리오: {current_problem.get('scenario', '')}
목표: {current_problem.get('goal', [])}
과제: {current_problem.get('task', '')}
요구사항: {current_problem.get('requirements', [])}
제약사항: {current_problem.get('constraints', [])}
가이드: {current_problem.get('guide', {})}
평가 기준: {current_problem.get('evaluation', [])}
"""
                
                # 프롬프트를 DB에서 가져오기
                system_prompt = DEFAULT_AI_REVIEW_PROMPT
                try:
                    # Supabase에서 프롬프트 조회 (QLearn 검토용 프롬프트 ID 사용)
                    db_prompt = st.session_state.db.get_prompt_by_id("9e55115e-0198-401d-8633-075bc8a25201")
                    if db_prompt:
                        system_prompt = db_prompt
                except Exception as e:
                    pass
                
                # 제미나이 API 호출
                review_result = gemini_client.review_content(
                    system_prompt=system_prompt,
                    user_prompt=review_content
                )
                
                # 검토 결과에서 JSON 추출 시도
                corrected_data = {}
                try:
                    # 직접 JSON 파싱 시도
                    corrected_data = json.loads(review_result)
                except json.JSONDecodeError:
                    # JSON 파싱 실패 시 텍스트에서 JSON 추출 시도
                    corrected_data = extract_json_from_text(review_result)
                
                # 2. qlearn_problems 테이블 업데이트 (active 필드 + 검토된 데이터)
                problem_id = current_problem["id"]
                update_data = {"active": True}
                
                # 검토된 데이터가 있으면 함께 업데이트
                if corrected_data:
                    # qlearn_problems 테이블에 존재하지 않는 필드들 제거
                    invalid_fields = ['role']  # questions 테이블에만 있는 필드들
                    for field in invalid_fields:
                        if field in corrected_data:
                            print(f"⚠️ qlearn_problems 테이블에 존재하지 않는 필드 제거: {field}")
                            del corrected_data[field]
                    
                    update_data.update(corrected_data)
                
                # time_limit 필드가 누락되거나 null인 경우 난이도에 따른 기본값 설정
                if not update_data.get("time_limit") or update_data.get("time_limit") == "":
                    difficulty = current_problem.get("difficulty", "normal")
                    time_limit_defaults = {
                        "very easy": "3분 이내",
                        "easy": "4분 이내", 
                        "normal": "5분 이내",
                        "hard": "7분 이내",
                        "very hard": "10분 이내"
                    }
                    default_time_limit = time_limit_defaults.get(difficulty, "5분 이내")
                    update_data["time_limit"] = default_time_limit
                
                update_success = st.session_state.db.update_qlearn_problem(problem_id, update_data)
                
                if update_success:
                    progress["success"] += 1
                    progress["results"].append({
                        "problem_id": problem_id,
                        "status": "success",
                        "message": "제미나이 검토 완료 및 문제 활성화 완료"
                    })
                else:
                    progress["failed"] += 1
                    progress["results"].append({
                        "problem_id": problem_id,
                        "status": "failed",
                        "message": "문제 활성화 실패"
                    })
                
                # 완료 카운트 증가
                progress["completed"] += 1
                
                # 다음 문제 처리 또는 완료
                if progress["completed"] < progress["total"]:
                    st.rerun()  # 탭 상태를 유지하면서 배치 처리 진행
                else:
                    # 모든 처리 완료
                    st.session_state.gemini_batch_processing = False
                    st.rerun()  # 탭 상태를 유지하면서 완료 상태 반영
                    
            except Exception as e:
                progress["failed"] += 1
                progress["results"].append({
                    "problem_id": current_problem["id"],
                    "status": "error",
                    "message": f"처리 중 오류 발생: {str(e)}"
                })
                progress["completed"] += 1
                
                if progress["completed"] < progress["total"]:
                    st.rerun()  # 탭 상태를 유지하면서 배치 처리 진행
                else:
                    st.session_state.gemini_batch_processing = False
                    st.rerun()  # 탭 상태를 유지하면서 완료 상태 반영
    
    else:
        # 모든 처리 완료
        st.session_state.gemini_batch_processing = False
        elapsed_time = datetime.now() - progress["start_time"]
        
        st.success(f"✅ 모든 문제 배치 처리 완료!")
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
                    
                    st.write(f"{i}. {status_emoji} {result['problem_id']}: {result['message']}")
        
        # 초기화 버튼
        if st.button("🔄 새로 시작", key="batch_reset_v3"):
            # 배치 처리 상태 초기화
            if "batch_progress" in st.session_state:
                del st.session_state.batch_progress
            if "gemini_batch_processing" in st.session_state:
                del st.session_state.gemini_batch_processing
            # st.rerun() 제거 - 탭 이동 방지

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
