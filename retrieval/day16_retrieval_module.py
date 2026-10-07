"""Final-v3 semantic retrieval runtime for FDA Recall QA.

This module reuses the stored Train embeddings and encodes only the incoming
query text. It does not train a model, regenerate the corpus embeddings,
rerank results, or apply structured hard filters.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer


def _find_project_root(start: Path | None = None) -> Path:
    start = (start or Path.cwd()).resolve()
    for candidate in (start, *start.parents):
        if (candidate / "ARTIFACT_MANIFEST.csv").is_file() and (
            candidate / "artifacts" / "retrieval" / "retrieval_config.json"
        ).is_file():
            return candidate
    raise FileNotFoundError(
        "Project root with ARTIFACT_MANIFEST.csv and retrieval_config.json was not found."
    )


def _event_key(value: Any) -> str:
    """Normalize CSV/NumPy Event IDs without changing their substantive value."""
    if pd.isna(value):
        return ""
    if isinstance(value, (int, np.integer)):
        return str(int(value))
    if isinstance(value, (float, np.floating)) and float(value).is_integer():
        return str(int(value))
    return str(value).strip()


def _clean_output(value: Any) -> Any:
    if pd.isna(value):
        return None
    if isinstance(value, np.generic):
        return value.item()
    return value


class FinalV3RecallRetriever:
    """Read-only final-v3 Train-corpus retriever."""

    def __init__(
        self,
        project_root: str | Path | None = None,
        *,
        local_files_only: bool = True,
    ) -> None:
        self.project_root = _find_project_root(
            Path(project_root) if project_root is not None else None
        )
        self.config_path = (
            self.project_root / "artifacts" / "retrieval" / "retrieval_config.json"
        )
        self.config = json.loads(self.config_path.read_text(encoding="utf-8"))

        if self.config.get("similarity") != "cosine":
            raise ValueError("retrieval_config.json does not specify cosine similarity.")
        if not self.config.get("normalize_embeddings", False):
            raise ValueError("Current runtime requires normalized corpus embeddings.")
        if self.config.get("corpus_role") != "historical_train_only":
            raise ValueError("Corpus role is not historical_train_only.")
        if self.config.get("structured_hard_filter") is not False:
            raise ValueError("Structured hard filtering must remain disabled.")
        if self.config.get("reranking") is not False:
            raise ValueError("Reranking must remain disabled.")

        # These paths come directly from retrieval_config.json; no fallback path
        # guessing is performed.
        self.data_path = self.project_root / self.config["corpus_data"]
        self.train_ids_path = self.project_root / self.config["corpus_event_ids"]
        self.train_embeddings_path = self.project_root / self.config["train_embeddings"]
        for path in (self.data_path, self.train_ids_path, self.train_embeddings_path):
            if not path.is_file():
                raise FileNotFoundError(f"Configured retrieval artifact not found: {path}")

        self.train_embeddings = np.load(self.train_embeddings_path, mmap_mode="r")
        self.train_event_ids = np.load(self.train_ids_path, allow_pickle=True)
        self.train_event_keys = np.asarray(
            [_event_key(x) for x in self.train_event_ids], dtype=object
        )

        if self.train_embeddings.ndim != 2:
            raise ValueError("Train embedding artifact is not a 2D matrix.")
        if len(self.train_embeddings) != len(self.train_event_keys):
            raise ValueError("Train embedding rows and Event ID rows do not match.")
        if len(set(self.train_event_keys)) != len(self.train_event_keys):
            raise ValueError("Duplicate Event IDs exist in the Train Event ID artifact.")
        expected_rows = int(self.config["snapshot_verification"]["train_rows"])
        if len(self.train_event_keys) != expected_rows:
            raise ValueError(
                f"Train corpus has {len(self.train_event_keys):,} rows; expected {expected_rows:,}."
            )
        expected_dim = int(self.config["embedding_dimension"])
        if self.train_embeddings.shape[1] != expected_dim:
            raise ValueError(
                f"Embedding dimension is {self.train_embeddings.shape[1]}; expected {expected_dim}."
            )
        norms = np.linalg.norm(np.asarray(self.train_embeddings), axis=1)
        if not np.allclose(norms, 1.0, atol=1e-3):
            raise ValueError("Stored Train embeddings are not normalized as configured.")

        # Actual integrated-v3 -> runtime output mapping:
        # reason_for_recall_clean -> retrieved_reason
        # root_cause_group        -> retrieved_root_cause
        # action_clean            -> recall_action
        # specialties             -> specialty
        # product_codes           -> product_code
        # device_classes          -> device_class
        # firm_norm               -> firm
        columns = [
            "res_event_number",
            "reason_for_recall_clean",
            "root_cause_group",
            "action_clean",
            "specialties",
            "product_codes",
            "device_classes",
            "firm_norm",
            "event_date_initiated_clean",
        ]
        events = pd.read_csv(self.data_path, usecols=columns, low_memory=False)
        events["_event_key"] = events["res_event_number"].map(_event_key)
        if events["_event_key"].duplicated().any():
            raise ValueError("Event metadata contains duplicate res_event_number values.")
        metadata = events.set_index("_event_key", drop=False)
        missing_ids = [key for key in self.train_event_keys if key not in metadata.index]
        if missing_ids:
            raise ValueError(
                f"{len(missing_ids)} Train Event IDs are missing from event metadata."
            )
        # Reindexing by train_event_ids.npy is the alignment contract between
        # embedding row i and Event metadata row i.
        self.corpus = metadata.loc[self.train_event_keys].reset_index(drop=True)
        self.corpus_dates = pd.to_datetime(
            self.corpus["event_date_initiated_clean"], errors="coerce"
        )
        if self.corpus_dates.isna().any():
            raise ValueError("Train retrieval corpus contains an invalid initiated date.")
        if not np.array_equal(
            self.corpus["_event_key"].to_numpy(dtype=object), self.train_event_keys
        ):
            raise ValueError("Embedding/Event ID/metadata alignment check failed.")

        self.embedding_model_name = self.config["embedding_model"]
        self._encoder = SentenceTransformer(
            self.embedding_model_name, local_files_only=local_files_only
        )
        self.default_k = int(self.config["default_k"])
        self.max_k = int(self.config["max_k"])

    @property
    def artifact_info(self) -> dict[str, Any]:
        return {
            "config": self.config_path.relative_to(self.project_root).as_posix(),
            "corpus_data": self.data_path.relative_to(self.project_root).as_posix(),
            "train_event_ids": self.train_ids_path.relative_to(self.project_root).as_posix(),
            "train_embeddings": self.train_embeddings_path.relative_to(
                self.project_root
            ).as_posix(),
            "embedding_model": self.embedding_model_name,
            "corpus_rows": int(len(self.corpus)),
            "embedding_dimension": int(self.train_embeddings.shape[1]),
            "corpus_role": self.config["corpus_role"],
        }

    def retrieve(
        self,
        query_text: str,
        query_date: str | None = None,
        query_event_id: str | None = None,
    ) -> dict[str, Any]:
        """Return final-v3 Train-corpus semantic matches.

        The response contains the default Top-3, optional ranks 4-5, and all
        available results up to the configured max_k. When query_date is None,
        no date is imputed and no date filter is applied.
        """
        if not isinstance(query_text, str) or not query_text.strip():
            raise ValueError("query_text must be a non-empty string.")

        date_filter_applied = query_date is not None
        parsed_query_date: pd.Timestamp | None = None
        if date_filter_applied:
            parsed_query_date = pd.to_datetime(query_date, errors="coerce")
            if pd.isna(parsed_query_date):
                raise ValueError(f"query_date could not be parsed: {query_date!r}")
            parsed_query_date = pd.Timestamp(parsed_query_date)

        query_key = _event_key(query_event_id) if query_event_id is not None else None
        allowed = np.ones(len(self.corpus), dtype=bool)
        if date_filter_applied:
            allowed &= self.corpus_dates.to_numpy() < np.datetime64(parsed_query_date)
        if query_key:
            allowed &= self.train_event_keys != query_key

        query_embedding = self._encoder.encode(
            [query_text.strip()],
            normalize_embeddings=bool(self.config["normalize_embeddings"]),
            show_progress_bar=False,
            convert_to_numpy=True,
        )[0]
        if query_embedding.shape[0] != self.train_embeddings.shape[1]:
            raise ValueError("Query and corpus embedding dimensions do not match.")
        if not np.isclose(np.linalg.norm(query_embedding), 1.0, atol=1e-3):
            raise ValueError("Query embedding was not normalized as configured.")

        # With normalized query/corpus vectors, the dot product is cosine
        # similarity. No alternate metric, reranking, or structured filter is used.
        similarities = np.asarray(self.train_embeddings @ query_embedding).reshape(-1)
        eligible_indices = np.flatnonzero(allowed)
        ranked_indices = eligible_indices[
            np.argsort(-similarities[eligible_indices], kind="stable")[: self.max_k]
        ]

        results: list[dict[str, Any]] = []
        for rank, idx in enumerate(ranked_indices, start=1):
            row = self.corpus.iloc[int(idx)]
            results.append(
                {
                    "rank": rank,
                    "retrieved_event_id": _event_key(row["res_event_number"]),
                    "similarity": float(similarities[idx]),
                    "retrieved_reason": _clean_output(row["reason_for_recall_clean"]),
                    "retrieved_root_cause": _clean_output(row["root_cause_group"]),
                    "recall_action": _clean_output(row["action_clean"]),
                    "specialty": _clean_output(row["specialties"]),
                    "product_code": _clean_output(row["product_codes"]),
                    "device_class": _clean_output(row["device_classes"]),
                    "firm": _clean_output(row["firm_norm"]),
                    "retrieved_date": pd.Timestamp(
                        row["event_date_initiated_clean"]
                    ).date().isoformat(),
                }
            )

        insufficient = len(results) < self.default_k
        if insufficient:
            insufficient_reason = (
                f"Only {len(results)} eligible historical Train recalls remained "
                "after the requested date/self-match filters."
            )
        else:
            insufficient_reason = None

        date_policy_note = None
        if not date_filter_applied:
            date_policy_note = (
                "query_date was not provided, so no date filter was applied. "
                "The final operating policy for missing query dates is not yet decided by the team."
            )

        return {
            "query_text": query_text,
            "query_date": parsed_query_date.isoformat() if parsed_query_date else None,
            "query_event_id": query_key,
            "date_filter_applied": date_filter_applied,
            "self_match_exclusion_applied": query_event_id is not None,
            "date_policy_note": date_policy_note,
            "corpus_role": "historical_train_only",
            "test_data_used": False,
            "similarity": "cosine",
            "structured_hard_filter": False,
            "reranking": False,
            "default_k": self.default_k,
            "max_k": self.max_k,
            "eligible_corpus_n": int(allowed.sum()),
            "returned_n": len(results),
            "insufficient_results": insufficient,
            "insufficient_reason": insufficient_reason,
            "default_results": results[: self.default_k],
            "additional_results": results[self.default_k :],
            "results": results,
        }


_DEFAULT_RETRIEVER: FinalV3RecallRetriever | None = None


def retrieve_similar_recalls(
    query_text: str,
    query_date: str | None = None,
    query_event_id: str | None = None,
) -> dict[str, Any]:
    """Convenience function using a lazily initialized final-v3 retriever."""
    global _DEFAULT_RETRIEVER
    if _DEFAULT_RETRIEVER is None:
        _DEFAULT_RETRIEVER = FinalV3RecallRetriever()
    return _DEFAULT_RETRIEVER.retrieve(query_text, query_date, query_event_id)


__all__ = ["FinalV3RecallRetriever", "retrieve_similar_recalls"]
