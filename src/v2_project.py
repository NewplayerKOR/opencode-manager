"""V2 project cleanup (T20). Reuses T19 per-member logic.

Contract: `gates_ok` must already include the active-project extra
confirmation when `is_active` is true. `global` project id is refused.
`global.dat` is never modified.
"""
from __future__ import annotations

import sqlite3
from collections.abc import Callable
from pathlib import Path

from . import v2_safety, v2_session

GLOBAL_ID = "global"


def _need_gates(gates_ok: bool, action: str) -> None:
    if not gates_ok:
        from .errors import ReadError

        raise ReadError(f"게이트 미통과 시 {action}할 수 없습니다.")


def member_sessions(con: sqlite3.Connection, project_id: str) -> list[str]:
    return [
        r[0]
        for r in con.execute(
            "SELECT id FROM session WHERE project_id=?", (project_id,)
        ).fetchall()
    ]


def archive_project(con: sqlite3.Connection, project_id: str, gates_ok: bool) -> dict:
    """Archive every member session. Project rows are kept."""
    _need_gates(gates_ok, "보관")
    done = [v2_session.archive(con, sid, True) for sid in member_sessions(con, project_id)]
    return {"archived": len(done)}


def unarchive_project(con: sqlite3.Connection, project_id: str) -> None:
    for sid in member_sessions(con, project_id):
        v2_session.unarchive(con, sid)


def cleanup_project(
    con: sqlite3.Connection,
    project_id: str,
    diff_dir: Path | None,
    workspace_files: list[Path],
    dat_keys: set[str],
    is_active: bool,
    gates_ok: bool,
    mover: Callable[[Path], None] | None = None,
) -> dict:
    """Remove a project batch: members (T19) then directory/project rows.

    Workspace files move to trash whole. Caller folds the active extra
    confirmation into `gates_ok` (see module contract above).
    """
    if project_id == GLOBAL_ID:
        from .errors import ReadError

        raise ReadError("global 프로젝트는 정리 대상이 아닙니다.")
    _need_gates(gates_ok, "정리")
    details: list[dict] = []
    for sid in member_sessions(con, project_id):
        diff = (
            v2_session.safe_diff_path(diff_dir, sid)
            if diff_dir is not None
            else None
        )
        details.append(v2_session.delete(con, sid, diff, dat_keys, True, mover=mover))
    con.execute("DELETE FROM project_directory WHERE project_id=?", (project_id,))
    cur = con.execute("DELETE FROM project WHERE id=?", (project_id,))
    con.commit()
    move = mover or (lambda p: v2_safety.move_to_trash([p]))
    moved_ws: list[str] = []
    for f in workspace_files:
        if f.is_file():
            move(f)
            moved_ws.append(f.name)
    return {
        "project_deleted": cur.rowcount,
        "members": details,
        "workspace_moved": moved_ws,
        "active_extra_confirmed": bool(is_active),
    }
