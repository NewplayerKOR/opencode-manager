# FEATURES.md — 무엇을 만드는가

> 최종수정일: 2026-09-26 / 상태: v2 개정 / 전제: Windows 우선, 1단계 읽기전용
> 핵심 방향 (2026-09-26 확정): 복잡한 분석보다 **프로젝트명 + 세션명 목록, 활성/비활성 구분**이 메인.

## 1. 문제 정의
- Opencode Desktop은 세션/프로젝트 데이터가 계속 누적됨. 오래된 세션, 보관된 세션, 삭제된 프로젝트 잔재가 남음.
- 실측 (2026-09-23, Windows): `~\.local\share\opencode` 약 315MB 중 `opencode.db` 약 286MB 차지.
- 충돌 유형 (upstream 이슈 기반):
  1. `opencode.global.dat` 손상/비동기화 → 세션 안보임, 새 세션 저장 실패
  2. Windows 경로 정규화 불일치 (`/` vs `\`, `D:\` vs `/`, 대소문자) → 재시작 후 목록 소실
  3. Desktop 상태(`.dat`)와 SQLite(`opencode.db`) 이중 관리 → CLI에는 보이나 GUI에 안보임
  4. `lockfile` 잔류, Tauri 마이그레이션 잔재, `drafts.sqlite`-WAL 비대

## 2. 제품 목표
- GUI로 **현황 파악**을 쉽게: 프로젝트명과 해당 프로젝트의 세션명 목록을 보여줘 사용자가 삭제 유무를 판단할 수 있게 함.
- 활성(Desktop에서 보이고 사용 중) / 비활성(보이지 않고 사용하지 않음)을 구분 표시하는 것이 핵심.
- 1단계는 **읽기전용 뷰어**. 삭제/정리는 보여주되 실행하지 않음 (V2에서 안전장치와 함께 구현).
- 활성 기준 (2026-09-26 확정): `opencode.global.dat`의 프로젝트 목록에 있으면 활성. DB에만 있고 목록에 없으면 비활성.

## 3. 1단계 MVP 기능 (읽기전용, 필수)
### F01. 프로젝트 + 세션 탐색기 (메인)
- 좌측: 프로젝트명 목록을 `활성` / `비활성` 두 그룹으로 분리 표시.
  - 활성 = `opencode.global.dat` 프로젝트 목록에 있음 (Desktop 사이드바에 보이는 것).
  - 비활성 = DB에는 세션이 있으나 `.dat` 목록에 없음 (Desktop에서 안 보이는 옛 프로젝트).
  - `.dat`에만 있고 DB 세션이 없는 항목은 "잔재 상태" 배지 표시.
- 우측: 선택한 프로젝트의 세션명 목록. 세션명 = DB title 우선, 없으면 `id 앞 8자 + 날짜` 대체 표기 (2026-09-26 확정).
- 세션 상세: id, 날짜(생성/수정), 메시지 수, `session_diff` 유무.
- 각 행 체크박스 표시만 제공 (삭제 판단 보조용, 실행 없음).

### F02. 대시보드 (보조)
- 전체 용량, `opencode.db` 크기 + WAL 크기, 세션 수, 프로젝트 수(활성/비활성 각각), `.dat` 개수, `drafts.sqlite` 크기 표시.
- 데이터 위치 목록과 존재 여부 표시.

### F03. 저장소 분석기 (보조)
- `~\.local\share\opencode` 하위 파일별 용량 상위 N건, `storage/session_diff` 개수/용량.
- 프로젝트별 세션 수/메시지 수/최종 활동일 집계표 + 정렬 (어느 프로젝트가 무거운지 판단용).

### F04. 진단 (보조, 읽기전용 규칙)
- 고아 workspace: `opencode.workspace.*.dat` 중 `global.dat` 인덱스에 없는 항목 의심 표시.
- 오래된 매핑(stale): DB 세션 directory와 `.dat` 프로젝트 경로가 정규화 후에도 불일치 시 경고.
- lockfile 잔류, `opencode.db-wal` 과다(예: 50MB 이상 시 주의 — 임계값은 T06에서 확정), `.dat` 0바이트/파싱 실패 의심 표시.
- 모든 진단은 "의심" 수준. 확정 판정, 자동 수정 금지. 문구는 안내형으로 (상세 `DESIGNS.md`).

### F05. 백업 가이드 (실행 없이 안내만)
- 수동 백업 경로/순서 안내 (Desktop 종료 → 폴더 복사). 프로그램이 파일을 만지지 않음.

## 4. 데이터 소스 스펙 (Windows)
| ID | 데이터 | 경로 | 역할 | 읽기 방법 (1단계) | 주의 |
|---|---|---|---|---|---|
| D01 | 세션 DB | `%USERPROFILE%\.local\share\opencode\opencode.db` | project/session/message 진실원천(서버측) | `sqlite3`, `mode=ro` | 실행 중 잠금 가능, WAL에 손대지 말 것 |
| D02 | 세션 diff | `%USERPROFILE%\.local\share\opencode\storage\session_diff\` | 세션별 diff JSON | 파일 목록/크기만 | 내용 파싱은 T02 이후 결정 |
| D03 | 마이그레이션 | `%USERPROFILE%\.local\share\opencode\storage\migration\` | 마이그레이션 잔재 | 목록/크기만 | 삭제 금지 |
| D04 | Desktop 전역 상태 | `%APPDATA%\ai.opencode.desktop\opencode.global.dat` | UI 프로젝트/세션 매핑, 사이드바 원천 | 읽기전용 파싱 시도 (T03) | 손상 가능, 단일 실패점. 쓰기 금지 |
| D05 | Desktop 워크스페이스 | `%APPDATA%\ai.opencode.desktop\opencode.workspace.*.dat` | 워크스페이스별 UI 상태 | 목록/크기, 파싱은 T03 | 고아 발생 가능 |
| D06 | 초안 | `%APPDATA%\ai.opencode.desktop\drafts.sqlite` | 임시/초안 | `mode=ro`, 크기/개수만 | 1.8MB 실측 |
| D07 | 전역 설정 | `%USERPROFILE%\.config\opencode\opencode.jsonc` | 플러그인/서버 설정 | 텍스트 읽기 | 수정 금지(1단계) |
| D08 | 잠금 | `%APPDATA%\ai.opencode.desktop\lockfile` | 실행 잠금 잔재 | 존재 여부/크기만 | 삭제 금지 |

- macOS/Linux 경로(`~/.local/share/opencode`, `~/.config/ai.opencode.desktop` 등)는 설계 시 상수로 분리만 해두고 구현 보류.

## 5. Non-Goal (1단계에서 하지 않는 것)
- 세션/프로젝트/파일의 삭제, 보관, 이동, `.dat` 재빌드, 자동 정리, lockfile 삭제, 프로세스 kill.
- 위 기능이 필요하다는 것은 보고서/진단 문구로만 표현하고, 실행 버튼을 만들지 말 것.
- V2 후보로 `TASKS.md` T07에 분리 기록.

## 6. 수용 기준 (1단계 완료 정의)
- 프로젝트 목록이 활성/비활성으로 구분되어 표시되고, 선택한 프로젝트의 세션명 목록이 보임.
- Desktop 종료 여부와 무관하게 읽기전용 조회가 크래시 없이 동작.
- DB 잠금 시 에러 대신 안내 문구 표시.
- 실데이터 대신 fixture/복사본으로 검증한 기록이 `TASKS.md`에 남음.
