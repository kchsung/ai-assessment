"""
자동 문제 검토 탭
"""
import streamlit as st
import json
import uuid
import re
from datetime import datetime
from src.constants import ASSESSMENT_AREAS, QUESTION_TYPES, VALID_DIFFICULTIES, DEFAULT_DIFFICULTY, DEFAULT_DOMAIN

def render(st):
    st.header("🤖 자동 문제 검토(JSON)")
    st.caption("subjective 타입 문제의 JSON 형식을 자동으로 검토하고 교정하여 qlearn_problems 테이블에 저장합니다.")
    
    # DB 연결 체크
    if st.session_state.db is None:
        st.error("데이터베이스 연결이 초기화되지 않았습니다.")
        return
    
    
    # 1단계: 문제 가져오기 및 필터링
    st.markdown("### 문제 가져오기 및 필터링")
    
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
            key="auto_review_area_filter_v2"
        )
    
    with col2:
        # 문제 유형 필터
        type_filter = st.selectbox(
            "문제 유형 필터", 
            options=["전체"] + list(QUESTION_TYPES.keys()),
            format_func=lambda x: "전체" if x == "전체" else x,
            key="auto_review_type_filter_v2"
        )
    
    # 필터 적용하여 문제 가져오기
    if st.button("🔍 문제 조회", type="primary", key="auto_review_search_v2"):
        filters = {}
        if area_filter != "전체":
            # 한국어 키를 영어 값으로 변환
            filters["category"] = ASSESSMENT_AREAS[area_filter]
        if type_filter != "전체":
            filters["type"] = type_filter
        
        # 검토 완료되지 않은 문제만 가져오기 (review_done이 FALSE인 문제들)
        filters["review_done"] = False  # FALSE 값으로 필터링
            
        questions = st.session_state.db.get_questions(filters)
        st.session_state.auto_review_questions = questions
        st.success(f"총 {len(questions)}개의 검토 대기 문제를 찾았습니다.")
        
        # 기존 선택된 문제 정보 초기화
        if "selected_auto_review_question" in st.session_state:
            del st.session_state.selected_auto_review_question
        if "mapped_auto_review_data" in st.session_state:
            del st.session_state.mapped_auto_review_data
    
    # 조회된 문제 표시 및 자동 처리
    if "auto_review_questions" in st.session_state and st.session_state.auto_review_questions:
        questions = st.session_state.auto_review_questions
        
        st.markdown("### 조회된 문제 목록")
        st.info(f"📊 총 {len(questions)}개의 문제가 조회되었습니다. 모든 문제를 자동으로 처리합니다.")
        
        # 조회된 문제 목록 표시
        with st.expander("조회된 문제 목록", expanded=True):
            for i, question in enumerate(questions, 1):
                question_text = question.get("question", "제목 없음")
                st.write(f"{i}. {question_text[:100]}{'...' if len(question_text) > 100 else ''}")
        
        # 자동 처리 시작 버튼
        if st.button("🚀 모든 문제 자동 처리 시작", type="primary", key="auto_review_batch_start_v2"):
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
    
    # 사용 안내
    st.markdown("---")
    st.markdown("### ℹ️ 사용 안내")
    st.info("""
    **자동 문제 검토 프로세스:**
    1. **1단계**: 문제 가져오기 및 필터링 - 미검토 문제만 지원
    2. **2단계**: 자동 데이터 매핑 - 모든 조회된 문제를 qlearn_problems 형식으로 자동 변환
    3. **3단계**: 자동 DB 저장 - 모든 매핑된 데이터를 자동으로 DB에 저장하고 원본 문제 검토상태 업데이트
    
    **참고**: 
    - 조회된 모든 문제가 자동으로 처리됩니다.
    - 처리된 원본 문제는 자동으로 검토완료 상태로 변경되어 중복 처리를 방지합니다.
    """)

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
    # 더 정확한 코드 블록 패턴 (```json으로 시작하고 ```로 끝나는 부분)
    code_block_pattern = r'```(?:json)?\s*\n?(\{.*?\})\s*\n?```'
    code_matches = re.findall(code_block_pattern, text, re.DOTALL)
    for match in code_matches:
        try:
            # 공백과 줄바꿈 정리
            cleaned_match = match.strip()
            return json.loads(cleaned_match)
        except json.JSONDecodeError:
            continue
    
    # 2-1. 더 간단한 코드 블록 패턴도 시도
    simple_code_pattern = r'```json\s*(\{.*?\})\s*```'
    simple_matches = re.findall(simple_code_pattern, text, re.DOTALL)
    for match in simple_matches:
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
    
    # 5. 중괄호 개수를 맞춰서 JSON 추출 시도
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
    
    # 6. 플레이스홀더가 있는 JSON 처리 (예: {time_limit})
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
                return json.loads(json_candidate)
            except json.JSONDecodeError:
                pass
    
    return {}

def ensure_array_format(data) -> list:
    """데이터를 올바른 배열 형식으로 변환 (JSONB 호환)"""
    if data is None:
        return []
    
    if isinstance(data, list):
        # 이미 배열인 경우, 각 요소를 그대로 유지 (이스케이프 방지)
        return [item for item in data if item is not None and str(item).strip()]
    
    if isinstance(data, str):
        # 문자열인 경우, JSON 파싱 시도 후 실패하면 단일 요소 배열로 변환
        try:
            parsed = json.loads(data)
            if isinstance(parsed, list):
                # 파싱된 배열의 각 요소를 그대로 유지
                return [item for item in parsed if item is not None and str(item).strip()]
            else:
                # 단일 값인 경우 그대로 반환
                return [parsed] if str(parsed).strip() else []
        except (json.JSONDecodeError, TypeError):
            # JSON 파싱 실패 시 원본 문자열을 그대로 반환
            return [data] if data.strip() else []
    
    # 기타 타입인 경우 그대로 단일 요소 배열로 반환
    return [data] if str(data).strip() else []

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
    mapped_data = {
        "id": problem_id,
        "lang": metadata.get("lang", "kr"),
        "category": metadata.get("category", question.get("category", "")),
        "topic": metadata.get("topic", ""),
        "difficulty": valid_difficulty,  # 변환된 difficulty 사용
        "time_limit": time_limit,
        "topic_summary": metadata.get("topic", ""),
        "title": question.get("question", metadata.get("topic", "")),
        "scenario": metadata.get("scenario", ""),
        "goal": ensure_array_format(metadata.get("goal", [])),
        "first_question": ensure_array_format(metadata.get("first_question", [])),
        "requirements": ensure_array_format(metadata.get("requirements", [])),
        "constraints": ensure_array_format(metadata.get("constraints", [])),
        "guide": metadata.get("guide", {}),
        "evaluation": ensure_array_format(metadata.get("evaluation", [])),
        "task": metadata.get("task", ""),
        # created_by 필드는 제외 (UUID 오류 방지)
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
        "reference": metadata.get("reference", {}),
        "active": False  # 기본값
    }
    
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
        st.info(f"🔄 현재 처리 중: {current_question.get('question', '제목 없음')[:100]}...")
        
        # 배치 처리 실행
        with st.spinner(f"자동 처리 중... ({progress['completed'] + 1}/{progress['total']})"):
            try:
                # 현재 처리할 문제
                current_question = questions[progress["completed"]]
                current_index = progress["completed"]
                
                # 1. 데이터 매핑 (qlearn_problems 형식으로 변환)
                mapped_data = map_question_to_qlearn_format(current_question)
                mapped_data["active"] = False
                
                # 2. qlearn_problems 테이블에 저장
                save_success = st.session_state.db.save_qlearn_problem(mapped_data)
                
                if save_success:
                    # 저장 성공 시 원본 문제의 review_done 상태를 True로 업데이트
                    try:
                        update_success = st.session_state.db.update_question_review_done(
                            question_id=current_question["id"], 
                            review_done=True
                        )
                        if update_success:
                            progress["success"] += 1
                            progress["results"].append({
                                "question_id": current_question["id"],
                                "status": "success",
                                "message": "매핑 및 qlearn_problems 테이블 저장 완료, 원본 문제 검토상태 업데이트 완료"
                            })
                        else:
                            progress["success"] += 1
                            progress["results"].append({
                                "question_id": current_question["id"],
                                "status": "partial_success",
                                "message": "매핑 및 qlearn_problems 테이블 저장 완료, 원본 문제 검토상태 업데이트 실패"
                            })
                    except Exception as update_error:
                        progress["success"] += 1
                        progress["results"].append({
                            "question_id": current_question["id"],
                            "status": "partial_success",
                            "message": f"매핑 및 qlearn_problems 테이블 저장 완료, 원본 문제 검토상태 업데이트 오류: {str(update_error)}"
                        })
                else:
                    progress["failed"] += 1
                    progress["results"].append({
                        "question_id": current_question["id"],
                        "status": "failed",
                        "message": "qlearn_problems 테이블 저장 실패"
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
        if st.button("🔄 새로 시작", key="auto_review_batch_reset_v2"):
            # 배치 처리 상태 초기화
            if "auto_review_batch_progress" in st.session_state:
                del st.session_state.auto_review_batch_progress
            if "auto_review_batch_processing" in st.session_state:
                del st.session_state.auto_review_batch_processing
            if "auto_review_questions" in st.session_state:
                del st.session_state.auto_review_questions
            st.rerun()