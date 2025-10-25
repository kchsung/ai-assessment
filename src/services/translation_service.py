import json
from typing import Dict, List, Any
from src.services.gemini_client import GeminiClient
from src.services.edge_client import EdgeDBClient

class TranslationService:
    def __init__(self, gemini_client: GeminiClient, edge_client: EdgeDBClient):
        self.gemini_client = gemini_client
        self.edge_client = edge_client
        self.TRANSLATION_PROMPT_ID = "335175d3-ea19-4e47-9d47-1edb798a3a72"

    def translate_problem(self, problem: Dict) -> Dict:
        """
        문제 데이터를 영어로 번역 (전체 JSON을 한 번에 번역)
        
        Args:
            problem: qlearn_problems 테이블의 문제 데이터
            
        Returns:
            번역된 문제 데이터
        """
        try:
            
            # 전체 문제 데이터를 JSON으로 변환
            problem_json = json.dumps(problem, ensure_ascii=False, indent=2)
            
            # 제미나이 API로 전체 JSON 번역
            system_prompt = self._get_translation_prompt()
            user_prompt = f"Translate the following Korean problem data to English:\n\n{problem_json}"
            
            translated = self.gemini_client.review_content(system_prompt, user_prompt)
            
            if translated and isinstance(translated, str):
                result = translated.strip()
                
                # JSON 형태의 응답인 경우 파싱 시도
                if '```json' in result:
                    try:
                        # ```json과 ``` 사이의 내용 추출
                        start_idx = result.find('```json') + 7
                        end_idx = result.find('```', start_idx)
                        if end_idx == -1:
                            json_content = result[start_idx:].strip()
                        else:
                            json_content = result[start_idx:end_idx].strip()
                        
                        
                        # JSON 파싱 시도
                        parsed = json.loads(json_content)
                        
                        # 번역된 데이터를 i18n 형식으로 변환
                        # subjective 타입으로 고정 (questions_subjective 테이블에서만 가져옴)
                        source_id = problem.get('id')
                        
                        translated_problem = {
                            'source_problem_id': source_id,
                            'lang': 'en',
                            'category': parsed.get('category', problem.get('category', problem.get('domain'))),
                            'topic': parsed.get('topic', problem.get('topic', '')),
                            'difficulty': parsed.get('difficulty', problem.get('difficulty')),
                            'time_limit': parsed.get('time_limit', problem.get('time_limit', '')),
                            'topic_summary': parsed.get('topic_summary', ''),
                            'title': parsed.get('title', ''),
                            'scenario': parsed.get('scenario', ''),
                            'goal': parsed.get('goal', []),
                            'first_question': parsed.get('first_question', []),
                            'requirements': parsed.get('requirements', []),
                            'constraints': parsed.get('constraints', []),
                            'guide': parsed.get('guide', {}),
                            'evaluation': parsed.get('evaluation', []),
                            'task': parsed.get('task', ''),
                            'reference': parsed.get('reference', {}),
                            'active': True
                        }
                        
                        return translated_problem
                        
                    except json.JSONDecodeError as e:
                        return self._create_fallback_translation(problem)
                else:
                    return self._create_fallback_translation(problem)
            else:
                return self._create_fallback_translation(problem)
                
        except Exception as e:
            return self._create_fallback_translation(problem)
    
    def _create_fallback_translation(self, problem: dict) -> dict:
        """번역 실패 시 원본 데이터를 사용한 폴백 번역"""
        # subjective 타입으로 고정 (questions_subjective 테이블에서만 가져옴)
        
        return {
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

    def _get_translation_prompt(self) -> str:
        """번역용 프롬프트를 데이터베이스에서 조회"""
        try:
            prompt = self.edge_client.get_prompt_by_id(self.TRANSLATION_PROMPT_ID)
            
            # 응답이 문자열인 경우 (직접 프롬프트 텍스트)
            if prompt and isinstance(prompt, str):
                return prompt
            
            # 응답이 딕셔너리인 경우
            if prompt and isinstance(prompt, dict):
                prompt_text = prompt.get('prompt_text', '')
                if prompt_text:
                    return prompt_text
            
            return self._get_default_translation_prompt()
        except Exception as e:
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

    def save_translated_problem(self, translated_problem: dict) -> bool:
        """번역된 문제를 i18n 테이블에 저장"""
        try:
            # 필수 필드 존재 여부 확인
            required_fields = ['source_problem_id', 'lang', 'category', 'topic', 'difficulty', 
                             'time_limit', 'topic_summary', 'title', 'scenario', 'task', 'active']
            missing_fields = [field for field in required_fields if field not in translated_problem]
            
            if missing_fields:
                error_msg = f"필수 필드 누락: {missing_fields}"
                raise ValueError(error_msg)
            
            # Edge Function을 통해 저장 (이미 en 필드 업데이트 로직이 포함됨)
            success = self.edge_client.save_i18n_problem(translated_problem)
            
            if success:
                return True
            else:
                error_msg = f"Edge Function에서 저장 실패 응답: {translated_problem.get('source_problem_id')}"
                raise RuntimeError(error_msg)
                
        except Exception as e:
            error_msg = f"저장 중 오류 발생: {str(e)}"
            raise RuntimeError(error_msg)

    def translate_and_save_problem(self, problem: dict, debug_callback=None) -> dict:
        """문제를 번역하고 저장하는 전체 프로세스"""
        debug_info = {
            "steps": [],
            "errors": [],
            "success": False,
            "translated_problem": None
        }
        
        def update_debug(step, error=None):
            if step:
                debug_info["steps"].append(step)
            if error:
                debug_info["errors"].append(error)
            if debug_callback:
                debug_callback(debug_info)
        
        try:
            step_info = f"🔄 번역 시작: {problem.get('title', 'Unknown')[:50]}..."
            update_debug(step_info)
            
            # 1단계: 문제 번역
            step_info = "📝 1단계: 문제 번역 중..."
            update_debug(step_info)
            
            translated_problem = self.translate_problem(problem)
            
            if not translated_problem:
                update_debug(None, "문제 번역 실패")
                raise RuntimeError("문제 번역 실패")
            
            step_info = "✅ 1단계 완료: 문제 번역 성공"
            update_debug(step_info)
            
            # 2단계: i18n 테이블에 저장
            step_info = "💾 2단계: i18n 테이블 저장 중..."
            update_debug(step_info)
            
            save_success = self.save_translated_problem(translated_problem)
            
            if not save_success:
                update_debug(None, "번역된 문제 저장 실패")
                raise RuntimeError("번역된 문제 저장 실패")
            
            step_info = "✅ 2단계 완료: i18n 테이블 저장 성공"
            update_debug(step_info)
            
            success_msg = f"🎉 번역 완료: {problem.get('title', 'Unknown')[:50]}..."
            update_debug(success_msg)
            
            debug_info["success"] = True
            debug_info["translated_problem"] = translated_problem
            
            return translated_problem
            
        except Exception as e:
            error_msg = f"❌ 번역 및 저장 실패: {str(e)}"
            update_debug(None, error_msg)
            raise RuntimeError(f"문제 번역 및 저장 실패: {str(e)}")
