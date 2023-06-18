import copy
from typing import List

from cjw.aistory.bots.Utterance import Utterance


class StoryFork:
    @classmethod
    def of(
            cls,
            contents: str | Utterance | List[str] | List[Utterance],
            nextActors: List[str],
            previous: "StoryFork" = None
    ) -> "StoryFork":

        utterances = Utterance.of(contents)
        utterances.reverse()

        story = None
        branches = None

        for u in utterances:
            story = StoryFork(u, nextActors=nextActors, branches=branches, previous=previous)
            if branches:
                branches[0].previous = story
            branches = [story]
            nextActors = [u.speaker]

        return story

    def __init__(
            self,
            utterance: Utterance,
            nextActors: List[str] = None,
            branches: List["StoryFork"] = None,
            previous: "StoryFork" = None
    ):
        self.utterance = utterance
        self.branches = branches if branches else []
        self.nextActors = nextActors if nextActors else []
        self.previous = previous
        self.rephrases = []

    def getStoryLine(self, actor: str) -> List[Utterance]:
        storyLine = []
        fork = self
        while fork:
            if fork.utterance.speaker != actor and fork.utterance.private:
                continue

            utterance = copy.copy(fork.utterance)
            utterance.creator = Utterance.Creator.AI if utterance.speaker == actor else Utterance.Creator.USER
            storyLine.append(utterance)
            fork = fork.previous

        storyLine.reverse()
        return storyLine

    def getStoryLeads(self) -> List["StoryFork"]:
        leads = []
        queue = [self]

        while queue:
            fork = queue.pop(0)
            if fork.branches:
                queue += fork.branches
            else:
                leads.append(fork)

        return leads

    def serialize(self) -> dict:
        content = {
            "utterance": self.utterance.serialize(),
            "nextActors": self.nextActors
        }
        if self.rephrases:
            content["rephrases"] = self.rephrases
        if self.branches:
            content["branches"] = [b.serialize() for b in self.branches]

        return content

    @classmethod
    def deserialize(cls, data: dict) -> "StoryFork":
        fork = StoryFork(
            utterance=Utterance.deserialize(data["utterance"]),
            nextActors=data["nextActors"],
            branches=[cls.deserialize(b) for b in data["branches"]] if "branches" in data else [],
        )
        fork.rephrases = data["rephrases"] if "rephrases" in data else []

        for b in fork.branches:
            b.previous = fork

        return fork

    def prettyList(self, indent="    ", indentLevel=0) -> str:
        line = f"{indent * indentLevel}{self.utterance}",
        rephrases = [f"{indent * indentLevel}({r})" for r in self.rephrases]
        branches = [b.prettyList(indent=indent, indentLevel=indentLevel + 1) for b in self.branches]

        return '\n'.join(list(line) + rephrases + branches)
