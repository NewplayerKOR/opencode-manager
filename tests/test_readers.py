"""T08 verification on synthetic fixture only. No real DB/.dat access."""
import base64
import json
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src import dat_reader, db_reader, errors, paths_win


@pytest.fixture()
def fx():
    # NOTE: repo-local tmp instead of pytest tmp_path (broken ACL on this
    # machine's Temp\\pytest-of-<user>). Still synthetic fixture only.
    tmp_path = Path(tempfile.mkdtemp(prefix="om-fx-"))
    yield _build_fx(tmp_path)
    shutil.rmtree(tmp_path, ignore_errors=True)


def _build_fx(tmp_path: Path):
    db = tmp_path / "fx.db"
    con = sqlite3.connect(str(db))
    con.execute("CREATE TABLE project (id TEXT PRIMARY KEY, worktree TEXT, name TEXT)")
    con.execute(
        "CREATE TABLE session (id TEXT PRIMARY KEY, project_id TEXT,"
        " directory TEXT, title TEXT, time_created INTEGER,"
        " time_updated INTEGER, time_archived INTEGER)"
    )
    con.execute(
        "CREATE TABLE message (id TEXT PRIMARY KEY, session_id TEXT,"
        " time_created INTEGER, time_updated INTEGER, data TEXT)"
    )
    con.execute(
        "INSERT INTO project VALUES ('p1','C:/Proj/A','a'),('p2','C:/Proj/B',NULL)"
    )
    con.executemany(
        "INSERT INTO session VALUES (?,?,?,?,?,?,?)",
        [
            ("ses_aaa11111", "p1", "C:/Proj/A", "Hello", 1700000000000, 1700000001000, None),
            ("ses_bbb22222", "p1", "C:/Proj/A", "", 1700000002000, 1700000003000, None),
            ("ses_ccc33333", "p2", "C:/Proj/B", "Old", 1700000004000, 1700000005000, 1700000006000),
        ],
    )
    con.executemany(
        "INSERT INTO message VALUES (?,?,?,?,?)",
        [
            ("m1", "ses_aaa11111", 1, 1, "{}"),
            ("m2", "ses_aaa11111", 2, 2, "{}"),
            ("m3", "ses_ccc33333", 3, 3, "{}"),
        ],
    )
    con.commit()
    con.close()
    diff = tmp_path / "diff"
    diff.mkdir()
    (diff / "ses_aaa11111.json").write_text("{}", encoding="utf-8")
    wt = base64.b64encode("C:\\Proj\\A".encode()).decode().rstrip("=")
    g = {
        "server": json.dumps(
            {
                "projects": {"local": [{"worktree": "C:\\Proj\\A", "expanded": True}]},
                "recentlyClosed": {"local": ["C:\\Proj\\B"]},
            }
        ),
        "layout": json.dumps({"sessionTabs": {f"local\x00{wt}/ses_aaa11111": {}}}),
    }
    gdat = tmp_path / "global.dat"
    gdat.write_text(json.dumps(g), encoding="utf-8")
    (tmp_path / "opencode.workspace.x.dat").write_text('{"a":1}', encoding="utf-8")
    return {"db": db, "diff": diff, "gdat": gdat, "dir": tmp_path}


def test_db_projects_and_counts(fx):
    con = db_reader.connect_ro(fx["db"])
    try:
        projs = {p.worktree: p.session_count for p in db_reader.list_db_projects(con)}
        assert projs == {"C:/Proj/A": 2, "C:/Proj/B": 1}
        assert db_reader.counts(con) == {"session": 3, "project": 2, "message": 3}
    finally:
        con.close()


def test_session_title_fallback(fx):
    con = db_reader.connect_ro(fx["db"])
    try:
        got = {s.id: s.title for s in db_reader.list_sessions(con, "C:\\Proj\\A")}
        assert got["ses_aaa11111"] == "Hello"
        assert got["ses_bbb22222"].endswith("(자동 표기)")
        d = db_reader.session_detail(con, "ses_aaa11111", fx["diff"])
        assert (d.message_count, d.has_diff) == (2, True)
        d2 = db_reader.session_detail(con, "ses_bbb22222", fx["diff"])
        assert (d2.message_count, d2.has_diff) == (0, False)
        act = {a["directory"]: a for a in db_reader.project_activity(con)}
        assert act["C:/Proj/A"]["message_count"] == 2
    finally:
        con.close()


def test_session_detail_not_found(fx):
    con = db_reader.connect_ro(fx["db"])
    try:
        with pytest.raises(errors.NotFound):
            db_reader.session_detail(con, "ses_missing")
    finally:
        con.close()


def test_storage_stats(fx):
    st = db_reader.storage_stats(fx["diff"])
    assert st["count"] == 1 and st["bytes"] > 0


def test_dat_reader(fx):
    g = dat_reader.load_global(fx["gdat"])
    assert dat_reader.active_worktrees(g) == ["C:\\Proj\\A"]
    assert dat_reader.recently_closed(g) == ["C:\\Proj\\B"]
    assert dat_reader.session_tabs(g) == [("C:\\Proj\\A", "ses_aaa11111")]
    inv = dat_reader.workspace_inventory(str(fx["dir"] / "opencode.workspace.*.dat"))
    assert len(inv) == 1
    with pytest.raises(errors.DatMissing):
        dat_reader.load_global(fx["dir"] / "nope.dat")
    bad = fx["dir"] / "bad.dat"
    bad.write_text("{oops", encoding="utf-8")
    with pytest.raises(errors.DatParseFailed):
        dat_reader.load_global(bad)


def test_paths_and_errors():
    assert set(paths_win.resolve_all()) == {"D01", "D02", "D03", "D04", "D05", "D06", "D07", "D08"}
    assert paths_win.file_size(Path("C:/no/such/file-xyz.dat")) is None
    assert "잠겨" in errors.DbLocked().msg
    assert db_reader.normalize_directory("C:/A//B\\") == "c:\\a\\b"
    assert db_reader.is_unc_or_wsl("\\\\wsl$\\x") is True
