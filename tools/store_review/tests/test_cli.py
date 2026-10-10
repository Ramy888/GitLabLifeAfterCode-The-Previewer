import subprocess
import sys


def test_help_lists_commands():
    out = subprocess.run([sys.executable, "-m", "store_review", "--help"], capture_output=True, text=True)
    assert out.returncode == 0
    for cmd in ("scan", "merge", "handoff", "validate-inputs", "package", "benchmark"):
        assert cmd in out.stdout
