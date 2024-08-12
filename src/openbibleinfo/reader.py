"""Read TSV data into a dataframe for further analysis."""

from functools import lru_cache
from pathlib import Path

import pandas as pd

from biblelib.word.bcvwpid import BCVID, BCVIDRange

from src import DATAPATH


class Reader:
    """Read TSV data into a dataframe."""

    votescolumns = ("Topic", "StartVerseId", "EndVerseId", "Votes")
    votesdtypes = {
        "Topic": "string",
        "StartVerseId": "string",
        "EndVerseId": "string",
        "Votes": "int",
    }

    def __init__(self, datapath: Path = DATAPATH / "OpenBible.info/topic-votes.txt") -> None:
        """Initialize an instance."""
        self.df = pd.read_csv(
            datapath,
            delimiter="\t",
            header=0,
            names=self.votescolumns,
            usecols=self.votescolumns,
            dtype=self.votesdtypes,
        )

    def display_topic_data(self, topic: str) -> None:
        """Display verses and votes for a topic."""
        topicdf = self.df[self.df.Topic == topic]
        print(f"{len(topicdf)} verses with {topicdf.Votes.sum()} votes")
        print(topicdf)

    @staticmethod
    @lru_cache
    def passagelen(StartVerseId: str, EndVerseId: str, verbose: bool = False) -> int:
        """Convert IDs to BCV and return the length of the range.

        A single verse has a length of 1, unsurprisingly. Ranges
        across chapters are given an arbitrary length of 99 (i don't
        have code to compute those yet). Ranges across books are given
        an arbitrary length of 999.

        """
        if pd.isna(EndVerseId):
            return 1
        else:
            start = BCVID(StartVerseId)
            end = BCVID(EndVerseId)
            if start.book_ID != end.book_ID:
                if verbose:
                    print(f"Bad range {StartVerseId}, {EndVerseId}: returning 1")
                return 999
            if start.chapter_ID != end.chapter_ID:
                # arbitrarily large number
                return 99
            else:
                return len(BCVIDRange(start, end).enumerate())

    @staticmethod
    def usablerange(row) -> bool:
        """A range is usable if within the same chapter.

        Not usable if the end is in a different chapter or book.
        """
        if row.PassageLength == 99:
            return False
        elif row.PassageLength == 999:
            # this assumes you've run passagelen()
            return False
        elif pd.isna(row.EndVerseId):
            # not a range: single verse
            return False
        else:
            return True
