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
st.caption("OpenAI API + Supabase Edge Function 기반")

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
