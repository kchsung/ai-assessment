import os
import streamlit as st

from src.config import get_secret
from src.constants import ASSESSMENT_AREAS, ASSESSMENT_AREAS_DISPLAY, DIFFICULTY_LEVELS, QUESTION_TYPES
from src.services.edge_client import EdgeDBClient
from src.services.ai_generator import AIQuestionGenerator
from src.services.hitl import HITLManager

from src.ui.tabs.tab_create import render as render_create
from src.ui.tabs.tab_bank import render as render_bank
from src.ui.tab_feedback import render as render_feedback
from src.ui.tabs.tab_dashboard import render as render_dashboard
from src.ui.tabs.tab_settings import render as render_settings
from src.ui.tabs.tab_auto_generate import render as render_auto_generate


st.set_page_config(page_title="AI 활용능력평가 에이전트 v2.0", page_icon="🤖", layout="wide")

# 폰트 설정 및 헤더 크기 조정
st.markdown("""
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css');
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@100;200;300;400;500;600;700;800;900&display=swap');

/* 헤더 영역 크기 줄이기 */
.stApp > header {
    padding-top: 0.5rem !important;
    padding-bottom: 0.5rem !important;
}

/* 메인 타이틀 크기 줄이기 */
.stApp > header .stAppHeader {
    padding: 0.5rem 1rem !important;
}

/* 페이지 타이틀 크기 조정 */
h1 {
    font-size: 1.8rem !important;
    margin-bottom: 0.5rem !important;
    margin-top: 0.5rem !important;
}

/* 서브타이틀 크기 조정 */
.stApp > header p {
    font-size: 0.9rem !important;
    margin-bottom: 0.5rem !important;
}

/* 탭 메뉴 패딩 줄이기 */
.stTabs {
    margin-top: 0.5rem !important;
    margin-bottom: 0.5rem !important;
}

.stTabs [data-baseweb="tab-list"] {
    padding: 0.5rem 0 !important;
}

/* 전체 앱 폰트 설정 */
.stApp {
    font-family: 'Pretendard', 'Noto Sans KR', -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', 'Segoe UI', 'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol', sans-serif !important;
}

/* 제목 폰트 */
h1, h2, h3, h4, h5, h6 {
    font-family: 'Pretendard', 'Noto Sans KR', -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', 'Segoe UI', 'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', sans-serif !important;
    font-weight: 600 !important;
}

/* 본문 텍스트 */
p, div, span, label {
    font-family: 'Pretendard', 'Noto Sans KR', -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', 'Segoe UI', 'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', sans-serif !important;
}

/* 버튼 폰트 */
.stButton > button {
    font-family: 'Pretendard', 'Noto Sans KR', -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', 'Segoe UI', 'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', sans-serif !important;
    font-weight: 500 !important;
}

/* 입력 필드 폰트 */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div > select {
    font-family: 'Pretendard', 'Noto Sans KR', -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', 'Segoe UI', 'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', sans-serif !important;
}

/* 탭 폰트 */
.stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
    font-family: 'Pretendard', 'Noto Sans KR', -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', 'Segoe UI', 'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', sans-serif !important;
    font-weight: 500 !important;
}

/* 메트릭 폰트 */
[data-testid="metric-container"] {
    font-family: 'Pretendard', 'Noto Sans KR', -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', 'Segoe UI', 'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', sans-serif !important;
}

/* JSON 표시 폰트 */
.stJson {
    font-family: 'Pretendard', 'Noto Sans KR', -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', 'Segoe UI', 'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', monospace !important;
}
</style>
""", unsafe_allow_html=True)

# --- 세션 초기화 ---
def init_state():
    if "db" not in st.session_state:
        # Edge Function만 사용
        edge_url = get_secret("EDGE_FUNCTION_URL") or os.getenv("EDGE_FUNCTION_URL")
        edge_token = get_secret("EDGE_SHARED_TOKEN") or os.getenv("EDGE_SHARED_TOKEN")
        supabase_key = get_secret("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_ANON_KEY")
        
        if not edge_url or not edge_token:
            st.error("🚨 **Edge Function 설정이 필요합니다**")
            st.markdown("""
            Streamlit Cloud에서 앱을 실행하려면 다음 설정이 필요합니다:
            
            **Secrets 탭에서 설정해야 할 값들:**
            - `EDGE_FUNCTION_URL`: Supabase Edge Function URL
            - `EDGE_SHARED_TOKEN`: Edge Function 공유 토큰
            - `SUPABASE_ANON_KEY`: Supabase 익명 키
            - `OPENAI_API_KEY`: OpenAI API 키
            
            **설정 방법:**
            1. Streamlit Cloud 앱 페이지에서 "Manage app" 클릭
            2. "Secrets" 탭 선택
            3. 위의 키-값 쌍들을 추가
            4. 앱 재배포
            
            설정 후 앱을 새로고침하세요.
            """)
            st.stop()
        
        st.session_state.db = EdgeDBClient(
            base_url=edge_url,
            token=edge_token,
            supabase_anon=supabase_key,
        )
        print("✅ Edge Function 초기화 완료")

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


tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📝 문제 생성", "📚 문제 은행", "💬 피드백 & HITL", "📊 분석 대시보드", "🤖 문제 자동생성", "⚙️ 설정"])

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
    render_settings(st)
