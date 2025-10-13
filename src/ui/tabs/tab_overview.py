import streamlit as st

def render(st):
    """Overview 탭 렌더링"""
    
    st.markdown("## 📋 AI 활용능력평가 문제생성 에이전트 개요")
    
    # 프로세스 개요
    st.markdown("""
    이 시스템은 AI를 활용하여 체계적이고 효율적인 문제 생성 및 관리 프로세스를 제공합니다.
    고품질의 평가 문제를 쉽게 생성하고 관리할 수 있도록 지원합니다.
    """)
    
    # 프로세스 플로우 다이어그램
    st.markdown("### 🔄 업무 프로세스")
    
    # 프로세스 플로우 다이어그램 (한 줄 레이아웃)
    st.markdown("""
    <style>
        .process-container {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
            margin: 15px 0;
        }
        .process-row {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 8px;
            flex-wrap: wrap;
        }
        .process-box {
            padding: 10px;
            border-radius: 8px;
            width: calc((100% - 32px) / 5);
            min-width: 220px;
            max-width: 230px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            flex-shrink: 0;
        }
        .process-box h3 {
            margin: 0;
            font-size: 16px;
            line-height: 1.2;
        }
        .process-box p {
            margin: 3px 0 0 0;
            font-size: 12px;
            line-height: 1.1;
        }
        .process-box div {
            margin-top: 5px;
            font-size: 10px;
            line-height: 1.1;
        }
        .arrow-horizontal {
            font-size: 14px;
            color: #666;
            flex-shrink: 0;
            width: 12px;
            text-align: center;
        }
    </style>
    <div class="process-container">
        <div class="process-row">
            <!-- 1단계: 문제 생성 -->
            <div class="process-box" style="background: linear-gradient(135deg, #e1f5fe, #b3e5fc);">
                <h3 style="color: #01579b;">📝 1단계: 문제 생성</h3>
                <p style="color: #0277bd;">Problem Creation</p>
                <div style="color: #01579b;">
                    • 주제별 문제 생성<br>• 객관식/주관식 선택<br>• 난이도 설정
                </div>
            </div>
            <div class="arrow-horizontal">➡️</div>
            <!-- 2단계: 문제 등록 -->
            <div class="process-box" style="background: linear-gradient(135deg, #f3e5f5, #e1bee7);">
                <h3 style="color: #4a148c;">📚 2단계: 문제 등록</h3>
                <p style="color: #6a1b9a;">Problem Registration</p>
                <div style="color: #4a148c;">
                    • 문제 은행 저장<br>• 메타데이터 관리<br>• 분류 체계 적용
                </div>
            </div>
            <div class="arrow-horizontal">➡️</div>
            <!-- 3단계: 문제 난이도 검토 -->
            <div class="process-box" style="background: linear-gradient(135deg, #fff3e0, #ffcc02);">
                <h3 style="color: #e65100;">📊 3단계: 문제 난이도 검토</h3>
                <p style="color: #f57c00;">Difficulty Review</p>
                <div style="color: #e65100;">
                    • AI 기반 난이도 분석<br>• 전문가 검토<br>• 품질 평가
                </div>
            </div>
            <div class="arrow-horizontal">➡️</div>
            <!-- 4단계: 문제 정규화 -->
            <div class="process-box" style="background: linear-gradient(135deg, #e8f5e8, #c8e6c9);">
                <h3 style="color: #1b5e20;">🔧 4단계: 문제 정규화</h3>
                <p style="color: #2e7d32;">Problem Normalization</p>
                <div style="color: #1b5e20;">
                    • 형식 표준화<br>• 문법 검사<br>• 일관성 확보
                </div>
            </div>
            <div class="arrow-horizontal">➡️</div>
            <!-- 5단계: 번역 -->
            <div class="process-box" style="background: linear-gradient(135deg, #fce4ec, #f8bbd9);">
                <h3 style="color: #880e4f;">🌐 5단계: 번역</h3>
                <p style="color: #ad1457;">Translation</p>
                <div style="color: #880e4f;">
                    • 다국어 지원<br>• 문화적 적응<br>• 품질 검증
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 각 단계별 상세 설명
    st.markdown("### 📖 단계별 상세 설명")
    
    # 1단계: 문제 생성
    with st.expander("📝 1단계: 문제 생성 (Problem Creation)", expanded=True):
        st.markdown("""
        **목적**: 교육 목표에 맞는 고품질 문제를 생성합니다.
        
        **주요 기능**:
        - 🎯 **주제별 문제 생성**: AI가 특정 주제에 맞는 문제를 자동 생성
        - 📋 **문제 유형 선택**: 객관식, 주관식, 서술형 등 다양한 유형 지원
        - 📊 **난이도 설정**: 초급, 중급, 고급 등 난이도 레벨 지정
        - 🔧 **커스터마이징**: 사용자 요구사항에 맞는 문제 맞춤 생성
        
        **사용 방법**:
        1. 문제 생성 탭에서 주제와 난이도를 선택
        2. 문제 유형과 개수를 설정
        3. AI가 자동으로 문제를 생성
        4. 생성된 문제를 검토하고 수정
        """)
    
    # 2단계: 문제 등록
    with st.expander("📚 2단계: 문제 등록 (Problem Registration)"):
        st.markdown("""
        **목적**: 생성된 문제를 체계적으로 관리하고 저장합니다.
        
        **주요 기능**:
        - 🗄️ **문제 은행 저장**: 생성된 문제를 데이터베이스에 체계적으로 저장
        - 🏷️ **메타데이터 관리**: 주제, 난이도, 유형 등 상세 정보 관리
        - 📂 **분류 체계**: 주제별, 난이도별, 유형별 자동 분류
        - 🔍 **검색 및 필터링**: 저장된 문제를 쉽게 찾고 관리
        
        **사용 방법**:
        1. 문제 은행 탭에서 저장된 문제 목록 확인
        2. 주제, 난이도, 유형별로 필터링
        3. 문제 상세 정보 확인 및 수정
        4. 문제 삭제 또는 재분류
        """)
    
    # 3단계: 문제 난이도 검토
    with st.expander("📊 3단계: 문제 난이도 검토 (Difficulty Review)"):
        st.markdown("""
        **목적**: 문제의 난이도를 정확하게 평가하고 품질을 보장합니다.
        
        **주요 기능**:
        - 🤖 **AI 기반 난이도 분석**: 머신러닝 모델을 통한 자동 난이도 평가
        - 👨‍🏫 **전문가 검토**: 교육 전문가의 수동 검토 및 피드백
        - 📈 **품질 평가**: 문제의 명확성, 적절성, 교육적 가치 평가
        - 🔄 **피드백 루프**: 검토 결과를 바탕으로 문제 개선
        
        **사용 방법**:
        1. 문제 검토 탭에서 난이도 분석 결과 확인
        2. AI 제안 난이도와 실제 난이도 비교
        3. 전문가 피드백 수집 및 반영
        4. 문제 품질 개선 및 재검토
        """)
    
    # 4단계: 문제 정규화
    with st.expander("🔧 4단계: 문제 정규화 (Problem Normalization)"):
        st.markdown("""
        **목적**: 문제의 형식과 품질을 표준화하여 일관성을 확보합니다.
        
        **주요 기능**:
        - 📝 **형식 표준화**: 문제 형식, 문체, 구조의 일관성 확보
        - ✍️ **문법 검사**: 맞춤법, 문법, 표현의 정확성 검증
        - 🎯 **일관성 확보**: 용어, 표현 방식의 통일성 유지
        - 🔍 **품질 검증**: 최종 품질 점검 및 승인 프로세스
        
        **사용 방법**:
        1. 문제 정규화 탭에서 자동 검사 실행
        2. 발견된 문제점 확인 및 수정
        3. 표준 형식에 맞게 문제 조정
        4. 최종 품질 검증 및 승인
        """)
    
    # 5단계: 번역
    with st.expander("🌐 5단계: 번역 (Translation)"):
        st.markdown("""
        **목적**: 다국어 환경에서 사용할 수 있도록 문제를 번역합니다.
        
        **주요 기능**:
        - 🌍 **다국어 지원**: 영어, 중국어, 일본어 등 다양한 언어 지원
        - 🎭 **문화적 적응**: 각 언어권의 문화적 특성에 맞는 번역
        - 🔍 **품질 검증**: 번역의 정확성과 자연스러움 검증
        - 🔄 **역번역 검토**: 번역 품질을 위한 역번역 검증
        
        **사용 방법**:
        1. 번역 탭에서 대상 언어 선택
        2. AI 기반 자동 번역 실행
        3. 번역 결과 검토 및 수정
        4. 문화적 맥락에 맞는 표현 조정
        """)
    
    # 시스템 특징
    st.markdown("### ✨ 시스템 특징")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **🤖 AI 기반 자동화**
        - GPT 모델을 활용한 지능형 문제 생성
        - 자동 난이도 평가 및 품질 검증
        - 효율적인 번역 및 정규화
        """)
    
    with col2:
        st.markdown("""
        **👥 인간-AI 협업**
        - HITL(Human-in-the-Loop) 프로세스
        - 전문가 피드백 통합
        - 품질 보장을 위한 다단계 검토
        """)
    
    with col3:
        st.markdown("""
        **📊 체계적 관리**
        - 문제 은행을 통한 체계적 저장
        - 메타데이터 기반 분류 및 검색
        - 분석 대시보드를 통한 인사이트
        """)
    
    # 사용 가이드
    st.markdown("### 🚀 시작하기")
    
    st.markdown("""
    **1단계**: 📝 **문제 생성** 탭에서 첫 번째 문제를 생성해보세요.
    
    **2단계**: 📚 **문제 은행** 탭에서 생성된 문제를 확인하고 관리하세요.
    
    **3단계**: 🔍 **문제 검토** 탭에서 AI 기반 난이도 분석을 확인하세요.
    
    **4단계**: ⚙️ **설정** 탭에서 API 키와 기본 설정을 구성하세요.
    
    **5단계**: 📊 **분석 대시보드** 탭에서 전체적인 통계와 인사이트를 확인하세요.
    """)
    
    # 주의사항
    st.markdown("### ⚠️ 주의사항")
    
    st.warning("""
    - **API 키 설정**: OpenAI API 키가 필요합니다. 설정 탭에서 구성해주세요.
    - **인터넷 연결**: AI 모델 사용을 위해 안정적인 인터넷 연결이 필요합니다.
    - **데이터 보안**: 민감한 정보는 문제에 포함하지 마세요.
    - **품질 검토**: AI 생성 결과는 반드시 전문가 검토를 거쳐주세요.
    """)
