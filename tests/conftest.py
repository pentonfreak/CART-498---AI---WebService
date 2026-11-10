"""Allow both `pytest` and `python -m pytest` from project root."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
