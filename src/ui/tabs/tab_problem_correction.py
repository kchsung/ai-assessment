"""
자동 문제 검토 탭
"""
import streamlit as st
import json
import uuid
from datetime import datetime
from src.services.problem_correction_service import ProblemCorrectionService
from src.constants import ASSESSMENT_AREAS_DISPLAY, ASSESSMENT_AREAS, QUESTION_TYPES

def render(st):
    st.header("🤖 자동 문제 검토")
    st.caption("subjective 타입 문제를 자동으로 검토하고 교정하여 qlearn_problems 테이블에 저장합니다.")
    
    # DB 연결 체크
    if st.session_state.db is None:
        st.error("데이터베이스 연결이 초기화되지 않았습니다.")
        return
    
    # 문제 교정 서비스 초기화
    correction_service = ProblemCorrectionService()
    
    if not correction_service.is_available():
        st.warning("⚠️ 제미나이 API를 사용할 수 없습니다. 자동 문제 검토 기능을 사용할 수 없습니다.")
        if hasattr(correction_service, 'initialization_error') and correction_service.initialization_error:
            with st.expander("오류 상세 정보"):
                st.error(correction_service.initialization_error)
        return
    
    # 1단계: 문제 가져오기 및 필터링 (수동)
    st.markdown("### 1단계: 문제 가져오기 및 필터링")
    st.info("💡 이 단계만 수동으로 수행합니다. 선택한 문제들은 자동으로 교정되어 저장됩니다.")
    
    # 필터링 옵션
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # 평가 영역 필터
        area_options = [""] + list(ASSESSMENT_AREAS_DISPLAY.keys())
        selected_area = st.selectbox(
            "평가 영역",
            options=area_options,
            format_func=lambda x: ASSESSMENT_AREAS_DISPLAY.get(x, "전체") if x else "전체",
            key="auto_review_area_filter"
        )
    
    with col2:
        # 난이도 필터
        try:
            # questions에서 난이도 목록 추출
            questions_result = st.session_state.db.get_questions({})
            
            # questions_result가 딕셔너리인지 리스트인지 확인
            if isinstance(questions_result, dict):
                questions = questions_result.get("questions", [])
            else:
                questions = questions_result if isinstance(questions_result, list) else []
            
            difficulties = set()
            for question in questions:
                if isinstance(question, dict) and "difficulty" in question:
                    difficulties.add(question["difficulty"])
            difficulty_options = [""] + sorted(list(difficulties))
        except Exception as e:
            # 기본 난이도 옵션 사용
            print(f"난이도 옵션 추출 중 오류: {e}")
            difficulty_options = ["", "very_easy", "easy", "medium", "hard", "very_hard"]
        
        selected_difficulty = st.selectbox(
            "난이도", 
            options=difficulty_options,
            key="auto_review_difficulty_filter"
        )
    
    with col3:
        # 검토 상태 필터 (review_done = False인 문제만)
        review_status = st.selectbox(
            "검토 상태",
            options=["미검토", "전체"],
            index=0,  # 기본값: 미검토
            key="auto_review_status_filter"
        )
    
    # 문제 가져오기 버튼
    if st.button("📋 문제 목록 가져오기", type="primary", key="auto_review_get_questions"):
        with st.spinner("문제 목록을 가져오는 중..."):
            try:
                # 필터 조건 구성
                filters = {}
                if selected_area:
                    filters["area"] = selected_area
                if selected_difficulty:
                    filters["difficulty"] = selected_difficulty
                if review_status == "미검토":
                    filters["review_done"] = False
                
                # subjective 타입만 필터링
                filters["type"] = "subjective"
                
                # 문제 조회
                questions_result = st.session_state.db.get_questions(filters)
                
                # questions_result가 딕셔너리인지 리스트인지 확인
                if isinstance(questions_result, dict):
                    questions = questions_result.get("questions", [])
                else:
                    questions = questions_result if isinstance(questions_result, list) else []
                
                if not questions:
                    st.warning("조건에 맞는 subjective 타입 문제가 없습니다.")
                else:
                    st.session_state.auto_review_questions = questions
                    st.success(f"✅ {len(questions)}개의 subjective 타입 문제를 찾았습니다.")
                    
            except Exception as e:
                st.error(f"❌ 문제 목록 가져오기 실패: {str(e)}")
    
    # 2단계: 자동 교정 실행
    if "auto_review_questions" in st.session_state and st.session_state.auto_review_questions:
        st.markdown("### 2단계: 자동 교정 실행")
        
        questions = st.session_state.auto_review_questions
        st.info(f"📊 총 {len(questions)}개의 subjective 타입 문제가 자동으로 교정됩니다.")
        
        # 진행 상황 표시
        if "auto_review_progress" not in st.session_state:
            st.session_state.auto_review_progress = {
                "total": len(questions),
                "completed": 0,
                "success": 0,
                "failed": 0,
                "results": []
            }
        
        progress = st.session_state.auto_review_progress
        
        # 진행률 표시
        if progress["completed"] < progress["total"]:
            progress_bar = st.progress(progress["completed"] / progress["total"])
            st.caption(f"진행률: {progress['completed']}/{progress['total']} (성공: {progress['success']}, 실패: {progress['failed']})")
        else:
            st.success(f"✅ 모든 문제 교정 완료! (성공: {progress['success']}, 실패: {progress['failed']})")
        
        # 자동 교정 시작 버튼
        if st.button("🚀 자동 교정 시작", type="primary", disabled=progress["completed"] >= progress["total"], key="auto_review_start_correction"):
            with st.spinner("자동 교정을 진행 중..."):
                try:
                    # 각 문제에 대해 자동 교정 수행
                    for i, question in enumerate(questions[progress["completed"]:], start=progress["completed"]):
                        try:
                            # 1. 데이터 매핑 (qlearn_problems 형식으로 변환)
                            mapped_data = map_question_to_qlearn_format(question)
                            
                            # 2. 제미나이로 문제 교정
                            question_json = json.dumps(question, ensure_ascii=False, indent=2)
                            corrected_result = correction_service.correct_problem(
                                problem_json=question_json,
                                category="learning_concept"  # 기본 카테고리 사용
                            )
                            
                            # 교정된 결과를 JSON으로 파싱
                            try:
                                corrected_data = json.loads(corrected_result)
                                # 교정된 데이터로 매핑된 데이터 업데이트
                                mapped_data.update(corrected_data)
                            except json.JSONDecodeError:
                                # JSON 파싱 실패 시 원본 데이터 사용
                                st.warning(f"문제 {i+1}: 교정 결과 JSON 파싱 실패, 원본 데이터 사용")
                            
                            # 3. qlearn_problems 테이블에 교정된 문제 저장
                            save_success = st.session_state.db.save_qlearn_problem(mapped_data)
                            
                            if save_success:
                                # 저장 후 실제로 DB에서 조회되는지 확인
                                try:
                                    saved_problem = st.session_state.db.get_qlearn_problems({"id": mapped_data["id"]})
                                    if saved_problem and len(saved_problem) > 0:
                                        progress["success"] += 1
                                        progress["results"].append({
                                            "question_id": question["id"],
                                            "status": "success",
                                            "message": "교정 및 qlearn_problems 테이블 저장 완료 (DB 확인됨)"
                                        })
                                    else:
                                        progress["failed"] += 1
                                        progress["results"].append({
                                            "question_id": question["id"],
                                            "status": "warning",
                                            "message": "저장 성공했지만 DB에서 조회되지 않음"
                                        })
                                except Exception as verify_error:
                                    progress["success"] += 1
                                    progress["results"].append({
                                        "question_id": question["id"],
                                        "status": "success",
                                        "message": f"교정 및 qlearn_problems 테이블 저장 완료 (검증 오류: {str(verify_error)})"
                                    })
                            else:
                                progress["failed"] += 1
                                progress["results"].append({
                                    "question_id": question["id"],
                                    "status": "failed",
                                    "message": "qlearn_problems 테이블 저장 실패"
                                })
                            
                        except Exception as e:
                            progress["failed"] += 1
                            progress["results"].append({
                                "question_id": question["id"],
                                "status": "error",
                                "message": f"교정 중 오류: {str(e)}"
                            })
                        
                        progress["completed"] += 1
                        
                        # 진행률 업데이트
                        progress_bar.progress(progress["completed"] / progress["total"])
                        st.caption(f"진행률: {progress['completed']}/{progress['total']} (성공: {progress['success']}, 실패: {progress['failed']})")
                        
                        # 실시간 업데이트를 위해 rerun
                        if progress["completed"] < progress["total"]:
                            st.rerun()
                    
                    st.success("🎉 모든 자동 교정이 완료되었습니다!")
                    
                except Exception as e:
                    st.error(f"❌ 자동 교정 중 오류 발생: {str(e)}")
        
        # 결과 상세 보기
        if progress["results"]:
            st.markdown("### 3단계: 교정 결과")
            
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
                        st.success(f"✅ {result['question_id']}: {result['message']}")
                    elif result["status"] == "partial_success":
                        st.warning(f"⚠️ {result['question_id']}: {result['message']}")
                    else:
                        st.error(f"❌ {result['question_id']}: {result['message']}")
        
        # 초기화 버튼
        if st.button("🔄 새로 시작", type="secondary", key="auto_review_reset"):
            if "auto_review_questions" in st.session_state:
                del st.session_state.auto_review_questions
            if "auto_review_progress" in st.session_state:
                del st.session_state.auto_review_progress
            st.rerun()
    
    # 사용 안내
    st.markdown("---")
    st.markdown("### ℹ️ 사용 안내")
    st.info("""
    **자동 문제 검토 프로세스:**
    1. **1단계 (수동)**: 문제 가져오기 및 필터링 - subjective 타입만 지원
    2. **2단계 (자동)**: 데이터 매핑 → 제미나이 교정 → questions 테이블에 교정된 문제 저장
    
    **지원 기능:**
    - subjective 타입 문제만 자동 교정
    - learning_concept 카테고리 프롬프트 사용
    - 실시간 진행률 표시
    - 상세한 결과 로그
    - 교정된 문제는 qlearn_problems 테이블에 저장
    
    **참고**: 교정된 문제는 qlearn_problems 테이블에 저장됩니다.
    """)

def map_question_to_qlearn_format(question: dict) -> dict:
    """questions 테이블 데이터를 qlearn_problems 형식으로 매핑"""
    
    # UUID 생성
    problem_id = str(uuid.uuid4())
    
    # 현재 시간
    now = datetime.now()
    
    # 메타데이터 추출
    metadata = question.get("metadata", {})
    
    # 매핑된 데이터 구성
    mapped_data = {
        "id": problem_id,
        "lang": metadata.get("lang", "kr"),
        "category": metadata.get("category", question.get("area", "")),
        "topic": metadata.get("topic", ""),
        "difficulty": question.get("difficulty", ""),
        "time_limit": metadata.get("time_limit", ""),
        "topic_summary": metadata.get("topic", ""),
        "title": metadata.get("topic", question.get("question", "")),
        "scenario": metadata.get("scenario", ""),
        "goal": metadata.get("goal", []),
        "first_question": metadata.get("first_question", []),
        "requirements": metadata.get("requirements", []),
        "constraints": metadata.get("constraints", []),
        "guide": metadata.get("guide", {}),
        "evaluation": metadata.get("evaluation", []),
        "task": metadata.get("task", ""),
        # created_by 필드는 제외 (UUID 오류 방지)
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
        "reference": metadata.get("reference", {}),
        "active": False  # 기본값
    }
    
    return mapped_data