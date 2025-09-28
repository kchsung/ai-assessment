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
        

    def _call(self, action: str, params: dict | None = None):
        headers = {
            "content-type": "application/json",
            "x-edge-token": self.token,
        }
        if self.supabase_anon:
            headers["authorization"] = f"Bearer {self.supabase_anon}"

        payload = {"action": action, "params": params or {}}
        # 디버그 정보는 로깅으로 변경 (문제 데이터 출력 방지)
        # print(f"🚀 Edge Function 호출 - Action: {action}")
        # print(f"📡 URL: {self.base_url}")
        # print(f"📦 Payload: {payload}")
        
        resp = requests.post(self.base_url, headers=headers, json=payload)
        # print(f"📊 Response Status: {resp.status_code}")
        # print(f"📄 Response Text: {resp.text}")
        
        if resp.status_code >= 400:
            raise RuntimeError(f"Edge error {resp.status_code}: {resp.text}")
        
        # JSON 파싱 시도
        try:
            data = resp.json()
            # print(f"📋 Parsed Response: {data}")
        except ValueError as e:
            raise RuntimeError(f"Edge JSON parse error: {e}, Response: {resp.text}")
        
        if not data.get("ok"):
            raise RuntimeError(f"Edge failure: {data.get('error')}")
        return data.get("data")
    

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