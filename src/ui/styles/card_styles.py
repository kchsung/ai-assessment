"""
카드 및 배지 스타일 CSS 정의
"""

CARD_STYLES = """
<style>
/* 카드 */
.ql-card {
  border: 1px solid rgba(255,255,255,.08);
  background: rgba(255,255,255,.03);
  border-radius: 10px;
  padding: 12px 14px;
  margin: 10px 0 14px;
}

/* 헤더: 제목(작게) + 상태배지 */
.ql-card .ql-header {
  display: flex; align-items: center; gap: 8px;
  margin-bottom: 6px;
}
.ql-card .ql-title {
  font-size: 14px;            /* ✅ 작게 */
  font-weight: 600;
  line-height: 1.2;
  margin: 0;
}

/* 정보 라인: 평가영역/난이도/유형 + DB상태 */
.ql-card .ql-meta {
  display: flex; gap: 12px; align-items: center; flex-wrap: wrap;
  font-size: 12px; color: rgba(255,255,255,.65);
  margin: 2px 0 8px;
}
.ql-meta .ql-item { display: inline-flex; gap: 6px; align-items: center; }
.ql-meta .ql-label { opacity: .75; }
.ql-meta .ql-value { color: rgba(255,255,255,.9); }

/* 배지 */
.badge { 
  display:inline-flex; align-items:center; gap:6px;
  border-radius: 999px; padding: 2px 8px; font-size: 11px; 
  line-height: 1; border: 1px solid transparent;
}
.badge-success { background: rgba(16,185,129,.15); color:#10b981; border-color: rgba(16,185,129,.35); }
.badge-warn    { background: rgba(245,158,11,.15); color:#f59e0b; border-color: rgba(245,158,11,.35); }

/* 본문 */
.ql-card .ql-body { font-size: 13px; color: rgba(255,255,255,.9); }
.ql-card .ql-body .ql-label { font-weight: 600; margin-right: 6px; color: rgba(255,255,255,.85); }

/* 불필요한 흰색 띠(기본 입력 위젯 느낌) 방지: 카드 내부는 전부 커스텀 HTML만 사용 */
</style>
"""
