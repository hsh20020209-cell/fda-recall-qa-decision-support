"""Retrieval 수동 평가 요약 표시 (읽기 전용).

원본 평가표(manual_evaluation_sheet.csv)가 있으면 그 집계를 함께 보여주고,
없으면 artifacts/retrieval/manual_review_summary.json(작성자 수동 평가 요약)을 표시한다.
숫자는 코드에 넣지 않고 JSON 파일에서만 읽는다.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st


def load_summary(root: Path):
    try:
        return json.loads((Path(root) / "artifacts/retrieval/manual_review_summary.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def summary_label(summary) -> str:
    if not summary:
        return "Retrieval 수동 평가 · 자료 없음"
    q = summary["query_quality"]
    return f"Retrieval 수동 평가 · GOOD {q['GOOD']} · PARTIAL {q['PARTIAL']} · POOR {q['POOR']} (Query {sum(q.values())}건)"


def render(root: Path, csv_evidence=None):
    summary = load_summary(root)
    if summary is None:
        st.caption("수동 평가 요약 자료(artifacts/retrieval/manual_review_summary.json)를 찾을 수 없습니다.")
        return
    st.warning(summary["notice"])
    st.caption("평가 범위 · " + summary["scope"])
    q, low = summary["query_quality"], summary["low_confidence_queries"]
    frame = pd.DataFrame([
        {"구분": f"전체 Query {sum(q.values())}건", "GOOD": q["GOOD"], "PARTIAL": q["PARTIAL"], "POOR": q["POOR"]},
        {"구분": f"Confidence LOW Query {low['total']}건", "GOOD": low["GOOD"], "PARTIAL": low["PARTIAL"], "POOR": low["POOR"]},
    ])
    st.dataframe(frame, hide_index=True, width="stretch")
    st.caption("GOOD: 비교할 근거가 있음 · PARTIAL: 보조 참고 수준 · POOR: 조사에 도움이 될 근거를 찾기 어려움")
    checks = " · ".join(f"{k} {v}건" for k, v in summary["logic_checks"].items())
    st.caption("검색 로직 검증: " + checks)
    st.markdown("**평가 기준**")
    st.markdown("\n".join(f"- {item}" for item in summary["criteria"]))
    st.markdown("**대표 사례 (성공 · 부분 · 실패)**")
    cases = pd.DataFrame(summary["cases"]).rename(columns={"kind": "구분", "case": "사례", "observation": "검색 결과 관찰", "implication": "시사점"})
    st.dataframe(cases, hide_index=True, width="stretch")
    if csv_evidence and sum(csv_evidence["counts"].values()):
        st.caption("원본 평가표(CSV) 집계: " + " · ".join(f"{k} {v}건" for k, v in csv_evidence["counts"].items()))
    st.caption("출처: " + summary["source"])
