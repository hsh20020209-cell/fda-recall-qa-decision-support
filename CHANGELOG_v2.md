# CHANGELOG — v1 → v2 (튜터 피드백 반영)

- **v1**: 최초 설계(노션 9페이지 기획 + 팀원 UI shell 통합본). 원본 파일은 `versions/v1_before_tutor_feedback/` 에 보관.
- **v2**: 튜터 피드백을 반영한 유지보수 버전. 새 기능 추가 없이 정보구조·판단 독립성·검증 표시·시연 검증 중심으로 수정.

## 피드백 항목별 변경

| # | 피드백 | v1 | v2 | 주요 파일 |
|---|---|---|---|---|
| 1 | Recall 분석 화면 정보구조 간소화 | 탭 4개(Root Cause·Confidence / 과거 Recall / QA 검토 / 검증 정보) + 하단에 QA Final Decision | 탭 3개 **AI 분석 결과 / 과거 사례·근거 / QA 검토·판단**. Confidence Validation/Test 검증 정보는 접이식, 중복되던 유사 Recall Preview 표 제거, QA Final Decision·후속 단계는 '검토·판단' 탭으로 이동 | `app_design_prototype.py` |
| 2 | Human QA 판단 독립성 | 최종 Root Cause 기본값 = AI Top-1, 다른 원인일 때만 수정 사유 | **기본값 미선택**. AI와 같은 원인을 고르면 "직접 검토했음" 명시 확인 체크 필수, 같은 원인/다른 원인 **모두 판단 근거 필수**(다르면 이유 선택도 필수). 이력·보고서에 `AI 제안 명시 확인` 기록 | `app_design_prototype.py`, `day21_prototype_workflow.py` |
| 3 | Retrieval 근거 신뢰성·평가 보완 | Retrieval Manual Review 가 '자료 없음' | 수동 평가 요약(GOOD 28 / PARTIAL 7 / POOR 5, LOW 15건 9/4/2), 평가 기준, 대표 성공·부분·실패 사례 표시. **개시일 기준 필터링(적용·검증)과 실제 정보 공개 시점 검증(미수행)을 구분**해 안내 | `artifacts/retrieval/manual_review_summary.json`, `dashboard/day23_manual_review.py` |
| 4 | 시연 검증 / Audit Trail 과장 금지 | 시나리오 검증 없음 | AI≠QA 사례, Confidence LOW 사례 포함 자동 시나리오 검증(`tests/test_v2_feedback.py`, 24항목). 이력·소개·판단 화면에 "현재 세션에만 유지, 영구 감사 추적(Audit Trail) 아님" 명시 | `tests/`, `app_design_prototype.py` |
| - | 시스템 소개 페이지 크기 | Streamlit 컬럼에 전역 flex 강제 + 고정 min-height(640/450/380px) 충돌 | 같은 행의 두 패널을 **하나의 CSS grid**로 렌더링(높이 자동 일치), 전역 flex 강제·고정 min-height 제거, 반응형(1050px 이하 1열) | `dashboard/day21_prototype_ui.py` |

## 수동 평가 요약 데이터에 대한 주의

- `manual_review_summary.json` 은 프로젝트 노션 "Retrieval 수동검토 40건" 문서의 **요약**이며, 원본 평가표(`out/day19_retrieval_evaluation/manual_evaluation_sheet.csv`)는 이 패키지에 없습니다.
- 숫자는 코드에 넣지 않고 이 JSON에서만 읽습니다. 원본 CSV를 해당 경로에 넣으면 CSV 집계가 추가로 표시됩니다.
- 작성자 1인의 수동 평가이며 전문 QA 검증이 아닙니다. 검색 정확도(%)로 해석하지 않습니다.

## 남은 한계 (v2에서도 유지)

- QA 판단 이력은 세션 전용입니다. 영구 저장, 사용자·변경 이력, 위변조 방지가 없어 **Audit Trail 이 아닙니다**.
- 실제 정보 공개 시점 검증은 수행하지 않았습니다(개시일 필터링만).
- Slack 전송은 팀 기본 설계에 없던 확장이며 외부 전송 확인창을 거칩니다.
