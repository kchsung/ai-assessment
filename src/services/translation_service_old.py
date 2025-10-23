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
            print(f"🔄 문제 번역 시작 - 원본 문제 ID: {problem.get('id')}")
            print(f"📋 원본 문제 정보:")
            print(f"   - 제목: {problem.get('title', '')[:50]}...")
            print(f"   - 카테고리: {problem.get('category', problem.get('domain', 'N/A'))}")
            print(f"   - 난이도: {problem.get('difficulty', 'N/A')}")
            
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
            
            print(f"🔧 번역할 필드들: {fields_to_translate}")
            print(f"🔧 JSON 배열 필드들: {json_array_fields}")
            print(f"🔧 JSON 객체 필드들: {json_object_fields}")
            
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
            
            print(f"📝 번역된 문제 데이터 구조 초기화 완료")
            
            # time_limit 번역 (숫자만 그대로, 나머지 형식 유지)
            if 'time_limit' in problem and problem['time_limit']:
                print(f"⏰ time_limit 번역 중: {problem['time_limit']}")
                translated_problem['time_limit'] = self._translate_time_limit(problem['time_limit'])
            
            # 일반 텍스트 필드들 번역
            print(f"📝 일반 텍스트 필드 번역 시작...")
            # 프롬프트를 한 번만 조회
            system_prompt = self._get_translation_prompt()
            for field in fields_to_translate:
                if field in problem and problem[field]:
                    print(f"   🔄 {field} 필드 번역 중...")
                    try:
                        translated_text = self._translate_text(problem[field], system_prompt)
                        translated_problem[field] = translated_text
                        print(f"   ✅ {field} 필드 번역 완료: {translated_text[:30]}...")
                    except Exception as e:
                        print(f"   ❌ {field} 필드 번역 실패: {e}")
                        translated_problem[field] = problem[field]  # 원본 유지
                else:
                    print(f"   ⏭️ {field} 필드 건너뛰기 (값 없음)")
            
            # JSON 배열 필드들 번역
            print(f"📝 JSON 배열 필드 번역 시작...")
            for field in json_array_fields:
                if field in problem and problem[field]:
                    print(f"   🔄 {field} 필드 번역 중...")
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
                            print(f"   ⚠️ {field} 필드 JSON 파싱 실패, 원본 유지")
                            translated_problem[field] = problem[field]
                else:
                    print(f"   ⏭️ {field} 필드 건너뛰기 (값 없음)")
            
            # JSON 객체 필드들 번역
            print(f"📝 JSON 객체 필드 번역 시작...")
            for field in json_object_fields:
                if field in problem and problem[field]:
                    print(f"   🔄 {field} 필드 번역 중...")
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
                            print(f"   ⚠️ {field} 필드 JSON 파싱 실패, 원본 유지")
                            translated_problem[field] = problem[field]
                else:
                    print(f"   ⏭️ {field} 필드 건너뛰기 (값 없음)")
            
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

    def _translate_text(self, text: str, system_prompt: str = None) -> str:
        """텍스트를 영어로 번역"""
        if not text or not text.strip():
            print(f"🔍 빈 텍스트 건너뛰기: '{text}'")
            return text or ""
        
        print(f"🌐 제미나이 API 호출 시작 - 텍스트: '{text[:50]}{'...' if len(text) > 50 else ''}'")
        
        # 프롬프트가 제공되지 않은 경우에만 조회
        if not system_prompt:
            system_prompt = self._get_translation_prompt()
        
        user_prompt = f"Translate this Korean text to English:\n\n{text}"
        
        # 간단한 타임아웃 체크를 위한 시간 기록
        import time
        start_time = time.time()
        
        try:
            print(f"📤 제미나이 API 요청 전송 중...")
            translated = self.gemini_client.review_content(system_prompt, user_prompt)
            
            if translated and isinstance(translated, str):
                result = translated.strip()
                print(f"✅ 제미나이 API 응답 성공 - 번역 결과: '{result[:50]}{'...' if len(result) > 50 else ''}'")
                
                # JSON 형태의 응답인 경우 파싱 시도
                if '```json' in result:
                    try:
                        # ```json과 ``` 사이의 내용 추출
                        start_idx = result.find('```json') + 7
                        end_idx = result.find('```', start_idx)
                        if end_idx == -1:
                            # ```가 없는 경우 끝까지 사용
                            json_content = result[start_idx:].strip()
                        else:
                            json_content = result[start_idx:end_idx].strip()
                        
                        print(f"🔍 추출된 JSON 내용: {json_content[:100]}...")
                        
                        # JSON 파싱 시도
                        parsed = json.loads(json_content)
                        
                        # 다양한 필드에서 번역 결과 찾기
                        if 'translation' in parsed:
                            translation = parsed['translation']
                            print(f"✅ JSON에서 'translation' 필드 추출: {translation[:50]}...")
                            return translation
                        elif 'title' in parsed:
                            translation = parsed['title']
                            print(f"✅ JSON에서 'title' 필드 추출: {translation[:50]}...")
                            return translation
                        elif 'text' in parsed:
                            translation = parsed['text']
                            print(f"✅ JSON에서 'text' 필드 추출: {translation[:50]}...")
                            return translation
                        else:
                            print(f"⚠️ JSON에 번역 필드가 없음, 첫 번째 문자열 값 사용")
                            # 첫 번째 문자열 값 찾기
                            for key, value in parsed.items():
                                if isinstance(value, str) and value.strip():
                                    print(f"✅ JSON에서 '{key}' 필드 추출: {value[:50]}...")
                                    return value
                            print(f"⚠️ JSON에 유효한 문자열 값이 없음, 원본 응답 사용")
                            return result
                    except json.JSONDecodeError as e:
                        print(f"⚠️ JSON 파싱 실패: {e}")
                        print(f"⚠️ 원본 응답 사용: {result[:100]}...")
                        return result
                else:
                    return result
            else:
                print(f"❌ 제미나이 API 응답이 유효하지 않음: {translated}")
                return text  # 번역 실패 시 원본 반환
        except Exception as e:
            print(f"❌ 제미나이 API 호출 실패: {e}")
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
            print(f"💾 데이터베이스 저장 시작 - 문제 ID: {translated_problem.get('source_problem_id')}")
            
            db = st.session_state.get("db")
            if not db:
                print("❌ 데이터베이스 연결이 없습니다.")
                return False
            
            print(f"📊 저장할 데이터 구조:")
            print(f"   - source_problem_id: {translated_problem.get('source_problem_id')}")
            print(f"   - lang: {translated_problem.get('lang')}")
            print(f"   - category: {translated_problem.get('category')}")
            print(f"   - topic: {translated_problem.get('topic', '')[:50]}...")
            print(f"   - difficulty: {translated_problem.get('difficulty')}")
            print(f"   - time_limit: {translated_problem.get('time_limit')}")
            print(f"   - topic_summary: {translated_problem.get('topic_summary', '')[:50]}...")
            print(f"   - title: {translated_problem.get('title', '')[:50]}...")
            print(f"   - scenario: {translated_problem.get('scenario', '')[:50]}...")
            print(f"   - task: {translated_problem.get('task', '')[:50]}...")
            print(f"   - active: {translated_problem.get('active')}")
            
            # 필수 필드 검증
            required_fields = ['source_problem_id', 'lang', 'category', 'topic', 'difficulty', 'time_limit', 'topic_summary', 'title', 'scenario', 'task']
            missing_fields = [field for field in required_fields if not translated_problem.get(field)]
            if missing_fields:
                print(f"⚠️ 필수 필드 누락: {missing_fields}")
            else:
                print(f"✅ 모든 필수 필드 존재")
            
            # i18n 테이블에 저장
            print(f"🔄 Edge Function 호출 중...")
            success = db.save_i18n_problem(translated_problem)
            
            if success:
                print(f"✅ 번역된 문제 저장 완료: {translated_problem.get('source_problem_id')}")
            else:
                print(f"❌ 번역된 문제 저장 실패: {translated_problem.get('source_problem_id')}")
            
            return success
            
        except Exception as e:
            print(f"❌ 번역된 문제 저장 중 오류 발생: {e}")
            return False


    def translate_and_save_problem(self, problem: Dict) -> Dict:
        """문제를 번역하고 i18n 테이블에 저장"""
        try:
            if not problem:
                raise RuntimeError("번역할 문제 데이터가 없습니다")
            
            print(f"🔄 번역 시작: {problem.get('title', 'Unknown')[:50]}...")
            
            # 1. 문제 번역
            print("📝 1단계: 문제 번역 중...")
            translated_problem = self.translate_problem(problem)
            
            if not translated_problem:
                raise RuntimeError("문제 번역 실패")
            
            print("✅ 1단계 완료: 문제 번역 성공")
            
            # 2. i18n 테이블에 저장
            print("💾 2단계: i18n 테이블에 저장 중...")
            save_success = self.save_translated_problem(translated_problem)
            
            if not save_success:
                raise RuntimeError("번역된 문제 저장 실패")
            
            print("✅ 2단계 완료: i18n 테이블 저장 성공")
            print(f"🎉 번역 완료: {problem.get('title', 'Unknown')[:50]}...")
            print(f"🏁 번역 프로세스 완전 종료")
            return translated_problem
            
        except Exception as e:
            print(f"❌ 번역 및 저장 실패: {str(e)}")
            raise RuntimeError(f"문제 번역 및 저장 실패: {str(e)}")

    def is_available(self) -> bool:
        """번역 서비스 사용 가능 여부 확인"""
        return self.gemini_client.is_available()
