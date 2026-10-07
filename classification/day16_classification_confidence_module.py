"""Final-v3 Word + Character TF-IDF classification/confidence runtime.

This module loads the existing fitted vectorizers and SGDClassifier. It never
fits a vectorizer, retrains/calibrates a model, or changes confidence policy.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from scipy.sparse import hstack


def _find_project_root(start: Path | None = None) -> Path:
    start = (start or Path.cwd()).resolve()
    for candidate in (start, *start.parents):
        if (candidate / "ARTIFACT_MANIFEST.csv").is_file() and (
            candidate / "artifacts" / "classification" / "classification_config.json"
        ).is_file():
            return candidate
    raise FileNotFoundError(
        "Project root with ARTIFACT_MANIFEST.csv and classification config was not found."
    )


def confidence_level_for_score(
    confidence: float,
    *,
    low_threshold: float = 0.3,
    high_threshold: float = 0.6,
) -> str:
    """Apply the configured top-1 probability policy to a supplied score."""
    if isinstance(confidence, bool) or not isinstance(
        confidence, (int, float, np.integer, np.floating)
    ):
        raise TypeError("confidence must be a numeric scalar.")
    value = float(confidence)
    if not np.isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError("confidence must be finite and between 0 and 1.")
    if not 0.0 <= low_threshold < high_threshold <= 1.0:
        raise ValueError("Confidence thresholds must satisfy 0 <= low < high <= 1.")
    if value >= high_threshold:
        return "HIGH"
    if value >= low_threshold:
        return "MEDIUM"
    return "LOW"


class FinalV3ClassificationConfidence:
    """Read-only runtime for the final-v3 executable classification baseline."""

    def __init__(self, project_root: str | Path | None = None) -> None:
        self.project_root = _find_project_root(
            Path(project_root) if project_root is not None else None
        )
        self.classification_config_path = (
            self.project_root
            / "artifacts"
            / "classification"
            / "classification_config.json"
        )
        self.class_mapping_path = (
            self.project_root / "artifacts" / "classification" / "class_mapping.json"
        )
        self.confidence_policy_path = (
            self.project_root / "artifacts" / "confidence" / "confidence_policy.json"
        )
        self.experiment_config_path = (
            self.project_root
            / "modeling"
            / "03_word_char_tfidf"
            / "artifacts"
            / "experiment_config.json"
        )
        for path in (
            self.classification_config_path,
            self.class_mapping_path,
            self.confidence_policy_path,
            self.experiment_config_path,
        ):
            if not path.is_file():
                raise FileNotFoundError(f"Required configured file not found: {path}")

        self.classification_config = json.loads(
            self.classification_config_path.read_text(encoding="utf-8")
        )
        self.class_mapping = json.loads(
            self.class_mapping_path.read_text(encoding="utf-8")
        )
        self.confidence_policy = json.loads(
            self.confidence_policy_path.read_text(encoding="utf-8")
        )
        self.experiment_config = json.loads(
            self.experiment_config_path.read_text(encoding="utf-8")
        )

        executable = self.classification_config.get("current_executable_baseline", {})
        if executable.get("runtime_ready") is not True or executable.get("final_v3") is not True:
            raise ValueError("Configured executable baseline is not runtime-ready final-v3.")

        # Artifact paths are read from classification_config.json. There is no
        # fallback search or substitution with the historical Synthetic model.
        self.model_path = self.project_root / executable["model"]
        self.word_vectorizer_path = self.project_root / executable["word_vectorizer"]
        self.char_vectorizer_path = self.project_root / executable["char_vectorizer"]
        for path in (self.model_path, self.word_vectorizer_path, self.char_vectorizer_path):
            if not path.is_file():
                raise FileNotFoundError(f"Configured classification artifact not found: {path}")

        self.classifier = joblib.load(self.model_path)
        self.word_vectorizer = joblib.load(self.word_vectorizer_path)
        self.char_vectorizer = joblib.load(self.char_vectorizer_path)
        if not callable(getattr(self.classifier, "predict_proba", None)):
            raise TypeError("Stored classifier does not support predict_proba().")
        if not hasattr(self.classifier, "classes_"):
            raise TypeError("Stored classifier has no fitted classes_ attribute.")

        self.classes = [str(value) for value in self.classifier.classes_.tolist()]
        configured_classes = [str(value) for value in self.class_mapping.get("classes", [])]
        if self.classes != configured_classes:
            raise ValueError(
                "classifier.classes_ and class_mapping.json differ; no automatic correction applied."
            )

        self.low_threshold = float(self.confidence_policy["low_threshold"])
        self.high_threshold = float(self.confidence_policy["high_threshold"])
        if self.confidence_policy.get("confidence_type") != "top1_probability":
            raise ValueError("Confidence policy is not top1_probability.")
        if self.low_threshold != 0.3 or self.high_threshold != 0.6:
            raise ValueError(
                "confidence_policy.json does not match the established 0.3/0.6 policy."
            )

        self.char_weight = float(self.experiment_config["best_char_weight"])
        self.word_dimension = len(self.word_vectorizer.get_feature_names_out())
        self.char_dimension = len(self.char_vectorizer.get_feature_names_out())
        self.combined_dimension = self.word_dimension + self.char_dimension
        if int(self.classifier.n_features_in_) != self.combined_dimension:
            raise ValueError(
                "Saved vectorizer dimensions do not match classifier.n_features_in_."
            )
        if self.experiment_config.get("text_column") != (
            "reason_lower (reason_for_recall_clean lowercased)"
        ):
            raise ValueError("Experiment text preprocessing definition is unexpected.")

        word_expected = self.experiment_config["word_tfidf_settings"]
        word_actual = self.word_vectorizer.get_params()
        word_matches = (
            tuple(word_actual["ngram_range"]) == tuple(word_expected["ngram_range"])
            and word_actual["min_df"] == word_expected["min_df"]
            and word_actual["max_features"] == word_expected["max_features"]
            and word_actual["sublinear_tf"] is word_expected["sublinear_tf"]
            and word_actual["analyzer"] == "word"
            and word_actual["lowercase"] is True
        )
        char_expected = self.experiment_config["best_character_tfidf_settings"]
        char_actual = self.char_vectorizer.get_params()
        char_matches = (
            char_actual["analyzer"] == char_expected["analyzer"]
            and tuple(char_actual["ngram_range"])
            == tuple(char_expected["ngram_range"])
            and char_actual["min_df"] == char_expected["min_df"]
            and char_actual["sublinear_tf"] is char_expected["sublinear_tf"]
            and char_actual["lowercase"] is True
        )
        sgd_expected = self.experiment_config["sgd_settings"]
        sgd_actual = self.classifier.get_params()
        sgd_matches = all(
            sgd_actual[key] == expected for key, expected in sgd_expected.items()
        )
        self.training_settings_verified = word_matches and char_matches and sgd_matches
        if not self.training_settings_verified:
            raise ValueError(
                "Stored model/vectorizer parameters differ from experiment_config.json."
            )

    @property
    def artifact_info(self) -> dict[str, Any]:
        def relative(path: Path) -> str:
            return path.relative_to(self.project_root).as_posix()

        return {
            "model": relative(self.model_path),
            "word_vectorizer": relative(self.word_vectorizer_path),
            "char_vectorizer": relative(self.char_vectorizer_path),
            "experiment_config": relative(self.experiment_config_path),
            "classification_config": relative(self.classification_config_path),
            "class_mapping": relative(self.class_mapping_path),
            "confidence_policy": relative(self.confidence_policy_path),
            "word_dimension": self.word_dimension,
            "char_dimension": self.char_dimension,
            "combined_dimension": self.combined_dimension,
            "char_weight": self.char_weight,
            "training_settings_verified": self.training_settings_verified,
        }

    def confidence_level(self, confidence: float) -> str:
        return confidence_level_for_score(
            confidence,
            low_threshold=self.low_threshold,
            high_threshold=self.high_threshold,
        )

    @staticmethod
    def _validate_query_text(query_text: str) -> None:
        if not isinstance(query_text, str):
            raise TypeError("query_text must be a string.")
        if not query_text.strip():
            raise ValueError("query_text must be a non-empty, non-whitespace string.")

    def classify(self, query_text: str) -> dict[str, Any]:
        """Classify one Recall Reason using one predict_proba() invocation."""
        self._validate_query_text(query_text)

        # Training notebook created reason_lower with Series.str.lower(). It did
        # not add stemming, stop-word removal, or any other text transformation.
        reason_lower = query_text.lower()
        word_features = self.word_vectorizer.transform([reason_lower])
        char_features = self.char_vectorizer.transform([reason_lower])
        features = hstack(
            [word_features, char_features * self.char_weight], format="csr"
        )
        if features.shape != (1, self.combined_dimension):
            raise ValueError("Runtime feature shape does not match the trained model.")

        # This is the only predict_proba() call. Classification Top-3 and
        # confidence reuse this exact probability vector.
        probabilities = np.asarray(self.classifier.predict_proba(features)[0], dtype=float)
        if probabilities.shape != (len(self.classes),):
            raise ValueError("Probability output does not align with classifier.classes_.")
        if not np.isclose(probabilities.sum(), 1.0, atol=1e-9):
            raise ValueError("Classifier probabilities do not sum to one.")

        order = np.argsort(-probabilities, kind="stable")
        top3 = [
            {
                "rank": rank,
                "root_cause": self.classes[int(index)],
                "probability": float(probabilities[int(index)]),
            }
            for rank, index in enumerate(order[:3], start=1)
        ]
        confidence = float(top3[0]["probability"])
        return {
            "query_text": query_text,
            "top1_root_cause": top3[0]["root_cause"],
            "top1_confidence": confidence,
            "confidence_level": self.confidence_level(confidence),
            "top3_candidates": top3,
            "classifier_classes_order": list(self.classes),
            "model_name": "word_char_tfidf_sgd",
            "taxonomy": "project_defined_7class",
            "human_review_required": True,
        }


_DEFAULT_RUNTIME: FinalV3ClassificationConfidence | None = None


def classify_quality_issue(query_text: str) -> dict[str, Any]:
    """Convenience function backed by a lazily loaded final-v3 runtime."""
    global _DEFAULT_RUNTIME
    if _DEFAULT_RUNTIME is None:
        _DEFAULT_RUNTIME = FinalV3ClassificationConfidence()
    return _DEFAULT_RUNTIME.classify(query_text)


__all__ = [
    "FinalV3ClassificationConfidence",
    "classify_quality_issue",
    "confidence_level_for_score",
]
