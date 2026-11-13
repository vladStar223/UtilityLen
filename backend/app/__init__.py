"""UtilityLens backend application package."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
CASES_DIR = DATA_DIR / "cases"
