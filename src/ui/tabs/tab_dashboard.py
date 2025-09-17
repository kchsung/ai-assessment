import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

def render(st):
    st.header("📊 분석 대시보드")
    all_q = st.session_state.db.get_questions()
    if not all_q:
        st.info("데이터가 없습니다."); return

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("전체 문제", len(all_q))
    with c2: st.metric("AI 생성", sum(1 for q in all_q if q.get("ai_generated", False)))
    with c3: st.metric("총 피드백", st.session_state.db.count_feedback())
    with c4: st.metric("난이도 조정", st.session_state.db.count_adjustments())

    st.markdown("### 문제 분포")
    df = pd.DataFrame(all_q)
    area = df["area"].value_counts()
    st.plotly_chart(px.pie(values=area.values, names=area.index, title="평가 영역별 분포"), use_container_width=True)
    diff = df["difficulty"].value_counts()
    st.plotly_chart(px.bar(x=diff.index, y=diff.values, title="난이도별 분포"), use_container_width=True)

    st.markdown("### 피드백 분석 (샘플 20)")
    rows=[]
    for q in all_q[:20]:
        s = st.session_state.db.get_feedback_stats(q["id"])
        if s:
            rows.append({"question_id": q["id"][:10]+"...", "difficulty": s["avg_difficulty"], "relevance": s["avg_relevance"], "clarity": s["avg_clarity"]})
    if rows:
        dff = pd.DataFrame(rows)
        fig = go.Figure()
        fig.add_trace(go.Bar(name="난이도", x=dff["question_id"], y=dff["difficulty"]))
        fig.add_trace(go.Bar(name="관련성", x=dff["question_id"], y=dff["relevance"]))
        fig.add_trace(go.Bar(name="명확성", x=dff["question_id"], y=dff["clarity"]))
        fig.update_layout(title="문제별 평가 점수", barmode="group", yaxis_title="평균 점수", xaxis_title="문제 ID")
        st.plotly_chart(fig, use_container_width=True)
