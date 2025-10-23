"""
제미나이 번역 서비스
"""
import json
import re
import streamlit as st
from typing import Dict, List, Optional
from src.services.gemini_client import GeminiClient

class TranslationService:
    def __init__(self):
        self.gemini_client = GeminiClient()
        # 번역용 프롬프트 ID
        self.TRANSLATION_PROMPT_ID = "335175d3-ea19-4e47-9d47-1edb798a3a72"
    
    def translate_problem(self, problem: Dict) -> Dict:
        """
        문제 데이터를 영어로 번역
        
        Args:
            problem: qlearn_problems 테이블의 문제 데이터
            
        Returns:
            번역된 문제 데이터
        """
        try:
            # 번역할 필드들 정의
            fields_to_translate = [
                'title', 'scenario', 'task', 'topic_summary'
            ]
            
            # JSON 배열 필드들
            json_array_fields = [
                'goal', 'first_question', 'requirements', 'constraints', 'evaluation'
            ]
            
            # JSON 객체 필드들
            json_object_fields = [
                'guide', 'reference'
            ]
            
            # 번역된 문제 데이터 초기화 (i18n 테이블 구조에 맞게)
            translated_problem = {
                'source_problem_id': problem.get('id'),
                'lang': 'en',
                'category': problem.get('category', problem.get('domain')),
                'topic': problem.get('topic', ''),
                'difficulty': problem.get('difficulty'),
                'time_limit': problem.get('time_limit', ''),
                'topic_summary': problem.get('topic_summary', ''),
                'title': problem.get('title', ''),
                'scenario': problem.get('scenario', ''),
                'goal': problem.get('goal', []),
                'first_question': problem.get('first_question', []),
                'requirements': problem.get('requirements', []),
                'constraints': problem.get('constraints', []),
                'guide': problem.get('guide', {}),
                'evaluation': problem.get('evaluation', []),
                'task': problem.get('task', ''),
                'reference': problem.get('reference', {}),
                'active': True
            }
            
            # time_limit 번역 (숫자만 그대로, 나머지 형식 유지)
            if 'time_limit' in problem and problem['time_limit']:
                translated_problem['time_limit'] = self._translate_time_limit(problem['time_limit'])
            
            # 일반 텍스트 필드들 번역
            for field in fields_to_translate:
                if field in problem and problem[field]:
                    translated_problem[field] = self._translate_text(problem[field])
            
            # JSON 배열 필드들 번역
            for field in json_array_fields:
                if field in problem and problem[field]:
                    if isinstance(problem[field], list):
                        translated_problem[field] = [
                            self._translate_text(item) if isinstance(item, str) else item
                            for item in problem[field]
                        ]
                    else:
                        # JSON 문자열인 경우 파싱 후 번역
                        try:
                            data = json.loads(problem[field]) if isinstance(problem[field], str) else problem[field]
                            if isinstance(data, list):
                                translated_problem[field] = [
                                    self._translate_text(item) if isinstance(item, str) else item
                                    for item in data
                                ]
                        except (json.JSONDecodeError, TypeError):
                            # 파싱 실패 시 원본 유지
                            translated_problem[field] = problem[field]
            
            # JSON 객체 필드들 번역
            for field in json_object_fields:
                if field in problem and problem[field]:
                    if isinstance(problem[field], dict):
                        translated_problem[field] = self._translate_json_object(problem[field])
                    else:
                        # JSON 문자열인 경우 파싱 후 번역
                        try:
                            data = json.loads(problem[field]) if isinstance(problem[field], str) else problem[field]
                            if isinstance(data, dict):
                                translated_problem[field] = self._translate_json_object(data)
                        except (json.JSONDecodeError, TypeError):
                            # 파싱 실패 시 원본 유지
                            translated_problem[field] = problem[field]
            
            # 번역된 문제가 유효한지 확인
            if not translated_problem or not isinstance(translated_problem, dict):
                raise RuntimeError("번역된 문제 데이터가 유효하지 않습니다")
            
            return translated_problem
            
        except Exception as e:
            print(f"❌ 문제 번역 실패: {str(e)}")
            raise RuntimeError(f"문제 번역 실패: {str(e)}")
    
    def _get_translation_prompt(self) -> str:
        """데이터베이스에서 번역용 프롬프트를 가져옵니다."""
        try:
            # streamlit이 실행 중인지 확인
            import streamlit as st
            if not hasattr(st, 'session_state'):
                return self._get_default_translation_prompt()
            
            db = st.session_state.get("db")
            if not db:
                print("❌ 데이터베이스 연결이 없습니다. 기본 프롬프트를 사용합니다.")
                return self._get_default_translation_prompt()
            
            prompt = db.get_prompt_by_id(self.TRANSLATION_PROMPT_ID)
            if prompt:
                print(f"✅ 번역용 프롬프트 사용: {self.TRANSLATION_PROMPT_ID}")
                return prompt
            else:
                print(f"❌ 번역용 프롬프트를 찾을 수 없습니다 (ID: {self.TRANSLATION_PROMPT_ID}). 기본 프롬프트를 사용합니다.")
                return self._get_default_translation_prompt()
        except Exception as e:
            print(f"❌ 번역용 프롬프트 조회 실패: {e}. 기본 프롬프트를 사용합니다.")
            return self._get_default_translation_prompt()
    
    def _get_default_translation_prompt(self) -> str:
        """기본 번역 프롬프트를 반환합니다."""
        return """You are a professional translator specializing in educational content. 
Translate the following Korean text to English while maintaining:
1. Technical accuracy and educational context
2. Professional tone appropriate for learning materials
3. Clear and concise language
4. Original formatting and structure

Return only the translated text without any additional explanations or comments."""

    def _translate_text(self, text: str) -> str:
        """텍스트를 영어로 번역"""
        if not text or not text.strip():
            return text or ""
        
        system_prompt = self._get_translation_prompt()
        user_prompt = f"Translate this Korean text to English:\n\n{text}"
        
        try:
            translated = self.gemini_client.review_content(system_prompt, user_prompt)
            if translated and isinstance(translated, str):
                return translated.strip()
            else:
                print(f"번역 결과가 유효하지 않음: {translated}")
                return text  # 번역 실패 시 원본 반환
        except Exception as e:
            print(f"번역 실패: {e}")
            return text  # 번역 실패 시 원본 반환
    
    def _translate_time_limit(self, time_limit: str) -> str:
        """시간 제한 텍스트 번역 (숫자만 그대로, 나머지 형식 유지)"""
        if not time_limit:
            return time_limit or ""
        
        # 숫자 추출
        numbers = re.findall(r'\d+', time_limit)
        
        if not numbers:
            return time_limit
        
        # "분 이내" 패턴을 "minutes"로 번역
        if "분 이내" in time_limit:
            return f"within {numbers[0]} minutes"
        elif "분" in time_limit:
            return f"{numbers[0]} minutes"
        else:
            # 다른 패턴의 경우 전체 번역
            return self._translate_text(time_limit)
    
    def _translate_json_object(self, obj: Dict) -> Dict:
        """JSON 객체의 모든 문자열 값들을 번역"""
        if not isinstance(obj, dict):
            return obj or {}
        
        translated_obj = {}
        for key, value in obj.items():
            if isinstance(value, str):
                translated_obj[key] = self._translate_text(value)
            elif isinstance(value, dict):
                translated_obj[key] = self._translate_json_object(value)
            elif isinstance(value, list):
                translated_obj[key] = [
                    self._translate_text(item) if isinstance(item, str) else item
                    for item in value
                ]
            else:
                translated_obj[key] = value
        
        return translated_obj
    
    def batch_translate_problems(self, problems: List[Dict]) -> List[Dict]:
        """여러 문제를 일괄 번역"""
        translated_problems = []
        
        for i, problem in enumerate(problems):
            try:
                print(f"번역 진행 중: {i+1}/{len(problems)} - {problem.get('title', 'Unknown')[:50]}...")
                translated = self.translate_problem(problem)
                translated_problems.append(translated)
            except Exception as e:
                print(f"문제 {i+1} 번역 실패: {e}")
                # 번역 실패한 문제는 원본 유지하되 is_en을 True로 설정
                failed_problem = problem.copy()
                failed_problem['is_en'] = True
                translated_problems.append(failed_problem)
        
        return translated_problems
    
    def save_translated_problem(self, translated_problem: Dict) -> bool:
        """번역된 문제를 i18n 테이블에 저장"""
        try:
            db = st.session_state.get("db")
            if not db:
                print("❌ 데이터베이스 연결이 없습니다.")
                return False
            
            # i18n 테이블에 저장
            success = db.save_i18n_problem(translated_problem)
            
            if success:
                print(f"✅ 번역된 문제 저장 완료: {translated_problem.get('source_problem_id')}")
            else:
                print(f"❌ 번역된 문제 저장 실패: {translated_problem.get('source_problem_id')}")
            
            return success
            
        except Exception as e:
            print(f"❌ 번역된 문제 저장 중 오류 발생: {e}")
            return False

    def update_translation_status(self, question_id: str, question_type: str) -> bool:
        """번역 완료 후 question_status 테이블의 translation_done을 True로 업데이트"""
        try:
            db = st.session_state.get("db")
            if not db:
                print("❌ 데이터베이스 연결이 없습니다.")
                return False
            
            # question_status 테이블 업데이트
            success = db.update_question_status(question_id, {
                "translation_done": True
            })
            
            if success:
                print(f"✅ 번역 상태 업데이트 완료: {question_id}")
            else:
                print(f"❌ 번역 상태 업데이트 실패: {question_id}")
            
            return success
            
        except Exception as e:
            print(f"❌ 번역 상태 업데이트 중 오류 발생: {e}")
            return False

    def translate_and_save_problem(self, problem: Dict) -> Dict:
        """문제를 번역하고 i18n 테이블에 저장한 후 상태를 업데이트"""
        try:
            if not problem:
                raise RuntimeError("번역할 문제 데이터가 없습니다")
            
            # 1. 문제 번역
            translated_problem = self.translate_problem(problem)
            
            if not translated_problem:
                raise RuntimeError("문제 번역 실패")
            
            # 2. i18n 테이블에 저장
            save_success = self.save_translated_problem(translated_problem)
            
            if not save_success:
                raise RuntimeError("번역된 문제 저장 실패")
            
            # 3. 번역 상태 업데이트
            question_type = "subjective" if "topic" in problem else "multiple_choice"
            status_success = self.update_translation_status(problem.get('id'), question_type)
            
            if not status_success:
                print(f"⚠️ 번역 상태 업데이트 실패: {problem.get('id')}")
            
            return translated_problem
            
        except Exception as e:
            print(f"❌ 번역 및 저장 실패: {str(e)}")
            raise RuntimeError(f"문제 번역 및 저장 실패: {str(e)}")

    def is_available(self) -> bool:
        """번역 서비스 사용 가능 여부 확인"""
        return self.gemini_client.is_available()
