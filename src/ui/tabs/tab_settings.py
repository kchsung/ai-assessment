import streamlit as st

def render(st):
    
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
        current_model = st.session_state.get("selected_model", "gpt-5")
        
        # 모델 선택
        selected_model = st.selectbox(
            "사용할 OpenAI 모델을 선택하세요:",
            options=list(available_models.keys()),
            format_func=lambda x: f"{x} - {available_models[x]}",
            index=list(available_models.keys()).index(current_model),
            key="settings_model"
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
        
        config_info = {
            "selected_model": st.session_state.get("selected_model", "gpt-5"),
            "api_configured": "✅ 설정됨" if st.session_state.get("generator") else "❌ 미설정",
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
    
    # 구분선
    st.divider()
    
    # 제미나이 모델 설정
    st.subheader("🤖 제미나이 모델 설정")
    
    # 좌우 컬럼으로 나누기
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # 사용 가능한 제미나이 모델 목록
        available_gemini_models = {
            "gemini-2.5-pro": "Gemini 2.5 Pro (최신 모델, 최고 성능)",
            "gemini-1.5-pro": "Gemini 1.5 Pro (안정적, 높은 성능)",
            "gemini-1.5-flash": "Gemini 1.5 Flash (빠른 응답, 기본 성능)",
            "gemini-1.5-flash-latest": "Gemini 1.5 Flash Latest (최신 Flash)",
            "gemini-pro": "Gemini Pro (기본 모델)"
        }
        
        # 현재 선택된 제미나이 모델 (세션 상태에서 가져오기)
        current_gemini_model = st.session_state.get("selected_gemini_model", "gemini-2.5-pro")
        
        # 제미나이 모델 선택
        selected_gemini_model = st.selectbox(
            "사용할 제미나이 모델을 선택하세요:",
            options=list(available_gemini_models.keys()),
            format_func=lambda x: f"{x} - {available_gemini_models[x]}",
            index=list(available_gemini_models.keys()).index(current_gemini_model) if current_gemini_model in available_gemini_models else 0,
            key="settings_gemini_model"
        )
        
        # 제미나이 모델 정보 표시
        st.info(f"**선택된 제미나이 모델**: {selected_gemini_model}")
        st.caption(available_gemini_models[selected_gemini_model])
        
        # 제미나이 모델 변경 시 세션 상태 업데이트
        if selected_gemini_model != current_gemini_model:
            st.session_state.selected_gemini_model = selected_gemini_model
            st.success(f"제미나이 모델이 {selected_gemini_model}로 변경되었습니다!")
            st.rerun()
        
        # Temperature 설정
        st.markdown("#### 🌡️ Temperature 설정")
        
        # 현재 temperature 값 (세션 상태에서 가져오기)
        current_temperature = st.session_state.get("gemini_temperature", 0.3)
        
        # Temperature 슬라이더
        selected_temperature = st.slider(
            "Temperature 값 (0.0 = 일관된 응답, 1.0 = 창의적 응답):",
            min_value=0.0,
            max_value=1.0,
            value=current_temperature,
            step=0.1,
            key="settings_gemini_temperature"
        )
        
        # Temperature 정보 표시
        if selected_temperature <= 0.2:
            temp_desc = "매우 일관된 응답 (정확한 평가에 적합)"
            temp_color = "🟢"
        elif selected_temperature <= 0.5:
            temp_desc = "균형잡힌 응답 (일반적인 용도에 적합)"
            temp_color = "🟡"
        else:
            temp_desc = "창의적인 응답 (다양한 관점이 필요한 경우)"
            temp_color = "🔴"
        
        st.info(f"{temp_color} **현재 Temperature**: {selected_temperature} - {temp_desc}")
        
        # Temperature 변경 시 세션 상태 업데이트
        if selected_temperature != current_temperature:
            st.session_state.gemini_temperature = selected_temperature
            st.success(f"Temperature가 {selected_temperature}로 변경되었습니다!")
            st.rerun()
    
    with col2:
        # 현재 제미나이 설정 정보
        st.markdown("### 📊 제미나이 설정")
        
        # 제미나이 API 키 확인
        from src.config import get_secret
        gemini_api_key = get_secret("GEMINI_API_KEY")
        
        gemini_config_info = {
            "selected_model": st.session_state.get("selected_gemini_model", "gemini-2.5-pro"),
            "temperature": st.session_state.get("gemini_temperature", 0.3),
            "api_configured": "✅ 설정됨" if gemini_api_key else "❌ 미설정",
            "environment": "☁️ Streamlit Cloud" if is_streamlit_cloud() else "💻 로컬",
            "api_key_source": "🔐 secrets" if gemini_api_key else "❌ 없음"
        }
        
        st.json(gemini_config_info)
        
        # 제미나이 API 키 안내 메시지
        if not gemini_api_key:
            if is_streamlit_cloud():
                st.warning("**Streamlit Cloud**: Secrets 탭에서 GEMINI_API_KEY를 설정하세요")
            else:
                st.warning("**로컬**: .streamlit/secrets.toml 또는 .env 파일에 GEMINI_API_KEY를 설정하세요")
    
    # 구분선
    st.divider()
    
    # Streamlit Cloud 설정 가이드
    if is_streamlit_cloud():
        st.markdown("### ☁️ Streamlit Cloud 설정 가이드")
        
        with st.expander("🔧 Secrets 설정 방법", expanded=False):
            st.markdown("""
            **Streamlit Cloud에서 다음 secrets를 설정해야 합니다:**
            
            ```toml
            # Streamlit Cloud Secrets 탭에서 설정
            EDGE_FUNCTION_URL = "https://your-project.supabase.co/functions/v1/your-function"
            EDGE_SHARED_TOKEN = "your_shared_token_here"
            SUPABASE_ANON_KEY = "your_supabase_anon_key_here"
            OPENAI_API_KEY = "your_openai_api_key_here"
            GEMINI_API_KEY = "your_gemini_api_key_here"
            ```
            
            **설정 방법:**
            1. Streamlit Cloud 대시보드에서 앱 선택
            2. "Settings" → "Secrets" 탭 클릭
            3. 위의 키-값 쌍을 입력
            4. "Save" 버튼 클릭
            5. 앱 재배포
            """)
            
            # 현재 설정 상태 확인
            from src.config import get_secret
            edge_url = get_secret("EDGE_FUNCTION_URL")
            edge_token = get_secret("EDGE_SHARED_TOKEN")
            supabase_key = get_secret("SUPABASE_ANON_KEY")
            openai_key = get_secret("OPENAI_API_KEY")
            gemini_key = get_secret("GEMINI_API_KEY")
            
            st.markdown("**현재 설정 상태:**")
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"🔗 EDGE_FUNCTION_URL: {'✅ 설정됨' if edge_url else '❌ 누락'}")
                st.write(f"🔑 EDGE_SHARED_TOKEN: {'✅ 설정됨' if edge_token else '❌ 누락'}")
                st.write(f"🗄️ SUPABASE_ANON_KEY: {'✅ 설정됨' if supabase_key else '❌ 누락'}")
            
            with col2:
                st.write(f"🤖 OPENAI_API_KEY: {'✅ 설정됨' if openai_key else '❌ 누락'}")
                st.write(f"🤖 GEMINI_API_KEY: {'✅ 설정됨' if gemini_key else '❌ 누락'}")
            
            if not all([edge_url, edge_token, supabase_key, openai_key, gemini_key]):
                st.error("⚠️ 일부 필수 설정이 누락되었습니다. 위의 가이드를 따라 설정하세요.")
            else:
                st.success("✅ 모든 필수 설정이 완료되었습니다!")

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
    
    # 구분선
    st.divider()
    
    # 제미나이 모델별 특징 설명
    st.markdown("### 📋 제미나이 모델별 특징")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**Gemini 2.5 Pro**")
        st.markdown("""
        - 🎯 **용도**: 복잡한 평가 및 분석
        - ⚡ **속도**: 보통
        - 💰 **비용**: 높음
        - 🧠 **성능**: 최고 (Thinking 기능 지원)
        - 🔥 **특징**: 최신 모델, 사고 과정 표시
        """)
    
    with col2:
        st.markdown("**Gemini 1.5 Pro**")
        st.markdown("""
        - 🎯 **용도**: 안정적인 평가 작업
        - ⚡ **속도**: 보통
        - 💰 **비용**: 중간
        - 🧠 **성능**: 높음
        - 🔥 **특징**: 안정적, 대용량 컨텍스트
        """)
    
    with col3:
        st.markdown("**Gemini 1.5 Flash**")
        st.markdown("""
        - 🎯 **용도**: 빠른 평가 및 검토
        - ⚡ **속도**: 빠름
        - 💰 **비용**: 낮음
        - 🧠 **성능**: 기본
        - 🔥 **특징**: 빠른 응답, 효율적
        """)
