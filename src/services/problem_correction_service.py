"""
문제 교정 서비스
"""
import streamlit as st
import json
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
    
    def get_correction_prompt(self, category: str = None) -> str:
        """
        Supabase prompts 테이블에서 교정 프롬프트를 가져옵니다.
        
        Args:
            category: 프롬프트 카테고리 (learning_concept 등)
            
        Returns:
            str: 교정 프롬프트
        """
        try:
            # print(f"🔍 get_correction_prompt 호출됨 - category: '{category}'")
            
            db = st.session_state.get("db")
            if not db:
                # print("❌ 데이터베이스 연결이 없습니다. 기본 프롬프트를 사용합니다.")
                return DEFAULT_PROBLEM_CORRECTION_PROMPT
            
            # learning_concept 카테고리인 경우 특별 ID 사용
            if category == "learning_concept":
                # print(f"🎯 learning_concept 카테고리 감지됨!")
                # print(f"🔍 LEARNING_CONCEPT_PROMPT_ID: {LEARNING_CONCEPT_PROMPT_ID}")
                
                prompt = db.get_prompt_by_id(LEARNING_CONCEPT_PROMPT_ID)
                if prompt:
                    # print(f"✅ learning_concept 카테고리용 프롬프트 사용 성공: {LEARNING_CONCEPT_PROMPT_ID}")
                    # print(f"📝 프롬프트 길이: {len(prompt) if prompt else 0} 문자")
                    return prompt
                else:
                    # print(f"❌ learning_concept 프롬프트를 찾을 수 없습니다. 기본 프롬프트를 사용합니다.")
                    return DEFAULT_PROBLEM_CORRECTION_PROMPT
            
            # 카테고리가 지정된 경우 해당 카테고리의 프롬프트 조회
            if category:
                prompts = db.get_prompts(category=category)
                if prompts and len(prompts) > 0:
                    # print(f"카테고리 '{category}'의 프롬프트 사용")
                    return prompts[0].get('prompt_text', DEFAULT_PROBLEM_CORRECTION_PROMPT)
            
            # 기본 프롬프트 사용
            # print("기본 교정 프롬프트 사용")
            return DEFAULT_PROBLEM_CORRECTION_PROMPT
            
        except Exception as e:
            # print(f"프롬프트 조회 중 오류 발생: {e}")
            return DEFAULT_PROBLEM_CORRECTION_PROMPT
    
    def correct_problem(self, problem_json: str, category: str = None) -> str:
        """
        문제 JSON을 교정합니다.
        
        Args:
            problem_json: 교정할 문제의 JSON 문자열
            category: 프롬프트 카테고리
            
        Returns:
            str: 교정된 문제의 JSON 문자열
        """
        if not self.gemini_client:
            error_msg = "❌ 제미나이 API를 사용할 수 없습니다."
            if self.initialization_error:
                error_msg += f"\n\n오류 상세: {self.initialization_error}"
            return error_msg
        
        try:
            # 교정 프롬프트 가져오기
            system_prompt = self.get_correction_prompt(category)
            
            # 사용자 프롬프트 구성
            user_prompt = f"다음 문제 JSON을 교정해주세요:\n\n{problem_json}"
            
            # 제미나이 API 호출
            corrected_result = self.gemini_client.review_content(
                system_prompt=system_prompt,
                user_prompt=user_prompt
            )
            
            # print(f"DEBUG: 문제 교정 결과 길이: {len(corrected_result) if corrected_result else 0}")
            return corrected_result
            
        except Exception as e:
            return f"❌ 문제 교정 중 오류가 발생했습니다: {str(e)}"
    
    def is_available(self) -> bool:
        """문제 교정 서비스 사용 가능 여부 확인"""
        return self.gemini_client is not None and GEMINI_AVAILABLE
    
    def auto_correct_questions(self, questions: list, category: str = None) -> dict:
        """
        여러 문제를 자동으로 교정합니다.
        
        Args:
            questions: 교정할 문제 리스트
            category: 프롬프트 카테고리
            
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
                corrected_result = self.correct_problem(question_json, category)
                
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