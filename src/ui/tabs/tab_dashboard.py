import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

def render(st):
    try:
        with st.spinner("데이터를 불러오는 중..."):
            # 대량 데이터 처리를 위해 타임아웃 증가
            all_q = st.session_state.db.get_questions()
        
        if not all_q:
            st.info("데이터가 없습니다.")
            return

        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric("전체 문제", len(all_q))
        with c2: st.metric("AI 생성", sum(1 for q in all_q if q.get("ai_generated", False)))
        
        # 피드백과 조정 수는 별도로 조회 (더 안정적)
        try:
            with c3: st.metric("총 피드백", st.session_state.db.count_feedback())
        except Exception as e:
            with c3: st.metric("총 피드백", "오류")
            st.caption(f"피드백 조회 오류: {e}")
            
        try:
            with c4: st.metric("난이도 조정", st.session_state.db.count_adjustments())
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

    # 피드백 분석 (샘플 20개만)
    try:
        st.markdown("### 피드백 분석 (샘플 20)")
        rows = []
        sample_questions = all_q[:20]  # 샘플 크기 제한
        
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
                st.caption(f"피드백 조회 오류 (문제 {q['id'][:10]}...): {e}")
                continue
        
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
