"""Presentation-only helpers. Every dynamic HTML value is escaped here."""
from html import escape

import streamlit as st

APP_STYLE = """
<style>
:root {--qa-blue:#4F6EF7; --qa-text:#202634; --qa-muted:#6F7785; --qa-line:#E7EAF0;}
.stApp,[data-testid="stAppViewContainer"] {background:#F6F8FB; color:var(--qa-text);}
.stApp {font-family:Pretendard,Inter,Arial,"Malgun Gothic",sans-serif;}
[data-testid="stMainBlockContainer"] {padding:4.5rem 2rem 2rem; max-width:none;}
[data-testid="stSidebar"] {background:white; min-width:230px; max-width:240px; border-right:1px solid var(--qa-line);}
[data-testid="stSidebarUserContent"] {padding:1rem!important;}
h1 {font-size:clamp(28px,2.3vw,38px)!important; font-weight:750!important; letter-spacing:-.8px; padding:0!important;}
h2,h3 {font-size:21px!important; font-weight:700!important; padding:0 0 .3rem!important;}
[data-testid="stCaptionContainer"] {font-size:13px; color:var(--qa-muted)!important;}
[data-testid="stCaptionContainer"] p {color:var(--qa-muted)!important;}
[data-testid="stVerticalBlock"] {gap:.65rem;}
[class*="st-key-shell_"] {background:white; border:1px solid var(--qa-line)!important; border-radius:12px; padding:18px 20px; box-shadow:0 2px 8px #20263403;}
[data-testid="stTextInputRootElement"], [data-testid="stTextAreaRootElement"],
[data-testid="stDateInput"] [role="group"], [data-testid="stSelectbox"] [role="group"],
[data-testid="stMultiSelect"] [role="group"] {background:white!important; border:1px solid #DDE3EF!important; border-radius:7px;}
[data-testid="stWidgetLabel"] p {font-size:13px; color:#485674;}
button[kind="primary"] {background:var(--qa-blue); border-color:var(--qa-blue); color:white;}
[data-testid="stBaseButton-primary"], [data-testid="stBaseButton-primary"]:hover, [data-testid="stBaseButton-primary"]:focus {background:var(--qa-blue)!important; border-color:var(--qa-blue)!important; color:white!important;}
[data-testid="stDateInputField"] {background:white!important; border:1px solid #DDE3EF; border-radius:7px;}
[data-testid="stDateInput"] [role="group"] {border:0!important;}
[data-testid="stButton"] button,[data-testid="stDownloadButton"] button {border-radius:7px; min-height:40px; font-size:13px;}
[data-testid="stSidebar"] [role="radiogroup"] {gap:9px; margin-top:24px;}
.st-key-d21_navigation, [data-testid="stSidebar"] [data-testid="stRadioGroup"] {width:100%!important;}
[data-testid="stSidebar"] [data-testid="stRadioGroup"] > div {width:100%;}
[data-testid="stSidebar"] [data-testid="stRadioOption"] {display:flex; margin:0; padding:13px 14px; border-radius:9px; width:100%; color:#46536A; cursor:pointer;}
[data-testid="stSidebar"] [data-testid="stRadioOption"] > div > div:first-child {display:none;}
[data-testid="stSidebar"] [data-testid="stRadioOption"][data-selected="true"] {background:#EEF1FF; color:var(--qa-blue); font-weight:650;}
[data-testid="stSidebar"] [data-testid="stRadioOption"]:focus-within {outline:2px solid var(--qa-blue); outline-offset:2px;}
[data-testid="stSidebar"] [data-testid="stRadioOption"]::before {content:''; width:19px; height:19px; margin-right:12px; flex-shrink:0; background:currentColor; mask:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Ccircle cx='10' cy='10' r='6' fill='none' stroke='black' stroke-width='2'/%3E%3Cpath d='m15 15 6 6' stroke='black' stroke-width='2'/%3E%3C/svg%3E") center/contain no-repeat;}
[data-testid="stSidebar"] [data-testid="stRadioOption"]:has(input[value="1"])::before {mask-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath d='M6 2h9l4 4v16H6zM9 10h7M9 14h7M9 18h7' fill='none' stroke='black' stroke-width='2'/%3E%3C/svg%3E");}
[data-testid="stSidebar"] [data-testid="stRadioOption"]:has(input[value="2"])::before {mask-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Ccircle cx='12' cy='12' r='9' fill='none' stroke='black' stroke-width='2'/%3E%3Cpath d='M12 10v7M12 6v2' stroke='black' stroke-width='2'/%3E%3C/svg%3E");}
.qa-brand {display:flex; align-items:center; gap:10px; font-size:22px; font-weight:750; padding:4px 10px;}
.qa-brand svg {color:var(--qa-blue); width:28px; min-width:28px;} .qa-brand span {white-space:nowrap;}
.qa-sidebar-foot {margin-top:48px; padding:10px; color:var(--qa-muted); font-size:11px; line-height:1.8; letter-spacing:.4px;}
.stTabs [role="tablist"] {gap:22px; border-bottom:1px solid var(--qa-line);}
.stTabs [role="tab"] {padding:6px 4px 12px; height:42px; color:#485674; font-size:14px;}
.stTabs [aria-selected="true"] {color:var(--qa-blue)!important;}
.stTabs .react-aria-SelectionIndicator {background:var(--qa-blue)!important; height:2px;}
[data-testid="stExpander"] {border-color:var(--qa-line); border-radius:8px; background:white;}
.qa-summary-grid {display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:14px; margin-bottom:10px;}
.qa-summary-grid.three {grid-template-columns:repeat(3,minmax(0,1fr));}
.qa-summary {display:flex; gap:14px; align-items:flex-start; min-height:110px; border:1px solid var(--qa-line); border-radius:10px; padding:17px; background:white; box-sizing:border-box;}
.qa-icon {display:flex; align-items:center; justify-content:center; width:44px; height:44px; flex-shrink:0; border-radius:9px; background:#EEF1FF; color:var(--qa-blue);}
.qa-icon svg {width:24px; height:24px;}
.qa-label {font-size:13px; color:#485674; margin-bottom:7px;}
.qa-value {font-size:25px; font-weight:750; line-height:1.2; overflow-wrap:anywhere; color:var(--qa-text);}
.qa-description {font-size:12px; color:var(--qa-muted); margin-top:7px; line-height:1.5;}
.qa-empty {min-height:120px; display:flex; align-items:center; justify-content:center; text-align:center; color:var(--qa-muted); font-size:14px; background:#FAFBFD; border:1px dashed #E0E5EF; border-radius:8px; padding:18px;}
.qa-notice {background:#F0F4FF; color:#526184; border-radius:8px; padding:12px 15px; font-size:13px; line-height:1.65;}
.qa-notice strong {display:block; color:#263E74; margin-bottom:4px;}
.rank-row {display:grid; grid-template-columns:28px minmax(90px,1fr) 1.6fr 52px; gap:12px; align-items:center; padding:10px 0; font-size:14px;}
.rank-circle {border-radius:50%; background:#EEF1F5; height:28px; display:flex; align-items:center; justify-content:center;}
.rank-row:first-child .rank-circle {background:#EEF1FF; color:var(--qa-blue);}
.rank-track {background:#EEF1F5; height:9px; border-radius:8px; overflow:hidden;}
.rank-fill {background:var(--qa-blue); height:100%; border-radius:8px;}
.qa-preview {width:100%; border-collapse:collapse; font-size:12px; table-layout:fixed;}
.qa-preview th {font-weight:500; text-align:left; color:#53617C; background:#F6F8FC;}
.qa-preview td,.qa-preview th {padding:7px 8px!important; line-height:1.4!important; border:0!important; border-bottom:1px solid #EEF1F5!important;}
.qa-preview td {overflow:hidden; text-overflow:ellipsis; white-space:nowrap;}
.qa-preview th:nth-child(1) {width:76px;} .qa-preview th:nth-child(2) {width:84px;}
.qa-preview th:nth-child(3) {width:76px;}
.qa-pill {display:inline-block; border-radius:6px; padding:3px 7px; background:#EEF1FF; color:#4963C9; font-size:12px;}
.qa-secondary .qa-pill, .qa-pill.qa-secondary {background:#F1F3F7; color:#6F7785;}
.qa-detail-row {display:grid; grid-template-columns:66px 110px 86px 130px minmax(0,1fr); gap:12px; align-items:center; font-size:13px; padding:9px 4px;}
.qa-detail-row .qa-snippet {overflow:hidden; white-space:nowrap; text-overflow:ellipsis; color:#53617C;}
.qa-detail-header {display:grid; grid-template-columns:66px 110px 86px 130px minmax(0,1fr) 90px; gap:12px; padding:9px 10px; font-size:12px; font-weight:650; color:#53617C; background:#F6F8FC; border-radius:6px; margin-bottom:6px;}
.qa-field-row {display:flex; align-items:center; gap:9px; padding:6px 0; font-size:13px;}
.qa-field-row svg {width:16px; height:16px; color:var(--qa-muted); flex-shrink:0;}
.qa-field-row .qa-field-label {color:var(--qa-muted); min-width:138px;}
.qa-field-row .qa-field-value {color:var(--qa-text); font-weight:550;}
.qa-info-box {background:#F0F4FF; border-radius:8px; padding:10px 13px; font-size:12px; color:#526184; display:flex; gap:8px; align-items:flex-start; margin-top:6px;}
.qa-info-box svg {width:15px; height:15px; flex-shrink:0; margin-top:1px; color:#4F6EF7;}
/* 시스템 소개: Streamlit 컬럼 구조에 의존하지 않는 CSS grid.
   같은 행의 두 패널은 grid의 stretch 로 항상 같은 높이가 되고, 고정 min-height 는 두지 않는다. */
.qa-intro-grid {display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:16px; align-items:stretch; margin:16px 0 0;}
.qa-intro-panel {border:1px solid var(--qa-line); border-radius:10px; padding:20px 22px; background:white; box-sizing:border-box; min-width:0;}
.qa-intro-panel.qa-spread {display:flex; flex-direction:column;}
.qa-intro-panel.qa-spread .qa-panel-body {flex:1; display:flex; flex-direction:column; justify-content:space-between; gap:10px;}
.qa-intro-panel .qa-panel-title {font-size:21px; font-weight:700; line-height:1.35; margin:0 0 8px; color:var(--qa-text);}
.qa-intro-card {display:flex; gap:14px; align-items:flex-start; border:1px solid var(--qa-line); border-radius:10px; padding:20px; background:white; box-sizing:border-box;}
.qa-intro-card .qa-intro-title {font-size:16px; font-weight:700; margin-bottom:6px; color:var(--qa-text);}
.qa-intro-card .qa-intro-desc {font-size:13px; color:var(--qa-muted); line-height:1.55;}
.qa-workflow-step {display:flex; gap:12px; align-items:flex-start; padding:5px 0;}
.qa-workflow-step p {margin:2px 0 0;}
.qa-workflow-step .qa-step-number {flex-shrink:0;}
.qa-workflow-step .qa-icon {width:38px; height:38px; flex-shrink:0;}
.qa-workflow-arrow {text-align:left; color:#B9C0D1; font-size:11px; line-height:8px; padding-left:11px; margin:0;}
.qa-principle-row {display:grid; grid-template-columns:34px minmax(0,1fr); gap:12px; align-items:start; padding:11px 0; border-bottom:1px solid var(--qa-line);}
.qa-principle-row:last-child {border-bottom:none;}
.qa-principle-row .qa-icon-sm {width:34px; height:34px; border-radius:8px; background:#EEF1FF; color:var(--qa-blue); display:flex; align-items:center; justify-content:center;}
.qa-principle-row .qa-icon-sm svg {width:17px; height:17px;}
.qa-principle-row .qa-principle-title {font-size:14px; font-weight:650; color:var(--qa-text); padding-top:5px;}
.qa-principle-row .qa-principle-desc {font-size:13px; color:#53617C; line-height:1.55; padding-top:3px;}
.qa-limit-row {display:flex; gap:11px; align-items:flex-start; padding:8px 0; font-size:13px; color:var(--qa-text); line-height:1.55;}
.qa-limit-number {flex-shrink:0; width:24px; height:24px; border-radius:50%; background:#EEF1FF; color:var(--qa-blue); display:flex; align-items:center; justify-content:center; font-size:12px; font-weight:650;}
.qa-subheader-icon {display:inline-flex; align-items:center; gap:8px; font-size:16px; font-weight:700; color:var(--qa-text); margin-bottom:4px;}
.qa-subheader-icon svg {width:18px; height:18px; color:#B45309;}
.qa-subheader-icon.layers svg {color:var(--qa-blue);}
.qa-step {display:flex; gap:13px; align-items:flex-start; padding:9px 0;}
.qa-step-number {display:flex; align-items:center; justify-content:center; min-width:30px; height:30px; background:#EEF1FF; color:var(--qa-blue); border-radius:50%; font-weight:650;}
.qa-step strong {font-size:14px;} .qa-step p {font-size:13px; color:#6F7785; margin:4px 0 0; line-height:1.55;}
.qa-tags {display:flex; gap:7px; flex-wrap:wrap; padding-top:8px;}
.qa-tags span {background:#EEF1FF; border-radius:20px; color:#4963C9; padding:6px 11px; font-size:12px;}
.st-key-shell_ai_reference {background:#F0F4FF!important;}
@media(max-width:1050px) {.qa-intro-grid {grid-template-columns:1fr;}}
/* ---- 시스템 소개 글자·아이콘 크기 조정 (v2.1) ---- */
.qa-intro-panel .qa-step {gap:16px; padding:13px 0;}
.qa-intro-panel .qa-step .qa-step-number {min-width:38px; height:38px; font-size:16px;}
.qa-intro-panel .qa-step strong {font-size:18px;}
.qa-intro-panel .qa-step p {font-size:15.5px; line-height:1.65; margin:6px 0 0;}
.qa-workflow-step {gap:10px; padding:3px 0;}
.qa-workflow-step .qa-step-number {min-width:24px; height:24px; font-size:12px;}
.qa-workflow-step .qa-icon {width:30px; height:30px; border-radius:7px;}
.qa-workflow-step .qa-icon svg {width:16px; height:16px;}
.qa-workflow-step strong {font-size:13px;}
.qa-workflow-step p {font-size:12px; line-height:1.45; margin:1px 0 0;}
.qa-intro-panel .qa-limit-row {font-size:15.5px; line-height:1.65; padding:11px 0; gap:13px;}
.qa-intro-panel .qa-limit-number {width:28px; height:28px; font-size:14px;}
.qa-intro-panel .qa-subheader-icon {font-size:19px; gap:10px;}
.qa-intro-panel .qa-subheader-icon svg {width:22px; height:22px;}
.qa-intro-panel .qa-tags {gap:10px; padding-top:12px;}
.qa-intro-panel .qa-tags span {font-size:14.5px; padding:8px 15px;}

@media(max-width:1050px) {.qa-summary-grid {grid-template-columns:repeat(2,minmax(0,1fr));} .qa-detail-row {grid-template-columns:60px 100px 70px 1fr;} .qa-detail-row .qa-snippet {grid-column:1/-1;}}
@media(max-width:700px) {[data-testid="stMainBlockContainer"] {padding:4.5rem 1rem 1rem;} .qa-summary-grid,.qa-summary-grid.three {grid-template-columns:1fr;} .qa-preview th:nth-child(2) {width:70px;} .qa-summary {min-height:90px;}}
</style>
"""

PATHS = {
    "document": '<path d="M6 3h8l4 4v14H6zM14 3v5h4M9 12h6M9 16h6"/>',
    "chart": '<rect x="4" y="13" width="3" height="8" rx="1"/><rect x="10" y="8" width="3" height="13" rx="1"/><rect x="16" y="3" width="3" height="18" rx="1"/>',
    "database": '<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v14c0 4 16 4 16 0V5M4 12c0 4 16 4 16 0"/>',
    "person": '<circle cx="12" cy="7" r="4"/><path d="M4 21v-3c0-7 16-7 16 0v3z"/>',
    "shield": '<path d="m12 2 9 4v6c0 6-9 10-9 10S3 18 3 12V6z"/><path d="m8 12 3 3 5-6"/>',
    "calendar": '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M16 3v4M8 3v4M3 10h18"/>',
    "heart": '<path d="M12 21s-7-4.5-9.5-9A5.5 5.5 0 0 1 12 6a5.5 5.5 0 0 1 9.5 6c-2.5 4.5-9.5 9-9.5 9z"/>',
    "box": '<path d="M3 7l9-4 9 4-9 4-9-4z"/><path d="M3 7v10l9 4 9-4V7"/><path d="M12 11v10"/>',
    "factory": '<path d="M3 21V10l6 4v-4l6 4V7l6 4v10H3z"/><path d="M7 17h2M11 17h2M15 17h2"/>',
    "building": '<rect x="4" y="3" width="16" height="18" rx="1"/><path d="M9 7h2M13 7h2M9 11h2M13 11h2M9 15h2M13 15h2"/>',
    "pencil": '<path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z"/>',
    "list": '<path d="M8 6h13M8 12h13M8 18h13"/><circle cx="3" cy="6" r="1"/><circle cx="3" cy="12" r="1"/><circle cx="3" cy="18" r="1"/>',
    "check": '<circle cx="12" cy="12" r="9"/><path d="m8 12 3 3 5-6"/>',
    "warning": '<path d="M12 2 2 20h20z"/><path d="M12 9v5M12 17h.01"/>',
    "layers": '<path d="m12 3 9 5-9 5-9-5z"/><path d="m3 13 9 5 9-5"/>',
}


def icon(name):
    return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + PATHS.get(name, PATHS["document"]) + '</svg>'


def html(value):
    return escape(str(value), quote=True)


def summary_cards(cards):
    # 카드 튜플은 (symbol, label, value, description) 4개 또는 끝에 value_color를 더한 5개.
    # value_color 생략 시 기존 기본 색상 그대로(다른 페이지 호출부는 영향 없음).
    parts = []
    for card in cards:
        symbol, label, value, description = card[:4]
        value_color = card[4] if len(card) > 4 and card[4] else None
        style = f' style="color:{value_color}"' if value_color else ''
        parts.append(f'<div class="qa-summary"><div class="qa-icon">{icon(symbol)}</div><div><div class="qa-label">{html(label)}</div><div class="qa-value"{style}>{html(value)}</div><div class="qa-description">{html(description)}</div></div></div>')
    st.markdown(f'<div class="qa-summary-grid {"three" if len(cards) == 3 else ""}">{"".join(parts)}</div>', unsafe_allow_html=True)


def empty(message):
    st.markdown(f'<div class="qa-empty">{html(message)}</div>', unsafe_allow_html=True)


def notice(title, message):
    st.markdown(f'<div class="qa-notice"><strong>{html(title)}</strong>{html(message)}</div>', unsafe_allow_html=True)


def steps_html(items):
    return ''.join(f'<div class="qa-step"><span class="qa-step-number">{i}</span><div><strong>{html(title)}</strong><p>{html(description)}</p></div></div>' for i, (title, description) in enumerate(items, 1))


def steps(items):
    st.markdown(steps_html(items), unsafe_allow_html=True)


def intro_cards(cards):
    """시스템 소개 상단 3카드: (icon, title, description) — summary_cards와 달리 큰 value 줄이 없음."""
    markup = ''.join(
        f'<div class="qa-intro-card"><div class="qa-icon">{icon(sym)}</div>'
        f'<div><div class="qa-intro-title">{html(title)}</div><div class="qa-intro-desc">{html(desc)}</div></div></div>'
        for sym, title, desc in cards
    )
    st.markdown(f'<div class="qa-summary-grid three">{markup}</div>', unsafe_allow_html=True)


def notice_html(title, message):
    return f'<div class="qa-notice"><strong>{html(title)}</strong>{html(message)}</div>'


def workflow_html(items):
    """워크플로우: 번호 + 아이콘박스 + 제목/설명, 단계 사이에 ↓ 커넥터. items: (icon, title, description)"""
    parts = []
    for i, (sym, title, description) in enumerate(items, 1):
        parts.append(
            f'<div class="qa-workflow-step"><span class="qa-step-number">{i}</span>'
            f'<div class="qa-icon">{icon(sym)}</div>'
            f'<div><strong>{html(title)}</strong><p>{html(description)}</p></div></div>'
        )
        if i < len(items):
            parts.append('<div class="qa-workflow-arrow">↓</div>')
    return ''.join(parts)


def workflow_steps(items):
    st.markdown(workflow_html(items), unsafe_allow_html=True)


def principle_html(items):
    """해석 원칙: 아이콘 | (제목 / 설명). items: (icon, title, description)"""
    return ''.join(
        f'<div class="qa-principle-row"><div class="qa-icon-sm">{icon(sym)}</div>'
        f'<div><div class="qa-principle-title">{html(title)}</div><div class="qa-principle-desc">{html(desc)}</div></div></div>'
        for sym, title, desc in items
    )


def principle_rows(items):
    st.markdown(principle_html(items), unsafe_allow_html=True)


def limit_html(items):
    return ''.join(f'<div class="qa-limit-row"><span class="qa-limit-number">{i}</span><span>{html(text)}</span></div>' for i, text in enumerate(items, 1))


def limit_list(items):
    """Prototype 한계 사항: 번호 + 한 줄 설명(별도 제목 없음)."""
    st.markdown(limit_html(items), unsafe_allow_html=True)


def subheader_icon_html(symbol, title, css_class=""):
    return f'<div class="qa-subheader-icon {css_class}">{icon(symbol)}<span>{html(title)}</span></div>'


def subheader_with_icon(symbol, title, css_class=""):
    st.markdown(subheader_icon_html(symbol, title, css_class), unsafe_allow_html=True)


def tags_html(labels):
    return '<div class="qa-tags">' + ''.join(f'<span>{html(label)}</span>' for label in labels) + '</div>'


def panel_html(title, body_html, title_icon=None, spread=False):
    """spread=True: 패널이 더 높게 늘어날 때 본문 항목을 세로로 고르게 배치(빈 공간 완화)."""
    head = subheader_icon_html(title_icon, title) if title_icon else f'<div class="qa-panel-title">{html(title)}</div>'
    if spread:
        return f'<div class="qa-intro-panel qa-spread">{head}<div class="qa-panel-body">{body_html}</div></div>'
    return f'<div class="qa-intro-panel">{head}{body_html}</div>'


def intro_row(left_panel_html, right_panel_html):
    """같은 행의 두 패널을 하나의 grid 로 렌더링 → 두 패널의 높이가 항상 같다."""
    st.markdown(f'<div class="qa-intro-grid">{left_panel_html}{right_panel_html}</div>', unsafe_allow_html=True)


def retrieval_preview(retrieval, on_detail=None):
    title, action = st.columns([3, 2], vertical_alignment="center")
    title.subheader("유사 Recall Preview")
    if on_detail:
        action.button("과거 Recall 상세 보기", key="d21_recall_jump", on_click=on_detail, type="tertiary")
    if retrieval is None:
        empty("분석을 실행하면 과거 유사 Recall 사례가 표시됩니다.")
        return
    items = (retrieval.get("default_results") or []) + (retrieval.get("additional_results") or [])
    if not items:
        empty("조건을 만족하는 유사 Recall이 없습니다.")
        return
    rows = []
    for item in items[:4]:
        preview = ' '.join(str(item.get("retrieved_reason") or "정보 없음").split())
        rows.append(f'<tr class="{"qa-secondary" if item["rank"] > 3 else ""}"><td><span class="qa-pill">Rank {html(item["rank"])}</span></td><td>{html(item["retrieved_event_id"])}</td><td>{float(item["similarity"]):.4f}</td><td>{html(preview[:120])}</td></tr>')
    st.markdown('<table class="qa-preview"><thead><tr><th>Rank</th><th>Event ID</th><th>Similarity</th><th>Recall Reason 미리보기</th></tr></thead><tbody>' + ''.join(rows) + '</tbody></table>', unsafe_allow_html=True)
    st.caption("전체 Reason·Action은 ‘과거 Recall’ 탭에서 확인하세요.")
