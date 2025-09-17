import os
import requests
from .local_db import LocalDBClient

class EdgeDBClient:
    def __init__(self, base_url: str | None, token: str | None, supabase_anon: str | None):
        self.base_url = base_url or os.getenv("EDGE_FUNCTION_URL")
        self.token = token or os.getenv("EDGE_SHARED_TOKEN")
        self.supabase_anon = supabase_anon or os.getenv("SUPABASE_ANON_KEY")
        if not self.base_url:
            raise RuntimeError("EDGE_FUNCTION_URL not set")
        if not self.token:
            raise RuntimeError("EDGE_SHARED_TOKEN not set")
        
        # Fallback을 위한 LocalDBClient 인스턴스
        self._local_fallback = LocalDBClient()
        self._use_fallback = False

    def _call(self, action: str, params: dict | None = None):
        # Fallback 모드인 경우 LocalDBClient 사용
        if self._use_fallback:
            return self._local_call(action, params)
        
        headers = {
            "content-type": "application/json",
            "x-edge-token": self.token,
        }
        if self.supabase_anon:
            headers["authorization"] = f"Bearer {self.supabase_anon}"

        try:
            resp = requests.post(self.base_url, headers=headers, json={"action": action, "params": params or {}})
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
        except Exception as e:
            # Edge Function 실패 시 fallback 모드로 전환
            print(f"Edge Function 실패, LocalDB로 fallback: {e}")
            self._use_fallback = True
            return self._local_call(action, params)
    
    def _local_call(self, action: str, params: dict | None = None):
        """LocalDBClient를 사용한 fallback 호출"""
        if action == "get_questions":
            return self._local_fallback.get_questions(params)
        elif action == "save_question":
            return self._local_fallback.save_question(params)
        elif action == "save_feedback":
            return self._local_fallback.save_feedback(params)
        elif action == "get_feedback_stats":
            return self._local_fallback.get_feedback_stats(params.get("question_id"))
        elif action == "get_prompts":
            return self._local_fallback.get_prompts(params.get("category"), params.get("lang", "kr"))
        elif action == "adjust_difficulty":
            return self._local_fallback.adjust_difficulty(
                params.get("question_id"), 
                params.get("new_difficulty"), 
                params.get("reason"), 
                params.get("adjusted_by", "system")
            )
        elif action == "count_feedback":
            return self._local_fallback.count_feedback()
        elif action == "count_adjustments":
            return self._local_fallback.count_adjustments()
        elif action == "reset_database":
            return self._local_fallback.reset_database()
        else:
            raise RuntimeError(f"Unknown action: {action}")

    # API
    def save_question(self, q: dict) -> bool:
        self._call("save_question", q); return True

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

    def adjust_difficulty(self, question_id: str, new_difficulty: str, reason: str, adjusted_by: str = "system"):
        self._call("adjust_difficulty", {
            "question_id": question_id, "new_difficulty": new_difficulty,
            "reason": reason, "adjusted_by": adjusted_by
        })

    def count_feedback(self) -> int:
        return int(self._call("count_feedback") or 0)

    def count_adjustments(self) -> int:
        return int(self._call("count_adjustments") or 0)

    def reset_database(self):
        self._call("reset_database")
