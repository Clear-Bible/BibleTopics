"""Write topic data in JSON format.

>>> from src import writer
# get the topics
>>> tw = writer.TopicWriter()
# write just the topics
>>> tw.write_topics(tw.topicdict)
# also write the text of references no longer than 3 verses
>>> tw.write_topics(tw.topicversetext)
# also write ChatGPT-generated summary of verse content
>>> tw.write_topics(tw.topicsummary)
"""

import jsonlines
from pathlib import Path
from typing import Callable

from biblelib.word.urlmanager import URLManager

from src import DATAPATH
from .reader import Topics
from .versetext import VerseTextReader
from .versesummary import VerseSummaryReader
from .topic import Topic
from .verse import Verse


class TopicWriter:
    """Write topic data for LLM training."""

    # these parameters might need to be changed
    urlmgr = URLManager(netloc="bible.com", edition="BSB")
    # where below the datadir the output should go
    subdir: str = "llm"
    topicreader: dict[str, list[Verse]] = Topics()
    topicsdict: dict[str, list[Verse]] = topicreader.topicsdict
    vtreader = VerseTextReader()
    vsreader = VerseSummaryReader()

    def __init__(self, outpath: Path = DATAPATH / subdir) -> None:
        """Initialize an instance."""
        outpath.mkdir(exist_ok=True)
        self.jsonoutpath = outpath / "jsonl"
        self.jsonoutpath.mkdir(exist_ok=True)

    def write_topics(self, datafn: Callable) -> None:
        """Write topic data. Supply a function to format triples."""
        filename = f"{datafn.__name__}.jsonl"
        outpath = self.jsonoutpath / filename
        with jsonlines.open(outpath, mode="w") as f:
            for topicslug in self.topicsdict:
                if topicslug in self.vsreader:
                    f.write(datafn(topicslug))

    def topicdict(self, topicslug: str) -> dict[str, str]:
        """Return a serializable dict of topic data."""
        topicinst: Topic = self.topicsdict[topicslug]
        topiclabel: str = topicinst.topic
        topicrefstr: str = topicinst.referencestr
        promptstr: str = f"What does the Bible say about the topic of '{topiclabel}'?"
        completionstr: str = f"These are some popular verses addressing {topiclabel}: {topicrefstr}"
        return {
            "prompt": promptstr,
            "completion": completionstr,
            "context": "",
            # "context": f"Respond drawing on the most Bible important verses for the topic {topiclabel}, and answer from a Christian perspective.",
        }

    def _render_verse(self, verse: Verse) -> str:
        """Return rendered verse reference and text."""
        return f"{verse.userref}: {self.vtreader[verse.usfmref]}"

    def _render_summary(self, topicslug: str) -> str:
        """Return rendered verse reference and text."""
        return self.vsreader[self.topicreader[topicslug]]

    def _render_versetext(self, topicslug: str, maxverselen: int = 3) -> str:
        """Return a block of rendered reference text."""
        topicinst: Topic = self.topicsdict[topicslug]
        # include text if not too many verses
        textrefstr: str = "\n".join(
            [
                self._render_verse(verse)
                for verse in topicinst.verses
                if verse.passagelength <= maxverselen
            ]
        )
        refstr: str = ", ".join(
            [verse.userref for verse in topicinst.verses if verse.passagelength > maxverselen]
        )
        if refstr:
            return f"{textrefstr}\nOther passages: {refstr}"
        else:
            return textrefstr

    def topicversetext(self, topicslug: str, maxverselen: int = 3) -> dict[str, str]:
        """Return a serializable dict of topic data.

        Includes verse text for references whose length does not
        exceed maxverselen.

        """
        topicinst: Topic = self.topicsdict[topicslug]
        topiclabel: str = topicinst.topic
        topicrefstr: str = self._render_versetext(topicslug=topicslug, maxverselen=maxverselen)
        promptstr: str = f"What does the Bible say about the topic of '{topiclabel}'?"
        completionstr: str = (
            f"These are some popular verses addressing {topiclabel}:\n{topicrefstr}"
        )
        return {
            "prompt": promptstr,
            "completion": completionstr,
            "context": "",
            # "context": f"Respond drawing on the most Bible important verses for the topic {topiclabel}, and answer from a Christian perspective.",
        }

    def topicsummary(self, topicslug: str, maxverselen: int = 3) -> dict[str, str]:
        """Return a serializable dict of topic data.

        Includes verse text and topic summaries.

        """
        topicinst: Topic = self.topicsdict[topicslug]
        topiclabel: str = topicinst.topic
        promptstr: str = f"What does the Bible say about the topic of '{topiclabel}'?"
        topicrefstr: str = self._render_versetext(topicslug=topicslug, maxverselen=maxverselen)
        summary: str = self.vsreader[topicslug]
        completionstr: str = (
            f"These are some popular verses addressing {topiclabel}:\n{topicrefstr}\n{summary}"
        )
        return {
            "prompt": promptstr,
            "completion": completionstr,
            "context": "",
            # "context": f"Respond drawing on the most Bible important verses for the topic {topiclabel}, and answer from a Christian perspective.",
        }
