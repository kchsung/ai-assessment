import os
import streamlit as st

# .env 로드 (있으면)
try:
    from dotenv import load_dotenv
    load_dotenv(override=False)
except Exception:
    pass

def get_secret(name: str, default=None) -> str | None:
    # 1) st.secrets
    try:
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    # 2) env
    val = os.getenv(name)
    if val not in (None, ""):
        return val
    # 3) default
    return default
