"""Direct mode must keep loading contracts pinned to the GenVM v0.2 SDK.

The v0.2 SDK lives under ``genlayer.py`` / ``genlayer.gl`` while v0.3 exposes
its modules at the package root, and both cannot share one interpreter, so the
cases run in a separate pytest process.
"""

import subprocess
import sys
from pathlib import Path

LEGACY_DIR = Path(__file__).parent / "legacy_v02"


def test_v02_contract_cases_pass():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-p",
            "no:cacheprovider",
            "-q",
            "--tb=short",
            str(LEGACY_DIR / "legacy_cases.py"),
        ],
        cwd=LEGACY_DIR,
        capture_output=True,
        text=True,
        timeout=600,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "5 passed" in result.stdout
