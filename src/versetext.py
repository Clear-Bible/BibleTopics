"""Retrieve Bible text and cache in TSV.

>>> from src import reader, versetext
# get the topics
>>> rd = reader.Topics()
>>> vt = versetext.VerseText(topics=rd.topics)

# dump text to file: only need to do this once/if references
change. But it takes quite a while, so we cache the results on disk.
>>> vt.dump_text()

# once it's dumped you can read it in
>>> vtr = versetext.VerseTextReader()
>>> len(vtr)
322
>>> vtr["MAL 3:5"]
'“Then I will draw near to you for judgment. And I will be a swift witness against sorcerers and adulterers and perjurers, against oppressors of the widowed and fatherless, and against those who defraud laborers of their wages and deny justice to the foreigner but do not fear Me,” says the LORD of Hosts. '
# but you need to text to ensure the text for a verse is present
>>> "JHN 3:16" in vtr
True
>>> "JHN 3:1" in vtr
False

"""

from collections import UserDict
from csv import DictReader, DictWriter
from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport
from gql.transport.exceptions import TransportServerError
from pathlib import Path
from time import sleep

# endpoint defined in .env
from src import DATAPATH, SYMPHONY_ATLAS_GRAPHQL_ENDPOINT
from .topic import Topic


class VerseText:
    """Manage text for a selected set of Bible references associated with topics."""

    transport = RequestsHTTPTransport(
        url=SYMPHONY_ATLAS_GRAPHQL_ENDPOINT,
        # TODO: Enable authorization header for "closed" textual editions
        # headers={"Authorization": "Bearer <YOUR-API-KEY_HERE>"},
    )
    query = gql(
        """query PassageByReference($filters: PassageFilter) {
    passage(filters: $filters) {
      usfmRef
      ref
      textContent
    }
    }"""
    )
    _cache = {}

    def __init__(self, topics: dict[str, Topic], textualEdition: str = "BSB") -> None:
        """Initialize an instance."""
        self.topics = topics
        self.edition = textualEdition
        self.client = Client(transport=self.transport, fetch_schema_from_transport=True)

    def get_response(self, usfmRef: str) -> dict[str, list[dict[str, str]]]:
        """Return a response object with textContent.

        Caches responses so they're only retrieved once.
        """
        if usfmRef not in self._cache:
            variables = {
                "filters": {
                    "scriptureReference": {
                        "usfmRef": usfmRef,
                        "textualEdition": self.edition,
                    }
                }
            }
            try:
                self._cache[usfmRef] = self.client.execute(self.query, variable_values=variables)
            except TransportServerError:
                print("TransportServerError: trying again in 5 seconds")
                sleep(5)
                try:
                    self._cache[usfmRef] = self.client.execute(self.query, variable_values=variables)
                except TransportServerError:
                    print("2nd TransportServerError: failing.")
                    return None
        return self._cache[usfmRef]

    def get_text(self, response) -> dict[str, list[dict[str, str]]]:
        """Return the plan text from a response.

        For ranges, concatenate the textContent.
        """
        return "".join([passage["textContent"] for passage in response["passage"]])

    def dump_text(self, outpath: Path = DATAPATH / "versetext.tsv") -> None:
        """Dump reference and text to TSV."""
        with outpath.open("w") as f:
            writer = DictWriter(f, ("usfmRef", "text"), delimiter="\t")
            writer.writeheader()
            for topicinst in self.topics.values():
                for verse in topicinst.verses:
                    usfmRef = verse.userref
                    if usfmRef not in self._cache:
                        response = self.get_response(usfmRef)
                        if response:
                            writer.writerow({"usfmRef": usfmRef, "text": self.get_text(response)})
                        else:
                            print(f"Skipping {usfmRef}")


class VerseTextReader(UserDict):
    """Read verse text from file."""

    def __init__(self, tsvpath: Path = DATAPATH / "versetext.tsv") -> None:
        super().__init__(self)
        self.tsvpath = tsvpath
        assert self.tsvpath.exists(), f"File does not exist: {self.tsvpath}"
        with self.tsvpath.open() as f:
            reader = DictReader(f, delimiter="\t")
            self.data = {row["usfmRef"]: row["text"] for row in reader}
