"""v2(튜터 피드백 반영) 화면 시나리오 검증. 프로젝트 루트에서 실행:

    python tests/test_v2_feedback.py

* 실제 환경: sentence-transformers 가 설치돼 있으면 그대로 실제 모델로 실행됩니다.
* 샌드박스처럼 모델을 받을 수 없는 환경: QA_TEST_MOCK_ENCODER=1 (검색 결과 내용은 무작위라 흐름만 검증).
분류 결과(Root Cause / Confidence)는 항상 실제 저장 모델을 사용합니다.
"""
import os, sys, datetime
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT); sys.path.insert(0, str(ROOT))
if os.environ.get("QA_TEST_MOCK_ENCODER") == "1":
    import numpy as np
    from unittest.mock import MagicMock
    class _Enc:
        def __init__(self, *a, **k): pass
        def encode(self, texts, **k):
            n = 1 if isinstance(texts, str) else len(texts)
            r = np.random.RandomState(1); v = r.randn(n, 384).astype("float32")
            return v / np.linalg.norm(v, axis=1, keepdims=True)
    fake = MagicMock(); fake.SentenceTransformer = _Enc; sys.modules["sentence_transformers"] = fake
from streamlit.testing.v1 import AppTest

import pandas as pd
_EV = pd.read_csv(ROOT / "out/event_features_integrated_v3.csv", low_memory=False).set_index("res_event_number")
LOW_TEXT = _EV.loc[96075, "reason_for_recall_clean"]    # final-v3 Test, 저장된 예측 Confidence 0.272 (LOW)
HIGH_TEXT = _EV.loc[96055, "reason_for_recall_clean"]   # final-v3 Test, 저장된 예측 Confidence 0.764 (HIGH)
DATE = datetime.date(2026, 10, 6)
RESULTS = []
def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond))); print(("PASS" if cond else "FAIL"), "-", name, detail)

def new_app():
    at = AppTest.from_file(str(ROOT / "app_design_prototype.py"), default_timeout=180); at.run(); return at
def analyze(at, text):
    at.text_area(key="d21_reason").set_value(text); at.date_input(key="d21_date").set_value(DATE)
    at.button(key="d21_analyze").click().run()
def warns(at): return " ".join(str(w.value) for w in at.warning)
def md(at): return " ".join(str(m.value) for m in at.markdown)

at = new_app()
check("앱이 예외 없이 시작", not at.exception)
check("상세 탭이 3개 영역으로 압축", [t.label for t in at.tabs] == ["AI 분석 결과", "과거 사례·근거", "QA 검토·판단"], str([t.label for t in at.tabs]))
check("검증 정보는 접이식(expander)으로 제공", any("Confidence 검증 정보" in e.label for e in at.expander))
check("수동 평가 요약이 '자료 없음'이 아님", any(e.label.startswith("Retrieval 수동 평가 · GOOD 28 · PARTIAL 7 · POOR 5") for e in at.expander), str([e.label for e in at.expander if "수동" in e.label]))

# --- HIGH 사례: AI와 같은 원인 채택
analyze(at, HIGH_TEXT)
res = at.session_state["d21_result"]["classification"]
ai = res["top1_root_cause"]; check("분석 후 개시일 필터링과 정보 공개 시점 검증을 구분해 안내", "개시일 기준 필터링 ≠ 정보 공개 시점 검증" in md(at))
check("HIGH 사례 분석", res["confidence_level"] == "HIGH", f"{ai} {res['top1_confidence']:.3f}")
check("최종 Root Cause 기본값이 미선택(AI Top-1이 기본값 아님)", at.selectbox(key="d21_final_root").value is None)
at.button(key="d21_save").click().run()
check("미선택 상태로는 저장 불가", ("d21_saved" not in at.session_state or not at.session_state["d21_saved"]) and "직접 선택해 주세요" in warns(at))
at.selectbox(key="d21_final_root").set_value(ai).run()
check("AI와 같은 원인을 고르면 명시적 확인 체크박스가 나타남", any(c.key == "d21_final_confirm" for c in at.checkbox))
at.button(key="d21_save").click().run(); check("확인 없이 저장 불가", "직접 검토했음을 확인" in warns(at))
at.checkbox(key="d21_final_confirm").check().run(); at.button(key="d21_save").click().run(); check("근거 없이 저장 불가(같은 원인 선택 시에도)", "판단 근거를 간단히 기록" in warns(at))
at.text_area(key="d21_final_comment").set_value("Recall Reason의 software 관련 표현과 과거 사례를 검토해 AI 제안에 동의함").run(); at.button(key="d21_save").click().run()
row = at.session_state["d21_history"][-1] if at.session_state["d21_history"] else {}
check("확인+근거가 있으면 저장되고 이력에 기록", row.get("동일/변경") == "동일" and row.get("AI 제안 명시 확인") == "확인함" and "동의" in row.get("QA 의견", ""), str({k: row.get(k) for k in ("동일/변경", "AI 제안 명시 확인")}))

# --- LOW Confidence 사례: AI와 다른 원인 선택
at.button(key="d21_clear").click().run(); analyze(at, LOW_TEXT)
res = at.session_state["d21_result"]["classification"]; ai = res["top1_root_cause"]
check("LOW Confidence 사례 분석", res["confidence_level"] == "LOW", f"{ai} {res['top1_confidence']:.3f}")
check("LOW 안내 문구 표시", "AI 결과에 대한 의존도를 낮추세요" in md(at))
classes = list(at.selectbox(key="d21_final_root").options); other = next(c for c in classes if c != ai)
at.selectbox(key="d21_final_root").set_value(other).run()
check("AI와 다른 원인을 고르면 '다른 이유' 선택이 나타남", any(m.key == "d21_final_reasons" for m in at.multiselect))
at.button(key="d21_save").click().run(); check("이유 없이 저장 불가", "다른 판단의 이유" in warns(at))
at.multiselect(key="d21_final_reasons").set_value(["QA 조사 결과와 차이"]).run(); at.button(key="d21_save").click().run(); check("근거 없이 저장 불가(다른 원인 선택 시)", "판단 근거를 간단히 기록" in warns(at))
at.text_area(key="d21_final_comment").set_value("원문 확인 결과 needle 분리 문제로 공정/변경관리 가능성을 우선 검토").run(); at.button(key="d21_save").click().run()
row = at.session_state["d21_history"][-1]
check("AI≠QA 판단이 이력에 '변경'으로 기록", row["동일/변경"] == "변경" and row["AI Confidence"] == "LOW" and row["QA Final Root Cause"] == other, str((row["AI Root Cause"], row["QA Final Root Cause"])))
at.button(key="d21_report").click().run()
report = " ".join(str(t.value) for t in at.text)
check("QA Summary Report에 판단 근거·AI 제안 확인 항목 포함", "AI 제안 명시 확인" in report and "원문 확인 결과" in report)
check("검색 기준일 ≠ 공개일 안내가 보고서에 포함", "FDA 공개일/당시 정보 이용 가능일을 의미하지 않습니다" in report)

# --- 이력 / 시스템 소개
at.sidebar.radio(key="d21_navigation").set_value("QA 판단 이력").run()
check("이력 화면: 영구 감사 추적이 아님을 명시", "Audit Trail" in md(at) and not at.exception)
at.sidebar.radio(key="d21_navigation").set_value("시스템 소개").run()
html = md(at)
check("시스템 소개 예외 없음", not at.exception)
check("소개 패널이 CSS grid 2행(4패널)으로 렌더링", html.count('class="qa-intro-grid"') == 2 and html.count('class="qa-intro-panel') == 4, f"grid={html.count('class=\"qa-intro-grid\"')} panel={html.count('class=\"qa-intro-panel')}")
check("한계 사항에 감사 추적 아님 명시", "Audit Trail" in html)
failed = [n for n, ok in RESULTS if not ok]
print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} PASS"); sys.exit(1 if failed else 0)
