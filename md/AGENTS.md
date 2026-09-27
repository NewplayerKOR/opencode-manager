# AGENTS.md — 세션 진입점 (가장 먼저 읽을 것)

> 최종수정일: 2026-10-02 / 상태: v3 개정 / 대상: Windows 우선, 읽기전용 1단계

## 1. 이 프로젝트는 무엇인가
- Opencode Desktop 관리 프로그램. Opencode Desktop은 유용하지만 개발 단계라 불편이 많음.
- 핵심 문제: 오래된 세션 / 보관된 세션 / 프로젝트 잔재 등 데이터가 계속 쌓여 무거워지고, 충돌이 발생함.
- 목표: GUI 형태로 현황을 파악하고 관리할 수 있게 함.
- 실측 근거 (2026-09-23, Windows): `~\.local\share\opencode` 전체 약 315MB, 그중 `opencode.db` 약 286MB.

## 2. 필독 순서 (모든 세션 공통)
1. `AGENTS.md` (본 파일) — 규칙과 진행 방식
2. `FEATURES.md` — 무엇을 만드는가
3. `TASKS.md` — 무엇을 해야 하는가 (업무 목록, 여기서 1개 선택)
4. `DESIGNS.md` — 어떻게 생겨야/동작해야 하는가

위 순서를 건너뛰고 작업하지 말 것.

## 3. PM 규칙 (최우선)
- PM 세션은 **프로젝트 관리, 방향성, 추천만 진행. 코드 작성 금지.**
- 코드 작성, 파일 생성/편집이 필요하면 구현용 별도 세션에 위임하고, PM은 `TASKS.md`로 지시/검수만 함.
- PM도 본 문서 4종(기획 문서, 규칙 문서)의 작성/수정은 허용됨. 단, 구현 코드(`*.py` 등)는 금지.

## 4. 세션 워크플로우 (필수)
1. `TASKS.md`를 읽고 미완료(`TODO`) 항목 중 1개를 선택.
2. 착수 전 해당 항목의 상태를 `TODO` → `DOING`으로 수정하고, 담당(세션명)/착수일을 기입.
3. 작업 수행. 불명확한 점은 추측하지 말고 `FEATURES.md` / `DESIGNS.md`와 대조, 그래도 모르면 중단하고 PM에게 질문.
4. 완료 후 `TASKS.md`에 결과를 반영: `DONE` 표시, 완료일, 산출물(파일 경로/커밋), 검증 방법 기입.
5. **완료 표시 없이 종료 금지.** 미완이면 `TODO`/`DOING` 그대로 두고 사유를 남길 것.

## 4-2. DEV 규칙 (작업 후 TASKS.md 갱신 의무)
- DEV는 작업 완료 후 반드시 `TASKS.md` 해당 항목을 갱신할 것: `상태`(TODO/DOING/DONE), 완료일, 산출물(파일 경로), 검증 방법을 빠짐없이 기입.
- 미완료 시 상태를 되돌리고(DOING → TODO) 사유를 남길 것. `DONE` 허위 표기 금지.
- `TASKS.md` 갱신 없이 작업 종료 금지.
- 문서 내 기능 번호(F01–F05 등)를 참조할 때는 번호가 바뀔 수 있으므로 **이름을 함께 병기**할 것 (예: F04 진단).

## 4-3. 문체 점검 규칙 (전 세션 공통)
- 산출물·문서·코드 주석 작성 후 완료 처리 전에, 한글·영어 외 문자(중국어·일본어·한자 혼용 등)와 문체·문법 오류를 점검할 것.
- 점검 대상: `md/`·`docs/` 문서, 코드 주석·docstring, 사용자에게 보이는 UI 문구.
- 허용 예외: 기술 고유명사(`msgpack`, `WAL`, `SQLite` 등), 파일 경로·코드·식별자, 인용된 원문.
- 점검 방법: 완료 전 해당 파일 전체를 육안으로 1회 통독 + 한자·가나 혼입 여부 grep 확인. 위반 발견 시 완료 처리 금지, 수정 후 진행.
- **위반 발견 시 즉시 수정하고, 사용자에게는 문제없는 문체·문법의 최종본만 보여줄 것.** 오류가 있던 경위 설명은 생략하고 수정된 결과로 보고.
- 이 규칙 위반은 `DONE` 허위 표기에 준해 취급.

## 5. 기술 전제 (2026-09-23 결정)
- GUI: **Python + Tkinter/PySide** (가벼운 Windows 관리툴 지향)
- OS: **Windows 우선**. macOS/Linux는 설계 시 경로만 염두, 구현은 후순위.
- 1단계: **읽기전용 뷰어 우선**. 삭제/보관/자동정리는 V2로 연기, 1단계에서 구현 금지.

## 6. 안전 수칙 (1단계 핵심, 위반 금지)
- `opencode.db`, `opencode.global.dat`, `opencode.workspace.*.dat`, `drafts.sqlite`에 대해 **쓰기/삭제/이동 금지**.
- SQLite 조회는 반드시 읽기전용 URI 사용: `file:...?mode=ro`. WAL(`-wal`, `-shm`)에 손대지 말 것.
- Opencode Desktop 실행 중 DB 잠금(Locked) 발생 가능 → 강제 해제, 프로세스 kill, lockfile 삭제 금지. 사용자에게 안내 문구만 제공.
- 경로 다룰 때 Windows 원본(`C:\...`, `\` 구분자, 대소문자)을 보존하고, 비교용 정규화값은 별도 필드로 병기 (상세는 `DESIGNS.md`).
- 검증은 fixture/복사본 DB로만. 실데이터 실측이 필요하면 읽기전용 조회 + 결과만 기록.

## 7. 데이터 위치 빠른 참조 (Windows)
| 데이터 | 경로 | 비고 |
|---|---|---|
| 세션 DB | `%USERPROFILE%\.local\share\opencode\opencode.db` | 286MB 실측, WAL 별도 |
| 세션 diff/마이그레이션 | `%USERPROFILE%\.local\share\opencode\storage\` | `session_diff/`, `migration/` |
| Desktop 전역 상태 | `%APPDATA%\ai.opencode.desktop\opencode.global.dat` | 139KB 실측, 프로젝트/세션 매핑 |
| Desktop 워크스페이스 상태 | `%APPDATA%\ai.opencode.desktop\opencode.workspace.*.dat` | 14개 실측 |
| 임시/초안 | `%APPDATA%\ai.opencode.desktop\drafts.sqlite` | 1.8MB 실측 |
| 전역 설정 | `%USERPROFILE%\.config\opencode\opencode.jsonc` | 플러그인 등 |
| 잠금 | `%APPDATA%\ai.opencode.desktop\lockfile` | 잔류 시 안내만, 삭제 금지(1단계) |

상세 스펙은 `FEATURES.md` §4를 볼 것.

## 8. 다음 세션 할 일
- `TASKS.md`에서 `T08`부터 순차 착수. 착수 전 본 파일 §4 워크플로우를 다시 확인할 것.
