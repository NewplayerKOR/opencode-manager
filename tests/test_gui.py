"""T09 GUI smoke on synthetic fixture only (offscreen, no real data)."""
import os
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PySide6.QtWidgets import QApplication, QPushButton  # noqa: E402

from src.main import MainWindow  # noqa: E402
from test_readers import _build_fx  # noqa: E402


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


_set_counter = 0


def mkw(fx, **kw):
    """Build MainWindow with isolated IniFormat prefs (never real user prefs).

    NOTE: QSettings(org, app) ignores setDefaultFormat on this stack, so an
    explicit IniFormat object is injected instead.
    """
    from PySide6.QtCore import QSettings

    global _set_counter
    _set_counter += 1
    d = Path(tempfile.mkdtemp(prefix="om-set-"))
    QSettings.setPath(QSettings.IniFormat, QSettings.UserScope, str(d))
    settings = QSettings(
        QSettings.IniFormat, QSettings.UserScope,
        "OpencodeManager", f"Test{_set_counter}",
    )
    settings._tmpdir = str(d)  # kept alive via window reference below
    win = MainWindow(
        db_path=fx["db"], global_dat=fx["gdat"], diff_dir=fx["diff"],
        settings=settings, **kw,
    )
    win._settings_tmpdir = str(d)
    return win


@pytest.fixture()
def fx():
    tmp = Path(tempfile.mkdtemp(prefix="om-gui-"))
    yield _build_fx(tmp)
    shutil.rmtree(tmp, ignore_errors=True)


def test_window_loads_fixture(app, fx):
    win = mkw(fx)
    try:
        assert "세션 3건" in win.dash.text()
        assert "활성 1 / 비활성 1" in win.dash.text()
        assert win.tree.topLevelItemCount() == 2
        labels = [win.btn_refresh.text(), win.btn_copy.text()]
        assert labels == ["새로고침", "복사"]
        v2labels = [win.btn_archive.text(), win.btn_delete.text(), win.btn_cleanup.text()]
        assert v2labels == ["세션 보관", "세션 삭제", "프로젝트 삭제"]
        # V2 buttons exist but stay disabled until gates pass (T22)
        assert not win.btn_archive.isEnabled()
        # excluded-3 (lockfile delete / kill / auto clean) have no buttons
        texts = [b.text() for b in win.findChildren(QPushButton)]
        for bad in ("복구", "kill", "자동"):
            assert all(bad not in t for t in texts)
        # select first project -> sessions listed
        top = win.tree.topLevelItem(0)
        win.tree.setCurrentItem(top.child(0))
        assert win.table.rowCount() >= 1
        assert win.diag.text().startswith("진단:")
        assert "T10 반영 예정" not in win.diag.text()
        assert "<li>" in win.diag.text()  # findings separated per line (T24)
        assert "<b>R02</b>" in win.diag.text()
    finally:
        win.close()


def test_v2_buttons_gate_on_lockfile(app, fx):
    tmp = Path(tempfile.mkdtemp(prefix="om-gui-v2-"))
    try:
        (tmp / "lock").write_text("x", encoding="utf-8")
        locked = mkw(fx, lockfile=tmp / "lock")
        try:
            top = locked.tree.topLevelItem(0)
            locked.tree.setCurrentItem(top.child(0))
            assert not locked.btn_archive.isEnabled()
            assert not locked.btn_cleanup.isEnabled()
        finally:
            locked.close()
        free = mkw(fx, lockfile=tmp / "no-lock")
        try:
            top = free.tree.topLevelItem(0)
            free.tree.setCurrentItem(top.child(0))
            assert free.btn_cleanup.isEnabled()
            assert not free.btn_archive.isEnabled()  # no session selected yet
        finally:
            free.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_resize_min_and_stretch(app, fx):
    from PySide6.QtWidgets import QHeaderView

    win = mkw(fx)
    try:
        assert (win.minimumWidth(), win.minimumHeight()) == (800, 500)
        assert win.table.horizontalHeader().stretchLastSection() is True
        assert win.table.horizontalHeader().sectionResizeMode(1) == QHeaderView.Interactive
        assert win.tree.header().stretchLastSection() is True
        win.show()
        app.processEvents()
        win.resize(800, 500)
        app.processEvents()
        narrow = win.split.widget(1).width()
        col_narrow = win.table.columnWidth(2)
        win.resize(1200, 800)
        app.processEvents()
        assert win.split.widget(1).width() > narrow
        assert win.table.columnWidth(2) >= col_narrow
    finally:
        win.close()


def test_splitter_smooth_narrow(app, fx):
    win = mkw(fx)
    try:
        assert win.split.isCollapsible(0) is False
        assert win.split.isCollapsible(1) is False
        win.show()
        app.processEvents()
        win.resize(1100, 650)
        app.processEvents()
        sizes = win.split.sizes()
        assert sizes[0] > 0 and sizes[1] > 0
        handle = win.split.handleWidth() + sizes[0]
        prev = sizes[0]
        for step in range(1, 6):
            win.split.moveSplitter(handle + step * 10, 1)
            app.processEvents()
            cur = win.split.sizes()
            assert cur[0] > 0 and cur[1] > 0  # no collapse jumps
            assert cur[0] > prev  # smooth monotonic growth
            assert cur[0] - prev <= 25  # no chunky leaps
            prev = cur[0]
    finally:
        win.close()


def test_fold_toggle_both(app, fx):
    win = mkw(fx)
    try:
        win.show()
        app.processEvents()
        win.resize(1000, 650)
        app.processEvents()
        before = win.split.sizes()
        assert before[0] > 0 and before[1] > 0
        win.btn_fold_left.click()
        app.processEvents()
        assert win.split.sizes()[0] == 0
        assert "펼치기" in win.btn_fold_left.text()
        win.btn_fold_left.click()
        app.processEvents()
        assert win.split.sizes()[0] > 0
        assert "접기" in win.btn_fold_left.text()
        win.btn_fold_right.click()
        app.processEvents()
        assert win.split.sizes()[1] == 0
        win.btn_fold_right.click()
        app.processEvents()
        assert win.split.sizes()[1] > 0
    finally:
        win.close()


def test_message_column_prefilled(app, fx):
    win = mkw(fx)
    try:
        top = win.tree.topLevelItem(0)
        win.tree.setCurrentItem(top.child(0))
        assert win.table.rowCount() >= 1
        for r in range(win.table.rowCount()):
            assert win.table.item(r, 2).text() != ""
    finally:
        win.close()


def test_theme_and_font(app, fx):
    win = mkw(fx)
    try:
        assert win.theme_combo.count() == 2  # light is default
        assert "font-size: 13px" in win.styleSheet()
        win.size_spin.setValue(14)
        assert "font-size: 14px" in win.styleSheet()
        win.theme_combo.setCurrentIndex(1)
        assert "#18181B" in win.styleSheet()
        win.theme_combo.setCurrentIndex(0)
        win.size_spin.setValue(12)
        assert "font-size: 12px" in win.styleSheet()
        assert win.settings.value("theme") == "light"
    finally:
        win.close()


def test_font_family_saved(app, fx):
    from PySide6.QtWidgets import QApplication

    win = mkw(fx)
    try:
        assert win.set_font_combo is not None
        win._change_font_family("Arial")
        assert win.settings.value("font_family") == "Arial"
        assert QApplication.instance().font().family() == "Arial"
    finally:
        win.close()


def test_diag_palette_per_theme(app, fx):
    win = mkw(fx)
    try:
        assert "#854D0E" in win.diag.text()  # light warn brown
        win.theme_combo.setCurrentIndex(1)
        assert "#FDE047" in win.diag.text()  # dark warn yellow
    finally:
        win.close()


def test_settings_tab_contents(app, fx):
    win = mkw(fx)
    try:
        assert win.tabs.count() == 3
        assert win.tabs.tabText(0) == "메인"
        assert win.tabs.tabText(1) == "설정"
        assert win.tabs.tabText(2) == "백업"
        assert win.lang_combo.count() == 4
        assert win.theme_combo.count() == 2
        assert (win.size_spin.minimum(), win.size_spin.maximum()) == (11, 18)
    finally:
        win.close()


def test_language_switch(app, fx):
    win = mkw(fx)
    try:
        win._set_lang("en")
        assert win.btn_refresh.text() == "Refresh"
        assert win.tree.headerItem().text(0) == "Projects (active/inactive)"
        assert win.tabs.tabText(1) == "Settings"
        assert win.btn_archive.text() == "Archive session"
        assert "look different" in win.diag.text()
        assert win.settings.value("lang") == "en"
        win._set_lang("ko")
        assert win.btn_refresh.text() == "새로고침"
    finally:
        win.close()


def _one_session_id(db):
    import sqlite3

    con = sqlite3.connect(str(db))
    try:
        return con.execute("SELECT id FROM session LIMIT 1").fetchone()[0]
    finally:
        con.close()


def test_backup_tab_list_restore_delete(app, fx):
    import sqlite3
    from unittest import mock

    from src import v2_backup

    from src.main import MainWindow

    tmp = Path(tempfile.mkdtemp(prefix="om-bakui-"))
    try:
        sid = _one_session_id(fx["db"])
        con = sqlite3.connect(str(fx["db"]))
        dest = tmp / "baks"
        v2_backup.backup(con, [sid], [], [], {"reason": "t", "confirmed": True}, dest / "x")
        con.close()
        win = mkw(fx, backup_root=dest, lockfile=tmp / "no-lock")
        try:
            win.tabs.setCurrentIndex(2)
            app.processEvents()
            assert win.bak_list.count() == 1
            win.bak_list.setCurrentRow(0)
            assert win._sel_backup() == dest / "x"
            # restore path: delete rows, restore via UI handler
            con = sqlite3.connect(str(fx["db"]))
            con.execute("DELETE FROM message WHERE session_id=?", (sid,))
            con.execute("DELETE FROM session WHERE id=?", (sid,))
            con.commit()
            con.close()
            win._confirm2 = lambda *a: True
            win._run_restore_backup()
            con = sqlite3.connect(str(fx["db"]))
            try:
                assert con.execute("SELECT COUNT(*) FROM session WHERE id=?", (sid,)).fetchone()[0] == 1
            finally:
                con.close()
            # delete path: mocked trash (fake moves aside like real trash)
            win.bak_list.setCurrentRow(0)
            with mock.patch(
                "src.v2_safety.move_to_trash",
                side_effect=lambda paths: [Path(p).rename(tmp / "trash") for p in paths],
            ) as m:
                win._run_delete_backup()
                m.assert_called_once_with([dest / "x"])
            assert win._bak_paths == []
        finally:
            win.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_geometry_remembered(app, fx):
    from PySide6.QtCore import QSettings

    from src.main import MainWindow

    d = Path(tempfile.mkdtemp(prefix="om-set-geo-"))
    QSettings.setPath(QSettings.IniFormat, QSettings.UserScope, str(d))
    try:
        shared = QSettings(QSettings.IniFormat, QSettings.UserScope, "OpencodeManager", "GeoT")
        win = MainWindow(
            db_path=fx["db"], global_dat=fx["gdat"], diff_dir=fx["diff"], settings=shared,
        )
        win.show()
        app.processEvents()
        win.resize(800, 550)  # within offscreen 800x600 screen
        app.processEvents()
        win.close()
        win2 = MainWindow(
            db_path=fx["db"], global_dat=fx["gdat"], diff_dir=fx["diff"], settings=shared,
        )
        try:
            assert (win2.width(), win2.height()) == (800, 550)
        finally:
            win2.close()
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_missing_db_no_crash(app, tmp_path_factory=None, tmpdir=None):
    import tempfile as _tf

    tmp = Path(_tf.mkdtemp(prefix="om-gui-miss-"))
    try:
        win = mkw(
            {"db": tmp / "no.db", "gdat": tmp / "no.dat", "diff": tmp / "no-diff"}
        )
        try:
            assert "잠겨" in win.dash.text() or "조회" in win.dash.text()
        finally:
            win.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
