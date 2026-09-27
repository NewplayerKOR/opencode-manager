"""V2 safety gates S01-S05 (T18). Pure checks; no unlock, no auto-clean."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class Gate:
    id: str
    passed: bool
    message: str


def check_s01(lock_exists: bool) -> Gate:
    """Opencode Desktop off check. Lockfile present (running or leftover) blocks."""
    if lock_exists:
        return Gate(
            "S01", False,
            "잠금 표시판이 있습니다. Opencode Desktop 종료 여부를 직접 확인하세요.",
        )
    return Gate("S01", True, "Opencode Desktop 종료 확인됨.")


def check_s02(backup_ok: bool) -> Gate:
    """Backup (v2_backup.verify result) must pass before execution."""
    if not backup_ok:
        return Gate("S02", False, "사전 백업 검증 전에는 실행할 수 없습니다.")
    return Gate("S02", True, "사전 백업 검증됨.")


def check_s03(trash_available: bool) -> Gate:
    """OS trash route must exist. Permanent delete is forbidden."""
    if not trash_available:
        return Gate("S03", False, "휴지통 경로를 사용할 수 없습니다.")
    return Gate("S03", True, "OS 휴지통 경유 가능.")


def check_s04(stage1_done: bool, stage2_done: bool) -> Gate:
    """Two-step confirmation: select, then impact review, then confirm."""
    if not (stage1_done and stage2_done):
        return Gate("S04", False, "2단계 확인이 끝나지 않았습니다.")
    return Gate("S04", True, "2단계 확인됨.")


def check_s05(restore_ready: bool) -> Gate:
    """Restore path (trash + backup) must be announced and ready."""
    if not restore_ready:
        return Gate("S05", False, "복원 경로가 준비되지 않았습니다.")
    return Gate("S05", True, "복원 경로 준비됨.")


def check_all(
    lock_exists: bool,
    backup_ok: bool,
    trash_available: bool,
    stage1_done: bool,
    stage2_done: bool,
    restore_ready: bool,
) -> list[Gate]:
    return [
        check_s01(lock_exists),
        check_s02(backup_ok),
        check_s03(trash_available),
        check_s04(stage1_done, stage2_done),
        check_s05(restore_ready),
    ]


def all_passed(gates: list[Gate]) -> bool:
    return all(g.passed for g in gates)


def move_to_trash(paths: list[Path]) -> None:
    """Thin wrapper over send2trash. Called only after all gates pass."""
    from send2trash import send2trash

    for p in paths:
        send2trash(str(p))
