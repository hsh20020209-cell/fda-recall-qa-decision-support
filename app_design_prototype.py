"""Day21 local design prototype. Run with streamlit run app_design_prototype.py."""
from __future__ import annotations

import copy
import json
import os
from datetime import datetime
from html import escape

import pandas as pd
import streamlit as st

from dashboard import day21_prototype_adapter as adapter
from dashboard import day21_prototype_ui as ui
from dashboard import day21_prototype_workflow as workflow
from dashboard import day22_slack_notify as slack  # [Slack 신규 추가] 팀원 설계 외 기능, 분리된 모듈

APP_STYLE = ui.APP_STYLE
CHANGE_REASONS = ["Recall Reason에 추가 정보 존재", "핵심 문맥 해석 차이", "Root Cause taxonomy가 모호함",
                  "여러 원인이 동시에 존재", "QA 조사 결과와 차이", "기타"]
TABS = ["Root Cause · Confidence", "과거 Recall", "QA 검토", "검증 정보"]


@st.cache_resource(show_spinner=False)
def load_qa_runtime(project_root: str):
    return adapter.create_runtime(project_root)


@st.cache_resource(show_spinner=False)
def load_lookup(directory: str):
    return adapter.load_lookup_tables(directory)


def inject_style():
    st.markdown(APP_STYLE, unsafe_allow_html=True)


def reset_case():
    for key in list(st.session_state):
        if key.startswith(("d21_check_", "d21_final_")) or key in (
            "d21_result", "d21_case", "d21_message", "d21_error", "d21_saved",
            "d21_memo", "d21_snapshot", "d21_show_next", "d21_show_report"
        ):
            del st.session_state[key]


def clear_inputs():
    reset_case()
    for key in ("d21_number", "d21_reason", "d21_event", "d21_device"):
        st.session_state[key] = ""
    st.session_state["d21_date"] = None
    st.session_state.pop("d21_lookup_message", None)


def input_changed():
    # Never allow an edited input to be mistaken for the analyzed case.
    reset_case()


def perform_lookup():
    reset_case()
    tables = load_lookup(str(adapter.lookup_directory()))
    found = adapter.lookup_recall(st.session_state.get("d21_number", ""), tables)
    st.session_state["d21_device"] = ""
    if found:
        st.session_state["d21_reason"] = found["recall_reason"]
        st.session_state["d21_device"] = found["device_name"]
        message = "과거 reference에서 조회했습니다. 입력 내용을 확인해 주세요."
    else:
        message = "조회 결과가 없습니다. Recall Reason을 직접 입력해 주세요." if tables else "Recall Number lookup unavailable · 직접 입력 가능합니다."
    st.session_state["d21_lookup_message"] = message
    # Date and optional Event ID are never inferred from this historical lookup.


def render_sidebar():
    with st.sidebar:
        st.markdown(f'<div class="qa-brand">{ui.icon("shield")}<span>QA Support</span></div>', unsafe_allow_html=True)
        page = st.radio("메뉴", ["Recall 분석", "QA 판단 이력", "시스템 소개"],
                        key="d21_navigation", label_visibility="collapsed", width="stretch")
        st.markdown('<div class="qa-sidebar-foot">DESIGN PROTOTYPE<br>단일 사용자 · 로컬 세션</div>', unsafe_allow_html=True)
    return page


def render_page_header(page="Recall 분석"):
    title, subtitle = {
        "Recall 분석": ("FDA Recall QA Decision Support", "신규 품질이슈의 초기 조사와 QA 판단을 지원합니다."),
        "QA 판단 이력": ("QA 판단 이력", "현재 세션에서 저장한 QA 판단 기록을 확인합니다."),
        "시스템 소개": ("시스템 소개", "FDA Recall 기반 QA 의사결정 지원 시스템 개요"),
    }[page]
    st.title(title)
    st.caption(subtitle)


def analyze_input():
    reset_case()
    reason = st.session_state.get("d21_reason", "").strip()
    query_date = st.session_state.get("d21_date")
    if not reason or query_date is None:
        st.session_state["d21_message"] = "Recall Reason과 검색 기준일을 모두 입력해 주세요."
        return
    try:
        runtime = load_qa_runtime(str(adapter.ROOT))
        raw = runtime.analyze_with_review(
            query_text=reason, query_date=query_date.isoformat(),
            query_event_id=st.session_state.get("d21_event", "").strip() or None,
        )
        if raw.get("status") != "NORMAL":
            st.session_state["d21_message"] = "입력을 정상 처리하지 못했습니다. Recall Reason을 확인해 주세요."
            return
        st.session_state["d21_result"] = adapter.extract_display_result(raw)
        st.session_state["d21_case"] = {
            "Recall Number": st.session_state.get("d21_number", ""),
            "Device Name": st.session_state.get("d21_device", ""),
            "Recall Reason": reason,
            "검색 기준일": query_date.isoformat(),
            "Event ID": st.session_state.get("d21_event", ""),
        }
    except Exception:
        st.session_state.pop("d21_result", None)
        st.session_state["d21_error"] = "분석 Runtime을 사용할 수 없습니다. 환경 및 Artifact 확인이 필요합니다."


def render_input_section():
    with st.container(key="shell_input"):
        heading, reset = st.columns([5, 1], vertical_alignment="center")
        heading.subheader("Recall 조회 / 신규 이슈 입력")
        reset.button("입력·결과 지우기", key="d21_clear", on_click=clear_inputs, type="tertiary")
        cols = st.columns([2.1, 3.6, 1.5, 1.3, 1.1], vertical_alignment="top")
        with cols[0]:
            field, button = st.columns([3.5, 1], vertical_alignment="bottom")
            with field:
                st.text_input("Recall Number", key="d21_number", on_change=perform_lookup,
                              placeholder="Z-XXXX-YYYY")
            with button:
                st.button("조회", on_click=perform_lookup, key="d21_lookup", width="stretch")
        with cols[1]:
            st.text_area("Recall Reason (필수)", key="d21_reason", height=68,
                         on_change=input_changed, help="영어 입력 기준. 한국어·혼합 언어 성능은 NOT_VERIFIED입니다.")
        with cols[2]:
            st.date_input("검색 기준일 (필수)", value=None, key="d21_date", on_change=input_changed,
                          help="Recall initiated date가 기준일보다 이전인 사례만 검색. 같은 날짜 제외. FDA 공개일 또는 당시 이용 가능 날짜가 아닙니다.")
        with cols[3]:
            st.text_input("Event ID (선택)", key="d21_event", on_change=input_changed,
                          help="입력한 동일 Event는 검색 결과에서 제외합니다.")
        with cols[4]:
            st.markdown('<div style="height:28px" aria-hidden="true"></div>', unsafe_allow_html=True)
            st.button("분석 실행", type="primary", key="d21_analyze", on_click=analyze_input, width="stretch")
        if st.session_state.get("d21_device"):
            st.text("Device Name: " + st.session_state["d21_device"])
        if load_lookup(str(adapter.lookup_directory())) is None:
            st.caption("Recall Number lookup unavailable · 직접 입력 가능합니다.")
        if st.session_state.get("d21_lookup_message"):
            st.caption(st.session_state["d21_lookup_message"])
    if st.session_state.get("d21_message"):
        st.warning(st.session_state["d21_message"])
    if st.session_state.get("d21_error"):
        st.error(st.session_state["d21_error"])


_CONFIDENCE_COLOR = {"HIGH": "#22C55E", "MEDIUM": "#EAB308", "LOW": "#EF4444"}  # 초록/노랑/빨강


def render_summary_cards(result):
    c, r = (result["classification"], result["retrieval"]) if result else ({}, {})
    confidence_level = c.get("confidence_level") if c else None
    cards = [
        ("document", "Root Cause", c.get("top1_root_cause", "—"), f"Top-1 · {c['top1_confidence']:.1%}" if c else "분석 후 표시됩니다."),
        ("chart", "Confidence", confidence_level or "—", "검토 수준: " + {"HIGH": "핵심 근거 확인", "MEDIUM": "보통", "LOW": "추가 근거 필요"}.get(confidence_level, "확인 필요") if c else "분석 후 표시됩니다.", _CONFIDENCE_COLOR.get(confidence_level)),
        ("database", "Similar Recall", f"{r['returned_n']}건" if r else "—", "과거 근거 사례" if r else "분석 후 표시됩니다."),
        ("person", "QA Review", "Required", "Final decision by QA"),
    ]
    with st.container(key="shell_summary"):
        st.subheader("분석 결과 요약")
        ui.summary_cards(cards)
        if result:
            st.caption("NORMAL은 기술적 처리 성공이며 QA 승인 또는 검토 완료가 아닙니다.")


def render_root_cause_tab(c, review, extra=None):
    st.subheader("Top-3 Root Cause 후보")
    if not c:
        ui.empty("분석을 실행하면 Root Cause Top-3 후보가 표시됩니다.")
    for item in c.get("top3_candidates", []):
        probability = float(item["probability"])
        # Only finite pipeline probabilities enter CSS; all textual data is escaped.
        if not 0 <= probability <= 1:
            st.error("표시할 모델 점수의 형식이 올바르지 않습니다.")
            continue
        st.markdown(
            f'<div class="rank-row"><span class="rank-circle">{escape(str(item["rank"]))}</span>'
            f'<span>{escape(str(item["root_cause"]))}</span>'
            f'<div class="rank-track"><div class="rank-fill" style="width:{probability * 100:.6f}%"></div></div>'
            f'<span>{probability:.1%}</span></div>', unsafe_allow_html=True,
        )
    ui.notice("Confidence 해석", "Confidence는 과거 유사 사례를 기반으로 한 검토 우선순위 신호이며, 자동 승인 기준이 아닙니다. 최종 판단은 QA의 검토와 결정이 필요합니다.")
    for warning in review.get("warnings") or []:
        st.text(str(warning))

    # ---- 본인 담당 추가 ①: 모델 예측 근거(XAI, 규칙 기반 요약) ----
    xai = extra.get("xai_explanation") if extra else None
    if xai:
        st.markdown("**모델 예측 근거**")
        # Top-3 Root Cause 후보(.rank-row)와 동일한 수준으로 크고 진하게
        st.markdown(f'<div style="font-size:16px; font-weight:650; line-height:1.6; color:var(--qa-text);">{escape(xai.get("natural_summary", ""))}</div>', unsafe_allow_html=True)
        if xai.get("top_words"):
            keywords_html = " · ".join(f'<span style="color:var(--qa-text); font-weight:650;">{escape(w)}</span>' for w in xai["top_words"])
            st.markdown(f'<div style="font-size:13px; color:var(--qa-muted); margin-top:4px;">주요 키워드: {keywords_html}</div>', unsafe_allow_html=True)
        st.caption("word+char 결합 모델 중 word 쪽 피처만 근거로 사용한 규칙 기반 요약입니다 (실제 문맥 이해가 아님).")

    # ---- 본인 담당 추가 ②: Top-3 후보별 확인 포인트 ----
    tc = extra.get("top3_comparison") if extra else None
    if tc and tc.get("candidate_points"):
        with st.expander("Top-3 후보별 확인 포인트 보기"):
            for cp in tc["candidate_points"]:
                points = ", ".join(cp["points"]) if cp["points"] else "-"
                st.write(f"**{escape(cp['root_cause'])}**: {escape(points)}")


_FIELD_ICONS = {
    "Recall initiated date": "calendar", "Medical Specialty": "heart",
    "Product Code": "box", "Device Class": "factory", "Recalling Firm": "building",
}


def text_value(label, value, show_icon=True):
    shown = "정보 없음" if value is None or not str(value).strip() else str(value)
    if not show_icon:
        st.text(f"{label}: {shown}")
        return
    icon_name = _FIELD_ICONS.get(label, "document")
    st.markdown(
        f'<div class="qa-field-row">{ui.icon(icon_name)}'
        f'<span class="qa-field-label">{ui.html(label)}</span>'
        f'<span class="qa-field-value">{ui.html(shown)}</span></div>',
        unsafe_allow_html=True,
    )


def render_recall_card(item):
    preview = " ".join(str(item.get("retrieved_reason") or "정보 없음").split())
    dim = item["rank"] > 3
    toggle_key = f"d21_recall_open_{item['rank']}_{item.get('retrieved_event_id')}"
    is_open = st.session_state.get(toggle_key, False)

    cols = st.columns([0.7, 1.15, 0.9, 1.35, 4.2, 1.1], vertical_alignment="center")
    pill_class = "qa-pill qa-secondary" if dim else "qa-pill"
    cols[0].markdown(f'<span class="{pill_class}">Rank {ui.html(item["rank"])}</span>', unsafe_allow_html=True)
    cols[1].markdown(f'<span style="font-size:13px;">Event {ui.html(item["retrieved_event_id"])}</span>', unsafe_allow_html=True)
    cols[2].markdown(f'<span style="font-size:13px;">{item["similarity"]:.4f}</span>', unsafe_allow_html=True)
    cols[3].markdown(f'<span style="font-size:13px;">{ui.html(item.get("retrieved_root_cause") or "정보 없음")}</span>', unsafe_allow_html=True)
    # [확대] Recall Reason 미리보기 — 기존보다 큰 글씨로
    cols[4].markdown(f'<div style="font-size:15px; line-height:1.5; color:#30374A;">{ui.html(preview[:220])}</div>', unsafe_allow_html=True)
    # [우측 이동] 상세보기 트리거를 각 행의 가장 오른쪽 컬럼에 배치
    if cols[5].button("접기" if is_open else "상세보기", key=f"{toggle_key}_btn", width="stretch"):
        st.session_state[toggle_key] = not is_open
        st.rerun()

    if is_open:
        with st.container(key=f"{toggle_key}_panel", border=True):
            st.caption(f"Rank {item['rank']} · 전체 Reason · Action · Context")
            left, right = st.columns([3, 5])
            with left:
                text_value("Recall initiated date", item.get("retrieved_date"))
                text_value("Medical Specialty", item.get("specialty"))
                text_value("Product Code", item.get("product_code"))
                text_value("Device Class", item.get("device_class"))
                text_value("Recalling Firm", item.get("firm"))
            with right:
                st.markdown("**전체 Recall Reason**")
                st.text(item.get("retrieved_reason") or "정보 없음")

                st.markdown("**전체 Recall Action · 과거 실제 조치 이력 (신규 이슈 권장 조치 아님)**")
                st.text(item.get("recall_action") or "정보 없음")
                st.markdown(
                    f'<div class="qa-info-box">{ui.icon("shield")}'
                    f'<span>Recall Action은 과거 사례에서 수행된 조치이며, 본 건에 대한 권장 조치가 아닙니다.</span></div>',
                    unsafe_allow_html=True,
                )


def render_retrieval_tab(retrieval):
    ui.notice("유사 Recall은 참고 근거로 활용하세요.", "아래의 과거 Recall 사례는 입력된 이슈와 유사도 분석 사례를 AI가 검색한 결과입니다. 유사도(Similarity)는 문서의 내용적 유사성을 의미하며, 동일한 Root Cause를 보장하지 않습니다. 최종 판단은 제품의 구체적인 상황과 최신 규제 요건을 고려하여 QA가 수행해야 합니다.")
    if retrieval is None:
        ui.empty("분석을 실행하면 과거 유사 Recall 사례가 표시됩니다.")
        return
    all_items = (retrieval.get("default_results") or []) + (retrieval.get("additional_results") or [])
    header_col, _ = st.columns([3, 2])
    header_col.markdown(f"**유사 Recall 사례 (Top {len(all_items)})**")
    if not retrieval.get("date_filter_applied"):
        st.warning("날짜 필터가 적용되지 않았습니다.")
    if retrieval.get("insufficient_results"):
        st.warning(retrieval.get("insufficient_reason") or "조건에 맞는 검색 결과가 3건 미만입니다.")
    if not all_items:
        st.caption("조건을 만족하는 유사 Recall이 없습니다.")
        return
    st.markdown(
        '<div class="qa-detail-header"><span>Rank</span><span>Event ID</span><span>Similarity</span>'
        '<span>과거 Root Cause</span><span>Recall Reason (요약)</span><span></span></div>',
        unsafe_allow_html=True,
    )
    for item in all_items:
        render_recall_card(item)
    with st.expander("검색 기준 · 해석 안내"):
        st.caption("all-MiniLM-L6-v2 · cosine similarity · final-v3 Train corpus. Recall initiated date < 검색 기준일, 같은 날짜 및 입력한 동일 Event 제외. FDA 공개일이나 당시 실제 정보 이용 가능 날짜를 의미하지 않습니다. 과거 Action은 신규 이슈의 권장·확정 조치가 아닙니다.")


def checklist_key(index):
    return f"d21_check_{index}"


def render_qa_checklist_tab(review):
    st.subheader("QA 조사 참고 체크리스트")
    st.caption("DOMAIN_REVIEW_PENDING · 참고 초안. FDA 공식 지침, 필수 SOP 또는 확정 조치가 아닙니다.")
    checklist = review.get("qa_checklist") or {}
    if not checklist:
        ui.empty("분석 후 QA 조사 참고 체크리스트가 표시됩니다.")
    for index, item in enumerate(checklist.get("items") or []):
        key = checklist_key(index)
        # Keep case state across sidebar navigation, independent of widget cleanup.
        st.session_state.setdefault(key, False)
        st.checkbox(str(item), key=key, disabled=st.session_state.get("d21_saved", False))


def render_qa_review(review):
    left, right = st.columns(2)
    with left:
        render_qa_checklist_tab(review)
    with right:
        st.subheader("Next Review Actions")
        ui.notice("검토 순서 참고 템플릿", "분석 근거를 확인하기 위한 일반 안내입니다. 확정 조치나 조직의 SOP가 아닙니다.")
        ui.steps([(item, "") for item in workflow.REVIEW_ACTIONS])
    st.subheader("검토 결과 메모")
    left, right = st.columns(2)
    with left:
        st.text_area("추가 확인 필요사항", key="d21_memo", height=100,
                     disabled=not review or st.session_state.get("d21_saved", False),
                     placeholder="QA 검토 중 확인한 추가 조사 사항을 직접 입력하세요.")
    with right:
        st.markdown("**QA Summary Report 구성 (미리보기)**")
        st.markdown('<div class="qa-tags">' + ''.join(f'<span>{x}</span>' for x in
                    ("1 Case 정보", "2 AI Analysis", "3 Historical Evidence", "4 QA Review", "5 Final Decision", "6 Next Actions")) + '</div>', unsafe_allow_html=True)


def render_model_validation_tab():
    st.subheader("Confidence 검증 정보")
    table = adapter.load_confidence_segment_table()
    if table is None:
        st.caption("모델 검증 자료 unavailable · 현재 참고 표를 표시할 수 없습니다.")
    else:
        st.dataframe(table, hide_index=True, width="stretch")
    st.caption("final-v3 · 저장된 Validation 1,338건 / Test 1,042건 검증 결과 (읽기 전용)")
    st.caption("Coverage는 평가 split에서 해당 구간에 포함된 비율이며 실제 QA workload를 직접 의미하지 않습니다. Accuracy는 해당 구간에서 Top-1이 실제 라벨과 일치한 비율이며 현재 입력이 맞을 확률이 아닙니다. Test는 프로젝트 중 반복 확인했으므로 untouched holdout이 아닙니다.")
    st.subheader("Retrieval Manual Review")
    directory = adapter.ROOT / "out/day19_retrieval_evaluation"
    evidence = workflow.load_manual_review(directory)
    if evidence is None:
        st.caption("수동평가 자료 unavailable · 확인할 수 있는 평가 결과가 없습니다.")
    else:
        st.text(f"평가 준비: Query {evidence['queries']}건 / 검색 pair {evidence['pairs']}건")
        st.text(f"사람 평가 기록: Query {sum(evidence['counts'].values())}건 / pair {evidence['pair_reviewed']}건 · Query 미완료 {evidence['pending']}건")
        if sum(evidence['counts'].values()):
            st.text(" · ".join(f"{k} {v}건" for k, v in evidence['counts'].items()))
        else:
            st.caption("HUMAN_REVIEW_PENDING · 평가표 추출 완료와 사람 평가 완료는 다릅니다.")
        if evidence['conflicts']:
            st.warning(f"불일치/잘못된 Query 평가 {evidence['conflicts']}건: 집계에서 제외했습니다.")
        st.caption("출처: out/day19_retrieval_evaluation/manual_evaluation_sheet.csv · 읽기 전용, 자동 판정 없음")
    guide = directory / "evaluation_guide.md"
    if guide.is_file():
        with st.expander("수동평가 기준 · 원본 가이드"):
            st.text(guide.read_text(encoding="utf-8"))


def save_qa_decision(result):
    c = result["classification"]
    final = st.session_state["d21_final_root"]
    if not final:
        st.warning("최종 Root Cause를 선택해 주세요.")
        return
    changed = final != c["top1_root_cause"]
    reasons = st.session_state.get("d21_final_reasons", []) if changed else []
    if changed and not reasons:
        st.warning("AI 참고 결과와 다른 판단의 수정 사유를 선택해 주세요.")
        return
    items = (result["qa_review"].get("qa_checklist") or {}).get("items", [])
    row = {**{k: v for k, v in copy.deepcopy(st.session_state["d21_case"]).items() if k != "Recall Reason"},
           "시각": datetime.now().astimezone().isoformat(timespec="seconds"),
           "AI Root Cause": c["top1_root_cause"], "AI Confidence": c["confidence_level"],
           "Top-1 score": c["top1_confidence"], "QA Final Root Cause": final,
           "동일/변경": "변경" if changed else "동일", "수정 사유": ", ".join(reasons),
           "QA 의견": st.session_state.get("d21_final_comment", ""),
           "Checklist 상태": json.dumps({item: bool(st.session_state.get(checklist_key(i), False))
                                          for i, item in enumerate(items)}, ensure_ascii=False)}
    st.session_state["d21_history"].append(row)
    st.session_state["d21_snapshot"] = copy.deepcopy({"case": st.session_state["d21_case"],
        "result": result, "decision": row, "memo": st.session_state.get("d21_memo", "")})
    st.session_state["d21_saved"] = True


def render_post_decision():
    saved = bool(st.session_state.get("d21_saved") and st.session_state.get("d21_snapshot"))
    with st.container(key="shell_post_decision"):
        label, next_col, report_col = st.columns([3, 1.5, 2])
        label.markdown("**판단 이후** · QA 판단 저장 후 후속 검토와 요약을 확인하세요.")
        if next_col.button("Next Action 확인", disabled=not saved, key="d21_next", width="stretch"):
            st.session_state["d21_show_next"] = not st.session_state.get("d21_show_next", False)
        if report_col.button("QA Summary Report 생성", disabled=not saved, key="d21_report", width="stretch"):
            st.session_state["d21_show_report"] = True
    if saved and st.session_state.get("d21_show_next"):
        with st.container(key="shell_next_actions"):
            st.subheader("Next Action · 참고 템플릿")
            st.caption("확정 조치 또는 SOP가 아닙니다. 담당자가 근거에 따라 선택하며, 외부 전송은 수행하지 않습니다.")
            ui.steps([(item, "") for item in workflow.NEXT_ACTIONS])
    if saved and st.session_state.get("d21_show_report"):
        with st.container(key="shell_report"):
            st.subheader("QA Summary Report · Template")
            report = workflow.build_report(st.session_state["d21_snapshot"])
            st.text(report)
            dl_col, slack_col = st.columns([1, 1])
            dl_col.download_button("요약 TXT 다운로드", report.encode("utf-8-sig"), "qa_summary.txt", "text/plain", width="stretch")
            # [Slack 신규 추가] 팀원 설계("외부 전송은 수행하지 않습니다")를 벗어나는 기능.
            # Webhook URL은 코드에 두지 않고 환경변수로만 받는다.
            if slack_col.button("Slack으로 전송", key="d21_slack_send", width="stretch"):
                st.session_state["d21_slack_confirm_open"] = True
            st.caption("⚠️ [신규 추가] 이 보고서를 Slack 채널로 전송합니다 — 외부 서비스로 데이터가 나갑니다 (팀원 기본 설계에는 없는 기능).")
            st.caption("저장 시점의 분석·QA 입력을 묶은 템플릿입니다. GenAI 생성이 아닙니다. 다운로드하면 사용자 파일로 남습니다.")

    if st.session_state.get("d21_slack_confirm_open"):
        _render_slack_confirm_dialog()
    slack_result = st.session_state.pop("d21_slack_result", None)
    if slack_result:
        ok, message = slack_result
        (st.success if ok else st.error)(message)


@st.dialog("외부 전송 확인")
def _render_slack_confirm_dialog():
    # [Slack 신규 추가] 요청하신 확인창 흐름: 경고 -> 확인 누르면 전송 후 창 닫힘
    st.warning("⚠️ 외부 채널 — 해당 데이터가 전송됩니다.")
    if st.button("확인", key="d21_slack_confirm_ok", type="primary"):
        if not slack.SLACK_FIXED_WEBHOOK_URL:
            st.session_state["d21_slack_result"] = (False, "Slack Webhook이 설정되지 않았습니다. 환경변수 SLACK_WEBHOOK_URL 을 확인하세요.")
        else:
            report = workflow.build_report(st.session_state["d21_snapshot"])
            case_label = st.session_state["d21_case"].get("Recall Number") or "신규 입력"
            st.session_state["d21_slack_result"] = slack.send_report(report, case_label)
        st.session_state["d21_slack_confirm_open"] = False
        st.rerun()


def render_qa_final_decision(result):
    with st.container(key="shell_final"):
        st.subheader("QA Final Decision")
        left, right = st.columns([3, 7])
        c = result["classification"] if result else {}
        with left, st.container(key="shell_ai_reference"):
            st.markdown("**AI 분석 참고**")
            text_value("Root Cause", c.get("top1_root_cause", "—"), show_icon=False)
            text_value("Confidence", c.get("confidence_level", "—"), show_icon=False)
            st.text(f"Top-1: {c['top1_confidence']:.1%}" if c else "Top-1: —")
            st.caption("QA 판단을 위한 참고 정보")
        with right:
            st.markdown("**Human QA 최종 판단**")
            if not result:
                a, b = st.columns(2)
                a.selectbox("최종 Root Cause", ["분석 결과 확인 후 선택"], disabled=True, key="empty_root")
                b.multiselect("수정 사유", [], disabled=True, key="empty_reasons")
                st.text_area("판단 근거 / 검토 의견", disabled=True, height=68, key="empty_comment",
                             placeholder="분석 결과 확인 후 입력할 수 있습니다.")
                with st.container(horizontal=True, horizontal_alignment="right"):
                    st.button("QA 판단 저장", disabled=True, key="empty_save")
                return
            try:
                classes = json.loads((adapter.ROOT / "artifacts/classification/class_mapping.json").read_text(encoding="utf-8"))["classes"]
                if len(classes) != 7 or c["top1_root_cause"] not in classes:
                    raise ValueError("Invalid taxonomy")
            except (OSError, ValueError, KeyError):
                st.error("7-class taxonomy 자료를 사용할 수 없어 QA 판단 입력을 표시하지 못합니다.")
                return
            saved = st.session_state.get("d21_saved", False)
            st.session_state.setdefault("d21_final_root", c["top1_root_cause"])
            st.selectbox("최종 Root Cause", classes, index=None, key="d21_final_root", disabled=saved)
            if st.session_state["d21_final_root"] != c["top1_root_cause"]:
                st.multiselect("수정 사유", CHANGE_REASONS, key="d21_final_reasons", disabled=saved)
            st.text_area("판단 근거 / 검토 의견", key="d21_final_comment", height=68, disabled=saved)
            st.caption("QA가 직접 검토 후 저장합니다. 현재 세션 이력에만 기록됩니다.")
            with st.container(horizontal=True, horizontal_alignment="right"):
                save_clicked = st.button("QA 판단 저장", key="d21_save", disabled=st.session_state.get("d21_saved", False), type="primary")
            if save_clicked:
                save_qa_decision(result)
                if st.session_state.get("d21_saved"):
                    st.rerun()
            if st.session_state.get("d21_saved"):
                st.caption("현재 분석의 QA 판단을 세션 이력에 기록했습니다. 새 판단은 다시 분석한 뒤 입력하세요.")


def export_csv(rows):
    # Preserve session records, escape spreadsheet formula prefixes only in export.
    frame = pd.DataFrame(rows)
    def safe(value):
        if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
            return "'" + value
        return value
    return frame.map(safe).to_csv(index=False).encode("utf-8-sig")


def render_decision_history():
    rows = st.session_state["d21_history"]
    same = sum(row["동일/변경"] == "동일" for row in rows)
    ui.summary_cards([
        ("document", "총 기록", f"{len(rows)}건", "현재 세션의 QA 판단 기록"),
        ("chart", "AI 채택", f"{same}건", "AI 참고 결과와 같은 원인 선택"),
        ("pencil", "AI 수정", f"{len(rows) - same}건", "QA가 다른 원인 선택"),
    ])
    with st.container(key="shell_history_filter"):
        st.subheader("기록 검색 / 필터")
        number_col, root_col, match_col, date_col = st.columns([2, 2, 2, 2])
        number = number_col.text_input("Recall Number", key="history_number", placeholder="Recall Number 검색")
        roots = sorted({row["AI Root Cause"] for row in rows})
        root = root_col.selectbox("Root Cause (AI)", ["전체", *roots], key="history_root")
        match = match_col.selectbox("AI 결과 동일 여부", ["전체", "동일", "변경"], key="history_match")
        dates = date_col.date_input("기간 검색", value=(), key="history_dates")
        st.caption("기간 미선택: 전체 기록 · 저장 시각의 날짜를 기준으로 필터링합니다.")
        st.button("검색", key="history_search")
    filtered = [row for row in rows if number.casefold() in str(row["Recall Number"]).casefold()
                and (root == "전체" or row["AI Root Cause"] == root)
                and (match == "전체" or row["동일/변경"] == match)
                and (not dates or dates[0] <= datetime.fromisoformat(row["시각"]).date() <= dates[-1])]
    with st.container(key="shell_history_table"):
        title, download = st.columns([4, 1])
        title.subheader(f"QA 판단 이력 ({len(filtered)}건)")
        download.download_button("CSV 내보내기", export_csv(filtered) if filtered else b"", "qa_session_decisions.csv", "text/csv", disabled=not filtered)
        if filtered:
            columns = ["시각", "Recall Number", "Device Name", "AI Root Cause", "AI Confidence", "QA Final Root Cause", "동일/변경", "수정 사유", "QA 의견"]
            st.dataframe(pd.DataFrame(filtered)[columns], hide_index=True, width="stretch")
            st.caption("AI 채택/수정은 AI 결과와 QA 판단의 동일/변경을 뜻하며 정답 여부가 아닙니다. CSV에는 원 점수와 체크리스트도 포함됩니다.")
        else:
            ui.empty("현재 세션에 저장된 QA 판단이 없습니다." if not rows else "필터에 맞는 QA 판단이 없습니다.")
        ui.notice("현재 세션의 판단 기록", "영구 DB가 아닙니다. CSV를 내려받으면 사용자 파일로 남습니다. 동일·변경 여부는 QA 판단의 옳고 그름을 뜻하지 않습니다.")


def render_system_intro():
    ui.intro_cards([
        ("document", "시스템 목적", "AI와 과거 FDA Recall 근거를 제공하여 Human QA의 초기 조사와 최종 판단을 지원"),
        ("chart", "핵심 Workflow", "신규 품질이슈부터 최종 판단과 요약 보고까지 일관된 분석 프로세스 제공"),
        ("person", "Human QA Principle", "AI는 분석 근거를 제시하고, 최종 판단은 Human QA가 수행"),
    ])
    left, right = st.columns(2)
    with left, st.container(key="shell_intro_purpose"):
        st.subheader("시스템 목적")
        ui.notice("", "본 시스템은 FDA Recall 데이터를 기반으로, AI 분석 결과와 과거 사례 근거를 제공하여 Human QA의 효율적이고 일관된 의사결정을 지원하는 것을 목적으로 합니다.")
        ui.steps([
            ("초기 조사 지원", "신규 품질이슈에 대한 가능성 있는 Root Cause와 관련 근거를 신속히 제공합니다."),
            ("과거 사례 기반 근거 제공", "유사한 FDA Recall 사례와 조치 이력을 통해 판단에 필요한 참고 정보를 제공합니다."),
            ("일관된 QA 의사결정 지원", "AI 분석, 유사 사례, 체크리스트를 종합하여 Human QA의 최종 판단을 지원합니다."),
        ])
    with right, st.container(key="shell_intro_workflow"):
        st.subheader("워크플로우 (Workflow)")
        ui.workflow_steps([
            ("document", "신규 품질이슈 입력", "품질이슈에 대한 기본 정보(Recall Number, 사유, 검색 기준일 등)를 입력합니다."),
            ("list", "Root Cause Top-3 분석", "AI가 가능한 Root Cause 후보 Top-3를 제시합니다."),
            ("chart", "Confidence 제공", "각 Root Cause 후보에 대한 신뢰도(Confidence)를 제공합니다."),
            ("database", "과거 유사 Recall 검색", "각 후보와 유사한 과거 FDA Recall 사례를 검색하고 유사도를 제공합니다."),
            ("check", "QA 검토", "분석 결과와 유사 사례를 검토하고 추가 확인이 필요한 사항을 점검합니다."),
            ("person", "Human QA 최종 판단", "모든 분석 결과와 근거를 바탕으로 Human QA가 최종 판단을 수행합니다."),
            ("document", "QA Summary / Next Action", "최종 판단 결과를 요약하고, 필요한 후속 조치 및 액션 아이템을 제안합니다."),
        ])
    left, right = st.columns(2)
    with left, st.container(key="shell_intro_principles"):
        st.subheader("해석 원칙")
        ui.principle_rows([
            ("chart", "Confidence (신뢰도)", "AI가 제시한 Root Cause 후보의 검토 우선순위를 위한 보조 신호입니다. 값이 높을수록 해당 원인을 우선 검토할 필요가 있음을 의미합니다."),
            ("document", "Similarity (유사도)", "입력된 품질이슈와 과거 FDA Recall 사례 간의 유사도를 나타냅니다. 높은 유사도는 참고할 만한 근거가 될 수 있으나, 동일한 사례를 의미하지 않습니다."),
            ("database", "Recall Action (과거 조치 이력)", "과거 FDA Recall에서 수행된 조치 내역으로, 현재 이슈에 대한 대응 방안을 검토하는 데 참고할 수 있습니다."),
            ("person", "Human QA (최종 의사결정 주체)", "AI 분석 결과, 유사 사례, 체크리스트 등은 의사결정을 위한 참고 자료이며, 최종 판단과 조치는 반드시 Human QA가 수행합니다."),
        ])
    with right, st.container(key="shell_intro_limits"):
        ui.subheader_with_icon("warning", "Prototype 한계 사항")
        ui.limit_list([
            "본 시스템은 내부 검증을 위한 로컬 프로토타입입니다.",
            "분석 이력 및 결과에 대한 영구 저장 기능은 지원되지 않습니다.",
            "브라우저 및 서버 로그의 완전한 비저장은 보장되지 않습니다.",
        ])
        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
        ui.subheader_with_icon("layers", "프로젝트 Root Cause 7-class", css_class="layers")
        st.markdown('<div class="qa-tags">' + ''.join(f'<span>{ui.html(label)}</span>' for label in
                    ("설계", "소프트웨어", "공정/변경관리", "자재/부품", "포장/라벨링", "인적요인", "규제/인허가")) + '</div>', unsafe_allow_html=True)


def show_recall_tab():
    st.session_state["d21_tabs"] = TABS[1]


def main():
    st.set_page_config(page_title="FDA Recall QA Decision Support", layout="wide")
    inject_style()
    st.session_state.setdefault("d21_history", [])
    # Detach case widgets from Streamlit page cleanup while retaining session data.
    for key in list(st.session_state):
        if key.startswith(("d21_check_", "d21_final_")) or key in ("d21_reason", "d21_date", "d21_event", "d21_number", "d21_memo"):
            st.session_state[key] = st.session_state[key]
    page = render_sidebar()
    render_page_header(page)
    if page == "Recall 분석":
        render_input_section()
        result = st.session_state.get("d21_result")
        render_summary_cards(result)
        with st.container(key="shell_tabs"):
            tabs = st.tabs(TABS, key="d21_tabs", on_change="rerun")
            with tabs[0]:
                left, right = st.columns([44, 56], gap="medium")
                with left:
                    render_root_cause_tab(result["classification"] if result else {}, result["qa_review"] if result else {}, result if result else {})
                with right:
                    level = result["classification"]["confidence_level"] if result else None
                    guidance_items = workflow.GUIDANCE.get(level, ["분석 후 Confidence에 따른 검토 안내를 표시합니다."])
                    guidance_html = "".join(f"<div>· {escape(item)}</div>" for item in guidance_items)
                    st.markdown(f'<div class="qa-notice"><strong>Review Guidance ({escape(level or "분석 전")})</strong>{guidance_html}</div>', unsafe_allow_html=True)
                    # Keep the one-argument helper contract across Streamlit hot reloads.
                    # Navigation belongs to the app, not the presentation helper.
                    with st.container(horizontal=True, horizontal_alignment="right"):
                        st.button("과거 Recall 상세 보기", key="d21_recall_jump",
                                  on_click=show_recall_tab, type="tertiary")
                    ui.retrieval_preview(result["retrieval"] if result else None)
            with tabs[1]:
                render_retrieval_tab(result["retrieval"] if result else None)
            with tabs[2]:
                render_qa_review(result["qa_review"] if result else {})
            with tabs[3]:
                render_model_validation_tab()
        render_qa_final_decision(result)
        render_post_decision()
    elif page == "QA 판단 이력":
        render_decision_history()
    else:
        render_system_intro()


if __name__ == "__main__":
    main()
