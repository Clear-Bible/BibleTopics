"""Internal code for working with Bible Topics."""

from pathlib import Path

ROOT = Path(__file__).parent.parent
DATAPATH = ROOT / "data"

__all__ = [
    "ROOT",
    "DATAPATH",
]
