"""Presentation-only guidance, immutable report formatting, read-only review evidence."""
from pathlib import Path
import json
import pandas as pd

GUIDANCE = {
    "HIGH": ["Top-3 후보와 유사 Recall을 함께 비교하세요.", "핵심 근거를 확인하세요. HIGH도 자동 승인 기준이 아닙니다."],
    "MEDIUM": ["Top-3 후보 간 차이를 함께 확인하세요.", "유사 Recall의 제품 Context를 비교하세요.", "최종 Root Cause는 QA가 결정합니다."],
    "LOW": ["AI 결과에 대한 의존도를 낮추세요.", "원문과 품질 기록을 확인하고 추가 근거를 확보하세요."],
}
REVIEW_ACTIONS = ["관련 변경 이력과 품질 기록을 교차 확인합니다.",
                  "Complaint / CAPA에서 동일 패턴 존재 여부를 확인합니다.",
                  "유사 Recall의 제품 Context와 규제 문맥을 비교합니다.",
                  "필요 시 추가 검토 또는 보고 여부를 결정합니다."]
NEXT_ACTIONS = ["관련 품질 기록을 확인합니다.", "Complaint / CAPA 이력을 확인합니다.",
                "과거 Recall과 현재 제품의 Context를 비교합니다.",
                "필요 시 관련 검토 담당자에게 추가 검토를 요청합니다.", "추가 조사 결과와 판단 근거를 기록합니다."]


def load_manual_review(directory):
    """Count recorded human labels only; incomplete/conflicting query groups stay pending."""
    directory = Path(directory)
    try:
        frame = pd.read_csv(directory / "manual_evaluation_sheet.csv", dtype=str, keep_default_na=False)
        required = {"query_event_id", "query_quality", "pair_judgment"}
        if not required.issubset(frame.columns) or frame.empty or frame.query_event_id.eq("").any():
            return None
        counts = dict.fromkeys(("GOOD", "PARTIAL", "POOR"), 0)
        pending = conflicts = 0
        for _, group in frame.groupby("query_event_id"):
            labels = group.query_quality.str.strip()
            if labels.nunique() == 1 and labels.iloc[0] in counts:
                counts[labels.iloc[0]] += 1
            else:
                pending += 1
                conflicts += int(bool(set(labels) - {"", "GOOD", "PARTIAL", "POOR"}) or len(set(labels) - {""}) > 1)
        return {"queries": int(frame.query_event_id.nunique()), "pairs": len(frame),
                "pair_reviewed": int(frame.pair_judgment.isin(["USEFUL", "PARTIAL", "NOT_USEFUL"]).sum()),
                "counts": counts, "pending": pending, "conflicts": conflicts}
    except (OSError, ValueError, pd.errors.ParserError):
        return None


def build_report(snapshot):
    """Plain text only: explicit saved snapshot, no inference or external service."""
    result, decision = snapshot["result"], snapshot["decision"]
    c = result["classification"]
    lines = ["QA Summary Report · Template", "현재 세션에서 저장한 판단의 요약 · 자동 승인/권장 조치가 아닙니다.",
             "", "1. Case 정보"]
    lines += [f"{k}: {v or '정보 없음'}" for k, v in snapshot["case"].items()]
    lines += ["", "2. AI Analysis", f"Confidence: {c['confidence_level']} · Top-1 score: {c['top1_confidence']}"]
    lines += [f"Rank {x['rank']} | {x['root_cause']} | {x['probability']}" for x in c["top3_candidates"]]
    lines += ["Confidence는 보정된 정답 확률·자동 승인 기준이 아닙니다.", "", "3. Historical Evidence"]
    items = result["retrieval"]["default_results"] + result["retrieval"]["additional_results"]
    for x in items[:3]:
        reason = " ".join(str(x.get("retrieved_reason") or "정보 없음").split())
        lines.append(f"Rank {x['rank']} | Event {x['retrieved_event_id']} | Similarity {x['similarity']} | {x.get('retrieved_root_cause')}")
        lines.append(reason[:240] + ("…" if len(reason) > 240 else ""))
    if not items:
        lines.append("검색 조건에 맞는 과거 사례 없음")
    lines += ["Similarity는 동일 원인·QA 유용성을 보장하지 않습니다. 과거 Action은 신규 이슈 권장 조치가 아닙니다.",
              "Recall initiated date < 검색 기준일. FDA 공개일/당시 정보 이용 가능일을 의미하지 않습니다.",
              "", "4. QA Review · DOMAIN_REVIEW_PENDING 참고 초안"]
    lines += [f"[{'확인' if checked else '미확인'}] {item}" for item, checked in json.loads(decision["Checklist 상태"]).items()]
    lines += ["추가 확인 필요사항: " + (snapshot["memo"] or "입력 없음"), "", "5. Final Decision"]
    lines += [f"{k}: {decision[k] or '입력 없음'}" for k in ("시각", "QA Final Root Cause", "동일/변경", "수정 사유", "QA 의견")]
    lines += ["", "6. Next Actions · 일반 참고 템플릿 (확정 조치/SOP 아님)"] + NEXT_ACTIONS
    return "\n".join(lines)
