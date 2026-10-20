import os
from pathlib import Path
import subprocess
import tempfile
import time
import unittest

GUARD = Path(__file__).resolve().parents[1] / "deploy" / "omc-scratch-guard"
OLD = time.time() - 10 * 86400


def make(path, old=True):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("x")
    if old:
        os.utime(path, (OLD, OLD))


class ScratchGuardTest(unittest.TestCase):
    def run_guard(self, root, used):
        env = dict(os.environ, SCRATCH_ROOT=str(root), FAKE_USED_PCT=str(used),
                   GUARD_LOCK=str(root.parent / "guard.lock"))
        return subprocess.run([str(GUARD)], env=env, capture_output=True, text=True)

    def test_enough_space_removes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "scratch"
            make(root / "stale" / "a.bin")
            result = self.run_guard(root, 70)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("ok used_pct=70", result.stdout)
            self.assertTrue((root / "stale").exists())

    def test_low_space_removes_only_idle_unprotected_units(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "scratch"
            make(root / "stale" / "deep" / "a.bin")
            make(root / "fresh" / "old.bin")
            make(root / "fresh" / "new.bin", old=False)
            make(root / "py-venv" / "lib.py")
            make(root / "claude-1001" / "-old-project" / "x.txt")
            make(root / "claude-1001" / "-live-project" / "y.txt", old=False)
            readonly = root / "gomod" / "pkg" / "go.mod"
            make(readonly)
            readonly.chmod(0o444)
            readonly.parent.chmod(0o555)
            held = root / "held" / "log.txt"
            make(held)
            locked = root / "locked" / "private"
            make(locked / "db.bin")
            locked.chmod(0o000)
            try:
                with open(held):
                    result = self.run_guard(root, 97)
            finally:
                locked.chmod(0o700)
            self.assertEqual(result.returncode, 3, result.stdout + result.stderr)
            self.assertIn("removed=3", result.stdout)
            for gone in ("stale", "gomod", "claude-1001/-old-project"):
                self.assertFalse((root / gone).exists(), gone)
            # An unreadable subtree cannot prove idleness, so its unit is kept.
            for kept in ("fresh", "py-venv", "held", "locked", "claude-1001/-live-project"):
                self.assertTrue((root / kept).exists(), kept)


if __name__ == "__main__":
    unittest.main()
