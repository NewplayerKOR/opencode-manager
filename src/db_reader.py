"""SQLite read-only access. Never writes; WAL/-shm untouched."""
from __future__ import annotations

import datetime as _dt
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from .errors import DbLocked

TIMEOUT = 5


@dataclass
class Project:
    worktree: str
    name: str | None
    session_count: int
    status: str = ""  # filled by caller after dat_reader comparison


@dataclass
class Session:
    id: str
    title: str
    directory: str
    directory_norm: str
    time_created: int
    time_updated: int


@dataclass
class SessionDetail(Session):
    message_count: int = 0
    has_diff: bool = False
    time_archived: int | None = None


def normalize_directory(p: str) -> str:
    """DESIGNS.md draft: slash to backslash, collapse dupes, strip trailing, casefold."""
    s = p.replace("/", "\\")
    while "\\\\" in s:
        s = s.replace("\\\\", "\\")
    s = s.rstrip("\\")
    return s.casefold()


def is_unc_or_wsl(p: str) -> bool:
    s = p.replace("/", "\\")
    return s.startswith("\\\\") or s.casefold().startswith("\\\\wsl$")


def display_title(session_id: str, title: str | None, time_created_ms: int) -> str:
    if title and title.strip():
        return title
    day = _dt.datetime.fromtimestamp(time_created_ms / 1000).strftime("%Y-%m-%d")
    return f"{session_id[:8]} {day} (자동 표기)"


def connect_ro(db: Path) -> sqlite3.Connection:
    try:
        return sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=TIMEOUT)
    except sqlite3.OperationalError as e:
        raise DbLocked() from e


def _locked(err: sqlite3.Error) -> bool:
    return "locked" in str(err).lower() or "busy" in str(err).lower()


def list_db_projects(con: sqlite3.Connection) -> list[Project]:
    try:
        rows = con.execute(
            "SELECT id, worktree, name FROM project"
        ).fetchall()
        cnt = dict(
            con.execute(
                "SELECT directory, COUNT(*) FROM session GROUP BY directory"
            ).fetchall()
        )
    except sqlite3.OperationalError as e:
        raise DbLocked() from e if _locked(e) else e
    out: list[Project] = []
    seen: set[str] = set()
    for _pid, worktree, name in rows:
        norm = normalize_directory(worktree or "")
        n = sum(c for d, c in cnt.items() if normalize_directory(d) == norm)
        out.append(Project(worktree=worktree, name=name, session_count=n))
        seen.add(norm)
    for d, c in cnt.items():
        if normalize_directory(d) not in seen:
            out.append(Project(worktree=d, name=None, session_count=c))
    return out


def list_sessions(con: sqlite3.Connection, directory: str) -> list[Session]:
    norm = normalize_directory(directory)
    try:
        rows = con.execute(
            "SELECT id, title, directory, time_created, time_updated FROM session"
        ).fetchall()
    except sqlite3.OperationalError as e:
        raise DbLocked() from e if _locked(e) else e
    out = []
    for sid, title, d, tc, tu in rows:
        if normalize_directory(d or "") == norm:
            out.append(
                Session(
                    id=sid,
                    title=display_title(sid, title, tc or 0),
                    directory=d,
                    directory_norm=normalize_directory(d or ""),
                    time_created=tc,
                    time_updated=tu,
                )
            )
    return out


def session_detail(
    con: sqlite3.Connection, session_id: str, diff_dir: Path | None = None
) -> SessionDetail:
    try:
        row = con.execute(
            "SELECT id, title, directory, time_created, time_updated,"
            " time_archived FROM session WHERE id=?",
            (session_id,),
        ).fetchone()
        if row is None:
            from .errors import NotFound

            raise NotFound("세션", session_id)
        m = con.execute(
            "SELECT COUNT(*) FROM message WHERE session_id=?", (session_id,)
        ).fetchone()
    except sqlite3.OperationalError as e:
        raise DbLocked() from e if _locked(e) else e
    sid, title, d, tc, tu, ta = row
    has_diff = False
    if diff_dir is not None:
        try:
            has_diff = (diff_dir / f"{sid}.json").exists()
        except OSError:
            has_diff = False
    return SessionDetail(
        id=sid,
        title=display_title(sid, title, tc or 0),
        directory=d,
        directory_norm=normalize_directory(d or ""),
        time_created=tc,
        time_updated=tu,
        message_count=int(m[0]) if m else 0,
        has_diff=has_diff,
        time_archived=ta,
    )


def counts(con: sqlite3.Connection) -> dict:
    out = {}
    for t in ("session", "project", "message"):
        try:
            out[t] = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        except sqlite3.OperationalError as e:
            raise DbLocked() from e if _locked(e) else e
    return out


def storage_stats(diff_dir: Path, top_n: int = 10) -> dict:
    files: list[tuple[str, int]] = []
    total = 0
    try:
        entries = list(diff_dir.iterdir()) if diff_dir.exists() else []
    except OSError:
        entries = []
    for f in entries:
        if f.is_file():
            try:
                n = f.stat().st_size
            except OSError:
                continue
            files.append((f.name, n))
            total += n
    files.sort(key=lambda x: x[1], reverse=True)
    return {"count": len(files), "bytes": total, "top": files[:top_n]}


def project_activity(con: sqlite3.Connection) -> list[dict]:
    try:
        rows = con.execute(
            "SELECT directory, COUNT(*), MAX(time_updated) FROM session"
            " GROUP BY directory ORDER BY COUNT(*) DESC"
        ).fetchall()
    except sqlite3.OperationalError as e:
        raise DbLocked() from e if _locked(e) else e
    out = []
    for d, n, last in rows:
        try:
            mc = con.execute(
                "SELECT COUNT(*) FROM message WHERE session_id IN"
                " (SELECT id FROM session WHERE directory=?)",
                (d,),
            ).fetchone()[0]
        except sqlite3.OperationalError as e:
            raise DbLocked() from e if _locked(e) else e
        out.append(
            {
                "directory": d,
                "session_count": n,
                "message_count": mc,
                "last_activity": last,
            }
        )
    return out
