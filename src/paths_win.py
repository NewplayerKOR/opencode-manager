"""Windows data locations (D01-D08). Read-only helpers only, no writes."""
from __future__ import annotations

import os
from pathlib import Path


def _env_path(var: str, rest: str) -> Path:
    base = os.environ.get(var, "")
    return Path(base) / Path(rest) if base else Path(rest)


# D01 session DB (+WAL/-shm are beside it, never touched)
OPENCODE_DB = _env_path("USERPROFILE", ".local/share/opencode/opencode.db")
# D02 session diff / D03 migration
SESSION_DIFF_DIR = _env_path("USERPROFILE", ".local/share/opencode/storage/session_diff")
MIGRATION_PATH = _env_path("USERPROFILE", ".local/share/opencode/storage/migration")
# D04 global state / D05 workspace states
GLOBAL_DAT = _env_path("APPDATA", "ai.opencode.desktop/opencode.global.dat")
WORKSPACE_GLOB = "opencode.workspace.*.dat"
WORKSPACE_DIR = _env_path("APPDATA", "ai.opencode.desktop")
# D06 drafts / D07 global config / D08 lockfile
DRAFTS_SQLITE = _env_path("APPDATA", "ai.opencode.desktop/drafts.sqlite")
GLOBAL_CONFIG = _env_path("USERPROFILE", ".config/opencode/opencode.jsonc")
LOCKFILE = _env_path("APPDATA", "ai.opencode.desktop/lockfile")

# macOS/Linux (reserved, unused in V1):
# ~/.local/share/opencode/opencode.db
# ~/.config/ai.opencode.desktop/...

LOCATIONS: dict[str, Path] = {
    "D01": OPENCODE_DB,
    "D02": SESSION_DIFF_DIR,
    "D03": MIGRATION_PATH,
    "D04": GLOBAL_DAT,
    "D05": WORKSPACE_DIR,
    "D06": DRAFTS_SQLITE,
    "D07": GLOBAL_CONFIG,
    "D08": LOCKFILE,
}


def resolve_all() -> dict[str, Path]:
    """Return id -> path mapping (caller checks existence, never raises)."""
    return dict(LOCATIONS)


def file_size(p: Path) -> int | None:
    """Read-only size probe. Returns None when missing/unreadable."""
    try:
        return p.stat().st_size
    except OSError:
        return None
