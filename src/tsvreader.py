"""Generalized Reader for TSV data.

Subclass this, defining tsvpath, idattr, and model.
"""

from collections import UserDict
from csv import DictReader
from pathlib import Path
from typing import Any


class TSVReader(UserDict):
    """Read TSV data into a dict.

    This is generalized for use where the source data is in TSV, with
    column headers that match a BaseModel instance, and a designated
    identity element.

    """

    # subs must define these
    tsvpath: Path
    idattr: str
    model: Any

    def __init__(self) -> None:
        """Initialize a Reader instance."""
        super().__init__()
        assert self.tsvpath, "tsvpath must be defined"
        assert self.idattr, "idattr must be defined"
        assert self.model, "model must be defined"
        with self.tsvpath.open() as f:
            reader = DictReader(f, delimiter="\t")
            self.data = {
                idattr: self.model(**row) for row in reader if (idattr := row[self.idattr])
            }
