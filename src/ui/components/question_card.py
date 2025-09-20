"""
문제 카드 렌더링 컴포넌트 (배지를 메타라인에 표시, 흰색띠 제거용 커스텀 HTML)
"""
import streamlit as st
from src.ui.utils.text_sanitizer import _sanitize_content

# 목록 섹션(우측) 진입 시 1번만 넣어두면 됨
def inject_card_css():
    st.markdown("""
    <style>
    .ql-card {
      border: 1px solid rgba(255,255,255,.08);
      background: rgba(255,255,255,.03);
      border-radius: 10px;
      padding: 12px 14px;
      margin: 10px 0 14px;
    }
    .ql-header { display:flex; align-items:center; gap:8px; margin-bottom:6px; }
    .ql-title { font-size:14px; font-weight:600; line-height:1.2; margin:0; }

    .ql-meta {
      display:flex; gap:12px; align-items:center; flex-wrap:wrap;
      font-size:12px; color:rgba(255,255,255,.65);
      margin:2px 0 2px;
    }
    .ql-item { display:inline-flex; gap:6px; align-items:center; }
    .ql-label { opacity:.75; }
    .ql-value { color:rgba(255,255,255,.9); }

    .badge { 
      display:inline-flex; align-items:center; gap:6px;
      border-radius:999px; padding:2px 8px; font-size:11px; line-height:1;
      border:1px solid transparent;
    }
    .badge-success { background: rgba(16,185,129,.15); color:#10b981; border-color: rgba(16,185,129,.35); }
    .badge-warn    { background: rgba(245,158,11,.15); color:#f59e0b; border-color: rgba(245,158,11,.35); }

    .ql-body { font-size:13px; color:rgba(255,255,255,.9); }
    .ql-body .ql-label { font-weight:600; margin-right:6px; color:rgba(255,255,255,.85); }

    /* 혹시 우측 영역에 남아있는 입력 위젯(흰 띠)이 있으면 숨김(선택) */
    [data-testid="stTextInput"] { display:none; }
    [data-testid="stSuccess"] { display:none; }  /* st.success 띠 제거용 */
    </style>
    """, unsafe_allow_html=True)

def render_question_card(i: int, q: dict):
    """문제 카드를 렌더링"""
    title = (q.get("title") or "제목 없음").strip()
    question_text = (q.get("content") or "").strip()
    area  = q.get("area_display", "N/A")
    diff  = q.get("difficulty_display", "N/A")
    qtype = q.get("type_display", "N/A")
    saved = bool(q.get("saved_to_db"))

    # 메타 라인 끝에 붙일 배지
    badge = '<span class="badge badge-success">✅ DB에 저장됨</span>' if saved \
            else '<span class="badge badge-warn">⚠️ DB 저장 안됨</span>'

    # 제목에 question_text 내용 붙이기
    full_title = question_text if question_text else title

    # 헤더(작은 제목) + 메타(배지 포함)
    st.markdown(f"""
    <div class="ql-card">
      <div class="ql-header">
        <div class="ql-title">문제 {i}: {full_title}</div>
      </div>

      <div class="ql-meta">
        <div class="ql-item"><span class="ql-label">평가 영역</span><span class="ql-value">{area}</span></div>
        <div class="ql-item"><span class="ql-label">난이도</span><span class="ql-value">{diff}</span></div>
        <div class="ql-item"><span class="ql-label">유형</span><span class="ql-value">{qtype}</span></div>
        {badge}
      </div>
    </div>
    """, unsafe_allow_html=True)
