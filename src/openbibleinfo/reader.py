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
        # add PassageLength and UsableRange
        self.df["PassageLength"] = self.df.apply(lambda row: self.passagelen(row.StartVerseId, row.EndVerseId), axis=1)
        self.df["UsableRange"] = self.df.apply(self.usablerange, axis=1)
        self.df["UsableReference"] = (self.df.PassageLength == 1) | self.df.UsableRange
        # drop records with cross-chapter/book ranges
        self.topicsdf = self.df[self.df.UsableReference]
        self.toptopics = self.top_topics()

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

    def passage_probability(self, row) -> float:
        """Return the percentage of this row's votes for the whole topic.

        Only computable given self.toptopics.
        """
        if not row.UsableReference:
            return 0.0
        elif not self.toptopics.Topic.str.contains(row.Topic).any():
            return 0.0
        else:
            rowtopic = self.toptopics[self.toptopics.Topic == row.Topic]
            if rowtopic.empty:
                return 0.0
            else:
                votesum = int(rowtopic.TopicVotesSum.iloc[0])
                if not votesum:
                    return 0.0
                else:
                    votes = int(row.Votes)
                    return votes / votesum

    def top_topics(self, threshold: int = 55) -> pd.DataFrame:
        """Return topics whose MeanPassageVotes exceed threshold."""

        topicsdf = pd.DataFrame(self.topicsdf.Topic.value_counts()).reset_index()
        topicsdf.columns = ["Topic", "TopicPassageCount"]
        passagecountdf = self.topicsdf.pivot_table(index="Topic", aggfunc="count", values="StartVerseId").reset_index()
        passagecountdf.columns = ["Topic", "TopicPassageCount"]
        topicvotessum = self.topicsdf.pivot_table(index="Topic", aggfunc="sum", values=["Votes"]).reset_index()
        topicvotessum.columns = ["Topic2", "TopicVotesSum"]
        topicsdf = pd.concat([passagecountdf, topicvotessum], axis="columns").drop("Topic2", axis="columns")
        topicsdf["MeanPassageVotes"] = topicsdf.TopicVotesSum / topicsdf.TopicPassageCount
        return topicsdf[topicsdf.MeanPassageVotes > threshold].sort_values("MeanPassageVotes", ascending=False)
