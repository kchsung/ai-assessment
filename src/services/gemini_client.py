"""
제미나이 API 클라이언트
"""
import os
import json
import google.generativeai as genai
from src.config import get_secret

# .env 파일 로드
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

class GeminiClient:
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GeminiClient, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        # 이미 초기화된 경우 중복 초기화 방지
        if GeminiClient._initialized:
            return
            
        # Streamlit Cloud에서는 st.secrets 사용, 로컬에서는 환경변수 사용
        api_key = None
        
        # 1순위: st.secrets 직접 접근
        try:
            import streamlit as st
            api_key = st.secrets["GEMINI_API_KEY"]
        except Exception:
            pass
        
        # 2순위: st.secrets.get() 방식
        if not api_key:
            try:
                import streamlit as st
                api_key = st.secrets.get("GEMINI_API_KEY")
            except Exception:
                pass
        
        # 3순위: get_secret 방식
        if not api_key:
            api_key = get_secret("GEMINI_API_KEY")
        
        # 4순위: 환경변수 fallback
        if not api_key:
            api_key = os.getenv("GEMINI_API_KEY")
        
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY가 설정되지 않았습니다")
        
        genai.configure(api_key=api_key)
        
        # 제미나이 모델 설정
        # 세션 상태에서 모델 선택, 없으면 기본값 사용
        import streamlit as st
        model_name = st.session_state.get("selected_gemini_model") or get_secret("GEMINI_MODEL") or os.getenv("GEMINI_MODEL", "gemini-2.5-pro")
        
        # 세션 상태에서 temperature 선택, 없으면 기본값 사용
        temperature = st.session_state.get("gemini_temperature", 0.3)
        
        generation_config = genai.types.GenerationConfig(
            temperature=temperature
        )
        
        # ThinkingConfig 설정 (gemini-2.5-pro에서 지원, 버전에 따라 선택적 사용)
        thinking_config = None
        try:
            if hasattr(genai.types, 'ThinkingConfig'):
                thinking_config = genai.types.ThinkingConfig(
                    thinking_budget=-1,  # 무제한 사고 예산
                )
        except Exception:
            thinking_config = None
        
        try:
            if thinking_config:
                self.model = genai.GenerativeModel(
                    model_name,
                    generation_config=generation_config,
                    thinking_config=thinking_config
                )
            else:
                self.model = genai.GenerativeModel(
                    model_name,
                    generation_config=generation_config
                )
        except Exception as e:
            # 대체 모델 시도
            fallback_models = ["gemini-1.5-flash", "gemini-1.5-flash-latest", "gemini-pro"]
            for fallback_model in fallback_models:
                try:
                    self.model = genai.GenerativeModel(
                        fallback_model,
                        generation_config=generation_config,
                        thinking_config=thinking_config
                    )
                    break
                except Exception:
                    continue
            else:
                raise RuntimeError(f"모든 제미나이 모델 초기화 실패. 마지막 오류: {e}")
        
        # 초기화 완료 표시
        GeminiClient._initialized = True

    def review_content(self, system_prompt: str, user_prompt: str) -> str:
        """내용 검토를 위한 제미나이 API 호출"""
        try:
            # 최신 Google Generative AI 라이브러리에서는 contents 배열을 사용
            contents = [
                {"role": "user", "parts": [{"text": f"{system_prompt}\n\n{user_prompt}"}]}
            ]
            response = self.model.generate_content(contents)
            
            
            # 기본적으로 text 반환
            if response.text:
                return response.text
            else:
                # text가 없는 경우 candidates에서 추출 시도
                if hasattr(response, 'candidates') and response.candidates:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                        text_parts = []
                        for part in candidate.content.parts:
                            if hasattr(part, 'text') and part.text:
                                text_parts.append(part.text)
                        if text_parts:
                            return '\n'.join(text_parts)
                
                return "❌ 제미나이 응답에서 텍스트를 추출할 수 없습니다."
                
        except Exception as e:
            raise RuntimeError(f"제미나이 API 호출 실패: {str(e)}")

    def list_available_models(self) -> list:
        """사용 가능한 제미나이 모델 목록 조회"""
        try:
            models = genai.list_models()
            available_models = []
            for model in models:
                if 'generateContent' in model.supported_generation_methods:
                    available_models.append(model.name.replace('models/', ''))
            return available_models
        except Exception:
            return []

    def is_available(self) -> bool:
        """제미나이 API 사용 가능 여부 확인"""
        try:
            # 직접 환경 변수에서 가져오기
            api_key = os.getenv("GEMINI_API_KEY")
            
            if not api_key:
                # get_secret도 시도
                api_key = get_secret("GEMINI_API_KEY")
            
            return bool(api_key)
        except Exception:
            return False
