"""Read topic data.

>>> from src import reader
>>> rd = reader.Topics()
"""

from collections import UserDict
from csv import DictReader, DictWriter
from pathlib import Path

from src import DATAPATH
from .topic import Topic
from .verse import Verse


class Topics(UserDict):
    """Maps a topic label to a list of Verse instances."""

    fieldnames = (
        "Index",
        "Topic",
        "StartVerseId",
        "EndVerseId",
        "Votes",
        "PassageLength",
        "UsableRange",
        "VotesPercentage",
    )
    verseattrs = {
        "StartVerseId": "startverseid",
        "EndVerseId": "endverseid",
        "Votes": "votes",
        "PassageLength": "passagelength",
        "UsableRange": "usablerange",
        "VotesPercentage": "votespercentage",
    }

    def __init__(self, datapath: Path = (DATAPATH / "toptopictopversedata.tsv")) -> None:
        """Initialize a instance by reading data."""
        super().__init__(self)
        with datapath.open() as f:
            reader = DictReader(f, delimiter="\t")
            for row in reader:
                topic = row["Topic"]
                if topic not in self:
                    self[topic] = []
                versedict = {
                    verseattr: row[attr]
                    for attr in self.verseattrs
                    if (verseattr := self.verseattrs[attr])
                }
                versedict["passagelength"] = int(versedict["passagelength"])
                versedict["votes"] = int(versedict["votes"])
                versedict["usablerange"] = True if versedict["usablerange"] == "True" else False
                versedict["votespercentage"] = float(versedict["votespercentage"])
                self[topic].append(Verse(**versedict))
        # slug -> Topic
        self.topicsdict = {
            topicslug: topicinst
            for topic, verses in self.items()
            if (topicinst := Topic(topic=topic, verses=verses))
            if (topicslug := topicinst.topicslug)
        }

    def write_topics(self, datapath: Path = (DATAPATH / "topics.tsv")) -> None:
        """Write topics as TSV."""
        with datapath.open("w") as f:
            writer = DictWriter(f, fieldnames=("topic", "definition"), delimiter="\t")
            writer.writeheader()
            for topic in self.topicsdict:
                writer.writerow({"topic": topic, "definition": ""})
