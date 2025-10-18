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
    
    # 프로세스 플로우 다이어그램 (현재 시스템 구조에 맞게 수정)
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
            padding: 15px;
            border-radius: 8px;
            width: calc((100% - 24px) / 4);
            min-width: 280px;
            max-width: 320px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            flex-shrink: 0;
        }
        .process-box h3 {
            margin: 0;
            font-size: 20px;
            line-height: 1.3;
        }
        .process-box p {
            margin: 5px 0 0 0;
            font-size: 14px;
            line-height: 1.2;
        }
        .process-box div {
            margin-top: 8px;
            font-size: 12px;
            line-height: 1.3;
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
            <!-- 1단계: 문제 생성 (자동생성 포함) -->
            <div class="process-box" style="background: linear-gradient(135deg, #e1f5fe, #b3e5fc);">
                <h3 style="color: #01579b;">📝 문제 생성</h3>
                <p style="color: #0277bd;">Problem Creation</p>
                <div style="color: #01579b;">
                    • 수동 문제 생성<br>• AI 자동 생성<br>• 주제별 맞춤 생성
                </div>
            </div>
            <div class="arrow-horizontal">➡️</div>
            <!-- 2단계: 문제 은행 -->
            <div class="process-box" style="background: linear-gradient(135deg, #f3e5f5, #e1bee7);">
                <h3 style="color: #4a148c;">📚 문제 은행</h3>
                <p style="color: #6a1b9a;">Problem Bank</p>
                <div style="color: #4a148c;">
                    • 생성된 문제 확인<br>• 체계적 관리<br>• 분류 및 검색
                </div>
            </div>
            <div class="arrow-horizontal">➡️</div>
            <!-- 3단계: AI 자동 교정 -->
            <div class="process-box" style="background: linear-gradient(135deg, #fff3e0, #ffcc02);">
                <h3 style="color: #e65100;">🤖 AI 자동 교정</h3>
                <p style="color: #f57c00;">AI Auto Correction</p>
                <div style="color: #e65100;">
                    • 문제 품질 개선<br>• 자동 검토<br>• 오류 수정
                </div>
            </div>
            <div class="arrow-horizontal">➡️</div>
            <!-- 4단계: 언어별 번역 -->
            <div class="process-box" style="background: linear-gradient(135deg, #fce4ec, #f8bbd9);">
                <h3 style="color: #880e4f;">🌐 언어별 번역</h3>
                <p style="color: #ad1457;">Language Translation</p>
                <div style="color: #880e4f;">
                    • 수동/자동 번역<br>• AI 검토<br>• 다국어 지원
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 각 단계별 상세 설명
    st.markdown("### 📖 단계별 상세 설명")
    
    # 1단계: 문제 생성 (수동 + 자동)
    with st.expander("📝 1단계: 문제 생성 (Problem Creation)", expanded=True):
        st.markdown("""
        **목적**: 교육 목표에 맞는 고품질 문제를 수동 및 자동으로 생성합니다.
        
        **주요 기능**:
        - 📝 **수동 문제 생성**: 사용자가 직접 주제, 난이도, 유형을 설정하여 문제 생성
        - 🤖 **AI 자동 생성**: AI가 대량의 문제를 자동으로 생성하는 기능
        - 🎯 **주제별 맞춤 생성**: 특정 주제에 맞는 문제를 맞춤형으로 생성
        - 📋 **다양한 유형 지원**: 객관식, 주관식, 서술형 등 다양한 문제 유형
        
        **사용 방법**:
        1. **수동 생성**: 문제 생성 탭에서 주제와 난이도를 선택하여 개별 문제 생성
        2. **자동 생성**: 문제 자동생성 탭에서 대량 문제 생성 설정 후 AI가 자동 생성
        3. 생성된 문제를 검토하고 필요시 수정
        4. 문제 은행에 저장하여 관리
        """)
    
    # 2단계: 문제 은행
    with st.expander("📚 2단계: 문제 은행 (Problem Bank)"):
        st.markdown("""
        **목적**: 생성된 문제를 체계적으로 관리하고 확인할 수 있는 중앙 저장소입니다.
        
        **주요 기능**:
        - 🗄️ **문제 저장소**: 생성된 모든 문제를 데이터베이스에 체계적으로 저장
        - 🔍 **문제 확인**: 저장된 문제를 쉽게 찾고 확인할 수 있는 인터페이스
        - 📂 **분류 체계**: 주제별, 난이도별, 유형별 자동 분류 및 필터링
        - 🏷️ **메타데이터 관리**: 주제, 난이도, 유형 등 상세 정보 관리
        
        **사용 방법**:
        1. 문제 은행 탭에서 저장된 문제 목록 확인
        2. 주제, 난이도, 유형별로 필터링하여 원하는 문제 검색
        3. 문제 상세 정보 확인 및 필요시 수정
        4. 문제 삭제 또는 재분류
        """)
    
    # 3단계: AI 자동 교정
    with st.expander("🤖 3단계: AI 자동 교정 (AI Auto Correction)"):
        st.markdown("""
        **목적**: AI를 활용하여 문제의 품질을 자동으로 개선하고 오류를 수정합니다.
        
        **주요 기능**:
        - 🔧 **자동 문제 개선**: AI가 문제의 명확성, 정확성, 적절성을 자동으로 검토
        - ✍️ **오류 자동 수정**: 문법, 맞춤법, 표현 오류를 자동으로 수정
        - 📊 **품질 평가**: 문제의 난이도와 품질을 AI가 자동으로 평가
        - 🎯 **일관성 확보**: 문제 형식과 표현의 일관성을 자동으로 개선
        
        **사용 방법**:
        1. 문제 교정 탭에서 교정할 문제 선택
        2. AI 자동 교정 기능 실행
        3. 교정 결과를 검토하고 수락 또는 거부
        4. 필요시 추가 수정 후 최종 승인
        """)
    
    # 4단계: 언어별 번역
    with st.expander("🌐 4단계: 언어별 번역 (Language Translation)"):
        st.markdown("""
        **목적**: 다국어 환경에서 사용할 수 있도록 문제를 다양한 언어로 번역합니다.
        
        **주요 기능**:
        - 🌍 **다국어 지원**: 영어, 중국어, 일본어 등 다양한 언어로 번역
        - 🤖 **AI 자동 번역**: AI가 자동으로 번역을 수행하고 품질을 검토
        - 👨‍🏫 **수동 번역 검토**: 전문가가 번역 결과를 검토하고 수정
        - 🎭 **문화적 적응**: 각 언어권의 문화적 특성에 맞는 번역 제공
        
        **사용 방법**:
        1. **자동 번역**: 자동 번역 탭에서 AI가 자동으로 번역 수행
        2. **수동 번역**: 수동 번역 탭에서 전문가가 번역을 검토하고 수정
        3. 번역 결과를 검토하고 필요시 추가 수정
        4. 최종 번역 결과를 승인하고 저장
        """)
    
    # 5단계: 휴먼 피드백
    with st.expander("💬 5단계: 휴먼 피드백 (Human Feedback)"):
        st.markdown("""
        **목적**: 전문가의 피드백을 통해 문제 품질을 최종적으로 보장합니다.
        
        **주요 기능**:
        - 👥 **HITL 프로세스**: Human-in-the-Loop을 통한 전문가 검토
        - 💬 **피드백 수집**: 전문가의 상세한 피드백과 개선 의견 수집
        - 🔄 **피드백 반영**: 수집된 피드백을 바탕으로 문제 개선
        - 📈 **품질 보장**: 최종 품질 검증을 통한 문제 승인 프로세스
        
        **사용 방법**:
        1. 피드백 탭에서 검토가 필요한 문제 확인
        2. 전문가가 문제를 검토하고 피드백 제공
        3. 피드백을 바탕으로 문제 개선 작업 수행
        4. 최종 승인 후 문제 은행에 등록
        """)
    
