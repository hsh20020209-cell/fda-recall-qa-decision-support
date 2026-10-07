"""
Root Cause별 QA Check List
============================
AI가 예측한 Root Cause에 따라, QA 담당자가 확인해야 할 항목을 안내합니다.
(정적 매핑 — 모델링과 무관, 도메인 지식 기반으로 팀/튜터 검토 필요)
"""

QA_CHECKLIST = {
    '설계': [
        '설계 사양(Design Specification) 검토',
        '설계 변경 이력(Design Change History) 확인',
        '설계 검증/밸리데이션 기록 확인',
    ],
    '공정/변경관리': [
        '공정 변경 이력(Process Change Record) 확인',
        'SOP(표준작업절차) 준수 여부 확인',
        '제조기록(Batch/Device History Record) 검토',
    ],
    '소프트웨어': [
        'SW 버전 및 변경 이력 확인',
        'Validation/검증 테스트 기록 확인',
        '펌웨어/소프트웨어 배포 이력 확인',
    ],
    '자재/부품': [
        '부품 사양(Component Specification) 확인',
        'Lot/배치 번호 추적',
        '공급업체(Supplier) 품질 이력 확인',
    ],
    '포장/라벨링': [
        '라벨 내용 및 표시사항 확인',
        '포장 공정 기록 확인',
        '라벨링 검수 절차 준수 여부 확인',
    ],
    '인적요인': [
        '사용설명서(IFU) 명확성 확인',
        '사용자 인터페이스(UI) 오조작 가능성 확인',
        '작업자 교육/숙련도 기록 확인',
        '⚠️ 참고: 이 클래스는 모델이 원천적으로 약한 영역입니다 (Test F1 0.07~0.12) — AI 예측보다 QA 직접 검토 비중을 높이는 것을 권장합니다',
    ],
    '규제/인허가': [
        '허가/승인 사항(510(k), PMA 등) 확인',
        '규제 요건 변경 여부 확인',
        '표시 광고 규정 준수 확인',
    ],
}


def get_checklist(root_cause):
    return QA_CHECKLIST.get(root_cause, ['(등록된 체크리스트 없음 — 도메인 전문가 확인 필요)'])


if __name__ == '__main__':
    for rc, items in QA_CHECKLIST.items():
        print(f"[{rc}]")
        for item in items:
            print(f"  - {item}")
        print()
