"""V2 session archive/delete (T19). Caller must pass T18 gate approval.

Writes confined to the supplied connection and diff path. `.dat` files
are never modified; mismatches are reported as warnings only.
"""
from __future__ import annotations

import re
import sqlite3
import time
from collections.abc import Callable
from pathlib import Path

from . import v2_safety

_SID = re.compile(r"^ses_[A-Za-z0-9]+$")


def safe_diff_path(diff_dir: Path, session_id: str) -> Path | None:
    """Return diff_dir/<id>.json only for well-formed ids inside diff_dir.

    Returns None for malformed ids or escape attempts (T30 QA5).
    """
    if not _SID.match(session_id):
        return None
    try:
        base = diff_dir.resolve()
        cand = (base / f"{session_id}.json").resolve()
    except OSError:
        return None
    if base not in cand.parents:
        return None
    return cand

# T14 cascade order.
CASCADE = (
    ("part", "session_id"),
    ("message", "session_id"),
    ("todo", "session_id"),
    ("session_context_epoch", "session_id"),
    ("session_input", "session_id"),
    ("session_message", "session_id"),
    ("session_share", "session_id"),
    ("event", "aggregate_id"),
    ("event_sequence", "session_id"),
)


def _tables(con: sqlite3.Connection) -> set[str]:
    return {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def _columns(con: sqlite3.Connection, table: str) -> set[str]:
    return {r[1] for r in con.execute(f"PRAGMA table_info({table})")}


def archive(con: sqlite3.Connection, session_id: str, gates_ok: bool) -> int:
    """Record time_archived. Returns the recorded value. Restore = NULL.

    No S02 backup: archiving only hides rows, originals stay intact and
    unarchive() restores them (T13 S01-S03 exemption, T30 QA2).
    """
    if not gates_ok:
        from .errors import ReadError

        raise ReadError("게이트 미통과 시 보관할 수 없습니다.")
    now = int(time.time() * 1000)
    cur = con.execute("UPDATE session SET time_archived=? WHERE id=?", (now, session_id))
    if cur.rowcount == 0:
        from .errors import NotFound

        raise NotFound("세션", session_id)
    con.commit()
    return now


def unarchive(con: sqlite3.Connection, session_id: str) -> None:
    con.execute("UPDATE session SET time_archived=NULL WHERE id=?", (session_id,))
    con.commit()


def delete(
    con: sqlite3.Connection,
    session_id: str,
    diff_file: Path | None,
    dat_keys: set[str],
    gates_ok: bool,
    mover: Callable[[Path], None] | None = None,
) -> dict:
    """Cascade delete one session. Returns counts and warnings.

    `mover` moves the diff file to trash; defaults to v2_safety wrapper.
    `.dat` mismatch (id absent from `dat_keys`) warns and continues.
    """
    if not gates_ok:
        from .errors import ReadError

        raise ReadError("게이트 미통과 시 삭제할 수 없습니다.")
    move = mover or (lambda p: v2_safety.move_to_trash([p]))
    warnings: list[str] = []
    if session_id not in dat_keys:
        warnings.append(f".dat 매핑에 없는 세션, 기록 후 계속: {session_id}")
    if con.execute("SELECT COUNT(*) FROM session WHERE id=?", (session_id,)).fetchone()[0] == 0:
        from .errors import NotFound

        raise NotFound("세션", session_id)
    tables = _tables(con)
    counts: dict[str, int] = {}
    for table, key in CASCADE:
        if table not in tables:
            continue
        cols = _columns(con, table)
        use = key if key in cols else None
        if use is None and table == "event_sequence":
            use = "aggregate_id" if "aggregate_id" in cols else None
        if use is None:
            warnings.append(f"연계 컬럼 없음, 건너뜀: {table}")
            continue
        cur = con.execute(f"DELETE FROM {table} WHERE {use}=?", (session_id,))
        counts[table] = cur.rowcount
    cur = con.execute("DELETE FROM session WHERE id=?", (session_id,))
    counts["session"] = cur.rowcount
    con.commit()
    moved = False
    if diff_file is not None and diff_file.is_file():
        move(diff_file)
        moved = True
    return {"counts": counts, "diff_moved": moved, "warnings": warnings}
