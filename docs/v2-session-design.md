# v2-session-design.md — V2 세션 단위 삭제/보관 설계 (설계만, 코드 없음)

> 작성일: 2026-10-08 / 상태: v1 초안 / 전제: T12 요구(V2-R02), T13 안전장치(S01–S05) 전제
> 범위: 세션 1건 단위. 프로젝트 통째 처리는 T15에서 별도 확정. 본 문서는 설계이며 V1 앱·`src/` 변경 없음.

## 1. 보관 (V2-R01 대응)
- `session.time_archived`에 보관 시각 기록 (기존 컬럼 활용, T02에서 3건 존재 확인).
- 보관 세션은 목록·집계에서 제외 표시, 복원은 `time_archived` NULL 환원.
- S04 2단계 확인 적용, S01–S03 면제 (원본 유지), S05 복원 제공.

## 2. 삭제 cascade (V2-R02 대응)
- FK 제약 존재 미확인 전제이므로 앱 레벨 순서 삭제로 정합 보장. 순서:
  1. `part` (`session_id`·`message_id` 경유)
  2. `message` (`session_id`)
  3. `todo` (`session_id`), `session_context_epoch`·`session_input`·`session_message`·`session_share` (세션 id 연계, 구현 시 컬럼 재확인)
  4. `event` (`aggregate_id`=세션 id), `event_sequence` (세션 대응분)
  5. `session` 본 행
- 삭제 후 검증 조건: 위 테이블에 해당 세션 id 잔류 0건 (고아 row 없음).
- `project`·`project_directory`는 건드리지 않음 (세션 단위 범위 밖).

## 3. `session_diff` 처리
- stem==세션 id 파일을 DB rows와 함께 OS 휴지통으로 이동 (S03). 2B 빈 파일도 동일 취급.
- stem 불일치 파일(고아 16/17, T02 인계)은 본 처리 대상 밖. 별도 판단 없이 유지.

## 4. `.dat` 매핑 불일치 방침
- `global.dat → layout.sessionTabs`와 workspace 파일에 해당 세션 키가 없으면 경고 기록 후 DB 처리 계속.
- `.dat` 파일 자체는 수정하지 않음 (1단계 읽기전용 원칙을 V2에서도 `.dat` 직접 편집에는 적용).
- 불일치 내역은 결과 화면에 안내 문구로 표시.

## 5. T13 게이트 적용
- 삭제 흐름은 `docs/v2-safety.md` §2 순서 전제: S01 종료 확인 → 영향범위 표시 → S02 대상별 백업 → S04 2차 확정 → S03 휴지통 이동 → S05 복원 안내.
- 어느 게이트라도 미통과 시 실행 불가.

## 6. cascade 대조 (T02 20종)
| 테이블 | 세션 연계 | 처리 |
|---|---|---|
| session | 본 행 | 보관=`time_archived`, 삭제=마지막 |
| message | `session_id` | cascade 2단계 |
| part | `session_id`·`message_id` | cascade 1단계 |
| todo | `session_id` | cascade 3단계 |
| session_context_epoch/input/message/share | 세션 id 연계 | cascade 3단계 (컬럼 구현 시 재확인) |
| event/event_sequence | `aggregate_id` | cascade 4단계 |
| project/project_directory | 없음 | 제외 |
| account 계열·migration·permission·workspace 등 | 없음 | 제외 |
