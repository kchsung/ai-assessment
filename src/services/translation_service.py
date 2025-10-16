"""
제미나이 번역 서비스
"""
import json
import re
from typing import Dict, List, Optional
from src.services.gemini_client import GeminiClient

class TranslationService:
    def __init__(self):
        self.gemini_client = GeminiClient()
    
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
            
            # 번역된 문제 데이터 초기화
            translated_problem = problem.copy()
            translated_problem['lang'] = 'en'
            translated_problem['is_en'] = True
            
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
            
            return translated_problem
            
        except Exception as e:
            raise RuntimeError(f"문제 번역 실패: {str(e)}")
    
    def _translate_text(self, text: str) -> str:
        """텍스트를 영어로 번역"""
        if not text or not text.strip():
            return text
        
        system_prompt = """You are a professional translator specializing in educational content. 
Translate the following Korean text to English while maintaining:
1. Technical accuracy and educational context
2. Professional tone appropriate for learning materials
3. Clear and concise language
4. Original formatting and structure

Return only the translated text without any additional explanations or comments."""
        
        user_prompt = f"Translate this Korean text to English:\n\n{text}"
        
        try:
            translated = self.gemini_client.review_content(system_prompt, user_prompt)
            return translated.strip()
        except Exception as e:
            print(f"번역 실패: {e}")
            return text  # 번역 실패 시 원본 반환
    
    def _translate_time_limit(self, time_limit: str) -> str:
        """시간 제한 텍스트 번역 (숫자만 그대로, 나머지 형식 유지)"""
        if not time_limit:
            return time_limit
        
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
            return obj
        
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
    
    def is_available(self) -> bool:
        """번역 서비스 사용 가능 여부 확인"""
        return self.gemini_client.is_available()
