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
                    raise RuntimeError(f"Edge JSON parse error: {e}, Response: {resp.text}")
                
                if not data.get("ok"):
                    raise RuntimeError(f"Edge failure: {data.get('error')}")
                return data.get("data")
                
            except (requests.exceptions.ChunkedEncodingError, 
                    requests.exceptions.ConnectionError,
                    requests.exceptions.Timeout) as e:
                if attempt < max_retries - 1:
                    print(f"⚠️ 네트워크 오류 발생, 재시도 중... ({attempt + 1}/{max_retries}): {e}")
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
            # print(f"🔍 save_question 호출됨 - ID: {q.get('id', 'N/A')}")
            # print(f"📝 저장할 데이터: {q}")  # 문제 데이터 출력 방지
            result = self._call("save_question", q)
            # print(f"✅ save_question 성공: {result}")
            return True
        except Exception as e:
            print(f"❌ save_question 실패: {e}")
            raise e

    def get_questions(self, filters: dict | None = None):
        return self._call("get_questions", filters or {}) or []

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
        self._call("save_qlearn_problem", problem)
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