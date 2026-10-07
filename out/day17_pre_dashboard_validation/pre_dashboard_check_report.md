# Day17-4A 실제 모델 기반 사전 점검

## 1. 이번 점검의 목적

final-v3 Validation에서 실제 저장 모델이 HIGH·MEDIUM·LOW로 예측한 사례를 각각 1건 선정해 Classification, Retrieval, QA 검토 정보가 대시보드 구현 전에 끝까지 연결되는지 확인했다. 새로운 성능 평가나 정책 조정은 수행하지 않았다.

## 2. HIGH·MEDIUM·LOW 실제 실행 결과

선정 방식은 각 구간별 Event ID 문자열 오름차순 정렬 후 NumPy `default_rng(42)`로 1건을 추출하는 방식이다.

| 구간 | Event | 실제 Root Cause | Top-3 | Confidence | Retrieval Top-3 | 체크리스트 | 경고 |
|---|---:|---|---|---:|---|---|---|
| HIGH | 92243 | 자재/부품 | 1위 소프트웨어 (0.7153), 2위 설계 (0.1873), 3위 포장/라벨링 (0.0287) | 0.7153 | 1위 Event 84337 (0.6348), 2위 Event 80671 (0.5395), 3위 Event 64070 (0.5291) | 소프트웨어 / DOMAIN_REVIEW_PENDING | 없음 |
| MEDIUM | 95224 | 공정/변경관리 | 1위 포장/라벨링 (0.3262), 2위 인적요인 (0.2601), 3위 공정/변경관리 (0.2306) | 0.3262 | 1위 Event 84732 (0.5873), 2위 Event 65993 (0.5841), 3위 Event 74896 (0.5774) | 포장/라벨링 / DOMAIN_REVIEW_PENDING | 없음 |
| LOW | 94833 | 공정/변경관리 | 1위 인적요인 (0.2751), 2위 자재/부품 (0.2656), 3위 공정/변경관리 (0.1896) | 0.2751 | 1위 Event 57515 (0.5320), 2위 Event 53955 (0.5225), 3위 Event 93876 (0.4976) | 인적요인 / DOMAIN_REVIEW_PENDING | 모델의 예측 확신도가 낮습니다. Root Cause 후보와 과거 Recall 근거를 함께 비교하고 추가 조사가 필요합니다.; 인적요인은 현재 모델에서 예측 성능이 제한적인 클래스입니다. 다른 Root Cause 후보와 추가 조사 정보를 함께 확인해야 합니다. |

세 사례 모두 `status=NORMAL`, `human_review_required=true`다. NORMAL과 HIGH는 자동 승인이나 정답 보장을 의미하지 않는다.

## 3. 기존 모듈과의 결과 일치 여부

- Classification 전체 결과: 3/3 완전 일치
- Top-3 순위와 full-precision 확률: 3/3 일치
- Confidence 값과 구간: Day15 저장값 및 현재 모델과 3/3 일치
- Retrieval 전체 결과와 Recall Action: 3/3 일치
- QA enrichment로 인한 핵심 결과 변경: 없음

## 4. QA 체크리스트 및 경고 표시 결과

- 실제 Top-1 Root Cause에 대응하는 체크리스트 연결: 3/3
- 체크리스트 상태: 모두 `DOMAIN_REVIEW_PENDING`
- 과거 모델의 `Test F1` 문구 노출: 0건
- LOW 사례: LOW Confidence 경고 표시 및 Retrieval 유지
- HIGH·MEDIUM 사례: LOW 경고 미표시
- 실제 선정 사례의 인적요인 Top-1: 1건
- 실제 인적요인 경고 검증 상태: `VERIFIED_ON_ACTUAL_SELECTED_CASE`

## 5. 날짜 필터 및 날짜 미입력 검증

- 날짜 입력 3건: `date_filter_applied=true`
- 미래 Recall 검색: 0건
- 동일 Event 검색: 0건
- 검색 결과의 Train corpus 이탈: 0건
- LOW Event `94833` 날짜 미입력 추가 실행: `date_filter_applied=false`, 정책 안내 문구 유지
- 날짜 미입력 시 미래검색 방지는 보장된 것으로 판정하지 않았다.

## 6. 대시보드 구현 전에 남은 사항

1. 날짜 미입력 Retrieval 허용 여부는 `DECISION_NEEDED`다.
2. QA 체크리스트 문구는 도메인 검토 전이므로 `DOMAIN_REVIEW_PENDING`을 표시해야 한다.
3. 실제 모델의 인적요인 Top-1 경고는 Event 94833에서 검증됐다. 더 넓은 실제 QA 사례 검토는 별도 단계다.
4. QA 화면은 HIGH에서도 Top-3와 과거 Recall 근거를 제공하고, Recall Action을 신규 이슈 권고로 표현하지 않아야 한다.
5. 실제 QA 사용자 검토와 실행 환경 점검은 별도 단계다.

## 최종 결과

**PASS** — 실제 final-v3 HIGH·MEDIUM·LOW 구간별 전체 실행 경로와 JSON 직렬화를 확인했다. 이 결과는 성능 평가가 아니라 실행 정합성 검증이다.
