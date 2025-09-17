from datetime import datetime
import pandas as pd
import streamlit as st

def render(st):
    st.header("⚙️ 설정")
    st.subheader("API 설정")
    if st.secrets.get("OPENAI_API_KEY") or st.session_state.get("OPENAI_API_KEY"):
        st.success("✅ OpenAI API 키가 설정되어 있습니다.")
    else:
        st.warning("⚠️ OpenAI API 키가 설정되지 않았습니다. (로컬 .env 또는 Cloud Secrets)")

    st.subheader("데이터 관리")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("📥 데이터 내보내기"):
            qs = st.session_state.db.get_questions()
            df = pd.DataFrame(qs)
            csv = df.to_csv(index=False, encoding="utf-8-sig")
            st.download_button("CSV 다운로드", csv, file_name=f"ai_assessment_{datetime.now():%Y%m%d}.csv", mime="text/csv")
    with c2:
        if st.button("🗑️ 데이터베이스 초기화", type="secondary"):
            if st.checkbox("정말로 모든 데이터를 삭제하시겠습니까?"):
                st.session_state.db.reset_database()
                st.success("데이터베이스 초기화 완료")
                st.rerun()
