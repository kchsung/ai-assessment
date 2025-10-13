import os
import streamlit as st
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 디버그 모드 (환경변수로 제어)
# os.environ["DEBUG"] = "true"  # 개발 시에만 주석 해제

from src.config import get_secret, is_streamlit_cloud
from src.constants import ASSESSMENT_AREAS, DIFFICULTY_LEVELS, QUESTION_TYPES
from src.services.edge_client import EdgeDBClient
from src.services.ai_generator import AIQuestionGenerator
from src.services.hitl import HITLManager

from src.ui.tabs.tab_overview import render as render_overview
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
# 탭 이름 정의
TAB_NAMES = ["📋 Overview", "📝 문제 생성", "🤖 문제 자동생성", "📚 문제 은행", "💬 피드백 & HITL", "📊 분석 대시보드", "🔍 문제 검토(JSON)", "🤖 자동 문제 검토", "🔍 제미나이 수동 검토", "🤖 제미나이 자동 검토", "⚙️ 설정"]


st.set_page_config(page_title="AI 활용능력평가 에이전트 v2.0", page_icon="🤖", layout="wide")

# CSS 스타일 로드
load_all_styles()

# --- 세션 초기화 (UI 출력 금지: 상태만 세팅) ---
def init_state():
    if "initialized" in st.session_state:
        return

    edge_url = get_secret("EDGE_FUNCTION_URL") or os.getenv("EDGE_FUNCTION_URL")
    edge_token = get_secret("EDGE_SHARED_TOKEN") or os.getenv("EDGE_SHARED_TOKEN")
    supabase_key = get_secret("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_ANON_KEY")

    # 디버그용 결과는 세션에 저장만 (UI로 직접 출력 X)
    st.session_state["_debug_info"] = {
        "EDGE_FUNCTION_URL": bool(edge_url),
        "EDGE_SHARED_TOKEN": bool(edge_token),
        "SUPABASE_ANON_KEY": bool(supabase_key),
        "is_cloud": is_streamlit_cloud(),
    }

    try:
        st.session_state.db = EdgeDBClient(base_url=edge_url, token=edge_token, supabase_anon=supabase_key) \
                             if (edge_url and edge_token) else None
        st.session_state["_edge_init_ok"] = st.session_state.db is not None
    except Exception:
        st.session_state.db = None
        st.session_state["_edge_init_ok"] = False

    try:
        api_key = get_secret("OPENAI_API_KEY")
        st.session_state.generator = AIQuestionGenerator() if api_key else None
    except Exception:
        st.session_state.generator = None

    st.session_state.hitl = HITLManager(st.session_state.db)

    # 기타 selectbox 방어용 상태
    st.session_state.setdefault("gemini_auto_review_selected_area", "")
    st.session_state.setdefault("gemini_auto_review_running", False)
    st.session_state.setdefault("auto_generate_running", False)
    st.session_state.setdefault("auto_generate_stop_requested", False)
    st.session_state.setdefault("auto_generated_questions", [])
    st.session_state.setdefault("auto_generate_total_count", 5)

    st.session_state["initialized"] = True

init_state()

# 상단 헤더는 항상 같은 컨테이너에 고정 렌더
header = st.container()
with header:
    st.title("🤖 AI 활용능력평가 문제생성 에이전트 v2.0")
    st.caption("QLearn 문제 출제 에이젼트-내부용")

# 디버그 정보는 프로덕션에서 숨김
# with st.sidebar:
#     if os.getenv("DEBUG") == "true":
#         st.markdown("### 🔍 디버그")
#         info = st.session_state.get("_debug_info", {})
#         st.write(
#             f"- EDGE_FUNCTION_URL: {'✅' if info.get('EDGE_FUNCTION_URL') else '❌'}\n"
#             f"- EDGE_SHARED_TOKEN: {'✅' if info.get('EDGE_SHARED_TOKEN') else '❌'}\n"
#             f"- SUPABASE_ANON_KEY: {'✅' if info.get('SUPABASE_ANON_KEY') else '❌'}\n"
#             f"- Streamlit Cloud: {'✅' if info.get('is_cloud') else '❌'}"
#         )
#         if st.session_state.get("_edge_init_ok") is False:
#             st.error("Edge Function 초기화 실패")
#         elif st.session_state.get("_edge_init_ok") is True:
#             st.success("Edge Function 초기화 완료")

# 이제 탭을 생성 (위쪽 레이아웃이 rerun에도 변하지 않음)
TAB_NAMES = ["📋 Overview", "📝 문제 생성", "🤖 문제 자동생성", "📚 문제 은행", "💬 피드백 & HITL", "📊 분석 대시보드",
             "🔍 문제 검토(JSON)", "🤖 자동 문제 검토",
             "🔍 제미나이 수동 검토", "🤖 제미나이 자동 검토", "⚙️ 설정"]
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11 = st.tabs(TAB_NAMES)

with tab1:  render_overview(st)
with tab2:  render_create(st)
with tab3:  render_auto_generate(st)
with tab4:  render_bank(st)
with tab5:  render_feedback(st)
with tab6:  render_dashboard(st)
with tab7:  render_review(st)
with tab8:  render_problem_correction(st)
with tab9:  render_gemini_manual_review(st)
with tab10: render_gemini_auto_review(st)
with tab11: render_settings(st)
