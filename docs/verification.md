# verification.md — V1·V2 통합 검증 (T11·T21)

> 검증일: 2026-10-05 (V1), 2026-10-16 (V2 추기) / 방법: synthetic fixture로 갈음, 실데이터 검증 없음

## 1. 대조표
| # | 수용 기준 | 결과 | 근거 |
|---|---|---|---|
| ① | 프로젝트 목록이 활성/비활성으로 구분되어 표시되고, 선택한 프로젝트의 세션명 목록이 보임 | 충족 | `tests/test_gui.py::test_window_loads_fixture` — 대시보드 "활성 1 / 비활성 1", 프로젝트 선택 후 세션 행 1건 이상 표시 확인 |
| ② | Desktop 종료 여부와 무관하게 읽기전용 조회가 크래시 없이 동작 | 충족 | `test_missing_db_no_crash` — 존재하지 않는 DB 경로로 창 생성 시 예외 없이 안내 문구 표시 |
| ③ | DB 잠금 시 에러 대신 안내 문구 표시 | 충족 | `src/errors.py::DbLocked` 문구 + `MainWindow._show_lock` 패널 안내. `test_db_projects_and_counts` ro 접속 경로 커버 |
| ④ | 실데이터 대신 fixture/복사본으로 검증한 기록이 `TASKS.md`에 남음 | 충족 | `pytest tests` 12 passed (synthetic fixture만). 실DB·원본 `.dat` 접근 없음. 본 파일 + T08/T09/T10 검증란에 기록 |

## 2. 진단 일치 (T06→T10)
- T06 실측 대조표(`docs/diagnostic-rules.md` §3)와 T10 재현 fixture 결과가 일치: R02·R03만 발동, R01/R04/R05 미발동.
- V1 구현 블록(T08→T09→T10→T11) 완료. T12 이후는 PENDING-V2로 착수 금지.

## 3. V2 통합 검증 (T21)
- 왕복: `tests/test_v2_roundtrip.py` — 세션 삭제→복원 SHA-256+id 일치, 프로젝트 통째 정리→복원(`project` 행 포함) 일치. `pytest tests` 26 passed.
- `v2_backup` 최소 확장 (T17 산출물): project 계열 수집·복원·검증 추가. 기존 T17 테스트 회귀 없음.
- 제외 3종: `src/` 실행 코드 grep 무검출 (유일 히트는 `v2_safety.py` docstring의 금지 선언). GUI QPushButton 2개 유지, V2 버튼 미연결 확인.
- Non-Goal 대조: `FEATURES.md` §5와 T12 §4 정합. 실데이터 검증 없음.
