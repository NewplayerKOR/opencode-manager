# TASKS.md — 업무 목록 (반드시 여기서 1개씩 진행)

> 최종수정일: 2026-10-26 / 상태: v5 개정 / 규칙: `AGENTS.md` §4 준수
> 핵심 방향 (2026-09-26 확정): 프로젝트명 + 세션명 목록, 활성(`global.dat` 목록 기준)/비활성 구분이 메인.
> 단계 구분 (2026-10-02 확정, 2026-10-12 확장, 2026-10-19 확장, 2026-10-22 확장, 2026-10-28 확장): T01–T06은 V1 설계(도면, 코드 없음). T07–T11은 V1 구현(도면대로 제작). T12–T16은 V2 설계. T17–T21은 V2 구현. T22는 배포. T23–T29는 V1.1 UI 개선·릴리스. T30은 보안·개인정보 QA 후속 조치.
> 번호는 고정, 착수 순서는 `진행 현황 요약`에 명시.
> 상태 표기: `TODO` (미착수) / `DOING` (진행중) / `DONE` (완료) / `PENDING-V2` (V1 검증 후 착수)
> 착수 시 `DOING` + 담당/착수일 기입, 완료 시 `DONE` + 완료일/산출물/검증 기입. 완료 표시 없이 종료 금지.

## 진행 현황 요약
- T01 DONE (2026-09-23). T02 DONE (2026-09-27). T03 DONE (2026-09-28). T04 DONE (2026-09-29). T05 DONE (2026-09-30). T06 DONE (2026-10-01).
- 착수 순서: T08 → T09 → T10 → T11 (V1 구현) → T12 → T13 → T14 → T15 → T16 (V2 설계) → T17 → T18 → T19 → T20 → T21 (V2 구현) → T22 (배포) → T23 → T24 → T25 → T26 → T27 → T28 → T29 (V1.1 UI 개선·릴리스) → T30 (보안·개인정보 QA 후속). 전건 DONE (2026-10-28).

## T01. 문서 4종 초안 생성
- 상태: `DONE`
- 담당: PM 세션 / 착수일: 2026-09-23 / 완료일: 2026-09-23
- 내용: `AGENTS.md`, `FEATURES.md`, `TASKS.md`, `DESIGNS.md` v1 초안 생성. 전제: Python GUI, Windows 우선, 읽기전용 1단계.
- 산출물: `md/` 폴더의 문서 4종
- 검증: 4개 파일 존재 확인, 상호 참조(§번호) 정합 육안 확인

## T02. DB 스키마 리버스 (읽기전용)
- 상태: `DONE`
- 담당: DEV 세션 / 착수일: 2026-09-27 / 완료일: 2026-09-27
- 내용: `%USERPROFILE%\.local\share\opencode\opencode.db`를 `mode=ro`로 조회. `sqlite_master`에서 테이블/컬럼 목록, 각 테이블 건수, 대표 컬럼(session id/directory/project_id/시각, project id/worktree) 사전화. **`session` 테이블의 title 계열 컬럼 존재 여부를 최우선 확인** (없으면 id+날짜 대체 표기 확정). `session_diff` 파일명과 session id 매칭 가능 여부 판단.
- 산출물: `docs/schema.md` (테이블 20종/컬럼 사전/건수, title 존재 결론, `session_diff` 매칭 1/17 결론, F01 프로젝트+세션 탐색기–F05 백업 가이드 커버 확인)
- 검증: 실DB 읽기전용 직접 조회(`mode=ro`, `timeout=5`) 수치 기록, 쓰기 시도 없음. WAL/`-shm`/lockfile untouched. session 109/project 5/message 2469, title NULL/빈값 0건, session_diff 17개 중 매칭 1건 확인.
- 주의: WAL/`-shm`에 손대지 말 것. Desktop 실행 중 잠금 시 중단하고 안내 문구 기록.

## T03. `.dat` 포맷 조사 (읽기전용)
- 상태: `DONE`
- 담당: DEV 세션 / 착수일: 2026-09-27 / 완료일: 2026-09-28
- 내용: `opencode.global.dat`, `opencode.workspace.*.dat` 포맷 판별 (msgpack 여부 등). **최우선: `global.dat`에서 프로젝트 목록 추출 가능 여부만 결론.** 전체 파싱 불가 시 1단계는 목록/키 수준으로 한정.
- 산출물: `docs/dat-format.md` (JSON 판별, `server.projects.local` 4건 추출 가능 결론, sessionTabs base64 구조, workspace 세션키 46/DB 109 교집합 14, F01 프로젝트+세션 탐색기 인계)
- 검증: Temp 복사본 16개로만 바이트 판독, 원본 수정 없음. stdlib json 파싱, msgpack 설치 없음.

## T04. 읽기전용 조회 모듈 설계
- 상태: `DONE`
- 담당: DEV 세션 / 착수일: 2026-09-28 / 완료일: 2026-09-29
- 내용: Python 조회 계층 설계. `mode=ro`, `timeout`, 잠금 시 안내 예외, 경로 상수 분리(`paths_win.py` 등), 로깅 규칙. `DESIGNS.md` §5 준수.
- 선행: T02, T03
- 산출물: `docs/query-design.md` (4모듈 paths_win/errors/db_reader/dat_reader 분리, 함수 시그니처만, F01 프로젝트+세션 탐색기–F05 백업 가이드 커버행렬 포함). `docs/` 신설 후 `docs/schema.md`, `docs/dat-format.md` 이동.
- 검증: §8 커버행렬로 F01–F05 전건 대조, Non-Goal(삭제 실행) 미포함 확인. 실측 fixture 불필요한 설계서라 코드 실행 검증 없음.

## T05. GUI 목업 (프로젝트|세션 2영역)
- 상태: `DONE`
- 담당: DEV 세션 / 착수일: 2026-09-29 / 완료일: 2026-09-30
- 내용: Tkinter vs PySide 최종 선정 근거 + 목업(스케치/와이어프레임). 좌측 프로젝트(활성/비활성 두 그룹) + 우측 세션명 목록 + 상세 패널 구조. `DESIGNS.md` §1–§4 준수. 쓰기 버튼 없음, 체크박스는 판단 보조용임을 명기.
- 선행: T04
- 산출물: `docs/gui-mockup.md` (PySide 선정 근거+대가 명시, ASCII 와이어프레임 구조 계약, query-design 바인딩표, F01 프로젝트+세션 탐색기 중심 DESIGNS 대조)
- 검증: 실행 버튼류(`[삭제]`/`[정리]`/`[복구]`) 부재 grep 확인, `[새로고침]`/`[복사]`만 존재 확인. 렌더 검증은 PySide 미설치로 구현 단계 이월.

## T06. 진단 규칙 정의
- 상태: `DONE`
- 담당: DEV 세션 / 착수일: 2026-09-30 / 완료일: 2026-10-01
- 내용: F04 진단 규칙 확정. 고아 workspace / 오래된 매핑 / lockfile 잔류 / WAL 과다 임계값 / 0바이트 `.dat` 기준. 모두 "의심" 수준 문구로 정의.
- 선행: T02, T03
- 산출물: `docs/diagnostic-rules.md` (R01–R05 조건/문구/색상, WAL 50MB 확정, 0B+파싱실패 포함, F04 진단 인계)
- 검증: 실측값(DB 294MB/WAL 4MB/lockfile 존재/workspace 15개) 대입 육안 검토. R04·R05 미발동, R02 video-editor 1건만 의심, 오탐 없음.

## T07. V1 구현 블록 개요 (전환, 작업 없음)
- 상태: `DONE` (개요 전환, 2026-10-02)
- 내용: 기존 "V2 삭제/정리 설계" 항목을 V1 구현 블록 개요로 전환. V2 설계 내용은 T12로 이동. T01–T06이 설계(도면)에 해당하므로, T08–T11에서 도면대로 V1 읽기전용 앱을 구현한다. 구현은 작업지시서 방식으로 진행: `docs/` 5종이 명세서 역할을 하므로 지시 한 줄로 착수 가능.
- 산출물: 본 항목 (개요)

## T08. 조회 모듈 구현
- 상태: `DONE`
- 담당: DEV 세션 / 착수일: 2026-10-03 / 완료일: 2026-10-03
- 내용: `docs/query-design.md`의 4모듈(paths_win/errors/db_reader/dat_reader)을 Python 코드로 구현. `mode=ro`, `timeout=5`, 잠금 시 안내 예외, `DESIGNS.md` §5 준수. 실DB 직접 접근 금지, fixture/복사본 DB로만 테스트.
- 선행: T02, T03, T04
- 산출물: `src/paths_win.py`, `src/errors.py`, `src/db_reader.py`, `src/dat_reader.py` (평탄 4파일+`__init__`), `tests/test_readers.py` (F01 프로젝트+세션 탐색기–F05 백업 가이드 함수 커버)
- 검증: synthetic fixture로 `pytest tests` 6 passed. 실DB·원본 `.dat` 접근 없음, `src/` 쓰기 패턴 grep 무검출. 본 머신 `Temp\pytest-of-<user>` ACL 문제로 pytest 내장 tmp_path 대신 자체 tmp fixture 사용.

## T09. GUI 구현 (프로젝트|세션 2영역)
- 상태: `DONE`
- 담당: DEV 세션 / 착수일: 2026-10-03 / 완료일: 2026-10-04
- 내용: `docs/gui-mockup.md`대로 PySide 앱 구현. 좌측 프로젝트(활성/비활성 두 그룹) + 우측 세션명 목록 + 상세 패널. `[새로고침]`/`[복사]`만 허용, 실행 버튼류(`[삭제]`/`[정리]`/`[복구]`) 금지. 진단 표시는 T10 인계 전이므로 플레이스홀더(T06 확정 후 반영)로 둔다.
- 선행: T08, T05
- 산출물: `src/main.py` (PySide6 6.11.2, 진입점. F01 프로젝트+세션 탐색기 2영역+상세+상태바, 진단 플레이스홀더), `tests/test_gui.py` (offscreen 스모크)
- 검증: `pytest tests` 8 passed (synthetic fixture만, 실DB 접근 없음). `main.py` 실행 버튼류 grep 무검출(QPushButton 2개만), CJK 문체 grep 무검출. 렌더 실측은 offscreen 스모크로 대체.

## T10. 진단 규칙 구현
- 상태: `DONE`
- 담당: DEV 세션 / 착수일: 2026-10-04 / 완료일: 2026-10-05
- 내용: `docs/diagnostic-rules.md` R01–R05를 앱에 반영. 모두 "의심" 수준 배지/문구로 표시, 확정 판정·자동 수정 금지.
- 선행: T09, T06
- 산출물: `src/diagnostics.py` (R01–R05 순수함수, F04 진단), `src/main.py` diag 실표시 연결, `tests/test_diagnostics.py`
- 검증: `pytest tests` 12 passed. T06 재현 fixture로 R02·R03만 발동(R01/R04/R05 미발동) 일치 확인. CJK 문체 무검출, 확정 표현·빨강 미사용.

## T11. V1 통합 검증 + 사용법 정리
- 상태: `DONE`
- 담당: DEV 세션 / 착수일: 2026-10-05 / 완료일: 2026-10-06
- 내용: 복사본 DB로 V1 앱 전체 동작 확인. `FEATURES.md` §6 수용 기준 전건 대조. 사용법 1쪽 정리.
- 선행: T10
- 산출물: `docs/verification.md` (수용 4기준 대조표, 기존 테스트로 갈음), `README.md` (소개+사용법 1쪽, 과장 없음)
- 검증: `pytest tests` 12 passed 재확인, CJK·과장 표현 grep 무검출. 실데이터 검증 없음.

## T12. V2 요구사항 정의 (구 T07 이전)
- 상태: `DONE`
- 담당: DEV 세션 / 착수일: 2026-10-06 / 완료일: 2026-10-07
- 내용: 삭제/보관 요구사항 정리. 범위 (2026-09-26 확정): **세션 단위 + 프로젝트 단위(통째) 모두 포함**. 제외 확정: lockfile 삭제, 프로세스 kill, 자동 정리 — 데이터 손실 위험으로 V2에서도 제외 유지.
- 산출물: `docs/v2-requirements.md` (V2-R01–R05 포함 목록, 제외 3종 확정, 보관=숨김+복원·선택 삭제 정의)
- 검증: 포함/제외 × `FEATURES.md` §5 Non-Goal 대조표 (§4) 확인. CJK 문체 무검출. 설계 없음.

## T13. V2 안전장치 설계
- 상태: `DONE`
- 담당: DEV 세션 / 착수일: 2026-10-07 / 완료일: 2026-10-08
- 내용: Desktop 종료 확인, 사전 백업, 휴지통 이동 원칙(영구 삭제 금지), 확정 클릭 2단계, 실수 복구 절차를 설계. 설계만 수행.
- 선행: T12
- 산출물: `docs/v2-safety.md` (S01–S05 게이트, 실행 흐름, V2-R01–R04 대조표)
- 검증: 게이트 대조표(§3)로 삭제 실행 불가 구조 확인. CJK 문체 무검출. 코드 없음.

## T14. V2 세션 단위 삭제/보관 설계
- 상태: `DONE`
- 담당: DEV 세션 / 착수일: 2026-10-08 / 완료일: 2026-10-09
- 내용: 세션 단위 삭제/보관 설계. DB cascade(세션-메시지-diff) 범위, `session_diff` 파일 처리, `.dat` 매핑 불일치 시 처리 방침. T13 안전장치 전제, 설계만 수행.
- 선행: T13
- 산출물: `docs/v2-session-design.md` (보관=`time_archived` 활용, 5단계 cascade, diff 함께 휴지통, `.dat` 불일치 경고 후 계속)
- 검증: cascade 집합 × T02 20종 대조표(§6)로 고아 row 발생 불가 확인. CJK 문체 무검출. 코드 없음.

## T15. V2 프로젝트 단위 정리 설계
- 상태: `DONE`
- 담당: DEV 세션 / 착수일: 2026-10-09 / 완료일: 2026-10-10
- 내용: 프로젝트 통째 정리 설계. DB project + 소속 세션 일괄 처리, `workspace.*.dat` 처리 방침(제거 vs 재빌드). T13 안전장치 전제, 설계만 수행.
- 선행: T13
- 산출물: `docs/v2-project-design.md` (T14 cascade 재사용 일괄 순서, workspace 파일째 휴지통, 활성 3단계 확인, `global` 제외)
- 검증: 활성 오삭제 방지 3조건(§6) 명시 대조. CJK 문체 무검출. 코드 없음.

## T16. V2 백업/복원 설계
- 상태: `DONE`
- 담당: DEV 세션 / 착수일: 2026-10-10 / 완료일: 2026-10-11
- 내용: 사전 백업 포맷, 복원 절차, 복원 검증 방법 설계. 설계만 수행.
- 선행: T13
- 산출물: `docs/v2-backup-design.md` (폴더 그대로 포맷, 역순 복원 절차, SHA-256+id 집합 검증)
- 검증: 범위별 복원 가능 대조표(§4)로 삭제 전 상태 복원 확인. CJK 문체 무검출. 코드 없음.

## T17. V2 백업/복원 구현
- 상태: `DONE`
- 담당: DEV 세션 / 착수일: 2026-10-11 / 완료일: 2026-10-13
- 내용: `docs/v2-backup-design.md`를 코드로 구현. 폴더 그대로 백업 포맷, 역순 복원 절차, SHA-256+id 집합 검증. 삭제 실행보다 복원 경로를 먼저 만든다. 실DB·원본 `.dat` 접근 금지, fixture/복사본으로만 테스트.
- 선행: T16
- 산출물: `src/v2_backup.py` (backup/restore/verify 3함수, stdlib만), `tests/test_v2_backup.py`
- 검증: `pytest tests` 14 passed (synthetic 왕복·변조 탐지·보관 플래그 보존). 실경로 참조 grep 무검출, CJK 무검출.

## T18. V2 안전 게이트 구현
- 상태: `DONE`
- 담당: DEV 세션 / 착수일: 2026-10-13 / 완료일: 2026-10-14
- 내용: `docs/v2-safety.md` S01–S05를 코드로 구현. Desktop 종료 확인, 사전 백업 강제, 휴지통 이동 원칙(영구 삭제 금지), 확정 클릭 2단계. 게이트 불충족 시 삭제 실행 불가 구조. 실DB·원본 `.dat` 접근 금지.
- 선행: T17, T13
- 산출물: `src/v2_safety.py` (순수 판정 함수+send2trash 래퍼, lockfile 기준 차단), `tests/test_v2_safety.py`
- 검증: `pytest tests` 18 passed. 게이트별 차단 확인, Non-Goal 실행 코드 grep 무검출, CJK 무검출.

## T19. V2 세션 단위 보관/삭제 구현
- 상태: `DONE`
- 담당: DEV 세션 / 착수일: 2026-10-14 / 완료일: 2026-10-15
- 내용: `docs/v2-session-design.md`를 코드로 구현. `time_archived` 활용 보관, 5단계 cascade 삭제, `session_diff` 함께 휴지통 이동, `.dat` 매핑 불일치 시 경고 후 계속. T18 게이트 전제. 파괴적 테스트는 복사본 DB에서만.
- 선행: T18, T14
- 산출물: `src/v2_session.py` (archive/delete+unarchive, mover 주입, 게이트 플래그 필수), `tests/test_v2_session.py`
- 검증: `pytest tests` 21 passed. 고아 row 0건·보관 복원·`.dat` 경고후계속 확인. 실DB 접근·`.dat` 수정·실경로 참조 없음.

## T20. V2 프로젝트 단위 정리 구현
- 상태: `DONE`
- 담당: DEV 세션 / 착수일: 2026-10-15 / 완료일: 2026-10-16
- 내용: `docs/v2-project-design.md`를 코드로 구현. T19 cascade 재사용 일괄 순서, workspace 파일째 휴지통 이동, 활성 3단계 확인, `global` 프로젝트 제외. T18 게이트 전제. 파괴적 테스트는 복사본 DB에서만.
- 선행: T18, T15
- 산출물: `src/v2_project.py` (archive/cleanup, T19 호출 재사용, 단일 gates_ok 계약), `tests/test_v2_project.py`
- 검증: `pytest tests` 24 passed. 3조건(`global` 거부·활성 표시·게이트) 동작 확인. `.dat` 재빌드·실경로 참조 없음.

## T21. V2 통합 검증
- 상태: `DONE`
- 담당: DEV 세션 / 착수일: 2026-10-16 / 완료일: 2026-10-17
- 내용: 복사본 DB로 삭제→복원 왕복 검증. 제외 3종(lockfile 삭제·프로세스 kill·자동 정리)의 코드·버튼 부재 grep 확인. `FEATURES.md` Non-Goal과 대조. GUI에 V2 동작 연결 시 실행 버튼류가 게이트 뒤에만 존재하는지 확인.
- 선행: T19, T20
- 산출물: `tests/test_v2_roundtrip.py` (세션+프로젝트 왕복), `docs/verification.md` §3 추기. `src/v2_backup.py` project 계열 최소 확장 (T17 산출물 수정, 회귀 없음)
- 검증: `pytest tests` 26 passed. 왕복 SHA-256+id 일치, 제외 3종 실행 코드 무검출, GUI V2 버튼 미연결 확인. 실데이터 검증 없음.

## T22. 배포 패키징 + 릴리스 정리
- 상태: `DONE`
- 담당: DEV 세션 / 착수일: 2026-10-17 / 완료일: 2026-10-18
- 내용: 실행 파일 패키징, `README.md`에 V2 사용법·주의사항(읽기전용이 아님, 사전 백업 필수, 제외 3종) 반영. 과장 표현 금지.
- 선행: T21
- 산출물: `dist/OpencodeManager.exe` 47MB (PyInstaller 단일 exe, git 대상 밖), `src/main.py` V2 연결 (게이트 뒤 보관/삭제/정리 3버튼), `README.md` V2절, `.gitignore`, `tests/test_gui.py` V2 게이트 테스트
- 검증: `pytest tests` 27 passed, exe offscreen 10초 기동 확인, CJK·과장 무검출, 제외 3종 버튼 부재.

## T23. GUI 창·영역 자유 조절
- 상태: `DONE` (재작업 완료, exe 재빌드 보류)
- 담당: DEV 세션 / 착수일: 2026-10-19 / 완료일: 2026-10-20 / 재착수: 2026-10-21 / 재완료: 2026-10-21
- 반려 사유: 최소 크기 근처에서 핸들 드래그가 단락 점프 (collapsible 기본 동작 + 진단 라벨 장문 최소너비가 원인 확정)
- 내용: 창 크기 자유 조절이 체감되도록 수정. 최소 창 크기 800×500 지정, 최소 크기에서 가로·세로 모두 자유 조절 가능. 원인 확정(`setFixedSize` 계열은 없으므로 테이블 열 너비 고정·스플리터 신축 배분 미비가 유력) 후 조치. 좌(프로젝트 트리)·우(세션 테이블) 스플리터 신축 배분, 테이블 열 너비 자동 신축(상호작용 조절 유지). 읽기전용·버튼 원칙 유지, 삭제 실행 미포함.
- 산출물: `src/main.py` 수정 (최소 800×500, 우측 우선 신축, 마지막 열 신축, collapsible 해제, 양쪽 접기 버튼+크기 복원, 진단 라벨 줄바꿈), `tests/test_gui.py` 매끄러움·접기 왕복 테스트, `dist/OpencodeManager.exe` 재빌드 (1차)
- 검증: `pytest tests` 30 passed, exe offscreen 10초 기동 확인 (1차). 실DB 접근 없음, CJK 문체 무검출.
- 재배포 (2026-10-21): v1.1.0 표기 (`src/__init__.py`, 타이틀, README), exe 재빌드 47,213,276B + offscreen 10초 기동 확인. 잔류 프로세스 종료 후 빌드.

## T24. V1.1 UI 문구 개선
- 상태: `DONE`
- 담당: DEV 세션 / 착수일: 2026-10-22 / 완료일: 2026-10-22
- 내용: `프로젝트 정리` 버튼을 `프로젝트 삭제`로 개명 (동작=삭제 경로, 보관 버튼 없음). F04 진단 표시를 항목별 줄바꿈+색 구분 리치텍스트로 개선 (문구 원문 불변). 읽기전용·버튼·게이트 원칙 유지.
- 선행: T22, T23
- 산출물: `src/main.py` 수정 (버튼·대화상자·진단 `<li>` 표시) + `tests/test_gui.py` 갱신 + `README.md` 문구 통일
- 검증: `pytest tests` 30 passed. `프로젝트 정리` 잔류 0건, CJK 문체 무검출. 실DB 접근 없음.
- 재배포 (2026-10-22): exe 재빌드 47,259,182B (T24분 포함) + offscreen 10초 기동 확인. 잔류 프로세스 종료 후 빌드.

## T25. V1.1 사용성 개선 묶음
- 상태: `DONE`
- 담당: DEV 세션 / 착수일: 2026-10-23 / 완료일: 2026-10-23
- 내용: 메시지 열 전건 표시. R01/R02 쉬운 문구 교체 (ID·판정 불변). V2 행·툴팁 `조건` wording 통일 + `Opencode Desktop` 명시. 창 geometry 기억, 라이트/다크 테마 (기본 라이트), 글자 11~18px 조절. exe 재빌드 포함.
- 선행: T24
- 산출물: `src/main.py` (QSettings 기억·테마·글자, 상태바 토글), `src/diagnostics.py`·`src/errors.py`·`src/v2_safety.py` 문구, `tests/test_gui.py` (설정 주입·기억·테마·전건), `README.md` v1.2.0, `dist/` 재빌드
- 검증: `pytest tests` 33 passed. CJK·과장 무검출, 실DB 접근 없음. exe 47,261,823B offscreen 10초 기동.

## T26. V1.1 폰트·테마 대비 개선
- 상태: `DONE`
- 담당: DEV 세션 / 착수일: 2026-10-24 / 완료일: 2026-10-24
- 내용: 시스템 폰트 선택 (`QFontComboBox`, QSettings 저장). Zinc 팔레트로 라이트·다크 전면 교체 (명도 3단계 입체감, 진단·상단바·버튼 즉시 수정 3건 포함). R01/R02 판정·문구 불변. exe 재빌드 포함.
- 선행: T25
- 산출물: `src/main.py` (폰트 콤보·Zinc QSS·테마별 진단색·`settings` 주입), `tests/test_gui.py` (폰트·팔레트 테스트), `README.md` v1.3.0, `dist/` 재빌드
- 검증: `pytest tests` 35 passed. CJK·과장 무검출, 실DB 접근 없음. exe 47,263,058B offscreen 10초 기동.

## T27. V1.1 설정탭·다국어·진단상세
- 상태: `DONE`
- 담당: DEV 세션 / 착수일: 2026-10-25 / 완료일: 2026-10-25
- 내용: [메인][설정] 2탭, 폰트·크기·테마·언어(KO/EN/JA/ZH) 설정탭 통합. R01–R05 포함 주요 라벨 전건 번역 (ID·색·판정 불변). 진단 항목 대상 최대 3건 병기. exe 재빌드 포함.
- §4-3 예외 기록: JA/ZH UI 번역문(`src/i18n.py`)과 README 언어명 표기는 의도적 타언어 표시이므로 CJK grep 대상 밖 (PM 승인 2026-10-25). 그 외 무검출.
- 선행: T26
- 산출물: `src/i18n.py` (90키×4언어), `src/main.py` (설정탭·retranslate·진단 대상 병기·`settings` 주입), `src/diagnostics.py` (n·targets), `tests/test_gui.py` (언어·설정탭 테스트), `README.md` v1.4.0, `dist/` 재빌드
- 검증: `pytest tests` 37 passed. 과장 무검출, 실DB 접근 없음. exe 47,275,659B offscreen 10초 기동.

## T28. V1.1 진단 정밀화·상태바 정리
- 상태: `DONE`
- 담당: DEV 세션 / 착수일: 2026-10-26 / 완료일: 2026-10-26
- 내용: R01은 세션 키 포함 고아만 발동 (빈 껍데기 3건 원본 직접 대조済, 미발동). R02 행동 안내 추가 (용량 차지·V2 삭제/재열기). 상태바 A-·A+·폰트·테마 4종 제거 (설정탭 유지). exe 재빌드 포함.
- 선행: T27
- 산출물: `src/diagnostics.py` (ws_sessions·targets) + `src/main.py` (키 스캔·상태바 정리) + `src/i18n.py` (R02 4언어) + `tests/` (R01 정밀화) + `README.md` v1.5.0 + `dist/` 재빌드
- 검증: `pytest tests` 38 passed. CJK(§4-3 예외 유지)·과장 무검출, 실DB 접근 없음. exe 47,275,460B offscreen 10초 기동.

## T29. 릴리스 정리·배포 인도
- 상태: `DONE`
- 담당: DEV 세션 / 착수일: 2026-10-27 / 완료일: 2026-10-27
- 내용: README에 `실제 폴더는 지우지 않음` 명시 + 최신화 (v1.6.0). `.gitignore`에 DB·DAT·로그·환경 파일 추가. 릴리스 에셋 방식 확정 (repo 트리에는 exe 미포함, Releases에서 단일 파일 배포). 커밋·push는 사용자 담당.
- 선행: T28
- 산출물: `README.md` (실제폴더 고지·다운로드 안내·v1.6.0) + `.gitignore` (11항목) + `dist/OpencodeManager.exe` 47,276,367B
- 검증: `pytest tests` 38 passed. CJK(§4-3 예외 유지)·과장 무검출, 실DB 접근 없음. offscreen 10초 기동. `git status` 민감 파일 없음.

## T30. 보안 QA 후속 + 백업 보관함 UI
- 상태: `DONE`
- 담당: DEV 세션 / 착수일: 2026-10-28 / 완료일: 2026-10-28
- 내용: QA 지적 해소. (1) 게이트 스터빙 해소 (`_gates_ok` S03–S05 실체크 연결, 복원경로 manifest 실체크 포함). (2) 보관 경로 백업 면제 문서화 (원본 유지이므로 S02 면제, T13 대조표와 정합). (3) 백업 평문 잔재 대응 (보존 안내 + 보관함 삭제 UI). (4) 문서·주석 실경로 마스킹. (5) 경로 탐색 가드 (`sid` 허용목록 + `diff_dir` 이탈 검사). (6) 의존성 버전 고정 (`requirements.txt`). (7) 릴리스 SHA-256·SmartScreen 안내. (8) 백업 보관함 UI (목록+복원+휴지통 삭제, 2단계 확인). 읽기전용·버튼·게이트 원칙 유지, 실DB·원본 `.dat` 접근 금지.
- 선행: T29 (QA 보고서 2026-10-28)
- 산출물: `src/main.py` (백업탭·게이트 실체크·경로가드 적용) + `src/v2_session.py` (`safe_diff_path`) + `src/v2_backup.py` (`verify_files`·project 계열) + `src/v2_project.py` (가드 적용) + `tests/` (왕복·가드·보관함) + `docs/` 마스킹분 + `requirements.txt` + `README.md` v1.7.0 + `dist/` 재빌드
- 검증: `pytest tests` 40 passed. 스터빙·실경로 grep 무검출, CJK(§4-3 예외 유지)·과장 무검출, 실DB 접근 없음. exe 47,281,504B offscreen 10초 기동. SHA-256: 4ae1d3de134d6d20413aefb4b10a5ceac5746424c4134a112c88257dedd699e2.
- 재검토 (2026-10-28): 잔재 3건 보완 — 보관 경로 잠금 확인 추가 (`src/main.py` `_run_archive_session`), 주석·기록 사용자명 마스킹 (`tests/test_readers.py`, `md/TASKS.md` T08), `requirements.txt` 버전 표기 정정 (v1.7.0). 재검증 `pytest tests` 40 passed, 비밀키·사용자명 grep 무검출, 게이트 스터빙 무검출. 배포 가능.
