import os
import streamlit as st

from src.config import get_secret
from src.constants import ASSESSMENT_AREAS, ASSESSMENT_AREAS_DISPLAY, DIFFICULTY_LEVELS, QUESTION_TYPES
from src.services.edge_client import EdgeDBClient
from src.services.local_db import LocalDBClient
from src.services.ai_generator import AIQuestionGenerator
from src.services.hitl import HITLManager

from src.ui.tabs.tab_create import render as render_create
from src.ui.tabs.tab_bank import render as render_bank
from src.ui.tab_feedback import render as render_feedback
from src.ui.tabs.tab_dashboard import render as render_dashboard
from src.ui.tabs.tab_settings import render as render_settings


st.set_page_config(page_title="AI 활용능력평가 에이전트 v2.0", page_icon="🤖", layout="wide")

# --- 세션 초기화 ---
def init_state():
    if "db" not in st.session_state:
        # Edge 우선, 실패 시 Local fallback
        try:
            edge_url = get_secret("EDGE_FUNCTION_URL") or os.getenv("EDGE_FUNCTION_URL")
            edge_token = get_secret("EDGE_SHARED_TOKEN") or os.getenv("EDGE_SHARED_TOKEN")
            supabase_key = get_secret("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_ANON_KEY")
            
            if edge_url and edge_token:
                st.session_state.db = EdgeDBClient(
                    base_url=edge_url,
                    token=edge_token,
                    supabase_anon=supabase_key,
                )
            else:
                raise Exception("Edge Function 설정이 없습니다")
        except Exception as e:
            # Edge 실패 시 Local DB 사용
            st.session_state.db = LocalDBClient()

    if "generator" not in st.session_state:
        try:
            # API 키 확인
            api_key = get_secret("OPENAI_API_KEY")
            if not api_key:
                raise RuntimeError("OPENAI_API_KEY가 설정되지 않았습니다")
            st.session_state.generator = AIQuestionGenerator()
        except RuntimeError as e:
            st.session_state.generator = None
            # 경고 메시지는 설정 탭에서만 표시

    if "hitl" not in st.session_state:
        st.session_state.hitl = HITLManager(st.session_state.db)

init_state()

st.title("🤖 AI 활용능력평가 문제생성 에이전트 v2.0")
st.caption("QLearn 문제 출제 에이젼트-내부용")

# 상세보기 모달
if st.session_state.get("selected_question"):
    q = st.session_state.selected_question
    with st.container():
        st.markdown("---")
        st.markdown("### 📋 문제 상세보기")
        
        # 닫기 버튼
        if st.button("❌ 닫기", key="close_detail"):
            st.session_state.selected_question = None
            st.rerun()
        
        st.info(f"**문제 ID**: {q['id']}  \n**평가 영역**: {q['area']}  \n**난이도**: {q['difficulty']}  \n**유형**: {q['type']}")
        
        meta = q.get("metadata", {})
        
        # 객관식 문제 상세 표시
        if q.get("type") == "multiple_choice" and meta.get("steps"):
            st.markdown("### 📋 객관식 문제")
            steps = meta["steps"]
            
            # 스텝별 탭으로 표시
            if len(steps) > 1:
                step_tabs = st.tabs([f"Step {step['step']}" for step in steps])
                for i, step in enumerate(steps):
                    with step_tabs[i]:
                        st.markdown(f"**{step.get('title', '문제')}**")
                        st.markdown(step.get('question', ''))
                        
                        # 선택지 표시
                        if step.get('options'):
                            st.markdown("**선택지:**")
                            for opt in step['options']:
                                col_a, col_b = st.columns([1, 4])
                                with col_a:
                                    st.markdown(f"**{opt['id']}**")
                                with col_b:
                                    st.markdown(opt['text'])
                                    if opt.get('feedback'):
                                        st.caption(f"💡 {opt['feedback']}")
                        
                        # 정답 표시
                        if step.get('answer'):
                            with st.expander("정답 확인"):
                                st.success(f"정답: {step['answer']}")
            else:
                # 단일 스텝인 경우
                step = steps[0]
                st.markdown(f"**{step.get('title', '문제')}**")
                st.markdown(step.get('question', ''))
                
                # 선택지 표시
                if step.get('options'):
                    st.markdown("**선택지:**")
                    for opt in step['options']:
                        col_a, col_b = st.columns([1, 4])
                        with col_a:
                            st.markdown(f"**{opt['id']}**")
                        with col_b:
                            st.markdown(opt['text'])
                            if opt.get('feedback'):
                                st.caption(f"💡 {opt['feedback']}")
                
                # 정답 표시
                if step.get('answer'):
                    with st.expander("정답 확인"):
                        st.success(f"정답: {step['answer']}")
        
        # 주관식 문제 상세 표시
        elif q.get("type") == "subjective":
            st.markdown("### 📝 주관식 문제")
            
            # 시나리오를 마크다운으로 표시
            if meta.get("scenario"):
                st.markdown("**📖 문제 상황**")
                st.markdown(meta["scenario"])
            
            # 목표 표시
            if meta.get("goal"):
                st.markdown("**🎯 목표**")
                for goal in meta["goal"]:
                    st.markdown(f"- {goal}")
            
            # 과제 표시
            if meta.get("task"):
                st.markdown("**📋 과제**")
                st.markdown(meta["task"])
            
            # 첫 번째 질문들
            if meta.get("first_question"):
                st.markdown("**❓ 질문**")
                for question in meta["first_question"]:
                    st.markdown(f"- {question}")
            
            # 요구사항
            if meta.get("requirements"):
                st.markdown("**📌 요구사항**")
                for req in meta["requirements"]:
                    st.markdown(f"- {req}")
            
            # 제약사항
            if meta.get("constraints"):
                st.markdown("**⚠️ 제약사항**")
                for constraint in meta["constraints"]:
                    st.markdown(f"- {constraint}")
            
            # 평가 기준
            if meta.get("evaluation"):
                st.markdown("**📊 평가 기준**")
                for eval_criteria in meta["evaluation"]:
                    st.markdown(f"- {eval_criteria}")
        
        # 기존 방식으로 fallback
        else:
            st.markdown("### 문제")
            st.markdown(q.get("question","(없음)"))
            if meta.get("scenario"):
                st.markdown("### 상황 설명")
                st.markdown(meta["scenario"])
        
        st.markdown("---")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📝 문제 생성", "📚 문제 은행", "💬 피드백 & HITL", "📊 분석 대시보드", "⚙️ 설정"])

with tab1:
    render_create(st)
with tab2:
    render_bank(st)
with tab3:
    render_feedback(st)
with tab4:
    render_dashboard(st)
with tab5:
    render_settings(st)
