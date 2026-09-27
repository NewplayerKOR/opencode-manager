"""T20 project cleanup on synthetic copy DB only."""
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src import v2_project  # noqa: E402
from src.errors import ReadError  # noqa: E402

P1 = "proj_tomodachi"
P2 = "proj_other"


@pytest.fixture()
def fx():
    tmp = Path(tempfile.mkdtemp(prefix="om-v2p-"))
    db = tmp / "w.db"
    con = sqlite3.connect(str(db))
    con.execute("CREATE TABLE project (id TEXT PRIMARY KEY, worktree TEXT)")
    con.execute("CREATE TABLE project_directory (project_id TEXT, directory TEXT)")
    con.execute("CREATE TABLE session (id TEXT PRIMARY KEY, project_id TEXT, title TEXT, time_archived INTEGER)")
    con.execute("CREATE TABLE message (id TEXT PRIMARY KEY, session_id TEXT, data TEXT)")
    con.execute("CREATE TABLE part (id TEXT PRIMARY KEY, message_id TEXT, session_id TEXT, data TEXT)")
    con.execute("INSERT INTO project VALUES (?, 'C:/P1'), (?, 'C:/P2'), ('global', 'C:/G')", (P1, P2))
    con.execute("INSERT INTO project_directory VALUES (?, 'C:/P1')", (P1,))
    con.execute(
        "INSERT INTO session VALUES ('ses_a111', ?, 'A', NULL), ('ses_a222', ?, 'B', NULL), ('ses_b999', ?, 'K', NULL)",
        (P1, P1, P2),
    )
    con.execute("INSERT INTO message VALUES ('m1', 'ses_a111', '{}'), ('m9', 'ses_b999', '{}')")
    con.execute("INSERT INTO part VALUES ('p1', 'm1', 'ses_a111', '{}')")
    con.commit()
    diff = tmp / "diff"
    diff.mkdir()
    (diff / "ses_a111.json").write_text("{}", encoding="utf-8")
    ws = tmp / "opencode.workspace.q.dat"
    ws.write_text("{}", encoding="utf-8")
    yield {"dir": tmp, "con": con, "diff": diff, "ws": ws}
    con.close()
    shutil.rmtree(tmp, ignore_errors=True)


def test_archive_batch(fx):
    out = v2_project.archive_project(fx["con"], P1, True)
    assert out == {"archived": 2}
    n = fx["con"].execute("SELECT COUNT(*) FROM session WHERE project_id=? AND time_archived IS NOT NULL", (P1,)).fetchone()[0]
    assert n == 2
    v2_project.unarchive_project(fx["con"], P1)
    n = fx["con"].execute("SELECT COUNT(*) FROM session WHERE project_id=? AND time_archived IS NULL", (P1,)).fetchone()[0]
    assert n == 2
    with pytest.raises(ReadError):
        v2_project.archive_project(fx["con"], P1, False)


def test_cleanup_batch(fx):
    con = fx["con"]
    moved = []
    out = v2_project.cleanup_project(
        con, P1, fx["diff"], [fx["ws"]], {"ses_a111", "s2"}, False, True, mover=moved.append,
    )
    assert out["project_deleted"] == 1
    assert len(out["members"]) == 2
    assert out["workspace_moved"] == [fx["ws"].name]
    assert con.execute("SELECT COUNT(*) FROM project WHERE id=?", (P1,)).fetchone()[0] == 0
    assert con.execute("SELECT COUNT(*) FROM project_directory WHERE project_id=?", (P1,)).fetchone()[0] == 0
    assert con.execute("SELECT COUNT(*) FROM session WHERE project_id=?", (P1,)).fetchone()[0] == 0
    assert con.execute("SELECT COUNT(*) FROM part").fetchone()[0] == 0
    assert con.execute("SELECT COUNT(*) FROM session WHERE project_id=?", (P2,)).fetchone()[0] == 1
    assert con.execute("SELECT COUNT(*) FROM message WHERE session_id='ses_b999'").fetchone()[0] == 1
    assert fx["diff"] / "ses_a111.json" in moved


def test_global_refused_and_active_flag(fx):
    with pytest.raises(ReadError):
        v2_project.cleanup_project(fx["con"], "global", None, [], set(), False, True, mover=lambda p: None)
    out = v2_project.cleanup_project(
        fx["con"], P2, None, [], {"s9"}, True, True, mover=lambda p: None,
    )
    assert out["active_extra_confirmed"] is True
    assert out["project_deleted"] == 1
