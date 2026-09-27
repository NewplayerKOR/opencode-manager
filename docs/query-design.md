# query-design.md — 읽기전용 조회 계층 설계 (코드 아님)

> 최종수정일: 2026-09-28 / 상태: v1 초안 / 전제: Python, Windows 우선, 1단계 읽기전용
> 선행: `docs/schema.md` (T02), `docs/dat-format.md` (T03) / 준수: `DESIGNS.md` §5

## 1. 모듈 구조 (4모듈 분리)
```
paths_win.py   # 경로 상수 (D01–D08), 환경변수 경유
errors.py      # 안내 예외 (잠금/파싱 실패 → 문구 변환)
db_reader.py   # SQLite 읽기전용 (D01, D02, D03, D06)
dat_reader.py  # `.dat` JSON 읽기전용 (D04, D05)
```
- 결합 로직(활성/비활성 판정, 대시보드 집계)은 호출 측(향후 GUI/T05)이 본 설계의 함수만 조합. 쓰기 함수 없음.
- OS 분기: `paths_win.py`에 Windows 실측 경로, macOS/Linux는 주석 상수로만 분리.

## 2. `paths_win.py` — 경로 상수
- `%USERPROFILE%`, `%APPDATA%` 경유, `pathlib` 사용. 하드코딩된 `C:\Users\...` 금지.
- 상수: `OPENCODE_DB`, `SESSION_DIFF_DIR`, `MIGRATION_PATH`, `GLOBAL_DAT`, `WORKSPACE_GLOB`, `DRAFTS_SQLITE`, `GLOBAL_CONFIG`, `LOCKFILE`.
- 함수 시그니처:
  - `resolve_all() -> dict[str, Path]` — 존재 여부 포함 목록 반환 (F02 데이터 위치 목록용).
  - `file_size(p: Path) -> int | None` — 부재 시 `None`, 예외를 던지지 않음.

## 3. `errors.py` — 안내 예외
- `ReadError(Exception)` 기반 클래스, `msg: str`는 화면 안내문구만 보관. 스택트레이스 노출 금지.
  - `DbLocked(msg="DB가 잠겨 있습니다. Desktop 종료 후 새로고침 하세요.")`
  - `DatMissing(path)`, `DatParseFailed(path)` — 패널별 배지용.
  - `NotFound(kind, key)` — 빈 상태 문구용 ("조회 결과 0건 (DB 잠금 여부 확인)").
- 규칙: `sqlite3.OperationalError: locked/busy` → `DbLocked`, `json.JSONDecodeError`/`FileNotFoundError` → `DatParseFailed`/`DatMissing`으로 변환 후 로그 + 화면 안내.

## 4. `db_reader.py` — SQLite 읽기전용
- 접속 원칙: `sqlite3.connect(f"file:{p}?mode=ro", uri=True, timeout=5)` 강제. WAL/`-shm` 접근 없음.
- 반환 타입 (표시 원본 보존, 정규화값 별도):
  - `Project(worktree: str, name: str | None, session_count: int, status: str)` — `status`는 호출 측이 `dat_reader`와 대조해 결정.
  - `Session(id: str, title: str, directory: str, directory_norm: str, time_created: int, time_updated: int)`
  - `SessionDetail(Session + message_count: int, has_diff: bool, time_archived: int | None)`
- 함수 시그니처:
  - `connect_ro(db: Path) -> sqlite3.Connection`
  - `list_db_projects(con) -> list[Project]` — `project` + `session GROUP BY directory` 집계 (T02 §4).
  - `list_sessions(con, directory: str) -> list[Session]` — title 우선, 빈 title은 `id 앞 8자 + 날짜` + `(자동 표기)` fallback.
  - `session_detail(con, session_id: str) -> SessionDetail` — `message COUNT`, `session_diff` stem 존재 여부.
  - `counts(con) -> dict` — session/project/message 건수 (F02용).
  - `storage_stats(diff_dir: Path) -> dict` — 개수/합계, 파일별 Top N (F03용).
  - `project_activity(con) -> list` — 프로젝트별 세션 수/메시지 수/최종 활동일 (F03 집계표용).

## 5. `dat_reader.py` — `.dat` JSON 읽기전용
- 원칙: 원본 직접 파싱 금지, 호출 측이 복사본 또는 읽기 핸들을 전달. 전체 파싱 없이 키 수준만 사용 (T03 §4).
- 함수 시그니처:
  - `load_global(dat: Path) -> dict` — JSON 파싱, 실패 시 `DatParseFailed`.
  - `active_worktrees(g: dict) -> list[str]` — `server.projects.local[].worktree` 원본 `\` 그대로 반환.
  - `recently_closed(g: dict) -> list[str]` — 비활성 후보 보조.
  - `session_tabs(g: dict) -> list[tuple[str, str]]` — `(worktree, ses_id)` 복원, base64 패딩 보정 포함.
  - `workspace_inventory(glob: str) -> list[tuple[str, int]]` — `(파일명, 크기)` 목록만, 내용 해석 없음 (1단계).

## 6. 결합 규칙 (호출 측)
1. 활성 = `directory_norm`이 `active_worktrees` 정규화 집합에 있음. DB에만 있으면 비활성. `.dat`에만 있으면 "잔재 상태" 배지 (F01).
2. `global.dat` 부재/파싱 실패 시 좌측은 DB 프로젝트로 fallback + "전역 상태 조회 실패" 배지, 크래시 금지.
3. 경로 정규화는 `DESIGNS.md` §3 초안 그대로 (`/`→`\`, 중복 제거, 끝 제거, 대소문자 무시 비교, UNC/`\\wsl$` 별도 배지). 확정은 T06.
4. 새로고침은 수동 호출만. 자동 폴링 금지.

## 7. 로깅/UX 매핑
- 조회 실패(잠금, 파싱 실패)는 로그 1줄 + 해당 패널 안내문구. 성공 시 마지막 새로고침 시각 갱신.
- 용량은 MB 소수 1자리 + bytes 병기, 건수는 천 단위 구분 (F02). 진단 문구는 "의심" 수준까지만 (F04).

## 8. F01–F05 커버 대조
| 기능 | 사용 함수 | 원천 |
|---|---|---|
| F01 프로젝트+세션 탐색기 (메인) | `list_db_projects` + `active_worktrees` + `list_sessions` + `session_detail` | D01, D02, D04 |
| F02 대시보드 (보조) | `resolve_all` + `file_size` + `counts` + `workspace_inventory` | D01–D08 |
| F03 저장소 분석기 (보조) | `storage_stats` + `project_activity` | D01, D02, D03 |
| F04 진단 (보조) | `session_tabs` + `workspace_inventory` + `recently_closed` + lockfile/WAL 크기 | D04, D05, D08 |
| F05 백업 가이드 (안내만) | `resolve_all` 경로/순서 문구 | D01–D08 |

## 9. Non-Goal / T05 인계
- 삭제/보관/이동/`.dat` 재빌드/자동 정리/lockfile 삭제/프로세스 kill 함수 없음. 체크박스는 판단 보조용 상태로만 취급.
- T05는 본 설계의 반환 타입을 그대로 표에 바인딩. 쓰기 버튼 추가 시 설계 위반으로 검수 탈락.
