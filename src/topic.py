"""Define data container for templated structured learning data."""

from dataclasses import dataclass

from slugify import slugify

from .verse import Verse


@dataclass
class Topic:
    topic: str
    verses: tuple[Verse, ...]
    # computed
    topicslug: str = ""
    # definition of the topic, possibly synthesized from multiple sources?
    definition: str = ""
    # sum of votespercentage for all verses: a rough metric for how
    # much of the total probability mass these verses capture
    focus: float = 0.0
    # user-displayable list of references as a single string
    referencestr: str = ""
    # summary of what's taught in the verses
    summary: str = ""
    # the text for verses: must be populated
    versetexts: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Compute values after initialization."""
        self.topicslug = slugify(self.topic)
        self.focus = sum(float(verse.votespercentage) for verse in self.verses)
        self.referencestr = self.get_referencestr()

    def __repr__(self) -> str:
        """Return a printed representation."""
        return f"<Topic({self.topicslug}) {len(self.verses)} verses>"

    def get_referencestr(self) -> str:
        """Return a user-displayable USFM string for verses."""
        if len(self.verses) == 1:
            return self.verses[0].userref
        elif len(self.verses) == 2:
            return f"{self.verses[0].userref} and {self.verses[1].userref}"
        else:
            butlast = ", ".join([v.userref for v in self.verses[:-2]])
            return f"{butlast}, and {self.verses[-1].userref}"

    def get_linked_referencestr(self) -> str:
        """Return a user-displayable USFM string for verses with markdown links."""
        if len(self.verses) == 1:
            return self.verses[0].userref
        elif len(self.verses) == 2:
            return f"{self.verses[0].userref} and {self.verses[1].userref}"
        else:
            butlast = ", ".join([v.userref for v in self.verses[:-2]])
            return f"{butlast}, and {self.verses[-1].userref}"
