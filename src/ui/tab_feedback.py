import streamlit as st
from src.constants import DIFFICULTY_LEVELS
from src.config import get_secret
from src.prompts.ai_review_template import DEFAULT_AI_REVIEW_PROMPT
import openai
import json

def render(st):
    
    # DB 연결 체크
    if st.session_state.db is None:
        st.error("데이터베이스 연결이 초기화되지 않았습니다. Edge Function 설정을 확인하세요.")
        return
    
    # 문제 선택 (통합된 인터페이스)
    try:
        all_q = st.session_state.db.get_questions()
    except Exception as e:
        all_q = []
    
    # all_q가 리스트가 아닌 경우 빈 리스트로 초기화
    if not isinstance(all_q, list):
        all_q = []
    
    if not all_q:
        st.info("문제가 없습니다. 먼저 문제를 생성해주세요.")
        return
    
    # 문제 선택 옵션을 question_text로 표시
    question_options = {}
    for question in all_q:
        # question이 딕셔너리인지 확인
        if not isinstance(question, dict):
            continue
            
        qt = question.get("question") if isinstance(question, dict) else "(없음)"
        if not qt:
            qt = question.get("question_text", "(없음)") if isinstance(question, dict) else "(없음)"
        question_id = question.get("id", "unknown") if isinstance(question, dict) else "unknown"
        display_text = f"{qt[:60]}{'...' if len(qt) > 60 else ''} [{question_id[:8]}...]"
        question_options[display_text] = question
    
    # 문제 선택과 AI 검토 버튼을 같은 라인에 배치
    col_select, col_ai = st.columns([3, 1])
    
    with col_select:
        selected_display = st.selectbox(
            "📋 피드백할 문제 선택", 
            options=list(question_options.keys()),
            help="문제를 선택하면 피드백을 입력하고 기존 피드백을 조회할 수 있습니다."
        )
    
    with col_ai:
        st.markdown("<br>", unsafe_allow_html=True)  # 공간 맞춤
        if st.button("🤖 AI로 난이도 검토", use_container_width=True, type="secondary"):
            st.session_state.show_ai_review = True
    
    if selected_display:
        selected_question = question_options[selected_display]
        
        # selected_question이 딕셔너리인지 확인
        if not isinstance(selected_question, dict):
            st.error(f"선택된 문제 데이터가 유효하지 않습니다: {type(selected_question)}")
            return
            
        selected_id = selected_question.get("id", "unknown") if isinstance(selected_question, dict) else "unknown"
        
        # 선택된 문제 정보 표시
        qt = selected_question.get("question") if isinstance(selected_question, dict) else "(없음)"
        if not qt:
            qt = selected_question.get("question_text", "(없음)") if isinstance(selected_question, dict) else "(없음)"
        st.markdown(f"**선택된 문제**: {qt}")
        
        area = selected_question.get('area', 'N/A') if isinstance(selected_question, dict) else 'N/A'
        difficulty = selected_question.get('difficulty', 'N/A') if isinstance(selected_question, dict) else 'N/A'
        st.caption(f"문제 ID: {selected_id} | 영역: {area} | 난이도: {difficulty}")
        
        # 좌우 분할: 피드백 입력 vs 기존 피드백 조회
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("📝 새 피드백 입력")
            
            # 피드백 입력 폼
            with st.form("feedback_form"):
                st.markdown("**평가 항목**")
                col1_1, col1_2, col1_3 = st.columns(3)
                with col1_1:
                    d = st.slider("난이도 평가", 1, 5, 3, help="1: 매우 쉬움, 5: 매우 어려움")
                with col1_2:
                    r = st.slider("관련성 평가", 1, 5, 3, help="1: 관련성 낮음, 5: 관련성 높음")
                with col1_3:
                    c = st.slider("명확성 평가", 1, 5, 3, help="1: 불명확, 5: 매우 명확")
                
                actual = st.radio("실제 체감 난이도", options=list(DIFFICULTY_LEVELS.values()))
                
                # 텍스트 입력창
                comments = st.text_area(
                    "💬 피드백 내용", 
                    placeholder="문제에 대한 의견, 개선사항, 오류 발견 등을 자유롭게 작성해주세요...",
                    height=100
                )
                
                submitted = st.form_submit_button("💾 피드백 저장", type="primary")
                
                # 변수 정의 확인
                try:
                    local_vars = locals()
                    
                    # local_vars가 딕셔너리인지 확인
                    if isinstance(local_vars, dict):
                        pass
                    else:
                        # 기본값으로 변수들 초기화
                        d = 3
                        r = 3
                        c = 3
                        actual = "medium"
                        comments = ""
                        selected_id = "unknown"
                        
                except Exception as e:
                    # 기본값으로 변수들 초기화
                    d = 3
                    r = 3
                    c = 3
                    actual = "medium"
                    comments = ""
                    selected_id = "unknown"
                
                if submitted:
                    if comments.strip():  # 텍스트 입력이 있는 경우에만 저장
                        try:
                            # 변수 타입 확인 및 안전한 변환
                            try:
                                d = d
                            except Exception as e:
                                d = 3  # 기본값 설정
                            
                            try:
                                r = r
                            except Exception as e:
                                r = 3  # 기본값 설정
                            
                            try:
                                c = c
                            except Exception as e:
                                c = 3  # 기본값 설정
                            
                            try:
                                actual = actual
                            except Exception as e:
                                actual = "medium"  # 기본값 설정
                            
                            try:
                                selected_id = selected_id
                            except Exception as e:
                                selected_id = "unknown"  # 기본값 설정
                            
                            # 안전한 타입 변환
                            difficulty_rating = int(d) if isinstance(d, (int, str)) and str(d).isdigit() else 3
                            relevance_rating = int(r) if isinstance(r, (int, str)) and str(r).isdigit() else 3
                            clarity_rating = int(c) if isinstance(c, (int, str)) and str(c).isdigit() else 3
                            actual_difficulty = str(actual) if actual else "medium"
                            question_id = str(selected_id) if selected_id else "unknown"
                            
                            feedback_data = {
                                "question_id": question_id, 
                                "difficulty_rating": difficulty_rating,
                                "relevance_rating": relevance_rating, 
                                "clarity_rating": clarity_rating,
                                "actual_difficulty": actual_difficulty, 
                                "comments": str(comments)
                            }
                            ok = st.session_state.db.save_feedback(feedback_data)
                        except Exception as e:
                            st.error(f"피드백 저장 중 오류가 발생했습니다: {str(e)}")
                            ok = False
                        if ok:
                            st.success("✅ 피드백이 성공적으로 저장되었습니다!")
                            st.rerun()  # 페이지 새로고침하여 새 피드백 표시
                        else:
                            st.error("❌ 피드백 저장에 실패했습니다.")
                    else:
                        st.warning("⚠️ 피드백 내용을 입력해주세요.")

        with col2:
            st.subheader("📊 기존 피드백 조회")
            
            # 선택된 문제의 피드백 조회
            try:
                feedbacks = st.session_state.db.get_feedback(selected_id)
            except Exception as e:
                feedbacks = []
            
            # feedbacks가 리스트인지 확인
            if not isinstance(feedbacks, list):
                feedbacks = []
            
            if feedbacks:
                st.markdown(f"**📋 총 {len(feedbacks)}개의 피드백**")
                
                for idx, feedback in enumerate(feedbacks, 1):
                    # feedback이 딕셔너리인지 확인
                    if not isinstance(feedback, dict):
                        continue
                        
                    with st.expander(f"피드백 #{idx} - {feedback.get('created_at', '날짜 미상')}"):
                        col_f1, col_f2, col_f3 = st.columns(3)
                        with col_f1:
                            st.metric("난이도", f"{feedback.get('difficulty_rating', 0)}/5")
                        with col_f2:
                            st.metric("관련성", f"{feedback.get('relevance_rating', 0)}/5")
                        with col_f3:
                            st.metric("명확성", f"{feedback.get('clarity_rating', 0)}/5")
                        
                        st.markdown(f"**실제 체감 난이도**: {feedback.get('actual_difficulty', '미설정')}")
                        
                        if feedback.get('comments'):
                            st.markdown("**💬 피드백 내용**:")
                            st.markdown(feedback['comments'])
                        else:
                            st.markdown("*피드백 내용 없음*")
            else:
                st.info("이 문제에 대한 피드백이 아직 없습니다. 왼쪽에서 첫 번째 피드백을 작성해보세요!")
        
    # AI 검토 모달
    if st.session_state.get("show_ai_review"):
        if not selected_display:
            st.warning("⚠️ 먼저 검토할 문제를 선택해주세요.")
            st.session_state.show_ai_review = False
        else:
            # AI 검토 실행
            with st.spinner("🤖 AI가 문제를 검토하고 있습니다..."):
                ai_review = perform_ai_review(selected_question)
            
            # 검토 결과 모달 표시
            with st.container():
                st.markdown("---")
                st.markdown("### 🤖 AI 난이도 검토 결과")
                
                # 닫기 버튼
                if st.button("❌ 닫기", key="close_ai_review"):
                    st.session_state.show_ai_review = False
                    st.rerun()
                
                # 검토 결과 표시
                st.markdown(ai_review)
                
                st.markdown("---")

def perform_ai_review(question):
    """AI를 사용하여 문제를 검토하는 함수"""
    try:
        # OpenAI 클라이언트 초기화
        api_key = get_secret("OPENAI_API_KEY")
        if not api_key:
            return "❌ OpenAI API 키가 설정되지 않았습니다."
        
        client = openai.OpenAI(api_key=api_key)
        
        # 문제 정보 수집
        question_text = question.get("question") or question.get("question_text", "")
        meta = question.get("metadata", {})
        
        # 문제 내용 구성
        problem_content = f"""
**문제 ID**: {question.get('id', 'N/A')}
**평가 영역**: {question.get('area', 'N/A')}
**현재 난이도**: {question.get('difficulty', 'N/A')}
**문제 유형**: {question.get('type', 'N/A')}

**문제 내용**:
{question_text}

"""
        
        # Multiple choice problems: add options
        if question.get("type") == "multiple_choice" and meta.get("steps"):
            problem_content += "**선택지**:\n"
            for step in meta["steps"]:
                if step.get("options"):
                    for opt in step["options"]:
                        problem_content += f"- {opt.get('id', '')}: {opt.get('text', '')}\n"
        
        # Subjective problems: add additional info
        elif question.get("type") == "subjective":
            if meta.get("scenario"):
                problem_content += f"**시나리오**: {meta['scenario']}\n"
            if meta.get("goal"):
                problem_content += f"**목표**: {', '.join(meta['goal'])}\n"
            if meta.get("task"):
                problem_content += f"**과제**: {meta['task']}\n"
        
        # AI 검토 프롬프트를 DB에서 가져오기
        try:
            # Supabase에서 프롬프트 조회 (피드백용 프롬프트 ID 사용)
            system_prompt = st.session_state.db.get_prompt_by_id("d98893e6-db7b-47f4-8f66-1a33e326a5be")
            if not system_prompt:
                # DB에서 가져오지 못한 경우 기본 프롬프트 사용
                system_prompt = DEFAULT_AI_REVIEW_PROMPT
        except Exception as e:
            # 오류 발생 시 기본 프롬프트 사용
            system_prompt = DEFAULT_AI_REVIEW_PROMPT
        
        user_prompt = f"다음 문제를 검토해주세요:\n\n{problem_content}"
        
        # AI 호출
        response = client.chat.completions.create(
            model=st.session_state.get("selected_model", "gpt-5"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"❌ AI 검토 중 오류가 발생했습니다: {str(e)}"
