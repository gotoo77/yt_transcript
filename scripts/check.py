"""Run the same quality gates locally and from DevMenu."""

import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    for arguments in (
        ["ruff", "check", "."],
        ["ruff", "format", "--check", "."],
        ["mypy"],
        ["pytest", "--cov", "--cov-report=term-missing"],
    ):
        result = subprocess.run([sys.executable, "-m", *arguments], cwd=root, check=False)
        if result.returncode:
            return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
