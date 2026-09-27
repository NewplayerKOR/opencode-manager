# dat-format.md — T03 `.dat` 포맷 조사 결과 (읽기전용)

> 조회일: 2026-09-27 / 대상 복사본: `Temp\opencode\T03\` (global 1 + workspace 15, 원본 수정 없음) / 원본: `%APPDATA%\ai.opencode.desktop\opencode.*.dat`
> 스냅샷 주의: Desktop 실행 중이라 수치가 유동적임 (global.dat 142,099→142,293B).

## 1. 포맷 판별 결론
- msgpack 아님. 전부 UTF-8 JSON 텍스트 (`{\n\t"..."` 시작).
- 외부 패키지 불필요 (stdlib `json` 파싱 가능, msgpack 설치 미수행).
- 값은 이중 인코딩된 JSON 문자열이 많음 (top-level value가 `str`인 JSON).

## 2. `opencode.global.dat` (142,293B, 최우선)
- top-level 키 9개: `command.catalog.v1, notification, server, settings-v2.models.providers, layout, model, review-panel-v2, permission, open.app`.
- 프로젝트 목록 추출 가능: `server` 내부 JSON의 `projects.local[]`.
  - 활성 4건: `C:\Work\Opencode-manager`, `...\Kotlin\daytrack`, `...\Cs\multi-image-gen`, `...\typescript\sliding-block-puzzle` (각 `expanded:true`, 경로 비식별화).
  - `lastProject.local`: Opencode-manager.
  - `recentlyClosed.local`: `C:\Users\<user>\Desktop`, `...\win\video-editor`, `...\win\example1`, `...\Documents\Default Project`.
- 결론: F01 프로젝트+세션 탐색기 활성 기준 (`global.dat` 목록에 있으면 활성) 판정 가능. DB 5 프로젝트 중 video-editor는 `recentlyClosed`에만 있어 비활성 판정 근거 확보 (T02 `md/schema.md:4`와 정합).
- `layout.sessionTabs` 16건, 키 형식 `local\0<base64 worktree>/<ses_id>` (예: `local\0Qzpc.../ses_fa3b...`). base64 디코딩 시 worktree 복원 가능 (예시값 비식별화).
- `ses_` 언급 555건 (notification 97KB 포함). 세션 매핑 보조 후보이나 1단계는 프로젝트 목록만 사용.

## 3. `opencode.workspace.*.dat` (15개, 77~1,941B)
- 전부 JSON. 파일명 2종: 구형 `C--Dev-Works.*`/`C--Users-par.*` 9개 + 신형 `QzpcRGV2XFdv.*` 6개 (base64 prefix + suffix).
- top-level 키 종류: `workspace:project, workspace:vcs, workspace:model-selection, workspace:followup, workspace:icon, workspace:terminal, workspace:comments` + `session:<ses_id>:comments/file-view`.
- `workspace:project` 값은 아이콘 메타만 (`{"value":{"icon":{"color":"..."}}}`), 경로 매핑 없음. 경로는 global.dat에서만 추출.
- 세션 키 46개 vs DB session 109건, 교집합 14건. ws_only 예: `ses_005c...` (example1 등 구 프로젝트), db_only 예: `ses_f36845...`. F04 진단(고아 workspace/오래된 매핑) 후보.
- 샘플 (값 마스킹): `workspace:vcs {"value":{"branch":"main",...}}`, `workspace:model-selection {"session":{"ses_...":{"agent":"build","model":{...}}}}`.

## 4. 위험도
- 낮음 (읽기): JSON 텍스트라 바이너리 파싱 위험 없음. 단 live 갱신 중 복사 타이밍에 따라 부분 쓰기 가능 → 복사 후 `json.loads` 실패 시 안내 예외 필요.
- 중간 (스키마): 버전 키 없음. `server`/`layout` 구조 변경 시 파서 깨짐 → 키 부재 시 크래시 금지, 패널별 안내 문구 (DESIGNS.md §4).
- 1단계 한정: 전체 파싱 불필요. `server.projects.local` + `layout.sessionTabs` 키 수준만 사용. `.dat` 직접 해석 추가 시도는 T03 범위를 초과하므로 금지.

## 5. T04 인계 (F01 읽기전용 조회 모듈 설계용)
- 활성 목록: `global.dat → server → projects.local[].worktree` (원본 `\` 보존).
- 비활성 판정: DB session.directory는 있으나 global 목록에 없음 (video-editor가 실증).
- 워크스페이스 파일명-경로 직접 매칭은 확정 불가 (구/신형 혼재). 필요 시 `layout.sessionTabs` base64 경유.
- 파싱 실패 가정: global.dat 부재/깨짐 시 F01 좌측은 DB 프로젝트로 fallback + "전역 상태 조회 실패" 배지.
