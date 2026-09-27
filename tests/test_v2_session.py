"""T19 session archive/delete on synthetic copy DB only."""
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src import v2_session  # noqa: E402
from src.errors import NotFound, ReadError  # noqa: E402

DEL = "ses_del00001"
KEEP = "ses_keep0002"


@pytest.fixture()
def fx():
    tmp = Path(tempfile.mkdtemp(prefix="om-v2s-"))
    db = tmp / "w.db"
    con = sqlite3.connect(str(db))
    con.execute("CREATE TABLE session (id TEXT PRIMARY KEY, title TEXT, time_archived INTEGER)")
    con.execute("CREATE TABLE message (id TEXT PRIMARY KEY, session_id TEXT, data TEXT)")
    con.execute("CREATE TABLE part (id TEXT PRIMARY KEY, message_id TEXT, session_id TEXT, data TEXT)")
    con.execute("CREATE TABLE todo (session_id TEXT PRIMARY KEY, content TEXT)")
    con.execute("CREATE TABLE event (id TEXT PRIMARY KEY, aggregate_id TEXT, data TEXT)")
    con.execute("INSERT INTO session VALUES (?, 'Old', NULL), (?, 'Live', NULL)", (DEL, KEEP))
    con.execute("INSERT INTO message VALUES ('m1', ?, '{}'), ('m2', ?, '{}')", (DEL, KEEP))
    con.execute("INSERT INTO part VALUES ('p1', 'm1', ?, '{}')", (DEL,))
    con.execute("INSERT INTO todo VALUES (?, 't')", (DEL,))
    con.execute("INSERT INTO event VALUES ('e1', ?, '{}')", (DEL,))
    con.commit()
    diff = tmp / f"{DEL}.json"
    diff.write_text("{}", encoding="utf-8")
    yield {"dir": tmp, "con": con, "diff": diff}
    con.close()
    shutil.rmtree(tmp, ignore_errors=True)


def test_archive_and_restore(fx):
    con = fx["con"]
    now = v2_session.archive(con, DEL, True)
    assert now > 0
    assert con.execute("SELECT time_archived FROM session WHERE id=?", (DEL,)).fetchone()[0] == now
    v2_session.unarchive(con, DEL)
    assert con.execute("SELECT time_archived FROM session WHERE id=?", (DEL,)).fetchone()[0] is None
    with pytest.raises(ReadError):
        v2_session.archive(con, DEL, False)
    with pytest.raises(NotFound):
        v2_session.archive(con, "ses_missing", True)


def test_delete_cascade(fx):
    con = fx["con"]
    moved = []
    out = v2_session.delete(con, DEL, fx["diff"], {DEL}, True, mover=moved.append)
    assert out["counts"]["session"] == 1
    assert out["counts"]["message"] == 1 and out["counts"]["part"] == 1
    assert out["diff_moved"] is True and moved == [fx["diff"]]
    assert out["warnings"] == []
    for t, k in [("message", "session_id"), ("part", "session_id"),
                 ("todo", "session_id"), ("event", "aggregate_id")]:
        assert con.execute(f"SELECT COUNT(*) FROM {t} WHERE {k}=?", (DEL,)).fetchone()[0] == 0
    assert con.execute("SELECT COUNT(*) FROM session WHERE id=?", (KEEP,)).fetchone()[0] == 1
    assert con.execute("SELECT COUNT(*) FROM message WHERE session_id=?", (KEEP,)).fetchone()[0] == 1


def test_safe_diff_path(fx):
    from src.v2_session import safe_diff_path

    d = fx["dir"]
    assert safe_diff_path(d, "ses_abc123") == d / "ses_abc123.json"
    assert safe_diff_path(d, "s1") is None
    assert safe_diff_path(d, "../evil") is None
    assert safe_diff_path(d, "ses_a/b") is None


def test_delete_dat_mismatch_warns_and_continues(fx):
    out = v2_session.delete(fx["con"], DEL, None, {"ses_other"}, True, mover=lambda p: None)
    assert out["counts"]["session"] == 1
    assert len(out["warnings"]) == 1 and DEL in out["warnings"][0]
    with pytest.raises(ReadError):
        v2_session.delete(fx["con"], KEEP, None, {KEEP}, False, mover=lambda p: None)
