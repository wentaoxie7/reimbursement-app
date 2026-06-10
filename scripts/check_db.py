"""Run from project root: python scripts/check_db.py (uses backend/.venv if present)"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
SCRIPT = BACKEND / "scripts" / "check_db.py"

if not SCRIPT.is_file():
    print(f"Missing {SCRIPT}")
    sys.exit(1)

venv_python = BACKEND / ".venv" / "Scripts" / "python.exe"
python = str(venv_python) if venv_python.is_file() else sys.executable

raise SystemExit(subprocess.call([python, str(SCRIPT)], cwd=BACKEND))
