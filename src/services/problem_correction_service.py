"""
문제 교정 서비스
"""
import streamlit as st
import json
from datetime import datetime
from src.config import get_secret
from src.prompts.problem_correction_template import (
    DEFAULT_PROBLEM_CORRECTION_PROMPT, 
    LEARNING_CONCEPT_PROMPT_ID
)
try:
    from src.services.gemini_client import GeminiClient
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    GeminiClient = None

class ProblemCorrectionService:
    def __init__(self):
        self.gemini_client = None
        self.initialization_error = None
        if GEMINI_AVAILABLE:
            try:
                self.gemini_client = GeminiClient()
                # print("✅ ProblemCorrectionService 초기화 성공")
            except Exception as e:
                self.initialization_error = str(e)
                # print(f"❌ GeminiClient 초기화 실패: {e}")
        else:
            self.initialization_error = "google-generativeai 패키지가 설치되지 않았습니다"
    
    def get_correction_prompt(self, question_type: str = "subjective") -> str:
        """
        문제 교정 프롬프트를 가져옵니다.
        항상 DEFAULT_PROBLEM_CORRECTION_PROMPT를 사용합니다.
        
        Args:
            question_type: 문제 유형 ('multiple_choice' 또는 'subjective') - 현재는 사용하지 않음
            
        Returns:
            str: 교정 프롬프트 (DEFAULT_PROBLEM_CORRECTION_PROMPT)
        """
        # 항상 DEFAULT_PROBLEM_CORRECTION_PROMPT 사용
        # 명시적으로 다시 import하여 최신 버전을 가져옴
        from src.prompts.problem_correction_template import DEFAULT_PROBLEM_CORRECTION_PROMPT as latest_prompt
        import streamlit as st
        if hasattr(st, 'write'):
            # 디버깅: 프롬프트 확인
            st.write(f"🔍 [get_correction_prompt] 프롬프트 길이: {len(latest_prompt)} 문자")
            st.write(f"🔍 [get_correction_prompt] 프롬프트 시작: {latest_prompt[:100]}...")
        return latest_prompt
    
    def correct_problem(self, problem_json: str, question_type: str = "subjective") -> str:
        """
        문제 JSON을 교정합니다.
        
        Args:
            problem_json: 교정할 문제의 JSON 문자열
            question_type: 문제 유형 ('multiple_choice' 또는 'subjective')
            
        Returns:
            str: 교정된 문제의 JSON 문자열
        """
        if not self.gemini_client:
            error_msg = "❌ 제미나이 API를 사용할 수 없습니다."
            if self.initialization_error:
                error_msg += f"\n\n오류 상세: {self.initialization_error}"
            return error_msg
        
        try:
            # 교정 프롬프트 가져오기 (명시적으로 최신 버전 import)
            import importlib
            from src.prompts import problem_correction_template
            importlib.reload(problem_correction_template)  # 모듈 캐시 무시하고 다시 로드
            # 직접 DEFAULT_PROBLEM_CORRECTION_PROMPT 사용 (get_correction_prompt 우회)
            system_prompt = problem_correction_template.DEFAULT_PROBLEM_CORRECTION_PROMPT
            
            # 디버깅: 프롬프트 확인
            import streamlit as st
            if hasattr(st, 'write'):
                with st.expander("📝 사용된 프롬프트 확인", expanded=True):
                    # 프롬프트가 DEFAULT_PROBLEM_CORRECTION_PROMPT인지 확인
                    is_default = system_prompt == problem_correction_template.DEFAULT_PROBLEM_CORRECTION_PROMPT
                    st.write(f"**프롬프트 소스**: {'✅ 기본 프롬프트 (DEFAULT_PROBLEM_CORRECTION_PROMPT)' if is_default else '❌ DB에서 가져온 프롬프트'}")
                    st.write(f"**프롬프트 길이**: {len(system_prompt)} 문자")
                    st.write(f"**프롬프트 시작 부분 (처음 300자)**:")
                    st.code(system_prompt[:300])
                    st.write(f"**프롬프트 해시 (처음 100자)**: {hash(system_prompt[:100])}")
                    if not is_default:
                        st.error("**⚠️ 주의**: DB에서 가져온 프롬프트를 사용 중입니다. 기본 프롬프트와 다를 수 있습니다.")
                    else:
                        st.success("✅ 올바른 기본 프롬프트를 사용 중입니다.")
            
            # 사용자 프롬프트 구성
            user_prompt = f"다음 문제 JSON을 교정해주세요:\n\n{problem_json}"
            
            # 새로운 문제 교정 메서드 사용 가능 여부 확인
            # google-genai 패키지가 설치되어 있고 correct_problem 메서드가 있는 경우에만 사용
            use_new_method = False
            debug_info_dict = {}
            
            try:
                # NEW_GENAI_AVAILABLE 플래그를 직접 확인
                from src.services.gemini_client import NEW_GENAI_AVAILABLE
                try:
                    from src.services.gemini_client import _GENAI_VERSION
                    debug_info_dict["google-genai 버전"] = _GENAI_VERSION
                except (ImportError, AttributeError):
                    debug_info_dict["google-genai 버전"] = "확인 불가"
                
                debug_info_dict["NEW_GENAI_AVAILABLE"] = NEW_GENAI_AVAILABLE
                debug_info_dict["has_correct_problem"] = hasattr(self.gemini_client, 'correct_problem')
                
                # 패키지가 설치되어 있고, 메서드가 존재하는 경우에만 True
                if NEW_GENAI_AVAILABLE is True and hasattr(self.gemini_client, 'correct_problem'):
                    use_new_method = True
                    debug_info_dict["use_new_method"] = True
                else:
                    debug_info_dict["use_new_method"] = False
                    if not NEW_GENAI_AVAILABLE:
                        debug_info_dict["reason"] = "google-genai 패키지가 설치되지 않음"
                        try:
                            import google.genai
                            debug_info_dict["패키지 확인"] = "패키지는 있지만 import 실패"
                        except ImportError as ie:
                            debug_info_dict["import_error"] = str(ie)
                    elif not hasattr(self.gemini_client, 'correct_problem'):
                        debug_info_dict["reason"] = "correct_problem 메서드가 없음"
            except (ImportError, AttributeError, NameError) as e:
                use_new_method = False
                debug_info_dict["error"] = str(e)
                debug_info_dict["use_new_method"] = False
                debug_info_dict["error_type"] = type(e).__name__
            
            # 디버깅: 메서드 선택 정보 (세션 상태에 저장하여 항상 표시)
            debug_info_dict["사용할_메서드"] = "correct_problem" if use_new_method else "review_content"
            if "correction_method_debug" not in st.session_state:
                st.session_state.correction_method_debug = []
            st.session_state.correction_method_debug.append({
                "timestamp": datetime.now().isoformat(),
                "use_new_method": use_new_method,
                "debug_info": debug_info_dict
            })
            
            # 화면에 표시
            with st.expander("🔍 API 메서드 선택 정보", expanded=True):
                st.write("**사용할 메서드**:", "✅ `correct_problem` (새로운 방식 - 레이어 구조)" if use_new_method else "⚠️ `review_content` (기존 방식 - 일반 텍스트)")
                st.json(debug_info_dict)
                if not use_new_method:
                    st.error("⚠️ **주의**: 기존 `review_content` 메서드가 사용됩니다. 레이어 구조가 아닌 일반 형식으로 응답됩니다.")
                    st.info("💡 **해결 방법**: `pip install google-genai`를 실행하여 새로운 패키지를 설치하세요.")
            
            # 새로운 메서드 사용 가능하면 시도 (패키지가 없으면 아예 호출하지 않음)
            if use_new_method:
                try:
                    st.success("✅ 새로운 `correct_problem` 메서드 사용 중 (레이어 구조)")
                    # 세션 상태에 메서드 사용 정보 저장
                    if "correction_method_used" not in st.session_state:
                        st.session_state.correction_method_used = []
                    st.session_state.correction_method_used.append({
                        "method": "correct_problem",
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    corrected_result = self.gemini_client.correct_problem(
                        system_prompt=system_prompt,
                        user_prompt=user_prompt
                    )
                    st.success("✅ `correct_problem` 메서드 호출 성공")
                    return corrected_result
                except RuntimeError as e:
                    # RuntimeError인 경우 (패키지 미설치 등) 기존 메서드로 fallback
                    error_msg = str(e)
                    st.error(f"❌ `correct_problem` 메서드 호출 실패: {error_msg}")
                    if "google-genai" in error_msg.lower():
                        st.warning("⚠️ `google-genai` 패키지 관련 오류로 인해 기존 `review_content` 메서드로 전환합니다.")
                        st.info("💡 **해결 방법**: `pip install google-genai`를 실행하세요.")
                    else:
                        st.warning("⚠️ 기존 `review_content` 메서드로 전환합니다.")
                    
                    # 세션 상태에 fallback 정보 저장
                    if "correction_method_used" not in st.session_state:
                        st.session_state.correction_method_used = []
                    st.session_state.correction_method_used.append({
                        "method": "review_content (fallback)",
                        "error": error_msg,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    corrected_result = self.gemini_client.review_content(
                        system_prompt=system_prompt,
                        user_prompt=user_prompt
                    )
                    st.info("✅ `review_content` 메서드로 fallback 완료 (레이어 구조 아님)")
                    return corrected_result
                except Exception as e:
                    # 기타 예외도 fallback
                    st.error(f"❌ `correct_problem` 메서드 호출 중 예외 발생: {str(e)}")
                    st.warning("⚠️ 기존 `review_content` 메서드로 전환합니다.")
                    
                    # 세션 상태에 fallback 정보 저장
                    if "correction_method_used" not in st.session_state:
                        st.session_state.correction_method_used = []
                    st.session_state.correction_method_used.append({
                        "method": "review_content (fallback)",
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    corrected_result = self.gemini_client.review_content(
                        system_prompt=system_prompt,
                        user_prompt=user_prompt
                    )
                    st.info("✅ `review_content` 메서드로 fallback 완료 (레이어 구조 아님)")
                    return corrected_result
            
            # 새로운 메서드를 사용할 수 없는 경우 기존 메서드 사용 (원래 방식)
            st.warning("⚠️ 기존 `review_content` 메서드 사용 중 (일반 텍스트 응답)")
            st.info("💡 이 메서드는 레이어 구조가 아닌 일반 형식으로 응답합니다.")
            
            # 세션 상태에 메서드 사용 정보 저장
            if "correction_method_used" not in st.session_state:
                st.session_state.correction_method_used = []
            st.session_state.correction_method_used.append({
                "method": "review_content",
                "reason": "NEW_GENAI_AVAILABLE이 False이거나 correct_problem 메서드가 없음",
                "timestamp": datetime.now().isoformat()
            })
            
            corrected_result = self.gemini_client.review_content(
                system_prompt=system_prompt,
                user_prompt=user_prompt
            )
            st.info("✅ `review_content` 메서드 호출 완료")
            return corrected_result
            
        except Exception as e:
            return f"❌ 문제 교정 중 오류가 발생했습니다: {str(e)}"
    
    def is_available(self) -> bool:
        """문제 교정 서비스 사용 가능 여부 확인"""
        return self.gemini_client is not None and GEMINI_AVAILABLE
    
    def auto_correct_questions(self, questions: list, question_type: str = "subjective") -> dict:
        """
        여러 문제를 자동으로 교정합니다.
        
        Args:
            questions: 교정할 문제 리스트
            question_type: 문제 유형 ('multiple_choice' 또는 'subjective')
            
        Returns:
            dict: 교정 결과 통계
        """
        results = {
            "total": len(questions),
            "success": 0,
            "failed": 0,
            "details": []
        }
        
        for question in questions:
            try:
                # 문제를 JSON으로 변환
                question_json = json.dumps(question, ensure_ascii=False, indent=2)
                
                # 교정 실행
                corrected_result = self.correct_problem(question_json, question_type)
                
                # 결과 저장
                results["details"].append({
                    "question_id": question.get("id"),
                    "status": "success",
                    "corrected_result": corrected_result
                })
                results["success"] += 1
                
            except Exception as e:
                results["details"].append({
                    "question_id": question.get("id"),
                    "status": "failed",
                    "error": str(e)
                })
                results["failed"] += 1
        
        return results