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
        self.topicvotesum = self.topic_vote_sum()


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

    def topic_vote_sum(self):
        """Return a DataFrame with summaries by topic."""
        # this returns other columns: i'm not sure why
        return self.topicsdf.groupby("Topic").sum("Votes")
        
    def passage_probability2(self, row) -> float:
        """Return the percentage of this row's votes for the whole topic.

        Only computable given self.toptopics. Attempting a faster approach.
        """
        if not row.UsableReference:
            return 0.0
        elif not self.toptopics.Topic.str.contains(row.Topic).any():
            return 0.0
        else:
            votesum = int(self.topicvotesum.loc[row.Topic].Votes)
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

    def consolidate_intersections(self, weight: float = 0.75) -> pd.Dataframe:
        """Return a new DataFrame that combines single verses with 2-verse ranges.

        Single verse votes are weighted according to weight and added
        to the votes for the range.

        """

        def intersects(rangetuple: pd.core.frame.Pandas, singletuple: pd.core.frame.Pandas) -> bool:
            """Return True if singletuple falls within rangetuple.

            Here 'within' simply means the single is the same as
            either start or end. This should only be applied to tuples
            with the same topic.

            """
            if rangetuple.UsableRange and (rangetuple.PassageLength == 2) and (singletuple.PassageLength == 1):
                return ((rangetuple.StartVerseId == singletuple.StartVerseId) or
                        (rangetuple.EndVerseId == singletuple.StartVerseId))
            else:
                return False

        # within rows for each topic
        #  ranges = (UsableRange == True)
        #  singles = (UsableRange == False)
        #  for each value in ranges:
        #    for each value in singles:
        #      if intersects(range, single):
        #        add range to new df with weighted votes from single
        #        remove single from singles so you don't process it again
        #  finally add remaining ranges and singles
        pass
