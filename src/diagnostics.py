"""F04 diagnostic rules R01-R05. Pure data in/out; no I/O, no writes.

All findings are "suspicion" level with guidance text. No red, no fixes.
Caller (main.py) supplies inventory data gathered with T08 helpers.
"""
from __future__ import annotations

import base64
import re
from dataclasses import dataclass

WAL_WARN_BYTES = 50 * 1024 * 1024


@dataclass
class Finding:
    id: str
    message: str
    color: str  # "orange" (caution) or "gray" (info)
    n: int = 0
    targets: tuple = ()  # up to 3 names/paths for display


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.casefold())


def _b64frag(token: str) -> str:
    """Decode a truncated base64 filename token to a path fragment."""
    pad = "=" * (-len(token) % 4)
    try:
        return base64.b64decode(token + pad).decode("utf-8", errors="strict")
    except Exception:
        return ""


def workspace_indexed(name: str, indexed_norm: set[str], normalize) -> bool:
    """True when a workspace filename maps to a known worktree.

    New-style names carry a base64 path prefix, old-style names a slug
    prefix. Either direction prefix match counts ("suspicion" level).
    """
    stem = name
    if stem.startswith("opencode.workspace."):
        stem = stem[len("opencode.workspace.") :]
    if stem.endswith(".dat"):
        stem = stem[: -len(".dat")]
    for tok in stem.split("."):
        if len(tok) < 4:
            continue
        ts = _slug(tok)
        if ts and any(
            _slug(p).startswith(ts) or ts.startswith(_slug(p)) for p in indexed_norm
        ):
            return True
        frag = _b64frag(tok)
        if len(frag) >= 4:
            fn = normalize(frag)
            if any(p.startswith(fn) or fn.startswith(p) for p in indexed_norm):
                return True
    return False


def evaluate(
    active_raw: list[str],
    tabs_raw: list[tuple[str, str]],
    workspace_names: list[str],
    db_dirs_norm: set[str],
    lock_exists: bool,
    wal_bytes: int | None,
    dat_bad: list[str],
    normalize,
    ws_sessions: dict[str, bool] | None = None,
) -> list[Finding]:
    """Evaluate R01-R05 against plain data. `normalize` is the T08 helper.

    R01 fires only for orphans holding session keys (empty shells stay
    silent). `ws_sessions` maps filename -> session-key presence; when it
    is None every orphan fires (legacy behavior).
    """
    out: list[Finding] = []
    indexed = {normalize(w) for w in active_raw}
    indexed |= {normalize(w) for w, _s in tabs_raw}
    active = {normalize(w) for w in active_raw}

    orphans = [n for n in workspace_names if not workspace_indexed(n, indexed, normalize)]
    if ws_sessions is not None:
        orphans = [n for n in orphans if ws_sessions.get(n, True)]
    if orphans:
        out.append(
            Finding(
                "R01",
                f"Opencode Desktop 목록에 없는 옛 화면 파일 의심 {len(orphans)}건."
                " 지우지 말고 백업을 먼저 하세요.",
                "orange",
                n=len(orphans),
                targets=tuple(orphans[:3]),
            )
        )

    stale = sorted(d for d in db_dirs_norm if d not in active)
    if stale:
        out.append(
            Finding(
                "R02",
                f"DB와 Opencode Desktop 목록의 폴더명이 서로 달라 보이는 것 {len(stale)}건."
                " DB 용량 차지 중: 불필요하면 V2 삭제, 필요하면 Opencode Desktop에서 다시 여세요.",
                "orange",
                n=len(stale),
                targets=tuple(stale[:3]),
            )
        )

    if lock_exists:
        out.append(
            Finding(
                "R03",
                "Opencode Desktop 실행 중이거나 잔류 파일일 수 있습니다."
                " 삭제하지 말고 종료 여부를 확인하세요.",
                "gray",
                n=1,
            )
        )

    if wal_bytes is not None and wal_bytes >= WAL_WARN_BYTES:
        out.append(
            Finding(
                "R04",
                "WAL이 50MB 이상으로 주의 수준. Opencode Desktop 종료 후 재확인하세요.",
                "orange",
                n=1,
            )
        )

    if dat_bad:
        out.append(
            Finding(
                "R05",
                f"상태 파일 읽기 실패 의심 {len(dat_bad)}건."
                " 파일을 건드리지 말고 백업 가이드를 참조하세요.",
                "orange",
                n=len(dat_bad),
                targets=tuple(dat_bad[:3]),
            )
        )
    return out
