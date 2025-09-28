"""
문제 검토 탭
"""
import streamlit as st
import uuid
from datetime import datetime
from src.constants import ASSESSMENT_AREAS_DISPLAY, ASSESSMENT_AREAS, QUESTION_TYPES
try:
    from src.services.gemini_client import GeminiClient
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    GeminiClient = None
from src.prompts.ai_review_template import DEFAULT_AI_REVIEW_PROMPT

def render(st):
    st.header("🔍 제미나이 문제 검토")
    st.caption("생성된 문제를 검토하고 qlearn_problems 테이블에 저장합니다.")
    
    # DB 연결 체크
    if st.session_state.db is None:
        st.error("데이터베이스 연결이 초기화되지 않았습니다.")
        return
    
    # 제미나이 API 연결 체크
    gemini_available = False
    gemini_client = None
    
    if GEMINI_AVAILABLE:
        try:
            # 환경 변수에서 직접 확인
            import os
            api_key = os.getenv("GEMINI_API_KEY")
            # print(f"DEBUG tab_review: GEMINI_API_KEY found: {bool(api_key)}")
            
            if api_key:
                gemini_client = GeminiClient()
                # print("DEBUG tab_review: GeminiClient 초기화 성공")
                gemini_available = True
            else:
                # print("DEBUG tab_review: GEMINI_API_KEY not found")
                pass
        except Exception as e:
            # print(f"DEBUG tab_review: GeminiClient 초기화 실패: {e}")
            gemini_available = False
    else:
        # print("DEBUG tab_review: GEMINI_AVAILABLE = False")
        pass
    
    if not gemini_available:
        if not GEMINI_AVAILABLE:
            st.warning("⚠️ google-generativeai 패키지가 설치되지 않았습니다. 내용 검토 기능을 사용할 수 없습니다.")
        else:
            st.warning("⚠️ 제미나이 API 키가 설정되지 않았습니다. 내용 검토 기능을 사용할 수 없습니다.")
    
    # 1단계: 문제 가져오기 및 필터링
    st.markdown("### 1단계: 문제 가져오기 및 필터링")
    
    # 필터링 옵션
    col1, col2 = st.columns(2)
    
    with col1:
        # 평가 영역 필터
        area_filter = st.selectbox(
            "평가 영역 필터",
            options=["전체"] + list(ASSESSMENT_AREAS_DISPLAY.keys()),
            format_func=lambda x: "전체" if x == "전체" else ASSESSMENT_AREAS_DISPLAY[x]
        )
    
    with col2:
        # 문제 유형 필터
        type_filter = st.selectbox(
            "문제 유형 필터", 
            options=["전체"] + list(QUESTION_TYPES.keys()),
            format_func=lambda x: "전체" if x == "전체" else QUESTION_TYPES[x]
        )
    
    # 필터 적용하여 문제 가져오기
    if st.button("🔍 문제 조회", type="primary"):
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
        if "gemini_review_result" in st.session_state:
            del st.session_state.gemini_review_result
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
            options=list(question_options.keys())
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
            if st.button("📋 매핑 데이터 확인", type="secondary"):
                st.session_state.mapped_review_data = mapped_data
                st.success("데이터 매핑이 완료되었습니다.")
        
    
    # 3단계: 제미나이 API 내용 검토
    if "mapped_review_data" in st.session_state and gemini_available:
        st.markdown("### 3단계: 제미나이 API 내용 검토")
        
        # 세션 상태 초기화 버튼 (디버깅용)
        if st.button("🔄 세션 상태 초기화 (디버깅)", type="secondary"):
            # 모든 관련 세션 상태 초기화
            keys_to_clear = [
                "gemini_review_result", "used_review_prompt", "prompt_source",
                "selected_review_question", "mapped_review_data"
            ]
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            st.success("세션 상태가 초기화되었습니다.")
            st.rerun()
        
        mapped_data = st.session_state.mapped_review_data
        
        if st.button("🤖 제미나이로 내용 검토", type="primary"):
            with st.spinner("제미나이 API로 내용을 검토 중..."):
                try:
                    # 검토할 내용 구성
                    review_content = f"""
문제 제목: {mapped_data.get('title', '')}
주제: {mapped_data.get('topic', '')}
난이도: {mapped_data.get('difficulty', '')}
시나리오: {mapped_data.get('scenario', '')}
목표: {mapped_data.get('goal', [])}
과제: {mapped_data.get('task', '')}
요구사항: {mapped_data.get('requirements', [])}
제약사항: {mapped_data.get('constraints', [])}
가이드: {mapped_data.get('guide', {})}
평가 기준: {mapped_data.get('evaluation', [])}
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
                    st.session_state.used_review_prompt = system_prompt
                    st.session_state.prompt_source = prompt_source
                    
                    # 제미나이 API 호출
                    review_result = gemini_client.review_content(
                        system_prompt=system_prompt,
                        user_prompt=review_content
                    )
                    
                    st.session_state.gemini_review_result = review_result
                    st.success("제미나이 API 검토가 완료되었습니다.")
                    
                except Exception as e:
                    st.error(f"제미나이 API 검토 실패: {str(e)}")
        
        # 검토 결과 표시
        if "gemini_review_result" in st.session_state:
            st.markdown("**제미나이 API 검토 결과**")
            
            # 응답 길이 정보 표시
            result_length = len(st.session_state.gemini_review_result)
            st.caption(f"응답 길이: {result_length} 문자")
            
            # 검토 내용 표시
            st.text_area("검토 내용", st.session_state.gemini_review_result, height=300)
            
            # 사용된 프롬프트 정보 표시
            if "used_review_prompt" in st.session_state and "prompt_source" in st.session_state:
                st.markdown("---")
                st.markdown("### 📋 사용된 프롬프트 정보")
                
                # 프롬프트 소스 정보
                st.info(f"**프롬프트 소스**: {st.session_state.prompt_source}")
                
                # 프롬프트 내용 표시
                with st.expander("🔍 사용된 프롬프트 전체 내용", expanded=False):
                    st.text_area(
                        "프롬프트 내용", 
                        st.session_state.used_review_prompt, 
                        height=400,
                        help="제미나이 API에 전달된 시스템 프롬프트의 전체 내용입니다."
                    )
                    st.caption(f"프롬프트 길이: {len(st.session_state.used_review_prompt)} 문자")
            
            # 원시 응답 정보 (디버깅용)
            with st.expander("🔍 응답 디버깅 정보"):
                st.code(f"응답 타입: {type(st.session_state.gemini_review_result)}")
                st.code(f"응답 길이: {result_length}")
                if result_length > 0:
                    st.code(f"첫 100자: {st.session_state.gemini_review_result[:100]}...")
                else:
                    st.warning("응답이 비어있습니다.")
    
    # 4단계: qlearn_problems 테이블에 저장
    if "mapped_review_data" in st.session_state:
        st.markdown("### 4단계: qlearn_problems 테이블에 저장")
        
        mapped_data = st.session_state.mapped_review_data
        
        # 검토 완료 여부 확인
        review_completed = "gemini_review_result" in st.session_state
        
        if review_completed:
            st.success("✅ 내용 검토가 완료되었습니다.")
        else:
            st.warning("⚠️ 내용 검토를 건너뛰고 저장하시겠습니까?")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("💾 qlearn_problems 저장", type="primary", disabled=not review_completed):
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
                        
                        # 4단계: questions 테이블의 review_done 상태 확인
                        st.info("📝 4단계: questions 테이블 review_done 상태 확인 중...")
                        try:
                            updated_questions = st.session_state.db.get_questions({"id": original_question_id})
                            if updated_questions and len(updated_questions) > 0:
                                review_done_status = updated_questions[0].get("review_done", False)
                                if review_done_status:
                                    st.success("✅ 4단계 완료: questions 테이블 review_done이 TRUE로 정상 업데이트됨")
                                else:
                                    st.warning("⚠️ 4단계 경고: questions 테이블 review_done이 여전히 FALSE입니다")
                            else:
                                st.warning("⚠️ 4단계 경고: questions 테이블에서 원본 문제를 찾을 수 없습니다")
                        except Exception as check_error:
                            st.warning(f"⚠️ 4단계 경고: questions 테이블 상태 확인 오류: {str(check_error)}")
                        
                        # 최종 성공 메시지
                        st.success("🎉 모든 저장 과정이 완료되었습니다!")
                        
                        # 세션 상태 정리
                        if "selected_review_question" in st.session_state:
                            del st.session_state.selected_review_question
                        if "mapped_review_data" in st.session_state:
                            del st.session_state.mapped_review_data
                        if "gemini_review_result" in st.session_state:
                            del st.session_state.gemini_review_result
                        if "used_review_prompt" in st.session_state:
                            del st.session_state.used_review_prompt
                        if "prompt_source" in st.session_state:
                            del st.session_state.prompt_source
                        
                        st.rerun()
                    else:
                        st.error("❌ 1단계 실패: qlearn_problems 테이블 저장에 실패했습니다.")
                        
                except Exception as e:
                    st.error(f"❌ 저장 중 오류가 발생했습니다: {str(e)}")
                    st.exception(e)  # 상세한 오류 정보 표시
        
        with col2:
            # 새로 시작 버튼
            if st.button("🔄 새로 시작", type="secondary"):
                # 세션 상태 정리
                if "selected_review_question" in st.session_state:
                    del st.session_state.selected_review_question
                if "mapped_review_data" in st.session_state:
                    del st.session_state.mapped_review_data
                if "gemini_review_result" in st.session_state:
                    del st.session_state.gemini_review_result
                if "used_review_prompt" in st.session_state:
                    del st.session_state.used_review_prompt
                if "prompt_source" in st.session_state:
                    del st.session_state.prompt_source
                st.rerun()

def map_question_to_qlearn_format(question: dict) -> dict:
    """questions 테이블 데이터를 qlearn_problems 형식으로 매핑"""
    
    # 현재 시간
    now = datetime.now()
    
    # 메타데이터 추출
    metadata = question.get("metadata", {})
    
    # category 필드에 들어갈 수 있는 유효한 값들
    # life, news, interview, learning_concept, pharma_distribution
    
    # category 값 매핑 (원본 값 -> 유효한 enum 값으로 변환)
    category_mapping = {
        "Pharma Distribution": "pharma_distribution",
        "pharma_distribution": "pharma_distribution",
        "pharma": "pharma_distribution",
        "Pharma": "pharma_distribution",
        "Distribution": "pharma_distribution",
        "Life": "life",
        "life": "life",
        "News": "news", 
        "news": "news",
        "Interview": "interview",
        "interview": "interview",
        "Learning Concept": "learning_concept",
        "learning_concept": "learning_concept",
        "Learning": "learning_concept",
        "Concept": "learning_concept",
        "": "life",  # 기본값
        None: "life"
    }
    
    # difficulty 값 매핑 (한국어 -> 올바른 enum 값으로 변환)
    difficulty_mapping = {
        "매우 쉬움": "very easy",
        "very easy": "very easy",
        "Very Easy": "very easy",
        "쉬움": "easy",
        "easy": "easy",
        "Easy": "easy",
        "보통": "normal",
        "normal": "normal",
        "Normal": "normal",
        "medium": "normal",  # medium도 normal로 매핑
        "Medium": "normal",
        "어려움": "hard",
        "hard": "hard",
        "Hard": "hard",
        "매우 어려움": "very hard",
        "very hard": "very hard",
        "Very Hard": "very hard",
        "very_hard": "very hard",  # 언더스코어 버전도 지원
        "": "normal",  # 기본값
        None: "normal"
    }
    
    original_area = metadata.get("category", question.get("area", ""))
    valid_category = category_mapping.get(original_area, "life")  # 기본값은 "life"
    
    original_difficulty = question.get("difficulty") or "보통"
    valid_difficulty = difficulty_mapping.get(original_difficulty, "normal")  # 기본값은 "normal"
    
    # 매핑된 데이터 구성 (모든 NOT NULL 필드에 기본값 제공)
    mapped_data = {
        "lang": "kr",  # 기본값으로 고정
        "category": valid_category,  # 유효한 category 값 사용
        "topic": metadata.get("topic") or "기본 주제",  # NOT NULL
        "difficulty": valid_difficulty,  # 유효한 difficulty enum 값 사용
        "time_limit": metadata.get("time_limit") or "5분",  # NOT NULL
        "topic_summary": metadata.get("topic") or "기본 주제 요약",  # NOT NULL
        "title": metadata.get("topic") or question.get("question") or "기본 제목",  # NOT NULL
        "scenario": metadata.get("scenario") or "기본 시나리오",  # NOT NULL
        "goal": metadata.get("goal") or [],  # NOT NULL (jsonb)
        "first_question": metadata.get("first_question") or [],  # NOT NULL (jsonb)
        "requirements": metadata.get("requirements") or [],  # NOT NULL (jsonb)
        "constraints": metadata.get("constraints") or [],  # NOT NULL (jsonb)
        "guide": metadata.get("guide") or {},  # NOT NULL (jsonb)
        "evaluation": metadata.get("evaluation") or [],  # NOT NULL (jsonb)
        "task": metadata.get("task") or "기본 과제",  # NOT NULL
        "active": False  # 기본값
    }
    
    # 선택적 필드들 추가
    if metadata.get("reference"):
        mapped_data["reference"] = metadata.get("reference")
    
    # 시간 필드는 항상 포함
    mapped_data["created_at"] = now.isoformat()
    mapped_data["updated_at"] = now.isoformat()
    
    # id나 created_by 필드가 있는 경우 제거
    if "id" in mapped_data:
        del mapped_data["id"]
    
    # created_by 필드가 빈 문자열이거나 None인 경우 제거
    if "created_by" in mapped_data:
        created_by_value = mapped_data["created_by"]
        if created_by_value is None or created_by_value == "" or created_by_value.strip() == "":
            del mapped_data["created_by"]
    
    # 빈 문자열이나 None 값들을 정리
    keys_to_remove = []
    for key, value in mapped_data.items():
        if value is None or (isinstance(value, str) and value.strip() == ""):
            keys_to_remove.append(key)
    
    for key in keys_to_remove:
        del mapped_data[key]
    
    return mapped_data
