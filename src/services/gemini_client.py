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
            
        # 직접 환경 변수에서 가져오기
        api_key = os.getenv("GEMINI_API_KEY")
        # print(f"DEBUG: Direct os.getenv('GEMINI_API_KEY'): {bool(api_key)}")
        
        if not api_key:
            # get_secret도 시도
            api_key = get_secret("GEMINI_API_KEY")
            # print(f"DEBUG: get_secret('GEMINI_API_KEY'): {bool(api_key)}")
        
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY가 설정되지 않았습니다")
        
        genai.configure(api_key=api_key)
        
        # 제미나이 모델 설정
        # gemini-2.5-pro 사용
        model_name = get_secret("GEMINI_MODEL") or os.getenv("GEMINI_MODEL", "gemini-2.5-pro")
        
        generation_config = genai.types.GenerationConfig(
            temperature=0.3
        )
        
        try:
            self.model = genai.GenerativeModel(
                model_name,
                generation_config=generation_config
            )
            print(f"✅ 제미나이 모델 초기화 성공: {model_name}")
        except Exception as e:
            print(f"❌ 모델 {model_name} 초기화 실패: {e}")
            
            # 사용 가능한 모델 목록 출력
            try:
                available_models = self.list_available_models()
                print(f"📋 사용 가능한 모델 목록: {available_models}")
            except:
                print("📋 모델 목록 조회 실패")
            
            # 대체 모델 시도
            fallback_models = ["gemini-1.5-flash", "gemini-1.5-flash-latest", "gemini-pro"]
            for fallback_model in fallback_models:
                try:
                    print(f"🔄 대체 모델 시도: {fallback_model}")
                    self.model = genai.GenerativeModel(
                        fallback_model,
                        generation_config=generation_config
                    )
                    print(f"✅ 대체 모델 초기화 성공: {fallback_model}")
                    break
                except Exception as fallback_error:
                    print(f"❌ 대체 모델 {fallback_model} 실패: {fallback_error}")
                    continue
            else:
                raise RuntimeError(f"모든 제미나이 모델 초기화 실패. 마지막 오류: {e}")
        
        # 초기화 완료 표시
        GeminiClient._initialized = True

    def review_content(self, system_prompt: str, user_prompt: str) -> str:
        """내용 검토를 위한 제미나이 API 호출"""
        try:
            # 제미나이에서는 system prompt를 직접 지원하지 않으므로 user prompt에 포함
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            
            response = self.model.generate_content(full_prompt)
            
            # 응답 디버깅 정보 출력 (문제 데이터 출력 방지를 위해 주석 처리)
            # print(f"DEBUG: 제미나이 응답 타입: {type(response)}")
            # print(f"DEBUG: 응답 속성들: {dir(response)}")
            
            # 응답의 모든 정보 확인
            # if hasattr(response, 'text'):
            #     print(f"DEBUG: response.text 길이: {len(response.text) if response.text else 0}")
            # if hasattr(response, 'candidates'):
            #     print(f"DEBUG: candidates 개수: {len(response.candidates) if response.candidates else 0}")
            #     if response.candidates:
            #         candidate = response.candidates[0]
            #         print(f"DEBUG: 첫 번째 candidate 속성들: {dir(candidate)}")
            #         if hasattr(candidate, 'content'):
            #             print(f"DEBUG: candidate.content 타입: {type(candidate.content)}")
            #             if hasattr(candidate.content, 'parts'):
            #                 print(f"DEBUG: parts 개수: {len(candidate.content.parts) if candidate.content.parts else 0}")
            
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
        except Exception as e:
            print(f"모델 목록 조회 실패: {e}")
            return []

    def is_available(self) -> bool:
        """제미나이 API 사용 가능 여부 확인"""
        try:
            # 직접 환경 변수에서 가져오기
            api_key = os.getenv("GEMINI_API_KEY")
            # print(f"DEBUG is_available: Direct os.getenv('GEMINI_API_KEY'): {bool(api_key)}")
            
            if not api_key:
                # get_secret도 시도
                api_key = get_secret("GEMINI_API_KEY")
                # print(f"DEBUG is_available: get_secret('GEMINI_API_KEY'): {bool(api_key)}")
            
            if api_key:
                # print(f"DEBUG is_available: API key length: {len(api_key)}")
                pass
            
            return bool(api_key)
        except Exception as e:
            # print(f"DEBUG is_available: Error checking GEMINI_API_KEY: {e}")
            return False
