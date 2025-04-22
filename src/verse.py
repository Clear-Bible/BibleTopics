"""Define a container for Verse vote data."""

from dataclasses import dataclass
from typing import Optional

from biblelib.word.bcvwpid import BCVID, BCVIDRange


@dataclass
class Verse:
    startverseid: str
    endverseid: str = ""
    votes: int = 0
    passagelength: int = 0
    usablerange: bool = False
    votespercentage: float = 0.0
    # post_init
    startbcv: Optional[BCVID] = None
    endbcv: Optional[BCVID] = None
    bcvrange: Optional[BCVIDRange] = None
    # internal string for the reference
    usfmref: str = ""
    # user-displayable string for the reference
    userref: str = ""

    def __post_init__(self) -> None:
        """Compute values after initialization."""
        self.startbcv = BCVID(self.startverseid)
        if self.endverseid:
            self.endbcv = BCVID(self.endverseid)
            self.bcvrange = BCVIDRange(startid=self.startbcv, endid=self.endbcv)
        if self.bcvrange:
            self.usfmref = self.bcvrange.to_usfm()
            self.userref = self.bcvrange.to_nameref()
        else:
            self.usfmref = self.startbcv.to_usfm()
            self.userref = self.startbcv.to_nameref()

    def __repr__(self) -> str:
        """Return a printed representation."""
        return f"<Verse({self.usfmref}): {self.votespercentage:0.4}>"
