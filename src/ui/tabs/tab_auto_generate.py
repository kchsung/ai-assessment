import streamlit as st
import time
import random
import re
from src.constants import ASSESSMENT_AREAS, DIFFICULTY_LEVELS, QUESTION_TYPES

# 임시로 함수들을 직접 정의 (Streamlit Cloud 호환성)
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
    """본문에서 키보드 힌트 토큰과 HTML 태그를 제거하는 함수"""
    if not raw:
        return ""
    text = str(raw)
    # HTML 태그 제거
    text = re.sub(r'<[^>]+>', '', text)
    # 라인 단위로 key/keyboard 안내만 있는 줄 제거
    text = re.sub(r'(?im)^\s*(?:key|keyboard)\s*[:=].*\n?', '', text)
    # inline keyboard_arrow_* 잔여 제거
    text = re.sub(r'(?i)\bkeyboard_arrow_(left|right|up|down)\b', '', text)
    # 연속된 공백 정리
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_answer(question_data):
    """생성된 문제에서 정답을 추출하는 함수"""
    try:
        metadata = question_data.get("metadata", {})
        
        if question_data.get("type") == "multiple_choice":
            # Multiple choice problems: find answer in steps
            steps = metadata.get("steps", [])
            for step in steps:
                if step.get("answer"):
                    return step["answer"]
        else:
            # Subjective problems: find answer in evaluation
            evaluation = metadata.get("evaluation", [])
            if evaluation:
                return evaluation[0] if isinstance(evaluation, list) else str(evaluation)
        
        return "정답 정보 없음"
    except Exception:
        return "정답 추출 실패"

def inject_card_css():
    st.markdown("""
    <style>
    .ql-card {
      border: 1px solid rgba(0,0,0,.1);
      background: #f8f9fa;
      border-radius: 10px;
      padding: 12px 14px;
      margin: 10px 0 14px;
      box-shadow: 0 2px 4px rgba(0,0,0,.05);
    }
    .ql-header { display:flex; align-items:center; gap:8px; margin-bottom:8px; }
    .ql-title { font-size:16px; font-weight:600; line-height:1.3; margin:0; color:#1a1a1a; }
    
    .ql-task { margin-bottom:8px; }
    .ql-task-text { font-size:14px; color:#2d2d2d; line-height:1.4; font-weight:500; }

    .ql-meta {
      display:flex; gap:12px; align-items:center; flex-wrap:wrap;
      font-size:11px; color:#333333;
      margin:2px 0 2px;
    }
    .ql-item { display:inline-flex; gap:6px; align-items:center; }
    .ql-label { opacity:.8; color:#555555; font-weight:500; }
    .ql-value { color:#1a1a1a; font-weight:600; }

    .badge { 
      display:inline-flex; align-items:center; gap:6px;
      border-radius:999px; padding:2px 8px; font-size:11px; line-height:1;
      border:1px solid transparent;
    }
    .badge-success { background: rgba(16,185,129,.15); color:#10b981; border-color: rgba(16,185,129,.35); }
    .badge-warn    { background: rgba(245,158,11,.15); color:#f59e0b; border-color: rgba(245,158,11,.35); }

    .ql-body { font-size:13px; color:#000000; }
    .ql-body .ql-label { font-weight:600; margin-right:6px; color:#000000; }

    /* 혹시 우측 영역에 남아있는 입력 위젯(흰 띠)이 있으면 숨김(선택) */
    [data-testid="stTextInput"] { display:none; }
    [data-testid="stSuccess"] { display:none; }  /* st.success 띠 제거용 */
    </style>
    """, unsafe_allow_html=True)

def render_question_card(i: int, q: dict):
    """문제 카드를 렌더링"""
    title = (q.get("title") or "제목 없음").strip()
    task = q.get("task", "")
    category = q.get("category", "N/A")
    difficulty = q.get("difficulty", "N/A")
    
    # HTML 태그 제거 및 텍스트 정리
    clean_title = sanitize_content(title)
    clean_task = sanitize_content(task)
    
    # 유형은 테이블에 따라 자동 결정
    question_type = q.get("type", "subjective")
    if question_type == "multiple_choice":
        type_display = "객관식"
    else:
        type_display = "주관식"

    # 제목과 Task를 분리해서 표시
    st.markdown(f"""
    <div class="ql-card">
      <div class="ql-header">
        <div class="ql-title">문제 {i}: {clean_title}</div>
      </div>
      
      <div class="ql-task">
        <div class="ql-task-text">{clean_task}</div>
      </div>

      <div class="ql-meta">
        <div class="ql-item"><span class="ql-label">평가 영역</span><span class="ql-value">{category}</span></div>
        <div class="ql-item"><span class="ql-label">난이도</span><span class="ql-value">{difficulty}</span></div>
        <div class="ql-item"><span class="ql-label">유형</span><span class="ql-value">{type_display}</span></div>
      </div>
    </div>
    """, unsafe_allow_html=True)

def render(st):
    """문제 자동생성 탭 렌더링"""
    
    # CSS는 우측 목록 섹션에서 inject_card_css()로 주입
    
    # 세션 상태는 app.py에서 초기화됨
    
    # 좌측: 설정 영역
    with st.container():
        col_left, col_right = st.columns([1, 1])
        
        with col_left:
            st.markdown("### ⚙️ 자동생성 설정")
            
            # 사용자 설정
            st.markdown("**📋 사용자 설정**")
            
            # 평가 영역 선택 (랜덤 옵션 포함)
            area_options = ["랜덤"] + list(ASSESSMENT_AREAS.keys())
            def format_auto_area(x):
                if x == "랜덤":
                    return "🎲 랜덤"
                return x
            
            selected_area = st.selectbox(
                "평가 영역",
                options=area_options,
                format_func=format_auto_area,
                key="tab_auto_area",
                index=0
            )
            
            # 난이도 선택 (랜덤 옵션 포함)
            difficulty_options = ["랜덤"] + list(DIFFICULTY_LEVELS.keys())
            selected_difficulty = st.selectbox(
                "난이도",
                options=difficulty_options,
                format_func=lambda x: "🎲 랜덤" if x == "랜덤" else DIFFICULTY_LEVELS[x],
                key="tab_auto_difficulty",
                index=0
            )
            
            # 문제 유형 선택 (랜덤 옵션 포함)
            type_options = ["랜덤"] + list(QUESTION_TYPES.keys())
            selected_type = st.selectbox(
                "문제 유형",
                options=type_options,
                format_func=lambda x: "🎲 랜덤" if x == "랜덤" else x,
                key="tab_auto_type",
                index=0
            )
            
            # 사용자 추가 요구사항
            additional_requirements = st.text_area(
                "추가 요구사항",
                placeholder="예: 특정 주제나 상황에 대한 문제를 생성해주세요...",
                key="tab_auto_requirements"
            )
            
            st.markdown("---")
            
            # 자동설정
            st.markdown("**🤖 자동설정**")
            
            # 문제 생성 개수
            total_count = st.number_input(
                "생성할 문제 개수",
                min_value=1,
                max_value=50,
                value=st.session_state.auto_generate_total_count,
                key="tab_auto_total_count"
            )
            st.session_state.auto_generate_total_count = total_count
            
            st.markdown("---")
            
            # 버튼 영역
            col_btn1, col_btn2 = st.columns([1, 1])
            
            with col_btn1:
                if st.button("🚀 자동생성 시작", use_container_width=True, type="primary", disabled=st.session_state.auto_generate_running, key="tab_auto_generate_start"):
                    # 자동생성 시작
                    st.session_state.auto_generate_running = True
                    st.session_state.auto_generate_stop_requested = False
                    st.session_state.auto_generated_questions = []
                    st.rerun()
            
            with col_btn2:
                if st.button("⏹️ 중지", use_container_width=True, type="secondary", disabled=not st.session_state.auto_generate_running, key="tab_auto_generate_stop"):
                    # 중지 요청
                    st.session_state.auto_generate_stop_requested = True
                    st.rerun()
            
            # 진행 상태 표시
            if st.session_state.auto_generate_running:
                progress = len(st.session_state.auto_generated_questions) / st.session_state.auto_generate_total_count
                st.progress(progress)
                st.caption(f"진행률: {len(st.session_state.auto_generated_questions)}/{st.session_state.auto_generate_total_count}")
                
                if st.session_state.auto_generate_stop_requested:
                    st.warning("⏹️ 중지 요청됨 - 현재 문제 생성 완료 후 중지됩니다.")
        
        with col_right:
            inject_card_css()           # ✅ 한 번만
            st.markdown("### 📋 생성된 문제 목록")
            
            # 생성된 문제 개수 표시
            generated_count = len(st.session_state.auto_generated_questions)
            total_count = st.session_state.auto_generate_total_count
            
            st.caption(f"생성 진행률: {generated_count}/{total_count}")
            
            if generated_count > 0:
                st.markdown("---")
                for i, q in enumerate(st.session_state.auto_generated_questions, 1):
                    render_question_card(i, q)   # ✅ 여기 한 줄
            
            else:
                st.info("아직 생성된 문제가 없습니다. 좌측에서 자동생성을 시작해보세요.")
    
    # 자동생성 로직 실행 - 한 개씩 생성
    if st.session_state.auto_generate_running and not st.session_state.auto_generate_stop_requested:
        if len(st.session_state.auto_generated_questions) < st.session_state.auto_generate_total_count:
            # 한 개씩 문제 생성
            current_count = len(st.session_state.auto_generated_questions) + 1
            
            with st.spinner(f"문제 생성 중... ({current_count}/{st.session_state.auto_generate_total_count})"):
                generate_next_question(st, selected_area, selected_difficulty, selected_type, additional_requirements)
                st.rerun()  # 한 개 생성 후 즉시 rerun
        else:
            # 모든 문제 생성 완료
            st.session_state.auto_generate_running = False
            st.success("🎉 모든 문제 생성이 완료되었습니다!")
            st.rerun()
    
    elif st.session_state.auto_generate_stop_requested and st.session_state.auto_generate_running:
        # 중지 처리
        st.session_state.auto_generate_running = False
        st.session_state.auto_generate_stop_requested = False
        st.info("⏹️ 자동생성이 중지되었습니다.")
        st.rerun()


def generate_next_question(st, selected_area, selected_difficulty, selected_type, additional_requirements):
    """다음 문제를 생성하는 함수"""
    
    try:
        # 랜덤 선택 처리
        area = selected_area
        if area == "랜덤":
            area = random.choice(list(ASSESSMENT_AREAS.keys()))
        
        difficulty = selected_difficulty
        if difficulty == "랜덤":
            difficulty = random.choice(list(DIFFICULTY_LEVELS.keys()))
        
        question_type = selected_type
        if question_type == "랜덤":
            question_type = random.choice(list(QUESTION_TYPES.keys()))
        
        # AI 생성기로 문제 생성
        generator = st.session_state.get("generator")
        if not generator:
            st.error("AI 생성기가 초기화되지 않았습니다. 설정 탭에서 API 키를 확인해주세요.")
            st.session_state.auto_generate_running = False
            return
        
        # 디버깅: 메서드 존재 여부 확인
        if not hasattr(generator, 'generate_with_ai'):
            st.error(f"❌ generate_with_ai 메서드가 없습니다. 사용 가능한 메서드: {[method for method in dir(generator) if not method.startswith('_')]}")
            st.session_state.auto_generate_running = False
            return
        
        # 문제 생성
        result = generator.generate_with_ai(
            area=area,
            difficulty=difficulty,
            question_type=question_type,
            user_prompt_extra="",
            system_prompt_extra=additional_requirements or ""
        )
        
        if result:
            # 생성된 문제를 DB에 저장 (문제 타입에 따라 적절한 테이블에 저장)
            try:
                db = st.session_state.get("db")
                if db:
                    question_type = result.get("type", "subjective")
                    
                    # 저장 전 상세 로그
                    st.info("🔍 데이터베이스 저장 전 데이터 검증:")
                    st.info(f"  문제 유형: {question_type}")
                    st.info(f"  전체 데이터 키: {list(result.keys())}")
                    
                    # 각 필드별 상세 검증
                    for key, value in result.items():
                        st.info(f"  {key}: {value} (타입: {type(value)})")
                        if key == "steps" and isinstance(value, list):
                            st.info(f"    steps 길이: {len(value)}")
                            if len(value) > 0:
                                st.info(f"    첫 번째 step: {value[0]}")
                    
                    if question_type == "multiple_choice":
                        # 객관식 문제는 questions_multiple_choice 테이블에 저장
                        st.info("📝 객관식 문제 저장 시도 중...")
                        try:
                            save_result = db.save_multiple_choice_question(result)
                            st.info(f"📝 저장 결과: {save_result}")
                            if save_result:
                                st.success("✅ 객관식 문제 저장 성공!")
                            else:
                                st.error("❌ 객관식 문제 저장 실패!")
                        except Exception as save_error:
                            st.error(f"❌ 객관식 문제 저장 중 오류: {save_error}")
                    else:
                        # 주관식 문제는 questions_subjective 테이블에 저장
                        st.info("📝 주관식 문제 저장 시도 중...")
                        try:
                            save_result = db.save_subjective_question(result)
                            st.info(f"📝 저장 결과: {save_result}")
                            if save_result:
                                st.success("✅ 주관식 문제 저장 성공!")
                            else:
                                st.error("❌ 주관식 문제 저장 실패!")
                        except Exception as save_error:
                            st.error(f"❌ 주관식 문제 저장 중 오류: {save_error}")
                else:
                    st.warning("⚠️ DB 연결이 없어 문제를 저장할 수 없습니다.")
            except Exception as e:
                st.error(f"❌ DB 저장 실패: {str(e)}")
            
            # 생성된 문제 정보 정리
            question_title = result.get("title") or result.get("question") or "제목 없음"
            clean_title = sanitize_title(question_title)
            question_info = {
                "title": clean_title,
                "task": result.get("task", ""),
                "category": area,
                "difficulty": difficulty,
                "type": question_type,
                "saved_to_db": True
            }
            
            st.session_state.auto_generated_questions.append(question_info)
            
            # 한 개씩 생성하므로 rerun은 메인 로직에서 처리
            
        else:
            st.error("문제 생성 실패: 알 수 없는 오류")
            st.session_state.auto_generate_running = False
    
    except Exception as e:
        st.error(f"문제 생성 중 오류 발생: {str(e)}")
        st.session_state.auto_generate_running = False


