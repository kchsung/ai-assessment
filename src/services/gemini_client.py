"""
제미나이 API 클라이언트
"""
import os
import json
from datetime import datetime
import google.generativeai as genai
from src.config import get_secret

# 문제 교정용 새로운 패키지 (google-genai)
try:
    from google import genai as new_genai
    from google.genai import types
    NEW_GENAI_AVAILABLE = True
    _CORRECT_PROBLEM_AVAILABLE = True
    # 디버깅: 패키지 버전 확인
    try:
        import google.genai
        _GENAI_VERSION = getattr(google.genai, '__version__', 'unknown')
    except:
        _GENAI_VERSION = 'unknown'
except ImportError as e:
    NEW_GENAI_AVAILABLE = False
    new_genai = None
    types = None
    _CORRECT_PROBLEM_AVAILABLE = False
    _GENAI_VERSION = None
    _IMPORT_ERROR = str(e)

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
            # 디버깅 정보를 세션 상태에 저장
            import streamlit as st
            if hasattr(st, 'session_state'):
                if "gemini_api_debug" not in st.session_state:
                    st.session_state.gemini_api_debug = []
                
                from datetime import datetime
                # 모델 이름 추출
                model_name = "unknown"
                if hasattr(self, 'model') and self.model:
                    if hasattr(self.model, 'model_name'):
                        model_name = self.model.model_name
                    elif hasattr(self.model, 'name'):
                        model_name = self.model.name
                    elif isinstance(self.model, str):
                        model_name = self.model
                
                api_debug_info = {
                    "timestamp": datetime.now().isoformat(),
                    "method": "review_content",
                    "model": model_name,
                    "parameters": {
                        "temperature": "기본값 (미설정)",
                        "thinking_level": "미지원",
                        "media_resolution": "미지원",
                        "response_mime_type": "text/plain (기본값)",
                        "response_schema": "미지원 (일반 텍스트 응답)"
                    },
                    "prompts": {
                        "system_prompt": system_prompt,
                        "system_prompt_length": len(system_prompt),
                        "user_prompt": user_prompt,
                        "user_prompt_length": len(user_prompt),
                        "combined_prompt": f"{system_prompt}\n\n{user_prompt}",
                        "combined_prompt_length": len(system_prompt) + len(user_prompt) + 2
                    }
                }
                st.session_state.gemini_api_debug.append(api_debug_info)
            
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
    
    def correct_problem(self, system_prompt: str, user_prompt: str) -> str:
        """
        문제 교정을 위한 제미나이 API 호출 (새로운 google-genai 패키지 사용)
        
        Args:
            system_prompt: 시스템 프롬프트
            user_prompt: 사용자 프롬프트 (문제 JSON 포함)
            
        Returns:
            str: 교정된 문제의 JSON 문자열
            
        Raises:
            RuntimeError: google-genai 패키지가 설치되지 않았거나 API 호출 실패 시
        """
        if not NEW_GENAI_AVAILABLE:
            raise RuntimeError("google-genai 패키지가 설치되지 않았습니다. pip install google-genai를 실행해주세요.")
        
        try:
            # API 키 가져오기
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
            
            # 새로운 클라이언트 생성
            client = new_genai.Client(api_key=api_key)
            
            # 모델 설정
            model = "gemini-3-pro-preview"
            
            # Contents 구성 (참조 코드와 동일하게 user role만 사용)
            contents = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=user_prompt),
                    ],
                ),
            ]
            
            # System instruction 구성 (GenerateContentConfig에 포함)
            system_instruction = [
                types.Part.from_text(text=system_prompt),
            ]
            
            # JSON 스키마 정의 (사용자 제공 스키마 구조 사용)
            response_schema = types.Schema(
                type=types.Type.OBJECT,
                required=["meta_layer", "user_view_layer", "system_view_layer", "evaluation_layer"],
                properties={
                    "meta_layer": types.Schema(
                        type=types.Type.OBJECT,
                        required=["id", "lang", "category", "difficulty", "time_limit", "problem_type", "target_template_code", "active"],
                        properties={
                            "idx": types.Schema(
                                type=types.Type.INTEGER,
                            ),
                            "id": types.Schema(
                                type=types.Type.STRING,
                            ),
                            "lang": types.Schema(
                                type=types.Type.STRING,
                            ),
                            "category": types.Schema(
                                type=types.Type.STRING,
                            ),
                            "topic": types.Schema(
                                type=types.Type.ARRAY,
                                items=types.Schema(
                                    type=types.Type.STRING,
                                ),
                            ),
                            "difficulty": types.Schema(
                                type=types.Type.STRING,
                            ),
                            "time_limit": types.Schema(
                                type=types.Type.STRING,
                            ),
                            "problem_type": types.Schema(
                                type=types.Type.STRING,
                            ),
                            "target_template_code": types.Schema(
                                type=types.Type.STRING,
                            ),
                            "created_by": types.Schema(
                                type=types.Type.STRING,
                            ),
                            "created_at": types.Schema(
                                type=types.Type.STRING,
                            ),
                            "updated_at": types.Schema(
                                type=types.Type.STRING,
                            ),
                            "active": types.Schema(
                                type=types.Type.BOOLEAN,
                            ),
                        },
                    ),
                    "user_view_layer": types.Schema(
                        type=types.Type.OBJECT,
                        required=["title", "summary", "scenario", "task"],
                        properties={
                            "title": types.Schema(
                                type=types.Type.STRING,
                            ),
                            "summary": types.Schema(
                                type=types.Type.STRING,
                            ),
                            "topic_summary": types.Schema(
                                type=types.Type.STRING,
                            ),
                            "scenario": types.Schema(
                                type=types.Type.STRING,
                            ),
                            "scenario_public": types.Schema(
                                type=types.Type.STRING,
                            ),
                            "task": types.Schema(
                                type=types.Type.STRING,
                            ),
                            "task_instruction": types.Schema(
                                type=types.Type.STRING,
                            ),
                            "goal": types.Schema(
                                type=types.Type.ARRAY,
                                items=types.Schema(
                                    type=types.Type.STRING,
                                ),
                            ),
                            "requirements": types.Schema(
                                type=types.Type.ARRAY,
                                items=types.Schema(
                                    type=types.Type.STRING,
                                ),
                            ),
                            "constraints": types.Schema(
                                type=types.Type.ARRAY,
                                items=types.Schema(
                                    type=types.Type.STRING,
                                ),
                            ),
                            "constraints_public": types.Schema(
                                type=types.Type.ARRAY,
                                items=types.Schema(
                                    type=types.Type.STRING,
                                ),
                            ),
                            "opening_line": types.Schema(
                                type=types.Type.STRING,
                            ),
                            "first_question": types.Schema(
                                type=types.Type.ARRAY,
                                items=types.Schema(
                                    type=types.Type.STRING,
                                ),
                            ),
                            "starter_guide": types.Schema(
                                type=types.Type.STRING,
                            ),
                            "attachments": types.Schema(
                                type=types.Type.ARRAY,
                                items=types.Schema(
                                    type=types.Type.STRING,
                                ),
                            ),
                            "task_raw": types.Schema(
                                type=types.Type.STRING,
                            ),
                        },
                    ),
                    "system_view_layer": types.Schema(
                        type=types.Type.OBJECT,
                        required=["data_facts", "guide"],
                        properties={
                            "data_facts": types.Schema(
                                type=types.Type.ARRAY,
                                items=types.Schema(
                                    type=types.Type.OBJECT,
                                    required=["key", "value"],
                                    properties={
                                        "key": types.Schema(
                                            type=types.Type.STRING,
                                        ),
                                        "value": types.Schema(
                                            type=types.Type.STRING,
                                        ),
                                    },
                                ),
                            ),
                            "hidden_constraints": types.Schema(
                                type=types.Type.ARRAY,
                                items=types.Schema(
                                    type=types.Type.STRING,
                                ),
                            ),
                            "reveal_rules": types.Schema(
                                type=types.Type.ARRAY,
                                items=types.Schema(
                                    type=types.Type.STRING,
                                ),
                            ),
                            "guide": types.Schema(
                                type=types.Type.OBJECT,
                                required=["tools", "approach", "considerations"],
                                properties={
                                    "tools": types.Schema(
                                        type=types.Type.ARRAY,
                                        items=types.Schema(
                                            type=types.Type.STRING,
                                        ),
                                    ),
                                    "approach": types.Schema(
                                        type=types.Type.ARRAY,
                                        items=types.Schema(
                                            type=types.Type.STRING,
                                        ),
                                    ),
                                    "considerations": types.Schema(
                                        type=types.Type.ARRAY,
                                        items=types.Schema(
                                            type=types.Type.STRING,
                                        ),
                                    ),
                                },
                            ),
                            "reference": types.Schema(
                                type=types.Type.ARRAY,
                                items=types.Schema(
                                    type=types.Type.OBJECT,
                                    required=["key", "value"],
                                    properties={
                                        "key": types.Schema(
                                            type=types.Type.STRING,
                                        ),
                                        "value": types.Schema(
                                            type=types.Type.STRING,
                                        ),
                                    },
                                ),
                            ),
                        },
                    ),
                    "evaluation_layer": types.Schema(
                        type=types.Type.OBJECT,
                        required=["evaluation", "process_criteria", "result_criteria", "scoring_weights", "critical_fail_rules"],
                        properties={
                            "evaluation": types.Schema(
                                type=types.Type.ARRAY,
                                items=types.Schema(
                                    type=types.Type.STRING,
                                ),
                            ),
                            "process_criteria": types.Schema(
                                type=types.Type.ARRAY,
                                items=types.Schema(
                                    type=types.Type.STRING,
                                ),
                            ),
                            "result_criteria": types.Schema(
                                type=types.Type.ARRAY,
                                items=types.Schema(
                                    type=types.Type.STRING,
                                ),
                            ),
                            "scoring_weights": types.Schema(
                                type=types.Type.OBJECT,
                                required=["process", "result"],
                                properties={
                                    "process": types.Schema(
                                        type=types.Type.NUMBER,
                                    ),
                                    "result": types.Schema(
                                        type=types.Type.NUMBER,
                                    ),
                                },
                            ),
                            "model_answer": types.Schema(
                                type=types.Type.STRING,
                            ),
                            "critical_fail_rules": types.Schema(
                                type=types.Type.ARRAY,
                                items=types.Schema(
                                    type=types.Type.STRING,
                                ),
                            ),
                        },
                    ),
                },
            )
            
            # GenerateContentConfig 설정 (참조 코드와 동일하게)
            temperature = 1.3
            thinking_level = "HIGH"
            media_resolution = "MEDIA_RESOLUTION_HIGH"
            response_mime_type = "application/json"
            
            # GenerateContentConfig에 system_instruction 포함 (참조 코드와 동일)
            generate_content_config = types.GenerateContentConfig(
                temperature=temperature,
                thinking_config=types.ThinkingConfig(
                    thinking_level=thinking_level,
                ),
                media_resolution=media_resolution,
                response_mime_type=response_mime_type,
                response_schema=response_schema,
                system_instruction=system_instruction,
            )
            
            # 디버깅 정보를 세션 상태에 저장
            import streamlit as st
            if hasattr(st, 'session_state'):
                if "gemini_api_debug" not in st.session_state:
                    st.session_state.gemini_api_debug = []
                
                from datetime import datetime
                api_debug_info = {
                    "timestamp": datetime.now().isoformat(),
                    "method": "correct_problem",
                    "model": model,
                    "parameters": {
                        "temperature": temperature,
                        "thinking_level": thinking_level,
                        "media_resolution": media_resolution,
                        "response_mime_type": response_mime_type,
                        "response_schema": "설정됨 (4개 레이어: meta_layer, user_view_layer, system_view_layer, evaluation_layer)"
                    },
                    "prompts": {
                        "system_prompt": system_prompt,
                        "system_prompt_length": len(system_prompt),
                        "user_prompt": user_prompt,
                        "user_prompt_length": len(user_prompt)
                    }
                }
                st.session_state.gemini_api_debug.append(api_debug_info)
            
            # 디버깅: 설정 확인
            if hasattr(st, 'write'):
                with st.expander("🔍 Gemini API 호출 설정", expanded=False):
                    st.write(f"**모델**: {model}")
                    st.write(f"**Temperature**: {temperature}")
                    st.write(f"**Thinking Level**: {thinking_level}")
                    st.write(f"**Response MIME Type**: {response_mime_type}")
                    st.write(f"**System Instruction 길이**: {len(system_prompt)} 문자")
                    st.write(f"**User Prompt 길이**: {len(user_prompt)} 문자")
                    st.write(f"**Response Schema**: 설정됨 (4개 레이어)")
            
            # 스트리밍으로 응답 받기
            response_text = ""
            chunk_count = 0
            for chunk in client.models.generate_content_stream(
                model=model,
                contents=contents,
                config=generate_content_config,
            ):
                if hasattr(chunk, 'text') and chunk.text:
                    response_text += chunk.text
                    chunk_count += 1
            
            # 디버깅: 응답 확인
            if hasattr(st, 'write'):
                with st.expander("📥 Gemini API 응답 정보", expanded=False):
                    st.write(f"**응답 길이**: {len(response_text)} 문자")
                    st.write(f"**Chunk 개수**: {chunk_count}")
                    st.write(f"**응답 미리보기 (처음 500자)**:")
                    st.code(response_text[:500] if response_text else "응답 없음")
            
            return response_text
            
        except Exception as e:
            raise RuntimeError(f"문제 교정 API 호출 실패: {str(e)}")
