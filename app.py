import os
import streamlit as st

from src.config import get_secret
from src.constants import ASSESSMENT_AREAS, DIFFICULTY_LEVELS, QUESTION_TYPES
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
            st.session_state.db = EdgeDBClient(
                base_url=os.getenv("EDGE_FUNCTION_URL"),
                token=get_secret("EDGE_SHARED_TOKEN", default=None),
                supabase_anon=get_secret("SUPABASE_ANON_KEY", default=None),
            )
        except Exception:
            st.session_state.db = LocalDBClient()

    if "generator" not in st.session_state:
        try:
            st.session_state.generator = AIQuestionGenerator()
        except RuntimeError as e:
            st.session_state.generator = None
            st.warning(f"AI 생성기 초기화 실패: {e}")

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
