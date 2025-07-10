#!/usr/bin/env python
"""
Run from the project root:

    python bootstrap_env.py
"""
from __future__ import annotations

import subprocess
import sys
import venv
from pathlib import Path

# ---------------------------------------------------------------------------
# 📦  Libraries required by the project so far
# ---------------------------------------------------------------------------
PACKAGES = [
    "SQLAlchemy>=2.0",   # ORM / DB
    "flask",             # Web framework
    "flask-restx",       # API + Swagger docs
    "tabulate",          # Pretty CLI tables (check_counts.py)
    "pytest",            # Unit‑testing
]


# ---------------------------------------------------------------------------
# Helper – create venv if it doesn't exist
# ---------------------------------------------------------------------------

def _ensure_venv(venv_dir: Path) -> None:
    if venv_dir.exists():
        print(f"✔︎ Virtual‑env already present: {venv_dir}")
        return
    print(f"Creating virtual‑env at {venv_dir} …")
    venv.create(venv_dir, with_pip=True, clear=False)


# ---------------------------------------------------------------------------
# Main routine
# ---------------------------------------------------------------------------

def main() -> None:
    root = Path(__file__).resolve().parent
    venv_dir = root / "venv"

    _ensure_venv(venv_dir)

    # Resolve the pip executable inside the venv (cross‑platform)
    pip = venv_dir / ("Scripts" if sys.platform.startswith("win") else "bin") / "pip"

    # Upgrade pip itself (quietly)
    subprocess.check_call([str(pip), "install", "--upgrade", "pip"])

    # Install / update required packages
    subprocess.check_call([str(pip), "install", *PACKAGES])

    # Friendly outro
    activate_cmd = (
        r".\venv\Scripts\activate" if sys.platform.startswith("win")
        else "source venv/bin/activate"
    )
    print("\n✅  Environment ready!  To start using it run:\n")
    print(f"    {activate_cmd}\n")
    print("Then launch your scripts, tests, or Flask API inside that shell.")


if __name__ == "__main__":
    main()
