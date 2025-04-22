"""Retrieve summaries of a set of topic verses from an LLM.

>>> from src import reader, versesummary
# get the topics
>>> rd = reader.Topics()
>>> vsq = versesummary.Query(topics=rd.topicsdict)
# read the data back in
>>> vsr = versesummary.VerseSummaryReader()
"""

from collections import UserDict
from csv import DictReader, DictWriter
from pathlib import Path
import re

import llm
from tqdm import tqdm

from src import DATAPATH, OPENAI_API_KEY
from .topic import Topic


class Query(UserDict):
    """Query an LLM for verse topic summaries."""

    modelname: str = "gpt-4o"
    model = llm.get_model(modelname)
    # lower values should produce less variability in responses. Not
    # sure that's important, but ...
    temperature: float = 0.1

    def __init__(self, topics: dict[str, Topic]) -> None:
        """Initialize an instance."""
        super().__init__(self)
        self.model.key = OPENAI_API_KEY
        self.topics = topics
        self.conversation: llm.models.Conversation = None
        self.lastresponse: llm.models.Response = None

    def get_response(self, prompt: str) -> str:
        """Return a response to the prompt."""
        # always start a new conversation: don't want previous topics
        # to pollute this one.
        self.conversation = self.model.conversation()
        self.lastresponse = self.conversation.prompt(prompt, temperature=self.temperature)
        responsetext = self.lastresponse.text()
        return responsetext

    def _topic_prompt(self, topic: Topic) -> str:
        """Return a string to use as a prompt with ChatGPT."""
        topicprompt = f"These are some popular verses addressing the topic of {topic.topic}: {topic.referencestr}."
        summaryprompt = f"Summarize in 2-3 sentences what these verses teach about {topic.topic}."
        prompt = f"You are a Christian pastor. {topicprompt} {summaryprompt}"
        return prompt

    def log_summaries(self, outpath: Path = DATAPATH / "topicsummariesnames.tsv") -> None:
        """Generate summaries for each topic and write to TSV.

        The topics should be ranked from highest 'engagement' to
        lowest, so order is significant.

        """
        with outpath.open("w") as f:
            writer = DictWriter(f, ("topicslug", "summary"), delimiter="\t")
            writer.writeheader()
            for topicslug, topicinst in tqdm(self.topics.items()):
                response = self.get_response(self._topic_prompt(topicinst))
                writer.writerow({"topicslug": topicslug, "summary": response})


class VerseSummaryReader(UserDict):
    """Read verse summaries from file."""

    mentionre = re.compile("(you|you've) (mentioned|list|referenced)")
    addressre = re.compile("(do not|don't) (directly|specifically) address")

    def __init__(self, tsvpath: Path = DATAPATH / "topicsummaries01.tsv") -> None:
        super().__init__(self)
        self.tsvpath = tsvpath
        assert self.tsvpath.exists(), f"File does not exist: {self.tsvpath}"
        with self.tsvpath.open() as f:
            reader = DictReader(f, delimiter="\t")
            self.alldata = {row["topicslug"]: row["summary"] for row in reader}
            self.data = {
                slug: summary
                for slug, summary in self.alldata.items()
                if not self.offtopic(summary)
            }

    def offtopic(self, summary: str) -> bool:
        """Return True if the summary suggests the verses don't address the topic.

        This is heuristic.
        """
        return self.mentionre.search(summary) and self.addressre.search(summary)
