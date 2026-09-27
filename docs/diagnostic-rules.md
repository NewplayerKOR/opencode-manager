# diagnostic-rules.md — F04 진단 규칙표 (읽기전용, 코드 아님)

> 최종수정일: 2026-09-30 / 상태: v1 초안 / 전제: Windows 우선, 1단계 읽기전용
> 선행: `docs/schema.md` (T02), `docs/dat-format.md` (T03) / 준수: `DESIGNS.md` §2·§4, `FEATURES.md` F04 진단

## 1. 공통 원칙
- 전부 "의심" 수준. 확정 판정·자동 수정 금지. 문구는 안내형.
- 색상: 주황(주의)까지만. 빨강 사용 금지 (V2 예약).
- 비교 전 정규화는 `DESIGNS.md` §3 초안 (`/`→`\`, 중복 제거, 끝 제거, 대소문자 무시, UNC/`\\wsl$` 별도 배지).

## 2. 규칙표
| ID | 조건 | 문구 (안내형) | 색상 |
|---|---|---|---|
| R01 고아 workspace 의심 | `opencode.workspace.*.dat` 중 `global.dat → layout.sessionTabs` 인덱스에 없는 파일 | "전역 목록에 없는 워크스페이스 파일 의심. Desktop 종료 후 수동 백업을 권장합니다." | 주황 |
| R02 오래된 매핑 의심 | DB 세션 `directory`가 정규화 후에도 `.dat` 프로젝트 경로 집합에 없음 | "정규화 후에도 경로 불일치 의심. 대소문자·구분자를 확인하세요." | 주황 |
| R03 lockfile 안내 | `lockfile` 존재 | "Desktop 실행 중이거나 잔류 파일일 수 있습니다. 삭제하지 말고 종료 여부를 확인하세요." | 회색 (정보) |
| R04 WAL 과다 주의 | `opencode.db-wal` 50MB 이상 (임계값 확정) | "WAL이 50MB 이상으로 주의 수준. Desktop 종료 후 재확인하세요." | 주황 |
| R05 `.dat` 이상 의심 | `.dat` 0바이트 또는 JSON 파싱 실패 | "상태 파일 읽기 실패 의심. 파일을 건드리지 말고 백업 가이드를 참조하세요." | 주황 |

## 3. 실측값 오탐 검토 (2026-09-30 스냅샷)
- DB 294MB / WAL 4MB → R04 미발동 (50MB 대비 여유, 오탐 없음).
- lockfile 존재 → R03 정보 표시만 (Desktop 실행 중 정상 가능, 주의 아님).
- workspace 15개: 구형 9개 중 일부 R01 후보이나 "의심" 한정으로 오탐 아님.
- video-editor (DB 48세션, global 목록 외): R02 의심 1건으로 정상 표출. 나머지 4개 프로젝트는 일치.
- `.dat` 0B 없음, JSON 파싱 성공 → R05 미발동.
- session_diff 16/17 불일치는 F01 표시용으로만 사용, 본 규칙 미포함 (T02 인계 유지).

## 4. T05 인계 (표시 위치)
- R01–R05는 별도 탭 없이 상세 패널 내 배지/문구로 축소 (`docs/gui-mockup.md` §2 하단 상세 영역).
- `query-design.md` 함수: `session_tabs`+`workspace_inventory`(R01), 정규화 대조(R02), `resolve_all`+`file_size`(R03–R05).
