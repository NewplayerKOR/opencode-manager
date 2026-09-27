"""UI strings for KO/EN/JA/ZH. JA/ZH entries are intentional UI text.

Rule keys map to per-language text. Finding templates take {n}.
"""
from __future__ import annotations

LANGS = ("ko", "en", "ja", "zh")

NAMES = {"ko": "한국어", "en": "English", "ja": "日本語", "zh": "中文"}

STRINGS: dict[str, dict[str, str]] = {
    "tab_main": {"ko": "메인", "en": "Main", "ja": "メイン", "zh": "主页"},
    "tab_settings": {"ko": "설정", "en": "Settings", "ja": "設定", "zh": "设置"},
    "tab_backup": {"ko": "백업", "en": "Backups", "ja": "バックアップ", "zh": "备份"},
    "bak_restore": {"ko": "복원", "en": "Restore", "ja": "復元", "zh": "恢复"},
    "bak_delete": {"ko": "백업 삭제", "en": "Delete backup", "ja": "バックアップ削除", "zh": "删除备份"},
    "bak_refresh": {"ko": "목록 새로고침", "en": "Refresh list", "ja": "一覧更新", "zh": "刷新列表"},
    "bak_empty": {"ko": "백업이 없습니다.", "en": "No backups.", "ja": "バックアップがありません。", "zh": "无备份。"},
    "bak_none_sel": {"ko": "백업을 먼저 선택하세요.", "en": "Select a backup first.", "ja": "先にバックアップを選択してください。", "zh": "请先选择备份。"},
    "br_t1": {"ko": "{name} 복원: DB 행 되돌리기.", "en": "Restore {name}: roll back DB rows.", "ja": "{name} 復元: DB行を戻します。", "zh": "恢复 {name}: 回滚数据库行。"},
    "br_t2": {"ko": "{name} 정말 복원합니까?", "en": "Really restore {name}?", "ja": "本当に{name}を復元しますか?", "zh": "真的恢复 {name} 吗?"},
    "bd_t1": {"ko": "{name} 삭제: OS 휴지통으로 이동, 휴지통 비우기 전까지 복원 가능.", "en": "Delete {name}: moves to OS trash, restorable until emptied.", "ja": "{name} 削除: OSごみ箱へ移動、空にするまで復元可能。", "zh": "删除 {name}: 移入系统回收站，清空前可恢复。"},
    "bd_t2": {"ko": "{name} 백업을 삭제합니까?", "en": "Delete backup {name}?", "ja": "{name} のバックアップを削除しますか?", "zh": "删除备份 {name} 吗?"},
    "restored_is": {"ko": "복원됨: ", "en": "Restored: ", "ja": "復元済み: ", "zh": "已恢复: "},
    "bak_deleted_is": {"ko": "백업 삭제됨: ", "en": "Backup deleted: ", "ja": "バックアップ削除済み: ", "zh": "备份已删除: "},
    "tree_header": {"ko": "프로젝트 (활성/비활성)", "en": "Projects (active/inactive)", "ja": "プロジェクト (有効/無効)", "zh": "项目 (启用/停用)"},
    "grp_active": {"ko": "활성", "en": "Active", "ja": "有効", "zh": "启用"},
    "grp_inactive": {"ko": "비활성", "en": "Inactive", "ja": "無効", "zh": "停用"},
    "col_mark": {"ko": "표시", "en": "Mark", "ja": "表示", "zh": "标记"},
    "col_session": {"ko": "세션명", "en": "Session", "ja": "セッション名", "zh": "会话名"},
    "col_message": {"ko": "메시지", "en": "Messages", "ja": "メッセージ", "zh": "消息"},
    "refresh": {"ko": "새로고침", "en": "Refresh", "ja": "更新", "zh": "刷新"},
    "copy": {"ko": "복사", "en": "Copy", "ja": "コピー", "zh": "复制"},
    "archive": {"ko": "세션 보관", "en": "Archive session", "ja": "セッション保管", "zh": "归档会话"},
    "delete": {"ko": "세션 삭제", "en": "Delete session", "ja": "セッション削除", "zh": "删除会话"},
    "cleanup": {"ko": "프로젝트 삭제", "en": "Delete project", "ja": "プロジェクト削除", "zh": "删除项目"},
    "v2row": {"ko": "V2 정리 (조건 통과 시에만 동작):", "en": "V2 actions (only when conditions pass):", "ja": "V2操作 (条件通過時のみ動作):", "zh": "V2 操作 (仅在条件通过时执行):"},
    "fold_left": {"ko": "◀ 접기", "en": "◀ Fold", "ja": "◀ 折りたたみ", "zh": "◀ 折叠"},
    "unfold_left": {"ko": "펼치기 ▶", "en": "Unfold ▶", "ja": "展開 ▶", "zh": "展开 ▶"},
    "fold_right": {"ko": "접기 ▶", "en": "Fold ▶", "ja": "折りたたみ ▶", "zh": "折叠 ▶"},
    "unfold_right": {"ko": "◀ 펼치기", "en": "◀ Unfold", "ja": "◀ 展開", "zh": "◀ 展开"},
    "theme_to_dark": {"ko": "테마: 다크", "en": "Theme: Dark", "ja": "テーマ: ダーク", "zh": "主题: 深色"},
    "theme_to_light": {"ko": "테마: 라이트", "en": "Theme: Light", "ja": "テーマ: ライト", "zh": "主题: 浅色"},
    "theme_light": {"ko": "라이트", "en": "Light", "ja": "ライト", "zh": "浅色"},
    "theme_dark": {"ko": "다크", "en": "Dark", "ja": "ダーク", "zh": "深色"},
    "font_tip": {"ko": "글꼴 선택 (시스템 폰트)", "en": "Font (system fonts)", "ja": "フォント選択", "zh": "选择字体"},
    "set_language": {"ko": "언어", "en": "Language", "ja": "言語", "zh": "语言"},
    "set_theme": {"ko": "테마", "en": "Theme", "ja": "テーマ", "zh": "主题"},
    "set_font": {"ko": "글꼴", "en": "Font", "ja": "フォント", "zh": "字体"},
    "set_size": {"ko": "글자 크기", "en": "Font size", "ja": "文字サイズ", "zh": "字号"},
    "select_session": {"ko": "세션을 선택하세요.", "en": "Select a session.", "ja": "セッションを選択してください。", "zh": "请选择会话。"},
    "empty_project": {"ko": "이 프로젝트의 조회 결과 0건 (DB 잠금 여부 확인)", "en": "0 results for this project (check DB lock)", "ja": "このプロジェクトの結果は0件 (DBロックを確認)", "zh": "此项目无结果 (请检查数据库锁定)"},
    "diag_prefix": {"ko": "진단:", "en": "Diagnosis:", "ja": "診断:", "zh": "诊断:"},
    "diag_ok": {"ko": "이상 의심 없음", "en": "No issues suspected", "ja": "異常の疑いなし", "zh": "未发现异常"},
    "tip_locked": {"ko": "Opencode Desktop이 켜져 있거나 표시판이 남아 있어 동작 불가. Opencode Desktop 종료 여부를 직접 확인하세요.", "en": "Blocked: Opencode Desktop may be running or its lock file remains. Check it manually.", "ja": "ブロック中: Opencode Desktopが実行中か、ロックが残っています。手動で確認してください。", "zh": "已阻止: Opencode Desktop 可能正在运行或残留锁定文件，请手动确认。"},
    "tip_noselect": {"ko": "대상을 먼저 선택하세요.", "en": "Select a target first.", "ja": "先に対象を選択してください。", "zh": "请先选择目标。"},
    "tip_ready": {"ko": "조건 확인 후 동작합니다.", "en": "Runs after condition check.", "ja": "条件確認後に動作します。", "zh": "条件确认后执行。"},
    "gate_title": {"ko": "게이트", "en": "Gate", "ja": "ゲート", "zh": "门禁"},
    "copy_title": {"ko": "복사", "en": "Copy", "ja": "コピー", "zh": "复制"},
    "copy_none": {"ko": "복사할 항목을 선택하세요.", "en": "Select an item to copy.", "ja": "コピーする項目を選択してください。", "zh": "请选择要复制的项目。"},
    "copied": {"ko": "복사됨: ", "en": "Copied: ", "ja": "コピー済み: ", "zh": "已复制: "},
    "backup_title": {"ko": "백업", "en": "Backup", "ja": "バックアップ", "zh": "备份"},
    "archived_is": {"ko": "보관됨: ", "en": "Archived: ", "ja": "保管済み: ", "zh": "已归档: "},
    "unit_sessions": {"ko": "건", "en": " sessions", "ja": "件", "zh": " 项"},
    "dash_t": {"ko": "대시보드: DB {mb}MB ({b}B) | 세션 {s}건 | 활성 {a} / 비활성 {ia}", "en": "Dashboard: DB {mb}MB ({b}B) | {s} sessions | active {a} / inactive {ia}", "ja": "ダッシュボード: DB {mb}MB ({b}B) | セッション{s}件 | 有効{a} / 無効{ia}", "zh": "仪表板: DB {mb}MB ({b}B) | 会话{s}项 | 启用{a} / 停用{ia}"},
    "dash_prefix": {"ko": "대시보드: ", "en": "Dashboard: ", "ja": "ダッシュボード: ", "zh": "仪表板: "},
    "lock_guidance": {"ko": "DB가 잠겨 있습니다. Opencode Desktop 종료 후 새로고침 하세요.", "en": "DB is locked. Quit Opencode Desktop and refresh.", "ja": "DBがロックされています。Opencode Desktop終了後に更新してください。", "zh": "数据库已锁定，请退出 Opencode Desktop 后刷新。"},
    "lock_cant": {"ko": "잠금 표시판이 있어 삭제할 수 없습니다.", "en": "Blocked by lock marker; cannot delete.", "ja": "ロック表示があるため削除できません。", "zh": "存在锁定标记，无法删除。"},
    "dl_title": {"ko": "제목", "en": "Title", "ja": "タイトル", "zh": "标题"},
    "dl_path": {"ko": "경로", "en": "Path", "ja": "パス", "zh": "路径"},
    "dl_norm": {"ko": "정규화", "en": "Normalized", "ja": "正規化", "zh": "规范化"},
    "dl_created": {"ko": "생성", "en": "Created", "ja": "作成", "zh": "创建"},
    "dl_updated": {"ko": "수정", "en": "Updated", "ja": "更新", "zh": "修改"},
    "dl_messages": {"ko": "메시지", "en": "Messages", "ja": "メッセージ", "zh": "消息"},
    "dl_diff": {"ko": "diff", "en": "diff", "ja": "diff", "zh": "diff"},
    "dl_yes": {"ko": "있음", "en": "yes", "ja": "あり", "zh": "有"},
    "dl_no": {"ko": "없음", "en": "none", "ja": "なし", "zh": "无"},
    "unc_badge": {"ko": " (UNC/WSL 배지)", "en": " (UNC/WSL badge)", "ja": " (UNC/WSLバッジ)", "zh": " (UNC/WSL 标记)"},
    "ca_t1": {"ko": "{sid} 보관: 목록에서 숨김, 복원 가능.", "en": "Archive {sid}: hide from list, restorable.", "ja": "{sid} 保管: 一覧から非表示、復元可能。", "zh": "归档 {sid}: 从列表隐藏，可恢复。"},
    "ca_t2": {"ko": "{sid} 보관 확정합니까?", "en": "Confirm archiving {sid}?", "ja": "{sid} の保管を確定しますか?", "zh": "确认归档 {sid} 吗?"},
    "cd_t1": {"ko": "{sid} 삭제: 메시지·diff 함께 휴지통 이동.", "en": "Delete {sid}: messages and diff move to trash.", "ja": "{sid} 削除: メッセージ・diffをごみ箱へ移動。", "zh": "删除 {sid}: 消息与 diff 移入回收站。"},
    "cd_t2": {"ko": "{sid} 정말 삭제합니까? 휴지통으로 이동됩니다.", "en": "Really delete {sid}? It moves to trash.", "ja": "本当に{sid}を削除しますか? ごみ箱へ移動します。", "zh": "真的删除 {sid} 吗? 将移入回收站。"},
    "cp_t1": {"ko": "{work} 영향: 세션 {n}건 통째 삭제.", "en": "{work} impact: delete {n} session(s) with project.", "ja": "{work} 影響: セッション{n}件をまとめて削除。", "zh": "{work} 影响: 连同 {n} 个会话一起删除。"},
    "cp_t2": {"ko": "{work} 정말 삭제합니까? 휴지통으로 이동됩니다.", "en": "Really delete {work}? It moves to trash.", "ja": "本当に{work}を削除しますか? ごみ箱へ移動します。", "zh": "真的删除 {work} 吗? 将移入回收站。"},
    "deleted_is": {"ko": "삭제됨: ", "en": "Deleted: ", "ja": "削除済み: ", "zh": "已删除: "},
    "no_warn": {"ko": "경고 없음", "en": "no warnings", "ja": "警告なし", "zh": "无警告"},
    "query_fail": {"ko": "조회 실패. 새로고침 하세요.", "en": "Query failed. Refresh.", "ja": "取得失敗。再更新してください。", "zh": "查询失败，请刷新。"},
    "ro_prefix": {"ko": "읽기전용 | ", "en": "Read-only | ", "ja": "読取専用 | ", "zh": "只读 | "},
    "refreshed_at": {"ko": "마지막 새로고침 ", "en": "Last refresh ", "ja": "最終更新 ", "zh": "上次刷新 "},
    "dash_before": {"ko": "대시보드: 조회 전", "en": "Dashboard: not loaded", "ja": "ダッシュボード: 未取得", "zh": "仪表板: 未加载"},
    "global_fail": {"ko": " | 전역 상태 조회 실패", "en": " | global state unreadable", "ja": " | グローバル状態取得失敗", "zh": " | 全局状态读取失败"},
    "c_archive": {"ko": "세션 보관", "en": "Archive session", "ja": "セッション保管", "zh": "归档会话"},
    "c_delete": {"ko": "세션 삭제", "en": "Delete session", "ja": "セッション削除", "zh": "删除会话"},
    "c_cleanup": {"ko": "프로젝트 삭제", "en": "Delete project", "ja": "プロジェクト削除", "zh": "删除项目"},
    "active_warn": {"ko": "Opencode Desktop에서 보이는 활성 프로젝트입니다. 통째 삭제하면 목록에서 사라집니다.", "en": "This is an active project visible in Opencode Desktop. Deleting removes it from the list.", "ja": "Opencode Desktopに表示中の有効なプロジェクトです。削除すると一覧から消えます。", "zh": "这是在 Opencode Desktop 中显示的启用项目，删除后将从列表消失。"},
    "active_warn_title": {"ko": "활성 경고", "en": "Active warning", "ja": "有効警告", "zh": "启用警告"},
    "keep_asking": {"ko": "계속합니까?", "en": "Continue?", "ja": "続けますか?", "zh": "继续吗?"},
    "global_no": {"ko": "global 프로젝트는 삭제 대상이 아닙니다.", "en": "The global project cannot be deleted.", "ja": "globalプロジェクトは削除対象外です。", "zh": "global 项目不可删除。"},
    "no_db_row": {"ko": "DB 프로젝트 행이 없어 정리할 수 없습니다.", "en": "No DB project row; cannot proceed.", "ja": "DBプロジェクト行がないため続行できません。", "zh": "无数据库项目行，无法继续。"},
    "r01": {"ko": "Opencode Desktop 목록에 없는 옛 화면 파일 의심 {n}건. 지우지 말고 백업을 먼저 하세요.", "en": "{n} old UI file(s) suspected missing from the Opencode Desktop list. Back up first, do not delete.", "ja": "Opencode Desktop一覧にない旧画面ファイルの疑い {n}件。削除せず先にバックアップしてください。", "zh": "疑似有 {n} 个旧界面文件不在 Opencode Desktop 列表中，请先备份，不要删除。"},
    "r02": {"ko": "DB와 Opencode Desktop 목록의 폴더명이 서로 달라 보이는 것 {n}건. DB 용량 차지 중: 불필요하면 V2 삭제, 필요하면 Opencode Desktop에서 다시 여세요.", "en": "{n} folder name(s) look different between DB and Opencode Desktop list, taking DB space. Delete via V2 if unneeded, or reopen in Opencode Desktop.", "ja": "DBとOpencode Desktop一覧でフォルダ名が異なる疑い {n}件。DB容量を使用中: 不要ならV2削除、必要ならOpencode Desktopで開き直してください。", "zh": "数据库与 Opencode Desktop 列表中有 {n} 个文件夹名疑似不一致，占用数据库空间。不需要请用 V2 删除，需要请在 Opencode Desktop 中重新打开。"},
    "r03": {"ko": "Opencode Desktop 실행 중이거나 잔류 파일일 수 있습니다. 삭제하지 말고 종료 여부를 확인하세요.", "en": "Opencode Desktop may be running or a leftover file may remain. Do not delete; check shutdown.", "ja": "Opencode Desktop実行中か、残留ファイルの可能性があります。削除せず終了を確認してください。", "zh": "Opencode Desktop 可能正在运行或有残留文件，请勿删除，先确认是否已退出。"},
    "r04": {"ko": "WAL이 50MB 이상으로 주의 수준. Opencode Desktop 종료 후 재확인하세요.", "en": "WAL over 50MB (caution). Recheck after quitting Opencode Desktop.", "ja": "WALが50MB以上で注意水準。Opencode Desktop終了後に再確認してください。", "zh": "WAL 超过 50MB (注意)。退出 Opencode Desktop 后重新确认。"},
    "r05": {"ko": "상태 파일 읽기 실패 의심 {n}건. 파일을 건드리지 말고 백업 가이드를 참조하세요.", "en": "{n} state file(s) suspected unreadable. Do not touch files; see the backup guide.", "ja": "状態ファイル読込失敗の疑い {n}件。ファイルに触れずバックアップ案内を参照してください。", "zh": "疑似有 {n} 个状态文件读取失败，请勿触碰文件，参考备份指南。"},
}

FINDING_KEYS = {"R01": "r01", "R02": "r02", "R03": "r03", "R04": "r04", "R05": "r05"}


def tr(key: str, lang: str) -> str:
    lang = lang if lang in LANGS else "ko"
    return STRINGS.get(key, {}).get(lang, STRINGS.get(key, {}).get("ko", key))


def finding_text(fid: str, n: int, lang: str) -> str:
    return tr(FINDING_KEYS.get(fid, fid), lang).format(n=n)
