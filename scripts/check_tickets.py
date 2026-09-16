"""Run the offline ticket tests and validate the repository's ticket records."""

from pathlib import Path
import subprocess
import sys


def main():
    root = Path(__file__).resolve().parents[1]
    commands = [
        [sys.executable, "-m", "unittest", "discover", "-s", "scripts/tests"],
        [sys.executable, "scripts/tickets.py", "check"],
    ]
    for command in commands:
        result = subprocess.run(command, cwd=root, check=False)
        if result.returncode:
            return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
