"""V2 backup/restore (T17). Writes confined to caller-supplied paths only.

Tables follow T14 cascade order. No real-data paths referenced here.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import shutil
import sqlite3
from pathlib import Path

# Delete order (T14 + T15); restore inserts in reverse.
CASCADE = ("part", "message", "todo", "event", "session")
SESSION_TABLES = ("session_context_epoch", "session_input", "session_message", "session_share")
PROJECT_TABLES = ("project_directory", "project")


def _tables(con: sqlite3.Connection) -> list[str]:
    names = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    out = [t for t in CASCADE if t in names]
    out += [t for t in SESSION_TABLES if t in names]
    return out + [t for t in PROJECT_TABLES if t in names]


def _key(table: str) -> str:
    if table == "event":
        return "aggregate_id"
    if table in ("session", "project"):
        return "id"
    if table == "project_directory":
        return "project_id"
    return "session_id"


def _rows(
    con: sqlite3.Connection,
    table: str,
    session_ids: list[str],
    project_ids: list[str],
) -> tuple[list[str], list[tuple]]:
    cols = [r[1] for r in con.execute(f"PRAGMA table_info({table})")]
    key = _key(table)
    ids = project_ids if table in PROJECT_TABLES else session_ids
    if key not in cols or not ids:
        return cols, []
    ph = ",".join("?" for _ in ids)
    rows = con.execute(f"SELECT * FROM {table} WHERE {key} IN ({ph})", ids).fetchall()
    return cols, [tuple(r) for r in rows]


def _sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def backup(
    con: sqlite3.Connection,
    session_ids: list[str],
    diff_files: list[Path],
    dat_files: list[Path],
    meta: dict,
    dest: Path,
    project_ids: list[str] | None = None,
) -> Path:
    """Copy target-only backup under `dest`. Returns manifest path."""
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "session_diff").mkdir(exist_ok=True)
    (dest / "dat").mkdir(exist_ok=True)
    pids = list(project_ids or [])
    payload: dict[str, dict] = {}
    for t in _tables(con):
        cols, rows = _rows(con, t, session_ids, pids)
        payload[t] = {"columns": cols, "rows": [list(r) for r in rows]}
    (dest / "db").mkdir(exist_ok=True)
    db_file = dest / "db" / "rows.json"
    db_file.write_text(json.dumps(payload), encoding="utf-8")
    for src in diff_files:
        if src.is_file():
            shutil.copy2(src, dest / "session_diff" / src.name)
    for src in dat_files:
        if src.is_file():
            shutil.copy2(src, dest / "dat" / src.name)
    manifest = {
        "time": _dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "reason": meta.get("reason", ""),
        "confirmed": bool(meta.get("confirmed", False)),
        "kind": meta.get("kind", "session"),
        "ids": list(session_ids),
        "project_ids": list(project_ids or []),
        "files": {},
    }
    for f in sorted(dest.rglob("*")):
        if f.is_file() and f.name != "manifest.json":
            manifest["files"][str(f.relative_to(dest))] = _sha(f)
    mfile = dest / "manifest.json"
    mfile.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    return mfile


def restore(backup_dir: Path, con: sqlite3.Connection) -> dict:
    """Reinsert in reverse cascade order. Returns counts per table."""
    payload = json.loads((backup_dir / "db" / "rows.json").read_text(encoding="utf-8"))
    out: dict[str, int] = {}
    for t in reversed(_tables(con)):
        if t not in payload:
            continue
        cols = payload[t]["columns"]
        rows = payload[t]["rows"]
        if not rows:
            out[t] = 0
            continue
        ph = ",".join("?" for _ in cols)
        con.executemany(f"INSERT INTO {t} ({','.join(cols)}) VALUES ({ph})", rows)
        out[t] = len(rows)
    con.commit()
    return out


def verify_files(backup_dir: Path) -> bool:
    """True when backup files match manifest checksums (no DB needed)."""
    try:
        manifest = json.loads((backup_dir / "manifest.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    for rel, sha in manifest["files"].items():
        f = backup_dir / rel
        if not f.is_file() or _sha(f) != sha:
            return False
    return True


def verify(backup_dir: Path, con: sqlite3.Connection) -> bool:
    """True when checksums and id sets match the backup."""
    if not verify_files(backup_dir):
        return False
    manifest = json.loads((backup_dir / "manifest.json").read_text(encoding="utf-8"))
    want = set(manifest["ids"])
    if want:
        cols = [r[1] for r in con.execute("PRAGMA table_info(session)")]
        if "id" in cols:
            ph = ",".join("?" for _ in want)
            have = {r[0] for r in con.execute(f"SELECT id FROM session WHERE id IN ({ph})", list(want))}
            if have != want:
                return False
    pwant = set(manifest.get("project_ids", []))
    if pwant:
        names = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if "project" in names:
            ph = ",".join("?" for _ in pwant)
            have = {r[0] for r in con.execute(f"SELECT id FROM project WHERE id IN ({ph})", list(pwant))}
            if have != pwant:
                return False
    return True
