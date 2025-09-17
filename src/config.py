import os
import streamlit as st

# .env 로드 (로컬에서만)
try:
    from dotenv import load_dotenv
    load_dotenv(override=False)
except Exception:
    pass

def get_secret(name: str, default=None) -> str | None:
    """
    환경 변수/시크릿을 안전하게 가져오는 함수
    우선순위: st.secrets > 환경변수 > 기본값
    """
    # 1) st.secrets (Streamlit Cloud/로컬 secrets.toml)
    try:
        if hasattr(st, 'secrets') and st.secrets:
            # secrets.toml에서 직접 접근 시도
            if name in st.secrets:
                val = st.secrets[name]
                if val and val != "your_openai_api_key_here" and val.strip() != "":
                    return val
            # default 섹션에서 접근 시도
            if hasattr(st.secrets, 'default') and hasattr(st.secrets.default, name):
                val = getattr(st.secrets.default, name)
                if val and val != "your_openai_api_key_here" and val.strip() != "":
                    return val
    except Exception as e:
        # 디버깅용
        print(f"st.secrets 접근 오류 ({name}): {e}")
        pass
    
    # 2) 환경변수 (로컬 .env 또는 시스템 환경변수)
    val = os.getenv(name)
    if val and val.strip() != "":
        return val
    
    # 3) 기본값
    return default

def is_streamlit_cloud() -> bool:
    """Streamlit Cloud에서 실행 중인지 확인"""
    try:
        # Streamlit Cloud 환경 변수 확인
        return os.getenv("STREAMLIT_CLOUD") is not None
    except:
        return False
