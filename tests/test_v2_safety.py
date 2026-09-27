"""T18 gate tests on synthetic inputs only. No trash movement."""
import sys
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src import v2_safety  # noqa: E402


def _all_ok():
    return v2_safety.check_all(False, True, True, True, True, True)


def test_all_pass():
    gates = _all_ok()
    assert [g.id for g in gates] == ["S01", "S02", "S03", "S04", "S05"]
    assert v2_safety.all_passed(gates) is True


def test_each_gate_blocks():
    base = dict(lock_exists=False, backup_ok=True, trash_available=True,
                stage1_done=True, stage2_done=True, restore_ready=True)
    for key, val in [("lock_exists", True), ("backup_ok", False),
                     ("trash_available", False), ("stage2_done", False),
                     ("restore_ready", False)]:
        args = dict(base, **{key: val})
        gates = v2_safety.check_all(**args)
        assert v2_safety.all_passed(gates) is False
        bad = [g for g in gates if not g.passed]
        assert len(bad) == 1 and bad[0].message


def test_trash_wrapper_calls_send2trash():
    with mock.patch("send2trash.send2trash") as m:
        v2_safety.move_to_trash([Path("C:/x/y.json")])
        m.assert_called_once_with(str(Path("C:/x/y.json")))


def test_no_forbidden_helpers():
    src = Path(__file__).resolve().parents[1] / "src" / "v2_safety.py"
    text = src.read_text(encoding="utf-8")
    assert "kill" not in text.lower()
    assert "taskkill" not in text.lower()
