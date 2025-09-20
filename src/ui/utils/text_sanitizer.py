"""
텍스트 정리 유틸리티 함수들
"""
import re

# 키보드 토큰 패턴 (컴파일된 정규식)
_KEY_PAT = re.compile(
    r'(?im)(?:^|\b)(?:key|keyboard)\s*[:=]?\s*'
    r'(?:arrow(?:left|right|up|down)|[-\w,\s])+',  # keyboard_arrow_* 등
)

def sanitize_title(raw: str) -> str:
    """제목에서 키보드 힌트 토큰과 불필요한 텍스트를 제거하는 함수"""
    if not raw:
        return "제목 없음"
    text = str(raw)
    # key:, keyboard:, keyboard_arrow_* 토큰 제거
    text = _KEY_PAT.sub('', text)
    # 1줄 추출 후 공백 정리
    text = text.strip().splitlines()[0]
    text = re.sub(r'\s+', ' ', text).strip()
    if len(text) < 5:
        text = str(raw).strip().replace('\n', ' ')[:50]
    return text or "제목 없음"

def sanitize_content(raw: str) -> str:
    """본문에서 키보드 힌트 토큰을 제거하는 함수"""
    if not raw:
        return ""
    text = str(raw)
    # 라인 단위로 key/keyboard 안내만 있는 줄 제거
    text = re.sub(r'(?im)^\s*(?:key|keyboard)\s*[:=].*\n?', '', text)
    # inline keyboard_arrow_* 잔여 제거
    text = re.sub(r'(?i)\bkeyboard_arrow_(left|right|up|down)\b', '', text)
    return text.strip()

def extract_answer(question_data):
    """생성된 문제에서 정답을 추출하는 함수"""
    try:
        metadata = question_data.get("metadata", {})
        
        if question_data.get("type") == "multiple_choice":
            # 객관식 문제의 경우 steps에서 정답 찾기
            steps = metadata.get("steps", [])
            for step in steps:
                if step.get("answer"):
                    return step["answer"]
        else:
            # 주관식 문제의 경우 evaluation에서 정답 찾기
            evaluation = metadata.get("evaluation", [])
            if evaluation:
                return evaluation[0] if isinstance(evaluation, list) else str(evaluation)
        
        return "정답 정보 없음"
    except Exception:
        return "정답 추출 실패"

# 하위 호환성을 위한 별칭
_sanitize_title = sanitize_title
_sanitize_content = sanitize_content
_extract_answer = extract_answer
