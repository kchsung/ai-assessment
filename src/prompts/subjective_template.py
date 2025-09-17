"""
주관식 문제 생성 프롬프트 템플릿
"""

def get_subjective_prompt(area_display: str, difficulty_display: str, guide: str, time_limit: str, context: str, assessment_area: str, topic_instruction: str, task_template: str, difficulty: str):
    """주관식 문제 생성 프롬프트"""
    return f"""
다음 조건에 맞는 AI 활용능력평가 주관식 문제를 생성해주세요:

평가 영역: {area_display}
난이도: {difficulty_display} - {guide}
시간 제한: {time_limit}
사용자 추가 요구사항: {context if context else '없음'}

요구사항:
1. 평가 영역과 관련된 상황을 반영한 현실적인 문제
2. AI를 활용해서 문제를 해결하는 능력을 평가하기 위한 문제
3. 단계별 접근이 필요한 문제
4. {difficulty_display} 수준에 맞는 복잡도

다음 JSON 형식으로 응답해주세요:
{{
  "lang": "kr",
  "category": "{assessment_area}",
  "title": "문제 제목",
  "topic": "{assessment_area if '구체적인 직무/상황' not in topic_instruction else '구체적인 직무/상황'}",
  "difficulty": "{difficulty}",
  "time_limit": "{time_limit}",
  "topic_summary": "주제 요약",
  "scenario": "문제 상황 및 배경 설명",
  "goal": ["목표 1", "목표 2", "목표 3"],
  "task": "{task_template}",
  "reference": {{
    "metrics": {{"paid_conv_rate": "유료 전환율 2.3%", "retention_d7": "7일 리텐션 45%"}},
    "funnel": {{"signup": "회원가입 단계별 데이터"}},
    "user_feedback": [{{"tag": "사용자 피드백 태그", "content": "피드백 내용"}}],
    "competitor_strategy": {{"campaign": {{"A": "경쟁사 A 전략", "B": "경쟁사 B 전략"}}}}
  }},
  "first_question": ["첫 번째 질문", "두 번째 질문"],
  "requirements": ["요구사항 1", "요구사항 2"],
  "constraints": ["제약사항 1", "제약사항 2"],
  "guide": {{
    "approach": "접근 방법 가이드",
    "tools": "사용 가능한 도구들",
    "considerations": "고려사항들"
  }},
  "evaluation": ["평가 기준 1", "평가 기준 2", "평가 기준 3"]
}}

중요: {topic_instruction}
"""
