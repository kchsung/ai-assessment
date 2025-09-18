"""
객관식 문제 생성 프롬프트 템플릿
"""

def get_multiple_choice_prompt(area_display: str, difficulty_display: str, guide: str, time_limit: str, context: str, assessment_area: str, topic_instruction: str, difficulty: str):
    """객관식 문제 생성 프롬프트"""
    return f"""
다음 조건에 맞는 AI 활용능력평가 객관식 문제를 생성해주세요:

평가 영역: {area_display}
난이도: {difficulty_display} - {guide}
시간 제한: {time_limit}
사용자 추가 요구사항: {context if context else '없음'}

요구사항:
1. 평가 영역과 관련된 상황을 반영한 현실적인 문제
2. AI를 활용해서 문제를 해결하는 능력을 평가하기 위한 문제
3. 단계별 접근이 필요한 문제
4. {difficulty_display} 수준에 맞는 복잡도
5. 복잡도에 따른 step1 ~ step9 구성, 복잡도가 높을 수록 스탭이 늘어나야 함

다음 JSON 형식으로 응답해주세요:
{{
  "lang": "kr",
  "category": "{assessment_area}",
  "problemTitle": "문제 제목",
  "topic": "{assessment_area if '구체적인 직무/상황' not in topic_instruction else '구체적인 직무/상황'}",
  "difficulty": "{difficulty}",
  "estimatedTime": "{time_limit}",
  "scenario": "문제 상황 및 배경 설명",
  "reference": {{
    "metrics": {{"paid_conv_rate": "유료 전환율 2.3%", "retention_d7": "7일 리텐션 45%"}},
    "funnel": {{"signup": "회원가입 단계별 데이터"}},
    "user_feedback": [{{"tag": "사용자 피드백 태그", "content": "피드백 내용"}}],
    "competitor_strategy": {{"campaign": {{"A": "경쟁사 A 전략", "B": "경쟁사 B 전략"}}}}
  }},
  "steps": [
    {{
      "step": 1,
      "title": "맥락 파악",
      "question": "핵심 질문 내용",
      "ref_paths": ["ref.metrics.paid_conv_rate"],
      "options": [
        {{"id":"A","text":"선택지 A","feedback":"피드백 A","weight":0.85,"ref_paths":["ref.funnel.signup"]}},
        {{"id":"B","text":"선택지 B","feedback":"피드백 B","weight":0.75,"ref_paths":["ref.user_feedback[0].tag"]}},
        {{"id":"C","text":"선택지 C","feedback":"피드백 C","weight":1.0,"ref_paths":["ref.metrics.retention_d7"]}},
        {{"id":"D","text":"선택지 D","feedback":"피드백 D","weight":0.65,"ref_paths":["ref.competitor_strategy.campaign.B"]}}
      ],
      "answer":"C"
    }}
  ]
}}

중요: {topic_instruction}
"""
