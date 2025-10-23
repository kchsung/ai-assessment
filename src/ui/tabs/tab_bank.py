import streamlit as st
from src.constants import ASSESSMENT_AREAS, DIFFICULTY_LEVELS, QUESTION_TYPES
import time
import json
from functools import lru_cache

# 탭 상태 관리 코드 제거

# 공통 유틸리티 함수
def _parse_json_field(value, default_if_empty):
    """
    문자열/JSON 이중 케이스를 모두 안전하게 리스트/딕트로 변환.
    - value가 None/"" -> default_if_empty 반환
    - value가 str -> json.loads 시도 (공백/'null'/'[]' 처리)
    - value가 list/dict -> 그대로 반환
    """
    if value is None:
        return default_if_empty
    if isinstance(value, (list, dict)):
        return value
    if isinstance(value, str):
        s = value.strip()
        if s in ("", "null", "NULL"):
            return default_if_empty
        try:
            return json.loads(s)
        except json.JSONDecodeError:
            # DB에 따옴표 이스케이프가 꼬인 경우 등 대비
            return default_if_empty
    return default_if_empty

def _steps_text_for_search(steps):
    """steps에서 검색 가능한 텍스트 추출"""
    steps_list = _parse_json_field(steps, default_if_empty=[])
    bucket = []
    for s in steps_list:
        if isinstance(s, dict):
            if s.get('title'):
                bucket.append(str(s['title']))
            if s.get('question'):
                bucket.append(str(s['question']))
            for opt in s.get('options', []):
                if isinstance(opt, dict) and opt.get('text'):
                    bucket.append(str(opt['text']))
    return " ".join(bucket).lower()

# 캐시 설정
@st.cache_data(ttl=300)  # 5분 캐시
def get_cached_questions(filters_hash, data_version):
    """캐시된 문제 목록 조회 - 새로운 테이블들에서 통합 조회 (버전 기반 캐시 무효화)"""
    try:
        # 객관식과 주관식 문제를 모두 조회하여 통합
        multiple_choice_questions = st.session_state.db.get_multiple_choice_questions({})
        subjective_questions = st.session_state.db.get_subjective_questions({})
        
        # 두 리스트를 통합하고 호환성을 위해 기존 형식으로 변환
        all_questions = []
        
        # 객관식 문제 추가
        for q in multiple_choice_questions:
            q['type'] = 'multiple_choice'  # 타입 명시
            q['question_type'] = '객관식'  # 한국어 타입명
            # title 필드 통일 (problem_title -> title)
            if 'problem_title' in q:
                q['title'] = q['problem_title']
            # ✅ steps 정규화 (JSON 문자열 -> 리스트 변환)
            q['steps'] = _parse_json_field(q.get('steps'), default_if_empty=[])
            # area 필드가 있다면 제거 (새로운 구조에서는 사용하지 않음)
            if 'area' in q:
                del q['area']
            all_questions.append(q)
        
        # 주관식 문제 추가
        for q in subjective_questions:
            q['type'] = 'subjective'  # 타입 명시
            q['question_type'] = '주관식'  # 한국어 타입명
            # area 필드가 있다면 제거 (새로운 구조에서는 사용하지 않음)
            if 'area' in q:
                del q['area']
            all_questions.append(q)
        
        return all_questions
    except Exception as e:
        st.error(f"문제 조회 실패: {e}")
        # 기존 방식으로 폴백
        return st.session_state.db.get_questions({})

def get_questions_hash(filters):
    """필터를 해시로 변환하여 캐시 키 생성"""
    return hash(str(sorted(filters.items())))

def filter_questions_cached(questions, filters, search_text=""):
    """클라이언트 측에서 문제 필터링"""
    filtered = questions
    
    # 평가 영역 필터링
    if filters.get("category"):
        filtered = [q for q in filtered if q.get("category") == filters["category"]]
    
    # 난이도 필터링
    if filters.get("difficulty"):
        filtered = [q for q in filtered if q.get("difficulty") == filters["difficulty"]]
    
    # 유형 필터링
    if filters.get("type"):
        filtered = [q for q in filtered if q.get("type") == filters["type"]]
    
    # 검색어 필터링 (title, task, scenario, steps 등에서 검색)
    if search_text.strip():
        search_term = search_text.strip().lower()
        search_filtered = []
        for q in filtered:
            hay = [
                (q.get("title", "") or "").lower(),
                (q.get("task", "") or "").lower(),
                (q.get("scenario", "") or "").lower(),
                (q.get("question", "") or q.get("question_text", "") or "").lower(),
                _steps_text_for_search(q.get("steps"))  # ✅ steps 내용도 검색
            ]
            if any(search_term in h for h in hay):
                search_filtered.append(q)
        filtered = search_filtered
    
    return filtered

def render(st):
    # 검색 필터
    c1, c2, c3, c4, c5 = st.columns([1, 1, 1, 2, 1])
    with c1:
        def format_bank_area(v):
            if v == "전체":
                return "전체"
            return v
        
        f_area = st.selectbox("평가 영역", ["전체"] + list(ASSESSMENT_AREAS.keys()), 
                             format_func=format_bank_area, key="bank_area_v2", index=0)
    with c2:
        f_diff = st.selectbox("난이도", ["전체"] + list(DIFFICULTY_LEVELS.keys()), 
                             format_func=lambda v: "전체" if v=="전체" else DIFFICULTY_LEVELS[v], key="bank_difficulty_v2", index=0)
    with c3:
        f_type = st.selectbox("유형", ["전체"] + list(QUESTION_TYPES.keys()), 
                             format_func=lambda v: "전체" if v=="전체" else v, key="bank_type_v2", index=0)
    with c4:
        search_text = st.text_input("검색어", placeholder="문제 내용으로 검색...", key="question_search_input_v2")
    with c5:
        st.markdown("<br>", unsafe_allow_html=True)  # 공간 추가
        col_search, col_refresh = st.columns([2, 1])
        with col_search:
            if st.button("🔍 검색", use_container_width=True, key="bank_search_v2"):
                filters = {}
                if f_area != "전체": 
                    filters["category"] = ASSESSMENT_AREAS[f_area]
                if f_diff != "전체": 
                    filters["difficulty"] = DIFFICULTY_LEVELS[f_diff]
                if f_type != "전체": 
                    filters["type"] = f_type
                
                # 캐시된 전체 문제 목록 가져오기 (버전 기반 캐시)
                with st.spinner("검색 중..."):
                    # DB 최신 버전 토큰 조회
                    data_version = st.session_state.db.get_questions_data_version()
                    all_questions = get_cached_questions(get_questions_hash(filters), data_version)
                    
                    # 클라이언트 측에서 필터링 (성능 개선)
                    questions = filter_questions_cached(all_questions, filters, search_text)
                
                st.session_state.filtered_questions = questions
                st.session_state.current_filters = filters
                st.session_state.current_page = 1  # 검색 시 첫 페이지로 리셋
                st.session_state.selected_question_id = None  # 검색 시 선택 초기화
                st.rerun()
        
        with col_refresh:
            if st.button("🔄", use_container_width=True, key="bank_refresh_v2", help="캐시 새로고침"):
                st.cache_data.clear()
                st.rerun()
    
    # 초기 로드 시 전체 문제 표시 (캐시 활용)
    if not st.session_state.get("filtered_questions"):
        if st.session_state.db is None:
            st.error("데이터베이스 연결이 초기화되지 않았습니다. Edge Function 설정을 확인하세요.")
            st.session_state.filtered_questions = []
        else:
            # 캐시된 데이터 사용 (버전 기반 캐시)
            with st.spinner("문제 목록을 불러오는 중..."):
                data_version = st.session_state.db.get_questions_data_version()
                st.session_state.filtered_questions = get_cached_questions(get_questions_hash({}), data_version)

    # 좌우 분할 레이아웃
    col_left, col_right = st.columns([1, 2])
    
    # 좌측: 검색 결과 카드뷰 (페이지네이션 적용)
    with col_left:
        st.markdown("### 📋 검색 결과")
        qs = st.session_state.get("filtered_questions", [])
        
        # qs가 리스트인지 확인하고, 아니면 빈 리스트로 초기화
        if not isinstance(qs, list):
            print(f"⚠️ filtered_questions가 리스트가 아님: {type(qs)}")
            qs = []
            st.session_state.filtered_questions = qs
        
        if qs:
            st.markdown(f"**총 {len(qs)}개 문제**")
            
            # 페이지네이션 설정
            items_per_page = 20
            total_pages = (len(qs) - 1) // items_per_page + 1
            current_page = st.session_state.get("current_page", 1)
            
            # 페이지네이션 컨트롤
            if total_pages > 1:
                col_prev, col_page, col_next = st.columns([1, 2, 1])
                with col_prev:
                    if st.button("◀️ 이전", disabled=current_page <= 1):
                        st.session_state.current_page = max(1, current_page - 1)
                        st.rerun()
                with col_page:
                    st.markdown(f"**{current_page}/{total_pages} 페이지**")
                with col_next:
                    if st.button("다음 ▶️", disabled=current_page >= total_pages):
                        st.session_state.current_page = min(total_pages, current_page + 1)
                        st.rerun()
            
            # 현재 페이지의 문제들만 표시
            start_idx = (current_page - 1) * items_per_page
            end_idx = start_idx + items_per_page
            page_questions = qs[start_idx:end_idx]
            
            # 문제 선택을 위한 selectbox 사용 (페이지 새로고침 없음)
            question_options = {}
            for q in page_questions:
                title = q.get("title", "(제목 없음)")
                difficulty = q.get("difficulty", "N/A")
                question_type = q.get("question_type", "N/A")
                
                # steps 데이터 유무 표시 (보수적 처리)
                steps = _parse_json_field(q.get("steps"), default_if_empty=[])
                steps_indicator = "📋" if steps and len(steps) > 0 else "📄"
                
                display_text = f"{steps_indicator} {title} ({difficulty})-{question_type}"
                question_options[display_text] = q
            
            # 현재 선택된 문제 찾기
            current_selection = None
            if st.session_state.get("selected_question_id"):
                for display_text, q in question_options.items():
                    if q["id"] == st.session_state.selected_question_id:
                        current_selection = display_text
                        break
            
            # 문제 선택 드롭다운
            selected_display = st.selectbox(
                "문제를 선택하세요:",
                options=list(question_options.keys()),
                index=list(question_options.keys()).index(current_selection) if current_selection else 0,
                key="question_selector_v2"
            )
            
            # 선택된 문제를 세션 상태에 저장
            if selected_display and selected_display in question_options:
                selected_q = question_options[selected_display]
                st.session_state.selected_question_id = selected_q["id"]
                st.session_state.selected_question = selected_q
        else:
            st.info("검색 결과가 없습니다.")
    
    # 우측: 선택된 문제 상세보기
    with col_right:
        st.markdown("### 📖 문제 상세보기")
        
        selected_q = st.session_state.get("selected_question")
        if selected_q:
            # 문제 기본 정보
            st.info(f"**문제 ID**: {selected_q['id']}  \n**평가 영역**: {selected_q.get('category', 'N/A')}  \n**난이도**: {selected_q['difficulty']}  \n**유형**: {selected_q.get('question_type', 'N/A')}")
            
            # Task를 상단에 표시 (공통)
            if selected_q.get("task"):
                st.markdown("### 🎯 Task")
                st.markdown(selected_q["task"])
            
            meta = selected_q.get("metadata", {})
            
            # 객관식 문제 상세 표시
            if selected_q.get("type") == "multiple_choice":
                st.markdown("### 📋 객관식 문제 상세")
                
                # ✅ steps를 한 번 더 안전 파싱 (혹시 모를 잔존 문자열 대비)
                steps = _parse_json_field(selected_q.get("steps"), default_if_empty=[])
                if steps and len(steps) > 0:
                    # 스텝별 탭으로 표시
                    if len(steps) > 1:
                        step_tabs = st.tabs([f"Step {i+1}" for i in range(len(steps))])
                        for i, step in enumerate(steps):
                            with step_tabs[i]:
                                st.markdown(f"**{step.get('title', f'Step {i+1} 문제')}**")
                                st.markdown(step.get('question', ''))
                                
                                # 선택지 표시
                                if step.get('options'):
                                    st.markdown("**선택지:**")
                                    for j, opt in enumerate(step['options']):
                                        option_text = opt.get('text', f'선택지 {j+1}')
                                        st.markdown(f"• {option_text}")
                                        if opt.get('feedback'):
                                            st.caption(f"💡 피드백: {opt['feedback']}")
                                
                                # 정답 표시
                                if step.get('answer'):
                                    st.markdown(f"**정답: {step['answer']}**")
                                
                                # 추가 정보 표시
                                if step.get('explanation'):
                                    st.markdown("**해설:**")
                                    st.markdown(step['explanation'])
                    else:
                        # 단일 스텝인 경우
                        step = steps[0]
                        st.markdown(f"**{step.get('title', '문제')}**")
                        st.markdown(step.get('question', ''))
                        
                        # 선택지 표시
                        if step.get('options'):
                            st.markdown("**선택지:**")
                            for j, opt in enumerate(step['options']):
                                option_text = opt.get('text', f'선택지 {j+1}')
                                st.markdown(f"• {option_text}")
                                if opt.get('feedback'):
                                    st.caption(f"💡 피드백: {opt['feedback']}")
                        
                        # 정답 표시
                        if step.get('answer'):
                            st.markdown(f"**정답: {step['answer']}**")
                        
                        # 추가 정보 표시
                        if step.get('explanation'):
                            st.markdown("**해설:**")
                            st.markdown(step['explanation'])
                else:
                    # steps 데이터가 없을 때 기본 정보 표시
                    st.warning("⚠️ 이 문제의 단계(`steps`)가 비어 있어 기본 정보를 표시합니다. 🔄(전체 새로고침) 또는 **이 문제만 강제 최신화**를 눌러 최신 상태를 확인하세요.")
                    
                    # 기본 문제 정보 표시
                    if selected_q.get("problem_title"):
                        st.markdown(f"**제목:** {selected_q['problem_title']}")
                    
                    if selected_q.get("scenario"):
                        st.markdown("**📖 Scenario**")
                        st.markdown(selected_q["scenario"])
                    
                    if selected_q.get("topic_summary"):
                        st.markdown("**📝 주제 요약**")
                        st.markdown(selected_q["topic_summary"])
                    
                    if selected_q.get("estimated_time"):
                        st.markdown(f"**⏱️ 예상 시간:** {selected_q['estimated_time']}")
                    
                    # 문제가 steps 없이 저장된 경우 안내 메시지
                    st.markdown("---")
                    st.markdown("**💡 참고사항**")
                    st.markdown("이 문제는 단계별 구성 없이 시나리오 기반으로 구성된 객관식 문제입니다. 문제 생성 시 단계별 구성이 필요하다면 문제 생성 탭에서 다시 생성해주세요.")
                    
                    # 개발자용 디버깅 정보 (접을 수 있도록)
                    with st.expander("🔧 개발자 디버깅 정보", expanded=False):
                        st.caption(f"Debug: steps 데이터 = {steps}")
                        st.caption(f"Debug: steps 타입 = {type(steps)}")
                        st.caption(f"Debug: 전체 데이터 키 = {list(selected_q.keys())}")
                        
                        # 원본 steps 데이터 확인
                        raw_steps = selected_q.get("steps")
                        st.caption(f"Debug: 원본 steps = {raw_steps}")
                        st.caption(f"Debug: 원본 steps 타입 = {type(raw_steps)}")
                        
                        # 전체 데이터 구조 확인
                        st.json(selected_q)
                        
                        # steps 데이터 수동 업데이트 기능 (개발자용)
                        st.markdown("---")
                        st.markdown("**🔧 Steps 데이터 수동 업데이트**")
                        st.markdown("아래 텍스트 영역에 올바른 steps JSON 데이터를 입력하고 업데이트 버튼을 클릭하세요.")
                        
                        # 예시 steps 데이터 표시
                        example_steps = [
                            {
                                "step": 1,
                                "title": "맥락·목표·제약 정리",
                                "answer": "C",
                                "options": [
                                    {
                                        "id": "A",
                                        "text": "지난 10개 숏츠의 평균 조회수와 좋아요 수만 요약해줘.",
                                        "weight": 0.6,
                                        "feedback": "정답이 아닙니다. 조회수/좋아요 요약은 필요하지만, 목표 지표(CTR·WTR·구독전환) 정렬, 제약(예산·시간·장비), 경쟁 채널 고려가 빠졌습니다.",
                                        "ref_paths": ["ref.analytics.summary"]
                                    }
                                ],
                                "question": "아래 중 초기 맥락을 빠르게 정리하고 목표·제약을 명확히 해 이후 분석·제작의 기준을 세우기 위한 가장 적절한 AI 지시문은 무엇인가요?",
                                "ref_paths": ["ref.metrics.wtr15", "ref.metrics.ctr"]
                            }
                        ]
                        
                        st.markdown("**예시 steps 데이터:**")
                        st.code(str(example_steps), language="json")
                        
                        new_steps_json = st.text_area(
                            "새로운 steps JSON 데이터 입력:",
                            value=str(steps) if steps else "[]",
                            height=200,
                            key=f"steps_update_{selected_q['id']}"
                        )
                        
                        if st.button("Steps 데이터 업데이트", key=f"update_steps_{selected_q['id']}"):
                            try:
                                import json
                                parsed_steps = json.loads(new_steps_json)
                                
                                # 데이터베이스 업데이트
                                success = st.session_state.db.update_multiple_choice_question(
                                    selected_q['id'], 
                                    {'steps': parsed_steps}
                                )
                                
                                if success:
                                    st.success("✅ Steps 데이터가 성공적으로 업데이트되었습니다!")
                                    st.cache_data.clear()  # 캐시 클리어
                                    st.rerun()
                                else:
                                    st.error("❌ Steps 데이터 업데이트에 실패했습니다.")
                                    
                            except json.JSONDecodeError as e:
                                st.error(f"❌ JSON 형식 오류: {e}")
                            except Exception as e:
                                st.error(f"❌ 업데이트 오류: {e}")
            
            # 주관식 문제 상세 표시
            elif selected_q.get("type") == "subjective":
                st.markdown("### 📝 주관식 문제 상세")
                
                # scenario 표시
                if selected_q.get("scenario"):
                    st.markdown("**📖 Scenario**")
                    st.markdown(selected_q["scenario"])
                elif meta.get("scenario"):
                    st.markdown("**📖 Scenario**")
                    st.markdown(meta["scenario"])
                
                # 목표 표시
                if selected_q.get("goal"):
                    st.markdown("**🎯 목표**")
                    if isinstance(selected_q["goal"], list):
                        for goal in selected_q["goal"]:
                            st.markdown(f"- {goal}")
                    else:
                        st.markdown(f"- {selected_q['goal']}")
                elif meta.get("goal"):
                    st.markdown("**🎯 목표**")
                    for goal in meta["goal"]:
                        st.markdown(f"- {goal}")
                
                # 요구사항 표시
                if selected_q.get("requirements"):
                    st.markdown("**📋 요구사항**")
                    if isinstance(selected_q["requirements"], list):
                        for req in selected_q["requirements"]:
                            st.markdown(f"- {req}")
                    else:
                        st.markdown(f"- {selected_q['requirements']}")
                
                # 제약사항 표시
                if selected_q.get("constraints"):
                    st.markdown("**⚠️ 제약사항**")
                    if isinstance(selected_q["constraints"], list):
                        for constraint in selected_q["constraints"]:
                            st.markdown(f"- {constraint}")
                    else:
                        st.markdown(f"- {selected_q['constraints']}")
                
                # 가이드 표시
                if selected_q.get("guide"):
                    st.markdown("**📚 가이드**")
                    if isinstance(selected_q["guide"], dict):
                        for key, value in selected_q["guide"].items():
                            st.markdown(f"**{key}:** {value}")
                    else:
                        st.markdown(f"- {selected_q['guide']}")
                
                # 평가 기준 표시
                if selected_q.get("evaluation"):
                    st.markdown("**📊 평가 기준**")
                    if isinstance(selected_q["evaluation"], list):
                        for eval_item in selected_q["evaluation"]:
                            st.markdown(f"- {eval_item}")
                    else:
                        st.markdown(f"- {selected_q['evaluation']}")
            
            # 기존 방식으로 fallback
            else:
                st.markdown("### 문제")
                st.markdown(selected_q.get("question","(없음)"))
                if meta.get("scenario"):
                    st.markdown("**📖 문제 상황**")
                    st.markdown(meta["scenario"])
                if meta.get("goal"):
                    st.markdown("**🎯 목표**")
                    for goal in meta["goal"]:
                        st.markdown(f"- {goal}")
            
            
            # 강제 최신화 버튼 (응급처치)
            st.markdown("---")
            col_refresh1, col_refresh2 = st.columns([2, 1])
            with col_refresh1:
                st.markdown("**🔄 데이터 새로고침**")
            with col_refresh2:
                if st.button("이 문제만 강제 최신화", key=f"force_refresh_{selected_q['id']}", help="캐시를 우회하여 최신 데이터를 가져옵니다"):
                    try:
                        # 캐시 우회하여 단건 조회
                        fresh = st.session_state.db.get_multiple_choice_question_by_id(selected_q["id"])
                        if fresh:
                            # ✅ 정규화: title, steps
                            if 'problem_title' in fresh:
                                fresh['title'] = fresh['problem_title']
                            fresh['steps'] = _parse_json_field(fresh.get('steps'), default_if_empty=[])
                            fresh['type'] = fresh.get('type', 'multiple_choice')
                            fresh['question_type'] = fresh.get('question_type', '객관식')
                            
                            # 세션 교체 & 전역 캐시도 비움
                            st.session_state.selected_question = fresh
                            st.cache_data.clear()
                            st.success("✅ 최신 데이터로 갱신했습니다!")
                            st.rerun()
                        else:
                            st.error("❌ 최신 데이터 조회에 실패했습니다.")
                    except Exception as e:
                        st.error(f"❌ 오류 발생: {e}")
            
            # 피드백 통계 표시 (캐시 활용)
            @st.cache_data(ttl=60)  # 1분 캐시
            def get_cached_feedback_stats(question_id):
                return st.session_state.db.get_feedback_stats(question_id)
            
            stats = get_cached_feedback_stats(selected_q["id"])
            if stats and isinstance(stats, dict):
                st.markdown("### 📊 피드백 통계")
                col_stat1, col_stat2, col_stat3 = st.columns(3)
                with col_stat1:
                    feedback_count = stats.get('feedback_count', 0)
                    st.metric("피드백 수", feedback_count)
                with col_stat2:
                    avg_difficulty = stats.get('avg_difficulty', 0)
                    st.metric("평균 난이도", f"{avg_difficulty:.1f}")
                with col_stat3:
                    avg_relevance = stats.get('avg_relevance', 0)
                    st.metric("평균 관련성", f"{avg_relevance:.1f}")
            else:
                st.info("피드백 통계를 불러올 수 없습니다.")
        else:
            st.info("좌측에서 문제를 선택하면 상세 내용이 여기에 표시됩니다.")