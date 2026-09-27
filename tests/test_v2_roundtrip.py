"""T21 delete->restore roundtrip (session + project) on synthetic copy only."""
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src import v2_backup, v2_project, v2_safety, v2_session  # noqa: E402

P1 = "proj_tomodachi"
P2 = "proj_other"


def _db(path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(str(path))
    con.execute("CREATE TABLE project (id TEXT PRIMARY KEY, worktree TEXT)")
    con.execute("CREATE TABLE project_directory (project_id TEXT, directory TEXT)")
    con.execute("CREATE TABLE session (id TEXT PRIMARY KEY, project_id TEXT, title TEXT, time_archived INTEGER)")
    con.execute("CREATE TABLE message (id TEXT PRIMARY KEY, session_id TEXT, data TEXT)")
    con.execute("CREATE TABLE part (id TEXT PRIMARY KEY, message_id TEXT, session_id TEXT, data TEXT)")
    con.execute("INSERT INTO project VALUES (?, 'C:/P1'), (?, 'C:/P2')", (P1, P2))
    con.execute("INSERT INTO project_directory VALUES (?, 'C:/P1')", (P1,))
    con.execute(
        "INSERT INTO session VALUES ('s1', ?, 'A', NULL), ('s2', ?, 'B', NULL), ('s9', ?, 'K', NULL)",
        (P1, P1, P2),
    )
    con.execute("INSERT INTO message VALUES ('m1', 's1', '{}'), ('m9', 's9', '{}')")
    con.execute("INSERT INTO part VALUES ('p1', 'm1', 's1', '{}')")
    con.commit()
    return con


def _gates(con, dest, sids, pids=()):
    bak_ok = v2_backup.verify(dest, con)
    return v2_safety.all_passed(
        v2_safety.check_all(False, bak_ok, True, True, True, True)
    )


def test_session_roundtrip(tmp_path=None):
    tmp = Path(tempfile.mkdtemp(prefix="om-v2r-s-"))
    try:
        con = _db(tmp / "w.db")
        diff = tmp / "diff"
        diff.mkdir()
        (diff / "s1.json").write_text("{}", encoding="utf-8")
        dest = tmp / "bak"
        v2_backup.backup(con, ["s1"], [diff / "s1.json"], [], {"reason": "t", "confirmed": True}, dest)
        assert _gates(con, dest, ["s1"]) is True
        v2_session.delete(con, "s1", diff / "s1.json", {"s1"}, True, mover=lambda p: None)
        assert v2_backup.verify(dest, con) is False
        out = v2_backup.restore(dest, con)
        assert out["session"] == 1 and v2_backup.verify(dest, con) is True
        assert con.execute("SELECT title FROM session WHERE id='s1'").fetchone()[0] == "A"
        con.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_project_roundtrip(tmp_path=None):
    tmp = Path(tempfile.mkdtemp(prefix="om-v2r-p-"))
    try:
        con = _db(tmp / "w.db")
        diff = tmp / "diff"
        diff.mkdir()
        (diff / "s1.json").write_text("{}", encoding="utf-8")
        (diff / "s2.json").write_text("{}", encoding="utf-8")
        ws = tmp / "opencode.workspace.q.dat"
        ws.write_text("{}", encoding="utf-8")
        dest = tmp / "bak"
        moved: list[Path] = []
        v2_backup.backup(
            con, ["s1", "s2"], [diff / "s1.json", diff / "s2.json"], [ws],
            {"reason": "t", "confirmed": True, "kind": "project"}, dest, project_ids=[P1],
        )
        assert _gates(con, dest, ["s1", "s2"]) is True
        out = v2_project.cleanup_project(
            con, P1, diff, [ws], {"s1", "s2"}, False, True, mover=moved.append,
        )
        assert out["project_deleted"] == 1
        assert v2_backup.verify(dest, con) is False
        # trash restore simulation: files back, then DB restore
        for p in moved:
            (tmp / p.name).write_bytes(b"{}")
        rout = v2_backup.restore(dest, con)
        assert rout["project"] == 1 and rout["session"] == 2
        assert v2_backup.verify(dest, con) is True
        assert con.execute("SELECT COUNT(*) FROM session WHERE project_id=?", (P1,)).fetchone()[0] == 2
        assert con.execute("SELECT COUNT(*) FROM message WHERE session_id='s9'").fetchone()[0] == 1
        con.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
