"""Read-only integration boundary for the Day21 design shell.

No model inference is implemented here. The canonical pipeline owns inference.
The lookup fallback is a verified local historical reference, never a corpus.
"""
from __future__ import annotations

import copy
import os
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REFERENCE_LOOKUP = ROOT / "production_model"  # 저장소 포함 lookup (환경변수 FDA_RECALL_LOOKUP_DIR 로 변경 가능)
CONFIDENCE_TABLE = ROOT / "out/day15_final_v3_confidence_revalidation/confidence_segment_summary.csv"

# ---------------------------------------------------------------------------
# 본인 담당 추가 기능 ① Root Cause별 "필수 확인 정보" (Day16/qa_checklist.py의
# 항목 체크리스트와는 별도로, 화면에 짧은 태그로 보여줄 목록)
# ---------------------------------------------------------------------------
REQUIRED_INFO: dict[str, list[str]] = {
    '설계': ['설계 변경 이력', '설계 사양', 'Failure Mode', '관련 부품'],
    '공정/변경관리': ['공정 변경 이력', 'SOP 버전', 'Batch Record', '변경 승인 이력'],
    '소프트웨어': ['SW/Firmware Version', '변경 이력', 'Validation 결과', '배포 일자'],
    '자재/부품': ['Lot Number', 'Supplier', 'Component', '동일 Lot 발생 여부'],
    '포장/라벨링': ['Label Version', 'Packaging Lot', 'Labeling Specification', '변경 이력'],
    '인적요인': ['IFU 버전', '작업자 교육 이력', 'UI 변경 이력'],
    '규제/인허가': ['허가/승인 번호', '규제 변경 이력', '표시광고 검토 이력'],
}

# 본인 담당 추가 기능 ② XAI 자연어 요약용 키워드-주제 매핑 (규칙 기반 요약이며
# 모델이 문맥을 실제로 이해한 것은 아님 — 화면에도 이 점을 그대로 명시함)
_KEYWORD_THEMES: dict[str, list[tuple[set, str]]] = {
    '소프트웨어': [({'software', 'anomaly', 'bug', 'firmware', 'version'}, '소프트웨어 기능 이상'),
                 ({'display', 'image', 'data', 'dose', 'treatment'}, '표시/데이터 처리 오류'),
                 ({'stop', 'interruption', 'closure', 'freeze', 'crash', 'issue'}, '시스템 동작 중단')],
    '설계': [({'design', 'specification', 'modification', 'spec'}, '설계 사양/변경'),
            ({'failure', 'fracture', 'break', 'breakage', 'crack'}, '구조적 파손'),
            ({'battery', 'power'}, '전원/배터리 관련 이상')],
    '공정/변경관리': [({'manufacturing', 'process', 'packaging', 'seal', 'sterile', 'sterility',
                     'pouch', 'compromised'}, '제조공정/멸균 이상')],
    '자재/부품': [({'material', 'component', 'specification', 'contain', 'false', 'positive',
                  'results'}, '부품/자재 규격 이상')],
    '포장/라벨링': [({'label', 'labeling', 'expiration', 'incorrect', 'mislabeled', 'package'}, '라벨/표시사항 오류')],
    '인적요인': [({'assembled', 'incorrectly', 'incorrect', 'mislabeled', 'operator'}, '조립/작업 절차 오류')],
    '규제/인허가': [({'approval', 'clearance', '510k', 'marketed', 'fda'}, '규제 승인 관련 이슈')],
}
_STOPWORDS = {
    'a', 'an', 'the', 'and', 'or', 'but', 'if', 'then', 'than', 'so', 'of', 'to', 'in', 'on',
    'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into', 'through', 'during',
    'before', 'after', 'above', 'below', 'from', 'up', 'down', 'out', 'off', 'over', 'under',
    'is', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does',
    'did', 'doing', 'this', 'that', 'these', 'those', 'it', 'its', 'as', 'due', 'may', 'which',
    'who', 'whom',
}


def _xai_explain(classification_runtime, text: str, predicted_class: str, top_n: int = 5) -> dict:
    """팀원분 Word+Character TF-IDF 모델에서 사람이 읽을 수 있는 판단 근거만 추출.
    char n-gram은 사람이 읽기 어려우므로 word 쪽 피처만 설명에 사용한다(분류 자체는 변경하지 않음)."""
    rt = classification_runtime
    vocab = rt.word_vectorizer.vocabulary_
    idx_to_word = {v: k for k, v in vocab.items()}
    classes = list(rt.classes)
    class_idx = classes.index(predicted_class)
    word_vec = rt.word_vectorizer.transform([text.lower()])
    if word_vec.nnz == 0:
        return {'top_words': [], 'natural_summary': '판단 근거 단어를 찾지 못함'}
    nonzero_idx = word_vec.nonzero()[1]
    weights = rt.classifier.coef_[class_idx][nonzero_idx]
    contributions = word_vec.data * weights
    order = np.argsort(-contributions)
    words = []
    for i in order:
        if contributions[i] <= 0:
            break
        word = idx_to_word[nonzero_idx[i]]
        if word in _STOPWORDS:
            continue
        words.append(word)
        if len(words) >= top_n:
            break
    themes = _KEYWORD_THEMES.get(predicted_class, [])
    matched = []
    for word in words:
        for kw_set, phrase in themes:
            if word in kw_set and phrase not in matched:
                matched.append(phrase)
                break
        if len(matched) >= 2:
            break
    if matched:
        phrase = ' 및 '.join(matched)
        josa = '과' if 0 <= ord(phrase[-1]) - 0xAC00 < 11172 and (ord(phrase[-1]) - 0xAC00) % 28 else '와'
        summary = f"Recall Reason에서 {phrase}{josa} 관련된 표현이 확인됨"
    elif words:
        summary = f"Recall Reason에서 '{', '.join(words[:3])}'와 유사한 표현이 확인됨"
    else:
        summary = "판단 근거 단어를 찾지 못함"
    return {'top_words': words, 'natural_summary': summary}


def _build_top3_comparison(top3: list[dict]) -> dict | None:
    """본인 담당 추가 기능 ③ Top-3 격차 분석(상태/의미/행동) + 후보별 확인 포인트."""
    if not top3:
        return None
    comparison = {
        'candidate_points': [
            {'root_cause': c['root_cause'], 'points': REQUIRED_INFO.get(c['root_cause'], [])}
            for c in top3
        ],
    }
    if len(top3) >= 2:
        gap = round(top3[0]['probability'] - top3[1]['probability'], 4)
        comparison['top1_top2_gap'] = gap
        if gap >= 0.1:
            comparison.update(gap_status='정상', gap_ok=True,
                               gap_meaning=f'후보 간 확률 차이가 충분함 ({gap*100:.0f}%p)',
                               gap_action='현재 AI 예측(1순위)을 참고하여 QA 검토')
        else:
            comparison.update(gap_status='주의', gap_ok=False,
                               gap_meaning=f'후보 간 차이가 작음 ({gap*100:.0f}%p) — 단일 원인으로 단정하기 어려움',
                               gap_action='Top-3 후보를 모두 함께 검토')
    return comparison


class _EnrichedRuntime:
    """팀원분 FinalV3QAReviewPipeline을 그대로 감싸서, 본인 담당 기능(XAI/Top-3 격차분석/
    후보별 확인포인트)만 결과에 추가한다. 분류/Confidence/Retrieval 로직은 전혀 건드리지 않는다."""

    def __init__(self, project_root):
        from pipeline.day17_qa_review_enrichment import FinalV3QAReviewPipeline
        self._pipeline = FinalV3QAReviewPipeline(project_root=Path(project_root))
        self._classification_runtime = self._pipeline.core_pipeline.classification_runtime

    def analyze_with_review(self, query_text, query_date=None, query_event_id=None):
        result = self._pipeline.analyze_with_review(query_text, query_date, query_event_id)
        classification = result.get("classification")
        if classification:
            top1 = classification["top1_root_cause"]
            result["xai_explanation"] = _xai_explain(self._classification_runtime, query_text, top1)
            result["top3_comparison"] = _build_top3_comparison(classification.get("top3_candidates") or [])
        return result


def create_runtime(project_root: str):
    # Lazy import(내부에서 수행): 추론 의존성이 없어도 shell은 그대로 열려야 함.
    return _EnrichedRuntime(project_root)


def extract_display_result(result: dict) -> dict:
    """Day20 allowlist + 본인 담당 추가 필드(xai_explanation, top3_comparison)."""
    fields = {
        "classification": ("top1_root_cause", "top1_confidence", "confidence_level",
                           "top3_candidates", "taxonomy", "human_review_required"),
        "retrieval": ("date_filter_applied", "self_match_exclusion_applied", "returned_n",
                      "insufficient_results", "insufficient_reason", "default_results", "additional_results"),
        "qa_review": ("input_quality", "qa_checklist", "ai_limitation_flags", "warnings",
                      "warning_policy_status", "review_attention_required"),
    }
    display = {key: result.get(key) for key in ("status", "status_reason")}
    display["human_review_required"] = bool(result.get("human_review_required", True))
    for section, keys in fields.items():
        source = result.get(section) or {}
        display[section] = {key: copy.deepcopy(source.get(key)) for key in keys}
    # 본인 담당 추가 필드 — 팀원분 allowlist 정책과 동일하게 필요한 키만 명시적으로 복사
    display["xai_explanation"] = copy.deepcopy(result.get("xai_explanation"))
    display["top3_comparison"] = copy.deepcopy(result.get("top3_comparison"))
    return display


def load_confidence_segment_table() -> pd.DataFrame | None:
    """Read and format stored values; no recomputation of evaluation metrics."""
    try:
        raw = pd.read_csv(CONFIDENCE_TABLE)
        rows = []
        for level in ("HIGH", "MEDIUM", "LOW"):
            row = {"Confidence": level}
            for split, label in (("VALIDATION", "Validation"), ("TEST", "Test")):
                selected = raw.loc[(raw.confidence_level == level) & (raw.split == split)]
                if len(selected) != 1:
                    return None
                for metric in ("coverage", "accuracy"):
                    row[f"{label} {metric.title()}"] = f"{float(selected[metric].iloc[0]):.2%}"
            rows.append(row)
        return pd.DataFrame(rows)
    except (OSError, ValueError, KeyError, AttributeError):
        return None


def lookup_directory() -> Path:
    configured = os.environ.get("FDA_RECALL_LOOKUP_DIR")
    if configured:
        return Path(configured)
    local = ROOT / "production_model"
    return local if local.is_dir() else REFERENCE_LOOKUP


def load_lookup_tables(directory: str):
    """Only local, user-provided trusted pickle artifacts; never upload inputs."""
    try:
        folder = Path(directory)
        db = pd.read_pickle(folder / "recall_lookup.pkl")
        mapping = pd.read_pickle(folder / "z_number_mapping.pkl")
        if not isinstance(db, pd.DataFrame) or not isinstance(mapping, pd.DataFrame):
            return None
        if not {"device_name", "recall_reason"}.issubset(db.columns):
            return None
        if "recall_number" not in mapping or not db.index.is_unique or not mapping.index.is_unique:
            return None
        return db, mapping
    except Exception:
        return None


def lookup_recall(number: str, tables) -> dict | None:
    if tables is None:
        return None
    db, mapping = tables
    key = number.strip()
    if key in mapping.index:
        key = str(mapping.loc[key, "recall_number"])
    if key not in db.index:
        return None
    row = db.loc[key]
    return {field: "" if pd.isna(row[field]) else str(row[field])
            for field in ("device_name", "recall_reason")}
