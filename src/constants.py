# 사용자 표시용 (한국어)
ASSESSMENT_AREAS_DISPLAY = {
    "ai_basics": "AI 기초 이해",
    "prompt_engineering": "프롬프트 엔지니어링",
    "work_application": "면접 문제",
    "daily_problem_solving": "일상 문제",
    "tool_utilization": "AI 도구 활용능력",
    "ethics_security": "AI 윤리/보안 인식",
    "pharma_distribution": "태전제약유통",
    "learning_concept": "학습-개념이해",
    "news": "뉴스/시사",  # 추가 카테고리
}

# 데이터베이스 저장용 (영어) - Supabase category enum 값과 일치
ASSESSMENT_AREAS = {
    "ai_basics": "life",  # 기본값으로 life 사용
    "prompt_engineering": "life",  # 기본값으로 life 사용
    "work_application": "interview",  # 면접 문제
    "daily_problem_solving": "life",  # 일상 문제
    "tool_utilization": "life",  # 기본값으로 life 사용
    "ethics_security": "life",  # 기본값으로 life 사용
    "pharma_distribution": "pharma_distribution",  # 올바른 enum 값
    "learning_concept": "learning_concept",  # 올바른 enum 값
    "news": "news",  # 뉴스/시사
}

DIFFICULTY_LEVELS = {
    "very_easy": "아주 쉬움",
    "easy": "쉬움",
    "medium": "보통",
    "hard": "어려움",
    "very_hard": "아주 어려움",
}

QUESTION_TYPES = {
    "multiple_choice": "객관식",
    "subjective": "주관식",
}
