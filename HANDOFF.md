# QA Dashboard UI Handoff

## 목적

최신 기능 통합본이 아닌 Streamlit 디자인 shell 전달용이다. 팀원의 최신 backend/pipeline/save logic을 아래 UI에 연결한다. 원본 앱과 helper를 수정 없이 복사했으며 모델·원본 데이터는 포함하지 않는다. UI integration handoff package이며 production-ready package가 아니다.

## 시작 파일 / 실행

`app_design_prototype.py`. `dashboard/` helper 3개와 같은 루트에 둔다. import 유지를 위해 예시의 src/ 대신 실제 dashboard/ 이름을 유지했다. Python namespace package이므로 __init__.py 추가가 필요하지 않다.

확인 환경: Python 3.12.10, Streamlit 1.64.0, pandas 2.3.3. 기존 환경 사용을 우선하며 별도 환경에서는:

```powershell
python -m pip install -r requirements_ui.txt
python -m streamlit run app_design_prototype.py --server.address 127.0.0.1 --server.headless true --browser.gatherUsageStats false
```

발신 프로젝트에서는 `.venv_streamlit_day18/Scripts/python.exe -m streamlit run app_design_prototype.py` 형태로 실행했다. 가상환경은 미포함이다. UI-only 패키지에는 inference 코드가 없으므로 분석 실행 시 runtime unavailable이 정상이다. 공통 자료가 없어도 초기 shell·메뉴는 열리고 검증/lookup에는 unavailable이 표시된다. 가짜 분석 결과를 채우지 않는다.

## 화면 구조 / 디자인 기준

Sidebar: Recall 분석 / QA 판단 이력 / 시스템 소개.

Recall 분석: 입력 → 1×4 요약 → Root Cause · Confidence / 과거 Recall / QA 검토 / 검증 정보 → QA Final Decision → Next Action / QA Summary Report. 분석 전에도 shell 유지, 저장 전 후속 버튼 disabled.

refs/01_main.png, 02_recall.png, 03_review.png, 04_history.png, 05_intro.png가 최신 visual reference다. 이미지 sample text/score/taxonomy는 logic source of truth가 아니다. Streamlit 기본 입력/표를 유지하여 pixel-perfect 복제는 아니다.

## Integration 우선순위

| 순서 | 영역 | 연결 지점 |
|---|---|---|
| 1 | Recall lookup | adapter.lookup_directory/load_lookup_tables/lookup_recall, 앱 perform_lookup |
| 2 | analysis pipeline | adapter.create_runtime → FinalV3QAReviewPipeline.analyze_with_review(query_text, query_date, query_event_id) |
| 3 | Root Cause Top-3 | classification.top3_candidates의 rank/root_cause/probability |
| 4 | Confidence | classification.top1_root_cause/top1_confidence/confidence_level |
| 5 | Retrieval | retrieval.default_results/additional_results 및 날짜·건수 flags |
| 6 | QA checklist | qa_review.qa_checklist.items, warnings 및 pending 상태 |
| 7 | 최종 판단 저장 | 앱 save_qa_decision: 현재 session history + deep-copy snapshot |
| 8 | 판단 이력 | render_decision_history: 현재 세션 필터·CSV export |
| 9 | 검증 자료 | adapter.load_confidence_segment_table, workflow.load_manual_review |

adapter.extract_display_result의 allowlist가 표시 계약이다. Retrieval 항목은 rank, retrieved_event_id, similarity, retrieved_root_cause, retrieved_reason, retrieved_date, recall_action, specialty, product_code, device_class, firm을 사용한다. status NORMAL은 기술 처리 성공이며 QA 승인 아님. UI/helper에서는 반환값을 재분류하거나 순위를 다시 매기지 않는다.

최신 오류 수정 포함: retrieval_preview는 앱에서 인자 1개로 호출하며 상세 이동 버튼도 앱에서 관리한다. 이전 helper가 메모리에 남은 서버와 충돌하지 않도록 이 호출 형태를 유지한다. 통합 시 앱과 helper를 한 묶음으로 반영하고 서버를 재시작한다.

## 현재 template / 실제 구현 상태

- Review Guidance / Next Review Actions / Next Action: 일반 참고 템플릿. 조직 SOP·rule engine·외부 전송 없음.
- Summary: 실제 저장한 입력·분석·QA 의견/체크리스트/메모를 템플릿으로 조합, native text와 TXT 다운로드. GenAI 아님.
- 저장·이력: 세션 전용(영구 감사 추적 Audit Trail 아님). 영구 저장 backend 연결은 팀원 통합 대상. 입력 변경/새 분석은 현재 결과·스냅샷을 제거하고 이력은 유지한다.
- Retrieval Manual Review(v2): 숫자를 코드에 hard-code하지 않고 `artifacts/retrieval/manual_review_summary.json`(노션 수동검토 40건 문서의 요약, 작성자 1인 평가)에서 읽어 표시한다. 원본 평가표 `out/day19_retrieval_evaluation/manual_evaluation_sheet.csv`는 패키지에 없으며, 넣으면 CSV 집계가 추가 표시된다. 검색 정확도(%)로 표현하지 않는다.
- v2 변경 요약은 `CHANGELOG_v2.md`, v1 원본은 `versions/v1_before_tutor_feedback/`, 시나리오 검증은 `python tests/test_v2_feedback.py`.

## 절대 변경하지 말아야 할 기준

프로젝트 7-class: 설계 / 소프트웨어 / 공정/변경관리 / 자재/부품 / 포장/라벨링 / 인적요인 / 규제/인허가.

Confidence는 Top-1 predict_proba 기반 HIGH ≥0.60 / MEDIUM ≥0.30 및 <0.60 / LOW <0.30. 보정된 정답 확률·자동 승인/반려 기준 아님. Similarity는 동일 원인·QA 유용성을 보장하지 않는다. 과거 Action은 신규 이슈 권장·확정 조치 아님. Recall initiated date < 검색 기준일, 같은 날짜·입력한 같은 Event 제외. FDA 공개일/실제 이용 가능일로 표현하지 않는다. DOMAIN_REVIEW_PENDING 참고 초안 및 최종 Human QA 판단을 유지한다.

외부 텍스트는 escape/기본 텍스트로 표시한다. 사용자 다운로드는 파일로 남으며 세션/브라우저/서버 로그의 완전한 무보관을 보장하지 않는다.

## 공통 artifact / 미포함 의존성

아래는 실제 코드/config에서 확인한 기존 canonical runtime 경로다. 팀원의 기존 프로젝트에서 연결하며 UI shell을 여는 데는 필요 없다.

- 코드: pipeline/day17_qa_review_enrichment.py, pipeline/day17_qa_integration.py, classification/day16_classification_confidence_module.py, retrieval/day16_retrieval_module.py, Day16/qa_checklist.py
- 루트/설정: ARTIFACT_MANIFEST.csv, artifacts/classification/classification_config.json, artifacts/classification/class_mapping.json, artifacts/confidence/confidence_policy.json, artifacts/retrieval/retrieval_config.json
- 분류: modeling/03_word_char_tfidf/artifacts/experiment_config.json, best_word_char_model.joblib, word_tfidf_vectorizer.joblib, char_tfidf_vectorizer.joblib (뒤 3개도 동일 디렉터리)
- 검색: out/event_features_integrated_v3.csv, modeling/01_sentence_embedding/artifacts/train_event_ids.npy, modeling/01_sentence_embedding/artifacts/train_embeddings.npy, 로컬 sentence-transformers/all-MiniLM-L6-v2 모델 캐시
- 선택 lookup: production_model/recall_lookup.pkl, production_model/z_number_mapping.pkl. 신뢰하는 기존 파일만 사용한다. FDA_RECALL_LOOKUP_DIR 환경변수로 팀원 경로 지정 권장. 원본 adapter에는 발신 환경의 Downloads 하위 fallback이 남아 있으며 그 폴더는 패키지에 없다. 이 환경변수 또는 패키지 루트 production_model/을 사용한다.
- 검증: out/day15_final_v3_confidence_revalidation/confidence_segment_summary.csv
- 수동평가: out/day19_retrieval_evaluation/manual_evaluation_sheet.csv 및 evaluation_guide.md

전체 추론 환경은 기존 numpy/scipy/scikit-learn/joblib/sentence-transformers 및 그 의존성이 필요하다. 이 패키지의 requirements는 UI-only이며 직렬화 모델과 호환되는 기존 runtime 환경을 유지한다. historical synthetic 후보와 current executable Word+Character 모델은 다른 대상이므로 임의 교체하지 않는다.

## 최소 확인 / 통합 후 검증

압축 해제 루트에서 모델 없이 초기 shell 검사:

```powershell
python -c "from streamlit.testing.v1 import AppTest; a=AppTest.from_file('app_design_prototype.py').run(); assert not a.exception; assert len(a.tabs)==4; print('UI shell PASS')"
```

기존 tests/day21_design_prototype_test.py는 Day18 테스트·원본 데이터·모델 등 전체 프로젝트에 의존한다. day21_preview_compatibility_test.py도 이 테스트를 import하므로 불완전한 테스트 묶음을 전달하지 않기 위해 제외했다. 통합 프로젝트에서는 기존 HIGH/MEDIUM/LOW·공통 데모의 결과 일치, 0/2개 검색, 오류 후 결과 제거, QA 저장 전후 버튼, 입력 수정 시 보고서 제거를 재검증한다.
