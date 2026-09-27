"""`.dat` JSON read-only helpers. Key-level parsing only (T03)."""
from __future__ import annotations

import base64
import glob
import json
import os
from pathlib import Path

from .errors import DatMissing, DatParseFailed


def load_global(dat: Path) -> dict:
    try:
        text = dat.read_text(encoding="utf-8")
    except FileNotFoundError as e:
        raise DatMissing(str(dat)) from e
    except OSError as e:
        raise DatParseFailed(str(dat)) from e
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise DatParseFailed(str(dat)) from e


def _nested(obj: dict, key: str) -> dict:
    raw = obj.get(key, {})
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            v = json.loads(raw)
            return v if isinstance(v, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


def active_worktrees(g: dict) -> list[str]:
    srv = _nested(g, "server")
    proj = srv.get("projects", {}) if isinstance(srv, dict) else {}
    local = proj.get("local", []) if isinstance(proj, dict) else []
    out = []
    for item in local:
        w = item.get("worktree") if isinstance(item, dict) else None
        if w:
            out.append(w)
    return out


def recently_closed(g: dict) -> list[str]:
    srv = _nested(g, "server")
    rc = srv.get("recentlyClosed", {}) if isinstance(srv, dict) else {}
    local = rc.get("local", []) if isinstance(rc, dict) else []
    return [x for x in local if isinstance(x, str)]


def _b64_or_empty(token: str) -> str:
    pad = "=" * (-len(token) % 4)
    try:
        return base64.b64decode(token + pad).decode("utf-8", errors="strict")
    except Exception:
        return ""


def session_tabs(g: dict) -> list[tuple[str, str]]:
    lay = _nested(g, "layout")
    tabs = lay.get("sessionTabs", {}) if isinstance(lay, dict) else {}
    out: list[tuple[str, str]] = []
    if not isinstance(tabs, dict):
        return out
    for key in tabs:
        if "\x00" not in key or "/" not in key:
            continue
        _scope, rest = key.split("\x00", 1)
        token, _, ses = rest.partition("/")
        w = _b64_or_empty(token)
        if w and ses:
            out.append((w, ses))
    return out


def workspace_inventory(pattern: str) -> list[tuple[str, int]]:
    """(filename, size) listing only, no content parsing."""
    out: list[tuple[str, int]] = []
    for p in glob.glob(pattern):
        try:
            out.append((os.path.basename(p), os.path.getsize(p)))
        except OSError:
            continue
    return out
