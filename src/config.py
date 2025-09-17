import os
import streamlit as st

# .env 로드 (있으면)
try:
    from dotenv import load_dotenv
    load_dotenv(override=False)
except Exception:
    pass

def get_secret(name: str, default=None) -> str | None:
    # 1) st.secrets (안전하게)
    try:
        if hasattr(st, 'secrets'):
            val = st.secrets.get(name)
            # 기본값이 아닌 실제 값인지 확인
            if val and val != "your_openai_api_key_here" and val.strip() != "":
                return val
    except Exception as e:
        # 디버깅용 (나중에 제거 가능)
        print(f"st.secrets 접근 오류: {e}")
        pass
    # 2) env
    val = os.getenv(name)
    if val and val.strip() != "":
        return val
    # 3) default
    return default
