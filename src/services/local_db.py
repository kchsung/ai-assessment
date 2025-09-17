import os, json, sqlite3, pandas as pd

class LocalDBClient:
    def __init__(self, db_path: str = "ai_assessment_bank.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id TEXT PRIMARY KEY,
            area TEXT NOT NULL,
            difficulty TEXT NOT NULL,
            type TEXT NOT NULL,
            question_text TEXT NOT NULL,
            options TEXT,
            correct_answer INTEGER,
            requirements TEXT,
            evaluation_criteria TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ai_generated BOOLEAN DEFAULT FALSE,
            template_id TEXT,
            metadata TEXT,
            -- 새로운 JSON 포맷 지원 필드들
            lang TEXT DEFAULT 'kr',
            category TEXT DEFAULT 'interview',
            topic TEXT,
            time_limit TEXT,
            topic_summary TEXT,
            scenario TEXT,
            goal TEXT,
            task TEXT,
            reference TEXT,
            first_question TEXT,
            constraints TEXT,
            guide TEXT,
            evaluation TEXT,
            steps TEXT
        )""")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id TEXT NOT NULL,
            user_id TEXT,
            difficulty_rating INTEGER CHECK(difficulty_rating BETWEEN 1 AND 5),
            relevance_rating INTEGER CHECK(relevance_rating BETWEEN 1 AND 5),
            clarity_rating INTEGER CHECK(clarity_rating BETWEEN 1 AND 5),
            comments TEXT,
            actual_difficulty TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS difficulty_adjustments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id TEXT NOT NULL,
            original_difficulty TEXT,
            adjusted_difficulty TEXT,
            adjustment_reason TEXT,
            adjusted_by TEXT,
            adjusted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS prompts (
            id TEXT PRIMARY KEY,
            lang TEXT NOT NULL DEFAULT 'kr',
            category TEXT NOT NULL,
            title TEXT NOT NULL,
            prompt_text TEXT NOT NULL,
            description TEXT,
            tags TEXT,
            active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
        
        # 기존 테이블에 새로운 컬럼들 추가 (마이그레이션)
        self._migrate_schema(conn)
        
        conn.commit(); conn.close()
    
    def _migrate_schema(self, conn):
        """기존 테이블에 새로운 컬럼들을 안전하게 추가"""
        cur = conn.cursor()
        
        # 새로운 컬럼들을 추가 (이미 존재하면 무시됨)
        new_columns = [
            ("lang", "TEXT DEFAULT 'kr'"),
            ("category", "TEXT DEFAULT 'interview'"),
            ("topic", "TEXT"),
            ("time_limit", "TEXT"),
            ("topic_summary", "TEXT"),
            ("scenario", "TEXT"),
            ("goal", "TEXT"),
            ("task", "TEXT"),
            ("reference", "TEXT"),
            ("first_question", "TEXT"),
            ("constraints", "TEXT"),
            ("guide", "TEXT"),
            ("evaluation", "TEXT"),
            ("steps", "TEXT")
        ]
        
        for column_name, column_def in new_columns:
            try:
                cur.execute(f"ALTER TABLE questions ADD COLUMN {column_name} {column_def}")
            except sqlite3.OperationalError:
                # 컬럼이 이미 존재하는 경우 무시
                pass

    # API (Edge와 인터페이스 동일)
    def save_question(self, q: dict) -> bool:
        conn = sqlite3.connect(self.db_path); cur = conn.cursor()
        
        # 메타데이터에서 새로운 필드들 추출
        metadata = q.get('metadata', {})
        
        cur.execute("""
        INSERT INTO questions (
           id, area, difficulty, type, question_text,
           options, correct_answer, requirements, evaluation_criteria,
           ai_generated, template_id, metadata,
           lang, category, topic, time_limit, topic_summary, scenario,
           goal, task, reference, first_question, constraints, guide, evaluation, steps
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
            q['id'], q['area'], q['difficulty'], q.get('type','general'),
            q['question'], json.dumps(q.get('options', [])),
            q.get('correct_answer'),
            json.dumps(q.get('requirements', [])),
            json.dumps(q.get('evaluation_criteria', [])),
            q.get('ai_generated', False),
            q.get('template_id'),
            json.dumps(metadata),
            # 새로운 필드들
            metadata.get('lang', 'kr'),
            metadata.get('category', 'interview'),
            metadata.get('topic'),
            metadata.get('time_limit') or metadata.get('estimatedTime'),
            metadata.get('topic_summary'),
            metadata.get('scenario'),
            json.dumps(metadata.get('goal', [])),
            metadata.get('task'),
            json.dumps(metadata.get('reference', {})),
            json.dumps(metadata.get('first_question', [])),
            json.dumps(metadata.get('constraints', [])),
            json.dumps(metadata.get('guide', {})),
            json.dumps(metadata.get('evaluation', [])),
            json.dumps(metadata.get('steps', []))
        ))
        conn.commit(); conn.close(); return True

    def get_questions(self, filters: dict | None = None):
        conn = sqlite3.connect(self.db_path)
        q = "SELECT * FROM questions"; params = []
        if filters:
            conds = []
            for k, col in {"id":"id","area":"area","difficulty":"difficulty","type":"type"}.items():
                if k in filters: conds.append(f"{col}=?"); params.append(filters[k])
            if conds: q += " WHERE " + " AND ".join(conds)
        df = pd.read_sql_query(q, conn, params=params); conn.close()
        out = []
        for _, r in df.iterrows():
            # 기본 메타데이터
            metadata = json.loads(r["metadata"]) if r["metadata"] else {}
            
            # 새로운 필드들을 메타데이터에 병합
            new_fields = {
                "lang": r.get("lang", "kr"),
                "category": r.get("category", "interview"),
                "topic": r.get("topic"),
                "time_limit": r.get("time_limit"),
                "topic_summary": r.get("topic_summary"),
                "scenario": r.get("scenario"),
                "goal": json.loads(r["goal"]) if r.get("goal") else [],
                "task": r.get("task"),
                "reference": json.loads(r["reference"]) if r.get("reference") else {},
                "first_question": json.loads(r["first_question"]) if r.get("first_question") else [],
                "constraints": json.loads(r["constraints"]) if r.get("constraints") else [],
                "guide": json.loads(r["guide"]) if r.get("guide") else {},
                "evaluation": json.loads(r["evaluation"]) if r.get("evaluation") else [],
                "steps": json.loads(r["steps"]) if r.get("steps") else []
            }
            
            # None이 아닌 값들만 메타데이터에 추가
            for key, value in new_fields.items():
                if value is not None and value != "" and value != [] and value != {}:
                    metadata[key] = value
            
            out.append({
                "id": r["id"], "area": r["area"], "difficulty": r["difficulty"], "type": r["type"],
                "question": r["question_text"],
                "options": json.loads(r["options"]) if r["options"] else None,
                "correct_answer": r["correct_answer"],
                "requirements": json.loads(r["requirements"]) if r["requirements"] else None,
                "evaluation_criteria": json.loads(r["evaluation_criteria"]) if r["evaluation_criteria"] else None,
                "ai_generated": r["ai_generated"],
                "metadata": metadata,
            })
        return out

    def save_feedback(self, fb: dict) -> bool:
        conn = sqlite3.connect(self.db_path); cur = conn.cursor()
        cur.execute("""
        INSERT INTO feedback (
            question_id, user_id, difficulty_rating, relevance_rating,
            clarity_rating, comments, actual_difficulty
        ) VALUES (?,?,?,?,?,?,?)""", (
            fb["question_id"], fb.get("user_id","anonymous"),
            fb["difficulty_rating"], fb["relevance_rating"], fb["clarity_rating"],
            fb.get("comments",""), fb.get("actual_difficulty")
        ))
        conn.commit(); conn.close(); return True

    def get_feedback(self, question_id: str = None):
        conn = sqlite3.connect(self.db_path)
        if question_id:
            df = pd.read_sql_query("""
            SELECT question_id, user_id, difficulty_rating, relevance_rating,
                   clarity_rating, comments, actual_difficulty, created_at
            FROM feedback WHERE question_id = ?
            ORDER BY created_at DESC""", conn, params=[question_id])
        else:
            df = pd.read_sql_query("""
            SELECT question_id, user_id, difficulty_rating, relevance_rating,
                   clarity_rating, comments, actual_difficulty, created_at
            FROM feedback
            ORDER BY created_at DESC""", conn)
        conn.close()
        return df.to_dict('records') if not df.empty else []

    def get_feedback_stats(self, question_id: str):
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query("""
        SELECT AVG(difficulty_rating) as avg_difficulty,
               AVG(relevance_rating)  as avg_relevance,
               AVG(clarity_rating)    as avg_clarity,
               COUNT(*)               as feedback_count,
               GROUP_CONCAT(actual_difficulty) as difficulty_votes
        FROM feedback WHERE question_id = ?""", conn, params=[question_id])
        conn.close()
        if df.empty or df.iloc[0]["feedback_count"] == 0: return None
        votes = {}
        raw = df.iloc[0]["difficulty_votes"]
        if raw:
            for v in str(raw).split(","):
                v=v.strip(); votes[v]=votes.get(v,0)+1
        return {
            "avg_difficulty": df.iloc[0]["avg_difficulty"],
            "avg_relevance" : df.iloc[0]["avg_relevance"],
            "avg_clarity"   : df.iloc[0]["avg_clarity"],
            "feedback_count": df.iloc[0]["feedback_count"],
            "difficulty_votes": votes,
        }

    def adjust_difficulty(self, question_id: str, new_difficulty: str, reason: str, adjusted_by: str = "system"):
        conn = sqlite3.connect(self.db_path); cur = conn.cursor()
        row = cur.execute("SELECT difficulty FROM questions WHERE id=?", (question_id,)).fetchone()
        original = row[0] if row else None
        cur.execute("UPDATE questions SET difficulty=? WHERE id=?", (new_difficulty, question_id))
        cur.execute("""
        INSERT INTO difficulty_adjustments (question_id, original_difficulty, adjusted_difficulty, adjustment_reason, adjusted_by)
        VALUES (?,?,?,?,?)""", (question_id, original, new_difficulty, reason, adjusted_by))
        conn.commit(); conn.close()

    def count_feedback(self) -> int:
        conn = sqlite3.connect(self.db_path); df = pd.read_sql_query("SELECT COUNT(*) cnt FROM feedback", conn); conn.close()
        return int(df.iloc[0]["cnt"]) if not df.empty else 0

    def count_adjustments(self) -> int:
        conn = sqlite3.connect(self.db_path); df = pd.read_sql_query("SELECT COUNT(*) cnt FROM difficulty_adjustments", conn); conn.close()
        return int(df.iloc[0]["cnt"]) if not df.empty else 0

    def get_prompts(self, category: str = None, lang: str = "kr"):
        """프롬프트 조회 - category와 lang으로 필터링"""
        conn = sqlite3.connect(self.db_path)
        q = "SELECT * FROM prompts WHERE lang = ? AND active = TRUE"
        params = [lang]
        
        if category:
            q += " AND category = ?"
            params.append(category)
        
        df = pd.read_sql_query(q, conn, params=params)
        conn.close()
        
        out = []
        for _, r in df.iterrows():
            out.append({
                "id": r["id"],
                "lang": r["lang"],
                "category": r["category"],
                "title": r["title"],
                "prompt_text": r["prompt_text"],
                "description": r["description"],
                "tags": json.loads(r["tags"]) if r["tags"] else [],
                "active": r["active"],
                "created_at": r["created_at"],
                "updated_at": r["updated_at"]
            })
        return out

    def reset_database(self):
        if os.path.exists(self.db_path): os.remove(self.db_path)
        self._init_db()
