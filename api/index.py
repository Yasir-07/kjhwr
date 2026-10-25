import sys
from pathlib import Path

# The backend package lives in backend/, so make it importable from the repo root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.main import app  # noqa: E402,F401
