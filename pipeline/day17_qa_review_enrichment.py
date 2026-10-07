"""QA review enrichment layered on the validated Day17 core pipeline.

The core classification, confidence, and retrieval outputs are preserved as-is.
This layer adds only provisional input-quality guidance, a domain-review-pending
checklist, and two evidence-backed limitation warnings. XAI is not included.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import numpy as np

from Day16.qa_checklist import QA_CHECKLIST
from pipeline.day17_qa_integration import FinalV3QAPipeline


SHORT_INPUT_WORD_THRESHOLD = 6
PLACEHOLDER_TERMS = {
    "unknown",
    "n/a",
    "na",
    "none",
    "tbd",
    "pending",
    "issue",
    "problem",
    "defect",
    ".",
}

LOW_CONFIDENCE_WARNING = (
    "모델의 예측 확신도가 낮습니다. Root Cause 후보와 과거 Recall 근거를 함께 "
    "비교하고 추가 조사가 필요합니다."
)
HUMAN_FACTOR_WARNING = (
    "인적요인은 현재 모델에서 예측 성능이 제한적인 클래스입니다. 다른 Root Cause "
    "후보와 추가 조사 정보를 함께 확인해야 합니다."
)


def _is_nonfinite_number(value: Any) -> bool:
    return isinstance(value, (float, np.floating)) and not math.isfinite(float(value))


def _json_safe_input(value: Any) -> Any:
    """Keep invalid-input meaning while removing non-standard JSON numbers."""
    if _is_nonfinite_number(value):
        return None
    if isinstance(value, np.generic):
        return value.item()
    return value


def _is_model_specific_checklist_note(item: str) -> bool:
    # The source Human Factor list contains a historical-model Test-F1 note.
    # It is retained in the source file for audit but is not an operational QA
    # checklist action and therefore is not exposed in the review response.
    return "Test F1" in item


class FinalV3QAReviewPipeline:
    """Add QA review context without rerunning or changing core predictions."""

    def __init__(
        self,
        project_root: str | Path | None = None,
        *,
        core_pipeline: Any | None = None,
    ) -> None:
        self.core_pipeline = core_pipeline or FinalV3QAPipeline(project_root)
        self.qa_checklist_source = QA_CHECKLIST
        self.excluded_source_items = {
            root_cause: [
                item for item in items if _is_model_specific_checklist_note(item)
            ]
            for root_cause, items in self.qa_checklist_source.items()
            if any(_is_model_specific_checklist_note(item) for item in items)
        }

    def checklist_for_root_cause(self, root_cause: str) -> dict[str, Any]:
        if root_cause not in self.qa_checklist_source:
            raise KeyError(f"No QA checklist mapping for Root Cause: {root_cause!r}")
        items = [
            item
            for item in self.qa_checklist_source[root_cause]
            if not _is_model_specific_checklist_note(item)
        ]
        return {
            "root_cause": root_cause,
            "items": list(items),
            "status": "DOMAIN_REVIEW_PENDING",
            "source": "Day16/qa_checklist.py",
            "excluded_model_specific_source_item_count": len(
                self.excluded_source_items.get(root_cause, [])
            ),
        }

    @staticmethod
    def _input_quality(query_text: str) -> dict[str, Any]:
        stripped = query_text.strip()
        word_count = len(stripped.split())
        short_input = word_count < SHORT_INPUT_WORD_THRESHOLD
        # This exactly follows the normalization and source term list in the
        # teammate's qa_decision_pipeline.py; it remains provisional guidance.
        placeholder = stripped.lower().rstrip(".") in PLACEHOLDER_TERMS
        warnings: list[str] = []
        if short_input:
            warnings.append(
                f"문장 길이 부족({word_count}단어, 최소 "
                f"{SHORT_INPUT_WORD_THRESHOLD}단어 권장)"
            )
        if placeholder:
            warnings.append("의미 없는 placeholder성 입력으로 추정")
        return {
            "word_count": word_count,
            "short_input": short_input,
            "placeholder_detected": placeholder,
            "warnings": warnings,
            "heuristic_policy_status": "PROVISIONAL",
            "analysis_blocked_by_heuristic": False,
        }

    def analyze_with_review(
        self,
        query_text: str,
        query_date: str | None = None,
        query_event_id: str | None = None,
    ) -> dict[str, Any]:
        """Call the core pipeline once, then append review-only information."""
        core_result = self.core_pipeline.analyze(
            query_text, query_date=query_date, query_event_id=query_event_id
        )
        result = dict(core_result)
        result["query_text"] = _json_safe_input(core_result.get("query_text"))

        if core_result["classification"] is None:
            # Invalid text was already rejected by the Day17-2 layer. No
            # prediction-based checklist or model limitation flag is generated.
            input_warning = core_result.get("status_reason")
            result["qa_review"] = {
                "input_quality": {
                    "word_count": None,
                    "short_input": None,
                    "placeholder_detected": None,
                    "warnings": [input_warning] if input_warning else [],
                    "heuristic_policy_status": "NOT_APPLICABLE",
                    "analysis_blocked_by_heuristic": False,
                },
                "qa_checklist": None,
                "ai_limitation_flags": None,
                "warnings": [input_warning] if input_warning else [],
                "warning_policy_status": "NOT_APPLICABLE",
                "review_attention_required": True,
            }
            return result

        classification = core_result["classification"]
        confidence_level = classification["confidence_level"]
        top1_root_cause = classification["top1_root_cause"]
        input_quality = self._input_quality(query_text)
        low_confidence = confidence_level == "LOW"
        human_factor_case = top1_root_cause == "인적요인"
        limitation_warnings: list[str] = []
        if low_confidence:
            limitation_warnings.append(LOW_CONFIDENCE_WARNING)
        if human_factor_case:
            limitation_warnings.append(HUMAN_FACTOR_WARNING)
        warnings = [*input_quality["warnings"], *limitation_warnings]

        result["qa_review"] = {
            "input_quality": input_quality,
            "qa_checklist": self.checklist_for_root_cause(top1_root_cause),
            "ai_limitation_flags": {
                "low_confidence": low_confidence,
                "human_factor_case": human_factor_case,
            },
            "warnings": warnings,
            "warning_policy_status": "PROVISIONAL",
            "review_attention_required": bool(warnings),
        }
        return result


_DEFAULT_REVIEW_PIPELINE: FinalV3QAReviewPipeline | None = None


def analyze_quality_issue_with_review(
    query_text: str,
    query_date: str | None = None,
    query_event_id: str | None = None,
) -> dict[str, Any]:
    """Convenience function backed by one lazily loaded review pipeline."""
    global _DEFAULT_REVIEW_PIPELINE
    if _DEFAULT_REVIEW_PIPELINE is None:
        _DEFAULT_REVIEW_PIPELINE = FinalV3QAReviewPipeline()
    return _DEFAULT_REVIEW_PIPELINE.analyze_with_review(
        query_text, query_date, query_event_id
    )


__all__ = [
    "FinalV3QAReviewPipeline",
    "analyze_quality_issue_with_review",
    "LOW_CONFIDENCE_WARNING",
    "HUMAN_FACTOR_WARNING",
]
