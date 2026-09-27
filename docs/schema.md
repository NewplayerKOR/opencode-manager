# schema.md — T02 DB 스키마 리버스 결과 (읽기전용)

> 조회일: 2026-09-27 / 대상: `%USERPROFILE%\.local\share\opencode\opencode.db` / 방식: 실DB 읽기전용 직접 조회 (`mode=ro`, `timeout=5`), 쓰기 시도 없음, WAL/`-shm`/lockfile 손대지 않음
> 스냅샷 주의: Desktop 실행 중(OpenCode 7 프로세스, lockfile 존재)으로 수치가 유동적임. message 2455→2469, opencode.db 290,070,528→291,024,896B로 조사 중 증가 확인.

## 1. 조회 방법
- `sqlite3.connect(f"file:{p}?mode=ro", uri=True, timeout=5)` (DESIGNS.md §5 준수)
- `sqlite_master` 테이블 목록 + `PRAGMA table_info()` + `COUNT(*)` + 샘플 `SELECT ... LIMIT`
- 파일 크기: `Get-Item` 읽기만. 실DB ro만 사용 (Temp 복사본 없음, 사용자 선택)

## 2. 파일 크기 (읽기만)
| 파일 | 크기 |
|---|---|
| `opencode.db` | 291,024,896B (조사 시작 시 290,070,528B) |
| `opencode.db-wal` | 4,185,952B |
| `opencode.db-shm` | 32,768B |
| `storage/session_diff/` | 17개, 합계 13,539B (13,507B 1개 + 2B 16개) |
| `storage/migration` | 1B 파일 (디렉토리 아님) |

## 3. 테이블 목록 + 건수 (20개, 2026-09-27 스냅샷)
| 테이블 | 건수 | 비고 |
|---|---|---|
| `account` | 0 | - |
| `account_state` | 0 | - |
| `control_account` | 0 | - |
| `credential` | 0 | - |
| `data_migration` | 0 | - |
| `event` | 38170 | `aggregate_id/seq/type/data` |
| `event_sequence` | 109 | session 수와 동일 |
| `message` | 2469 | F01 메시지 수 원천 |
| `migration` | 38 | - |
| `part` | 12063 | `message_id/session_id` 포함 |
| `permission` | 0 | - |
| `project` | 5 | F01 좌측 원천 |
| `project_directory` | 4 | `global` 제외 4건 |
| `session` | 109 | F01 우측 원천 |
| `session_context_epoch` | 0 | - |
| `session_input` | 0 | - |
| `session_message` | 0 | - |
| `session_share` | 0 | - |
| `todo` | 52 | `session_id/content/status` |
| `workspace` | 0 | 0건 (Desktop `.dat`와 별개) |

## 4. 대표 컬럼 사전
### session (109건, PK `id TEXT`)
```
id TEXT PK, project_id TEXT, workspace_id TEXT, parent_id TEXT, slug TEXT,
directory TEXT, path TEXT, title TEXT, version TEXT, share_url TEXT,
summary_additions/dels/files INTEGER, summary_diffs TEXT, metadata TEXT,
cost REAL, tokens_* INTEGER, revert/permission/agent/model TEXT,
time_created INTEGER, time_updated INTEGER, time_compacting INTEGER, time_archived INTEGER
```
- 시간 범위(ms): `time_created` 1786893606671 (2026-08-17) ~ 1790435230571 (2026-09-27)
- `time_archived IS NOT NULL` 3건
- `directory` 예: `C:/Work/win/video-editor` (경로 비식별화. DB 내 `/` 구분자, 화면 표기는 `\` 원본 유지 필요 — DESIGNS.md §3)
- `directory`별: video-editor 48, daytrack 44, multi-image-gen 9, sliding-block-puzzle 6, Opencode-manager 2
- `project_id`별: `9baa...` 48, `bb8b...` 44, `dd96...` 9, `d77d...` 6, `global` 2

### project (5건, PK `id TEXT`)
```
id TEXT PK, worktree TEXT, vcs TEXT, name TEXT, icon_url/url_override/color TEXT,
time_created/time_updated/time_initialized INTEGER, sandboxes TEXT, commands TEXT
```
- `global` → `C:/Work/win/Opencode-manager` (경로 비식별화), `name` NULL
- `d77d...` → sliding-block-puzzle, `dd96...` → multi-image-gen, `9baa...` → video-editor (`name='video-editor(delete)'`), `bb8b...` → daytrack

### project_directory (4건, PK `project_id, directory`)
```
project_id TEXT, directory TEXT, type TEXT, strategy TEXT, time_created INTEGER
```
- `global` 행 없음. 4개 프로젝트만 매핑 존재.

### message (2469건, PK `id TEXT`)
```
id TEXT PK, session_id TEXT, time_created INTEGER, time_updated INTEGER, data TEXT
```
- 세션당 메시지 Top5: 445, 155, 135, 134, 112건 (F01 상세/ F03 집계용 `session_id` GROUP BY 가능)

### part (12063건)
```
id TEXT PK, message_id TEXT, session_id TEXT, time_created/time_updated INTEGER, data TEXT
```

### workspace (0건)
```
id TEXT PK, type TEXT, name TEXT, branch TEXT, directory TEXT, extra TEXT, project_id TEXT, time_used INTEGER
```

### todo (52건)
```
session_id TEXT PK, content TEXT, status TEXT, priority TEXT, position INTEGER, time_created/time_updated INTEGER
```

## 5. title 결론 (최우선 확인 항목)
- `session.title TEXT NOT NULL` 존재 확인.
- `WHERE title IS NULL` 0건, `WHERE length(title)=0` 0건 (109건 전건 title 보유, 예: `00-PM-Control Tower`, `DEV-01`, `DEV-02`).
- 결론: F01 프로젝트+세션 탐색기 세션명은 DB title 우선 사용 가능. 단 DESIGNS.md 대체 표기(`id 앞 8자 + 날짜` + `(자동 표기)`)는 빈 title/구버전 대비 fallback으로 유지.

## 6. session_diff 매칭 결론
- 파일명 패턴: `ses_<26자>.json` (예: `ses_0123456789abcdefghijklmnop.json`, id 비식별화)
- 17개 중 stem==`session.id` 매칭 1건 (13,507B, 메시지 112건 세션)
- 나머지 16개는 2B (빈 JSON 의심) + 현 DB id와 불일치 → 고아/구버전 잔재 의심.
- 결론: 파일명 stem으로 `session.id`와 직접 매칭 가능. F01 세션 상세 `session_diff` 유무는 파일 존재 여부로 표시 가능. 단 매칭률 1/17이므로 F04 진단(오래된 매핑/잔재) 후보로 T06에 인계.

## 7. F01–F05 커버 확인 (T04 인계용)
- F01 메인: `project` 5 + `project_directory` 4 + `session` 109 + `title` + `directory/project_id` 조인 가능. `global` 프로젝트 세션 2건 별도 처리 필요.
- F02 대시보드: DB/WAL 크기 + 세션/프로젝트 건수 확보. `.dat`/`drafts.sqlite`는 T03에서 보완.
- F03 저장소 분석기: `message`/`part` 세션별 집계 + `session_diff` 개수/용량 확보.
- F04 진단: `time_archived` 3건, `session_diff` 고아 16/17, `project_directory` 없는 `global` 프로젝트 확인. WAL 4MB (50MB 임계값 이하).
- F05 백업 가이드: 경로/크기 확보. 실행 없음.

## 8. 제약/주의
- 잠금 발생 시 강제 해제/kill/lockfile 삭제 금지, 안내 문구만 (AGENTS.md §6).
- 경로 비교 시 원본 보존 + 정규화값 별도 (DESIGNS.md §3). DB 내 `/` vs 화면 `\` 주의.
- 본 수치는 스냅샷이며 live DB 특성상 재조회 시 변동 가능.
