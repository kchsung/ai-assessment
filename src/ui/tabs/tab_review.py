"""
문제 검토 탭
"""
import streamlit as st
import json
import uuid
import re
from datetime import datetime
from src.constants import ASSESSMENT_AREAS, QUESTION_TYPES, VALID_DIFFICULTIES, DEFAULT_DIFFICULTY, DEFAULT_DOMAIN

def render(st):
    st.header("🔍 문제 검토(JSON)")
    st.caption("생성된 문제의 JSON 형식을 검토하고 qlearn_problems 테이블에 저장합니다. (3단계까지만 수행)")
    
    # DB 연결 체크
    if st.session_state.db is None:
        st.error("데이터베이스 연결이 초기화되지 않았습니다.")
        return
    
    # 제미나이 검토 기능은 별도 탭으로 이동됨
    st.info("💡 제미나이 검토 기능은 '제미나이 수동 검토' 탭으로 이동되었습니다.")
    
    # 1단계: 문제 가져오기 및 필터링
    st.markdown("### 1단계: 문제 가져오기 및 필터링")
    
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
            key="tab_review_area_filter_v2"
        )
    
    with col2:
        # 문제 유형 필터
        type_filter = st.selectbox(
            "문제 유형 필터", 
            options=["전체"] + list(QUESTION_TYPES.keys()),
            format_func=lambda x: "전체" if x == "전체" else x,
            key="tab_review_type_filter_v2"
        )
    
    # 필터 적용하여 문제 가져오기
    if st.button("🔍 문제 조회", type="primary", key="tab_review_search_v2"):
        filters = {}
        if area_filter != "전체":
            # 한국어 키를 영어 값으로 변환
            filters["category"] = ASSESSMENT_AREAS[area_filter]
        if type_filter != "전체":
            filters["type"] = type_filter
        
        # 검토 완료되지 않은 문제만 가져오기 (review_done이 FALSE인 문제들)
        filters["review_done"] = False  # FALSE 값으로 필터링
            
        # print(f"DEBUG: 필터링 조건 - category: {filters.get('category')}, type: {filters.get('type')}, review_done: {filters.get('review_done')}")
        questions = st.session_state.db.get_questions(filters)
        st.session_state.review_questions = questions
        st.success(f"총 {len(questions)}개의 검토 대기 문제를 찾았습니다.")
        
        # 기존 선택된 문제 정보 초기화
        if "selected_review_question" in st.session_state:
            del st.session_state.selected_review_question
        if "mapped_review_data" in st.session_state:
            del st.session_state.mapped_review_data
        if "used_review_prompt" in st.session_state:
            del st.session_state.used_review_prompt
        if "prompt_source" in st.session_state:
            del st.session_state.prompt_source
    
    # 조회된 문제 표시
    if "review_questions" in st.session_state and st.session_state.review_questions:
        questions = st.session_state.review_questions
        
        st.markdown("### 조회된 문제 목록")
        
        # 문제 선택
        question_options = {}
        for i, question in enumerate(questions):
            question_text = question.get("question", "제목 없음")
            display_text = f"{i+1}. {question_text[:50]}{'...' if len(question_text) > 50 else ''} [{question.get('area', 'N/A')}]"
            question_options[display_text] = question
        
        selected_display = st.selectbox(
            "검토할 문제 선택",
            options=list(question_options.keys()),
            key="tab_review_question_selector_v2"
        )
        
        if selected_display:
            selected_question = question_options[selected_display]
            st.session_state.selected_review_question = selected_question
            
            # 선택된 문제 상세 정보 표시
            with st.expander("선택된 문제 상세 정보", expanded=True):
                st.json(selected_question)
    
    # 2단계: 데이터 매핑
    if "selected_review_question" in st.session_state:
        st.markdown("### 2단계: 데이터 매핑")
        
        selected_question = st.session_state.selected_review_question
        
        # 매핑된 데이터 미리보기
        mapped_data = map_question_to_qlearn_format(selected_question)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**원본 데이터 (questions 테이블)**")
            st.json(selected_question)
        
        with col2:
            st.markdown("**매핑된 데이터 (qlearn_problems 형식)**")
            st.json(mapped_data)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📋 매핑 데이터 확인", type="secondary", key="tab_review_mapping_confirm_v2"):
                st.session_state.mapped_review_data = mapped_data
                st.success("데이터 매핑이 완료되었습니다.")
        
    
    # 3단계: qlearn_problems 테이블에 저장
    if "mapped_review_data" in st.session_state:
        st.markdown("### 3단계: qlearn_problems 테이블에 저장")
        
        mapped_data = st.session_state.mapped_review_data
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("💾 qlearn_problems 저장", type="primary", key="tab_review_save_v2"):
                try:
                    # 선택된 문제 정보 확인
                    selected_question = st.session_state.get("selected_review_question")
                    if not selected_question or not selected_question.get("id"):
                        st.error("선택된 문제 정보가 없습니다.")
                        return
                    
                    # 매핑된 데이터를 다시 생성 (캐시 문제 방지)
                    fresh_mapped_data = map_question_to_qlearn_format(selected_question)
                    fresh_mapped_data["active"] = False
                    
                    original_question_id = selected_question.get("id")
                    st.info(f"🔍 저장 시작 - 원본 문제 ID: {original_question_id}, 새 ID는 Supabase에서 자동 생성됩니다")
                    
                    # 1단계: qlearn_problems 테이블에 저장
                    st.info("📝 1단계: qlearn_problems 테이블에 저장 중...")
                    success = st.session_state.db.save_qlearn_problem(fresh_mapped_data)
                    
                    if success:
                        st.success("✅ 1단계 완료: qlearn_problems 테이블 저장 성공")
                        
                        # 2단계: questions 테이블의 review_done 필드 업데이트
                        st.info("📝 2단계: questions 테이블의 review_done 필드 업데이트 중...")
                        st.info(f"업데이트할 question_id: {original_question_id}")
                        try:
                            review_update_success = st.session_state.db.update_question_review_done(original_question_id, True)
                            if review_update_success:
                                st.success("✅ 2단계 완료: questions 테이블 review_done 업데이트 성공")
                            else:
                                st.warning("⚠️ 2단계 경고: questions 테이블 review_done 업데이트 실패")
                        except Exception as review_error:
                            st.warning(f"⚠️ 2단계 경고: questions 테이블 review_done 업데이트 오류: {str(review_error)}")
                            st.exception(review_error)
                        
                        # 3단계: 저장 후 실제로 DB에서 조회되는지 확인
                        st.info("📝 3단계: 저장 검증 중...")
                        try:
                            # 최근 저장된 데이터 조회
                            saved_problems = st.session_state.db.get_qlearn_problems({})
                            if saved_problems and len(saved_problems) > 0:
                                latest_problem = saved_problems[0]
                                st.success("✅ 3단계 완료: qlearn_problems 테이블에서 저장된 데이터 확인됨")
                                st.info(f"📊 생성된 ID: {latest_problem.get('id', 'N/A')[:8]}...")
                            else:
                                st.warning("⚠️ 3단계 경고: 저장 성공했지만 DB에서 조회되지 않습니다. Edge Function을 확인해주세요.")
                        except Exception as verify_error:
                            st.warning(f"⚠️ 3단계 경고: 저장 검증 오류: {str(verify_error)}")
                        
                        # 최종 성공 메시지
                        st.success("🎉 모든 저장 과정이 완료되었습니다!")
                        
                        # 세션 상태 정리
                        if "selected_review_question" in st.session_state:
                            del st.session_state.selected_review_question
                        if "mapped_review_data" in st.session_state:
                            del st.session_state.mapped_review_data
                        
                        st.rerun()
                    else:
                        st.error("❌ 1단계 실패: qlearn_problems 테이블 저장에 실패했습니다.")
                        
                except Exception as e:
                    st.error(f"❌ 저장 중 오류가 발생했습니다: {str(e)}")
                    st.exception(e)  # 상세한 오류 정보 표시
        
        with col2:
            # 새로 시작 버튼
            if st.button("🔄 새로 시작", type="secondary", key="tab_review_restart_v2"):
                # 세션 상태 정리
                if "selected_review_question" in st.session_state:
                    del st.session_state.selected_review_question
                if "mapped_review_data" in st.session_state:
                    del st.session_state.mapped_review_data
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
