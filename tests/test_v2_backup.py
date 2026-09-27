"""T17 backup/restore roundtrip on synthetic fixture only."""
import json
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src import v2_backup  # noqa: E402

DEL = "ses_del00001"
KEEP = "ses_keep0002"


@pytest.fixture()
def fx():
    tmp = Path(tempfile.mkdtemp(prefix="om-v2b-"))
    db = tmp / "w.db"
    con = sqlite3.connect(str(db))
    con.execute("CREATE TABLE session (id TEXT PRIMARY KEY, title TEXT, time_archived INTEGER)")
    con.execute("CREATE TABLE message (id TEXT PRIMARY KEY, session_id TEXT, data TEXT)")
    con.execute("CREATE TABLE part (id TEXT PRIMARY KEY, message_id TEXT, session_id TEXT, data TEXT)")
    con.execute("CREATE TABLE todo (session_id TEXT PRIMARY KEY, content TEXT)")
    con.execute("CREATE TABLE event (id TEXT PRIMARY KEY, aggregate_id TEXT, data TEXT)")
    con.execute("INSERT INTO session VALUES (?, 'Old', 1700000006000), (?, 'Live', NULL)", (DEL, KEEP))
    con.execute("INSERT INTO message VALUES ('m1', ?, '{}'), ('m2', ?, '{}')", (DEL, KEEP))
    con.execute("INSERT INTO part VALUES ('p1', 'm1', ?, '{}')", (DEL,))
    con.execute("INSERT INTO todo VALUES (?, 't')", (DEL,))
    con.execute("INSERT INTO event VALUES ('e1', ?, '{}')", (DEL,))
    con.commit()
    diff = tmp / "ses_del00001.json"
    diff.write_text("{}", encoding="utf-8")
    dat = tmp / "w.dat"
    dat.write_text("{}", encoding="utf-8")
    yield {"dir": tmp, "db": db, "con": con, "diff": diff, "dat": dat}
    con.close()
    shutil.rmtree(tmp, ignore_errors=True)


def _delete(con, sid):
    con.execute("DELETE FROM part WHERE session_id=?", (sid,))
    con.execute("DELETE FROM message WHERE session_id=?", (sid,))
    con.execute("DELETE FROM todo WHERE session_id=?", (sid,))
    con.execute("DELETE FROM event WHERE aggregate_id=?", (sid,))
    con.execute("DELETE FROM session WHERE id=?", (sid,))
    con.commit()


def test_roundtrip(fx):
    con = fx["con"]
    dest = fx["dir"] / "bak"
    v2_backup.backup(
        con, [DEL], [fx["diff"]], [fx["dat"]],
        {"reason": "t", "confirmed": True, "kind": "session"}, dest,
    )
    manifest = json.loads((dest / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["ids"] == [DEL] and manifest["confirmed"] is True
    assert v2_backup.verify(dest, con) is True  # pre-delete: ids present
    _delete(con, DEL)
    assert v2_backup.verify(dest, con) is False
    out = v2_backup.restore(dest, con)
    assert out["session"] == 1 and out["message"] == 1 and out["part"] == 1
    assert v2_backup.verify(dest, con) is True
    row = con.execute("SELECT title, time_archived FROM session WHERE id=?", (DEL,)).fetchone()
    assert row == ("Old", 1700000006000)  # archived flag preserved
    assert con.execute("SELECT COUNT(*) FROM session WHERE id=?", (KEEP,)).fetchone()[0] == 1


def test_tamper_detected(fx):
    dest = fx["dir"] / "bak"
    v2_backup.backup(fx["con"], [DEL], [fx["diff"]], [fx["dat"]], {"reason": "t"}, dest)
    (dest / "session_diff" / fx["diff"].name).write_text('{"x":1}', encoding="utf-8")
    assert v2_backup.verify(dest, fx["con"]) is False
