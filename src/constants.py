# Supabase q_domain enum 값과 정확히 일치
ASSESSMENT_AREAS = {
    "life": "life",
    "news": "news",
    "interview": "interview",
    "learning_concept": "learning_concept",
    "pharma_distribution": "pharma_distribution",
}

# Supabase q_difficulty enum 값과 정확히 일치
DIFFICULTY_LEVELS = {
    "very easy": "very easy",
    "easy": "easy",
    "normal": "normal",
    "hard": "hard",
    "very hard": "very hard",
}

QUESTION_TYPES = {
    "multiple_choice": "multiple_choice",
    "subjective": "subjective",
}

# Supabase enum 값들 - 하드코딩 방지용
VALID_DIFFICULTIES = ["very easy", "easy", "normal", "hard", "very hard"]
VALID_DOMAINS = ["life", "news", "interview", "learning_concept", "pharma_distribution"]

# 기본값
DEFAULT_DIFFICULTY = "normal"
DEFAULT_DOMAIN = "life"
