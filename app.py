import os
import streamlit as st
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

from src.config import get_secret, is_streamlit_cloud
from src.constants import ASSESSMENT_AREAS, DIFFICULTY_LEVELS, QUESTION_TYPES
from src.services.edge_client import EdgeDBClient
from src.services.ai_generator import AIQuestionGenerator
from src.services.hitl import HITLManager

from src.ui.tabs.tab_create import render as render_create
from src.ui.tabs.tab_bank import render as render_bank
from src.ui.tab_feedback import render as render_feedback
from src.ui.tabs.tab_dashboard import render as render_dashboard
from src.ui.tabs.tab_settings import render as render_settings
from src.ui.tabs.tab_auto_generate import render as render_auto_generate
from src.ui.tabs.tab_review import render as render_review
from src.ui.tabs.tab_problem_correction import render as render_problem_correction
from src.ui.tabs.tab_gemini_manual_review import render as render_gemini_manual_review
from src.ui.tabs.tab_gemini_auto_review import render as render_gemini_auto_review
from src.ui.styles.css_loader import load_all_styles


st.set_page_config(page_title="AI 활용능력평가 에이전트 v2.0", page_icon="🤖", layout="wide")

# CSS 스타일 로드
load_all_styles()

# --- 세션 초기화 ---
def init_state():
    if "db" not in st.session_state:
        # Edge Function만 사용
        edge_url = get_secret("EDGE_FUNCTION_URL") or os.getenv("EDGE_FUNCTION_URL")
        edge_token = get_secret("EDGE_SHARED_TOKEN") or os.getenv("EDGE_SHARED_TOKEN")
        supabase_key = get_secret("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_ANON_KEY")
        
        # 디버깅 정보 표시 (개발 환경에서만)
        if os.getenv("DEBUG") == "true":
            st.write("🔍 **디버깅 정보:**")
            st.write(f"- EDGE_FUNCTION_URL: {'✅ 설정됨' if edge_url else '❌ 누락'}")
            st.write(f"- EDGE_SHARED_TOKEN: {'✅ 설정됨' if edge_token else '❌ 누락'}")
            st.write(f"- SUPABASE_ANON_KEY: {'✅ 설정됨' if supabase_key else '❌ 누락'}")
            st.write(f"- Streamlit Cloud 환경: {'✅ Cloud' if is_streamlit_cloud() else '❌ 로컬'}")
        
        if not edge_url or not edge_token:
            st.warning("⚠️ Edge Function 설정이 필요합니다")
            st.info("**Streamlit Cloud Secrets 설정 방법:**")
            st.code("""
EDGE_FUNCTION_URL = "https://your-project.supabase.co/functions/v1/your-function"
EDGE_SHARED_TOKEN = "your_shared_token_here"
SUPABASE_ANON_KEY = "your_supabase_anon_key_here"
            """)
            st.session_state.db = None
            return
        
        try:
            st.session_state.db = EdgeDBClient(
                base_url=edge_url,
                token=edge_token,
                supabase_anon=supabase_key,
            )
            st.success("✅ Edge Function 초기화 완료")
        except Exception as e:
            st.error(f"❌ Edge Function 초기화 실패: {str(e)}")
            st.error("**가능한 원인:**")
            st.write("1. Edge Function URL이 올바르지 않음")
            st.write("2. Edge Function Token이 유효하지 않음")
            st.write("3. Supabase 프로젝트가 활성화되지 않음")
            st.write("4. 네트워크 연결 문제")
            st.session_state.db = None
            return

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


tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs(["📝 문제 생성", "📚 문제 은행", "💬 피드백 & HITL", "📊 분석 대시보드", "🤖 문제 자동생성", "🔍 문제 검토(JSON)", "🤖 자동 문제 검토", "🔍 제미나이 수동 검토", "🤖 제미나이 자동 검토", "⚙️ 설정"])

with tab1:
    render_create(st)
with tab2:
    render_bank(st)
with tab3:
    render_feedback(st)
with tab4:
    render_dashboard(st)
with tab5:
    render_auto_generate(st)
with tab6:
    render_review(st)
with tab7:
    render_problem_correction(st)
with tab8:
    render_gemini_manual_review(st)
with tab9:
    render_gemini_auto_review(st)
with tab10:
    render_settings(st)
