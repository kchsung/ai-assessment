# AI 활용능력평가 문제생성 에이전트 v2.0

OpenAI API와 Supabase Edge Function을 활용한 지능형 문제 생성 시스템입니다.

## 🚀 기능

- **AI 문제 생성**: GPT-5 시리즈 모델을 활용한 자동 문제 생성
- **모델 선택**: gpt-5, gpt-5-nano, gpt-5-mini 중 선택 가능
- **문제 은행**: 생성된 문제들을 체계적으로 관리
- **피드백 시스템**: Human-in-the-Loop 기반 난이도 조정
- **분석 대시보드**: 문제별 통계 및 시각화

## 📋 모델별 특징

| 모델 | 용도 | 속도 | 비용 | Input 가격 | Output 가격 |
|------|------|------|------|------------|-------------|
| GPT-5 | 복잡한 문제 생성 | 보통 | 높음 | $0.03/1K | $0.12/1K |
| GPT-5 Nano | 일반적인 문제 생성 | 빠름 | 낮음 | $0.01/1K | $0.04/1K |
| GPT-5 Mini | 간단한 문제 생성 | 매우 빠름 | 매우 낮음 | $0.005/1K | $0.02/1K |

## 🛠️ 설치 및 실행

### 로컬 실행

1. **저장소 클론**
```bash
git clone <repository-url>
cd streamlit-learn
```

2. **의존성 설치**
```bash
pip install -r requirements.txt
```

3. **환경 변수 설정**
`.streamlit/secrets.toml` 파일 생성:
```toml
OPENAI_API_KEY = "your_openai_api_key_here"
EDGE_FUNCTION_URL = "your_edge_function_url"
EDGE_SHARED_TOKEN = "your_edge_token"
SUPABASE_ANON_KEY = "your_supabase_key"
```

4. **앱 실행**
```bash
streamlit run app.py
```

### Streamlit Cloud 배포

1. **GitHub에 저장소 푸시**

2. **Streamlit Cloud에서 앱 생성**
   - [share.streamlit.io](https://share.streamlit.io) 접속
   - GitHub 저장소 연결

3. **Secrets 설정**
   Streamlit Cloud의 "Secrets" 탭에서:
   ```toml
   OPENAI_API_KEY = "your_openai_api_key_here"
   EDGE_FUNCTION_URL = "your_edge_function_url"
   EDGE_SHARED_TOKEN = "your_edge_token"
   SUPABASE_ANON_KEY = "your_supabase_key"
   ```

## 📁 프로젝트 구조

```
streamlit-learn/
├── app.py                 # 메인 애플리케이션
├── requirements.txt       # 의존성 패키지
├── .streamlit/
│   └── secrets.toml      # 로컬 설정 (Git 제외)
├── src/
│   ├── config.py         # 설정 관리
│   ├── constants.py      # 상수 정의
│   ├── services/         # 비즈니스 로직
│   │   ├── ai_generator.py
│   │   ├── edge_client.py
│   │   ├── hitl.py
│   │   └── local_db.py
│   └── ui/               # 사용자 인터페이스
│       ├── tab_feedback.py
│       └── tabs/
│           ├── tab_create.py
│           ├── tab_bank.py
│           ├── tab_dashboard.py
│           └── tab_settings.py
└── README.md
```

## 🔧 설정

### API 키 설정

- **로컬**: `.streamlit/secrets.toml` 또는 `.env` 파일
- **Streamlit Cloud**: 웹 인터페이스의 "Secrets" 탭

### 데이터베이스

- **Edge Function**: Supabase Edge Function 사용 (우선)
- **Local SQLite**: Edge Function 실패 시 자동 fallback

## 🎯 사용법

1. **문제 생성**: 설정 탭에서 모델 선택 후 문제 생성 탭에서 문제 생성
2. **문제 관리**: 문제 은행 탭에서 생성된 문제들 확인 및 관리
3. **피드백**: 피드백 탭에서 문제 품질 평가 및 난이도 조정
4. **분석**: 분석 대시보드에서 통계 및 시각화 확인

## 🔒 보안

- API 키는 Git에 커밋되지 않음
- `.env`, `.streamlit/` 폴더는 `.gitignore`에 포함
- Streamlit Cloud에서는 Secrets 기능 활용

## 📝 라이선스

MIT License



