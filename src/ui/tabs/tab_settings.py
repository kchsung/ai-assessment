import streamlit as st

def render(st):
    st.header("⚙️ 설정")
    
    # OpenAI 모델 설정
    st.subheader("🤖 OpenAI 모델 설정")
    
    # 좌우 컬럼으로 나누기
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # 사용 가능한 모델 목록
        available_models = {
            "gpt-5": "GPT-5 (최신 모델, 높은 성능)",
            "gpt-5-nano": "GPT-5 Nano (빠른 응답, 기본 성능)",
            "gpt-5-mini": "GPT-5 Mini (경량화, 빠른 처리)"
        }
        
        # 현재 선택된 모델 (세션 상태에서 가져오기)
        current_model = st.session_state.get("selected_model", "gpt-5-nano")
        
        # 모델 선택
        selected_model = st.selectbox(
            "사용할 OpenAI 모델을 선택하세요:",
            options=list(available_models.keys()),
            format_func=lambda x: f"{x} - {available_models[x]}",
            index=list(available_models.keys()).index(current_model)
        )
        
        # 모델 정보 표시
        st.info(f"**선택된 모델**: {selected_model}")
        st.caption(available_models[selected_model])
        
        # 모델 변경 시 세션 상태 업데이트
        if selected_model != current_model:
            st.session_state.selected_model = selected_model
            st.success(f"모델이 {selected_model}로 변경되었습니다!")
            st.rerun()
    
    with col2:
        # 현재 설정 정보
        st.markdown("### 📊 현재 설정")
        
        # 환경 정보 추가
        from src.config import is_streamlit_cloud, get_secret
        api_key = get_secret("OPENAI_API_KEY")
        
        # 데이터베이스 상태 확인
        db = st.session_state.get("db")
        db_type = "LocalDB" if db and "LocalDBClient" in str(type(db)) else "EdgeDB"
        
        config_info = {
            "selected_model": st.session_state.get("selected_model", "gpt-5-nano"),
            "api_configured": "✅ 설정됨" if st.session_state.get("generator") else "❌ 미설정",
            "database": f"✅ {db_type} 사용 중",
            "environment": "☁️ Streamlit Cloud" if is_streamlit_cloud() else "💻 로컬",
            "api_key_source": "🔐 secrets" if api_key and "sk-proj-" in str(api_key) else "❌ 없음"
        }
        
        st.json(config_info)
        
        # 환경별 안내 메시지
        if not st.session_state.get("generator"):
            if is_streamlit_cloud():
                st.warning("**Streamlit Cloud**: Secrets 탭에서 API 키를 설정하세요")
            else:
                st.warning("**로컬**: .streamlit/secrets.toml 또는 .env 파일에 API 키를 설정하세요")
    
    # 모델별 특징 설명
    st.markdown("### 📋 모델별 특징")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**GPT-5**")
        st.markdown("""
        - 🎯 **용도**: 복잡한 문제 생성
        - ⚡ **속도**: 보통
        - 💰 **비용**: 높음
        - 💵 **가격**: 
          - Input: $0.03/1K tokens
          - Output: $0.12/1K tokens
        - 🧠 **성능**: 최고
        """)
    
    with col2:
        st.markdown("**GPT-5 Nano**")
        st.markdown("""
        - 🎯 **용도**: 일반적인 문제 생성
        - ⚡ **속도**: 빠름
        - 💰 **비용**: 낮음
        - 💵 **가격**: 
          - Input: $0.01/1K tokens
          - Output: $0.04/1K tokens
        - 🧠 **성능**: 기본
        """)
    
    with col3:
        st.markdown("**GPT-5 Mini**")
        st.markdown("""
        - 🎯 **용도**: 간단한 문제 생성
        - ⚡ **속도**: 매우 빠름
        - 💰 **비용**: 매우 낮음
        - 💵 **가격**: 
          - Input: $0.005/1K tokens
          - Output: $0.02/1K tokens
        - 🧠 **성능**: 경량
        """)
