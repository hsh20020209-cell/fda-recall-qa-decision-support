# FDA Recall QA Decision Support

FDA 의료기기 Recall 데이터를 분석해, 신규 품질이슈에 대한 **Root Cause 후보(Top-3) · Confidence · 과거 유사 Recall**을 제시하고
**최종 판단은 Human QA가 기록**하도록 돕는 QA 의사결정 지원 대시보드(Streamlit)와 분석 노트북입니다.

> 이 시스템은 의사결정 **보조 도구**입니다. Root Cause를 자동으로 확정하거나 조치를 권고하지 않으며, 모든 화면에 `QA Review: Required`가 표시됩니다.

## 핵심 결과 (final-v3, 시간 기준 분할 Train 13,645 / Valid 1,338 / Test 1,042)

| 항목 | 값 |
|---|---|
| 데이터 | openFDA Medical Device Recall, Recall Event 22,468건 (확정 Root Cause 16,025건) |
| 분류 모델 | Word + Character TF-IDF + SGD (7-class) |
| Test Accuracy / Macro F1 | 50.48% / 0.4496 |
| Top-1 → Top-2 → Top-3 Hit Rate | 50.48% → 76.97% → 89.92% |
| Confidence (Top-1 확률) | HIGH ≥ 0.6 · MEDIUM 0.3~<0.6 · LOW < 0.3 (Test 정확도 76.17% / 47.21% / 30.83%) |

* Confidence는 **보정된 정답 확률이 아니라 검토 우선순위 신호**입니다(ECE 0.0522, 전반적으로 과소확신). HIGH도 자동 승인 기준이 아닙니다.
* 유사 Recall 검색은 정확도가 아니라 **사람이 읽는 수동 평가**로 확인했습니다(작성자 1인, 40 Query: GOOD 28 · PARTIAL 7 · POOR 5).
* 자세한 분석 과정(EDA → 모델링 → 오류 분석 → Confidence → 검색 → 대시보드 통합)은 [`notebooks/FDA_Recall_QA_Project.ipynb`](notebooks/FDA_Recall_QA_Project.ipynb)에 실행 결과와 함께 들어 있습니다.

## 화면 구성

사이드바 메뉴: **Recall 분석 / QA 판단 이력 / 시스템 소개**

Recall 분석 화면은 3개 영역으로 구성됩니다.

1. **AI 분석 결과** — Root Cause Top-3, Confidence, 모델 예측 근거(키워드), 후보별 확인 포인트, Confidence 검증 정보(접이식)
2. **과거 사례·근거** — 개시일 기준으로 필터링한 유사 Recall Top-3(+더 보기), 검색 기준 안내, Retrieval 수동 평가 요약과 대표 성공·실패 사례
3. **QA 검토·판단** — 조사 체크리스트, Next Review Actions, 메모, **QA Final Decision**(AI 참고 결과와 분리), QA Summary Report

### Human QA 판단 규칙 (v2)
* 최종 Root Cause는 **기본값 없이 QA가 직접 선택**합니다(AI Top-1이 자동 입력되지 않음).
* AI 제안과 **같은 원인**을 선택해도 "직접 검토했음"을 명시적으로 확인하고 판단 근거를 적어야 저장됩니다.
* **다른 원인**을 선택하면 이유 선택과 판단 근거가 필요합니다.
* 판단 이력은 **현재 세션에만** 유지됩니다. 영구 저장이나 감사 추적(Audit Trail)이 아닙니다.

## 저장소 구조

```
├─ streamlit_app.py            # 진입점 (app_design_prototype.main 호출)
├─ app_design_prototype.py     # 화면 구성 · 상태 관리
├─ dashboard/                  # 어댑터(XAI·확인 포인트), UI 컴포넌트, 워크플로우, 수동 평가 표시, Slack(선택)
├─ classification/             # Word+Char TF-IDF + SGD 분류, Confidence
├─ retrieval/                  # MiniLM 유사 Recall 검색
├─ pipeline/  Day16/           # 분류·검색 통합, QA 검토 체크리스트
├─ artifacts/                  # 분류·Confidence·검색 설정, 수동 평가 요약(manual_review_summary.json)
├─ modeling/                   # 저장된 TF-IDF 벡터라이저·모델, Train 임베딩
├─ production_model/           # Recall Number 조회용 lookup
├─ out/                        # Event 단위 데이터, Confidence 재검증 결과
├─ notebooks/                  # 과제 제출용 분석 노트북
├─ tests/                      # v2 시나리오 검증
├─ CHANGELOG_v2.md  HANDOFF.md
└─ requirements.txt  .streamlit/
```

## 빠른 시작 (로컬)

```bash
git clone <이 저장소 URL>
cd fda-recall-qa-decision-support
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

* Python 3.12 / Streamlit 1.64.0 기준으로 검증했습니다.
* 처음 실행할 때 `sentence-transformers`가 MiniLM(`all-MiniLM-L6-v2`) 모델을 내려받으므로 **인터넷 연결이 필요**합니다.
* 분류 모델(joblib)은 scikit-learn **1.9.0**으로 저장되어 `requirements.txt`에서 같은 버전으로 고정했습니다.

## 배포 (Streamlit Community Cloud)

1. 이 저장소를 GitHub에 push 합니다.
2. [share.streamlit.io](https://share.streamlit.io) → **New app** → 저장소 선택, **Main file path = `streamlit_app.py`**, Python 3.12.
3. (선택) Slack 전송을 쓰려면 **Advanced settings → Secrets**에 `.streamlit/secrets.toml.example`의 형식으로 `SLACK_WEBHOOK_URL`을 입력합니다.

**주의**
* `torch` + `sentence-transformers`는 메모리를 많이 사용합니다. 무료 플랜의 메모리 제한에 걸릴 수 있으니 배포 후 앱이 정상 기동하는지 확인하세요. 부족하면 로컬 실행 또는 더 큰 메모리를 제공하는 호스팅을 사용하세요.
* **Slack Webhook URL을 코드나 저장소에 넣지 마세요.** 환경변수 `SLACK_WEBHOOK_URL` 또는 `.streamlit/secrets.toml`(`.gitignore` 처리됨)로만 설정합니다. 설정하지 않으면 전송 버튼을 눌러도 안내 메시지만 표시됩니다.
* 이 대시보드는 사용자별 영구 저장 없이 **세션 단위**로 동작하며, 외부 접속자도 같은 앱을 사용하므로 개인정보나 비공개 품질 데이터를 입력하지 마세요.

## 분석 노트북

```bash
pip install -r requirements-notebook.txt
jupyter lab notebooks/FDA_Recall_QA_Project.ipynb
```

노트북에서 **[재계산]**으로 표시된 결과는 이 저장소의 데이터·아티팩트로 직접 계산한 값이고, **[보고값]**은 원본 실험 환경(과거 스냅샷, GPU 모델, 수동 평가 등)이 저장소에 없어 프로젝트 보고서의 값을 그대로 옮긴 것입니다.

## 테스트

```bash
python tests/test_v2_feedback.py                      # 실제 환경
QA_TEST_MOCK_ENCODER=1 python tests/test_v2_feedback.py   # MiniLM 다운로드가 불가능한 환경(검색 내용은 무작위, 흐름만 검증)
```

AI≠QA 판단, Confidence LOW 사례, 같은 원인 채택 시 명시적 확인, 시스템 소개 레이아웃 등 24개 시나리오를 Streamlit AppTest로 검증합니다.

## 버전

| 태그 | 내용 |
|---|---|
| `v1.0` | 최초 설계(노션 기획 + UI shell 통합본) |
| `v2.0` | 튜터 피드백 반영: 정보구조 3개 영역 압축, Human QA 판단 독립성, Retrieval 수동 평가·정보 공개 시점 구분, 시연 검증, 소개 페이지 레이아웃 |

변경 내용은 [`CHANGELOG_v2.md`](CHANGELOG_v2.md), 인수인계 메모는 [`HANDOFF.md`](HANDOFF.md)를 참고하세요.

## 한계

* 확정된 Root Cause 사례(16,025건)만 학습했으며, 분류체계(7-class)는 FDA 공식 분류가 아닌 프로젝트 정의입니다.
* 인적요인은 Top-3에서도 44.44%(Test 27건)로 약하고, 증강 효과는 통계적으로 확정하지 못했습니다.
* Word+Char 모델이 Word 단독보다 낫다는 것은 통계적으로 확정되지 않았으며(McNemar p=0.916), 재현 가능한 기준 모델로 연결했습니다.
* Confidence 정책은 잠정 검증 상태이며 보정되지 않았습니다.
* 검색 평가는 작성자 1인의 수동 평가이고, 개시일 기준 필터링은 실제 정보 공개 시점을 보장하지 않습니다.
* QA 판단 이력은 세션 전용이며 영구 감사 추적이 아닙니다.

## 데이터 출처

[openFDA Medical Device Recall](https://open.fda.gov/apis/device/recall/) 공개 데이터. 이 프로젝트는 FDA와 무관하며, 결과는 FDA의 공식 판단이 아닙니다.

## 팀

팀 현지인 — 유현지, 한인지, 황수현
