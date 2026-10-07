"""Day17 final-v3 QA core integration pipeline.

This module orchestrates the already validated Day16 classification/confidence
and retrieval runtimes. It does not duplicate or modify either runtime's model,
feature, confidence, or retrieval logic.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from classification.day16_classification_confidence_module import (
    FinalV3ClassificationConfidence,
)
from retrieval.day16_retrieval_module import FinalV3RecallRetriever


class FinalV3QAPipeline:
    """Run final-v3 classification/confidence and retrieval for one issue."""

    def __init__(
        self,
        project_root: str | Path | None = None,
        *,
        classification_runtime: Any | None = None,
        retrieval_runtime: Any | None = None,
    ) -> None:
        # Default construction loads each heavy runtime once. Optional runtime
        # injection is limited to integration testing; production defaults are
        # always the validated Day16 classes below.
        self.classification_runtime = classification_runtime or (
            FinalV3ClassificationConfidence(project_root)
        )
        self.retrieval_runtime = retrieval_runtime or FinalV3RecallRetriever(
            project_root
        )

    @staticmethod
    def _input_error(query_text: Any) -> str | None:
        if query_text is None:
            return "query_text is None. A Recall Reason string is required."
        if isinstance(query_text, (float, np.floating)) and np.isnan(query_text):
            return "query_text is NaN. A Recall Reason string is required."
        if not isinstance(query_text, str):
            return "query_text must be a string."
        if not query_text.strip():
            return "query_text is empty or whitespace-only."
        return None

    def analyze(
        self,
        query_text: str,
        query_date: str | None = None,
        query_event_id: str | None = None,
    ) -> dict[str, Any]:
        """Return one structured result for Human QA review.

        Invalid text inputs are routed to REVIEW_REQUIRED without invoking
        either core inference method. Unexpected runtime or artifact errors are
        intentionally allowed to propagate instead of being disguised as input
        quality outcomes.
        """
        error = self._input_error(query_text)
        if error is not None:
            return {
                "query_text": query_text,
                "query_date": query_date,
                "query_event_id": query_event_id,
                "status": "REVIEW_REQUIRED",
                "status_reason": error,
                "human_review_required": True,
                "classification": None,
                "retrieval": None,
            }

        # The exact original text is passed to both runtimes. Lowercasing for
        # TF-IDF remains internal to the Day16 classification runtime.
        classification = self.classification_runtime.classify(query_text)
        # Retrieval runs for every valid text, independent of confidence level.
        retrieval = self.retrieval_runtime.retrieve(
            query_text,
            query_date=query_date,
            query_event_id=query_event_id,
        )
        return {
            "query_text": query_text,
            "query_date": query_date,
            "query_event_id": query_event_id,
            "status": "NORMAL",
            "status_reason": None,
            "human_review_required": True,
            "classification": classification,
            "retrieval": retrieval,
        }


_DEFAULT_PIPELINE: FinalV3QAPipeline | None = None


def analyze_quality_issue(
    query_text: str,
    query_date: str | None = None,
    query_event_id: str | None = None,
) -> dict[str, Any]:
    """Convenience function backed by one lazily loaded pipeline instance."""
    global _DEFAULT_PIPELINE
    if _DEFAULT_PIPELINE is None:
        _DEFAULT_PIPELINE = FinalV3QAPipeline()
    return _DEFAULT_PIPELINE.analyze(query_text, query_date, query_event_id)


__all__ = ["FinalV3QAPipeline", "analyze_quality_issue"]
