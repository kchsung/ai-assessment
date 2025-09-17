from src.constants import DIFFICULTY_LEVELS

class HITLManager:
    def __init__(self, db_client):
        self.db = db_client
        self.difficulty_thresholds = {
            "basic": {"min": 1.0, "max": 2.5},
            "intermediate": {"min": 2.5, "max": 4.0},
            "advanced": {"min": 4.0, "max": 5.0},
        }

    def analyze_difficulty_alignment(self, question_id: str) -> dict:
        stats = self.db.get_feedback_stats(question_id)
        if not stats or stats.get("feedback_count", 0) < 3:
            return {"status":"insufficient_data","message":"피드백 최소 3개 필요"}

        q = self.db.get_questions({"id": question_id})
        if not q: return {"status":"error","message":"문제 없음"}
        current = q[0]["difficulty"]

        avg = stats["avg_difficulty"]; votes = stats.get("difficulty_votes") or {}
        most, pct = current, 0
        if votes:
            items = sorted(votes.items(), key=lambda x: x[1], reverse=True)
            most, pct = items[0][0], items[0][1] / max(sum(votes.values()),1) * 100

        needs, rec = False, current
        for k, th in self.difficulty_thresholds.items():
            if th["min"] <= avg < th["max"]:
                if k != current: needs=True; rec=k
                break
        if pct > 50 and most != current:
            needs=True; rec=most

        return {
            "status": "analyzed",
            "current_difficulty": current,
            "avg_difficulty_rating": avg,
            "recommended_difficulty": rec,
            "needs_adjustment": needs,
            "confidence": pct,
            "feedback_count": stats["feedback_count"],
            "difficulty_votes": votes,
            "stats": stats,
        }

    def auto_adjust_difficulties(self) -> list[dict]:
        out=[]
        for q in self.db.get_questions():
            a = self.analyze_difficulty_alignment(q["id"])
            if a.get("status")=="analyzed" and a.get("needs_adjustment"):
                reason = f"자동 조정: 평균 {a['avg_difficulty_rating']:.1f}, {a['confidence']:.0f}%가 {a['recommended_difficulty']}로 평가"
                self.db.adjust_difficulty(q["id"], a["recommended_difficulty"], reason, "auto_system")
                out.append({"question_id": q["id"], "from": a["current_difficulty"], "to": a["recommended_difficulty"], "reason": reason})
        return out
