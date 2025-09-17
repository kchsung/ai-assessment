import streamlit as st
from src.constants import DIFFICULTY_LEVELS
from src.config import get_secret
import openai
import json

def render(st):
    # 헤더와 AI 검토 버튼을 같은 라인에 배치
    col_header, col_ai = st.columns([3, 1])
    
    with col_header:
        st.header("💬 피드백 & Human-in-the-Loop")
    
    with col_ai:
        st.markdown("<br>", unsafe_allow_html=True)  # 공간 맞춤
        if st.button("🤖 AI로 난이도 검토", use_container_width=True, type="secondary"):
            st.session_state.show_ai_review = True

    # 문제 선택 (통합된 인터페이스)
    all_q = st.session_state.db.get_questions()
    if not all_q:
        st.info("문제가 없습니다. 먼저 문제를 생성해주세요.")
        return
    
    # 문제 선택 옵션을 question_text로 표시
    question_options = {}
    for question in all_q:
        qt = question.get("question") or question.get("question_text","(없음)")
        display_text = f"{qt[:60]}{'...' if len(qt) > 60 else ''} [{question['id'][:8]}...]"
        question_options[display_text] = question
    
    selected_display = st.selectbox(
        "📋 피드백할 문제 선택", 
        options=list(question_options.keys()),
        help="문제를 선택하면 피드백을 입력하고 기존 피드백을 조회할 수 있습니다."
    )
    
    if selected_display:
        selected_question = question_options[selected_display]
        selected_id = selected_question["id"]
        
        # 선택된 문제 정보 표시
        qt = selected_question.get("question") or selected_question.get("question_text","(없음)")
        st.markdown(f"**선택된 문제**: {qt}")
        st.caption(f"문제 ID: {selected_id} | 영역: {selected_question.get('area', 'N/A')} | 난이도: {selected_question.get('difficulty', 'N/A')}")
        
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
                
                if submitted:
                    if comments.strip():  # 텍스트 입력이 있는 경우에만 저장
                        ok = st.session_state.db.save_feedback({
                            
                            "question_id": selected_id, 
                            "difficulty_rating": d,
                            "relevance_rating": r, 
                            "clarity_rating": c,
                            "actual_difficulty": actual, 
                            "comments": comments
                        })
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
            feedbacks = st.session_state.db.get_feedback(selected_id)
            
            if feedbacks:
                st.markdown(f"**📋 총 {len(feedbacks)}개의 피드백**")
                
                for idx, feedback in enumerate(feedbacks, 1):
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
        
        # 객관식 문제인 경우 선택지 추가
        if question.get("type") == "multiple_choice" and meta.get("steps"):
            problem_content += "**선택지**:\n"
            for step in meta["steps"]:
                if step.get("options"):
                    for opt in step["options"]:
                        problem_content += f"- {opt.get('id', '')}: {opt.get('text', '')}\n"
        
        # 주관식 문제인 경우 추가 정보
        elif question.get("type") == "subjective":
            if meta.get("scenario"):
                problem_content += f"**시나리오**: {meta['scenario']}\n"
            if meta.get("goal"):
                problem_content += f"**목표**: {', '.join(meta['goal'])}\n"
            if meta.get("task"):
                problem_content += f"**과제**: {meta['task']}\n"
        
        # AI 검토 프롬프트를 DB에서 가져오기
        try:
            # Supabase에서 프롬프트 조회
            system_prompt = st.session_state.db.get_prompt_by_id("d98893e6-db7b-47f4-8f66-1a33e326a5be")
            if not system_prompt:
                # DB에서 가져오지 못한 경우 기본 프롬프트 사용
                system_prompt = """[ROLE LOCK — 반드시 준수]
너는 "QLEARN 문제 평가 전문가"다.  
출제된 문제를 바탕으로 아래 세 가지 항목을 반드시 평가하고, 실제 사람이 의견을 말하는 것처럼 구체적으로 코멘트해라.  

───────────────────────────────

## 1. 난이도 평가 (Difficulty)
- 문제를 푸는 데 필요한 사고 수준을 판단하라.  
- 범위: "아주 쉬움 | 쉬움 | 보통 | 어려움 | 아주 어려움"  
- 왜 그렇게 평가했는지, 학습자 입장에서 어떤 점이 쉽거나 어려운지 근거를 제시하라.  

## 2. 관련성 평가 (Relevance)
- 문제가 실제 직무/맥락/시나리오와 얼마나 밀접하게 연결되는지 판단하라.  
- "높음 | 보통 | 낮음" 중 하나로 표시하고, 그 이유를 설명하라.  
- 불필요한 지식만 묻는 문제인지, 실제 상황에서 활용 가능한지 구분해라.  

## 3. 명확성 평가 (Clarity)
- 문제와 보기(선택지)가 혼동 없이 잘 이해되는지 평가하라.  
- "명확함 | 보통 | 모호함"으로 표시하고, 불명확하거나 애매한 부분이 있다면 지적하라.  

───────────────────────────────

## 4. 종합 의견 (Human-like Feedback)
- 마치 실제 사람이 동료에게 조언하듯 구체적으로 말하라.  
- 정답자의 관점(왜 이게 좋은 문제인가)과 오답자의 관점(왜 헷갈릴 수 있는가)을 모두 포함하라.  
- 학습자 입장에서 이 문제가 주는 학습 포인트나 개선 방향을 간단히 정리하라.  

───────────────────────────────

[출력 형식]
- 난이도 평가: (등급 + 근거)  
- 관련성 평가: (등급 + 근거)  
- 명확성 평가: (등급 + 근거)  
- 종합 의견: (자연스러운 문단 형식, 실제 사람의 심사평처럼 작성)"""
        except Exception as e:
            st.error(f"프롬프트 조회 실패: {e}")
            return f"❌ 프롬프트 조회 중 오류가 발생했습니다: {str(e)}"
        
        user_prompt = f"다음 문제를 검토해주세요:\n\n{problem_content}"
        
        # AI 호출
        response = client.chat.completions.create(
            model=st.session_state.get("selected_model", "gpt-5-nano"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"❌ AI 검토 중 오류가 발생했습니다: {str(e)}"
