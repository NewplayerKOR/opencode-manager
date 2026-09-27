"""T10 F04 diagnostic rule tests on synthetic data only."""
import base64
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src import diagnostics  # noqa: E402
from src.db_reader import normalize_directory as norm  # noqa: E402

A = "C:\\Proj\\A"
B = "C:\\Proj\\Old"


def _new_style(worktree: str) -> str:
    tok = base64.b64encode(worktree.encode()).decode().rstrip("=")
    return f"opencode.workspace.{tok}.a1b2c3.dat"


def test_t06_reproduction():
    """T06 snapshot: R02 1건 + R03 발동, R01/R04/R05 미발동."""
    got = diagnostics.evaluate(
        [A],
        [(A, "ses_x")],
        [_new_style(A)],
        {norm(A), norm(B)},
        True,
        4 * 1024 * 1024,
        [],
        norm,
    )
    assert [f.id for f in got] == ["R02", "R03"]
    assert {f.color for f in got} == {"orange", "gray"}


def test_all_rules_fire():
    got = diagnostics.evaluate(
        [A],
        [],
        ["opencode.workspace.C--Old-Thing.zz99.dat"],
        {norm(B)},
        True,
        60 * 1024 * 1024,
        ["opencode.global.dat"],
        norm,
    )
    assert [f.id for f in got] == ["R01", "R02", "R03", "R04", "R05"]
    assert {f.color for f in got} <= {"orange", "gray"}
    assert all("확정" not in f.message for f in got)


def test_clean():
    got = diagnostics.evaluate(
        [A], [(A, "s")], [_new_style(A)], {norm(A)}, False, 1024, [], norm
    )
    assert got == []


def test_r01_empty_shell_silent():
    """T28: orphans without session keys do not fire."""
    got = diagnostics.evaluate(
        [A],
        [],
        ["opencode.workspace.C--Old-Thing.zz99.dat"],
        {norm(A)},
        False,
        1024,
        [],
        norm,
        ws_sessions={"opencode.workspace.C--Old-Thing.zz99.dat": False},
    )
    assert [f.id for f in got] == []
    got2 = diagnostics.evaluate(
        [A],
        [],
        ["opencode.workspace.C--Old-Thing.zz99.dat"],
        {norm(A)},
        False,
        1024,
        [],
        norm,
        ws_sessions={"opencode.workspace.C--Old-Thing.zz99.dat": True},
    )
    assert [f.id for f in got2] == ["R01"]
    assert got2[0].targets == ("opencode.workspace.C--Old-Thing.zz99.dat",)


def test_old_style_name_maps():
    assert (
        diagnostics.workspace_indexed(
            "opencode.workspace.C--Proj-A.qwerty.dat", {norm(A)}, norm
        )
        is True
    )
    assert (
        diagnostics.workspace_indexed(
            "opencode.workspace.C--Old-Thing.zz99.dat", {norm(A)}, norm
        )
        is False
    )
