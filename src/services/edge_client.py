import os
import requests

class EdgeDBClient:
    def __init__(self, base_url: str | None, token: str | None, supabase_anon: str | None):
        self.base_url = base_url or os.getenv("EDGE_FUNCTION_URL")
        self.token = token or os.getenv("EDGE_SHARED_TOKEN")
        self.supabase_anon = supabase_anon or os.getenv("SUPABASE_ANON_KEY")
        if not self.base_url:
            raise RuntimeError("EDGE_FUNCTION_URL not set")
        if not self.token:
            raise RuntimeError("EDGE_SHARED_TOKEN not set")
        
        # 연결 테스트
        self._test_connection()
    
    def _test_connection(self):
        """Edge Function 연결 테스트"""
        try:
            # 간단한 연결 테스트 (get_questions 액션 사용)
            headers = {
                "content-type": "application/json",
                "x-edge-token": self.token,
            }
            if self.supabase_anon:
                headers["authorization"] = f"Bearer {self.supabase_anon}"
            
            payload = {"action": "get_questions", "params": {}}
            
            resp = requests.post(
                self.base_url, 
                headers=headers, 
                json=payload,
                timeout=10
            )
            
            if resp.status_code >= 400:
                raise RuntimeError(f"Edge Function 연결 실패 (HTTP {resp.status_code}): {resp.text}")
                
        except requests.exceptions.ConnectionError as e:
            raise RuntimeError(f"Edge Function에 연결할 수 없습니다. URL을 확인하세요: {self.base_url}")
        except requests.exceptions.Timeout as e:
            raise RuntimeError(f"Edge Function 연결 시간 초과: {self.base_url}")
        except Exception as e:
            # 연결 테스트가 실패해도 다른 액션은 시도해볼 수 있도록 경고만 출력
            pass

    def _call(self, action: str, params: dict | None = None, timeout: int = 30, max_retries: int = 3):
        headers = {
            "content-type": "application/json",
            "x-edge-token": self.token,
        }
        if self.supabase_anon:
            headers["authorization"] = f"Bearer {self.supabase_anon}"

        payload = {"action": action, "params": params or {}}
        
        # 재시도 로직
        for attempt in range(max_retries):
            try:
                resp = requests.post(
                    self.base_url, 
                    headers=headers, 
                    json=payload,
                    timeout=timeout,
                    stream=False  # 스트리밍 비활성화로 연결 안정성 향상
                )
                
                if resp.status_code >= 400:
                    raise RuntimeError(f"Edge error {resp.status_code}: {resp.text}")
                
                # JSON 파싱 시도
                try:
                    data = resp.json()
                except ValueError as e:
                    # 응답 텍스트의 일부만 표시 (너무 길면 잘라냄)
                    response_preview = resp.text[:500] + "..." if len(resp.text) > 500 else resp.text
                    raise RuntimeError(f"Edge JSON parse error: {e}, Response preview: {response_preview}")
                
                if not data.get("ok"):
                    raise RuntimeError(f"Edge failure: {data.get('error')}")
                
                return data.get("data")
                
            except (requests.exceptions.ChunkedEncodingError, 
                    requests.exceptions.ConnectionError,
                    requests.exceptions.Timeout) as e:
                if attempt < max_retries - 1:
                    import time
                    time.sleep(2 ** attempt)  # 지수 백오프
                    continue
                else:
                    raise RuntimeError(f"네트워크 오류로 인한 요청 실패 (최대 재시도 횟수 초과): {e}")
            except Exception as e:
                raise RuntimeError(f"예상치 못한 오류: {e}")
    

    # API
    def save_question(self, q: dict) -> bool:
        try:
            result = self._call("save_question", q)
            return True
        except Exception as e:
            raise e

    def get_questions(self, filters: dict | None = None):
        return self._call("get_questions", filters or {}) or []

    # 새로운 테이블 분리 메서드들
    def save_multiple_choice_question(self, question: dict) -> bool:
        """객관식 문제 저장"""
        try:
            result = self._call("save_multiple_choice_question", question)
            return True
        except Exception as e:
            raise e

    def save_subjective_question(self, question: dict) -> bool:
        """주관식 문제 저장"""
        try:
            result = self._call("save_subjective_question", question)
            return True
        except Exception as e:
            raise e

    def get_multiple_choice_questions(self, filters: dict | None = None):
        """객관식 문제 조회"""
        return self._call("get_multiple_choice_questions", filters or {}) or []

    def get_subjective_questions(self, filters: dict | None = None):
        """주관식 문제 조회"""
        return self._call("get_subjective_questions", filters or {}) or []

    def update_multiple_choice_question(self, question_id: str, updates: dict) -> bool:
        """객관식 문제 업데이트"""
        self._call("update_multiple_choice_question", {"question_id": question_id, "updates": updates})
        return True

    def update_subjective_question(self, question_id: str, updates: dict) -> bool:
        """주관식 문제 업데이트"""
        self._call("update_subjective_question", {"question_id": question_id, "updates": updates})
        return True

    def get_question_status(self, filters: dict | None = None):
        """문제 상태 조회"""
        return self._call("get_question_status", filters or {}) or []

    def update_question_status(self, question_id: str, updates: dict) -> bool:
        """문제 상태 업데이트"""
        self._call("update_question_status", {"question_id": question_id, "updates": updates})
        return True

    def save_feedback(self, feedback: dict) -> bool:
        self._call("save_feedback", feedback); return True

    def get_feedback_stats(self, question_id: str) -> dict | None:
        return self._call("get_feedback_stats", {"question_id": question_id})

    def get_prompts(self, category: str = None, lang: str = "kr"):
        """프롬프트 조회 - category와 lang으로 필터링"""
        params = {"lang": lang}
        if category:
            params["category"] = category
        return self._call("get_prompts", params) or []

    def get_prompt_by_id(self, prompt_id: str):
        """ID로 특정 프롬프트 조회"""
        return self._call("get_prompt_by_id", {"prompt_id": prompt_id})

    def adjust_difficulty(self, question_id: str, new_difficulty: str, reason: str, adjusted_by: str = "system"):
        self._call("adjust_difficulty", {
            "question_id": question_id, "new_difficulty": new_difficulty,
            "reason": reason, "adjusted_by": adjusted_by
        })

    def get_multiple_choice_question_by_id(self, question_id: str):
        """ID로 객관식 문제 단건 조회 (캐시 우회용)"""
        return self._call("get_multiple_choice_question_by_id", {"question_id": question_id})

    def get_questions_data_version(self) -> str:
        """문제 데이터 버전 토큰 조회 (캐시 무효화용)"""
        result = self._call("get_questions_data_version", {})
        return result.get("version", "1970-01-01T00:00:00Z") if result else "1970-01-01T00:00:00Z"

    def get_feedback(self, question_id: str = None):
        return self._call("get_feedback", {"question_id": question_id}) or []

    def count_feedback(self) -> int:
        return int(self._call("count_feedback") or 0)

    def count_adjustments(self) -> int:
        return int(self._call("count_adjustments") or 0)

    def reset_database(self):
        self._call("reset_database")

    # qlearn_problems 테이블 관련 메서드들
    def save_qlearn_problem(self, problem: dict) -> bool:
        """qlearn_problems 테이블에 문제 저장"""
        result = self._call("save_qlearn_problem", problem)
        return True

    def get_qlearn_problems(self, filters: dict | None = None):
        """qlearn_problems 테이블에서 문제 조회"""
        return self._call("get_qlearn_problems", filters or {}) or []

    def update_qlearn_problem(self, problem_id: str, updates: dict) -> bool:
        """qlearn_problems 테이블의 문제 업데이트"""
        self._call("update_qlearn_problem", {"problem_id": problem_id, "updates": updates})
        return True

    def update_question_review_done(self, question_id: str, review_done: bool = True) -> bool:
        """questions 테이블의 review_done 필드 업데이트"""
        self._call("update_question_review_done", {"question_id": question_id, "review_done": review_done})
        return True
    
    # 번역 관련 메서드들
    def save_qlearn_problem_en(self, problem: dict) -> bool:
        """qlearn_problems_en 테이블에 번역된 문제 저장"""
        self._call("save_qlearn_problem_en", problem)
        return True
    
    def get_qlearn_problems_en(self, filters: dict | None = None):
        """qlearn_problems_en 테이블에서 번역된 문제 조회"""
        return self._call("get_qlearn_problems_en", filters or {}) or []
    
    def update_qlearn_problem_is_en(self, problem_id: str, is_en: bool = True) -> bool:
        """qlearn_problems 테이블의 is_en 필드 업데이트"""
        self._call("update_qlearn_problem_is_en", {"problem_id": problem_id, "is_en": is_en})
        return True
    
    # qlearn_problems_multiple 테이블 관련 메서드들
    def save_qlearn_problem_multiple(self, problem: dict) -> bool:
        """qlearn_problems_multiple 테이블에 문제 저장"""
        result = self._call("save_qlearn_problem_multiple", problem)
        return True

    def get_qlearn_problems_multiple(self, filters: dict | None = None):
        """qlearn_problems_multiple 테이블에서 문제 조회"""
        return self._call("get_qlearn_problems_multiple", filters or {}) or []

    def update_qlearn_problem_multiple(self, problem_id: str, updates: dict) -> bool:
        """qlearn_problems_multiple 테이블의 문제 업데이트"""
        self._call("update_qlearn_problem_multiple", {"problem_id": problem_id, "updates": updates})
        return True