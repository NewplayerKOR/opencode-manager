"""Guidance-only errors. `msg` is screen text; never expose tracebacks."""
from __future__ import annotations


class ReadError(Exception):
    def __init__(self, msg: str) -> None:
        super().__init__(msg)
        self.msg = msg


class DbLocked(ReadError):
    def __init__(
        self, msg: str = "DB가 잠겨 있습니다. Opencode Desktop 종료 후 새로고침 하세요."
    ) -> None:
        super().__init__(msg)


class DatMissing(ReadError):
    def __init__(self, path: str) -> None:
        super().__init__(f"상태 파일을 찾을 수 없습니다: {path}")


class DatParseFailed(ReadError):
    def __init__(self, path: str) -> None:
        super().__init__(f"상태 파일 읽기 실패 의심: {path}. 파일을 건드리지 마세요.")


class NotFound(ReadError):
    def __init__(self, kind: str, key: str) -> None:
        super().__init__(f"이 {kind}의 조회 결과 0건 (DB 잠금 여부 확인): {key}")
