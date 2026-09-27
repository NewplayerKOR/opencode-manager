"""Opencode Manager (T09 V1 viewer + T22 V2 actions behind gates).

V1 area is read-only. V2 buttons (archive/delete/cleanup) stay disabled
unless every T18 gate passes; destructive paths need confirmation twice.
"""
from __future__ import annotations

import datetime as _dt
import html as _html
import json as _json
import sqlite3
import sys
import tempfile
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFontComboBox,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src import (
    __version__,
    dat_reader,
    db_reader,
    diagnostics,
    errors,
    i18n,
    paths_win,
    v2_backup,
    v2_project,
    v2_safety,
    v2_session,
)

QSS_LIGHT = """
QMainWindow, QWidget {{ font-size: {px}px; background: #F4F4F5; color: #18181B; }}
QLabel#dashboard {{ background: #EFF6FF; color: #1D4ED8; padding: 6px; border: 1px solid #E4E4E7; }}
QLabel#diagPlaceholder {{ background: #FFFFFF; color: #71717A; padding: 6px; border: 1px solid #E4E4E7; }}
QLabel#diagWarn {{ background: #FEF9C3; color: #854D0E; padding: 6px; border: 1px solid #E4E4E7; }}
QStatusBar {{ background: #F4F4F5; color: #71717A; }}
QPushButton {{ background: #FFFFFF; color: #18181B; border: 1px solid #E4E4E7; padding: 5px 10px; }}
QPushButton:disabled {{ color: #A1A1AA; }}
QTreeWidget, QTableWidget {{ background: #FFFFFF; color: #18181B; border: 1px solid #E4E4E7; }}
QHeaderView::section {{ background: #F4F4F5; color: #18181B; }}
QSplitter::handle {{ background: #E4E4E7; }}
"""

QSS_DARK = """
QMainWindow, QWidget {{ font-size: {px}px; background: #18181B; color: #F4F4F5; }}
QLabel#dashboard {{ background: #27272A; color: #60A5FA; padding: 6px; border: 1px solid #3F3F46; }}
QLabel#diagPlaceholder {{ background: #27272A; color: #A1A1AA; padding: 6px; border: 1px solid #3F3F46; }}
QLabel#diagWarn {{ background: #422006; color: #FDE047; padding: 6px; border: 1px solid #3F3F46; }}
QStatusBar {{ background: #18181B; color: #A1A1AA; }}
QPushButton {{ background: #27272A; color: #F4F4F5; border: 1px solid #3F3F46; padding: 5px 10px; }}
QPushButton:disabled {{ color: #71717A; }}
QTreeWidget, QTableWidget {{ background: #27272A; color: #F4F4F5; border: 1px solid #3F3F46; }}
QHeaderView::section {{ background: #27272A; color: #F4F4F5; }}
QSplitter::handle {{ background: #3F3F46; }}
"""

FONT_MIN, FONT_MAX, FONT_DEFAULT = 11, 18, 13


def _ms(ms: int | None) -> str:
    if not ms:
        return "-"
    return _dt.datetime.fromtimestamp(ms / 1000).strftime("%Y-%m-%d %H:%M")


class MainWindow(QMainWindow):
    def __init__(
        self,
        db_path: Path | None = None,
        global_dat: Path | None = None,
        diff_dir: Path | None = None,
        lockfile: Path | None = None,
        backup_root: Path | None = None,
        settings: QSettings | None = None,
    ) -> None:
        super().__init__()
        loc = paths_win.resolve_all()
        self.db_path = db_path or loc["D01"]
        self.global_dat = global_dat or loc["D04"]
        self.diff_dir = diff_dir if diff_dir is not None else loc["D02"]
        self.lockfile = lockfile or loc["D08"]
        self.backup_root = backup_root or (
            Path(tempfile.gettempdir()) / "opencode" / "v2bak"
        )
        self._active: set[str] = set()
        self._global_ok = True
        self.setWindowTitle(f"Opencode Manager v{__version__}")
        self.setMinimumSize(800, 500)
        self.settings = settings or QSettings("OpencodeManager", "OpencodeManager")
        self._lang = self.settings.value("lang", "ko")
        if self._lang not in i18n.LANGS:
            self._lang = "ko"
        self._t = lambda key: i18n.tr(key, self._lang)
        self._theme = self.settings.value("theme", "light")
        if self._theme not in ("light", "dark"):
            self._theme = "light"
        try:
            self._font_px = int(self.settings.value("font_px", FONT_DEFAULT))
        except (TypeError, ValueError):
            self._font_px = FONT_DEFAULT
        self._font_px = max(FONT_MIN, min(FONT_MAX, self._font_px))
        self._apply_style()
        self._build()
        geo = self.settings.value("geometry")
        if geo is not None:
            try:
                self.restoreGeometry(geo)
            except Exception:
                pass
        self.refresh()

    def _build(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)
        self.tabs = QTabWidget()
        outer.addWidget(self.tabs)
        tab_main = QWidget()
        root = QVBoxLayout(tab_main)
        self.tabs.addTab(tab_main, "")

        self.dash = QLabel("", objectName="dashboard")
        root.addWidget(self.dash)

        foldbar = QHBoxLayout()
        self.btn_fold_left = QPushButton("◀ 접기")
        self.btn_fold_left.setFixedWidth(80)
        self.btn_fold_left.clicked.connect(lambda: self._toggle_panel(0))
        self.btn_fold_right = QPushButton("접기 ▶")
        self.btn_fold_right.setFixedWidth(80)
        self.btn_fold_right.clicked.connect(lambda: self._toggle_panel(1))
        foldbar.addWidget(self.btn_fold_left)
        foldbar.addStretch(1)
        foldbar.addWidget(self.btn_fold_right)
        root.addLayout(foldbar)

        split = QSplitter(Qt.Horizontal)
        root.addWidget(split, 1)
        self.split = split
        self._split_saved: list[int] = []

        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("")
        self.tree.itemSelectionChanged.connect(self._on_project)
        self.tree.header().setStretchLastSection(True)
        self.tree.header().setMinimumSectionSize(30)
        self.tree.setMinimumWidth(120)
        split.addWidget(self.tree)

        right = QWidget()
        rl = QVBoxLayout(right)
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["", "", ""])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setMinimumSectionSize(30)
        self.table.itemSelectionChanged.connect(self._on_session)
        rl.addWidget(self.table, 1)

        self.detail = QLabel("", wordWrap=True)
        rl.addWidget(self.detail)

        self.diag = QLabel("", objectName="diagPlaceholder")
        self.diag.setWordWrap(True)
        rl.addWidget(self.diag)
        split.addWidget(right)
        split.setSizes([300, 500])
        split.setStretchFactor(0, 0)
        split.setStretchFactor(1, 1)
        split.setCollapsible(0, False)
        split.setCollapsible(1, False)

        bar = QHBoxLayout()
        self.btn_refresh = QPushButton()
        self.btn_refresh.clicked.connect(self.refresh)
        self.btn_copy = QPushButton()
        self.btn_copy.clicked.connect(self._on_copy)
        bar.addWidget(self.btn_refresh)
        bar.addWidget(self.btn_copy)
        bar.addStretch(1)
        root.addLayout(bar)

        v2bar = QHBoxLayout()
        self.v2row_label = QLabel()
        v2bar.addWidget(self.v2row_label)
        self.btn_archive = QPushButton()
        self.btn_archive.clicked.connect(self._run_archive_session)
        self.btn_delete = QPushButton()
        self.btn_delete.clicked.connect(self._run_delete_session)
        self.btn_cleanup = QPushButton()
        self.btn_cleanup.clicked.connect(self._run_cleanup_project)
        for b in (self.btn_archive, self.btn_delete, self.btn_cleanup):
            b.setEnabled(False)
            v2bar.addWidget(b)
        v2bar.addStretch(1)
        root.addLayout(v2bar)



        self.status = QStatusBar()
        self.setStatusBar(self.status)

        tab_set = QWidget()
        form = QFormLayout(tab_set)
        self.lang_combo = QComboBox()
        for code in i18n.LANGS:
            self.lang_combo.addItem(i18n.NAMES[code], code)
        self.lang_combo.currentIndexChanged.connect(self._on_lang_combo)
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("", "light")
        self.theme_combo.addItem("", "dark")
        self.theme_combo.currentIndexChanged.connect(self._on_theme_combo)
        self.set_font_combo = QFontComboBox()
        self.set_font_combo.setToolTip("")
        self.set_font_combo.currentTextChanged.connect(self._change_font_family)
        self.size_spin = QSpinBox()
        self.size_spin.setRange(FONT_MIN, FONT_MAX)
        self.size_spin.valueChanged.connect(self._on_size_spin)
        self.lbl_lang = QLabel()
        self.lbl_theme = QLabel()
        self.lbl_font = QLabel()
        self.lbl_size = QLabel()
        form.addRow(self.lbl_lang, self.lang_combo)
        form.addRow(self.lbl_theme, self.theme_combo)
        form.addRow(self.lbl_font, self.set_font_combo)
        form.addRow(self.lbl_size, self.size_spin)
        self.tabs.addTab(tab_set, "")

        tab_bak = QWidget()
        bak_layout = QVBoxLayout(tab_bak)
        self.bak_list = QListWidget()
        bak_layout.addWidget(self.bak_list, 1)
        bak_bar = QHBoxLayout()
        self.btn_bak_refresh = QPushButton()
        self.btn_bak_refresh.clicked.connect(self._refresh_backups)
        self.btn_bak_restore = QPushButton()
        self.btn_bak_restore.clicked.connect(self._run_restore_backup)
        self.btn_bak_delete = QPushButton()
        self.btn_bak_delete.clicked.connect(self._run_delete_backup)
        for b in (self.btn_bak_refresh, self.btn_bak_restore, self.btn_bak_delete):
            bak_bar.addWidget(b)
        bak_bar.addStretch(1)
        bak_layout.addLayout(bak_bar)
        self.tabs.addTab(tab_bak, "")
        self.tabs.currentChanged.connect(self._on_tab_changed)
        self._bak_paths: list[Path] = []
        self.retranslate()

    def _apply_style(self) -> None:
        base = QSS_DARK if self._theme == "dark" else QSS_LIGHT
        self.setStyleSheet(base.format(px=self._font_px))

    def _sync_chrome_labels(self) -> None:
        if hasattr(self, "theme_combo"):
            self.theme_combo.blockSignals(True)
            self.theme_combo.setItemText(0, self._t("theme_light"))
            self.theme_combo.setItemText(1, self._t("theme_dark"))
            self.theme_combo.setCurrentIndex(1 if self._theme == "dark" else 0)
            self.theme_combo.blockSignals(False)
        if hasattr(self, "size_spin") and self.size_spin.value() != self._font_px:
            self.size_spin.blockSignals(True)
            self.size_spin.setValue(self._font_px)
            self.size_spin.blockSignals(False)
        if hasattr(self, "lang_combo"):
            idx = self.lang_combo.findData(self._lang)
            if idx >= 0 and idx != self.lang_combo.currentIndex():
                self.lang_combo.blockSignals(True)
                self.lang_combo.setCurrentIndex(idx)
                self.lang_combo.blockSignals(False)
        if hasattr(self, "set_font_combo"):
            saved = self.settings.value("font_family", "") or ""
            if saved and self.set_font_combo.currentText() != saved:
                self.set_font_combo.blockSignals(True)
                self.set_font_combo.setCurrentText(saved)
                self.set_font_combo.blockSignals(False)

    def retranslate(self) -> None:
        _t = self._t
        self.tabs.setTabText(0, _t("tab_main"))
        self.tabs.setTabText(1, _t("tab_settings"))
        if hasattr(self, "tabs") and self.tabs.count() > 2:
            self.tabs.setTabText(2, _t("tab_backup"))
        if hasattr(self, "btn_bak_refresh"):
            self.btn_bak_refresh.setText(_t("bak_refresh"))
            self.btn_bak_restore.setText(_t("bak_restore"))
            self.btn_bak_delete.setText(_t("bak_delete"))
        self.tree.setHeaderLabel(_t("tree_header"))
        self.table.setHorizontalHeaderLabels(
            [_t("col_mark"), _t("col_session"), _t("col_message")]
        )
        self.btn_refresh.setText(_t("refresh"))
        self.btn_copy.setText(_t("copy"))
        self.v2row_label.setText(_t("v2row"))
        self.btn_archive.setText(_t("archive"))
        self.btn_delete.setText(_t("delete"))
        self.btn_cleanup.setText(_t("cleanup"))
        self.lbl_lang.setText(_t("set_language"))
        self.lbl_theme.setText(_t("set_theme"))
        self.lbl_font.setText(_t("set_font"))
        self.lbl_size.setText(_t("set_size"))
        self.set_font_combo.setToolTip(_t("font_tip"))
        if not getattr(self, "_row_session", None):
            self.detail.setText(_t("select_session"))
        left_open = self.split.widget(0).isVisible()
        right_open = self.split.widget(1).isVisible()
        self.btn_fold_left.setText(_t("fold_left") if left_open else _t("unfold_left"))
        self.btn_fold_right.setText(_t("fold_right") if right_open else _t("unfold_right"))
        self._sync_chrome_labels()
        self._sync_font_combo()
        self._render_diag()
        self._refresh_v2_state()

    def _set_lang(self, lang: str) -> None:
        if lang not in i18n.LANGS:
            return
        self._lang = lang
        self.settings.setValue("lang", lang)
        self.retranslate()
        self.refresh()

    def _on_lang_combo(self, idx: int) -> None:
        self._set_lang(self.lang_combo.itemData(idx))

    def _on_theme_combo(self, idx: int) -> None:
        self._set_theme_name(self.theme_combo.itemData(idx))

    def _on_size_spin(self, px: int) -> None:
        self._set_font_size(px)

    def _set_theme_name(self, name: str) -> None:
        if name not in ("light", "dark"):
            return
        self._theme = name
        self.settings.setValue("theme", name)
        self._apply_style()
        self._sync_chrome_labels()
        self._render_diag()

    def _set_font_size(self, px: int) -> None:
        self._font_px = max(FONT_MIN, min(FONT_MAX, px))
        self.settings.setValue("font_px", self._font_px)
        self._apply_style()
        self._sync_chrome_labels()

    def _apply_font_family(self, family: str) -> None:
        app = QApplication.instance()
        if app is not None:
            if family:
                app.setFont(QFont(family))
            else:
                app.setFont(QFont())

    def _sync_font_combo(self) -> None:
        saved = self.settings.value("font_family", "") or ""
        if saved:
            self.set_font_combo.blockSignals(True)
            self.set_font_combo.setCurrentText(saved)
            self.set_font_combo.blockSignals(False)
            self._apply_font_family(saved)

    def _change_font_family(self, family: str) -> None:
        self.settings.setValue("font_family", family)
        self._apply_font_family(family)
        combo = getattr(self, "set_font_combo", None)
        if combo is not None and combo.currentText() != family:
            combo.blockSignals(True)
            combo.setCurrentText(family)
            combo.blockSignals(False)

    def closeEvent(self, event) -> None:  # noqa: N802
        try:
            self.settings.setValue("geometry", self.saveGeometry())
        except Exception:
            pass
        super().closeEvent(event)

    def _load_active(self) -> None:
        self._active_raw: list[str] = []
        self._tabs: list[tuple[str, str]] = []
        try:
            g = dat_reader.load_global(self.global_dat)
            self._active_raw = dat_reader.active_worktrees(g)
            self._tabs = dat_reader.session_tabs(g)
            self._active = {
                db_reader.normalize_directory(w) for w in self._active_raw
            }
            self._global_ok = True
        except errors.ReadError:
            self._active = set()
            self._global_ok = False

    def refresh(self) -> None:
        self._load_active()
        try:
            con = db_reader.connect_ro(self.db_path)
        except errors.DbLocked as e:
            self._show_lock(e.msg)
            return
        try:
            projects = db_reader.list_db_projects(con)
            n = db_reader.counts(con)
        except errors.DbLocked as e:
            con.close()
            self._show_lock(e.msg)
            return
        except Exception:
            con.close()
            self.status.showMessage(self._t("query_fail"))
            return
        for p in projects:
            p.status = (
                self._t("grp_active")
                if db_reader.normalize_directory(p.worktree) in self._active
                else self._t("grp_inactive")
            )
        na = sum(1 for p in projects if p.status == self._t("grp_active"))
        sizes = {k: paths_win.file_size(v) for k, v in paths_win.resolve_all().items()}
        db_mb = (sizes.get("D01") or 0) / 1024 / 1024
        self.dash.setText(
            self._t("dash_t").format(
                mb=f"{db_mb:.1f}", b=f"{(sizes.get('D01') or 0):,}",
                s=f"{n.get('session', 0):,}", a=na, ia=len(projects) - na,
            )
            + ("" if self._global_ok else self._t("global_fail"))
        )
        self.tree.clear()
        for grp in (self._t("grp_active"), self._t("grp_inactive")):
            top = QTreeWidgetItem([grp])
            self.tree.addTopLevelItem(top)
            for p in projects:
                if p.status != grp:
                    continue
                it = QTreeWidgetItem([f"{p.worktree} ({p.session_count}{self._t('unit_sessions')})"])
                it.setFlags(it.flags() | Qt.ItemIsUserCheckable)
                it.setCheckState(0, Qt.Unchecked)
                it.setData(0, Qt.UserRole, p.worktree)
                top.addChild(it)
            top.setExpanded(True)
        old = getattr(self, "_con", None)
        if old is not None:
            try:
                old.close()
            except Exception:
                pass
        self._con = con
        self._update_diag([p.worktree for p in projects])
        self._refresh_v2_state()
        self.status.showMessage(
            self._t("ro_prefix") + self._t("refreshed_at")
            + _dt.datetime.now().strftime("%Y-%m-%d %H:%M")
        )

    def _show_lock(self, msg: str) -> None:
        msg = self._t("lock_guidance")
        self.dash.setText(self._t("dash_prefix") + msg)
        self.tree.clear()
        self.table.setRowCount(0)
        self.detail.setText(msg)
        self.diag.setText(self._t("diag_prefix") + " " + msg)
        self.diag.setObjectName("diagPlaceholder")
        self.diag.setStyleSheet("")
        self._findings = []
        for b in (self.btn_archive, self.btn_delete, self.btn_cleanup):
            b.setEnabled(False)
            b.setToolTip("DB 잠금: " + msg)
        self.status.showMessage(self._t("ro_prefix") + msg)

    def _ws_session_map(self, filenames: list[str]) -> dict[str, bool]:
        """Read-only key scan: does each workspace file hold session keys?"""
        import json as _json

        loc = paths_win.resolve_all()
        out: dict[str, bool] = {}
        for name in filenames:
            p = loc["D05"] / name
            try:
                keys = _json.loads(p.read_text(encoding="utf-8")).keys()
            except (OSError, ValueError):
                out[name] = True  # unreadable: stay loud, do not hide
                continue
            out[name] = any(str(k).startswith("session:") for k in keys)
        return out

    def _update_diag(self, worktrees: list[str]) -> None:
        loc = paths_win.resolve_all()
        pattern = str(loc["D05"] / paths_win.WORKSPACE_GLOB)
        inv = dat_reader.workspace_inventory(pattern)
        db_dirs = {db_reader.normalize_directory(w) for w in worktrees}
        wal = loc["D01"].parent / (loc["D01"].name + "-wal")
        dat_bad = [self.global_dat.name] if not self._global_ok else []
        dat_bad += [n for n, s in inv if s == 0]
        try:
            lock_exists = loc["D08"].exists()
        except OSError:
            lock_exists = False
        names = [n for n, _s in inv]
        findings = diagnostics.evaluate(
            self._active_raw,
            self._tabs,
            names,
            db_dirs,
            lock_exists,
            paths_win.file_size(wal),
            dat_bad,
            db_reader.normalize_directory,
            ws_sessions=self._ws_session_map(names),
        )
        self._findings = findings
        self._render_diag()

    def _render_diag(self) -> None:
        findings = getattr(self, "_findings", [])
        if not findings:
            self.diag.setText(f"{self._t('diag_prefix')} {self._t('diag_ok')}")
            self.diag.setObjectName("diagPlaceholder")
        else:
            if self._theme == "dark":
                color = {"orange": "#FDE047", "gray": "#A1A1AA"}
            else:
                color = {"orange": "#854D0E", "gray": "#71717A"}
            items = "".join(
                f"<li><b>{f.id}</b> "
                f"<span style='color:{color.get(f.color, '#71717A')}'>"
                f"{_html.escape(i18n.finding_text(f.id, f.n, self._lang))}"
                f"{': ' + _html.escape(', '.join(f.targets)) if f.targets else ''}"
                f"</span></li>"
                for f in findings
            )
            self.diag.setText(f"{self._t('diag_prefix')}<ul style='margin:0'>{items}</ul>")
            worst = "diagWarn" if any(f.color == "orange" for f in findings) else "diagPlaceholder"
            self.diag.setObjectName(worst)
        self.diag.setStyleSheet("")

    def _selected_worktree(self) -> str | None:
        it = self.tree.currentItem()
        if it is None or it.parent() is None:
            return None
        return it.data(0, Qt.UserRole)

    def _on_project(self) -> None:
        w = self._selected_worktree()
        con = getattr(self, "_con", None)
        if w is None or con is None:
            self._refresh_v2_state()
            return
        try:
            sessions = db_reader.list_sessions(con, w)
        except errors.DbLocked as e:
            self.detail.setText(e.msg)
            return
        self.table.setRowCount(len(sessions))
        self._row_session = {}
        try:
            msg_n = dict(
                con.execute(
                    "SELECT session_id, COUNT(*) FROM message GROUP BY session_id"
                ).fetchall()
            )
        except Exception:
            msg_n = {}
        for r, s in enumerate(sessions):
            c0 = QTableWidgetItem()
            c0.setFlags(c0.flags() | Qt.ItemIsUserCheckable)
            c0.setCheckState(Qt.Unchecked)
            c1 = QTableWidgetItem(s.title)
            c1.setData(Qt.UserRole, s.id)
            self.table.setItem(r, 0, c0)
            self.table.setItem(r, 1, c1)
            self.table.setItem(r, 2, QTableWidgetItem(f"{msg_n.get(s.id, 0):,}"))
            self._row_session[r] = s.id
        if not sessions:
            self.detail.setText(self._t("empty_project"))
        self._refresh_v2_state()

    def _on_session(self) -> None:
        rows = self.table.selectionModel().selectedRows() if self.table.selectionModel() else []
        if not rows:
            return
        sid = getattr(self, "_row_session", {}).get(rows[0].row())
        con = getattr(self, "_con", None)
        if sid is None or con is None:
            return
        try:
            d = db_reader.session_detail(con, sid, self.diff_dir)
        except errors.ReadError as e:
            self.detail.setText(e.msg)
            self._refresh_v2_state()
            return
        unc = self._t("unc_badge") if db_reader.is_unc_or_wsl(d.directory) else ""
        self.detail.setText(
            f"id: {d.id}\n{self._t('dl_title')}: {d.title}\n"
            f"{self._t('dl_path')}: {d.directory}{unc}\n"
            f"{self._t('dl_norm')}: {d.directory_norm}\n"
            f"{self._t('dl_created')}: {_ms(d.time_created)}"
            f" / {self._t('dl_updated')}: {_ms(d.time_updated)}\n"
            f"{self._t('dl_messages')}: {d.message_count:,}{self._t('unit_sessions')} / "
            f"{self._t('dl_diff')}: {self._t('dl_yes') if d.has_diff else self._t('dl_no')}"
        )
        self.table.setItem(rows[0].row(), 2, QTableWidgetItem(f"{d.message_count:,}"))
        self._refresh_v2_state()

    def _lock_exists(self) -> bool:
        try:
            return self.lockfile.exists()
        except OSError:
            return True

    def _sel_session_id(self) -> str | None:
        rows = self.table.selectionModel().selectedRows() if self.table.selectionModel() else []
        if not rows:
            return None
        return getattr(self, "_row_session", {}).get(rows[0].row())

    def _refresh_v2_state(self) -> None:
        locked = self._lock_exists() or getattr(self, "_con", None) is None
        sid = self._sel_session_id()
        work = self._selected_worktree()
        reason = ""
        if locked:
            reason = self._t("tip_locked")
        self.btn_archive.setEnabled(not locked and sid is not None)
        self.btn_delete.setEnabled(not locked and sid is not None)
        self.btn_cleanup.setEnabled(not locked and work is not None)
        for b in (self.btn_archive, self.btn_delete, self.btn_cleanup):
            if reason:
                b.setToolTip(reason)
            elif not b.isEnabled():
                b.setToolTip(self._t("tip_noselect"))
            else:
                b.setToolTip(self._t("tip_ready"))

    def _confirm2(self, title: str, stage1: str, stage2: str) -> bool:
        if (
            QMessageBox.question(self, title, stage1, QMessageBox.Yes | QMessageBox.No)
            != QMessageBox.Yes
        ):
            return False
        return (
            QMessageBox.warning(self, title, stage2, QMessageBox.Yes | QMessageBox.No)
            == QMessageBox.Yes
        )

    def _do_backup(
        self, kind: str, session_ids: list[str], project_ids: list[str],
        diffs: list[Path], dats: list[Path],
    ) -> Path | None:
        dest = self.backup_root / _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        try:
            con = db_reader.connect_ro(self.db_path)
        except errors.DbLocked as e:
            QMessageBox.information(self, self._t("backup_title"), e.msg)
            return None
        try:
            v2_backup.backup(
                con, session_ids, diffs, dats,
                {"reason": kind, "confirmed": True, "kind": kind}, dest,
                project_ids=project_ids,
            )
        finally:
            con.close()
        return dest

    @staticmethod
    def _trash_available() -> bool:
        try:
            import send2trash  # noqa: F401

            return True
        except ImportError:
            return False

    def _gates_ok(self, backup_dir: Path, con: sqlite3.Connection, confirmed: bool) -> bool:
        """confirmed must be True only after the 2-step dialogs passed."""
        gates = v2_safety.check_all(
            self._lock_exists(), v2_backup.verify(backup_dir, con),
            self._trash_available(), confirmed, confirmed,
            (backup_dir / "manifest.json").is_file(),
        )
        bad = [g for g in gates if not g.passed]
        if bad:
            QMessageBox.information(self, self._t("gate_title"), " / ".join(g.message for g in bad))
            return False
        return True

    def _rw(self) -> sqlite3.Connection:
        return sqlite3.connect(str(self.db_path))

    def _run_archive_session(self) -> None:
        sid = self._sel_session_id()
        if sid is None:
            return
        if self._lock_exists():
            QMessageBox.information(self, self._t("c_archive"), self._t("lock_cant"))
            return
        if not self._confirm2(self._t("c_archive"), self._t("ca_t1").format(sid=sid), self._t("ca_t2").format(sid=sid)):
            return
        con = self._rw()
        try:
            v2_session.archive(con, sid, True)
        except errors.ReadError as e:
            QMessageBox.information(self, self._t("c_archive"), e.msg)
            return
        finally:
            con.close()
        self.refresh()
        self.status.showMessage(self._t("archived_is") + sid)

    def _run_delete_session(self) -> None:
        sid = self._sel_session_id()
        if sid is None:
            return
        if self._lock_exists():
            QMessageBox.information(self, self._t("c_delete"), self._t("lock_cant"))
            return
        diff = v2_session.safe_diff_path(self.diff_dir, sid)
        dat_keys = {s for _, s in self._tabs}
        if not self._confirm2(
            self._t("c_delete"),
            self._t("cd_t1").format(sid=sid),
            self._t("cd_t2").format(sid=sid),
        ):
            return
        dest = self._do_backup("session", [sid], [], [diff] if diff.is_file() else [], [])
        if dest is None:
            return
        con = self._rw()
        try:
            if not self._gates_ok(dest, con, True):
                return
            out = v2_session.delete(con, sid, diff, dat_keys, True)
        finally:
            con.close()
        self.refresh()
        self._refresh_backups()
        warns = " / ".join(out["warnings"]) if out["warnings"] else self._t("no_warn")
        self.status.showMessage(f"{self._t('deleted_is')}{sid} ({warns})")

    def _workspace_files_for(self, worktree_norm: str) -> list[Path]:
        from src import diagnostics as _dg

        loc = paths_win.resolve_all()
        out = []
        for p in loc["D05"].glob(paths_win.WORKSPACE_GLOB):
            if p.is_file() and _dg.workspace_indexed(p.name, {worktree_norm}, db_reader.normalize_directory):
                out.append(p)
        return out

    def _run_cleanup_project(self) -> None:
        work = self._selected_worktree()
        if work is None:
            return
        if self._lock_exists():
            QMessageBox.information(self, self._t("c_cleanup"), self._t("lock_cant"))
            return
        con = getattr(self, "_con", None)
        if con is None:
            return
        pid_rows = con.execute("SELECT id FROM project WHERE worktree=?", (work,)).fetchall()
        pid = pid_rows[0][0] if pid_rows else None
        sids = [r[0] for r in con.execute("SELECT id FROM session WHERE directory=?", (work,)).fetchall()]
        if pid is None:
            QMessageBox.information(self, self._t("c_cleanup"), self._t("no_db_row"))
            return
        if pid == "global":
            QMessageBox.information(self, self._t("c_cleanup"), self._t("global_no"))
            return
        is_active = db_reader.normalize_directory(work) in self._active
        if not self._confirm2(
            self._t("c_cleanup"),
            self._t("cp_t1").format(work=work, n=len(sids)),
            self._t("cp_t2").format(work=work),
        ):
            return
        if is_active and not self._confirm2(
            self._t("active_warn_title"),
            self._t("active_warn"),
            self._t("keep_asking"),
        ):
            return
        wnorm = db_reader.normalize_directory(work)
        diffs = [
            p for s in sids
            if (p := v2_session.safe_diff_path(self.diff_dir, s)) is not None
        ]
        dest = self._do_backup("project", sids, [pid], [d for d in diffs if d.is_file()], self._workspace_files_for(wnorm))
        if dest is None:
            return
        con2 = self._rw()
        try:
            if not self._gates_ok(dest, con2, True):
                return
            v2_project.cleanup_project(
                con2, pid, self.diff_dir, self._workspace_files_for(wnorm),
                {s for _, s in self._tabs}, is_active, True,
            )
        finally:
            con2.close()
        self.refresh()
        self._refresh_backups()
        self.status.showMessage(self._t("deleted_is") + work)

    def _on_tab_changed(self, idx: int) -> None:
        if idx == 2:
            self._refresh_backups()

    def _backup_entries(self) -> list[tuple[Path, dict]]:
        try:
            dirs = sorted(self.backup_root.iterdir())
        except OSError:
            return []
        out = []
        for d in dirs:
            m = d / "manifest.json"
            if not d.is_dir() or not m.is_file():
                continue
            try:
                out.append((d, _json.loads(m.read_text(encoding="utf-8"))))
            except (OSError, ValueError):
                continue
        return out

    def _refresh_backups(self) -> None:
        self._bak_paths = []
        self.bak_list.clear()
        for d, m in self._backup_entries():
            ids = list(m.get("ids", [])) + list(m.get("project_ids", []))
            self._bak_paths.append(d)
            self.bak_list.addItem(f"{m.get('time', '?')} | {m.get('kind', '?')} | {len(ids)}건")
        if not self._bak_paths:
            self.bak_list.addItem(self._t("bak_empty"))

    def _sel_backup(self) -> Path | None:
        r = self.bak_list.currentRow()
        if 0 <= r < len(self._bak_paths):
            return self._bak_paths[r]
        return None

    def _run_restore_backup(self) -> None:
        d = self._sel_backup()
        if d is None:
            QMessageBox.information(self, self._t("bak_restore"), self._t("bak_none_sel"))
            return
        if self._lock_exists():
            QMessageBox.information(self, self._t("bak_restore"), self._t("lock_cant"))
            return
        if not self._confirm2(
            self._t("bak_restore"),
            self._t("br_t1").format(name=d.name),
            self._t("br_t2").format(name=d.name),
        ):
            return
        con = self._rw()
        try:
            gates = v2_safety.check_all(
                self._lock_exists(), v2_backup.verify_files(d),
                self._trash_available(), True, True,
                (d / "manifest.json").is_file(),
            )
            bad = [g for g in gates if not g.passed]
            if bad:
                QMessageBox.information(
                    self, self._t("bak_restore"), " / ".join(g.message for g in bad)
                )
                return
            v2_backup.restore(d, con)
            ok = v2_backup.verify(d, con)
        finally:
            con.close()
        self.refresh()
        self._refresh_backups()
        self.status.showMessage(f"{self._t('restored_is')}{d.name} ({self._t('diag_ok') if ok else self._t('query_fail')})")

    def _run_delete_backup(self) -> None:
        d = self._sel_backup()
        if d is None:
            QMessageBox.information(self, self._t("bak_delete"), self._t("bak_none_sel"))
            return
        if not self._confirm2(
            self._t("bak_delete"),
            self._t("bd_t1").format(name=d.name),
            self._t("bd_t2").format(name=d.name),
        ):
            return
        v2_safety.move_to_trash([d])
        self._refresh_backups()
        self.status.showMessage(self._t("bak_deleted_is") + d.name)

    def _toggle_panel(self, idx: int) -> None:
        w = self.split.widget(idx)
        if w.isVisible():
            self._split_saved = list(self.split.sizes())
            w.hide()
        else:
            w.show()
            if self._split_saved and sum(self._split_saved) > 0:
                self.split.setSizes(list(self._split_saved))
            else:
                total = sum(self.split.sizes()) or 800
                if idx == 0:
                    self.split.setSizes([300, total - 300])
                else:
                    self.split.setSizes([total - 500, 500])
        left_open = self.split.widget(0).isVisible()
        right_open = self.split.widget(1).isVisible()
        self.btn_fold_left.setText(self._t("fold_left") if left_open else self._t("unfold_left"))
        self.btn_fold_right.setText(self._t("fold_right") if right_open else self._t("unfold_right"))

    def _on_copy(self) -> None:
        rows = self.table.selectionModel().selectedRows() if self.table.selectionModel() else []
        text = ""
        if rows:
            sid = getattr(self, "_row_session", {}).get(rows[0].row(), "")
            text = sid
        else:
            w = self._selected_worktree()
            text = w or ""
        if text:
            QApplication.clipboard().setText(text)
            self.status.showMessage(self._t("ro_prefix") + self._t("copied") + text[:60])
        else:
            QMessageBox.information(self, self._t("copy_title"), self._t("copy_none"))


def main() -> None:
    app = QApplication(sys.argv)
    win = MainWindow()
    win.resize(900, 600)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
