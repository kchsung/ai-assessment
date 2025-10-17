import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from functools import lru_cache

@st.cache_data(ttl=300)  # 5분 캐시
def get_cached_dashboard_data():
    """대시보드 데이터 캐시 - 새로운 테이블들에서 통합 조회"""
    try:
        # 객관식과 주관식 문제를 모두 조회하여 통합
        multiple_choice_questions = st.session_state.db.get_multiple_choice_questions({})
        subjective_questions = st.session_state.db.get_subjective_questions({})
        
        # 두 리스트를 통합하고 호환성을 위해 기존 형식으로 변환
        all_questions = []
        
        # 객관식 문제 추가
        for q in multiple_choice_questions:
            q['type'] = 'multiple_choice'  # 타입 명시
            all_questions.append(q)
        
        # 주관식 문제 추가
        for q in subjective_questions:
            q['type'] = 'subjective'  # 타입 명시
            all_questions.append(q)
        
        return all_questions
    except Exception as e:
        st.error(f"문제 조회 실패: {e}")
        # 기존 방식으로 폴백
        return st.session_state.db.get_questions()

@st.cache_data(ttl=60)  # 1분 캐시
def get_cached_feedback_count():
    """피드백 수 캐시"""
    return st.session_state.db.count_feedback()

@st.cache_data(ttl=60)  # 1분 캐시
def get_cached_adjustments_count():
    """조정 수 캐시"""
    return st.session_state.db.count_adjustments()

def render(st):
    try:
        with st.spinner("데이터를 불러오는 중..."):
            # 캐시된 데이터 사용
            all_q = get_cached_dashboard_data()
        
        if not all_q:
            st.info("데이터가 없습니다.")
            return

        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric("전체 문제", len(all_q))
        with c2: st.metric("AI 생성", sum(1 for q in all_q if q.get("ai_generated", False)))
        
        # 피드백과 조정 수는 캐시된 데이터 사용
        try:
            with c3: st.metric("총 피드백", get_cached_feedback_count())
        except Exception as e:
            with c3: st.metric("총 피드백", "오류")
            st.caption(f"피드백 조회 오류: {e}")
            
        try:
            with c4: st.metric("난이도 조정", get_cached_adjustments_count())
        except Exception as e:
            with c4: st.metric("난이도 조정", "오류")
            st.caption(f"조정 수 조회 오류: {e}")
            
    except Exception as e:
        st.error(f"❌ 데이터 로딩 중 오류가 발생했습니다: {str(e)}")
        st.info("💡 네트워크 연결을 확인하거나 잠시 후 다시 시도해주세요.")
        return

    try:
        st.markdown("### 문제 분포")
        df = pd.DataFrame(all_q)
        
        # 평가 영역별 분포
        if "category" in df.columns:
            category = df["category"].value_counts()
            st.plotly_chart(px.pie(values=category.values, names=category.index, title="평가 영역별 분포"), use_container_width=True)
        else:
            st.warning("평가 영역 데이터가 없습니다.")
        
        # 난이도별 분포
        if "difficulty" in df.columns:
            diff = df["difficulty"].value_counts()
            st.plotly_chart(px.bar(x=diff.index, y=diff.values, title="난이도별 분포"), use_container_width=True)
        else:
            st.warning("난이도 데이터가 없습니다.")
            
    except Exception as e:
        st.error(f"차트 생성 중 오류: {e}")

    # 피드백 분석 (샘플 20개만, 캐시 활용)
    @st.cache_data(ttl=300)  # 5분 캐시
    def get_cached_feedback_analysis(sample_questions):
        """피드백 분석 데이터 캐시"""
        rows = []
        for q in sample_questions:
            try:
                s = st.session_state.db.get_feedback_stats(q["id"])
                if s:
                    rows.append({
                        "question_id": q["id"][:10]+"...", 
                        "difficulty": s["avg_difficulty"], 
                        "relevance": s["avg_relevance"], 
                        "clarity": s["avg_clarity"]
                    })
            except Exception as e:
                continue
        return rows
    
    try:
        st.markdown("### 피드백 분석 (샘플 20)")
        sample_questions = all_q[:20]  # 샘플 크기 제한
        
        # 캐시된 피드백 분석 데이터 사용
        rows = get_cached_feedback_analysis(sample_questions)
        
        if rows:
            dff = pd.DataFrame(rows)
            fig = go.Figure()
            fig.add_trace(go.Bar(name="난이도", x=dff["question_id"], y=dff["difficulty"]))
            fig.add_trace(go.Bar(name="관련성", x=dff["question_id"], y=dff["relevance"]))
            fig.add_trace(go.Bar(name="명확성", x=dff["question_id"], y=dff["clarity"]))
            fig.update_layout(title="문제별 평가 점수", barmode="group", yaxis_title="평균 점수", xaxis_title="문제 ID")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("피드백 데이터가 없습니다.")
            
    except Exception as e:
        st.error(f"피드백 분석 중 오류: {e}")
