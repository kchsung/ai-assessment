"""
탭 상태 관리 유틸리티
"""
import streamlit as st
from typing import Optional

# 탭 이름과 인덱스 매핑
TAB_NAMES = [
    "📝 문제 생성", "📚 문제 은행", "💬 피드백 & HITL", "📊 분석 대시보드", 
    "🤖 문제 자동생성", "🔍 문제 검토(JSON)", "🤖 자동 문제 검토", 
    "🔍 제미나이 수동 검토", "🤖 제미나이 자동 검토", "⚙️ 설정"
]

def get_current_tab_index() -> int:
    """현재 활성 탭의 인덱스를 반환합니다."""
    # URL 파라미터를 우선적으로 확인
    query_params = st.query_params
    url_tab = query_params.get("tab")
    
    if url_tab is not None:
        try:
            url_tab_index = int(url_tab)
            if 0 <= url_tab_index < len(TAB_NAMES):
                st.session_state.current_tab = url_tab_index
                return url_tab_index
        except (ValueError, TypeError):
            pass
    
    # URL 파라미터가 없거나 유효하지 않은 경우 세션 상태 확인
    if "current_tab" not in st.session_state:
        st.session_state.current_tab = 0
    
    return st.session_state.current_tab

def set_current_tab(tab_index: int) -> None:
    """현재 탭을 설정합니다."""
    if 0 <= tab_index < len(TAB_NAMES):
        st.session_state.current_tab = tab_index
        st.query_params.tab = str(tab_index)

def get_current_tab_name() -> str:
    """현재 활성 탭의 이름을 반환합니다."""
    tab_index = get_current_tab_index()
    return TAB_NAMES[tab_index] if tab_index < len(TAB_NAMES) else "알 수 없음"

def safe_rerun(tab_index: Optional[int] = None) -> None:
    """
    탭 상태를 유지하면서 안전하게 rerun을 실행합니다.
    
    Args:
        tab_index: 유지할 탭 인덱스. None이면 현재 탭 유지
    """
    if tab_index is not None:
        set_current_tab(tab_index)
    else:
        # 현재 탭 상태를 URL 파라미터에 저장
        current_tab = get_current_tab_index()
        st.query_params.tab = str(current_tab)
    
    # 탭 상태 복원을 위한 플래그 설정
    st.session_state._tab_restore_needed = True
    st.session_state._tab_restore_index = tab_index if tab_index is not None else current_tab
    
    st.rerun()

def restore_tab_if_needed() -> None:
    """필요한 경우 탭 상태를 복원합니다."""
    if st.session_state.get("_tab_restore_needed", False):
        restore_index = st.session_state.get("_tab_restore_index", 0)
        set_current_tab(restore_index)
        # 복원 완료 후 플래그 제거
        del st.session_state._tab_restore_needed
        del st.session_state._tab_restore_index

def force_tab_state_after_creation() -> None:
    """st.tabs 생성 후 탭 상태를 강제로 설정합니다."""
    current_tab = get_current_tab_index()
    
    # URL 파라미터를 강제로 설정하여 탭 상태 동기화
    st.query_params.tab = str(current_tab)
    
    # 탭 변경 감지 및 상태 동기화를 위한 JavaScript 추가
    import streamlit.components.v1 as components
    
    # Streamlit의 탭 버튼 선택자 (여러 선택자 시도)
    tab_selectors = [
        "div[data-testid='stTabs'] button",
        ".stTabs button",
        "[data-testid='stTabs'] > div > button",
        "button[data-testid='stTabs']"
    ]
    
    js_code = """
    <script>
    function setupTabMonitoring() {
        console.log('=== 탭 모니터링 설정 시작 ===');
        
        // 모든 가능한 탭 선택자 시도
        const allSelectors = [
            "div[data-testid='stTabs'] button",
            ".stTabs button",
            "[data-testid='stTabs'] > div > button",
            "button[data-testid='stTabs']",
            "div[data-testid='stTabs'] > div > div > button",
            ".stTabs > div > button",
            "button[role='tab']",
            "[role='tablist'] button"
        ];
        
        let tabButtons = null;
        let workingSelector = '';
        
        // 각 선택자 시도
        for (let sel of allSelectors) {
            const buttons = document.querySelectorAll(sel);
            console.log('선택자 "' + sel + '" 결과:', buttons.length, '개 버튼');
            
            if (buttons.length > 0) {
                // 버튼 텍스트 확인
                const buttonTexts = Array.from(buttons).map(btn => btn.textContent.trim());
                console.log('버튼 텍스트들:', buttonTexts);
                
                // 탭 관련 텍스트가 있는지 확인
                if (buttonTexts.some(text => text.includes('문제') || text.includes('탭') || text.includes('생성'))) {
                    tabButtons = buttons;
                    workingSelector = sel;
                    break;
                }
            }
        }
        
        console.log('최종 선택된 선택자:', workingSelector);
        console.log('찾은 탭 버튼 수:', tabButtons ? tabButtons.length : 0);
        
        if (tabButtons && tabButtons.length > 0) {
            // 각 탭 버튼에 클릭 이벤트 리스너 추가
            tabButtons.forEach((button, index) => {
                // 기존 이벤트 리스너 제거 (중복 방지)
                button.removeEventListener('click', handleTabClick);
                
                // 새 이벤트 리스너 추가
                button.addEventListener('click', handleTabClick);
                
                function handleTabClick(event) {
                    console.log('=== 탭 클릭 감지 ===');
                    console.log('탭 인덱스:', index);
                    console.log('탭 텍스트:', button.textContent.trim());
                    console.log('이벤트:', event);
                    
                    // URL 파라미터 업데이트
                    const url = new URL(window.location);
                    url.searchParams.set('tab', index);
                    window.history.replaceState({}, '', url);
                    
                    console.log('URL 업데이트됨:', url.toString());
                    
                    // 페이지 새로고침 (Streamlit 상태 동기화를 위해)
                    setTimeout(() => {
                        window.location.reload();
                    }, 100);
                }
            });
            
            // 첫 번째 탭이 아닌 경우 강제 클릭
            if (""" + str(current_tab) + """ != 0 && tabButtons.length > """ + str(current_tab) + """) {
                const targetTab = tabButtons[""" + str(current_tab) + """];
                console.log('대상 탭:', targetTab);
                console.log('탭 텍스트:', targetTab ? targetTab.textContent.trim() : '없음');
                
                if (targetTab) {
                    // 활성 상태 확인
                    const isActive = targetTab.classList.contains('stTabs__tab--active') || 
                                   targetTab.getAttribute('aria-selected') === 'true' ||
                                   targetTab.classList.contains('active');
                    
                    console.log('현재 활성 상태:', isActive);
                    
                    if (!isActive) {
                        console.log('탭 강제 클릭: """ + TAB_NAMES[current_tab] + """');
                        targetTab.click();
                        
                        // 클릭 후 상태 확인
                        setTimeout(() => {
                            const newActive = targetTab.classList.contains('stTabs__tab--active') || 
                                            targetTab.getAttribute('aria-selected') === 'true' ||
                                            targetTab.classList.contains('active');
                            console.log('클릭 후 활성 상태:', newActive);
                        }, 100);
                    } else {
                        console.log('탭이 이미 활성 상태입니다');
                    }
                }
            }
        } else {
            console.log('탭 버튼을 찾을 수 없습니다. DOM 구조 확인 중...');
            
            // DOM 구조 디버깅
            const tabsContainer = document.querySelector('[data-testid="stTabs"]');
            if (tabsContainer) {
                console.log('탭 컨테이너 발견:', tabsContainer);
                console.log('탭 컨테이너 HTML:', tabsContainer.outerHTML);
            } else {
                console.log('탭 컨테이너를 찾을 수 없습니다');
            }
        }
    }
    
    // DOM이 로드된 후 실행
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', setupTabMonitoring);
    } else {
        setupTabMonitoring();
    }
    
    // 추가로 약간의 지연 후에도 실행 (Streamlit 렌더링 완료 대기)
    setTimeout(setupTabMonitoring, 200);
    setTimeout(setupTabMonitoring, 500);
    setTimeout(setupTabMonitoring, 1000);
    setTimeout(setupTabMonitoring, 2000);
    </script>
    """
    
    components.html(js_code, height=0)
    
    # 디버깅 정보
    import os
    if os.getenv("DEBUG") == "true":
        st.sidebar.success(f"탭 상태 강제 설정: {TAB_NAMES[current_tab]} (인덱스: {current_tab})")
        st.sidebar.info(f"URL 파라미터: {st.query_params.get('tab', '없음')}")
        st.sidebar.info("탭 변경 감지 활성화됨")

def ensure_tab_state(tab_index: int) -> None:
    """
    특정 탭에서 실행될 때 탭 상태를 보장합니다.
    
    Args:
        tab_index: 현재 탭의 인덱스
    """
    set_current_tab(tab_index)

def debug_tab_state() -> None:
    """디버깅용 탭 상태 정보를 표시합니다."""
    import os
    if os.getenv("DEBUG") == "true":
        current_tab = get_current_tab_index()
        current_name = get_current_tab_name()
        url_tab = st.query_params.get("tab", "없음")
        
        st.sidebar.info(f"현재 탭: {current_name} (인덱스: {current_tab})")
        st.sidebar.info(f"URL 탭: {url_tab}")
        
        # 탭 상태 복원 플래그 표시
        if st.session_state.get("_tab_restore_needed", False):
            restore_index = st.session_state.get("_tab_restore_index", 0)
            st.sidebar.warning(f"탭 복원 대기 중: {TAB_NAMES[restore_index]} (인덱스: {restore_index})")
        
        # 세션 상태 정보
        st.sidebar.info(f"세션 current_tab: {st.session_state.get('current_tab', '없음')}")
        
        # 수동 탭 동기화 버튼
        st.sidebar.markdown("---")
        st.sidebar.markdown("**수동 탭 동기화**")
        
        # 각 탭별 동기화 버튼
        for i, tab_name in enumerate(TAB_NAMES):
            if st.sidebar.button(f"→ {tab_name}", key=f"manual_tab_sync_{i}"):
                st.session_state.current_tab = i
                st.query_params.tab = str(i)
                st.rerun()
        
        # 현재 탭 강제 설정 버튼
        if st.sidebar.button("🔄 현재 탭 강제 설정", key="force_current_tab"):
            st.query_params.tab = str(current_tab)
            st.rerun()

def monitor_tab_changes() -> None:
    """탭 변경을 모니터링하고 상태를 동기화합니다."""
    # URL 파라미터에서 현재 탭 확인
    query_params = st.query_params
    url_tab = query_params.get("tab")
    
    # URL 파라미터가 있으면 우선적으로 사용
    if url_tab is not None:
        try:
            url_tab_index = int(url_tab)
            if 0 <= url_tab_index < len(TAB_NAMES):
                # URL 파라미터와 세션 상태가 다르면 동기화
                if st.session_state.get("current_tab") != url_tab_index:
                    st.session_state.current_tab = url_tab_index
                    # 디버깅 정보
                    import os
                    if os.getenv("DEBUG") == "true":
                        st.sidebar.info(f"탭 상태 동기화: {TAB_NAMES[url_tab_index]} (인덱스: {url_tab_index})")
        except (ValueError, TypeError):
            pass
    else:
        # URL 파라미터가 없으면 세션 상태를 URL에 반영
        current_tab = st.session_state.get("current_tab", 0)
        st.query_params.tab = str(current_tab)

def force_tab_sync_from_content() -> None:
    """현재 렌더링되는 탭 내용을 기반으로 탭 상태를 강제 동기화합니다."""
    # 각 탭의 고유한 세션 상태 키를 기반으로 현재 탭 감지
    current_tab_index = -1
    
    # 각 탭의 고유한 세션 상태 키 확인
    tab_indicators = {
        8: ["gemini_auto_review_selected_area", "gemini_auto_review_problems", "gemini_auto_review_running"],
        7: ["selected_gemini_manual_review_problem", "gemini_manual_review_result"],
        6: ["selected_review_question", "mapped_review_data"],
        5: ["selected_review_question", "mapped_review_data"],
        4: ["auto_generate_problems", "auto_generate_running"],
        3: ["dashboard_data", "dashboard_filters"],
        2: ["hitl_feedback", "hitl_problems"],
        1: ["bank_problems", "bank_filters"],
        0: ["last_generated", "show_prompts"]
    }
    
    # 각 탭의 고유한 세션 상태 키가 있는지 확인
    for tab_index, indicators in tab_indicators.items():
        if any(key in st.session_state for key in indicators):
            current_tab_index = tab_index
            break
    
    # 감지된 탭이 있으면 상태 동기화
    if current_tab_index != -1:
        if st.session_state.get("current_tab") != current_tab_index:
            st.session_state.current_tab = current_tab_index
            st.query_params.tab = str(current_tab_index)
            
            # 디버깅 정보
            import os
            if os.getenv("DEBUG") == "true":
                st.sidebar.success(f"탭 세션 상태 기반 동기화: {TAB_NAMES[current_tab_index]} (인덱스: {current_tab_index})")
    
    return current_tab_index

def get_tab_restoration_info() -> dict:
    """탭 복원 정보를 반환합니다."""
    return {
        "needed": st.session_state.get("_tab_restore_needed", False),
        "index": st.session_state.get("_tab_restore_index", 0),
        "name": TAB_NAMES[st.session_state.get("_tab_restore_index", 0)]
    }
